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
__date__ = '2022-04-28'
__copyright__ = '(C) 2022 by Jannik Schilling'


import numpy as np
import pandas as pd
from datetime import datetime
from qgis.core import (
    Qgis,
    QgsWkbTypes,
    QgsProcessingException,
    QgsEditorWidgetSetup
)
from .g_s_defaults import def_tables_dict

## geometry functions
def get_coords_from_geometry(df):
    """
    extracts coords from any gpd.geodataframe
    :param pd.DataFrame df
    """
    
    geom_point_types = {
        'Point':'simple',
        'PointM':'simple',
        'PointZ':'simple',
        'PointZM':'simple'
    }
    geom_line_types = {
        'LineString':'simple',
        'LineStringZ':'simple',
        'LineStringZM':'simple',
        'LineStringM':'simple',
        'MultiLineString':'multi',
        'MultiLineStringM':'multi',
        'MultiLineStringZ':'multi',
        'MultiLineStringZM':'multi'
    }
    geom_polygon_types = {
        'Polygon':'simple',
        'PolygonZ':'simple',
        'PolygonM':'simple',
        'PolygonZM':'simple',
        'MultiPolygon':'multi',
        'MultiPolygonM':'multi',
        'MultiPolygonZ':'multi',
        'MultiPolygonZM':'multi'
    }
    point_t_names = list(geom_point_types.keys())
    line_t_names = list(geom_line_types.keys())
    polygon_t_names = list(geom_polygon_types.keys())
    
    def extract_xy_from_simple_line(line_simple):
        """extracts x and y coordinates from a LineString"""
        xy_arr = np.dstack((p.x(),p.y()) for p in line_simple)[0]
        xy_df = pd.DataFrame(xy_arr.T,columns = ['x','y'])
        return xy_df
    def extract_xy_from_line(line_row):
        """extraxts xy from LineString or MultiLineString"""
        act_line_type = QgsWkbTypes.displayString(line_row.wkbType())
        simple_or_multi = geom_line_types[act_line_type]
        if simple_or_multi == 'simple':
            return extract_xy_from_simple_line(line_row.asPolyline())
        if simple_or_multi == 'multi':
            xy_list = [extract_xy_from_simple_line(line_simple) for line_simple in line_row.asMultiPolyline()]
            return pd.concat(xy_list, ignore_index=True)
            
    if all(QgsWkbTypes.displayString(g_type.wkbType()) in point_t_names for g_type in df.geometry):
        df['X_Coord'] = [str(df_row.asPoint().x()) for df_row in df['geometry']]
        df['Y_Coord'] = [str(df_row.asPoint().y()) for df_row in df['geometry']]
        return df['X_Coord'],df['Y_Coord']
    elif all(QgsWkbTypes.displayString(g_type.wkbType()) in line_t_names for g_type in df.geometry):
        return {na:extract_xy_from_line(geom) for geom,na in zip(df.geometry,df.Name)}
    elif all(QgsWkbTypes.displayString(g_type.wkbType()) in polygon_t_names for g_type in df.geometry):
        def extract_xy_from_area(geom_row):
            """extraxts xy from polygon geometries"""
            xy_arr = np.dstack((v.x(),v.y()) for v in geom_row.vertices())[0]
            xy_df = pd.DataFrame(xy_arr.T,columns = ['x','y'])
            return xy_df
        return {na:extract_xy_from_area(ge) for ge,na in zip(df.geometry,df.Name)}
    else:
        raise QgsProcessingException('Geometry type of one or more features could not be handled')

def get_point_from_x_y(sr):
    """
    converts x and y coordinates from a pd.Series to a QgsPoint geometry
    :param pd.Series sr
    """
    from qgis.core import QgsGeometry
    x_coord = sr['X_Coord']
    y_coord = sr['Y_Coord']
    geom = QgsGeometry.fromWkt('POINT('+str(x_coord)+' '+str(y_coord)+')')
    return [sr['Name'],geom]
    
    

    

## functions for data in tables
def get_curves_from_table(curves_raw, name_col):
    """
    generates curve data for the input file from tables (curve_raw)
    :param pd.DataFrame curve_raw
    :param str name_col
    """
    curve_types = list(def_tables_dict['CURVES']['tables'].keys())
    curve_dict = dict()
    for curve_type in curve_types:
        if curve_type in curves_raw.keys():
            curve_df = curves_raw[curve_type]
            if len(curve_df.columns) > 3:
                curve_df = curve_df[curve_df.columns[:3]]
            curve_df = curve_df[curve_df[name_col] != ";"]
            curve_df = curve_df[pd.notna(curve_df[name_col])]
            if curve_df.empty:
                pass
            else:
                curve_df.set_index(keys=[name_col], inplace=True)
                for i in curve_df.index.unique():
                    curve = curve_df[curve_df.index == i]
                    curve = curve.reset_index(drop=True)
                    curve_dict[i] = {'Name':i, 'Type':curve_type,'frame':curve}
    return(curve_dict)
    

def get_patterns_from_table(patterns_raw, name_col):
    """
    generates a pattern dict for the input file from tables (patterns_raw)
    :param pd.DataFrame patterns_raw
    :param str name_col
    """
    pattern_types = def_tables_dict['PATTERNS']['tables'].keys()
    pattern_dict = {}
    for pattern_type in pattern_types:
        pattern_cols = def_tables_dict['PATTERNS']['tables'][pattern_type].keys()
        pattern_df = patterns_raw[pattern_type]
        check_columns('Patterns Table', pattern_cols, pattern_df.columns)
        pattern_df = pattern_df[pattern_df[name_col] != ";"]
        pattern_df = pattern_df[pd.notna(pattern_df[name_col])]
        if pattern_df.empty:
            pass
        else:
            pattern_df.set_index(keys=[name_col], inplace=True)
            for i in pattern_df.index.unique():
                pattern = pattern_df[pattern_df.index == i]
                pattern = pattern.drop(columns = pattern.columns[0])
                pattern = pattern.reset_index(drop=True)
                pattern_dict[i] = {'Name':i, 'Type':pattern_type,'Factors':pattern}
    return(pattern_dict)
    
def adjust_datetime(
    dt_column, 
    str_input_formats,
    str_output_format):
    """
    converts time values (tries different formats) into another time string
    :param list or series dt_column: column in which the date or time is written
    :param list str_input_formats
    :param str str_output_format
    """
    try:
        # if already in a date or time format
        dt_column = [t.strftime(str_output_format) for t in dt_column]
        return dt_column
    except:
        # if given as string
        for st in str_input_formats:
            try:
                dt_column = [datetime.strptime(str(t),st) for t in dt_column]
                dt_column = [t.strftime(str_output_format) for t in dt_column]
            except:
                dt_column = [str(t) for t in dt_column]
            else:
                return dt_column
                break
    
def get_timeseries_from_table(ts_raw, name_col, feedback):
    """
    generates a timeseries dict for the input file from tables (ts_raw)
    :param pd.DataFrame ts_raw
    :param str name_col
    :param QgsProcessingFeedback feedback
    """
    ts_dict = dict()
    rg_ts_dict = dict()
    ts_raw = ts_raw[ts_raw[name_col] != ";"]
    if not 'File_Name' in ts_raw.columns:
        feedback.setProgressText('No external file is used in time series')
    #deprecated:
    if ('Type' in ts_raw.columns) and ('Format' in ts_raw.columns):
        feedback.reportError('Warning: The columns \"Type\" and \"Format\" will not be used any longer in future versions of the plugin. Creating rain gages from timeseries only is deprecated. Please create a rain gage layer instead. You can get an examplary layer from the default data set or have a look at the documentation file.')
    if ts_raw.empty:
        pass
    else:
        for i in ts_raw[name_col].unique():
            ts_df = ts_raw[ts_raw[name_col] == i]
            if 'File_Name' in ts_raw.columns and not all(pd.isna(ts_df['File_Name'])): # external time series
                    ts_df['Date'] = 'FILE'
                    ts_df['Time'] = ts_df['File_Name']
                    ts_df['Value'] = ''
            else:
                ts_df['Date'] = adjust_datetime(
                    ts_df['Date'],
                    ['%Y-%m-%d','%d/%m/%Y','%d.%m.%Y'],
                    '%m/%d/%Y'
                )
                ts_df['Time'] = adjust_datetime(
                    ts_df['Time'],
                    ['%H:%M:%S', '%H:%M', '%H'],
                    '%H:%M'
                )
            ts_description= ts_df['Description'].fillna('').unique()[0]
            ts_dict[i] = {
                'Name':i,
                'TimeSeries':ts_df[['Name','Date','Time','Value']], 
                'Description':ts_description
            }
    return(ts_dict)
    
    




## errors and feedback


def check_columns(swmm_data_file, cols_expected, cols_in_df):
    """
    checks if all columns are in a dataframe
    :param str swmm_data_file
    :param list cols_expected
    :param list cols_in_df
    """
    missing_cols = [x for x in cols_expected if x not in cols_in_df]
    if len(missing_cols) == 0:
        pass
    else:
        err_message = 'Missing columns in '+swmm_data_file+': '+', '.join(missing_cols)
        err_message = err_message+'. Plaese add columns or check if the correct file was selected. '
        err_message = err_message+'For further advice regarding columns, read the documentation file in the plugin folder.'
        raise QgsProcessingException(err_message)
        
        
# input widgets
def field_to_value_map(layer, field, list_values):
    """
    creates a drop down menue in QGIS layers
    :param str layer 
    :param str field
    :param list list_values
    """
    config = {'map' : list_values}
    widget_setup = QgsEditorWidgetSetup('ValueMap',config)
    field_idx = layer.fields().indexFromName(field)
    layer.setEditorWidgetSetup(field_idx, widget_setup)
