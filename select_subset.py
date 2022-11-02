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


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import pandas as pd
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingException,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterVectorLayer)
from .g_s_various_functions import check_columns, get_coords_from_geometry
from .g_s_defaults import def_sections_dict, def_curve_types
from .g_s_read_write_data  import read_layers_direct

class SelectSubModel(QgsProcessingAlgorithm):
    """
    generates a swmm input file from geodata and tables
    """
    QGIS_OUT_INP_FILE = 'QGIS_OUT_INP_FILE'
    FILE_RAINGAGES = 'FILE_RAINGAGES'
    FILE_CONDUITS = 'FILE_CONDUITS'
    FILE_JUNCTIONS = 'FILE_JUNCTIONS'
    FILE_DIVIDERS = 'FILE_DIVIDERS'
    FILE_ORIFICES = 'FILE_ORIFICES'
    FILE_OUTFALLS = 'FILE_OUTFALLS'
    FILE_OUTLETS = 'FILE_OUTLETS'
    FILE_STORAGES = 'FILE_STORAGES'
    FILE_PUMPS    = 'FILE_PUMPS'
    FILE_SUBCATCHMENTS= 'FILE_SUBCATCHMENTS'
    FILE_WEIRS = 'FILE_WEIRS'
    
    
    def initAlgorithm(self, config):
        """
        inputs and output of the algorithm
        """
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_RAINGAGES,
                self.tr('Rain gages Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional = True#,defaultValue = 'SWMM_Raingagges'
                ))
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_JUNCTIONS,
                self.tr('Junctions Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional = True#,defaultValue = 'SWMM_junctions'
                ))
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_CONDUITS,
                self.tr('Conduits Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional = True#,defaultValue = 'SWMM_conduits'
                ))
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_SUBCATCHMENTS,
                self.tr('Subcatchments Layer'),
                types=[QgsProcessing.SourceType.TypeVectorAnyGeometry],
                optional = True#,defaultValue = 'SWMM_subcatchments'
                ))
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_STORAGES,
                self.tr('Storages Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional = True#,defaultValue = 'SWMM_storages'
                ))
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_OUTFALLS,
                self.tr('Outfalls Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional = True#,defaultValue = 'SWMM_outfalls'
                ))
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_DIVIDERS,
                self.tr('Dividers Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional = True#,defaultValue = 'SWMM_dividers'
                ))
                
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_PUMPS,
                self.tr('Pumps Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional = True#,defaultValue = 'SWMM_Pumps'
                ))
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_WEIRS,
                self.tr('Weirs Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional = True#,defaultValue = 'SWMM_weirs'
                ))
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_ORIFICES,
                self.tr('Orifices Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional = True#,defaultValue = 'SWMM_orifices'
                ))
                
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_OUTLETS,
                self.tr('Outlets Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional = True#,defaultValue = 'SWMM_outlets'
                ))
                
    def processAlgorithm(self, parameters, context, feedback):  
        """
        """
        # reading geodata
        feedback.setProgressText(self.tr('Reading shapfiles'))
        feedback.setProgress(1)
        file_raingages = self.parameterAsVectorLayer(parameters, self.FILE_RAINGAGES, context)
        file_outfalls = self.parameterAsVectorLayer(parameters, self.FILE_OUTFALLS, context)
        file_storages = self.parameterAsVectorLayer(parameters, self.FILE_STORAGES, context)
        file_subcatchments = self.parameterAsVectorLayer(parameters, self.FILE_SUBCATCHMENTS, context)
        file_conduits = self.parameterAsVectorLayer(parameters, self.FILE_CONDUITS, context)
        file_junctions = self.parameterAsVectorLayer(parameters, self.FILE_JUNCTIONS, context)
        file_pumps = self.parameterAsVectorLayer(parameters, self.FILE_PUMPS, context)
        file_weirs = self.parameterAsVectorLayer(parameters, self.FILE_WEIRS, context)
        file_orifices = self.parameterAsVectorLayer(parameters, self.FILE_ORIFICES, context)
        file_outlets = self.parameterAsVectorLayer(parameters, self.FILE_OUTLETS, context)
        file_dividers = self.parameterAsVectorLayer(parameters, self.FILE_DIVIDERS, context)
        
        # line layers
        line_layers_dict = {
            'conduits_raw': file_conduits,
            'pumps_raw':file_pumps,
            'weirs_raw':file_weirs,
            'orifices_raw':file_orifices,
            'outlets_raw':file_outlets
        }
        needed_line_attrs = ['Name','FromNode','ToNode']
        lines_df_dict = read_layers_direct(
            line_layers_dict,
            needed_line_attrs,
            with_id = True
        )
        
        # subcatchment layer
        subcatch_layers_dict = {
            'subcatchments_raw':file_subcatchments
        }
        needed_subc_attrs = ['Name','RainGage']
        subc_df_dict = read_layers_direct(
            subcatch_layers_dict,
            needed_subc_attrs,
            with_id = True
        )
        
        # node layers
        nodes_layers_dict = {
            'junctions_raw':file_junctions,
            'outfalls_raw':file_outfalls,
            'storages_raw':file_storages,
            'raingages_raw':file_raingages,
            'dividers_raw':file_dividers
        }
        needed_nodes_attrs = ['Name']
        nodes_df_dict = read_layers_direct(
            nodes_layers_dict,
            needed_nodes_attrs,
            with_id = True
        )

        feedback.setProgressText(self.tr('done \n'))
        feedback.setProgress(12)
####

#junctions = QgsProject.instance().mapLayer('[% @layer_id %]')
#junctions_field_name = junctions.fields().indexFromName("Name")
#junctions_startpoint = junctions.getFeature([% $id %])
#junctions_startpoint_attrs = junctions_startpoint.attributes()
# junctions_startpoint_name = junctions_startpoint_attrs[junctions_field_name]
# QtWidgets.QMessageBox.information(None,"Aktion", 'Selektiere alles oberhalb '+junctions_startpoint_name)
# junctions_data = [[str(f.attribute(junctions_field_name)),
    # f.id()] for f in junctions.getFeatures()]
# junctions_data_arr = np.array(junctions_data, dtype= 'object')


# conduits = QgsProject.instance().mapLayersByName('Conduits_Max_Sum_Flow')[0]
# conduits_field_id = conduits.fields().indexFromName('Name') 
# conduits_field_prev = conduits.fields().indexFromName('FromNode')
# conduits_field_next = conduits.fields().indexFromName('ToNode')
# conduits_field_len = conduits.fields().indexFromName('Length')
# conduits_data = [[str(f.attribute(conduits_field_id)),  #0
    # str(f.attribute(conduits_field_prev)),              #1
    # str(f.attribute(conduits_field_next)),              #2
    # f.id(),                                             #3
    # float(f.attribute(conduits_field_len))] for f in conduits.getFeatures()]
# conduits_data_arr = np.array(conduits_data, dtype= 'object')

# subcatch = QgsProject.instance().mapLayersByName('Subcatchments_Neu')[0]
# subcatch_field_routeto = subcatch.fields().indexFromName('Outlet') 
# subcatch_field_area = subcatch.fields().indexFromName('Area') 
# subcatch_data = [[str(f.attribute(subcatch_field_routeto)),
    # f.id(),
    # float(f.attribute(subcatch_field_area))] for f in subcatch.getFeatures()]
# subcatch_data_arr = np.array(subcatch_data, dtype= 'object')

# startId = np.where(conduits_data_arr[:,1]==junctions_startpoint_name)[0][0]
# StartMarker = conduits_data_arr[startId,0] #Start_name in Conduits


# # liste fuer das routing initialisieren
# conduits_route = []
# junctions_route = []

# '''find flow path upstream or downstream'''
# Marker=str(StartMarker) # NET_ID of first segment
# safe=["X"] #a list to safe segments when the net separates; "X" indicates an empty list and works as a Marker for the while loop below
# origins = [] # a list for origins/river heads upstream

# def nextFtsSel (Marker2):
            # clm_current = 1
            # clm_search = 2
            # vtx_connect = conduits_data_arr[np.where(conduits_data_arr[:,0] == Marker2)[0].tolist(),clm_current][0] # connecting vertex of actual segment
            # rows_connect = np.where(conduits_data_arr[:,clm_search] == vtx_connect)[0].tolist() # find rows in conduits_data_arr with matching vertices to vtx_connect
            # return(rows_connect)


# while str(Marker) != 'X':
    # next_rows = nextFtsSel (Marker)
    # if len (next_rows) > 0: # sometimes segments are saved in conduits_route...then they are deleted
        # for Z in next_rows: 
            # if conduits_data_arr[Z,3] in conduits_route:
                # next_rows.remove(Z)
        # conduits_route = conduits_route + conduits_data_arr[next_rows,3].tolist()
        # junctions_from_names = conduits_data_arr[next_rows,1].tolist()
        # junctions_route = junctions_route + junctions_from_names
    # if len(next_rows) > 1:
        # Marker=conduits_data_arr[next_rows[0],0]# change Marker to the NET_ID of one of the next segments
        # safe=safe + conduits_data_arr[next_rows[1:],0].tolist()
    # if len(next_rows) == 1:
        # Marker=conduits_data_arr[next_rows[0],0]
    # if len(next_rows) == 0:
        # origins = origins + [Marker]
        # Marker = safe[-1] #change Marker to the last "saved" NET_ID
        # safe=safe[:-1] #delete used NET_ID from "safe"-list

# # select conduits
# conduits_lengths = conduits_data_arr[np.where(np.isin(conduits_data_arr[:,3],conduits_route)),4].tolist()[0]
# sum_lengths = round(sum(conduits_lengths)/1000,2) #km
# sel=[]
# while len(conduits_route) != 0:
    # set1=conduits_route[:200]
    # sel=sel+[set1]
    # conduits_route=conduits_route[200:]
# conduits.removeSelection()
# for selSet in sel:
    # conduits.selectByIds(selSet, conduits.SelectBehavior(1))

# # select junctions
# sel=[]
# junctions_route_sel = junctions_data_arr[np.where(np.isin(junctions_data_arr[:,0],junctions_route)),1].tolist()[0]
# while len(junctions_route_sel) != 0:
    # set1=junctions_route_sel[:200]
    # sel=sel+[set1]
    # junctions_route_sel=junctions_route_sel[200:]
# junctions.removeSelection()
# for selSet in sel:
    # junctions.selectByIds(selSet, junctions.SelectBehavior(1))


# # select subcatchments
# sel=[]
# subcatch_route_sel = subcatch_data_arr[np.where(np.isin(subcatch_data_arr[:,0],junctions_route)),1].tolist()[0]
# subcatch_route_area = subcatch_data_arr[np.where(np.isin(subcatch_data_arr[:,0],junctions_route)),2].tolist()[0]
# sum_areas = round(sum(subcatch_route_area),2)
# while len(subcatch_route_sel) != 0:
    # set1=subcatch_route_sel[:200]
    # sel=sel+[set1]
    # subcatch_route_sel=subcatch_route_sel[200:]
# subcatch.removeSelection()
# for selSet in sel:
    # subcatch.selectByIds(selSet, subcatch.SelectBehavior(1))

# QtWidgets.QMessageBox.information(
    # None,
    # "Auswahl abgeschlossen",
    # 'Fließlänge oberhalb: '+str(sum_lengths)+' km\nEZG: '+str(sum_areas)+' ha')
