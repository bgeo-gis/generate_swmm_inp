# ![icon](/icons/icon.png) generate_swmm_inp
A QGIS plugin which provides tools to create a SWMM input file from layers in QGIS, and to import input files into QGIS. The plugin was recently updated according to new functions in SWMM 5.2. Input files from SWMM 5.1.15 will still work. 

## Documentation

[Link](https://github.com/Jannik-Schilling/generate_swmm_inp/blob/main/documentation/g_s_i_documentation_v_0_38.pdf) to the documentation file


If you use the plugin in scientific work or other studies, please cite as:
> *Schilling, J.; Tränckner, J. Generate_SWMM_inp: An Open-Source QGIS Plugin to Import and Export Model Input Files for SWMM. Water 2022, 14, 2262. https://doi.org/10.3390/w14142262*

## Provided features:
### Processing tools (will be added to the processing toolbox)

- **1_GenerateDefaultData**: Load a default set of layers to your QGIS project
- **2_GenerateSwmmInpFile**: Select a set of layers in QGIS to create an input file for a SWMM simulation

    <img src="/figures/export.png" alt= “export” width="40%">

- **3_ImportInpFile**: Import an existing SWMM model into QGIS (layers and tables).

    <img src="/figures/import.png" alt= “import” width="30%">

- **4_CreateSubModel**: Create a submodel (of an existing set of SWMM layers in QGIS) below or above a certain node

### Additional features
- style files (.qml) with **custom feature forms** for every SWMM layer; The styles will be added to the layers with the first tool. Alternatively you can download the style files or copy them from your QGIS plugin folder 
    <img src="/figures/feature_forms.png" alt= “export” width="65%">
- **import of SWMM report file sections** (see below)

## Workflow
### 0 Install 
- the generate_swmm_inp plugin in QGIS (from the official QGIS plugin repository or from zip-file)
- if needed: the python package "pandas": 
    - for windows: https://landscapearchaeology.org/2018/installing-python-packages-in-qgis-3-for-windows/
    - for linux, install via pip 
- [SWMM](https://www.epa.gov/water-research/storm-water-management-model-swmm) or other software to run the simulation ([see Links below](#further-useful-packages))

### 1 First steps in QGIS
Load a default data set with the first tool and have a look at the layers: There are separate layers for all types of "visible features" in SWMM: junctions, conduits, subcatchments, outfalls, pumps, weirs, ...
Further data is provided in tables (which will be saved in the chosen directory) and can be edited there: curves, inflows, options, patterns, quality, timeseries, ...

You can now **modify the layers** in QGIS with any processing tool. If you want to have different variants of SWMM features (e.g. planning scenarios with various combinations of conduits and junctions), creating new sets of layers (each in one .gpkg file) is recommended. 

When editing the attribute tables, the [documentation file](https://github.com/Jannik-Schilling/generate_swmm_inp/blob/main/documentation/g_s_i_documentation_v_0_29.pdf) and the [SWMM user manual](https://www.epa.gov/system/files/documents/2022-04/swmm-users-manual-version-5.2.pdf) will help you to find the right columns and suitable values. SWMM sections/infrastructures which are not implemented in the plugin yet (see [issue 2](https://github.com/Jannik-Schilling/generate_swmm_inp/issues/2)) can be added directly in SWMM later. 

Now you can write a swmm input file (.inp) and run the simulation with the second tool **(2_GenerateSwmmInpFile)**. You select the layers and tables which you want to use for your new models. The column names of the attribute tables are used by the tool in order to identify the correct information for the inp file. So be careful if you renamed or deleted any columns.
You can run the simulation directly in SWMM or with the help of scripts in R or python (see below).

### 2.1 Create new models from (any) geodata
If you already have layers/tables which you want to use in a new SWMM model, the most convenient approach is to apply the first tool **1_GenerateDefaultData** and select "empty layers". The empty layers will already have feature forms for the required fields. 
Now you can merge your existing geodata with these layers (or copy/paste selected features into the empty layers) and adjust the attribute table (e.g. using the field calculator).
When you start from scratch, a useful tool to create a network from a line layer is the QGIS plugin "WaterNetAnalyzer" (available in the [QGIS plugin repository](https://plugins.qgis.org/plugins/WaterNetAnalyzer-master/) or on [Github](https://github.com/Jannik-Schilling/WaterNetAnalyzer)).

Now apply the processing tool **(2_GenerateSwmmInpFile)** as described above.

### 2.2 Work with existing inp files (edits)
You can import existing inp files with the third tool (**3_ImportInpFile**). Creating a new folder (e.g. "swmm_data_v2") for the data is recommended. 
SWMM not necessarily requires "real" coordinates. QGIS does. So you either need to know the coordinate reference system of the input file or you can try to impoort the input file in any coordinate reference system and (move/rotate/scale) the imported features later.
You can choose a prefix (e.g. "v2") which will be added to the layers' names and the data format (.shp, .gpkg, .gml, .kml, .geojson).
Some formats seem to have problems with certain coordinate reference systems. GPKG and SHP worked fine so far.

The tool **4_CreateSubModel** allows you to simplify an existing model. Again, creating a new folder an working with a prefix for the resulting files is recommended.

### 3 run simulation / import results from report files
After you ran a simulation in SWMM (or with a python package, see below) you can add the results from a report file. You´ll find the button for the [QgisAction](https://docs.qgis.org/3.28/en/docs/training_manual/create_vector_data/actions.html) in the feature form of a SWMM layer:

<img src="/figures/action_report.png" alt= “export” width="65%">

You select the report file, the SWMM feature type and the desired report section. The resulting table will shown as a new table widget.

<img src="/figures/action_report2_n.png" alt= “export” width="65%">

You can save the table as a csv file and add it to the QGIS project (if you don´t want this, uncheck the checkbox).

<img src="/figures/action_report2.png" alt= “export” width="65%">

Now you can join the table to the SWMM layer: 

<img src="/figures/action_report3.png" alt= “export” width="65%">

There´s also a [video with a detailled instruction](https://docs.qgis.org/3.34/en/docs/training_manual/create_vector_data/actions.html) for table joins.

## Further useful packages
Python:
- [pyswmm](https://github.com/OpenWaterAnalytics/pyswmm)
- [swmm_api](https://gitlab.com/markuspichler/swmm_api) 
- [swmmio](https://github.com/aerispaha/swmmio)
- [swmmtoolbox](https://pypi.org/project/swmmtoolbox/)
- [SWMM5 for Python](https://pypi.org/project/SWMM5/)


R:
- https://github.com/cran/swmmr



## Contributing
- if you encounter any issues while using the plugin please report [here](https://github.com/Jannik-Schilling/generate_swmm_inp/issues).
- you can also propose new features and discuss them at the issues page. 
- You can fork this repository to implement your own code and send a pull request


## Funding
First versions of this plugin have been developed within the project PROSPER-RO, funded by BMBF, grant number 033L212
