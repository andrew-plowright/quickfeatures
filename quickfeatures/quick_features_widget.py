# Project
from quickfeatures.feature_templates import FeatureTemplateTableModel, QgsMapLayerComboDelegate, DefaultValueDelegate
import quickfeatures.toolbelt.preferences as plg_prefs_hdlr
from quickfeatures.__about__ import __title__

# Standard
from pathlib import Path

# qgis
from qgis.core import QgsMessageLog, QgsProject, Qgis

# PyQt
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QWidget, QHeaderView, QFileDialog, QPushButton


class QuickFeaturesWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Load UI file
        uic.loadUi(Path(__file__).parent / "gui/{}.ui".format(Path(__file__).stem), self)

        # Initialize table
        self.table_model = None
        self.table_map_lyr_delegate = None
        self.default_value_delegate = None
        self.init_table()

        # Connect buttons
        self.load_data_button.clicked.connect(self.load_data)
        self.clear_templates_button.clicked.connect(self.table_model.clear_templates)

        # Button used for debugging purpose
        self.debug_button()

    def init_table(self):

        # Set table's model
        self.table_model = FeatureTemplateTableModel(parent=self, templates=None)
        self.table_model.rowsInserted.connect(self.rows_inserted)

        # Connect model to view
        self.table_view.setModel(self.table_model)

        # Set delegate for map layer column
        map_lyr_col = 4
        self.table_map_lyr_delegate = QgsMapLayerComboDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(map_lyr_col, self.table_map_lyr_delegate)

        # Set delegate for default values column
        default_value_col = 3
        self.default_value_delegate = DefaultValueDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(default_value_col, self.default_value_delegate)

        # Set column sizes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_view.setColumnWidth(4, 150)
        for col_num in [0, 1, 2]:
            header.setSectionResizeMode(col_num, QHeaderView.ResizeMode.ResizeToContents)

    def rows_inserted(self, parent, first, last):

        for row in range(first, last + 1):
            self.table_view.openPersistentEditor(self.table_model.index(row, 4))

    def load_data(self):

        file_name = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "JSON file (*.json)")[0]

        if file_name != '':
            self.table_model.from_json(Path(file_name))

    def clean_up(self):
        self.table_model.clear_templates()

    def debug_button(self):

        debug_mode = plg_prefs_hdlr.PlgOptionsManager.get_plg_settings().debug_mode

        QgsMessageLog.logMessage(f"Found DEBUG mode and it was '{debug_mode}'", tag=__title__, level=Qgis.Info)

        if debug_mode:
            self.load_test_data_debug = QPushButton("Load Test Data", self)
            self.debug_button = QPushButton("Debug", self)
            self.debug_button_layout.addWidget(self.load_test_data_debug)
            self.debug_button_layout.addWidget(self.debug_button)

            self.load_test_data_debug.clicked.connect(self.debug_load_test_data)
            self.debug_button.clicked.connect(self.debug_function)

    def debug_load_test_data(self):

        test_data_path = QgsProject.instance().readPath("./") + '/template_group.json'
        self.table_model.from_json(Path(test_data_path))

    def debug_function(self):
        QgsMessageLog.logMessage(f"Debug message", tag=__title__, level=Qgis.Info)

        QgsMessageLog.logMessage(f"My class is: {self.__class__.__name__}", tag=__title__, level=Qgis.Info)

        # existing_shortcuts = self.findChildren(QShortcut) + QgsGui.shortcutsManager().listShortcuts()
