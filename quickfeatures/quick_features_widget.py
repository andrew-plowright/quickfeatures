# Project
from quickfeatures.feature_templates import FeatureTemplateTableModel, QgsMapLayerComboDelegate, DefaultValueDelegate
from quickfeatures.__about__ import __title__

# Standard
from pathlib import Path
import os

# qgis
from qgis.core import QgsMessageLog, QgsProject, Qgis, QgsApplication

# PyQt
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QHeaderView, QFileDialog, QPushButton, QToolBar, QAction


class QuickFeaturesWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.icon_dir = os.path.join(os.path.dirname(__file__), "resources/icons")

        # Load UI file
        uic.loadUi(Path(__file__).parent / "gui/{}.ui".format(Path(__file__).stem), self)

        # Initialize table
        self.table_model = None
        self.table_map_lyr_delegate = None
        self.default_value_delegate = None
        self.init_table()

        # Actions
        self.action_add_template = QAction(QIcon(os.path.join(self.icon_dir, 'mActionAdd.svg')), "Add template", self)
        self.action_add_template.setStatusTip("Add templates")
        #self.action_add_template.triggered.connect()

        self.action_clear_templates = QAction(QIcon(os.path.join(self.icon_dir, 'iconClearConsole.svg')), "Clear templates", self)
        self.action_clear_templates.setStatusTip("Clear templates")
        self.action_clear_templates.triggered.connect(self.table_model.clear_templates)

        self.action_load_templates = QAction(QIcon(os.path.join(self.icon_dir, 'mActionFileOpen.svg')), "Load templates", self)
        self.action_load_templates.setStatusTip("Load templates")
        self.action_load_templates.triggered.connect(self.load_data)

        self.action_save_templates = QAction(QIcon(os.path.join(self.icon_dir, 'mActionFileSave.svg')), "Save templates", self)
        self.action_save_templates.setStatusTip("Save templates")
        #self.action_save_templates.triggered.connect(self.table_model.clear_templates)

        # Toolbar
        self.toolbar = QToolBar()
        self.toolbar_layout.addWidget(self.toolbar)
        self.toolbar.addAction(self.action_add_template)
        self.toolbar.addAction(self.action_clear_templates)
        self.toolbar.addAction(self.action_load_templates)
        self.toolbar.addAction(self.action_save_templates)
        self.toolbar.setIconSize(QSize(18,18))

        # Button used for debugging purpose
        self.add_debug_actions()

    def init_table(self):

        # Set table's model
        self.table_model = FeatureTemplateTableModel(parent=self, templates=None)

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

    def load_data(self):

        file_name = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "JSON file (*.json)")[0]

        if file_name != '':
            self.table_model.from_json(Path(file_name))

        self.table_view.resizeColumnToContents(1)

    def clean_up(self):
        self.table_model.clear_templates()

    def add_debug_actions(self):

        debug_mode = True
        # QgsMessageLog.logMessage(f"Found DEBUG mode and it was '{debug_mode}'", tag=__title__, level=Qgis.Info)

        if debug_mode:

            self.action_testdata = QAction(QIcon(QgsApplication.iconPath("mIconFolderOpen.svg")),
                                                 "Load Test Data", self)
            self.action_debug = QAction(QIcon(QgsApplication.iconPath("mIndicatorBadLayer.svg")),
                                                 "Debug", self)

            self.action_testdata.triggered.connect(self.testdata)
            self.action_debug.triggered.connect(self.debug)

            self.toolbar.addAction(self.action_testdata)
            self.toolbar.addAction(self.action_debug)


    def testdata(self):

        test_data_path = QgsProject.instance().readPath("./") + '/template_group.json'
        self.table_model.from_json(Path(test_data_path))
        self.table_view.resizeColumnToContents(1)

    def debug(self):
        QgsMessageLog.logMessage(f"Debug message", tag=__title__, level=Qgis.Info)

        #QgsMessageLog.logMessage(f"My class is: {self.__class__.__name__}", tag=__title__, level=Qgis.Info)
        QgsMessageLog.logMessage(f"My palette is: {type(self.palette()).__name__}", tag=__title__, level=Qgis.Info)

        # existing_shortcuts = self.findChildren(QShortcut) + QgsGui.shortcutsManager().listShortcuts()
