# -*- coding: utf-8 -*-
"""
@author: schilling
"""

def_curve_types = ['Control','Pump1','Pump2','Pump3','Pump4','Storage','Rating','Weir','Tidal','Diversion','Shape']

def_sections_dict={'TITLE':None,
         'OPTIONS':['Option', 'Value'],
         'REPORT':None,
         'FILES': None,
         'RAINGAGES':['Description','Format','Interval','SCF', 'Source','SourceName', 'StationID','Units'],
         'EVAPORATION':None,
         'TEMPERATURE':None,
         'ADJUSTMENTS':None,
         'SUBCATCHMENTS': {'Name':'String',
                           'RainGage':'String', 
                           'Outlet':'String',
                           'Area':'Double', 
                           'Imperv':'Double',
                           'Width':'Double',
                           'Slope':'Double',
                           'CurbLen':'Double',
                           'SnowPack':'String'}, 
         'SUBAREAS':{'Name':'String',
                     'N_Imperv':'Double',
                     'N_Perv':'Double',
                     'S_Imperv':'Double',
                     'S_Perv':'Double',
                     'PctZero':'Double',
                     'RouteTo':'String',
                     'PctRouted':'Double'},
         'INFILTRATION':{'Name':'String',
                         'Param1':'String', 
                         'Param2':'Double',
                         'Param3':'Double',
                         'Param4':'Double',
                         'Param5':'String',
                         'kind':'String'},
         'LID_CONTROLS':None,
         'LID_USAGE':None,
         'AQUIFERS':None,
         'GROUNDWATER':None,
         'GWF':None,
         'SNOWPACKS':None,
         'JUNCTIONS':{'Name':'String',
                      'Elevation':'Double',
                      'MaxDepth':'Double', 
                      'InitDepth':'Double',
                      'SurDepth':'Double', 
                      'Aponded':'Double'},
         'OUTFALLS':{'Name':'String',
                     'Elevation':'Double',
                     'Type':'String',
                     'Data':'String',
                     'FlapGate':'String',
                     'RouteTo':'String'}, 
         'DIVIDERS':None,
         'STORAGE':{'Name':'String',
                    'Elevation':'Double',
                    'MaxDepth':'Double',
                    'InitDepth':'Double',
                    'Type':'String',
                    'Curve':'String',
                    'Apond':'String',
                    'Fevap':'Double',
                    'Psi':'Double',
                    'Ksat':'Double',
                    'IMD':'Double'},
         'CONDUITS': {'Name':'String',
                      'FromNode':'String',
                      'ToNode':'String',
                      'Length':'Double',
                      'Roughness':'Double',
                      'InOffset':'Double',
                      'OutOffset':'Double',
                      'InitFlow':'Double',
                      'MaxFlow':'Double'},
         'PUMPS':{'Name':'String',
                  'FromNode':'String',
                  'ToNode':'String',
                  'PumpCurve':'String',
                  'Status':'String',
                  'Startup':'Double',
                  'Shutoff':'Double'},
         'ORIFICES':None,
         'WEIRS':{'Name':'String',
                  'FromNode':'String',
                  'ToNode':'String',
                  'Type':'String',
                  'CrestHeigh':'Double',
                  'Qcoeff':'Double',
                  'FlapGate':'String',
                  'EndContrac':'Double',
                  'EndCoeff':'Double',
                  'Surcharge':'String',
                  'RoadWidth':'Double',
                  'RoadSurf':'String',
                  'Coeff_Curv':'String'},
         'OUTLETS':{'Name':'String',
                  'FromNode':'String',
                  'ToNode':'String',
                  'InOffset':'Double',
                  'Rate_Curve':'String',
                  'Qcoeff':'String',
                  'Qexpon':'Double',
                  'FlapGate':'String',
                  'CurveName':'String'},
         'XSECTIONS':{'Name':'String',
                      'Shape':'String',
                      'Geom1':'Double',
                      'Geom2':'Double',
                      'Geom3':'Double',
                      'Geom4':'Double',
                      'Barrels':'Double',
                      'Culvert':'String'},
         'TRANSECTS':None,
         'LOSSES': {'Name':'String',
                    'Inlet':'Double',
                    'Outlet':'Double',
                    'Averge':'Double',
                    'FlapGate':'String',
                    'Seepage':'Double'},
         'CONTROLS':None,
         'POLLUTANTS':{'Name':'String',
                       'Units':'String',
                       'RainConcentr':'Double',
                       'GwConcentr':'Double',
                       'IiConcentr':'Double',
                       'DecayCoeff':'Double',
                       'SnowOnly':'String',
                       'CoPollutant':'String',
                       'CoFraction':'Double',
                       'DwfConcentr':'Double',
                       'InitConcetr':'Double'},
         'LANDUSES':{'Name':'String', 
                     'SweepingInterval':'Double', 
                     'SweepingFractionAvailable':'Double', 
                     'LastSwept':'Double'},
         'COVERAGES':{'Subcatchment':'String',
                      'Landuse':'String',
                      'Percent':'Double'},
         'LOADINGS':{'Subcatchment':'String',
                     'Pollutant':'String',
                     'InitialBuildup':'Double'},
         'BUILDUP':{'Name':'String',
                    'Pollutant':'String',
                    'BuildupFunction':'String', 
                    'BuildupMax':'Double', 
                    'BuildupRateConstant':'Double',
                    'BuildupExponent_SatConst':'Double',
                    'BuildupPerUnit':'String'},
         'WASHOFF':{'Name':'String', 
                    'Pollutant':'String',
                    'WashoffFunction':'String',
                    'WashoffpCoefficient':'Double', 
                    'WashoffExponenet':'Double', 
                    'WashoffCleaninfEfficiency':'Double',
                    'WashoffBmpEfficiency':'Double'},
         'TREATMENT':None,
         'INFLOWS':['Name','Constituent','Baseline',
                    'Baseline_Pattern','Time_Series',
                    'Scale_Factor','Type'],
         'DWF':['Name','Constituent','Average_Value',
                'Time_Pattern1','Time_Pattern2',
                'Time_Pattern3','Time_Pattern4'],
         'RDII':None,
         'HYDROGRAPHS':None,
         'CURVES':['Name','XVal','YVal'],
         'TIMESERIES':['Name','Date','Time','Value'],
         'PATTERNS':None,
         'COORDINATES':['Name','X_Coord','Y_Coord'],
         'VERTICES':['Name','X_Coord','Y_Coord'],
         'Polygons':['Name','X_Coord','Y_Coord'],
         'SYMBOLS':['Name','X_Coord','Y_Coord'],
         'TAGS': None}