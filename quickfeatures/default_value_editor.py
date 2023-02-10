# Project
from quickfeatures.__about__ import __title__
from quickfeatures.default_value_options import DefaultValueOptionModel, DefaultValueOptionDelegate

# Misc
from pathlib import Path
from typing import Dict, List

# qgis
from qgis.core import QgsMapLayer, QgsMessageLog, Qgis, QgsDefaultValue
from qgis.gui import QgsSpinBox, QgsDoubleSpinBox, QgsDateTimeEdit, QgsDateEdit

# PyQt
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSize, QModelIndex, QVariant, QAbstractTableModel, QDate
from qgis.PyQt.QtGui import QCursor, QColor, QValidator
from qgis.PyQt.QtWidgets import QShortcut, QItemDelegate, QComboBox, QApplication, QAction, QWidget, QLineEdit, \
    QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QLabel, QTableWidgetItem, QCheckBox, QHeaderView


class DefaultValueEditor(QDialog):

    def __init__(self,  map_lyr: QgsMapLayer):
        super().__init__()

        # Load UI file
        uic.loadUi(Path(__file__).parent / "gui/{}.ui".format(Path(__file__).stem), self)

        # Set modality
        self.setWindowModality(Qt.ApplicationModal)

        # Add field names
        self.table_model = None
        self.init_table(map_lyr)

        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def showEvent(self, event):
        # Show the dialog at the current mouse position
        self.resize(380, 250)
        geom = self.frameGeometry()
        geom.moveCenter(QCursor.pos())
        self.setGeometry(geom)
        super().showEvent(event)

    # def _on_editingFinished(self):
    #     self.editingFinished.emit()

    def get_default_values(self) -> Dict[str, QgsDefaultValue]:
        return self.table_model.get_selected_default_values()

    def set_default_values(self, default_values: Dict[str, QgsDefaultValue]):
        self.table_model.set_selected_default_values(default_values)

    def init_table(self, map_lyr):
        # Create model
        self.table_model = DefaultValueOptionModel(map_lyr)
        self.table_model.rowsInserted.connect(self.rows_inserted)

        # Connect view and model
        self.table_view.setModel(self.table_model)

        # Set delegates
        self.table_map_value_delegate = DefaultValueOptionDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(2, self.table_map_value_delegate)

        # Populate model
        self.table_model.add_fields(map_lyr)

        # Set Column sizes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def rows_inserted(self, parent, first, last):
        QgsMessageLog.logMessage(f"Rows inserted", tag=__title__, level=Qgis.Info)

        for row in range(first, last + 1):
            self.table_view.openPersistentEditor(self.table_model.index(row, 2))
