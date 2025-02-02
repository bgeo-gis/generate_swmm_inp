from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QPushButton,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QComboBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    NULL
)
from qgis.PyQt import QtWidgets
from qgis.gui import QgsFileWidget
import pandas as pd
import numpy as np
import os

swmm_layer = QgsProject.instance().mapLayer('[% @layer_id %]')
# swmm_layer = iface.activeLayer()
feat_names = [f['Name'] for f in swmm_layer.getFeatures()]
layer_geom = swmm_layer.geometryType()
swmm_geom_types = {
    0: 'NODES',
    1: 'LINKS',
    2: 'SUBCATCHMENTS'
}
select_dict = {
    'NODES': {
        'JUNCIONS': [
            'node_depth',
            'node_inflow',
            'node_surcharge',
            'node_flooding'
        ],
        'OUTFALLS': [
            'node_depth',
            'node_inflow',
            'node_surcharge',
            'node_flooding',
            'outfall_loading'
        ],
        'DIVIDERS': [
            'node_depth',
            'node_inflow',
            'node_surcharge',
            'node_flooding'
        ],
        'STORAGE': [
            'node_depth',
            'node_inflow',
            'node_surcharge',
            'node_flooding',
            'storage_volume'
        ]
    },
    'LINKS': {
        'CONDUITS': [
            'link_flow',
            'flow_classification',
            'conduit_surcharge',
            'link_pollutant_load'
        ],
        'PUMPS': [
            'link_flow',
            'link_pollutant_load',
            'pumping_summary'
        ],
        'ORIFICES': [
            'link_flow',
            'flow_classification',
            'link_pollutant_load'
        ],
        'WEIRS': [
            'link_flow',
            'link_pollutant_load'
        ],
        'OUTLETS': [
            'link_flow',
            'link_pollutant_load'
        ],
    },
    'SUBCATCHMENTS': [
        'subcatchment_runoff',
        'subcatchment_washoff'
    ]
}
dict_report_line_sects = {
    'subcatchment_runoff': 'Subcatchment Runoff Summary',
    'subcatchment_washoff': 'Subcatchment Washoff Summary',
    'subcatchment_lid_performance': None,
    'subcatchment_groundwater': None,
    'node_depth': 'Node Depth Summary',
    'node_inflow': 'Node Inflow Summary',
    'node_surcharge': 'Node Surcharge Summary',
    'node_flooding': 'Node Flooding Summary',
    'storage_volume': 'Storage Volume Summary',
    'outfall_loading': 'Outfall Loading Summary',
    'street_flow': 'Street Flow Summary',
    'link_flow': 'Link Flow Summary',
    'flow_classification': 'Flow Classification Summary',
    'conduit_surcharge': 'Conduit Surcharge Summary',
    'pumping_summary': 'Pumping Summary',
    'link_pollutant_load': 'Link Pollutant Load Summary',
}


def get_header_val(header_lines, h_line, start, length):
    dist_whitespace = 2  # left whitespace in rpt file
    python_adjustment = 1  # in order to have the same vals as in Fresults.pas
    dist_whitespace = dist_whitespace + python_adjustment
    unit_line = header_lines[h_line]
    start = start - dist_whitespace
    end = start + length
    return unit_line[start:end]


def get_dict_report_cols(topic, header_lines):
    if topic == 'subcatchment_runoff':
        units_1 = get_header_val(header_lines, 2, 32, 2)
        units_2 = get_header_val(header_lines, 2, 104, 9)
        units_3 = get_header_val(header_lines, 2, 118, 4)
        cols = [
            'Name',
            'TotalPrecipitation'+'_'+units_1,
            'TotalRunon'+'_'+units_1,
            'TotalEvaporation'+'_'+units_1,
            'TotalInfiltration'+'_'+units_1,
            'ImperviousRunoff'+'_'+units_1,
            'PerviousRunoff'+'_'+units_1,
            'TotalRunoff1'+'_'+units_1,
            'TotalRunoff2'+'_'+units_2,
            'PeakRunoff'+'_'+units_3,
            'RunoffCoeffient'
        ]
    if topic == 'subcatchment_washoff':
        pol_names = header_lines[0].split()
        pol_units = header_lines[1].split()[1:]
        col_pol = [n+'_'+u for n, u in zip(pol_names, pol_units)]
        cols = ['Name'] + col_pol
    if topic == 'node_depth':
        units_1 = get_header_val(header_lines, 2, 35, 6).strip()
        cols = [
            'Name',
            'Type',
            'AverageDepth'+'_'+units_1,
            'MaximumDepth'+'_'+units_1,
            'MaximumHGL'+'_'+units_1,
            'TimeOfMaxOccurrence_Days',
            'TimeOfMaxOccurrence_HoursMin',
            'MaxReportedDepth'+'_'+units_1
        ]
    if topic == 'node_inflow':
        units_1 = get_header_val(header_lines, 3, 38, 4).strip()
        units_2 = get_header_val(header_lines, 3, 68, 8).strip()
        cols = [
            'Name',
            'Type',
            'MaximumLateralInflow'+'_'+units_1,
            'MaximumTotalInflow'+'_'+units_1,
            'TimeOfMaxOccurrence_Days',
            'TimeOfMaxOccurrence_HoursMin',
            'LateralInflowVolume'+'_'+units_2,
            'TotalInflowVolume'+'_'+units_2,
            'FlowBalanceError_Pcnt',
            'flag'
        ]
    if topic == 'node_surcharge':
        units_1 = get_header_val(header_lines, 2, 53, 6).strip()
        cols = [
            'Name',
            'Type',
            'Surcharged_Hours',
            'MaxHeightAboveCrown'+'_'+units_1,
            'MinDepthBelowRim'+'_'+units_1
        ]
    if topic == 'node_flooding':
        units_1 = get_header_val(header_lines, 3, 38, 4).strip()
        units_2 = get_header_val(header_lines, 3, 59, 9).strip()
        units_3 = get_header_val(header_lines, 3, 69, 9).strip()
        cols = [
            'Name',
            'Flooded_Hours',
            'MaximumRate'+'_'+units_1,
            'TimeOfMaxOccurrence_Days',
            'TimeOfMaxOccurrence_HoursMin',
            'TotalFloodVolume'+'_'+units_2,
            'MaximumPondedDepth'+'_'+units_3
        ]
    if topic == 'storage_volume':
        units_1 = get_header_val(header_lines, 2, 25, 9).strip()
        units_2 = get_header_val(header_lines, 2, 93, 6).strip()
        cols = [
            'Name',
            'AverageVolume'+'_'+units_1,
            'AvgFull_Pcnt',
            'EvapLoss_Pcnt',
            'ExfilLoss_Pcnt',
            'MaximumVolume'+'_'+units_1,
            'MaxFull_Pcnt',
            'TimeOfMaxOccurrence_Days',
            'TimeOfMaxOccurrence_HoursMin',
            'MaximumOutflow'+'_'+units_2
        ]
    if topic == 'outfall_loading':
        head_tokens = header_lines[1].split()
        units_1 = get_header_val(header_lines, 2, 36, 4).strip()
        units_2 = get_header_val(header_lines, 2, 54, 9).strip()
        cols = [
            'Name',
            'FlowFreq_Pcnt',
            'AvgFlow'+'_'+units_1,
            'MaxFlow'+'_'+units_1,
            'TotalVolume'+'_'+units_2
        ]
        if len(head_tokens) > 4:
            header_unit_line = header_lines[2][60:]
            header_unit_line = header_unit_line.strip()
            pol_names = head_tokens[4:]
            pol_units = header_unit_line.split()
            col_pol = ['Total'+n+'_'+u for n, u in zip(pol_names, pol_units)]
            cols = cols + col_pol
    if topic == 'street_flow':
        units_1 = get_header_val(header_lines, 3, 25, 4).strip()
        units_2 = get_header_val(header_lines, 3, 37, 2).strip()
        cols = [
            'Name',
            'PeakFlow'+'_'+units_1,
            'MaximumSpread'+'_'+units_2,
            'MaximumDepth'+'_'+units_2,
            'InletDesing',
            'InletLocation',
            'Inlet',
            'PeakFlowCapture_Pcnt',
            'AverageFlowCapture_Pcnt',
            'BypassFlowFrequnecy_Pcnt',
            'BackFlowFrequnecy_Pcnt',
            'PeakCaptureInlet'+'_'+units_1,
            'PeakBypassFlow'+'_'+units_1,
        ]
    if topic == 'link_flow':
        units_1 = get_header_val(header_lines, 2, 38, 4).strip()
        units_2 = get_header_val(header_lines, 2, 58, 6).strip()
        cols = [
            'Name',
            'Type',
            'MaximumFlow'+'_'+units_1,
            'TimeOfMaxOccurrence_Days',
            'TimeOfMaxOccurrence_HoursMin',
            'MaximumVeloc'+'_'+units_2,
            'MaxFullFlow',
            'MaxFullDepth'
        ]
    if topic == 'flow_classification':
        cols = [
            'Name',
            'AdjustedActualLength',
            'FractionOfTimeDry',
            'FractionOfTimeUpDry',
            'FractionOfTimeDownDry',
            'FractionOfTimeSubCrit',
            'FractionOfTimeSupCrit',
            'FractionOfTimeUpCrit',
            'FractionOfTimeDownCrit',
            'FractionOfTimeNormLtd',
            'FractionOfTimeInletCtrl'
        ]
    if topic == 'conduit_surcharge':
        cols = [
            'Name',
            'FullBothEnds_Hours',
            'FullUpstream_Hours',
            'FullDownstream_Hours',
            'AboveFullNormalFlow_Hours',
            'CapacityLimited_Hours',
        ]
    if topic == 'pumping_summary':
        units_1 = get_header_val(header_lines, 2, 51, 4).strip()
        units_2 = get_header_val(header_lines, 2, 76, 9).strip()
        units_3 = get_header_val(header_lines, 2, 89, 6).strip()
        cols = [
            'Name',
            'Utilized_Pcnt',
            'NumberOfStartups',
            'MinFlow'+'_'+units_1,
            'AverageFlow'+'_'+units_1,
            'MaxFlow'+'_'+units_1,
            'TotalVolume'+'_'+units_2,
            'PowerUsage'+'_'+units_3,
            'TimeBelowPumpCurve_Pcnt',
            'TimeAbovePumpCurve_Pcnt'
        ]
    if topic == 'link_pollutant_load':
        pol_names = header_lines[0].split()
        pol_units = header_lines[1].split()[1:]
        col_pol = [n+'_'+u for n, u in zip(pol_names, pol_units)]
        cols = ['Name'] + col_pol
    return cols


def build_df_from_vals_list(section_vals, col_names):
    """
    builds a dataframe for a section;
    missing vals at the end are set as np.nan
    :param list section_vals
    :param list col_names
    :return: pd.DataFrame
    """
    df = pd.DataFrame(section_vals)
    col_len = len(df.columns)
    if col_names is None:
        pass
    else:
        df.columns = col_names[0:col_len]
        if len(col_names) > col_len:  # if missing vals in inp-data
            for i in col_names[col_len:]:
                df[i] = np.nan
    return df


def find_rpt_section_position(i, rpt_line, rpt_text):
    """
    finds report sections in a list of text lines
    :param int i: index of the current text line
    :param str rpt_line: current text line
    :param list rpt_text
    """
    line_list = rpt_line.split()
    if i <= (len(rpt_text)-2):
        if line_list[0].startswith('**') and line_list[0].endswith('**'):
            line_list_2 = rpt_text[i+2].split()
            if line_list_2[0].startswith('**') and line_list_2[0].endswith('**'):
                return (i+1)
            else:
                return 'NA'
        else:
            return 'NA'
    else:
        return 'NA'


def get_rpt_df(topic, readfile):
    rpt_section_title = dict_report_line_sects[topic]
    rpt_text = get_rpt_txt(readfile)
    if rpt_section_title in rpt_text:
        startpos = rpt_text.index(rpt_section_title)
        rpt_text_trimmed = rpt_text[startpos:]
        separation_lines_0 = [
            i for i, l in enumerate(rpt_text_trimmed) if l.startswith('**') and l.endswith('**')
        ]
        if len(separation_lines_0) != 1:
            # last item
            endpos = separation_lines_0[1]
            sect_lines = rpt_text_trimmed[:endpos]
        else:
            sect_lines = rpt_text_trimmed
        separation_lines = [
            i for i, l in enumerate(sect_lines) if l.startswith('--') and l.endswith('--')
        ]
        if len(separation_lines) == 2:
            # without Summary
            separation_lines = separation_lines+[len(sect_lines)]
        sect_lines_vals = sect_lines[(separation_lines[1]+1):separation_lines[2]]
        sect_lines_vals = [x.split() for x in sect_lines_vals]
        header_lines = sect_lines[(separation_lines[0]+1):separation_lines[1]]
        col_names = get_dict_report_cols(topic, header_lines)
        df = build_df_from_vals_list(
            sect_lines_vals,
            col_names
        )
        return df
    else:
        return (pd.DataFrame())


def get_rpt_txt(readfile):
    # open file with different encodings
    encodings = [
        'utf-8',
        'windows-1250',
        'windows-1252'
    ]  # add more?
    for e in encodings:
        try:
            with open(readfile, 'r', encoding=e) as f:
                rpt_text = f.readlines()
        except UnicodeDecodeError:
            pass
        else:
            break
    rpt_text = [x for x in rpt_text if x != '\n']
    rpt_text = [x for x in rpt_text if x != '\r']
    rpt_text = [x.strip() for x in rpt_text]
    rpt_text = [x for x in rpt_text if len(x) > 0]
    # delete last three lines of the file (information on start and end time)
    rpt_text = rpt_text[:-3]
    return rpt_text


# third dialog
class saveCsvDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Save table section as CSV')
        self.df = parent.df
        self.topic = parent.topic
        self.layout = QVBoxLayout()

        # path
        self.label_CsvFile = QLabel('Resulting CSV file')
        self.layout.addWidget(self.label_CsvFile)
        self.CsvFile = QgsFileWidget()
        self.CsvFile.setFilter('CSV files (*.csv)')
        self.CsvFile.setStorageMode(3)
        self.layout.addWidget(self.CsvFile)

        # checkbox
        self.addcheckbox = QCheckBox('add resulting CSV file to Project')
        self.addcheckbox.setChecked(True)

        # OK/Cancel-Buttons
        btn2 = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(btn2)
        self.buttonBox.accepted.connect(self.save_csv_action)
        self.buttonBox.rejected.connect(self.close)

        self.layout.addWidget(self.addcheckbox)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def closeaction(self):
        self.close()

    def save_csv_action(self):
        csvpath = self.CsvFile.filePath()
        if csvpath == '':
            QtWidgets.QMessageBox.information(
                None,
                "Warning",
                'Resulting CSV file can`t be empty. Please select a file'
            )
        else:
            self.df.to_csv(csvpath, index=False)
            self.add_to_project = self.addcheckbox.isChecked()
            if self.add_to_project:
                showname = self.topic+' ('+os.path.split(csvpath)[1]+')'
                csv_layer = QgsVectorLayer(csvpath, showname, 'ogr')
                QgsProject.instance().addMapLayer(csv_layer)
            QtWidgets.QMessageBox.information(
                None,
                "Info",
                'Report data was saved in ' + csvpath
            )
            self.closeaction()


# second dialog
class showTableDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.topic = parent.topic
        self.setWindowTitle(self.topic)
        self.df = parent.df
        self.layout = QVBoxLayout()
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(
            len(self.df.columns)
        )
        self.tableWidget.setRowCount(
            len(self.df.index)
        )
        self.tableWidget.setSortingEnabled(True)
        if any([x in feat_names for x in self.df['Name']]):
            self.infotext = QLabel(
                'Features of the current layer are highlighted in yellow'
            )
        else:
            self.infotext = QLabel(
                'No features of current layer were found in this report section!'
            )
        self.layout.addWidget(self.infotext)
        for i in self.df.index:
            val0 = self.df['Name'][i]
            for j, col in enumerate(self.df.columns):
                val = self.df[col][i]
                item1 = QTableWidgetItem(str(val))
                item1.setFlags(Qt.ItemIsEditable)
                if val0 in feat_names:
                    item1.setBackground(QColor('yellow'))
                self.tableWidget.setItem(i, j, item1)
        self.tableWidget.setHorizontalHeaderLabels(
            list(self.df.columns)
        )

        # button to save csv
        self.button_save = QPushButton('Close and save table as CSV')
        self.button_save.clicked.connect(self.open_save_csv)
        self.layout.addWidget(self.button_save)
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

    def open_save_csv(self):
        self.w3 = saveCsvDialog(self)
        self.w3.show()
        self.close()


# main dialog
class joinSwmmReportDialog(QDialog):
    def __init__(self, parent=None):
        """Constructor."""
        super(joinSwmmReportDialog, self).__init__(parent)
        # Drop-down-Listen und Labels
        QDialog.__init__(self, parent)
        self.layout = QVBoxLayout()
        self.setWindowTitle('Get results from SWMM report file')

        # swmm rpt file
        self.label_SwmmRptFile = QLabel('SWMM report File')
        self.swmmRptFile = QgsFileWidget()  # rpt
        self.swmmRptFile.setFilter('SWMM report files (*.rpt)')
        self.layout.addWidget(self.label_SwmmRptFile)
        self.layout.addWidget(self.swmmRptFile)

        if swmm_type in ['NODES', 'LINKS']:
            # swmm obj type
            self.label_swmmobj_selBox = QLabel('SWMM layer type')
            self.swmmobj_selBox = QComboBox()
            self.swmmobj_list = list(select_dict[swmm_type].keys())
            self.swmmobj_selBox.addItems(self.swmmobj_list)
            self.swmmobj_selBox.setCurrentIndex(0)
            self.swmm_obj = self.swmmobj_selBox.currentText()
            self.swmmobj_selBox.currentIndexChanged.connect(self.update_topic_box)
            self.layout.addWidget(self.label_swmmobj_selBox)
            self.layout.addWidget(self.swmmobj_selBox)
            self.label_topic_selBox = QLabel('SWMM report topic')
            self.topic_selBox = QComboBox()
            self.topic_list = list(select_dict[swmm_type][self.swmm_obj])
            self.topic_selBox.addItems(self.topic_list)
            self.topic_selBox.setCurrentIndex(0)
            self.layout.addWidget(self.label_topic_selBox)
            self.layout.addWidget(self.topic_selBox)
        elif swmm_type == 'SUBCATCHMENTS':
            self.label_topic_selBox = QLabel('SWMM report topic')
            self.topic_selBox = QComboBox()
            self.topic_list = list(select_dict[swmm_type])
            self.topic_selBox.addItems(self.topic_list)
            self.topic_selBox.setCurrentIndex(0)
            self.layout.addWidget(self.label_topic_selBox)
            self.layout.addWidget(self.topic_selBox)
        else:
            QtWidgets.QMessageBox.information(
                None,
                "Warning",
                'No suitable data can be accessed'
            )
            self.close()

        # OK/Cancel-Buttons
        btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.accepted.connect(self.join_report_vals)
        self.buttonBox.rejected.connect(self.close)
        self.buttonBox.clicked.connect(self.close)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def update_topic_box(self):
        self.topic_selBox.clear()
        self.swmm_obj = self.swmmobj_selBox.currentText()
        self.topic_list_neu = list(select_dict[swmm_type][self.swmm_obj])
        self.topic_selBox.addItems(self.topic_list_neu)
        self.topic_selBox.setCurrentIndex(0)

    def join_report_vals(self):
        self.topic = self.topic_selBox.currentText()
        readfile = self.swmmRptFile.filePath()
        if readfile == '':
            QtWidgets.QMessageBox.information(
                None,
                "Warning",
                'SWMM report file can`t be empty. Please select a file'
            )
            w.show()
        else:
            self.df = get_rpt_df(self.topic, readfile)
            if len(self.df) == 0:
                QtWidgets.QMessageBox.information(
                    None,
                    "Warning",
                    (
                        'This report section is not available'
                        + ' in the chosen report file. Please '
                        + 'select another report file or topic'
                    )
                )
                w.show()
            else:
                w2 = showTableDialog(self)
                w2.show()


if layer_geom in swmm_geom_types.keys():
    swmm_type = swmm_geom_types[layer_geom]
    w = joinSwmmReportDialog()
    w.show()
else:
    QtWidgets.QMessageBox.information(
        None,
        Info",
        'Cannot show results for this data type'
    )
