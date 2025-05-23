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
__date__ = '2023-05-09'
__copyright__ = '(C) 2021 by Jannik Schilling'

import pandas as pd
from qgis.PyQt.QtCore import QTime, QDate
from qgis.core import (
    QgsWkbTypes,
    QgsProcessingException
)
from .g_s_defaults import (
    annotation_field_name,
    def_tables_dict,
    def_sections_dict,
    annotation_field_name
)


def get_annotations_from_raw_df(df_raw):
    """
    Extract annotations / descriptions from the dataframe.

    :param df_raw: Raw dataframe containing the annotations.
    :type df_raw: pd.DataFrame
    :return: Dictionary of annotations.
    :rtype: dict
    """
    if annotation_field_name in df_raw.columns:
        annot_dict = {k: v for k, v in zip(df_raw['Name'], df_raw[annotation_field_name])}  
        annot_dict = {k: v for k, v in annot_dict.items() if pd.notna(v)}
        annot_dict = {k: v for k, v in annot_dict.items() if len(v) > 0}
    else:
        annot_dict = {}
    return annot_dict


def data_preparation(data_name, data_entry, export_params):
    """
    Prepare data for each data entry in the export_data dictionary.

    :param data_name: Name of the layer type or table type.
    :type data_name: str
    :param data_entry: Data entry dictionary.
    :type data_entry: dict
    :param export_params: Export parameters dictionary.
    :type export_params: dict
    :return: Dictionary of prepared data.
    :rtype: dict
    :raises QgsProcessingException: If data_name is not an is not one of OPTIONS, SUBCATCHMENTS, CONDUITS, PUMPS, WEIRS, OUTLETS, ORIFICES, JUNCTIONS, OUTFALLS, STORAGE, DIVIDERS or INFLOWS.
    """
    if data_name == 'OPTIONS':
        from .g_s_options import get_options_from_table
        (
            options_df,
            main_infiltration_method,
            link_offsets
        ) = get_options_from_table(
                data_entry['OPTIONS'].copy()
            )
        export_params['main_infiltration_method'] = main_infiltration_method
        export_params['link_offsets'] = link_offsets
        return {'OPTIONS': {'data': options_df}}
    
    elif data_name == 'SUBCATCHMENTS':
        from .g_s_subcatchments import get_subcatchments_from_layer
        subcatchments_df, subareas_df, infiltration_df = get_subcatchments_from_layer(
            data_entry.copy(),
            export_params
        )
        return {
            'SUBCATCHMENTS': {'data': subcatchments_df},
            'SUBAREAS': {'data': subareas_df},
            'INFILTRATION': {'data': infiltration_df}
        }
        
    elif data_name == 'CONDUITS':
        from .g_s_links import get_conduits_from_shapefile
        conduits_df, xsections_df, losses_df = get_conduits_from_shapefile(
            data_entry.copy()
        )
        return {
            'CONDUITS': {'data': conduits_df},
            'XSECTIONS': {'data': xsections_df},
            'LOSSES': {'data': losses_df}
        }
        
    elif data_name == 'PUMPS':
        from .g_s_links import get_pumps_from_shapefile
        pumps_df = get_pumps_from_shapefile(data_entry.copy())
        return {'PUMPS': {'data': pumps_df}}
        
    elif data_name == 'WEIRS':
        from .g_s_links import get_weirs_from_shapefile
        weirs_df, xsections_df = get_weirs_from_shapefile(data_entry.copy())
        return {
            'WEIRS': {'data': weirs_df},
            'XSECTIONS': {'data': xsections_df}
        }
        
    elif data_name == 'OUTLETS':
        from .g_s_links import get_outlets_from_shapefile
        outlets_df = get_outlets_from_shapefile(data_entry.copy())
        return {'OUTLETS': {'data': outlets_df}}
        
    elif data_name == 'ORIFICES':
        from .g_s_links import get_orifices_from_shapefile
        orifices_df, xsections_df = get_orifices_from_shapefile(data_entry.copy())
        return {
            'ORIFICES': {'data': orifices_df},
            'XSECTIONS': {'data': xsections_df}
        }
        
    elif data_name == 'JUNCTIONS':
        from .g_s_nodes import get_junctions_from_layer
        junctions_df = get_junctions_from_layer(data_entry.copy())
        return {'JUNCTIONS': {'data': junctions_df}}
        
    elif data_name == 'OUTFALLS':
        from .g_s_nodes import get_outfalls_from_shapefile
        outfalls_df = get_outfalls_from_shapefile(data_entry.copy())
        return {'OUTFALLS': {'data': outfalls_df}}
        
    elif data_name == 'STORAGE':
        from .g_s_nodes import get_storages_from_layer
        storages_df = get_storages_from_layer(data_entry.copy())
        return {'STORAGE': {'data': storages_df}}

    elif data_name == 'DIVIDERS':
        from .g_s_nodes import get_dividers_from_layer
        dividers_df = get_dividers_from_layer(data_entry.copy())
        return {'DIVIDERS': {'data': dividers_df}}

    elif data_name == 'INFLOWS':
        from .g_s_nodes import get_inflows_from_table
        dwf_dict, inflows_dict, hydrogr_df, rdii_df = get_inflows_from_table(
            data_entry.copy(),
            export_params['all_nodes'],
            feedback=export_params['feedback']
        )
        res_dict = {
            'INFLOWS': {'data': inflows_dict},
            'DWF': {'data': dwf_dict},
            'HYDROGRAPHS': {'data': hydrogr_df},
        }
        if len(rdii_df) > 0:
            if len(hydrogr_df) == 0:
                feedback.pushWarning(
                    'Warning: No hydrographs were provided for RDII'
                    + '. Please check if the correct file was selected '
                    + 'and the \"Hydrographs\" table is set up correctly. '
                    + 'The RDII section will not be written into the input file '
                    + 'to avoid errors in SWMM.'
                )
            else:
                needed_U_H = list(rdii_df['UnitHydrograph'])
                misshing_U_H = [h for h in needed_U_H if h not in list(hydrogr_df['Name'])]
                if len (misshing_U_H) > 0:
                    feedback.pushWarning(
                        'Warning: Missing hydrographs for RDII: '
                        + ', '.join([str(x) for x in misshing_U_H])
                        + '. \nPlease check if the correct file was selected '
                        + 'and the \"Hydrographs\" table is set up correctly. '
                        + 'The RDII section will not be written into the input file '
                        + 'to avoid errors in SWMM.'
                    )
                else:
                    res_dict['RDII'] = {'data': rdii_df}
        return res_dict

    elif data_name == 'STREETS':
        from .g_s_links import get_street_from_tables
        streets_df, inlets_df, inlet_usage_df = get_street_from_tables(
            data_entry.copy()
        )
        return {
            'STREETS': {'data': streets_df},
            'INLETS': {'data': inlets_df},
            'INLET_USAGE': {'data': inlet_usage_df}
        }
    
    elif data_name == 'CURVES':
        curves_dict = get_curves_from_table(
            data_entry.copy(),
            name_col='Name'
        )
        return {'CURVES': {'data': curves_dict}}
        
    elif data_name == 'PATTERNS':
        patterns_dict = get_patterns_from_table(
            data_entry.copy()
        )
        return {'PATTERNS': {'data': patterns_dict}}
        
    elif data_name == 'TIMESERIES':
        timeseries_dict = get_timeseries_from_table(
            data_entry['TIMESERIES'],
            name_col='Name',
            feedback=export_params['feedback']
        )
        return {'TIMESERIES': {'data': timeseries_dict}}



    elif data_name == 'QUALITY':
        from .g_s_quality import get_quality_params_from_table
        (
            pollutants_df,
            landuses_df,
            buildup_df,
            washoff_df,
            coverages_df,
            loadings_df
        ) = get_quality_params_from_table(
            data_entry.copy(),
            export_params['all_subcatchments']
        )
        return  {
            'POLLUTANTS':  {'data':pollutants_df},
            'LANDUSES':  {'data':landuses_df},
            'BUILDUP':  {'data':buildup_df},
            'WASHOFF':  {'data':washoff_df},
            'COVERAGES':  {'data':coverages_df},
            'LOADINGS':  {'data':loadings_df}
        }
    elif data_name == 'TRANSECTS':
        from .g_s_links import get_transects_from_table
        transects_string_list = get_transects_from_table(data_entry.copy())
        return {'TRANSECTS': {'data': transects_string_list}}

    elif data_name == 'RAINGAGES':
        from .g_s_subcatchments import get_raingage_from_qgis_row
        rg_features_df = data_entry.copy()
        rg_features_df = rg_features_df.apply(
                lambda x: get_raingage_from_qgis_row(x),
                axis=1
            )
        rg_inp_cols = def_sections_dict['RAINGAGES']
        rg_features_df = rg_features_df[rg_inp_cols]  # drop unnecessary
        return {'RAINGAGES': {'data': rg_features_df}}
        
    else:
        raise QgsProcessingException(f'Unknown data name: {data_name}')

# geometry functions
def check_missing_z(z_vals, coord_type, all_names, layer_name):
    """
    Check if there is a missing (=nan) value in the z-coordinates.
    
    :param z_vals: List / series of z-coordinates.
    :type z_vals: pd.Series
    :param coord_type: Description of the coordinate type.
    :type coord_type: string
    :param all_names: List-like with all occuring names of the objects.
    :type all_names: list/pd.Series
    :param layer_name: Name of the current layer.
    :type layer_name: str
    """
    missing_z = [str(name) for z, name in zip(z_vals, all_names) if pd.isna(z)]
    if missing_z:
        raise QgsProcessingException(
            f'Missing z-Coordinates for the following {coord_type} in layer {layer_name}: {", ".join(missing_z)}'
            '\nPlease check all required nodes and links or run the tool without z-coordinates'
        )

def use_z_if_available(
    df,
    coords,
    use_z_bool,
    feedback,
    link_offsets='ELEVATION',
    layer_name=None,
    coords_nodes=None,
):
    """
    Replaces Elevation or InOffset/OutOffset by Z_Coords if available.

    :param df: Dataframe with links or nodes to be adjusted.
    :type df: pd.DataFrame
    :param coords: Dictionary containing coordinates.
    :type coords: dict
    :param use_z_bool: Boolean indicating whether to use Z coordinates.
    :type use_z_bool: bool
    :param feedback: Feedback for processing.
    :type feedback: QgsProcessingFeedback
    :param link_offsets: Type of link offsets ('ELEVATION' or 'DEPTH').
    :type link_offsets: str
    :param layer_name: Name of the layer.
    :type layer_name: str
    :param coords_nodes: Dataframe containing coordinates of nodes.
    :type coords_nodes: pd.DataFrame
    :return: Updated dataframe.
    :rtype: pd.DataFrame
    """
    if list(coords.keys())[0] == 'VERTICES':  # lines
        coords_dict = coords['VERTICES']['data']
        if use_z_bool:
            vertices_z_in = [coords_dict[link_name]['Z_Coord'].tolist()[0] for link_name in df['Name']]
            vertices_z_out = [coords_dict[link_name]['Z_Coord'].tolist()[-1] for link_name in df['Name']]
            nodes_z_in = [
                coords_nodes.loc[
                    coords_nodes['Name']==node_name,
                    'Z_Coord'
                ].tolist()[0] for node_name in df['FromNode']
            ]
            nodes_z_out = [
                coords_nodes.loc[
                    coords_nodes['Name']==node_name,
                    'Z_Coord'
                ].tolist()[0] for node_name in df['ToNode']
            ]
            if link_offsets == 'ELEVATION':
                #df['InOffset'] = vertices_z_in
                #df['OutOffset'] = vertices_z_out
                df['InOffset'] = [str(v_in) if (v_in - n_in != 0) else '*' for v_in, n_in in zip(vertices_z_in, nodes_z_in)]
                df['OutOffset'] = [str(v_out) if (v_out - n_out != 0) else '*' for v_out, n_out in zip(vertices_z_out, nodes_z_out)]
            elif link_offsets == 'DEPTH':
                df['InOffset'] = [str(v_in - n_in) for v_in, n_in in zip(vertices_z_in, nodes_z_in)]
                df['OutOffset'] = [str(v_out - n_out) for v_out, n_out in zip(vertices_z_out, nodes_z_out)]
            else:
                raise QgsProcessingException(f'Unknown link offsets type: {link_offsets}')

            check_missing_z(
                df['InOffset'],
                'links (first vertices or connected nodes)',
                df['Name'],
                layer_name
            )
            check_missing_z(
                df['OutOffset'],
                'links (last vertices or connected nodes)',
                df['Name'],
                layer_name
            )
        elif coords_nodes is not None:
            if 'Z_Coord' in coords_nodes.columns:
                coords_nodes.drop("Z_Coord", axis=1, inplace=True)

    else:  # points
        coords_df = coords['COORDINATES']['data']
        if use_z_bool:
            elevation_with_z = list(coords_df['Z_Coord'])
            check_missing_z(
                elevation_with_z,
                'nodes',
                df['Name'],
                layer_name
            )
            df['Elevation'] = elevation_with_z
        else:
            coords_df.drop("Z_Coord", axis=1, inplace=True)

    return df


def get_coords_from_geometry(df):
    """
    Extract coordinates from any geodataframe.

    :param df: Dataframe containing geometry data.
    :type df: pd.DataFrame
    :return: Dictionary of extracted coordinates.
    :rtype: dict
    """
    geom_point_types = {
        'Point': 'simple',
        'PointM': 'simple',
        'PointZ': 'simple',
        'PointZM': 'simple'
    }
    geom_line_types = {
        'LineString': 'simple',
        'LineStringZ': 'simple',
        'LineStringZM': 'simple',
        'LineStringM': 'simple',
        'MultiLineString': 'multi',
        'MultiLineStringM': 'multi',
        'MultiLineStringZ': 'multi',
        'MultiLineStringZM': 'multi'
    }
    geom_polygon_types = {
        'Polygon': 'simple',
        'PolygonZ': 'simple',
        'PolygonM': 'simple',
        'PolygonZM': 'simple',
        'MultiPolygon': 'multi',
        'MultiPolygonM': 'multi',
        'MultiPolygonZ': 'multi',
        'MultiPolygonZM': 'multi'
    }
    point_t_names = list(geom_point_types.keys())
    line_t_names = list(geom_line_types.keys())
    polygon_t_names = list(geom_polygon_types.keys())

    # case: points
    if all(
        QgsWkbTypes.displayString(
            g_type.wkbType()
        ) in point_t_names for g_type in df.geometry
    ):
        extr_coords = [
            extract_xyz_from_simple_point(
                p_name,
                point_simple
            ) for p_name, point_simple in zip(
                df['Name'],
                df['geometry']
            )
        ]
        extr_coords_df = pd.DataFrame(
            extr_coords,
            columns=(
                ['Name', 'X_Coord', 'Y_Coord', 'Z_Coord']
            )
        )
        return {'COORDINATES': {'data': extr_coords_df}}

    # case lines
    elif all(
        QgsWkbTypes.displayString(
            g_type.wkbType()
        ) in line_t_names for g_type in df.geometry
    ):
        extracted_vertices = {
            na: extract_xy_from_line(line_geom) for line_geom, na in zip(
                df.geometry,
                df.Name
            )
        }
        return {'VERTICES': {'data': extracted_vertices}}

    # case polygons
    elif all(
        QgsWkbTypes.displayString(
            g_type.wkbType()
        ) in polygon_t_names for g_type in df.geometry
    ):
        extracted_vertices = {
            na: extract_xy_from_area(polyg_geom) for polyg_geom, na in zip(
                df.geometry,
                df.Name
            )
        }
        return {'POLYGONS': {'data': extracted_vertices}}
    else:
        raise QgsProcessingException(
            'Geometry type of one or more features could not be handled'
        )

def extract_xyz_from_simple_point(p_name, point_simple):
    """
    Extract X, Y, and Z coordinates from a simple point.

    :param p_name: Name of the point.
    :type p_name: str
    :param point_simple: Simple point geometry.
    :type point_simple: QgsGeometry
    :return: Tuple containing point name, X coordinate, Y coordinate, and Z coordinate.
    :rtype: tuple
    """
    qgs_point = [p for p in point_simple.parts()][0]
    x_coord = str(qgs_point.x())
    y_coord = str(qgs_point.y())
    z_coord = qgs_point.z()
    return p_name, x_coord, y_coord, z_coord


def extract_xy_from_line(line_geom):
    """
    Extract X and Y coordinates from a LineString or MultiLineString.

    :param line_geom: Line geometry.
    :type line_geom: QgsGeometry
    :return: Dataframe of extracted coordinates.
    :rtype: pd.DataFrame
    """
    vertices_list = [p for p in line_geom.vertices()]
    extr_coords = [
            extract_xyz_from_simple_point(
                'nan',
                point_simple
            ) for point_simple in 
                vertices_list
        ]
    extr_coords_df = pd.DataFrame(
        extr_coords,
        columns=(
            ['Name', 'X_Coord', 'Y_Coord', 'Z_Coord']
        )
    )
    extr_coords_df.drop('Name', axis=1, inplace=True)
    return extr_coords_df

def extract_xy_from_area(geom_row):
    """
    extraxts xy from polygon geometries
    :return: pd.DataFrame
    """
    xy_list = [[str(v.x()), str(v.y())] for v in geom_row.vertices()]
    xy_df = pd.DataFrame(xy_list, columns=['X_Coord', 'Y_Coord'])
    return xy_df

# functions for data in tables
def get_curves_from_table(curves_raw, name_col):
    """
    Extract X and Y coordinates from polygon geometries.

    :param geom_row: Polygon geometry.
    :type geom_row: QgsGeometry
    :return: Dataframe of extracted coordinates.
    :rtype: pd.DataFrame
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
                    curve_dict[i] = {
                        'Name': i,
                        'Type': curve_type,
                        'frame': curve
                    }
    return (curve_dict)


def get_patterns_from_table(patterns_raw, name_col='Name'):
    """
    Generate a pattern dict for the input file from tables (patterns_raw)
    :param patterns_raw
    :type patterns_raw pd.DataFrame
    :param  name_col
    :type name_col str
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
                pattern = pattern.drop(columns=pattern.columns[0])
                pattern = pattern.reset_index(drop=True)
                pattern_dict[i] = {
                    'Name': i,
                    'Type': pattern_type,
                    'Factors': pattern
                }
    return (pattern_dict)


def adjust_datetime(
    dt_list,
    dt_type,
    str_output_format,
    ts_name,
    feedback
):
    """
    Convert time values (tries different formats) into another time string.
    
    :param list or series dt_list: Column in which the date or time is written.
    :type dt_list list/pd.series
    :param dt_type: "Date" or "Time".
    :type dt_type: str
    :param str_output_format
    :type str_output_format: str
    :param ts_name
    :type ts_name: str
    :param feedback
    :type feedback: QgsProcessingFeedback
    """
    dt_formats_dict = {
        'Date': ['yyyy-MM-dd', 'dd/MM/yyyy', 'dd.MM.yyyy'],
        'Time': ['HH:mm:ss', 'HH:mm', 'HH']
    }
    dt_formats = dt_formats_dict[dt_type]
    if all([type(dt_val) in [QDate, QTime] for dt_val in dt_list]):
        dt_val_list = [dt_val.toString(str_output_format) for dt_val in dt_list]
    else:
        dt_list = [str(dt_val) for dt_val in dt_list]
        if dt_type == 'Date':
            for d_f in dt_formats:
                dt_val_list = [QDate.fromString(dt_val, d_f) for dt_val in dt_list]
                if not any([x.isNull() for x in dt_val_list]):
                    break
        else:
            for d_f in dt_formats:
                dt_val_list = [QTime.fromString(dt_val, d_f) for dt_val in dt_list]
                if not any([x.isNull() for x in dt_val_list]):
                    break
        if not any([x.isNull() for x in dt_val_list]):
            dt_val_list = [dt_val.toString(str_output_format) for dt_val in dt_val_list]
            feedback.pushWarning(
                'Timeseries \"'+ts_name+'\" '+dt_type+'column was derived from strings (assumed format: '+d_f
            )
        else:
            raise QgsProcessingException(str(ts_name)+': column '+dt_type+' could not be converted properly. Tested formats: '+dt_formats)
    return dt_val_list


def get_timeseries_from_table(ts_raw, name_col, feedback):
    """
    generates a timeseries dict for the input file from tables (ts_raw)
    :param pd.DataFrame ts_raw
    :param str name_col
    :param QgsProcessingFeedback feedback
    """
    ts_dict = dict()
    ts_raw = ts_raw[ts_raw[name_col] != ";"]
    # warning for deprecated format:
    if ('Type' in ts_raw.columns) and ('Format' in ts_raw.columns):
        feedback.reportError(
            'Warning: The columns \"Type\" and \"Format\" '
            + 'are not used any longer in future versions of the plugin. '
            + 'Creating rain gages from timeseries only is deprecated. '
            + 'Please create a rain gage layer instead. You can get an '
            + 'examplary layer from the default data set or have a look '
            + 'at the documentation file.'
        )
    if ts_raw.empty:
        pass
    else:
        for ts_name in ts_raw[name_col].unique():
            ts_df = ts_raw[ts_raw[name_col] == ts_name]
            if 'File_Name' in ts_raw.columns and not all(pd.isna(ts_df['File_Name'])):  # external time series
                ts_df['Date'] = 'FILE'
                ts_df['Time'] = ts_df['File_Name']
                ts_df['Value'] = ''
            else:
                if sum(pd.isna(ts_df['Date'])) > 0:
                    # handes missing dates
                    if not all(pd.isna(ts_df['Date'])):
                        feedback.pushWarning(
                                'Warning: At least one date in the timeseries file is missing. Date will be set to start date')
                    ts_df['Date'] = ''
                else: 
                    ts_df['Date'] = adjust_datetime(
                        ts_df['Date'],
                        'Date',
                        'MM/dd/yyyy',
                        ts_name,
                        feedback = None
                    )
                ts_df['Time'] = adjust_datetime(
                    ts_df['Time'],
                    'Time',
                    'HH:mm',
                    ts_name,
                    feedback
                )
            if annotation_field_name in ts_df.columns:
                ts_annotation = ts_df[annotation_field_name].fillna('').unique()[0]
            else:
                ts_annotation = ''
            ts_dict[ts_name] = {
                'Name': ts_name,
                'TimeSeries': ts_df[['Name', 'Date', 'Time', 'Value']],
                'Annotations': ts_annotation
            }
    return (ts_dict)


# errors and feedback
def check_deprecated(
    swmm_data_file,
    swmm_section,
    df,
    cols_deprecated,
    feedback
):
    """
    :param str swmm_data_file
    :param str swmm_section
    :param pd.DataFrame df
    :param dic cols_deprecated: e.g. {'DeprecatedName': 'NewName'}
    :param QgsProcessingFeedback feedback
    """
    for dep_col in cols_deprecated.keys():
        if dep_col in df.columns:
            feedback.pushWarning(
                'Warning: usage of columns name \"' + dep_col +'\" in section '
                + swmm_section
                + ' is deprecated and will be removed in future versions of the plugin. Please use \"'
                + cols_deprecated[dep_col] + '\" instead.'
            )
            df = df.rename(columns={dep_col: cols_deprecated[dep_col]})
    return df
        
        
        
def check_columns(
    swmm_data_file,
    cols_expected,
    cols_in_df
):
    """
    checks if all columns are in a dataframe
    :param str swmm_data_file
    :param list cols_expected
    :param list cols_in_df
    """
    try:
        swmm_data_file_name = swmm_data_file.name()
    except Exception:
        swmm_data_file_name = str(swmm_data_file)
    missing_cols = [x for x in cols_expected if x not in cols_in_df]
    if len(missing_cols) == 0:
        pass
    else:
        err_message = 'Missing columns in '+swmm_data_file_name+': '+', '.join(missing_cols)
        err_message = err_message+'. Please add columns or check if the correct file/layer was selected. '
        err_message = err_message+'For further advice regarding columns, read the documentation file in the plugin folder.'
        raise QgsProcessingException(err_message)

