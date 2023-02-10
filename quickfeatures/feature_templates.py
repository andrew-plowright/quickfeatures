# Project
from quickfeatures.default_value_editor import *
from quickfeatures.__about__ import __title__

# Misc
from typing import Dict, List
from pathlib import Path
import json

# qgis
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMessageLog, QgsDefaultValue, QgsProject, Qgis, QgsMapLayerProxyModel, QgsMapLayer
from qgis.utils import iface

# PyQt
from qgis.PyQt.QtCore import QModelIndex, Qt, QAbstractTableModel, QVariant, QObject, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QKeySequence, QColor
from qgis.PyQt.QtWidgets import QShortcut, QItemDelegate, QApplication, QAction, QDialog


class FeatureTemplate(QObject):
    # Custom signal emitted when template is activated or deactivated
    beginActivation = pyqtSignal()
    activateChanged = pyqtSignal(bool)
    validChanged = pyqtSignal(bool)

    def __init__(self, parent, name: str, shortcut_str: str, map_lyr: QgsMapLayer,
                 default_values: Dict[str, QgsDefaultValue]):

        super().__init__(parent)

        self.name = name

        # QgsMessageLog.logMessage(f"Template's parent class is: {self.parent().__class__.__name__}", tag=__title__, level=Qgis.Info)

        # Register shortcut
        self.shortcut = QShortcut(QKeySequence(), parent)
        self.shortcut.activated.connect(self.toggle)
        self.set_shortcut(shortcut_str)

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

    def get_name(self) -> str:
        return self.name

    def set_name(self, name) -> bool:
        if name is None:
            return False
        else:
            self.name = name
            return True

    def set_map_lyr(self, map_lyr):

        self.set_active(False)

        if map_lyr:
            # QgsMessageLog.logMessage(f"Loaded map layer '{map_lyr.name()}'", tag=__title__, level=Qgis.Info)
            self.map_lyr = map_lyr
            self.map_lyr.willBeDeleted.connect(lambda value=None: self.set_map_lyr(None))
            self.set_validity(True)
        else:
            # QgsMessageLog.logMessage(f"Removed map layer'", tag=__title__, level=Qgis.Info)
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
        ...
        # QgsMessageLog.logMessage(f"Confirm deletion!", tag=__title__, level=Qgis.Info)

    def delete_template(self):
        self.set_active(False)
        self.delete_shortcut()
        self.setParent(None)
        self.deleteLater()

    def get_default_values_str(self) -> str:
        vals = self.default_values
        return ', '.join([key + ': ' + vals[key].expression() for key in vals])

    def set_default_values(self, values) -> bool:
        QgsMessageLog.logMessage(f"Default values set: {values}", tag=__title__, level=Qgis.Info)

        # TO DO HERE
        # Check that all default values:
        #   - Are valid
        #   - Correspond to fields within the layer
        # If not...
        #   - Make invalid
        #   - Deactivate
        # If they ARE
        #   - Make sure that set_default_definitions gets fired again
        # Also
        #   - Use this function in __init__ so that invalid default values are caught
        return True

    def toggle(self):

        self.set_active(not self.is_active())

    def set_active(self, value) -> None:

        if value:
            if not self.is_active() and self.is_valid():
                # QgsMessageLog.logMessage(f"Activated template '{self.name}'", tag=__title__, level=Qgis.Info)

                # Emit signal
                self.beginActivation.emit()

                # Get values that will be reverted
                self.revert_values = self.get_existing_default_definitions()
                self.revert_suppress = self.get_existing_form_suppress()

                # Set default definition and suppress form
                self.set_default_definitions(self.default_values)
                self.set_form_suppress(1)

                # Set this template as active
                self.active = True
                self.activateChanged.emit(True)

        else:
            if self.active:
                # QgsMessageLog.logMessage(f"Deactivated template '{self.name}'", tag=__title__, level=Qgis.Info)

                # Revert default value definitions and form suppression settings
                self.set_default_definitions(self.revert_values)
                self.set_form_suppress(self.revert_suppress)

                # Set this template as inactive
                self.active = False
                self.activateChanged.emit(False)

    def set_shortcut(self, value) -> bool:

        if value:

            # Get list of existing shortcuts
            existing_shortcuts = []
            for widget in QApplication.topLevelWidgets():
                shortcut_keys = [shortcut.key() for shortcut in widget.findChildren(QShortcut)]
                action_keys = [action.shortcut() for action in widget.findChildren(QAction)]
                existing_shortcuts.extend(shortcut_keys)
                existing_shortcuts.extend(action_keys)

            # Check if shortcut already exists
            for sc in existing_shortcuts:
                if sc.toString() and value == sc:
                    iface.messageBar().pushMessage("Shortcut keys",
                                                   f"The shortcut keys '{value}' is already being used",
                                                   level=Qgis.Warning)
                    return False

        self.shortcut.setKey(QKeySequence(value))
        return True

    def delete_shortcut(self) -> None:
        self.shortcut.setParent(None)
        self.shortcut.deleteLater()

    def get_shortcut_str(self) -> str:
        str = self.shortcut.key().toString()
        if str == '':
            str = 'None'
        return str

    def is_valid(self) -> bool:
        return self.valid

    def is_active(self) -> bool:
        return self.active

    def set_default_definitions(self, default_values: Dict[str, QgsDefaultValue]) -> None:

        field_ids = [get_field_id(self.map_lyr, field_name) for field_name in default_values]
        def_values = [default_values[field_name] for field_name in default_values]

        for i in range(len(default_values)):
            self.map_lyr.setDefaultValueDefinition(field_ids[i], def_values[i])

    def get_existing_default_definitions(self) -> dict:

        field_names = [field_name for field_name in self.default_values]

        field_ids = [get_field_id(self.map_lyr, field_name) for field_name in field_names]
        default_values = {}

        for i in range(len(field_ids)):
            default_values[field_names[i]] = self.map_lyr.defaultValueDefinition(field_ids[i])

        return default_values

    def set_form_suppress(self, suppress: int) -> None:
        edit_form = self.map_lyr.editFormConfig()
        edit_form.setSuppress(suppress)
        self.map_lyr.setEditFormConfig(edit_form)

    def get_existing_form_suppress(self) -> int:
        return self.map_lyr.editFormConfig().suppress()


class FeatureTemplateTableModel(QAbstractTableModel):
    header_labels = [
        "Active",
        "Name",
        "Shortcut",
        "Default Values",
        "Layer",
    ]

    def __init__(self, parent, templates: List[FeatureTemplate] = None):
        super().__init__(parent)

        self.templates = []
        if templates is not None:
            self.templates = templates

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_labels[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.templates)

    def columnCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.header_labels)

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return QVariant()

        row = index.row()
        column = index.column()
        column_header_label = self.header_labels[column]

        if row >= len(self.templates):
            return QVariant()

        template = self.templates[row]

        if role == Qt.DisplayRole:
            if column_header_label == "Name":
                return template.get_name()
            elif column_header_label == "Default Values":
                return template.get_default_values_str()
            elif column_header_label == "Shortcut":
                return template.get_shortcut_str()

        if role == Qt.CheckStateRole:
            if column_header_label == "Active":
                if template.is_active():
                    return Qt.Checked
                else:
                    return Qt.Unchecked

        if role == Qt.BackgroundRole:
            if template.is_active():
                return QColor(220, 255, 220)

        if role == Qt.ForegroundRole:
            if not template.is_valid():
                return QColor(180, 180, 180)

            if column_header_label == "Shortcut":
                if template.shortcut.key().toString() == "":
                    return QColor(180, 180, 180)

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags

        column_header_label = self.header_labels[index.column()]
        template = self.templates[index.row()]

        if column_header_label == 'Active':
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        if column_header_label == 'Default Values' and not template.is_valid():
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable

        # elif column_header_label == 'Layer':
        #     return Qt.ItemIsEditable | Qt.ItemIsEnabled
        # else:
        #     return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role=Qt.EditRole):

        if not index.isValid():
            return False

        column_header_label = self.header_labels[index.column()]
        template = self.templates[index.row()]

        if column_header_label == 'Active' and role == Qt.CheckStateRole:
            template.toggle()
            return True

        if column_header_label == 'Layer' and role == Qt.EditRole:
            template.set_map_lyr(value)
            self.dataChanged.emit(index, index)
            return True

        if column_header_label == 'Shortcut':
            if value == "":
                value = None
            return template.set_shortcut(value)

        if column_header_label == 'Name':
            if value == "":
                value = None
            return template.set_name(value)

        if column_header_label == 'Default Values':
            if value == "":
                value = None
            return template.set_default_values(value)

    def add_templates(self, templates: List[FeatureTemplate]) -> None:

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

        # QgsMessageLog.logMessage(f"Loaded map layer '{self.sender()}'", tag=__title__, level=Qgis.Info)

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

    def remove_template(self, template: FeatureTemplate) -> None:
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
            print({f"Template: '{tp.get_name()}', Active: {str(tp.is_active())}"})

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

            template = FeatureTemplate(parent=self.parent(), name=d['name'], shortcut_str=d['shortcut_str'],
                                       map_lyr=map_lyr, default_values=default_values)
            templates.append(template)

        self.add_templates(templates)


class QgsMapLayerComboDelegate(QItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QgsMapLayerComboBox(parent)
        editor.setFilters(QgsMapLayerProxyModel.VectorLayer)
        editor.setAllowEmptyLayer(True)
        editor.layerChanged.connect(self.layerSelected)
        return editor

    def setEditorData(self, editor, index):
        map_lyr = index.model().templates[index.row()].map_lyr
        editor.setLayer(map_lyr)

    def setModelData(self, editor, model, index):
        data = editor.currentLayer()
        model.setData(index, data)

    @pyqtSlot()
    def layerSelected(self):
        # This function simply closes the editor when a layer is selected so
        # that the model data is changed immediately

        # self.commitData.emit(self.sender())
        self.closeEditor.emit(self.sender())


class DefaultValueDelegate(QItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        map_lyr = index.model().templates[index.row()].map_lyr
        editor = DefaultValueEditor(map_lyr)
        # editor.setWindowFlags(Qt.Popup)
        return editor

    def setModelData(self, editor, model, index):
        if editor.result() == QDialog.Accepted:
            data = editor.get_default_values()
            model.setData(index, data)

    def setEditorData(self, editor, index):
        template = index.model().templates[index.row()]
        editor.set_default_values(template.default_values)


def get_field_id(map_lyr: QgsMapLayer, field_name: str) -> int:
    field_idx = map_lyr.fields().indexFromName(field_name)

    if field_idx == -1:
        raise Exception(f"Could not find '{field_name}'")

    return field_idx