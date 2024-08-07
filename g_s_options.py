# -*- coding: utf-8 -*-
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
__date__ = '2024-03-21'
__copyright__ = '(C) 2021 by Jannik Schilling'

import pandas as pd
from datetime import datetime, time
from qgis.core import QgsProcessingException
from .g_s_defaults import def_options_dtypes_dict


def adjust_options_dtypes(opt_key, opt_val, opt_source, feedback=None):
    """
    converts datetime formats to string and vice versa
    :param str opt_key
    :param any opt_val
    :param str opt_source: 'table' (source is the options table) or 'input' (source is the SWMM input file)
    :param QgsProcessingFeedback feedback
    """
    if opt_key in def_options_dtypes_dict.keys():
        def_option_i = def_options_dtypes_dict[opt_key]
        d_type_def = def_option_i['dtype']
    else:
        # assume str
        d_type_def = [str]
    if opt_source == 'table':
        d_type_val = type(opt_val)
        if d_type_val in d_type_def: # correct datatype
            if d_type_def[0] in [time, datetime]:
                # time to string; if d_type_val is not correct (e.g. float) it will be printed as str anyway
                d_struct = def_option_i['format']
                opt_val = opt_val.strftime(d_struct)
            elif (d_type_def[0] is str) and (opt_key != 'TEMPDIR'):
                # check if value is valid
                def_vals = def_option_i['values']
                if opt_val not in def_vals:
                    raise QgsProcessingException('[OPTIONS]: Value for ' + opt_key + ' must be one of '+', '.join(def_vals))
            else: # will be printed to str in the inp file
                pass
    if opt_source == 'input':
        if d_type_def[0] == datetime:
            d_struct = def_option_i['format']
            opt_val = datetime.strptime(opt_val, d_struct).date()
        if d_type_def[0] == time:
            d_struct = def_option_i['format']
            if opt_key in ['REPORT_STEP', 'WET_STEP', 'DRY_STEP'] and int(opt_val.split(':')[0]) > 23:
                feedback.reportError('Warning: ' + str(opt_key) + ' was more than 24h. To avoid time format errors in Python, this value was set to 01:00:00')
                opt_val = datetime.strptime('01:00:00', d_struct).time()
            el
            if opt_key == 'ROUTING_STEP':
                try:
                    opt_val = datetime.strptime(opt_val, d_struct).time()
                except Exception:
                    opt_val = float(opt_val)
            else:
                opt_val = datetime.strptime(opt_val, d_struct).time()
        if d_type_def[0] == int:
            opt_val = float(opt_val)
    return opt_val


# export from table to inp file
def get_options_from_table(options_df):
    """
    converts file_options_df to dict and
    converts datetime formats to string
    :param pd.DataFrame options_df
    """
    options_df['Value'] = [adjust_options_dtypes(k, v, 'table') for k, v in zip(options_df['Option'], options_df['Value'])]
    if 'INFILTRATION' in options_df['Option'].values:
        main_infiltration_method = options_df.loc[options_df['Option'] == 'INFILTRATION', 'Value']
    else:
        main_infiltration_method = None
    return options_df, main_infiltration_method


# import from inp file
def convert_options_format_for_import(
    df_options,
    import_parameters_dict,
    feedback
):
    '''
    converts formats in dict_options for the options file
    :param pd.DataFrame df_options
    :param dict import_parameters_dict
    :param QgsProcessingFeedback feedback
    '''
    dict_options = {k: v for k, v in zip(df_options['Option'], df_options['Value'])}
    df_options = pd.DataFrame()
    df_options['Option'] = dict_options.keys()
    df_options['Value'] = dict_options.values()
    if 'INFILTRATION' in df_options['Option'].values:
        main_infiltration_method = df_options.loc[df_options['Option'] == 'INFILTRATION', 'Value'].values[0]
        if main_infiltration_method not in [
            'HORTON',
            'MODIFIED_HORTON',
            'GREEN_AMPT',
            'MODIFIED_GREEN_AMPT',
            'CURVE_NUMBER'
        ]:
            main_infiltration_method = 'HORTON'
        import_parameters_dict['main_infiltration_method'] = main_infiltration_method
    return df_options

