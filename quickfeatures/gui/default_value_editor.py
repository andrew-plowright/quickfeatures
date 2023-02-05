from quickfeatures.__about__ import __title__

from pathlib import Path
from typing import Dict, List

from qgis.core import QgsMapLayer, QgsMessageLog, Qgis, QgsDefaultValue
from qgis.gui import QgsSpinBox, QgsDoubleSpinBox, QgsDateTimeEdit, QgsDateEdit

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSize, QModelIndex, QVariant, QAbstractTableModel, QDate
from qgis.PyQt.QtGui import QCursor, QColor, QValidator
from qgis.PyQt.QtWidgets import QShortcut, QItemDelegate, QComboBox, QApplication, QAction, QWidget, QLineEdit, \
    QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QLabel, QTableWidgetItem, QCheckBox, QHeaderView


class DefaultValueEditor(QDialog):

    def __init__(self, parent, map_lyr: QgsMapLayer):
        super().__init__(parent)

        # Load UI file
        uic.loadUi(Path(__file__).parent / "{}.ui".format(Path(__file__).stem), self)

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
        self.table_model = DefaultValueModel(map_lyr)
        self.table_model.rowsInserted.connect(self.rows_inserted)

        # Connect view and model
        self.table_view.setModel(self.table_model)

        # Set delegates
        self.table_map_value_delegate = ValueDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(2, self.table_map_value_delegate)

        # Populate model
        self.table_model.add_fields(map_lyr)

        # Set Column sizes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)


    def rows_inserted(self, parent, first, last):

        QgsMessageLog.logMessage(f"Rows inserted", tag=__title__,level=Qgis.Info)

        for row in range(first, last + 1):
            self.table_view.openPersistentEditor(self.table_model.index(row, 2))

    def init_table2(self, map_lyr: QgsMapLayer):

        background_col = self.palette().window().color()

        for field in map_lyr.fields().toList():

            row = self.value_table.rowCount()
            self.value_table.insertRow(row)

            field_name = field.name()
            field_name_widget = QTableWidgetItem(field_name)
            field_name_widget.setFlags(Qt.ItemIsEnabled)
            field_name_widget.setBackground(background_col)
            self.value_table.setItem(row, 0, field_name_widget)

            field_type = field.typeName()

            if field_type == 'Integer64' or field_type == 'integer':
                spin_box = QgsSpinBox()
                spin_box.setClearValue(None)
                self.value_table.setCellWidget(row , 1, spin_box)

            elif field_type == 'String' or field_type == 'JSON':
                self.value_table.setItem(row, 1, QTableWidgetItem())

            elif field_type == 'Real':
                self.value_table.setCellWidget(row, 1, QgsDoubleSpinBox())

            elif field_type == 'Date':
                date_time_edit = QgsDateTimeEdit()
                self.value_table.setCellWidget(row, 1, date_time_edit)

            elif field_type == 'datetime':
                date_time_edit = QgsDateTimeEdit()
                self.value_table.setCellWidget(row, 1, date_time_edit)

            elif field_type == 'boolean':
                check_box = QCheckBox
                self.value_table.setCellWidget(row, 1, check_box)
            else:
                field_type_widget = QTableWidgetItem()
                field_type_widget.setFlags(Qt.ItemIsEnabled)
                field_type_widget.setBackground(background_col)
                self.value_table.setItem(row, 1, field_type_widget)

        self.value_table.resizeRowsToContents()


class DefaultValue():
    def __init__(self, name: str, type: str):
        self.value = QgsDefaultValue()
        self.selected = False
        self.valid = True
        self.name = name
        self.type = type

    def set_value(self, value):
        QgsMessageLog.logMessage(f"Default value changed from {self.value.expression()} to {value}", tag=__title__, level=Qgis.Info)
        self.value.setExpression(value)


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


class DefaultValueModel(QAbstractTableModel):

    header_labels = [
        "Select",
        "Field",
        "Value"
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.default_values = []

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header_labels[section]
        return super().headerData(section, orientation, role)

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.default_values)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.header_labels)

    def data(self, index, role):

        if not index.isValid():
            return QVariant()

        row = index.row()
        default_val = self.default_values[row]

        column = index.column()
        column_header_label = self.header_labels[column]

        if role == Qt.CheckStateRole:
            if column_header_label == "Select":
                if default_val.is_selected():
                    return Qt.Checked
                else:
                    return Qt.Unchecked

        if role == Qt.ItemDataRole.DisplayRole:
            if column_header_label == "Field":
                return default_val.get_name()


        # if role == Qt.BackgroundRole:
        #     if template.is_active():
        #         return QColor(220, 255, 220)
        #
        # if role == Qt.ForegroundRole:
        #     if not template.is_valid():
        #         return QColor(200, 200, 200)
        #
        #     if column_header_label == "Shortcut":
        #         if template.shortcut.key().toString() == "":
        #             return QColor(200, 200, 200)

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags

        row = index.column()
        default_val = self.default_values[row]

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
        default_val = self.default_values[row]

        col = index.column()
        column_header_label = self.header_labels[col]

        if column_header_label == 'Select' and role == Qt.CheckStateRole:
            default_val.toggle_selected()
            return True

        if column_header_label == 'Value' and role == Qt.EditRole:
            default_val.set_value(value)
            return True



    def add_fields(self, map_lyr: QgsMapLayer) -> None:

        row = self.rowCount()

        fields = map_lyr.fields().toList()

        self.beginInsertRows(QModelIndex(), row, row + len(fields) - 1)

        for field in fields:

            default_val = DefaultValue(name=field.name(), type=field.typeName())

            self.default_values.append(default_val)

        self.endInsertRows()

    def get_selected_default_values(self):
        return 'SOME STUFF'

    def set_selected_default_values(self, set_default_values: Dict[str, QgsDefaultValue]):

        for field_name in set_default_values:

            set_default_val = None
            for default_val in self.default_values:
                if default_val.get_name() == field_name:
                    set_default_val = default_val

            if set_default_val:
                set_default_val.set_selected(True)

                QgsMessageLog.logMessage(f"Setting default field name: {set_default_val.get_name()}", tag=__title__,
                                     level=Qgis.Info)

        # index1 = self.createIndex(0, 0)
        # index2 = self.createIndex(self.rowCount(), self.columnCount())
        # self.dataChanged.emit(index1, index2)

class ValueDelegate(QItemDelegate):

    def __init__(self, parent):
        super().__init__(parent)

    def createEditor(self, parent, option, index):

        default_val = index.model().default_values[index.row()]

        field_type = default_val.get_type()

        if field_type == 'Integer64' or field_type == 'Integer':
            editor = QgsSpinBox(parent)

        elif field_type == 'String' or field_type == 'JSON':
            editor = QLineEdit(parent)

        elif field_type == 'Real':
            editor = QgsDoubleSpinBox(parent)

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

        default_val = index.model().default_values[index.row()]

        field_type = default_val.get_type()

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

        # Convert data to a string
        if data is not None:
            data = f"'{data}'"

        model.setData(index, data)

        ...
        # if editor.result() == QDialog.Accepted:
        #     data = editor.get_default_values()
        #     model.setData(index, data)

    def setEditorData(self, editor, index):
        date = QDate.fromString('2013-09-16', 'yyyy-MM-dd')
        # template = index.model().templates[index.row()]
        # editor.set_default_values(template.default_values)