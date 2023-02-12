# Project
from quickfeatures.__about__ import __title__

# Misc
from typing import Dict, List
import sys

# qgis
from qgis.core import QgsMapLayer, QgsMessageLog, Qgis, QgsDefaultValue, QgsVectorLayer
from qgis.gui import QgsSpinBox, QgsDoubleSpinBox, QgsDateTimeEdit, QgsDateEdit

# PyQt
from qgis.PyQt.QtCore import Qt, QSize, QModelIndex, QVariant, QAbstractTableModel, QDate, QDateTime
from qgis.PyQt.QtWidgets import QShortcut, QItemDelegate, QStyledItemDelegate, QComboBox, QApplication, QAction, QWidget, QLineEdit, \
    QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QLabel, QTableWidgetItem, QCheckBox, QHeaderView, QSpinBox, QDoubleSpinBox


class DefaultValueOption():

    def __init__(self, name: str, data_type: str):
        self.value = None
        self.selected = False
        self.valid = True
        self.name = name
        self.type = data_type

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> str:
        return self.type

    def is_valid(self) -> bool:
        return self.valid

    def is_selected(self) -> bool:
        return self.selected

    def toggle_selected(self):
        self.set_selected(not self.is_selected())

    def set_selected(self, value) -> None:

        if value:
            if not self.is_selected() and self.is_valid():
                self.selected = True
        else:
            if self.is_selected():
                self.selected = False


class DefaultValueOptionModel(QAbstractTableModel):
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


    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags

        row = index.row()
        default_val = self.default_values_options[row]

        col = index.column()
        column_header_label = self.header_labels[col]

        if not default_val.is_valid():
            return Qt.ItemIsEnabled

        if column_header_label == 'Select':
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        if column_header_label == 'Field':
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

    def add_fields(self, map_lyr: QgsVectorLayer) -> None:

        row = self.rowCount()

        if map_lyr:
            fields = map_lyr.fields().toList()

            self.beginInsertRows(QModelIndex(), row, row + len(fields) - 1)

            for field in fields:
                default_val = DefaultValueOption(name=field.name(), data_type=field.typeName())

                self.default_values_options.append(default_val)

            self.endInsertRows()

    def get_selected_default_values(self) -> Dict:
        out_values = {}
        for default_values_options in self.default_values_options:
            if default_values_options.is_selected():
                key = default_values_options.get_name()
                value = default_values_options.get_value()
                out_values[key] = value

        return out_values

    def set_selected_default_values(self, set_default_values: Dict):

        for field_name in set_default_values:

            # Check if this field name exists
            default_value_option = None
            row = None
            for i in range(len(self.default_values_options)):
                if self.default_values_options[i].get_name() == field_name:
                    default_value_option = self.default_values_options[i]
                    row = i

            # Set its value and set it as 'selected'
            if default_value_option:

                # QgsMessageLog.logMessage(f"set_selected_default_values: [{default_value_option.get_name()}] to [{set_default_values[field_name].expression()}]",
                #                          tag=__title__,
                #                          level=Qgis.Info)

                default_value_option.set_selected(True)
                default_value_option.set_value(set_default_values[field_name])

                index1 = self.createIndex(row, 0)
                index2 = self.createIndex(row, self.columnCount())

                self.dataChanged.emit(index1, index2)

class DefaultValueOptionDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    # def paint(self, painter, option, index):
    #     self.parent().openPersistentEditor(index)
    #     super().paint(painter, option, index)


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

        # QgsMessageLog.logMessage(
        #     f"\nValue [{data}]\n  - Type: [{type(data).__name__}]\n  - None: [{data == None}]",
        #     tag=__title__, level=Qgis.Info)


        model.setData(index, data)


    def setEditorData(self, editor, index):

        default_value_option = index.model().default_values_options[index.row()]

        field_type = default_value_option.get_type()
        value = default_value_option.get_value()

        # QgsMessageLog.logMessage(f"\nsetEditorData"
        #                          f"\n  Field   : [{default_value_option.get_name()}]"
        #                          f"\n  Checked : [{default_value_option.is_selected()}]"
        #                          f"\n  Current : [{default_value_option.get_value()}] "
        #                          f"\n  New val : [{value}]",
        #                          tag=__title__, level=Qgis.Info)

        if not value == '' and value is not None:

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
