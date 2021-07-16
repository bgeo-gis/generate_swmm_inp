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
__date__ = '2021-07-09'
__copyright__ = '(C) 2021 by Jannik Schilling'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProject,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from datetime import datetime, date
import pandas as pd
import numpy as np
import os


class GenerateSwmmInpFile(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    SWMM_FOLDER = 'SWMM_FOLDER'
    QGIS_OUT_INP_FILE = 'QGIS_OUT_INP_FILE'
    
    
    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.QGIS_OUT_INP_FILE,
                self.tr('Where should the inp file be saved?'),
                'INP files (*.inp)', #defaultValue=['date.inp'] 
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.SWMM_FOLDER,
                self.tr('Folder with all swmm data (e.g.\"swmm_data\")'),
                behavior=QgsProcessingParameterFile.Folder))

    def processAlgorithm(self, parameters, context, feedback):
        today = date.today()
        now = datetime.now()
        inp_file_path = self.parameterAsString(parameters, self.QGIS_OUT_INP_FILE, context)
        inp_file_name = os.path.basename(inp_file_path)
        project_dir = os.path.dirname(inp_file_path)
        swmm_data_dir = self.parameterAsString(parameters, self.SWMM_FOLDER, context)
        
        err_text = ''
        inp_dict = dict()
        inp_dict['junctions_df'] = pd.DataFrame()
        inp_dict['conduits_df'] = pd.DataFrame()
        inp_dict['storage_df'] = pd.DataFrame()
        inp_dict['vertices_dict'] = {}

        # reading Data
        feedback.setProgressText(self.tr('reading shapfiles'))
        feedback.setProgress(5)
        from .g_s_read_data import read_shapefiles
        file_outfalls = 'SWMM_outfalls.shp'
        file_storages = 'SWMM_storages.shp'
        file_subcatchments = 'SWMM_subcatchments.shp'
        file_conduits = 'SWMM_conduits.shp'
        file_junctions = 'SWMM_junctions.shp'
        file_pumps = 'SWMM_pumps.shp'
        file_weirs = 'SWMM_weirs.shp'
        raw_data_dict = read_shapefiles(swmm_data_dir,
                                           file_outfalls,
                                           file_storages,
                                           file_subcatchments,
                                           file_conduits,
                                           file_junctions,
                                           file_pumps,
                                           file_weirs)
        feedback.setProgressText(self.tr('done'))
        feedback.setProgress(20)

        feedback.setProgressText(self.tr('reading tables'))
        """data in tables (curves, patterns, inflows ...)"""
        file_curves = 'gisswmm_curves.xlsx'
        file_patterns = 'gisswmm_patterns.xlsx'
        file_options = 'gisswmm_options.xlsx'
        file_timeseries = 'gisswmm_timeseries.xlsx'
        file_inflows = 'gisswmm_inflows.xlsx'
        file_quality = 'gisswmm_quality.xlsx'
        from .g_s_read_data import read_data_from_table
        raw_data_dict['options_df'] = read_data_from_table(swmm_data_dir,file_options)
        raw_data_dict['curves'] = {}
        for curve_type in ['STORAGE','Pump1','Pump2','Pump3','Pump4']:
            raw_data_dict['curves'][curve_type] = read_data_from_table(swmm_data_dir,
                         file_curves,
                         sheet = curve_type)
        raw_data_dict['patterns'] = {}
        for pattern_type in ['HOURLY','DAILY','MONTHLY','WEEKEND']:
            raw_data_dict['patterns'][pattern_type] = read_data_from_table(swmm_data_dir,
                         file_patterns,
                         sheet = pattern_type)
        raw_data_dict['inflows'] = {}
        for inflow_type in ['Direct','Dry_Weather']:
             raw_data_dict['inflows'][inflow_type] = read_data_from_table(swmm_data_dir,
                         file_inflows,
                         sheet = inflow_type)
        if file_timeseries is not None:
            raw_data_dict['timeseries'] = read_data_from_table(swmm_data_dir, file_timeseries)   
        if file_quality is not None:
            raw_data_dict['quality']={}
            for quality_param in['POLLUTANTS', 'LANDUSES', 'COVERAGES','LOADINGS']:
                raw_data_dict['quality'][quality_param] = read_data_from_table(swmm_data_dir,
                             file_quality,
                             sheet = quality_param)
        feedback.setProgressText(self.tr('done'))
        feedback.setProgress(25)

        feedback.setProgressText(self.tr('preparing data for input file'))
        """options"""
        from .g_s_various_functions import get_options_from_table
        inp_dict['options_dict'] = get_options_from_table(raw_data_dict['options_df'].copy())

        """subcatchments"""
        if 'subcatchments_raw' in raw_data_dict.keys():
            from .g_s_subcatchments import get_subcatchments_from_shapefile
            from .g_s_various_functions import get_coords_from_geometry
            subcatchments_df = get_subcatchments_from_shapefile(raw_data_dict['subcatchments_raw'])
            inp_dict['polygons_dict'] = get_coords_from_geometry(subcatchments_df)
            inp_dict['subcatchments_df'] = subcatchments_df

        """conduits"""
        if 'conduits_raw' in raw_data_dict.keys():
            from .g_s_various_functions import get_coords_from_geometry
            from .g_s_links import get_conduits_from_shapefile
            conduits_df, xsections_df, losses_df =  get_conduits_from_shapefile(raw_data_dict['conduits_raw'].copy())
            #inp_dict['vertices_dict'].update(get_coords_from_geometry(raw_data_dict['conduits_raw'].copy()
            inp_dict['conduits_df'] = conduits_df
            inp_dict['xsections_df'] = xsections_df
            inp_dict['losses_df'] = losses_df

        """pumps"""
        if 'pumps_raw' in raw_data_dict.keys():
            from .g_s_links import get_pumps_from_shapefile
            from .g_s_various_functions import get_coords_from_geometry
            pumps_df = get_pumps_from_shapefile(raw_data_dict['pumps_raw'])
            inp_dict['vertices_dict'].update(get_coords_from_geometry(pumps_df))
            inp_dict['pumps_df'] = pumps_df

        """weirs"""
        if 'weirs_raw' in raw_data_dict.keys():
            from .g_s_links import get_weirs_from_shapefile
            weirs_df, xsections_df= get_weirs_from_shapefile(raw_data_dict['weirs_raw'])
            inp_dict['xsections_df'] = inp_dict['xsections_df'].append(xsections_df)
            inp_dict['xsections_df'] = inp_dict['xsections_df'].reset_index(drop=True)
            inp_dict['weirs_df'] = weirs_df
            
        """
        to do:
            # orifices
            # outlets
        """
        feedback.setProgress(40)


        from .g_s_various_functions import get_coords_from_geometry
        if 'junctions_raw' in raw_data_dict.keys():
            junctions_df = raw_data_dict['junctions_raw'].copy()
            junctions_df['X_Coord'],junctions_df['Y_Coord'] = get_coords_from_geometry(junctions_df)
            inp_dict['junctions_df'] = junctions_df
        if 'outfalls_raw' in raw_data_dict.keys():
            outfalls_df = raw_data_dict['outfalls_raw'].copy()
            outfalls_df['RouteTo'] = outfalls_df['RouteTo'].fillna('')
            outfalls_df['Data'] = outfalls_df['Data'].fillna('')
            outfalls_df['X_Coord'],outfalls_df['Y_Coord'] = get_coords_from_geometry(outfalls_df)
            inp_dict['outfalls_df'] = outfalls_df
        if 'storages_raw' in raw_data_dict.keys():
            storage_df = raw_data_dict['storages_raw'].copy()
            storage_df['X_Coord'],storage_df['Y_Coord'] = get_coords_from_geometry(storage_df)
            storage_df['Psi'] = storage_df['Psi'].fillna('')
            storage_df['Ksat'] = storage_df['Ksat'].fillna('')
            storage_df['IMD'] = storage_df['IMD'].fillna('')
            storage_df['Descriptio'] = storage_df['Descriptio'].fillna('')
            inp_dict['storage_df'] = storage_df
            
        """to do: dividers"""
        # if 'dividers_rwa' in raw_data_dict.keys():
            # #dividers
            # pass
        feedback.setProgress(50)

        """inflows"""
        from .g_s_various_functions import get_inflows_from_table
        dwf_dict , inflow_dict, err_txt = get_inflows_from_table(raw_data_dict['inflows'],junctions_df)
        err_text = err_text+err_txt
        if len(inflow_dict) > 0:
            inp_dict['inflow_dict'] = inflow_dict
        if len(dwf_dict) > 0:
            inp_dict['dwf_dict'] = dwf_dict
        feedback.setProgress(55)

        """Curves"""
        from .g_s_various_functions import get_curves_from_table
        inp_dict['curves_dict'] = get_curves_from_table(raw_data_dict['curves'],
                                                             name_col='Name')
        feedback.setProgress(60)

        """patterns"""
        from .g_s_various_functions import get_patterns_from_table
        inp_dict['patterns_dict'] = get_patterns_from_table(raw_data_dict['patterns'],
                                                             name_col='Name')
        feedback.setProgress(65)
        
        """time series"""
        if 'timeseries' in raw_data_dict.keys():
            from .g_s_various_functions import get_timeseries_from_table, get_raingages_from_timeseries
            inp_dict['timeseries_dict'] = get_timeseries_from_table(raw_data_dict['timeseries'],
                                                                 name_col='Name')
            """rain gages"""
            inp_dict['raingages_dict'] = get_raingages_from_timeseries(inp_dict['timeseries_dict'])
        feedback.setProgress(70)
   
        """quality"""
        if 'quality' in raw_data_dict.keys():
            from .g_s_quality import get_quality_params_from_table
            if 'subcatchments_df' in inp_dict.keys():
                inp_dict['quality_dict'] = get_quality_params_from_table(raw_data_dict['quality'], inp_dict['subcatchments_df'].copy())
            else: 
                inp_dict['quality_dict'] = get_quality_params_from_table(raw_data_dict['quality'])
        feedback.setProgressText(self.tr('done'))
        feedback.setProgress(80)

        feedback.setProgressText(self.tr('writing inp'))
        """writing inp"""
        from .g_s_write_inp import write_inp
        write_inp(inp_file_name,
                  project_dir,
                  inp_dict)
        feedback.setProgress(98)
        
        err_file = open(os.path.join(project_dir,inp_file_name[:-4]+'_errors.txt'),'w')
        err_file.write(err_text)
        err_file.close()
        feedback.setProgressText(self.tr('done'))
        return {}
        
    def shortHelpString(self):
        return self.tr(""" The tool combines all swmm data (shapefiles and xlsx-files) in a selected folder to write a swmm input file.\n
        File names and column names have to be the same as in the default data set.
        Proposed workflow:\n
        1) load default data with the first tool.\n
        2) copy all files to a new folder and change the data set.\n
        3) select the new folder to create the input file (.inp)\n
        4) run the input file in swmm
        """)


    def name(self):
        return 'GenerateSwmmInpFile'

    def displayName(self):
        return self.tr('2_GenerateSwmmInpFile')

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return GenerateSwmmInpFile()
