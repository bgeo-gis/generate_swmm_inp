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
__date__ = '2023-07-03'
__copyright__ = '(C) 2021 by Jannik Schilling'


# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import pandas as pd
import numpy as np
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProject,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterVectorLayer,
    QgsVectorFileWriter
)
from .g_s_read_write_data import (
    read_layers_direct,
    create_layer_from_df,
    save_layer_to_file
)
from .g_s_defaults import (
    def_ogr_driver_dict,
    def_stylefile_dict,
    ImportDataStatus
)
from .g_s_import_helpers import add_layer_on_completion


class CreateSubModel(QgsProcessingAlgorithm):
    """
    generates a swmm input file from geodata and tables
    """
    OPTION_ABOVE_BELOW = 'OPTION_ABOVE_BELOW'
    SAVE_FOLDER = 'SAVE_FOLDER'
    PREFIX = 'PREFIX'
    FILE_RAINGAGES = 'FILE_RAINGAGES'
    FILE_CONDUITS = 'FILE_CONDUITS'
    FILE_JUNCTIONS = 'FILE_JUNCTIONS'
    FILE_DIVIDERS = 'FILE_DIVIDERS'
    FILE_ORIFICES = 'FILE_ORIFICES'
    FILE_OUTFALLS = 'FILE_OUTFALLS'
    FILE_OUTLETS = 'FILE_OUTLETS'
    FILE_STORAGES = 'FILE_STORAGES'
    FILE_PUMPS = 'FILE_PUMPS'
    FILE_SUBCATCHMENTS = 'FILE_SUBCATCHMENTS'
    FILE_WEIRS = 'FILE_WEIRS'

    def initAlgorithm(self, config):
        """
        inputs and output of the algorithm
        """
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OPTION_ABOVE_BELOW,
                self.tr('Selection type'),
                [
                    'Model parts above selected node',
                    'Exclude model parts above selected node'
                ],
                optional=False,
                defaultValue=0
                ))
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.SAVE_FOLDER,
                self.tr('Folder in which the new model files will be saved.')
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.PREFIX,
                self.tr('Prefix for new data'),
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_JUNCTIONS,
                self.tr('Junctions Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_CONDUITS,
                self.tr('Conduits Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_SUBCATCHMENTS,
                self.tr('Subcatchments Layer'),
                types=[QgsProcessing.SourceType.TypeVectorAnyGeometry],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_STORAGES,
                self.tr('Storages Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_OUTFALLS,
                self.tr('Outfalls Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_DIVIDERS,
                self.tr('Dividers Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_PUMPS,
                self.tr('Pumps Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_WEIRS,
                self.tr('Weirs Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_ORIFICES,
                self.tr('Orifices Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_OUTLETS,
                self.tr('Outlets Layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.FILE_RAINGAGES,
                self.tr('Rain gages Layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional=True
            )
        )

    def name(self):
        return 'CreateSubModel'

    def shortHelpString(self):
        return self.tr(""" The tool creates a subset of features in the chosen SWMM layers in order to create a new model\n
        Workflow:\n
        1. select a Node (Junction, Storage, Divider, Outfall)
        2. Choose a folder and prefix for the subset
        3. run the tool with the existing layers
        """)

    def displayName(self):
        return self.tr('4_CreateSubModel')

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreateSubModel()

    def processAlgorithm(self, parameters, context, feedback):
        above_or_below = self.parameterAsInt(
            parameters,
            self.OPTION_ABOVE_BELOW, context
        )  # 0=above, 1=below
        feedback.setProgressText(self.tr('Reading layers'))
        feedback.setProgress(1)
        folder_save = self.parameterAsString(
            parameters,
            self.SAVE_FOLDER,
            context
        )
        if parameters['SAVE_FOLDER'] == 'TEMPORARY_OUTPUT':
            raise QgsProcessingException(
                'The data set needs to be saved in a directory (temporary folders won´t work). Please select a directoy'
            )
        result_prefix = self.parameterAsString(
            parameters,
            self.PREFIX,
            context
        )
        if result_prefix == '':
            result_prefix = 'Subset'
        file_raingages = self.parameterAsVectorLayer(
            parameters,
            self.FILE_RAINGAGES,
            context
        )
        file_outfalls = self.parameterAsVectorLayer(
            parameters,
            self.FILE_OUTFALLS,
            context
        )
        file_storages = self.parameterAsVectorLayer(
            parameters,
            self.FILE_STORAGES,
            context
        )
        file_subcatchments = self.parameterAsVectorLayer(
            parameters,
            self.FILE_SUBCATCHMENTS,
            context
        )
        file_conduits = self.parameterAsVectorLayer(
            parameters,
            self.FILE_CONDUITS,
            context
        )
        file_junctions = self.parameterAsVectorLayer(
            parameters,
            self.FILE_JUNCTIONS,
            context
        )
        file_pumps = self.parameterAsVectorLayer(
            parameters,
            self.FILE_PUMPS,
            context
        )
        file_weirs = self.parameterAsVectorLayer(
            parameters,
            self.FILE_WEIRS,
            context
        )
        file_orifices = self.parameterAsVectorLayer(
            parameters,
            self.FILE_ORIFICES,
            context
        )
        file_outlets = self.parameterAsVectorLayer(
            parameters,
            self.FILE_OUTLETS,
            context
        )
        file_dividers = self.parameterAsVectorLayer(
            parameters,
            self.FILE_DIVIDERS,
            context
        )
        pluginPath = os.path.dirname(__file__)

        feedback.setProgressText(self.tr('Loading layers...'))
        # list for all layer names which will be added
        # to the project after the tool is executed
        list_move_to_group = [] # currently not in use

        # create layer dictionaries
        # nodes
        nodes_layers_dict = {
            'JUNCTIONS': file_junctions,
            'OUTFALLS': file_outfalls,
            'STORAGE': file_storages,
            'DIVIDERS': file_dividers
        }
        nodes_layers_dict = {k: v for k, v in nodes_layers_dict.items() if v is not None}
        drivers_dict = {k: v.dataProvider().storageType() for k, v in nodes_layers_dict.items()}
        crs_dict = {k: v.dataProvider().crs() for k, v in nodes_layers_dict.items()}

        # links
        link_layers_dict = {
            'CONDUITS': file_conduits,
            'PUMPS': file_pumps,
            'WEIRS': file_weirs,
            'ORIFICES': file_orifices,
            'OUTLETS': file_outlets
        }
        link_layers_dict = {k: v for k, v in link_layers_dict.items() if v is not None}
        drivers_dict.update({k: v.dataProvider().storageType() for k, v in link_layers_dict.items()})
        crs_dict.update({k: v.dataProvider().crs() for k, v in link_layers_dict.items()})

        # subcatchments
        subcatch_layers_dict = {'SUBCATCHMENTS': file_subcatchments}
        subcatch_layers_dict = {k: v for k, v in subcatch_layers_dict.items() if v is not None}
        drivers_dict.update({k: v.dataProvider().storageType() for k, v in subcatch_layers_dict.items()})
        crs_dict.update({k: v.dataProvider().crs() for k, v in subcatch_layers_dict.items()})
        if len(subcatch_layers_dict) != 0:
            needed_subc_attrs = ['Name', 'Outlet', 'RainGage']
            subc_df_dict = read_layers_direct(
                subcatch_layers_dict,
                needed_subc_attrs,
                with_id=True,
                feedback = feedback
            )
            subc_df = subc_df_dict['SUBCATCHMENTS'][needed_subc_attrs+['id']]

        # raingages
        raingages_layer_dict = {'RAINGAGES': file_raingages}
        raingages_layer_dict = {k: v for k, v in raingages_layer_dict.items() if v is not None}
        drivers_dict.update({k: v.dataProvider().storageType() for k, v in raingages_layer_dict.items()})
        crs_dict.update({k: v.dataProvider().crs() for k, v in raingages_layer_dict.items()})
        if len(raingages_layer_dict) != 0:
            # load raingages layer as pd df
            needed_rg_attrs = ['Name']
            rg_df_dict = read_layers_direct(
                raingages_layer_dict,
                needed_rg_attrs,
                with_id=True,
                feedback = feedback
            )
            rg_df = rg_df_dict['RAINGAGES'][needed_rg_attrs+['id']]

        feedback.setProgressText(self.tr('Identifying start node...'))
        feedback.setProgress(6)
        if len(nodes_layers_dict) == 0:
            raise QgsProcessingException('You need at least one node layer')
        else:
            # load node layers (also checks if required fields exist)
            needed_nodes_attrs = ['Name', 'Elevation']
            nodes_df_dict = read_layers_direct(
                nodes_layers_dict,
                needed_nodes_attrs,
                with_id=True,
                feedback = feedback
            )
            # get startpoint...
            start_point = ''
            for k, p_f in nodes_layers_dict.items():
                if feedback.isCanceled():
                    break
                s_f_c = p_f.selectedFeatureCount()
                if s_f_c == 1:
                    if start_point == '':
                        start_point = p_f.selectedFeatures()[0].attribute('Name')
                        start_point_file = p_f.name()
                        start_layer_type = k
                        if k == 'OUTFALLS':
                            start_point_id = p_f.selectedFeatureIds()
                        else:
                            start_point_elvation = p_f.selectedFeatures()[0].attribute('Elevation')
                            start_point_geometry = p_f.selectedFeatures()[0].geometry()
                    else:
                        raise QgsProcessingException('There is more than one point selected in total (in different layers): ' + str(start_point_file) + ', '+str(p_f.name()) + '. Only one selected point is allowed for this tool!')
                if s_f_c > 1:
                    raise QgsProcessingException('There is more than one point selected in layer ' + str(p_f.name()) + '. Only one selected point is allowed for this tool!')
            if start_point == '':
                raise QgsProcessingException('No selected Node. Please select one node in the node layers')
            # merge node layers as pd.df
            all_nodes_df = pd.concat([i for i in nodes_df_dict.values()])
            all_nodes_df = all_nodes_df[needed_nodes_attrs+['id']]
            all_nodes_df = all_nodes_df.reset_index()

        feedback.setProgressText(self.tr('done \n'))
        feedback.setProgress(12)

        # links
        if len(link_layers_dict) == 0:
            feedback.setProgressText(self.tr('No link layers -> Selecting only node and subcatchments...'))
            nodes_route = [start_point]
        else:
            feedback.setProgressText(self.tr('Routing along links...'))
            # load and merge link layers as pd.df
            needed_link_attrs = ['Name', 'FromNode', 'ToNode']
            links_df_dict = read_layers_direct(
                link_layers_dict,
                needed_link_attrs,
                with_id=True,
                feedback = feedback
            )
            all_links_df = pd.concat([i for i in links_df_dict.values()])
            all_links_df = all_links_df[needed_link_attrs+['id']]
            all_links_df = all_links_df.reset_index()

            # initialize lists and Markerfor routing
            links_route = []
            nodes_route = []
            Marker = start_point  # Name of first segment
            safe = ["X"]  # a list to save segments when the net separates; "X" indicates an empty list and works as a Marker for the while loop below

            while str(Marker) != 'X':
                if feedback.isCanceled():
                    break
                next_rows = np.where(Marker == all_links_df['ToNode'])[0].tolist()
                if len(next_rows) > 0:
                    if Marker == start_point:
                        feedback.pushWarning('Warning: More than one link is connected to the selected node (which will be converted into an outfall node). This will lead to an error in SWMM.')
                    for Z in next_rows:
                        if all_links_df.loc[Z, 'Name'] in links_route:
                            # sometimes segments are saved in links_route...then they are deleted
                            next_rows.remove(Z)
                    links_route = links_route + all_links_df.loc[next_rows, 'Name'].tolist()
                    nodes_from_names = all_links_df.loc[next_rows, 'FromNode'].tolist()
                    nodes_route = nodes_route + nodes_from_names
                if len(next_rows) > 1:
                    Marker = all_links_df.loc[next_rows[0], 'FromNode']
                    safe = safe + all_links_df.loc[next_rows[1:], 'FromNode'].tolist()
                if len(next_rows) == 1:
                    Marker = all_links_df.loc[next_rows[0], 'FromNode']
                if len(next_rows) == 0:
                    Marker = safe[-1]
                    safe = safe[:-1]

            feedback.setProgressText(self.tr('done \n'))
            feedback.setProgress(40)

            # delete duplicate nodes
            nodes_route = list(np.unique(nodes_route))

            # check for splitting nodes
            links_not_above = all_links_df.loc[~np.isin(all_links_df['Name'].to_list(), links_route), :]

            # required nodes for 'not_above'
            nodes_route_2 = list(links_not_above['FromNode'])+list(links_not_above['ToNode'])
            nodes_route_2 = list(np.unique(nodes_route_2))

            # check for "splitting" nodes
            splitting_nodes = [str(f) for f in nodes_route_2 if f in nodes_route]
            if len(splitting_nodes) > 0:
                feedback.pushWarning("Warning: the network is splitting at :"+", ".join(splitting_nodes)+"\n")
            if above_or_below == 1:  # below
                links_route = list(links_not_above['Name'])
                nodes_route = nodes_route_2

        # check if all requires nodes are in nodes_route
        feedback.setProgressText(self.tr('Checking if all required nodes exist...'))
        feedback.setProgress(45)
        nodes_exist_dict = {n: (n in all_nodes_df['Name'].to_list()) for n in nodes_route}
        if all(nodes_exist_dict.values()):
            pass
        else:
            missing_nodes = [str(k) for k, v in nodes_exist_dict.items() if not v]
            raise QgsProcessingException('Missing nodes for submodel: '+', '.join(missing_nodes)+'. Please check if all required layers were selected')
        feedback.setProgressText(self.tr('done \n'))
        feedback.setProgress(50)

        # select links layers
        if len(link_layers_dict) == 0:
            pass
        else:
            for layer_n, vector_layer in link_layers_dict.items():
                layer_n_attrs = links_df_dict[layer_n]
                features_for_selection = list(layer_n_attrs.loc[layer_n_attrs['Name'].isin(links_route), 'id'])
                sel = []
                while len(features_for_selection) != 0:
                    if feedback.isCanceled():
                        break
                    set1 = features_for_selection[:200]
                    sel = sel+[set1]
                    features_for_selection = features_for_selection[200:]
                vector_layer.removeSelection()
                for selSet in sel:
                    vector_layer.selectByIds(
                        selSet,
                        vector_layer.SelectBehavior(1)
                    )

        # select node layers
        for layer_n, vector_layer in nodes_layers_dict.items():
            layer_n_attrs = nodes_df_dict[layer_n]
            features_for_selection = list(layer_n_attrs.loc[layer_n_attrs['Name'].isin(nodes_route), 'id'])
            sel = []
            while len(features_for_selection) != 0:
                set1 = features_for_selection[:200]
                sel = sel+[set1]
                features_for_selection = features_for_selection[200:]
            vector_layer.removeSelection()
            for selSet in sel:
                vector_layer.selectByIds(selSet, vector_layer.SelectBehavior(1))

        if above_or_below == 0:
            # add_outfall_node if start_layer_type is not OUTFALLS
            if start_layer_type == 'OUTFALLS':
                file_outfalls.selectByIds(start_point_id, vector_layer.SelectBehavior(1))
            else:
                feedback.setProgressText(self.tr('Creating outfall node...'))
                # get crs for outfall file from original outfall file or take the first crs from a node layer in the dict
                layer_name = str(result_prefix)+'_SWMM_outfalls'
                fname = os.path.join(folder_save, layer_name+'.'+'gpkg')
                if os.path.isfile(fname):
                    raise QgsProcessingException(
                        'File '+fname+' already exists. Submodel features will '
                        +'only be selected. Please choose another folder or prefix.'
                )
                if file_outfalls is not None:
                    crs_result = file_outfalls.crs().authid()
                else:
                    crs_result = list(nodes_layers_dict.values())[0].crs().authid()
                outfalls_df = pd.DataFrame()
                outfalls_df.loc[0, 'Name'] = start_point
                outfalls_df.loc[0, 'Elevation'] = start_point_elvation
                outfalls_df.loc[0, 'Type'] = 'FREE'
                outfalls_df.loc[0, 'FixedStage'] = 0
                outfalls_df.loc[0, 'Curve_TS'] = ''
                outfalls_df.loc[0, 'FlapGate'] = 'NO'
                outfalls_df.loc[0, 'RouteTo'] = ''
                outfalls_df.loc[0, 'geometry'] = start_point_geometry
                create_layer_dict = {
                    'data': outfalls_df,
                    'status': ImportDataStatus.GEOM_READY,
                    'layer_name': layer_name
                }
                list_move_to_group.append(layer_name)
                created_layer = create_layer_from_df(
                    create_layer_dict,
                    section_name='OUTFALLS',
                    crs_result=crs_result,
                    folder_save=folder_save,
                    feedback=feedback
                )
                save_layer_to_file(
                    vector_layer,
                    layer_name,
                    folder_save,
                    geodata_driver_num=1
                )
                add_layer_on_completion(
                    layer_name,
                    'style_outfalls.qml',
                    'gpkg',
                    folder_save,
                    pluginPath,
                    context,
                    layer_color = 'red'
                )
                feedback.setProgressText(self.tr('done \n'))
                feedback.setProgress(55)

        # subcatchments
        if len(subcatch_layers_dict) != 0:
            feedback.setProgressText(self.tr('Selecting subcatchments...'))
            # select subcatchments
            sc_for_selection = subc_df.loc[subc_df['Outlet'].isin(nodes_route), :]
            features_for_selection = list(sc_for_selection['id'])
            sel = []
            while len(features_for_selection) != 0:
                set1 = features_for_selection[:200]
                sel = sel+[set1]
                features_for_selection = features_for_selection[200:]
            file_subcatchments.removeSelection()
            for selSet in sel:
                file_subcatchments.selectByIds(
                    selSet,
                    file_subcatchments.SelectBehavior(1)
                )
            feedback.setProgressText(self.tr('done \n'))
            feedback.setProgress(60)

            # raingages
            if len(raingages_layer_dict) != 0:
                feedback.setProgressText(self.tr('Selecting raingages...'))
                # select raingages
                required_rangages = list(np.unique(sc_for_selection['RainGage']))
                features_for_selection = list(rg_df.loc[rg_df['Name'].isin(required_rangages), 'id'])
                sel = []
                while len(features_for_selection) != 0:
                    set1 = features_for_selection[:200]
                    sel = sel+[set1]
                    features_for_selection = features_for_selection[200:]
                file_raingages.removeSelection()
                for selSet in sel:
                    file_raingages.selectByIds(selSet, file_raingages.SelectBehavior(1))
                feedback.setProgressText(self.tr('done \n'))
                feedback.setProgress(70)

        # combine all dicts in order to save the selected parts
        dict_all_layers = {}
        dict_all_layers.update(nodes_layers_dict)
        dict_all_layers.update(link_layers_dict)
        dict_all_layers.update(subcatch_layers_dict)
        dict_all_layers.update(raingages_layer_dict)

        # add layers to canvas
        #print(crs_dict)
        feedback.setProgressText(self.tr('Adding layerst to canvas...'))
        for k, v in dict_all_layers.items():
            if v.selectedFeatureCount() > 0:
                vector_layer = v
                layer_name = str(result_prefix)+'_SWMM_'+k.lower()
                geodata_crs = crs_dict[k]
                geodata_driver_name = drivers_dict[k]
                geodata_driver_extension = def_ogr_driver_dict[geodata_driver_name]
                # vector_layer.setCrs(geodata_crs)
                # create layer
                options = QgsVectorFileWriter.SaveVectorOptions()
                options.fileEnconding = 'utf-8'
                options.driverName = geodata_driver_name
                options.onlySelectedFeatures = True
                transform_context = QgsProject.instance().transformContext()
                fname = os.path.join(
                    folder_save, layer_name+'.'+geodata_driver_extension
                )
                if os.path.isfile(fname):
                    raise QgsProcessingException('File '+fname
                    + ' already exists. Submodel features will only be '
                    + 'selected. Please choose another folder or prefix.')
                QgsVectorFileWriter.writeAsVectorFormatV3(
                    vector_layer,
                    fname,
                    transform_context,
                    options
                )
                style_file = def_stylefile_dict[k]
                add_layer_on_completion(
                    layer_name,
                    style_file,
                    geodata_driver_extension,
                    folder_save,
                    pluginPath,
                    context,
                    layer_color = 'red'
                )
                list_move_to_group.append(layer_name)
        feedback.setProgress(95)
        feedback.setProgressText(self.tr('done \n'))
        feedback.setProgressText(
            self.tr(
                'Layers saved to '+
                str(folder_save)
            )
        )
        return {}
