# Project
from quickfeatures.default_value_editor import *
from quickfeatures.feature_templates import FeatureTemplate
from quickfeatures.__about__ import __title__

# Misc
from typing import List
from pathlib import Path
import json

# qgis
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsProject, QgsMapLayerProxyModel, QgsMessageLog, Qgis, QgsVectorLayer

# PyQt
from qgis.PyQt.QtCore import QModelIndex, Qt, QAbstractTableModel, QVariant, QSize, pyqtSlot
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QItemDelegate, QStyledItemDelegate, QDialog, QPushButton
from qgis.PyQt.QtXml import QDomElement


class FeatureTemplateTableModel(QAbstractTableModel):

    header_labels = [
        "Active",
        "Name",
        "Shortcut",
        "Layer",
        "Values",
        "Remove",
    ]

    def __init__(self, parent):
        super().__init__(parent)

        self.templates = []
        self.highlight_brush = parent.palette().highlight()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            header_name = self.header_labels[section]
            if header_name == 'Active':
                return None
            else:
                return header_name
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
                return self.highlight_brush

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

        if column_header_label == 'Active':
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        column_header_label = self.header_labels[index.column()]
        template = self.templates[index.row()]

        if column_header_label == 'Active' and role == Qt.CheckStateRole:
            template.toggle_active()
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

        if column_header_label == 'Values':
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

    def get_templates(self):
        return self.templates

    def from_json(self, path: Path):
        self.clear_templates()

        templates = []

        qgs_project = QgsProject().instance()

        with open(path) as f:
            data = json.load(f)

        for d in data:
            map_lyr = vector_lyr_by_name(qgs_project, d['map_lyr_name'])

            template = FeatureTemplate(parent=self, widget=self.parent(), name=d['name'],
                                       shortcut_str=d['shortcut_str'],
                                       map_lyr=map_lyr, default_values=d['default_values'])

            templates.append(template)

        self.add_templates(templates)

    def to_json(self, path: Path):
        templates = self.get_templates()

        out_list = []

        for template in templates:

            template_json = {
                'name': template.get_name(),
                'map_lyr_name': template.map_lyr.name(),
                'default_values': template.get_default_values(),
                'shortcut_str': template.get_shortcut_str()
            }

            out_list.append(template_json)

        json_object = json.dumps(out_list, indent=4)

        with open(path, "w") as outfile:
            outfile.write(json_object)


    def from_xml(self, elem: QDomElement):
        self.clear_templates()

        templates = []

        qgs_project = QgsProject().instance()

        template_elems = elem.childNodes()

        for i in range(template_elems.length()):

            template_elem = template_elems.item(i)
            template_attr = template_elem.attributes()

            name = template_attr.namedItem('name').nodeValue()
            shortcut_str = template_attr.namedItem('shortcut').nodeValue()
            map_lyr_name = template_attr.namedItem('map_lyr').nodeValue()

            default_values = {}
            default_value_elems = template_elem.namedItem('default_values').childNodes()

            # QgsMessageLog.logMessage(f"Template '{name}' has {default_value_elems.length()} default values", tag=__title__, level=Qgis.Warning)

            for i in range(default_value_elems.length()):

                default_value_elem = default_value_elems.item(i)
                default_value_attr = default_value_elem.attributes()

                field = default_value_attr.namedItem('field').nodeValue()
                value = default_value_attr.namedItem('value').nodeValue()

                default_values[field] = value

            map_lyr = vector_lyr_by_name(qgs_project, map_lyr_name)

            template = FeatureTemplate(parent=self, widget=self.parent(), name=name, shortcut_str=shortcut_str,
                                       map_lyr=map_lyr, default_values=default_values)

            templates.append(template)

        self.add_templates(templates)


class QgsMapLayerComboDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        editor = QgsMapLayerComboBox(parent)
        editor.setFilters(QgsMapLayerProxyModel.VectorLayer)
        editor.setAllowEmptyLayer(True)
        editor.layerChanged.connect(lambda: self.closeEditor.emit(editor))
        return editor

    def setEditorData(self, editor, index):
        map_lyr = index.model().templates[index.row()].map_lyr
        editor.setLayer(map_lyr)

    def setModelData(self, editor, model, index):
        data = editor.currentLayer()
        model.setData(index, data)


class DefaultValueDelegate(QItemDelegate):

    def __init__(self, parent, table_icon):
        super().__init__(parent)
        self.table_icon = table_icon

    def createEditor(self, parent, option, index):
        editor = QPushButton(parent)

        editor.setIcon(self.table_icon)
        editor.setIconSize(QSize(20, 20))

        editor.dialog = DefaultValueEditor(parent)
        editor.dialog.accepted.connect(lambda: self.commitData.emit(editor))

        editor.clicked.connect(lambda: self.init_dialog(editor, index))
        return editor

    def setEditorData(self, editor, index):
        # This is a bit of a hack, but the editor's data is getting populated in
        # 'init_diolog' instead, given that I want this to happen every time
        # the button is clicked
        ...

    def setModelData(self, editor, model, index):

        # Only set model data if dialog was accepted
        if editor.dialog.result() == QDialog.Accepted:
            data = editor.dialog.get_editor_default_values()
            model.setData(index, data)

            # Reset result of dialog
            editor.dialog.setResult(QDialog.Rejected)

    # Populate the dialog and then open it`
    def init_dialog(self, editor, index):
        template = index.model().templates[index.row()]
        editor.dialog.populate_table(template.map_lyr, template.get_default_values())
        editor.dialog.open()


class RemoveDelegate(QItemDelegate):

    def __init__(self, parent, delete_icon):
        super().__init__(parent)
        self.delete_icon = delete_icon

    def createEditor(self, parent, option, index):
        model = index.model()
        template = model.templates[index.row()]
        editor = QPushButton(parent)
        editor.setIcon(self.delete_icon)
        editor.setIconSize(QSize(20, 20))
        editor.clicked.connect(lambda: model.remove_template(template))
        # editor.setWindowFlags(Qt.Popup)
        return editor

    def setModelData(self, editor, model, index):
        model.setData(index, True)


def vector_lyr_by_name(qgs_project: QgsProject, name):

    # Get all map layers with this name
    map_lyrs = qgs_project.mapLayersByName(name)

    # Filter out anything that is not a vector layer
    vec_lyrs = [map_lyr for map_lyr in map_lyrs if isinstance(map_lyr, QgsVectorLayer)]

    vec_lyr = None

    if len(vec_lyrs) > 0:
        vec_lyr = vec_lyrs[0]

    return vec_lyr
