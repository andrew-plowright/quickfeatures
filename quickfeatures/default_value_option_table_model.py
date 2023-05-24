# Project
from quickfeatures.__about__ import __title__
from quickfeatures.default_value_option import *

# Misc
from typing import Dict
from datetime import datetime

# qgis
from qgis.core import QgsVectorLayer, QgsMessageLog, Qgis
from qgis.gui import QgsDateTimeEdit, QgsDateEdit

# PyQt
from qgis.PyQt.QtCore import Qt, QModelIndex, QVariant, QAbstractTableModel, QDate, QDateTime
from qgis.PyQt.QtWidgets import QStyledItemDelegate, QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox
from qgis.PyQt.QtGui import QColor

class DefaultValueOptionTableModel(QAbstractTableModel):
    header_labels = [
        "Select",
        "Field",
        "Value"
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.default_values_options = []

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_labels[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.default_values_options)

    def columnCount(self, index=QModelIndex(), **kwargs) -> int:
        return len(self.header_labels)

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return QVariant()

        row = index.row()
        default_val = self.default_values_options[row]

        column = index.column()
        column_header_label = self.header_labels[column]

        if role == Qt.CheckStateRole:
            if column_header_label == "Select":
                if default_val.is_selected():
                    return Qt.Checked
                else:
                    return Qt.Unchecked

        if role == Qt.DisplayRole:
            if column_header_label == "Field":
                return default_val.get_name()

        if role == Qt.ForegroundRole:
            if column_header_label == "Field":
                if not default_val.is_valid():
                    return QColor(180, 180, 180)

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags

        row = index.row()
        default_val = self.default_values_options[row]

        col = index.column()
        column_header_label = self.header_labels[col]

        if column_header_label == 'Select':
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        elif column_header_label == 'Field':
            return Qt.ItemIsEnabled
        elif column_header_label == 'Value':
            return Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled

        # elif column_header_label == 'Layer':
        #     return Qt.ItemIsEditable | Qt.ItemIsEnabled
        # else:
        #     return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setData(self, index, value, role=Qt.EditRole):

        if not index.isValid():
            return False

        row = index.row()
        default_value_option = self.default_values_options[row]

        col = index.column()
        column_header_label = self.header_labels[col]

        if column_header_label == 'Select' and role == Qt.CheckStateRole:
            default_value_option.toggle_selected()
            return True

        if column_header_label == 'Value' and role == Qt.EditRole:
            default_value_option.set_value(value)
            return True

    def set_default_values(self, map_lyr: QgsVectorLayer, default_values: Dict) -> None:

        self.clear_default_values()

        default_values_to_set = []

        # Get fields from map layer
        if map_lyr:

            field_list = map_lyr.fields().toList()

            for field in field_list:
                default_values_to_set.append(
                    DefaultValueOption(name=field.name(), data_type=field.typeName(), selected=False, valid=True)
                )

        # Get fields from default values
        for field_name in default_values:

            value = default_values[field_name]

            add_invalid_default_value = True

            for existing_default_value in default_values_to_set:
                if existing_default_value.get_name() == field_name:
                    existing_default_value.set_selected(True)
                    existing_default_value.set_value(value)
                    add_invalid_default_value = False

            if add_invalid_default_value:

                default_values_to_set.append(
                    DefaultValueOption(name=field_name, data_type=guess_editor_type(value), selected=True, valid=False, value=value)
                )

        # Add rows to model
        if default_values_to_set:

            row = self.rowCount()
            self.beginInsertRows(QModelIndex(), row, row + len(default_values_to_set) - 1)

            self.default_values_options = default_values_to_set

            self.endInsertRows()


        # QgsMessageLog.logMessage(f".... start row count {row}", tag=__title__, level=Qgis.Info)

        #QgsMessageLog.logMessage(f".... end row count {self.rowCount()}", tag=__title__, level=Qgis.Info)

    def clear_default_values(self):
        if len(self.default_values_options) > 0:

            self.beginRemoveRows(QModelIndex(), 0, self.rowCount() - 1)
            self.default_values_options.clear()
            self.endRemoveRows()

    def get_selected_default_values(self) -> Dict:
        out_values = {}
        for default_values_options in self.default_values_options:
            if default_values_options.is_selected():
                key = default_values_options.get_name()
                value = default_values_options.get_value()
                out_values[key] = value

        return out_values

    # def set_selected_default_values(self, default_values: Dict):
    #
    #     for field_name in default_values:
    #
    #         # Check if this field name exists
    #         default_value_option = None
    #         row = None
    #         for i in range(len(self.default_values_options)):
    #             if self.default_values_options[i].get_name() == field_name:
    #                 default_value_option = self.default_values_options[i]
    #                 row = i
    #
    #         # Set its value and set it as 'selected'
    #         if default_value_option:
    #
    #             default_value_option.set_selected(True)
    #             default_value_option.set_value(default_values[field_name])
    #
    #             index1 = self.createIndex(row, 0)
    #             index2 = self.createIndex(row, self.columnCount())
    #
    #             self.dataChanged.emit(index1, index2)

class DefaultValueOptionDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):

        default_val = index.model().default_values_options[index.row()]

        field_type = default_val.get_type()

        if field_type == 'Integer64' or field_type == 'Integer':
            editor = QSpinBox(parent)
            editor.setMaximum(2147483647)
            editor.setMinimum(-2147483648)

        elif field_type == 'String' or field_type == 'JSON':
            editor = QLineEdit(parent)

        elif field_type == 'Real':
            editor = QDoubleSpinBox(parent)
            editor.setMaximum(float('inf'))
            editor.setMinimum(float('-inf'))
            editor.setDecimals(7)

        elif field_type == 'Date':
            editor = QgsDateEdit(parent)

        elif field_type == 'DateTime':
            editor = QgsDateTimeEdit(parent)

        elif field_type == 'Boolean':
            editor = QCheckBox(parent)
        else:
            editor = QLineEdit(parent)

        return editor

    def setModelData(self, editor, model, index):

        default_value_option = index.model().default_values_options[index.row()]

        field_type = default_value_option.get_type()

        data = None

        if field_type == 'Integer64' or field_type == 'Integer':
            data = editor.value()

        elif field_type == 'String' or field_type == 'JSON':
            if editor.hasAcceptableInput():
                data = editor.text()

        elif field_type == 'Real':
            data = editor.value()

        elif field_type == 'Date':
            data = editor.date().toString('yyyy-MM-dd')

        elif field_type == 'DateTime':
            data = editor.dateTime().toString('yyyy-MM-dd hh:mm:ss')

        elif field_type == 'Boolean':
            data = editor.isChecked()
        else:
            ...

        if data == "":
            data = None

        model.setData(index, data)


    def setEditorData(self, editor, index):

        default_value_option = index.model().default_values_options[index.row()]

        field_type = default_value_option.get_type()
        value = default_value_option.get_value()

        if not value == '' and value is not None:
            try:
                if field_type == 'Integer64' or field_type == 'Integer':
                    editor.setValue(value)

                elif field_type == 'String' or field_type == 'JSON':

                    editor.setText(value)
                    editor.deselect()

                elif field_type == 'Real':
                    editor.setValue(value)

                elif field_type == 'Date':
                    date = QDate.fromString(value, 'yyyy-MM-dd')
                    editor.setDate(date)

                elif field_type == 'DateTime':
                    date_time = QDateTime.fromString(value, 'yyyy-MM-dd hh:mm:ss')
                    editor.setDateTime(date_time)

                elif field_type == 'Boolean':
                    editor.setChecked(value)
                else:
                    ...
            except TypeError:
                pass



def guess_editor_type(value):

    if value is None:
        return 'String'
    elif isinstance(value, str):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return 'Date'
        except:
            pass
        try:
            datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return 'DateTime'
        except:
            pass
        return 'String'
    elif isinstance(value, int):
        return 'Integer'
    elif isinstance(value, float):
        return 'Real'
    elif isinstance(value, bool):
        return 'Boolean'



