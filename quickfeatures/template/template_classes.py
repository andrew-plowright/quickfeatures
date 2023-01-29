from quickfeatures.template.template_functions import *
from typing import Dict, List
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMessageLog, QgsDefaultValue, QgsProject, Qgis
from qgis.utils import iface
from quickfeatures.__about__ import __title__
from qgis.PyQt.QtCore import QModelIndex, Qt, QAbstractTableModel, QVariant, QObject, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QKeySequence, QColor
from qgis.PyQt.QtWidgets import QShortcut, QItemDelegate, QComboBox
from pathlib import Path
import json


class Template(QObject):
    # Custom signal emitted when template is activated or deactivated
    beginActivation = pyqtSignal()
    activateChanged = pyqtSignal(bool)
    validChanged = pyqtSignal(bool)

    def __init__(self, parent, name: str, shortcut_str: str, map_lyr: QgsMapLayer,
                 default_values: Dict[str, QgsDefaultValue]):

        super().__init__(parent)

        self.name = name

        # Register shortcut
        self.shortcut_str = shortcut_str
        self.shortcut = None
        self.register_shortcut(parent)

        # Store default values and 'dialog suppression' setting for when template is deactivated
        self.default_values = default_values
        self.revert_suppress = 0
        self.revert_values = {}

        # Switches
        self.active = False
        self.valid = False

        # Set map layer
        self.map_lyr = None
        self.set_map_lyr(map_lyr)

        self.destroyed.connect(self.confirm_deletion)

    def set_map_lyr(self, map_lyr):

        self.set_active(False)

        if map_lyr:
            QgsMessageLog.logMessage(f"Loaded map layer '{map_lyr.name()}'", tag=__title__, level=Qgis.Info)
            self.map_lyr = map_lyr
            self.map_lyr.willBeDeleted.connect(lambda value=None : self.set_map_lyr(None))
            self.set_validity(True)
        else:
            QgsMessageLog.logMessage(f"Removed map layer'", tag=__title__, level=Qgis.Info)
            self.map_lyr = None
            self.set_active(False)
            self.set_validity(False)


    def map_lyr_name(self) -> str:
        if self.map_lyr:
            return self.map_lyr.name()
        else:
            return 'None'

    def set_validity(self, value):
        if value:
            if not self.valid:
                self.valid = True
                self.validChanged.emit(True)
        else:
            if self.valid:
                self.valid = False
                self.validChanged.emit(False)

    @staticmethod
    def confirm_deletion(self):
        QgsMessageLog.logMessage(f"Confirm deletion!", tag=__title__, level=Qgis.Info)

    def delete_template(self):
        self.set_active(False)
        self.unregister_shortcut()
        self.setParent(None)
        self.deleteLater()

    def default_values_to_str(self) -> str:
        vals = self.default_values
        return ', '.join([key + ': ' + vals[key].expression() for key in vals])

    def toggle(self):

        self.set_active(not self.is_active())

    def set_active(self, value) -> None:

        if value:
            if not self.is_active() and self.is_valid():
                QgsMessageLog.logMessage(f"Activated template '{self.name}'", tag=__title__, level=Qgis.Info)

                # Emit signal
                self.beginActivation.emit()

                # Get values that will be reverted
                field_names = [field_name for field_name in self.default_values]
                self.revert_values = get_existing_default_definitions(self.map_lyr, field_names)
                self.revert_suppress = get_existing_form_suppress(self.map_lyr)

                # Set default definition and suppress form
                set_default_definitions(self.map_lyr, self.default_values)
                set_form_suppress(self.map_lyr, 1)

                # Set this template as active
                self.active = True

                # Emit signal
                self.activateChanged.emit(True)

        else:
            if self.active:
                QgsMessageLog.logMessage(f"Deactivated template '{self.name}'", tag=__title__, level=Qgis.Info)

                # Revert default value definitions and form suppression settings
                set_default_definitions(self.map_lyr, self.revert_values)
                set_form_suppress(self.map_lyr, self.revert_suppress)

                # Set this template as inactive
                self.active = False

                # Emit signal
                self.activateChanged.emit(False)

    def register_shortcut(self, parent) -> None:

        self.shortcut = QShortcut(QKeySequence(self.shortcut_str), parent)
        self.shortcut.activated.connect(self.toggle)

    def unregister_shortcut(self) -> None:

        self.shortcut.setParent(None)
        self.shortcut.deleteLater()

    def is_valid(self) -> bool:
        return self.valid

    def is_active(self) -> bool:
        return self.active


class TemplateTableModel(QAbstractTableModel):
    header_labels = [
        "Active",
        "Shortcut",
        "Name",
        "Default Values",
        "Map Layer",
    ]

    templates = []

    def __init__(self, parent=None, templates: List[Template] = None):
        super().__init__(parent)
        if templates is not None:
            self.templates = templates

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_labels[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.templates)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.header_labels)

    def data(self, index, role):

        if not index.isValid():
            return QVariant()

        row = index.row()
        column = index.column()
        column_header_label = self.header_labels[column]

        if row >= len(self.templates):
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole:
            if column_header_label == "Name":
                return self.templates[row].name
            elif column_header_label == "Default Values":
                return self.templates[row].default_values_to_str()
            elif column_header_label == "Shortcut":
                return self.templates[row].shortcut_str

        if role == Qt.CheckStateRole:
            if column_header_label == "Active":
                if self.templates[row].active:
                    return Qt.Checked
                else:
                    return Qt.Unchecked

        if role == Qt.ForegroundRole:
            if not self.templates[row].is_valid():
                return QColor(200, 200, 200)

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags

        column_header_label = self.header_labels[index.column()]

        if column_header_label == 'Active':
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        elif column_header_label == 'Map Layer':
            return Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

        # elif column_header_label == 'Map Layer':
        #     return Qt.ItemIsEditable | Qt.ItemIsEnabled
        # else:
        #     return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role=Qt.EditRole):

        if not index.isValid():
            return False

        column_header_label = self.header_labels[index.column()]

        if column_header_label == 'Active' and role == Qt.CheckStateRole:
            template = self.templates[index.row()]
            template.toggle()
            return True

        if column_header_label == 'Map Layer' and role == Qt.EditRole:
            template = self.templates[index.row()]
            template.set_map_lyr(value)
            self.dataChanged.emit(index, index)
            return True


    def add_templates(self, templates: List[Template]) -> None:

        row = self.rowCount()

        self.beginInsertRows(QModelIndex(), row, row + len(templates) - 1)

        for template in templates:
            self.templates.append(template)

            template.beginActivation.connect(self.deactivate_other_templates)

            template.activateChanged.connect(self.refresh_template)
            template.validChanged.connect(self.refresh_template)

        self.endInsertRows()

    @pyqtSlot()
    def refresh_template(self) -> None:

        #QgsMessageLog.logMessage(f"Loaded map layer '{self.sender()}'", tag=__title__, level=Qgis.Info)

        row = self.templates.index(self.sender())

        index1 = self.createIndex(row, 0)
        index2 = self.createIndex(row, self.columnCount())

        self.dataChanged.emit(index1, index2)

        # col = self.header_labels.index('Active')
        # index_start = self.createIndex(0, col)
        # index_end = self.createIndex(self.rowCount() - 1, col)
        # self.dataChanged.emit(index_start, index_end)

    @pyqtSlot()
    def deactivate_other_templates(self) -> None:

        template = self.sender()

        for row in range(len(self.templates)):
            if not self.templates[row] == template:
                self.templates[row].set_active(False)

    def remove_template(self, template: Template) -> None:
        try:
            row = self.templates.index(template)

            self.beginRemoveRows(QModelIndex(), row, row)

            template.delete_template()

            self.templates.remove(template)

            self.endRemoveRows()

        except ValueError:
            print(f'Template not found')

    def clear_templates(self):
        if len(self.templates) > 0:

            self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)

            for template in self.templates:

                template.delete_template()

            self.templates.clear()

            self.endRemoveRows()

    def print_templates(self) -> None:
        for tp in self.templates:
            print({f"Template: '{tp.name}', Active: {str(tp.active)}"})

    def from_json(self, path: Path):

        with open(path) as f:
            data = json.load(f)

        self.clear_templates()

        templates = []

        for d in data:

            default_values = {key: QgsDefaultValue(f"'{value}'") for key, value in d['default_values'].items()}

            map_lyr_name = d['map_lyr_name']
            map_lyrs = QgsProject().instance().mapLayersByName(map_lyr_name)

            map_lyr = None
            if len(map_lyrs) == 1:
                map_lyr = map_lyrs[0]
            elif len(map_lyrs) > 1:
                iface.messageBar().pushMessage("Multiple layers",
                                               f"Found multiple layers named {map_lyr_name}",
                                               level=Qgis.Warning, duration=3)
            else:
                iface.messageBar().pushMessage("Layer not found",
                                               f"Could not find a layer named {map_lyr_name}",
                                               level=Qgis.Warning, duration=3)

            template = Template(parent=self.parent(), name=d['name'], shortcut_str=d['shortcut_str'],
                                map_lyr=map_lyr, default_values=default_values)
            templates.append(template)

        self.add_templates(templates)


class QgsMapLayerComboDelegate(QItemDelegate):

    def __init__(self, parent):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QgsMapLayerComboBox(parent)
        combo.setAllowEmptyLayer(True)
        combo.layerChanged.connect(self.layerSelected)
        return combo

    def setEditorData(self, editor, index):
        map_lyr = index.model().templates[index.row()].map_lyr
        editor.setLayer(map_lyr)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentLayer())

    @pyqtSlot()
    def layerSelected(self):
        # This function simply closes the editor when a layer is selected so
        # that the model data is changed immediately

        #self.commitData.emit(self.sender())
        self.closeEditor.emit(self.sender())
