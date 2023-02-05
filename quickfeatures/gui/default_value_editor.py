from qgis.core import QgsMapLayer
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt import uic
from pathlib import Path
from qgis.PyQt.QtWidgets import QShortcut, QItemDelegate, QComboBox, QApplication, QAction, QWidget, QLineEdit, \
    QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QLabel


class DefaultValueEditor(QDialog):

    def __init__(self, parent, map_lyr: QgsMapLayer):
        super().__init__(parent)

        # Load UI file
        uic.loadUi(Path(__file__).parent / "{}.ui".format(Path(__file__).stem), self)

        # Set modality
        self.setWindowModality(Qt.ApplicationModal)

        field_names = [field.name() for field in map_lyr.fields().toList()]

        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)


    def showEvent(self, event):
        # Show the dialog at the current mouse position
        geom = self.frameGeometry()
        geom.moveCenter(QCursor.pos())
        self.setGeometry(geom)
        super().showEvent(event)

    # def _on_editingFinished(self):
    #     self.editingFinished.emit()


    def default_values(self):
        return self.edit_line.text()