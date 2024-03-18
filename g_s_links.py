# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GenerateSwmmInp
                                 A QGIS plugin
 This plugin generates SWMM Input files
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-07-09
        copyright            : (C) 2023 by Jannik Schilling
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
__date__ = '2023-05-09'
__copyright__ = '(C) 2023 by Jannik Schilling'

import pandas as pd
import numpy as np
from qgis.core import (
    NULL,
    QgsProcessingException,
    QgsGeometry
)
from .g_s_defaults import (
    def_qgis_fields_dict,
    def_sections_dict
)
from .g_s_various_functions import (
    check_columns
)

# Definitions
# Inlets
inl_types_def = {
    'GRATE': ['Length', 'Width', 'Shape'],
    'CUSTOM': ['Shape'],
    'CURB': ['Length', 'Heigth', 'Shape'],
    'SLOTTED': ['Length', 'Width'],
    'DROP_GRATE': ['Length', 'Width', 'Shape'],
    'DROP_CURB': ['Length', 'Heigth']}
all_inl_type_cols = [
    'Length',
    'Width',
    'Heigth',
    'Shape',
    'OpenFract',
    'SplashVel'
]


# Export
# conduits
def get_conduits_from_shapefile(conduits_raw):
    """
    prepares conduits data for writing an input file
    removes columns which are not needed, replaces empty values with '' or '*'
    :param pd.DataFrame conduits_raw
    """
    # check if all columns exist
    qgis_conduits_cols = list(def_qgis_fields_dict['CONDUITS'].keys())
    conduits_cols = def_sections_dict['CONDUITS']
    xsections_cols = def_sections_dict['XSECTIONS']
    losses_cols = def_sections_dict['LOSSES']
    cond_layer_name = 'Conduits Layer'
    check_columns(cond_layer_name,
                  qgis_conduits_cols,
                  conduits_raw.keys())
    conduits_df = conduits_raw[conduits_cols].copy()
    conduits_df['Name'] = [str(x) for x in conduits_df['Name']]
    # Asteriscs indicate that InOffset or OutOffset is the same as node elevation:
    conduits_df['InOffset'] = conduits_df['InOffset'].fillna('*')
    conduits_df['OutOffset'] = conduits_df['OutOffset'].fillna('*')
    conduits_df['InitFlow'] = conduits_df['InitFlow'].fillna('0')
    conduits_df['MaxFlow'] = conduits_df['MaxFlow'].fillna('0')
    xsections_df = conduits_raw[xsections_cols].copy()
    xsections_df['Culvert'] = xsections_df['Culvert'].fillna('')
    if any(xsections_df['XsectShape'] == 'IRREGULAR') or any(xsections_df['XsectShape'] == 'CUSTOM') or any(xsections_df['XsectShape'] == 'STREET'):
        if 'Shp_Trnsct' not in conduits_raw.columns:
            raise QgsProcessingException('Column \"Shp_Trnsct\" is missing for IRREGULAR, CUSTOM or STREET XsectShape')
        else:
            xsections_df.loc[xsections_df['XsectShape'] == 'IRREGULAR', 'Geom1'] = conduits_raw.loc[xsections_df['XsectShape'] == 'IRREGULAR', 'Shp_Trnsct']
            xsections_df.loc[xsections_df['XsectShape'] == 'STREET', 'Geom1'] = conduits_raw.loc[xsections_df['XsectShape'] == 'STREET', 'Shp_Trnsct']
            xsections_df.loc[xsections_df['XsectShape'] == 'CUSTOM', 'Geom2'] = conduits_raw.loc[xsections_df['XsectShape'] == 'CUSTOM', 'Shp_Trnsct']

    def fill_empty_xsects(xs_row, col):
        if col == 'Barrels':
            if xs_row['XsectShape'] in ['IRREGULAR', 'STREET']:
                return ''
            else:
                if pd.isna(xs_row[col]):
                    return '1'
                else:
                    return int(xs_row[col])
        else:
            if xs_row['XsectShape'] in ['IRREGULAR', 'STREET']:
                return ''
            else:
                if pd.isna(xs_row[col]):
                    return '0'
                else:
                    return xs_row[col]
    xsections_df['Geom2'] = xsections_df.apply(lambda x: fill_empty_xsects(x, 'Geom2'), axis=1)
    xsections_df['Geom3'] = xsections_df.apply(lambda x: fill_empty_xsects(x, 'Geom3'), axis=1)
    xsections_df['Geom4'] = xsections_df.apply(lambda x: fill_empty_xsects(x, 'Geom4'), axis=1)
    xsections_df['Barrels'] = xsections_df.apply(lambda x: fill_empty_xsects(x, 'Barrels'), axis=1)
    losses_df = conduits_raw[losses_cols].copy()
    losses_df['FlapGate'] = losses_df['FlapGate'].fillna('NO')
    losses_df['Seepage'] = losses_df['Seepage'].fillna('0')
    losses_df['Kentry'] = losses_df['Kentry'].fillna('0')
    losses_df['Kexit'] = losses_df['Kexit'].fillna('0')
    losses_df['Kavg'] = losses_df['Kavg'].fillna('0')
    return conduits_df, xsections_df, losses_df


# Streets
def get_street_from_tables(streets_inlets_raw):
    streets_df = streets_inlets_raw['STREETS']
    inlets_usage_df = streets_inlets_raw['INLET_USAGE']
    inlets_usage_df['Placement'] = inlets_usage_df['Placement'].fillna('')  # for automatic placement
    # inlets
    inlets_raw = streets_inlets_raw['INLETS']
    inlets_df = inlets_raw.copy()

    def inl_type_adjustment(inl_row):
        in_type_i = inl_row['Type']
        cols_needed_i = inl_types_def[in_type_i]
        if len(cols_needed_i) == 1:  # curve
            return inl_row[cols_needed_i[0]], '', '', '', ''
        elif len(cols_needed_i) == 2:  # Drop curb or slotted
            return inl_row[cols_needed_i[0]], inl_row[cols_needed_i[1]], '', '', ''
        else:
            if inl_row[cols_needed_i[2]] == 'GENERIC':
                return inl_row[cols_needed_i[0]], inl_row[cols_needed_i[1]],  inl_row[cols_needed_i[2]], inl_row['OpenFract'], inl_row['SplashVel']
            else:
                return inl_row[cols_needed_i[0]], inl_row[cols_needed_i[1]],  inl_row[cols_needed_i[2]], '', ''
    inlets_df[['Shape1', 'Shape2', 'Shape3', 'Shape4', 'Shape5']] = [inl_type_adjustment(inlets_df.loc[i]) for i in inlets_df.index]
    inlets_df = inlets_df.drop(columns=all_inl_type_cols)
    return streets_df, inlets_df, inlets_usage_df


# geometries
def del_first_last_vt(link):
    """
    deletes first and last vertex as it is already in nodes coordinates
    :param list link
    :return: list
    """
    return link[1:-1]


# pumps
def get_pumps_from_shapefile(pumps_raw):
    """prepares pumps data for writing an input file"""
    # check if all columns exist
    pumps_cols = list(def_qgis_fields_dict['PUMPS'].keys())
    pumps_layer_name = 'Pumps Layer'
    check_columns(
        pumps_layer_name,
        pumps_cols,
        pumps_raw.keys()
    )
    pumps_df = pumps_raw[pumps_cols].copy()
    pumps_df['Name'] = [str(x) for x in pumps_df['Name']]
    pumps_df['PumpCurve'] = pumps_df['PumpCurve'].fillna('*')
    pumps_df['Status'] = pumps_df['Status'].fillna('ON')
    pumps_df['Startup'] = pumps_df['Startup'].fillna('0')
    pumps_df['Shutoff'] = pumps_df['Shutoff'].fillna('0')
    pumps_df = pumps_df.reset_index(drop=True)
    return pumps_df


# weirs
weirs_shape_dict = {
    'TRANSVERSE': 'RECT_OPEN',
    'SIDEFLOW': 'RECT_OPEN',
    'V-NOTCH': 'TRIANGULAR',
    'TRAPEZOIDAL': 'TRAPEZOIDAL',
    'ROADWAY': 'RECT_OPEN'
}


def get_weirs_from_shapefile(weirs_raw):
    """prepares weirs data for writing an input file"""
    weirs_qgis_cols = list(def_qgis_fields_dict['WEIRS'].keys())
    weirs_inp_cols = def_sections_dict['WEIRS']
    weirs_layer_name = 'Weirs Layer'
    check_columns(
        weirs_layer_name,
        weirs_qgis_cols,
        weirs_raw.columns
    )
    weirs_df = weirs_raw.copy()
    weirs_df['Name'] = [str(x) for x in weirs_df['Name']]
    weirs_df['CrestHeigh'] = weirs_df['CrestHeigh'].fillna('*')
    weirs_df['RoadWidth'] = weirs_df['RoadWidth'].fillna('*')
    weirs_df['RoadSurf'] = weirs_df['RoadSurf'].fillna('*')
    weirs_df['CoeffCurve'] = weirs_df['CoeffCurve'].fillna('')
    weirs_df['FlapGate'] = weirs_df['FlapGate'].fillna('NO')
    weirs_df['EndContrac'] = weirs_df['EndContrac'].fillna('0')
    weirs_df['EndCoeff'] = weirs_df['EndCoeff'].fillna('0')
    weirs_df['Surcharge'] = weirs_df['Surcharge'].fillna('YES')
    weirs_df = weirs_df[weirs_inp_cols]
    weirs_raw = weirs_raw.rename(
        columns={
            'Height': 'Geom1',
            'Length': 'Geom2',
            'SideSlope': 'Geom3'
        }
    )
    weirs_raw['XsectShape'] = [weirs_shape_dict[x] for x in weirs_raw['Type']]
    weirs_raw['Geom3'] = weirs_raw['Geom3'].fillna('0')
    weirs_raw['Geom4'] = weirs_raw['Geom3']
    xsections_df = weirs_raw[[
        'Name',
        'XsectShape',
        'Geom1',
        'Geom2',
        'Geom3',
        'Geom4'
    ]].copy()
    xsections_df['Barrels'] = ''
    xsections_df['Culvert'] = ''
    return weirs_df, xsections_df


# orifices
def get_orifices_from_shapefile(orifices_raw):
    """
    prepares orifices data for writing an input file
    param: pd.DataFrame orifices_raw
    """
    # check if columns exist
    all_orifices_cols = list(def_qgis_fields_dict['ORIFICES'].keys())
    orifices_layer_name = 'Orifices Layer'
    check_columns(
        orifices_layer_name,
        all_orifices_cols,
        orifices_raw.columns
    )
    orifices_inp_cols = def_sections_dict['ORIFICES']
    orifices_df = orifices_raw.copy()
    orifices_df['Name'] = [str(x) for x in orifices_df['Name']]
    orifices_df['InOffset'] = orifices_df['InOffset'].fillna('*')
    orifices_df['FlapGate'] = orifices_df['FlapGate'].fillna('NO')
    orifices_df['CloseTime'] = orifices_df['CloseTime'].fillna('0')
    orifices_df = orifices_df[orifices_inp_cols]
    orifices_raw['Geom1'] = orifices_raw['Height']
    orifices_raw['Geom2'] = orifices_raw['Width']
    orifices_raw['Geom2'] = orifices_raw['Geom2'].fillna('0')
    orifices_raw['Geom3'] = 0
    orifices_raw['Geom4'] = 0
    xsections_df = orifices_raw[[
        'Name',
        'XsectShape',
        'Geom1',
        'Geom2',
        'Geom3',
        'Geom4'
    ]].copy()
    xsections_df['Barrels'] = ''
    xsections_df['Culvert'] = ''
    return orifices_df, xsections_df


# outlets
def get_outlets_from_shapefile(outlets_raw):
    """prepares outlets data for writing an input file"""
    def get_outl_curve(outl_row):
        """selects curve data according to rating curve type"""
        if outl_row['RateCurve'] in ['FUNCTIONAL/DEPTH', 'FUNCTIONAL/HEAD']:
            return outl_row['Qcoeff']
        else:
            return outl_row['CurveName']
    # check columns
    outlets_cols = list(def_qgis_fields_dict['OUTLETS'].keys())
    outlets_layer_name = 'Outlets Layer'
    check_columns(outlets_layer_name,
                  outlets_cols,
                  outlets_raw.keys())
    outlets_raw['Name'] = [str(x) for x in outlets_raw['Name']]
    outlets_raw['Qcoeff'] = outlets_raw['Qcoeff'].fillna(1)
    outlets_raw['CurveName'] = outlets_raw['CurveName'].fillna('*')
    outlets_raw['FlapGate'] = outlets_raw['FlapGate'].fillna('NO')
    outlets_raw['QCurve'] = [get_outl_curve(outlets_raw.loc[i]) for i in outlets_raw.index]
    outlets_df = outlets_raw[[
        'Name',
        'FromNode',
        'ToNode',
        'InOffset',
        'RateCurve',
        'QCurve',
        'Qexpon',
        'FlapGate'
    ]]
    return outlets_df


# Transects
def get_transects_from_table(transects_raw):
    """writes strings for transects"""
    tr_data = transects_raw['Data']
    tr_vals = transects_raw['XSections']

    def write_transect_lines(T_Name):
        tr_data_i = tr_data[tr_data['TransectName'] == T_Name]
        tr_vals_i = tr_vals[tr_vals['TransectName'] == T_Name]
        tr_count_i = len(tr_vals_i)
        tr_roughn_i = tr_data_i[['RoughnessLeftBank', 'RoughnessRightBank', 'RoughnessChannel']].values.tolist()[0]
        tr_bank_i = tr_data_i[['BankStationLeft', 'BankStationRight']].values.tolist()[0]
        tr_modifier_i = tr_data_i[['ModifierMeander', 'ModifierStations', 'ModifierElevations']].values.tolist()[0]
        NC_data_i = ['NC']+tr_roughn_i
        NC_string_i = '    '.join([str(i) for i in NC_data_i])
        X1_data_i = ['X1', T_Name, '', tr_count_i] + tr_bank_i + [0.0, 0.0] + tr_modifier_i
        X1_string_i = '    '.join([str(i) for i in X1_data_i])
        tr_vals_i_list = [tr_vals_i.loc[i, ['Elevation', 'Station']].to_list() for i in tr_vals_i.index]
        tr_vals_i_list = [str(x) for sublist in tr_vals_i_list for x in sublist]
        tr_vals_i_list_splitted = [tr_vals_i_list[i: i + 10] for i in range(0, len(tr_vals_i_list), 10)]
        tr_vals_i_list_splitted = [['GR'] + x for x in tr_vals_i_list_splitted]

        def concat_tr_str(tr_line):
            return '    '.join([str(i) for i in tr_line])
        GR_strings_i = [concat_tr_str(x) for x in tr_vals_i_list_splitted]
        GR_strings_i_joined = '\n'.join(GR_strings_i)
        tr_string = NC_string_i+'\n'+X1_string_i+'\n'+GR_strings_i_joined
        return tr_string
    transects_string_list = [write_transect_lines(x) for x in tr_data['TransectName']]
    return transects_string_list


# Import
# Inlets
def get_inlet_from_inp(inlets_raw_line):
    """
    converts an inlet string into a list of inlet values
    :param list inlets_raw_line
    :return: list
    """
    init_elems = inlets_raw_line[:2]
    inl_type_i = inlets_raw_line[1]
    inl_cols_i = inl_types_def[inl_type_i]
    inl_vals_i = {col: inlets_raw_line[2+i] for i, col in enumerate(inl_cols_i)}
    inl_missing = {col_0: np.nan for col_0 in all_inl_type_cols if col_0 not in inl_vals_i.keys()}
    inl_vals_i.update(inl_missing)
    # adjustment for generec shapes
    if inl_vals_i['Shape'] == 'GENERIC':
        inl_vals_i['OpenFract'] = inlets_raw_line[5]
        inl_vals_i['OpenFract'] = inlets_raw_line[6]
    type_elems = [inl_vals_i[t_c] for t_c in all_inl_type_cols]
    # resulting line
    inl_line_adjusted = init_elems + type_elems
    return (inl_line_adjusted)


# xsections
def adjust_xsection_df(all_xsections):  # no feedback!
    """
    fills the column 'Shp_Transct' in the xsections dataframe
    :param pd.DataFrame all_xsections
    :return: pd.DataFrame
    """
    all_xsections['Shp_Trnsct'] = np.nan
    all_xsections.loc[all_xsections['XsectShape'] == 'STREET', 'Shp_Trnsct'] = all_xsections.loc[all_xsections['XsectShape'] == 'STREET', 'Geom1']
    all_xsections.loc[all_xsections['XsectShape'] == 'STREET', 'Geom1'] = np.nan
    all_xsections.loc[all_xsections['XsectShape'] == 'IRREGULAR', 'Shp_Trnsct'] = all_xsections.loc[all_xsections['XsectShape'] == 'IRREGULAR', 'Geom1']
    all_xsections.loc[all_xsections['XsectShape'] == 'IRREGULAR', 'Geom1'] = np.nan
    all_xsections.loc[all_xsections['XsectShape'] == 'CUSTOM', 'Shp_Trnsct'] = all_xsections.loc[all_xsections['XsectShape'] == 'CUSTOM', 'Geom2']
    all_xsections.loc[all_xsections['XsectShape'] == 'CUSTOM', 'Geom2'] = np.nan
    return all_xsections


# outlets
def adjust_outlets_list(outl_list_i, feedback):
    """
    adds two np.nan if outlets is type TABULAR
    :param list outl_list_i
    :param QgsProcessingFeedback feedback
    """
    if outl_list_i[4].startswith('TABULAR'):
        curve_name = outl_list_i[5]
        flap_gate = outl_list_i[6]
        outl_list_i[:5]
        return outl_list_i[:5]+[np.nan, np.nan]+[flap_gate, curve_name]
    else:
        return outl_list_i+[np.nan]


# geometry
def get_line_from_points(
    line_name,
    from_node,
    to_node,
    dict_all_vals
):
    """
    :param str line_name
    :param str from_node
    :param str to_node
    :param dict dict_all_vals
    :return: list
    """
    all_geoms = dict_all_vals['COORDINATES']['data']
    all_vertices = dict_all_vals['VERTICES']['data']
    if (
        (from_node not in all_geoms.index)
        or (to_node not in all_geoms.index)
    ):
        line_geom = NULL
    else:
        verts = all_vertices[all_vertices.index == line_name]
        if len(verts) > 0:
            l_verts = verts.reset_index(drop=True)
            l_verts_points = [x.asPoint() for x in l_verts['geometry']]
        else:
            l_verts_points = []
        from_geom = all_geoms.loc[from_node, 'geometry']
        from_point = from_geom.asPoint()
        to_geom = all_geoms.loc[to_node, 'geometry']
        to_point = to_geom.asPoint()
        l_all_verts = [from_point]+l_verts_points+[to_point]
        line_geom = QgsGeometry.fromPolylineXY(l_all_verts)
    return [line_name, line_geom]


def create_lines_for_section(df_processed, dict_all_vals, feedback):
    """
    converts a point x-y-list into POINT-df
    :param pd.DataFrame df_processed
    :param dict dict_all_vals
    :param QgsProcessingFeedback feedback
    :return: pd.DataFrame
    """
    lines_created = [
        get_line_from_points(n, f, t, dict_all_vals) for n, f, t in zip(
            df_processed['Name'],
            df_processed['FromNode'],
            df_processed['ToNode']
            )
    ]
    lines_created = pd.DataFrame(
        lines_created,
        columns=['Name', 'geometry']
    ).set_index('Name')
    return lines_created
