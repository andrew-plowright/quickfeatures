#! python3  # noqa: E265

"""
    Plugin settings form integrated into QGIS 'Options' menu.
"""

from pathlib import Path
from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QWidget, QAction, QTableWidgetItem, QHeaderView, QButtonGroup, QRadioButton
from quick_feature_create.__about__ import __title__
from quick_feature_create.template.template_classes import TemplateTableModel


class MyPluginWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        # Load UI file
        uic.loadUi(Path(__file__).parent / "{}.ui".format(Path(__file__).stem), self)

        self.init_table()

        # Connect buttons
        self.load_data_button.clicked.connect(self.load_data)
        self.clear_templates_button.clicked.connect(self.table_model.clear_templates)

    def load_data(self):

        self.table_model.from_json(
            Path('C:/Users/aplowrig/Work/dev/qgis_plugins/quick_feature_create/template_group.json'))

        QgsMessageLog.logMessage(f"Loaded {len(self.table_model.templates)} templates", tag=__title__, level=Qgis.Success)

    def init_table(self):

        # Set table's model
        self.table_model = TemplateTableModel(parent=self, templates=None)
        self.table_view.setModel(self.table_model)

        # Set column stretches
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

