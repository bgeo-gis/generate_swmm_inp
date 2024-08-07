# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GenerateSwmmInp
                                 A QGIS plugin
 This plugin generates SWMM Input files
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-09
        copyright            : (C) 2021 by Jannik Schilling
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
__date__ = '2024-08-07'
__copyright__ = '(C) 2021 by Jannik Schilling'


import pandas as pd
import os
import numpy as np
import copy
from qgis import processing
from qgis.core import (
    NULL,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsProcessingException,
    QgsProcessingFeedback,
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
    def_qgis_fields_dict,
    def_point_geom,
    def_line_geom,
    def_ploygon_geom
)
from .g_s_import_helpers import replace_nan_null

# export functions
# helper function for export
def replace_null_nan(attr_value):
    """replaces NULL with np.nan"""
    if attr_value == NULL:
        return np.nan
    else:
        return attr_value

def del_none_bool(df):
    """
    replaces None or NULL with np.nan
    replaces True and False with 'YES' and 'NO'
    except of geometry column
    :param pd.DataFrame df
    :return: pd.DataFrame
    """
    df[df.columns[:-1]] = df[df.columns[:-1]].fillna(value=np.nan)
    df = df.applymap(replace_null_nan)
    df[df.columns[:-1]] = df[df.columns[:-1]].replace('True', 'YES').replace('False', 'NO')
    return df

def load_layer_to_df(
    vlayer,
    select_cols=[],
    with_id=False,
    feedback = QgsProcessingFeedback
):
    """
    reads layer attributes and geometries
    :param QgsVectorLayer vlayer
    :param list select_cols: if not empty, these will be extracted
    :param bool with_id
    :param QgsProcessingFeedback feedback
    :return: pd.DataFrame
    """
    feedback.setProgressText('    layer: '+vlayer.name())
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
            
            
    # check for missing and duplcat names and null or missing geometries
    check_list = [[f['Name'], f.id(), f.hasGeometry()] for f in vlayer.getFeatures()]
    seen = set()
    duplicat_names_list = []
    missing_names_list = []
    missing_geoms_list = []
    for f in check_list:
        feature_name = f[0]
        if not feature_name:
            missing_names_list.append(str(f[1]))  # add id to list
            feature_name = 'id = ' + str(f[1])  # replace with id for geometry check
        else:
            feature_name = str(feature_name)  # just in case it is numeric
            if feature_name in seen:
                duplicat_names_list.append(feature_name)
            else:
                seen.add(feature_name)
        if not f[2]:  # no geometry
            missing_geoms_list.append(feature_name)
    duplicat_names_list = list(set(duplicat_names_list))
    if missing_names_list or duplicat_names_list or missing_geoms_list:
        exception_text = (
            'Error in layer '+ vlayer.name()+':\n'
            +(
                (
                    '  missing attribute \"Name\" (primary key in SWMM) for feature(s) with id = '
                    +', '.join(missing_names_list)
                    +'\n'
                ) if missing_names_list else ''
            )+(
                (
                    '  duplicat attribute \"Name\" (primary key in SWMM): '
                    +', '.join(duplicat_names_list)
                    +'\n'
                ) if duplicat_names_list else ''
           )+(
                (
                    '  missing geometries: '
                    +', '.join(missing_geoms_list)
                ) if missing_geoms_list else ''
            )
        )
        raise QgsProcessingException(exception_text)


    # data generator
    if with_id is True:
        datagen = ([f[col] for col in cols] + [f.geometry()] + [f.id()] for f in vlayer.getFeatures())
        df = pd.DataFrame.from_records(data=datagen, columns=cols+['geometry', 'id'])
    else:
        datagen = ([f[col] for col in cols]+[f.geometry()] for f in vlayer.getFeatures())
        df = pd.DataFrame.from_records(data=datagen, columns=cols+['geometry'])
    return df

# layers with geometry
def read_layers_direct(
    raw_layers_dict,
    select_cols=[],
    with_id=False,
    feedback = QgsProcessingFeedback
):
    """
    reads layers from swmm model
    :param dict raw_layers_dict
    :param list select_cols
    :param bool with_id
    :param QgsProcessingFeedback feedback
    :return: dict
    """
    data_dict = {n: load_layer_to_df(d, select_cols, with_id, feedback) for n, d in raw_layers_dict.items() if d is not None}
    data_dict_out = {n: d for n, d in data_dict.items() if len(d) > 0}
    data_dict_out = {n: del_none_bool(data_dict_out[n]) for n in data_dict_out.keys()}
    return data_dict_out


# tables
def read_data_from_table_direct(tab_file, sheet=0, feedback=QgsProcessingFeedback):
    """
    reads curves or other tables from excel or gpkg
    :param str file
    :param str/int sheet
    """
    feedback.setProgressText('    Table: '+sheet)
    table_layers = QgsVectorLayer(tab_file, 'NoGeometry', 'ogr')
    table_provider = table_layers.dataProvider()
    sublayers = table_provider.subLayers()
    name_separator = table_provider.sublayerSeparator()
    sheets = [x.split(name_separator)[1] for x in sublayers]
    if sheet == 0:
        s_n = sheets[0]
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
        tab_layer_to_load = tab_file+'|layername='+str(s_n)
        vlayer = QgsVectorLayer(tab_layer_to_load, 'NoGeometry', 'ogr')
        cols = [f.name() for f in vlayer.fields()]
        datagen = ([f[col] for col in cols] for f in vlayer.getFeatures())
        data_df = pd.DataFrame.from_records(data=datagen, columns=cols)
        data_df = data_df.applymap(replace_null_nan)
        if all([x.startswith('Field') for x in data_df.columns]):
            rename_cols = {i:j for i, j in zip(cols, data_df.loc[0,:].tolist())}
            data_df = data_df.drop(index=0)
            data_df.rename(columns=rename_cols, inplace=True)
        data_df.dropna(axis=0, how='all', inplace=True)  # delete empty rows
        data_df.reset_index(drop=True, inplace=True)
        if 'fid' in cols:
            data_df = data_df.drop(columns=['fid'])
    else:
        data_df = pd.DataFrame()
    return data_df

# import
# write functions and helpers


def create_feature_from_row(df, geom_type):
    """
    creates a QgsFeature from data in df
    :param pd.DataFrame df
    :param str geom_type
    """
    f = QgsFeature()
    if geom_type != 'NoGeometry':
        # handle missing geometry: replace with default
        if df['geometry'] is NULL:
            if geom_type == 'Polygon':
                f.setGeometry(def_ploygon_geom)
            if geom_type == 'LineString':
                f.setGeometry(def_line_geom)
            if geom_type == 'Point':
                f.setGeometry(def_point_geom)
        else:
            f.setGeometry(df['geometry'])
        f.setAttributes(df.tolist()[:-1])
    else:
        f.setAttributes(df.tolist())
    return f

def transform_crs_function(
    vector_layer,
    current_crs_string,
    transform_crs_string
):
    """
    transforms a layer CRS
    :param QgsVectorLayer vector_layer
    :param str current_crs_string
    :param str transform_crs_string
    """
    current_crs = QgsCoordinateReferenceSystem(current_crs_string)
    transform_crs = QgsCoordinateReferenceSystem(transform_crs_string)
    vector_layer.startEditing()
    for ft in vector_layer.getFeatures():
        geom = ft.geometry()
        geom = QgsGeometry(geom)
        geom.transform(
            QgsCoordinateTransform(
                current_crs,
                transform_crs,
                QgsProject.instance()
            )
        )
        fid = ft.id()
        vector_layer.changeGeometry(fid,geom)
    vector_layer.commitChanges()
    vector_layer.setCrs(transform_crs)


def create_layer_from_df(
    data_dict,
    section_name,
    crs_result,
    feedback,
    custom_fields=None,
    create_empty=False,
    transform_crs_string='NA',
    **kwargs
):
    """
    creates a QgsVectorLayer from data in geodata_dict
    :param dict data_dict
    :param str section_name: name of SWMM section
    :param str crs_result: epsg code of the desired CRS
    :param QgsProcessingFeedback feedback
    :param dict custom_fields: additional fields e.g. annotations
    :param bool create_empty
    :param str transform_crs_string
    """
    data_df = data_dict['data']
    layer_name = data_dict['layer_name']

    # set geometry type and provider
    if section_name in def_sections_geoms_dict.keys():
        feedback.setProgressText('Writing layer for section \"'+section_name+'\"')
        geom_type = def_sections_geoms_dict[section_name]
    else:
        geom_type = 'NoGeometry' # for simple tables
    geom_type_and_crs = geom_type+'?crs='+crs_result
    pr = 'a'
    vector_layer = QgsVectorLayer(geom_type_and_crs, layer_name, 'memory')
    pr = vector_layer.dataProvider()


    # set fields
    field_types_dict = {
        'Double': QVariant.Double,
        'String': QVariant.String,
        'Int': QVariant.Int,
        'Bool': QVariant.Bool,
        'Date': QVariant.Date,
        'Time': QVariant.Time
    }
    if geom_type != 'NoGeometry':
        layer_fields = copy.deepcopy(def_qgis_fields_dict[section_name])
    else:
        layer_fields = def_tables_dict[section_name]['tables'][layer_name]
    if custom_fields is not None:
        layer_fields.update(custom_fields)
    for col, field_type_string in layer_fields.items():
        field_type = field_types_dict[field_type_string]
        # QgsField is deprecated since QGIS 3.38 -> QMetaType
        pr.addAttributes([QgsField(col, field_type)])
    vector_layer.updateFields()

    # get data_df columns in the correct order
    if not create_empty:
        data_df_column_order = list(layer_fields.keys())
        if geom_type != 'NoGeometry':
            data_df_column_order = data_df_column_order+['geometry']
            if any ([g == NULL for g in data_df['geometry']]):
                no_geom_features = list(data_df.loc[data_df['geometry'] == NULL, 'Name'])
                feedback.pushWarning(
                    'Warning: in section \"'
                    + section_name
                    + '\" one (or more) geometries are missing in the input file. Affected feature(s): '
                    + ', '.join([str(x) for x in no_geom_features])
                    + '.\nDefault geometries will be used instead. The features can be found around (0,0)'
                )
        else:
            # replace nan with NULL in tables
            data_df = data_df.applymap(replace_nan_null)
        data_df = data_df[data_df_column_order]
    if len(data_df) != 0:
        # add features if data_df is not empty (which can be the case for tables)
        feature_list = data_df.apply(lambda x: create_feature_from_row(x, geom_type), axis=1)
        pr.addFeatures(feature_list)
        vector_layer.updateExtents()
    # transformation of CRS
    if transform_crs_string != 'NA' and geom_type != 'NoGeometry':
        transform_crs_function(
            vector_layer,
            crs_result,
            transform_crs_string
        )
    return vector_layer
    
def save_layer_to_file(
    vector_layer,
    layer_name,
    folder_save,
    geodata_driver_num,
    **kwargs
):
    # set driver
    geodata_driver_name = def_ogr_driver_names[geodata_driver_num]
    geodata_driver_extension = def_ogr_driver_dict[geodata_driver_name]

    # create layer
    fname = os.path.join(
        folder_save, 
        layer_name+ '.' +geodata_driver_extension
    )
    if os.path.isfile(fname):
        raise QgsProcessingException('File '+fname
        + ' already exists. Please choose another folder.')
    try:
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.fileEncoding = 'utf-8'
        options.driverName = geodata_driver_name
        transform_context = QgsProject.instance().transformContext()
        QgsVectorFileWriter.writeAsVectorFormatV3(
            vector_layer,
            fname,
            transform_context,
            options
        )
    except BaseException:        # for older QGIS versions
        QgsVectorFileWriter.writeAsVectorFormat(
            vector_layer,
            fname,
            'utf-8',
            vector_layer.crs(),
            driverName=geodata_driver_name
        )

# Tables to Excel files
def create_empty_feature(vector_layer):
    """
    creates an empty QgsFeature for an existing QgsVectorLayer
    :param QgsVectorLayer vector_layer
    :return: QgsFeature
    """
    new_ft = QgsFeature()
    layer_fields = vector_layer.fields()
    new_ft.setFields(layer_fields)
    new_ft.setAttributes([NULL] * len(layer_fields))
    return new_ft

def layerlist_to_excel(
    layer_list,
    section_name,
    folder_save,
    feedback,
    result_prefix='',
    desired_table_format=None,
    **kwargs
):
    """
    writes an excel file from a data_dict
    :param list layer_list
    :param str section_name: name of SWMM section
    :param str folder_save
    :param QgsProcessingFeedback feedback
    :param str result_prefix: prefix for file name
    :param str desired_table_format
    """
    save_name = def_tables_dict[section_name]['filename']
    if result_prefix != '':
        save_name = result_prefix+'_'+save_name
    if desired_table_format is not None:
        ext = desired_table_format
    else: 
        ext = '.xlsx' # default setting
    save_name_ext = save_name + ext
    fname = os.path.join(folder_save, save_name_ext)
    feedback.setProgressText(
        'Writing file '
        + str(fname)
        +' for section \"'
        +section_name
        +'\"'
    )
    for vector_layer in layer_list:
        if vector_layer.featureCount() == 0:
            vector_layer.startEditing()
            new_ft = create_empty_feature(vector_layer)
            vector_layer.addFeature(new_ft)
            vector_layer.commitChanges()
    if os.path.isfile(fname):
        raise QgsProcessingException('File '+fname
        + ' already exists. Please choose another folder.')
    else:
        processing.run(
            "native:exporttospreadsheet", 
            {
                'LAYERS' : layer_list,
                'USE_ALIAS': False,
                'FORMATTED_VALUES': False,
                'OUTPUT': fname,
                'OVERWRITE': True
            }
        )
