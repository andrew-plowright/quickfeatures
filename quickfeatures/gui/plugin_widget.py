#! python3  # noqa: E265

"""
    Plugin settings form integrated into QGIS 'Options' menu.
"""

from pathlib import Path
from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QWidget, QAction, QTableWidgetItem, QHeaderView, QButtonGroup, QRadioButton, QFileDialog
from quickfeatures.__about__ import __title__
from quickfeatures.template.template_classes import TemplateTableModel, QgsMapLayerComboDelegate

from qgis.PyQt.QtCore import Qt

class MyPluginWidget(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.table_model = None

        # Load UI file
        uic.loadUi(Path(__file__).parent / "{}.ui".format(Path(__file__).stem), self)

        # Initialize table
        self.init_table()

        # Connect buttons
        self.load_data_button.clicked.connect(self.load_data)
        self.clear_templates_button.clicked.connect(self.table_model.clear_templates)

    def init_table(self):

        # Set table's model
        self.table_model = TemplateTableModel(parent=self, templates=None)
        self.table_model.rowsInserted.connect(self.rows_inserted)

        # Connect model to view
        self.table_view.setModel(self.table_model)

        # Set delegate
        map_lyr_col = 4
        self.table_map_lyr_delegate = QgsMapLayerComboDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(map_lyr_col, self.table_map_lyr_delegate)

        # Set column sizes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_view.setColumnWidth(4, 100)
        for col_num in [0, 1, 2]:
            header.setSectionResizeMode(col_num, QHeaderView.ResizeMode.ResizeToContents)

    def rows_inserted(self, parent, first, last):

        for row in range(first, last + 1):
            self.table_view.openPersistentEditor(self.table_model.index(row, 4))

    def load_data(self):

        fname = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\', "JSON file (*.json)")

        self.table_model.from_json(Path(fname[0]))
