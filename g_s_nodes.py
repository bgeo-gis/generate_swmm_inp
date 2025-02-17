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
__date__ = '2024-03-20'
__copyright__ = '(C) 2021 by Jannik Schilling'

import numpy as np
import pandas as pd
from qgis.core import (
    QgsProcessingException,
    QgsGeometry
)
from .g_s_defaults import (
    def_qgis_fields_dict,
    def_sections_dict,
    def_tables_dict
)
from .g_s_export_helpers import (
    check_columns
)

# Definitions for Storages
st_types_def = {
    'FUNCTIONAL': ['Coeff', 'Exponent', 'Constant'],
    'TABULAR': ['Curve'],
    'PYRAMIDAL': ['MajorAxis', 'MinorAxis', 'SideSlope'],
    'PARABOLIC': ['MajorAxis', 'MinorAxis', 'SurfHeight'],
    'CONICAL': ['MajorAxis', 'MinorAxis', 'SideSlope'],
    'CYLINDRICAL': ['MajorAxis', 'MinorAxis']
}
all_st_type_cols = [
    'Curve',
    'Coeff',
    'Exponent',
    'Constant',
    'MajorAxis',
    'MinorAxis',
    'SideSlope',
    'SurfHeight'
]

# Export
#----------
# Junctions
def get_junctions_from_layer(junctions_raw):
    junctions_df = junctions_raw.copy()
    junctions_df['Name'] = [str(x) for x in junctions_df['Name']]
    junctions_df['MaxDepth'] = junctions_df['MaxDepth'].fillna(0)
    junctions_df['InitDepth'] = junctions_df['InitDepth'].fillna(0)
    junctions_df['SurDepth'] = junctions_df['SurDepth'].fillna(0)
    junctions_df['Aponded'] = junctions_df['Aponded'].fillna(0)
    junctions_inp_cols = def_sections_dict['JUNCTIONS']
    junctions_df = junctions_df[junctions_inp_cols]
    return junctions_df
    
# dividers
def get_dividers_from_layer(dividers_raw):
    """
    adjusts dividers data
    :param pd.DataFrame dividers_raw
    """
    dividers_inp_cols = def_sections_dict['DIVIDERS']
    dividers_df = dividers_raw[dividers_inp_cols]
    dividers_df['Name'] = [str(x) for x in dividers_df['Name']]
    dividers_df['CutoffFlow'] = dividers_df['CutoffFlow'].fillna('')
    dividers_df['Curve'] = dividers_df['Curve'].fillna('')
    dividers_df['WeirMinFlo'] = dividers_df['WeirMinFlo'].fillna('')
    dividers_df['WeirMaxDep'] = dividers_df['WeirMaxDep'].fillna('')
    dividers_df['WeirCoeff'] = dividers_df['WeirCoeff'].fillna('')
    return dividers_df

# Outfalls
def get_outfalls_from_shapefile(outfalls_raw):
    """
    prepares a pandas.DataFrame for the export of OUTFALLS
    :param pd.DataFrame outfalls_raw
    :return: pd.DataFrame
    """
    outfalls_raw['Name'] = [str(x) for x in outfalls_raw['Name']]
    outfalls_raw.loc[outfalls_raw['Type'] == 'TIDAL', 'Data'] = outfalls_raw.loc[outfalls_raw['Type'] == 'TIDAL', 'Curve_TS']
    outfalls_raw.loc[outfalls_raw['Type'] == 'TIMESERIES', 'Data'] = outfalls_raw.loc[outfalls_raw['Type'] == 'TIMESERIES', 'Curve_TS']
    outfalls_raw.loc[outfalls_raw['Type'] == 'FIXED', 'Data'] = outfalls_raw.loc[outfalls_raw['Type'] == 'FIXED', 'FixedStage']
    outfalls_raw.loc[outfalls_raw['Type'] == 'FREE', 'Data'] = ''
    outfalls_raw.loc[outfalls_raw['Type'] == 'NORMAL', 'Data'] = ''
    outfalls_raw['RouteTo'] = outfalls_raw['RouteTo'].fillna('')
    outfalls_raw['FlapGate'] = outfalls_raw['FlapGate'].fillna('NO')
    outfalls_raw['Data'] = outfalls_raw['Data'].fillna('')
    return outfalls_raw

# Storages
def get_storages_from_layer(storages_raw):
    """
    creates a df for storages from raw storage data
    :param pd.DataFrame storages_raw
    :return: pd.DataFrame
    """
    storages_layer_name = 'Storages Layer'
    storage_df = storages_raw.copy()
    check_columns(storages_layer_name,
                  ['Type'],
                  storage_df.keys())
    occuring_storage_types = list(set(storages_raw['Type']))
    unknown_storage_types = [
        str(x) for x in occuring_storage_types if not x in st_types_def.keys()
    ]
    if len(unknown_storage_types) > 0:
        raise QgsProcessingException(
            'Unknown storage type(s) (-> field (\"Type\"): '
            + ', '.join(unknown_storage_types)
            + '. Please check if the correct file/layer was selected. '
            + '\"Type\" must be one of '
            + ', '.join(st_types_def.keys())
        )
    st_types_needed = list(set([col for s_t in occuring_storage_types for col in st_types_def[s_t]]))
    st_types_not_needed = [col for col in all_st_type_cols if col not in st_types_needed]
    storages_cols = list(def_qgis_fields_dict['STORAGE'].keys())
    storages_cols_needed = [col for col in storages_cols if col not in st_types_not_needed]
    check_columns(
        storages_layer_name,
        storages_cols_needed,
        storage_df.keys()
    )
    storage_df['Name'] = [str(x) for x in storage_df['Name']]

    def st_type_adjustment(st_row):
        st_type_i = st_row['Type']
        cols_needed_i = st_types_def[st_type_i]
        if len(cols_needed_i) == 1:  # TABULAR
            return st_row[cols_needed_i[0]], '', ''
        elif len(cols_needed_i) == 2:  # CYLINDRICAL
            return st_row[cols_needed_i[0]], st_row[cols_needed_i[1]], 0
        else:
            return st_row[cols_needed_i[0]], st_row[cols_needed_i[1]], st_row[cols_needed_i[2]]
    storage_df[['Shape1', 'Shape2', 'Shape3']] = [st_type_adjustment(storage_df.loc[i]) for i in storage_df.index]
    storage_df['Psi'] = storage_df['Psi'].fillna('')
    storage_df['Ksat'] = storage_df['Ksat'].fillna('')
    storage_df['IMD'] = storage_df['IMD'].fillna('')
    storage_df['InitDepth'] = storage_df['InitDepth'].fillna(0)
    storage_df['SurDepth'] = storage_df['SurDepth'].fillna(0)
    storage_df['Fevap'] = storage_df['Fevap'].fillna(0)
    # drop and keep columns
    storage_df = storage_df.drop(columns=st_types_needed)
    storage_inp_cols = [
                'Name', 'Elevation', 'MaxDepth','InitDepth','Type',
                'Shape1','Shape2','Shape3','SurDepth','Fevap','Psi',
                'Ksat','IMD'
            ]
    storage_df[storage_inp_cols]
    return storage_df

# inflows
def compose_infl_dict(inflow, i, inf_type):
    """
    writes an inflow dict from a pd.df for direct and dry weather inflow
    :param pd.DataFrame inflow
    :param str i: name
    :param str inf_type
    :return: dict
    """
    if inf_type == 'Direct':
        i_dict = {
            'Name': i,
            'Constituent': inflow['Constituent'],
            'Time_Series': inflow['Time_Series'],
            'Type': inflow['Type'],
            'Mfactor': inflow['Units_Factor'],
            'Sfactor': inflow['Scale_Factor'],
            'Baseline': inflow['Baseline'],
            'Pattern': inflow['Baseline_Pattern']
        }
    if inf_type == 'Dry_Weather':  # dry weather
        i_dict = {
            'Name': i,
            'Constituent': inflow['Constituent'],
            'Baseline': inflow['Average_Value'],
            'Patterns': ' '.join([
                inflow['Time_Pattern1'],
                inflow['Time_Pattern2'],
                inflow['Time_Pattern3'],
                inflow['Time_Pattern4']
            ])
        }            
    return i_dict
        
# Hydrographs
def compose_hydrograph_df(hydrog):
        """
        creates a pd.Dataframe for evey hydrograph with short, medium
        and long term parameters in different rows which can directly be 
        printed into the input file
        :param str i: hydrograph name
        :param pd.DataFrame hydrog
        :return: pd.DataFrame        
        """
        h_name = hydrog['Name']
        df_rg = pd.DataFrame(
            {'Name': h_name, 'RG_Month': hydrog['Rain_Gage']},
            index = [0]
        )
        for i, t in enumerate(['Short', 'Medium', 'Long']):
            df_i = pd.DataFrame(
                {
                    'Name': h_name,
                    'RG_Month': hydrog['Months'],
                    'Response': t,
                    'R': hydrog['R_'+t+'Term'],
                    'T': hydrog['T_'+t+'Term'],
                    'K': hydrog['K_'+t+'Term'],
                    'D_max': hydrog['D_max_'+t+'Term'],
                    'D_recovery': hydrog['D_recovery_'+t+'Term'],
                    'D_init': hydrog['D_init_'+t+'Term']
                },
                index = [i+1]
            )
            df_rg = pd.concat([df_rg, df_i])
        return df_rg

# Inflows
def get_inflows_from_table(inflows_raw, all_nodes, feedback):
    """
    generates a dict for direct inflow and
    dry weather inflow from tables in "inflows_raw"
    :param dict inflows_raw
    :param list all_nodes
    :param QgsProcessingFeedback feedback
    """       
    # create empty dicts / pd.DataFrame in case no flow is given
    inflow_dict = {}
    dwf_dict = {}
    hydrogr_df = pd.DataFrame()
    rdii_df = pd.DataFrame()
    for inflow_type in ['Direct', 'Dry_Weather', 'Hydrographs', 'RDII']:
        inflow_df = inflows_raw[inflow_type]
        if not inflow_df.empty:
            # check if all columns exits
            inflow_cols_needed = list(def_tables_dict['INFLOWS']['tables'][inflow_type].keys())
            table_name = inflow_type + ' table'
            check_columns(
                table_name,
                inflow_cols_needed,
                inflow_df.columns
            )
            # delete inflows for nodes which do no exist
            if inflow_type == 'RDII':
                inflow_df['Name'] = inflow_df['Node']
            inflow_df = inflow_df[inflow_df['Name'] != ";"]
            inflow_df['Name'] = [str(x) for x in inflow_df['Name']]
            if inflow_type != 'Hydrographs':
                missing_nodes = list(inflow_df.loc[~inflow_df['Name'].isin(all_nodes),'Name'])
                if len(missing_nodes) > 0:
                    feedback.pushWarning(
                        'Warning: Missing nodes for inflows: '
                        + ', '.join([str(x) for x in missing_nodes])
                        + '. Please check if the correct layers were selected.'
                        + 'The inflows will not be written into the input file '
                        + 'to avoid errors in SWMM'
                    )
                inflow_df = inflow_df[inflow_df['Name'].isin(all_nodes)]
                inflow_df = inflow_df[pd.notna(inflow_df['Name'])]
            inflow_df = inflow_df.fillna('""')
            if not inflow_df.empty:
                # prepare a dict with node names and constituents
                a_l = inflow_df['Name'].tolist()
                if inflow_type in ['Direct', 'Dry_Weather']:
                    b_l = inflow_df['Constituent'].tolist()
                    inflow_df['temp'] = [str(a) + '    ' + str(b) for a, b in zip(a_l, b_l)]
                    inflow_df.set_index(keys=['temp'], inplace=True)
                    if inflow_type == 'Direct':
                        inflow_dict = {
                            i: compose_infl_dict(
                                inflow_df.loc[i, :],
                                i,
                                inflow_type
                            ) for i in inflow_df.index
                        }
                    else:  # Dry_Weather
                        dwf_dict = {
                            i: compose_infl_dict(
                                inflow_df.loc[i, :],
                                i,
                                inflow_type
                            ) for i in inflow_df.index
                        }
                elif inflow_type == 'Hydrographs':
                    # to do: check if rain gage exists
                    hydrog_list = [
                        compose_hydrograph_df(
                            inflow_df.loc[i, :]
                        ) for i in inflow_df.index
                    ]
                    hydrogr_df = pd.concat(hydrog_list)
                    hydrogr_df = hydrogr_df.fillna('')
                else:  # rdii
                    rdii_df = inflow_df
                    rdii_df = rdii_df[['Node', 'UnitHydrograph', 'SewerArea']]
                                   
    return dwf_dict, inflow_dict, hydrogr_df, rdii_df


# Import
#-------
# Outfalls
def get_outfalls_from_inp(outfalls_line, feedback):
    """
    Prepares an outfall element
    :param list outfalls_line
    :param QgsProcessingFeedback feedback
    :return: list
    """
    if outfalls_line[2] in ['FREE', 'NORMAL']:
        outfalls_line.insert(3, np.nan)
        outfalls_line.insert(4, np.nan)
    if outfalls_line[2] == 'FIXED':
        outfalls_line.insert(4, np.nan)
    if outfalls_line[2] in ['TIDAL', 'TIMESERIES']:
        outfalls_line.insert(3, np.nan)
    return outfalls_line
    
# Dividers
def get_dividers_from_inp(divider_line, feedback):
    """
    Prepares a divider element
    :param list divider_line
    :param QgsProcessingFeedback feedback
    :return: list
    """
    if divider_line[3] == 'OVERFLOW':
        for pos in [4, 5, 6, 7, 8]:
            divider_line.insert(pos, np.nan)
    if divider_line[3] == 'CUTOFF':
        for pos in [5, 6, 7, 8]:
            divider_line.insert(pos, np.nan)
    if divider_line[3] == 'TABULAR':
        for pos in [4, 6, 7, 8]:
            divider_line.insert(pos, np.nan)
    if divider_line[3] == 'WEIR':
        for pos in [4, 5]:
            divider_line.insert(pos, np.nan)
    return divider_line

# Storage
def get_storages_from_inp(st_raw_line, feedback):
    """
    adjusts the inp line according to the storage type
    :param list st_raw_line
    :param QgsProcessingFeedback feedback
    :return: list
    """
    init_elems = st_raw_line[:5]
    st_type_i = st_raw_line[4]
    st_cols_i = st_types_def[st_type_i]
    st_vals_i = {col: st_raw_line[5+i] for i, col in enumerate(st_cols_i)}
    st_missing = {col_0: np.nan for col_0 in all_st_type_cols if col_0 not in st_vals_i.keys()}
    st_vals_i.update(st_missing)
    type_elems = [st_vals_i[t_c] for t_c in all_st_type_cols]
    # Seepage and Evaporation loss
    if st_type_i == 'TABULAR':
        sur_elems = st_raw_line[6:]
    else:
        sur_elems = st_raw_line[8:]
    if len(sur_elems) == 2:
        sur_elems = sur_elems + [np.nan, np.nan, np.nan]
    # resulting line
    st_line_adjusted = init_elems + type_elems + sur_elems
    return(st_line_adjusted)
    
# Hydrographs
def get_hydrogrphs(hg_name, df_hydrographs_raw):
    '''
    creates a flat hydrograph df
    :param str hg_name
    :param pd.DataFrame df_hydrographs_raw
    :return: pd.DataFrame
    '''
    subdf = df_hydrographs_raw[df_hydrographs_raw['Name'] == hg_name]
    hg_rg = subdf[pd.isna(subdf['Response'])]
    hg_rg = hg_rg[['Name', 'RG_Month']].rename(columns={'RG_Month': 'Rain_Gage'})
    for t in ['Short', 'Medium', 'Long']:
        hg_i = subdf[subdf['Response'] == t]
        if t == 'Short':
            hg_rg['Months'] = list(hg_i['RG_Month'])[0]
        hg_i = hg_i.drop(columns = ['RG_Month', 'Response'])
        ren_dict = {c: c+'_'+t+'Term' for c in hg_i.columns if c != 'Name'}
        hg_i = hg_i.rename(columns=ren_dict)
        hg_rg = hg_rg.join(
            hg_i.set_index('Name'),
            on='Name'
        )
    return (hg_rg)

# Geometry helpers
def create_point_from_x_y(sr, i, n, feedback):
    """
    converts x and y coordinates from a pd.Series to a QgsPoint geometry
    :param pd.Series sr
    :param int 1
    :param int n: length of data
    :param QgsProcessingFeedback feedback
    :return: list
    """
    x_coord = sr['X_Coord']
    y_coord = sr['Y_Coord']
    geom = QgsGeometry.fromWkt(
        'POINT(' + str(x_coord) + ' '+str(y_coord) + ')'
    )
    feedback.setProgress(((i+1)/n)*100)
    if feedback.isCanceled():
        pass
    return [sr['Name'], geom]

def create_points_df(data, feedback):
    """
    converts a point x-y-list into POINT-df
    :param pd.DataFrame data
    :param QgsProcessingFeedback feedback
    :return: pd.DataFrame
    """
    n = len(data)
    if n > 0:
        all_geoms = [create_point_from_x_y(
            data.loc[i,],
            i,
            n,
            feedback) for i in data.index] # point geometries
        df_out = pd.DataFrame(all_geoms, columns=['Name', 'geometry']).set_index('Name')
    else:
        df_out = pd.DataFrame(columns = ['Name', 'geometry']).set_index('Name')
    return df_out


def add_z_to_points(sr):
    """
    adds the elevation to a point geometry
    :param PandasSeries sr: one line of the DataFrame already with geometry
    :return: QgsGeometry
    """
    f_geometry = sr['geometry']
    z_coord = sr['Elevation']
    f_geometry_string_z = f_geometry.asWkt()[:-1]+' '+str(z_coord)+')'
    f_geometry_z = QgsGeometry.fromWkt(f_geometry_string_z)
    return f_geometry_z
