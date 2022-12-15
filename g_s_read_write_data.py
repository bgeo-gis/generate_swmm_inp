# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GenerateSwmmInp
                                 A QGIS plugin
 This plugin generates SWMM Input files
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-09
        copyright            : (C) 2022 by Jannik Schilling
        email                : jannik.schilling@posteo.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Jannik Schilling'
__date__ = '2022-12-15'
__copyright__ = '(C) 2022 by Jannik Schilling'


import pandas as pd
import os
import numpy as np
import copy
from qgis.core import (
    NULL,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsProcessingException,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer
)
from qgis.PyQt.QtCore import QVariant
from .g_s_defaults import (
    def_ogr_driver_names,
    def_ogr_driver_dict,
    def_sections_geoms_dict,
    def_tables_dict,
    def_qgis_fields_dict
)


# helper functions
def replace_null_nan(attr_value):
    """replaces NULL with np.nan"""
    if attr_value == NULL:
        return np.nan
    else:
        return attr_value


# read functions
# layers with geometry
def replace_null_nan(attr_value):
    """replaces NULL with np.nan"""
    if attr_value == NULL:
        return np.nan
    else:
        return attr_value


def read_layers_direct(
    raw_layers_dict,
    select_cols=[],
    with_id=False
):
    """
    reads layers from swmm model
    :param dict raw_layers_dict
    :param list select_cols
    :param bool with_id
    """

    def del_none_bool(df):
        """
        replaces None or NULL with np.nan
        replaces True and False with 'YES' and 'NO'
        except of geometry column
        :param pd.DataFrame df
        """
        df[df.columns[:-1]] = df[df.columns[:-1]].fillna(value=np.nan)
        df = df.applymap(replace_null_nan)
        df[df.columns[:-1]] = df[df.columns[:-1]].replace('True', 'YES').replace('False', 'NO')
        return df

    def load_layer_to_df(
        vlayer,
        select_cols=[],
        with_id=False
    ):
        """
        reads layer attributes and geometries
        :param QgsVectorLayer vlayer
        :param list select_cols
        :param bool with_id
        """
        cols = [f.name() for f in vlayer.fields()]
        if len(select_cols) > 0:
            if all([x in cols for x in select_cols]):
                cols = select_cols
            else:
                missing_cols = [x for x in select_cols if x not in cols]
                raise QgsProcessingException(
                    'Missing colums in layer '
                    + vlayer.name()
                    + ': ' + ', '.join(missing_cols)
                )
        # check for null geometries
        if any(not(f.hasGeometry()) for f in vlayer.getFeatures()):
            name_missing_geom = [f['Name'] for f in vlayer.getFeatures() if not(f.hasGeometry())]
            raise QgsProcessingException(
                'Failed to load layer: missing geometries in '
                + vlayer.name()+': '+', '.join(name_missing_geom)
            )
        # data generator
        if with_id is True:
            datagen = ([f[col] for col in cols] + [f.geometry()] + [f.id()] for f in vlayer.getFeatures())
            df = pd.DataFrame.from_records(data=datagen, columns=cols+['geometry', 'id'])
        else:
            datagen = ([f[col] for col in cols]+[f.geometry()] for f in vlayer.getFeatures())
            df = pd.DataFrame.from_records(data=datagen, columns=cols+['geometry'])
        return df
    data_dict = {n: load_layer_to_df(d, select_cols, with_id) for n, d in raw_layers_dict.items() if d is not None}
    data_dict_out = {n: d for n, d in data_dict.items() if len(d) > 0}
    data_dict_out = {n: del_none_bool(data_dict_out[n]) for n in data_dict_out.keys()}
    return data_dict_out


# tables
def read_data_from_table_direct(file, sheet=0):
    '''reads curves or other tables from excel or csv'''
    filename, file_extension = os.path.splitext(file)
    if file_extension == '.xlsx' or file_extension == '.xls' or file_extension == '.ods':
        try:
            sheets = list(pd.read_excel(file, None, engine='openpyxl').keys())
        except BaseException:
            sheets = pd.ExcelFile(file).sheet_names
        if sheet == 0:
            s_n = 0
        else:
            if sheet in sheets:
                s_n = sheet
            elif str(sheet).upper() in sheets:
                s_n = str(sheet).upper()
            elif str(sheet).lower() in sheets:
                s_n = str(sheet).lower()
            elif str(sheet).capitalize() in sheets:
                s_n = str(sheet).capitalize()
            else:
                s_n = None
        if s_n is not None:
            try:
                data_df = pd.read_excel(file, sheet_name=s_n)
            except BaseException:
                data_df = pd.read_excel(
                    file,
                    sheet_name=s_n,
                    engine='openpyxl'
                )
        else:
            data_df = pd.DataFrame()
    if file_extension == '.gpkg':
        if sheet == 0:
            gpkg_layers = QgsVectorLayer(file, 'NoGeometry', 'ogr')
            gpkg_provider = gpkg_layers.dataProvider()
            sublayer_0 = gpkg_provider.subLayers()[0]
            name_separator = gpkg_provider.sublayerSeparator()
            sheet = sublayer_0.split(name_separator)[1]
        read_file = file+'|layername='+str(sheet)
        vlayer = QgsVectorLayer(read_file, 'NoGeometry', 'ogr')
        cols = [f.name() for f in vlayer.fields()]
        datagen = ([f[col] for col in cols] for f in vlayer.getFeatures())
        data_df = pd.DataFrame.from_records(data=datagen, columns=cols)
        data_df = data_df.applymap(replace_null_nan)
        data_df = data_df.drop(columns=['fid'])
    return data_df


# write functions and helpers
def create_feature_from_df(df, pr, geom_type):
    """
    creates a QgsFeature from data in df
    :param pd.DataFrame df
    :param QgsVectorLayer.dataProvider() pr
    :param str geom_type
    """
    f = QgsFeature()
    if geom_type != 'NoGeometry':
        #f.setGeometry(df['geometry'])
        f.setGeometry(df['geometry'])
        f.setAttributes(df.tolist()[:-1])
    else:
        f.setAttributes(df.tolist())
    pr.addFeature(f)


def create_layer_from_table(
    data_df,
    section_name,
    layer_name,
    crs_result,
    folder_save,
    geodata_driver_num,
    custom_fields=None,
    create_empty=False
):
    """
    creates a QgsVectorLayer from data in data_df
    :param pd.DataFrame data_df
    :param str section_name: name of SWMM section
    :param str layer_name
    :param str crs_result: epsg code of the desired CRS
    :param str folder_save
    :param int geodata_driver_num: key of driver in def_ogr_driver_dict
    :param dict costum fields: additional fields
    """
    # set driver
    geodata_driver_name = def_ogr_driver_names[geodata_driver_num]
    geodata_driver_extension = def_ogr_driver_dict[geodata_driver_name]
    # set geometry type and provider
    geom_type = def_sections_geoms_dict[section_name]
    geom_type = geom_type+'?crs='+crs_result
    vector_layer = QgsVectorLayer(geom_type, layer_name, 'memory')
    pr = vector_layer.dataProvider()
    # set fields
    field_types_dict = {
        'Double': QVariant.Double,
        'String': QVariant.String,
        'Int': QVariant.Int,
        'Bool': QVariant.Bool
    }
    layer_fields = copy.deepcopy(def_qgis_fields_dict[section_name])
    if custom_fields is not None:
        layer_fields.update(custom_fields)
    for col, field_type_string in layer_fields.items():
        field_type = field_types_dict[field_type_string]
        pr.addAttributes([QgsField(col, field_type)])
    vector_layer.updateFields()
    # get data_df columns in the correct order
    if not create_empty:
        data_df_column_order = list(layer_fields.keys())
        if geom_type != 'NoGeometry':
            data_df_column_order = data_df_column_order+['geometry']
        data_df = data_df[data_df_column_order]
    data_df.apply(lambda x: create_feature_from_df(x, pr, geom_type), axis=1)
    vector_layer.updateExtents()
    # create layer
    try:
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.fileEncoding = 'utf-8'
        options.driverName = geodata_driver_name
        transform_context = QgsProject.instance().transformContext()
        QgsVectorFileWriter.writeAsVectorFormatV3(
            vector_layer,
            os.path.join(
                folder_save,
                layer_name + '.' + geodata_driver_extension
            ),
            transform_context,
            options
        )
    except BaseException:
        # for older QGIS versions
        QgsVectorFileWriter.writeAsVectorFormat(
            vector_layer,
            os.path.join(
                folder_save,
                layer_name + '.' + geodata_driver_extension
            ),
            'utf-8',
            vector_layer.crs(),
            driverName=geodata_driver_name
        )
    del vector_layer
    del pr
    return ()


# Tables to Excel files
def dict_to_excel(
    data_dict,
    file_key,
    folder_save,
    feedback,
    res_prefix='',
    desired_format=None
):
    """
    writes an excel file from a data_dict
    :param dict data_dict
    :param str save_name
    :param str folder_save
    :param QgsProcessingFeedback feedback
    :param str res_prefix: prefix for file name
    :param str desired_format
    """
    save_name = def_tables_dict[file_key]['filename']
    if res_prefix != '':
        save_name = res_prefix+'_'+save_name
    if desired_format is not None:
        try:
            save_name = save_name+desired_format
            with pd.ExcelWriter(os.path.join(folder_save, save_name)) as writer:
                for sheet_name, df in data_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        except BaseException:
            raise QgsProcessingException(self.tr(
                'Could not write tables in the desired file format.'
                ' Please install the package \"openpyxl\" (or alternatively'
                ' the package \"odf\"). Instructions can be found on the in '
                'the documentation or on GitHub '
                '(https://github.com/Jannik-Schilling/generate_swmm_inp)'
            ))
    else:
        try:
            save_name_xlsx = save_name+'.xlsx'
            with pd.ExcelWriter(os.path.join(folder_save, save_name_xlsx)) as writer:
                for sheet_name, df in data_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        except BaseException:
            try:
                save_name_xls = save_name+'.xls'
                with pd.ExcelWriter(os.path.join(folder_save, save_name_xls)) as writer:
                    for sheet_name, df in data_dict.items():
                        df.to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False
                        )
            except BaseException:
                try:
                    save_name_ods = save_name+'.ods'
                    with pd.ExcelWriter(os.path.join(folder_save, save_name_ods)) as writer:
                        for sheet_name, df in data_dict.items():
                            df.to_excel(
                                writer,
                                sheet_name=sheet_name,
                                index=False
                            )
                except BaseException:
                    raise QgsProcessingException(self.tr(
                        'Could not write tables in .xlsx, .xls, or .ods'
                        ' format. Please install the package \"openpyxl\" '
                        '(or alternatively the package "odf"). Instructions '
                        'can be found on the in the documentation or on '
                        'GitHub (https://github.com/Jannik-Schilling/generate_swmm_inp)'
                    ))
