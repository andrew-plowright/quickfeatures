# Project
from quickfeatures.default_value_editor import *
from quickfeatures.__about__ import __title__

# Misc
from typing import Dict, List
from pathlib import Path
import json

# qgis
from qgis.gui import QgsMapLayerComboBox
from qgis.core import QgsMessageLog, QgsDefaultValue, QgsProject, Qgis, QgsMapLayerProxyModel, QgsMapLayer, QgsVectorLayer
from qgis.utils import iface

# PyQt
from qgis.PyQt.QtCore import QModelIndex, Qt, QAbstractTableModel, QVariant, QSize, QObject, pyqtSignal, pyqtSlot
from qgis.PyQt.QtGui import QKeySequence, QColor
from qgis.PyQt.QtWidgets import QShortcut, QItemDelegate, QStyledItemDelegate, QApplication, QAction, QDialog, \
    QTableWidgetItem, QTableWidget, QPushButton
from qgis.PyQt.QtXml import QDomDocument, QDomElement

class FeatureTemplate(QObject):

    beginActivation = pyqtSignal()
    activateChanged = pyqtSignal(bool)
    validChanged = pyqtSignal(bool)

    def __init__(self, parent, widget, name: str, shortcut_str: str, map_lyr: QgsVectorLayer,
                 default_values: Dict):

        super().__init__(parent)

        self.name = name

        # QgsMessageLog.logMessage(f"Template's parent class is: {self.parent().__class__.__name__}", tag=__title__, level=Qgis.Info)

        # Register shortcut
        self.shortcut = QShortcut(QKeySequence(), widget)
        self.shortcut.activated.connect(self.toggle_active)
        self.set_shortcut(shortcut_str)

        self.active = False
        self.valid = False

        self.map_lyr = None
        self.default_values = {}
        self.revert_suppress = 0
        self.revert_values = {}

        self.set_map_lyr(map_lyr)
        self.set_default_values(default_values)

        QgsProject.instance().writeMapLayer.connect(self.prevent_save)
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
            self.map_lyr.willBeDeleted.connect(self.remove_map_lyr)
            self.map_lyr.attributeAdded.connect(self.check_validity)
            self.map_lyr.attributeDeleted.connect(self.check_validity)
        else:
            # QgsMessageLog.logMessage(f"Removed map layer'", tag=__title__, level=Qgis.Info)
            if self.map_lyr is not None:
                self.map_lyr.willBeDeleted.disconnect(self.remove_map_lyr)
                self.map_lyr.attributeAdded.disconnect(self.check_validity)
                self.map_lyr.attributeDeleted.disconnect(self.check_validity)
                self.map_lyr = None

        self.check_validity()

    def remove_map_lyr(self):
        self.set_map_lyr(None)

    def get_map_lyr(self) -> QgsVectorLayer:
        return self.map_lyr

    def map_lyr_name(self) -> str:
        if self.map_lyr:
            return self.map_lyr.name()
        else:
            return 'None'

    def is_valid(self) -> bool:
        return self.valid

    def check_validity(self) -> bool:
        valid = True
        if self.map_lyr is None:
            #QgsMessageLog.logMessage(f"Feature template '{self.get_name()}' invalid: no Map layer", tag=__title__, level=Qgis.Warning)
            valid = False
        else:

            # Check if all default value names exist within map layer
            map_field_names = [field.name() for field in self.map_lyr.fields().toList()]
            default_value_field_names = [key for key in self.default_values]
            all_names_valid = all([item in map_field_names for item in default_value_field_names])

            if not all_names_valid:
                #QgsMessageLog.logMessage(f"Feature template '{self.get_name()}' invalid: did not have correct attribute fields", tag=__title__, level=Qgis.Warning)
                valid = False

        self.set_validity(valid)

        return valid

    def set_validity(self, value):
        if value:
            if not self.valid:
                self.valid = True
                self.validChanged.emit(True)
        else:
            if self.valid:
                self.valid = False
                self.validChanged.emit(False)

    def is_active(self) -> bool:
        return self.active

    def toggle_active(self):

        self.set_active(not self.is_active())

    def set_active(self, value) -> None:

        if value:
            if not self.is_active() and self.is_valid():
                # QgsMessageLog.logMessage(f"Activated template '{self.name}'", tag=__title__, level=Qgis.Info)

                # Emit signal
                self.beginActivation.emit()

                # Get values that will be reverted
                self.revert_values = self.get_lyr_default_definitions()
                self.revert_suppress = self.get_lyr_form_suppress()

                # Set default definition and suppress form
                self.set_lyr_default_definitions(self.default_values)
                self.set_lyr_form_suppress(1)

                # Set this template as active
                self.active = True
                self.activateChanged.emit(True)

        else:
            if self.active:
                # QgsMessageLog.logMessage(f"Deactivated template '{self.name}'", tag=__title__, level=Qgis.Info)

                # Revert default value definitions and form suppression settings
                self.set_lyr_default_definitions(self.revert_values)
                self.set_lyr_form_suppress(self.revert_suppress)

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

    def get_default_values(self) -> Dict:

        # Strip away single quotes
        out_dict = {}
        for key, value in self.default_values.items():
            out = value.expression()
            if out.lower() == 'true':
                out = True
            elif out.lower() == 'false':
                out = False
            elif out.lstrip('-').isdigit():
                out = int(out)
            elif is_float(out):
                out = float(out)
            else:
                out = out.strip("\'")
            out_dict[key] = out

        return out_dict

    def set_default_values(self, values: Dict) -> bool:

        #QgsMessageLog.logMessage(f"Default values set: {values}", tag=__title__, level=Qgis.Info)

        self.set_active(False)

        default_values = {}
        for key, value in values.items():

            if isinstance(value, str):
                value = f"'{value}'"
            else:
                value = str(value)
            default_values[key] = QgsDefaultValue(value)

        self.default_values = default_values

        self.check_validity()

        return True

    def set_lyr_default_definitions(self, default_values: Dict[str, QgsDefaultValue]) -> None:

        field_ids = [get_field_id(self.map_lyr, field_name) for field_name in default_values]
        def_values = [default_values[field_name] for field_name in default_values]

        for i in range(len(default_values)):
            self.map_lyr.setDefaultValueDefinition(field_ids[i], def_values[i])

    def get_lyr_default_definitions(self) -> dict:

        field_names = [field_name for field_name in self.default_values]

        field_ids = [get_field_id(self.map_lyr, field_name) for field_name in field_names]
        default_values = {}

        for i in range(len(field_ids)):
            default_values[field_names[i]] = self.map_lyr.defaultValueDefinition(field_ids[i])

        return default_values

    def set_lyr_form_suppress(self, suppress: int) -> None:
        edit_form = self.map_lyr.editFormConfig()
        edit_form.setSuppress(suppress)
        self.map_lyr.setEditFormConfig(edit_form)

    def get_lyr_form_suppress(self) -> int:
        return self.map_lyr.editFormConfig().suppress()

    # This method is called when the 'writeMapLayer' signal is emitted
    # The 'elem' QDomElement contains the layer information that will be saved to file
    # This method is needed to prevent the default values that are activated by the
    # template to be saved to file.
    def prevent_save(self, map_lyr: QgsMapLayer, elem: QDomElement, doc: QDomDocument):

        if self.is_active() and self.get_map_lyr() == map_lyr:

            #QgsMessageLog.logMessage(f"Preventing template {self.get_name()} from being saved", tag=__title__, level=Qgis.Info)

            defaults_nodes = elem.namedItem('defaults').childNodes()

            revert_values = self.revert_values
            revert_suppress = self.revert_suppress

            for i in range(defaults_nodes.length()):
                default_node = defaults_nodes.item(i)
                field_value = default_node.attributes().namedItem('field').nodeValue()
                for field_name in revert_values:
                    if field_value == field_name:
                        revert_expression = revert_values[field_name].expression()
                        expression_node = default_node.attributes().namedItem('expression')
                        expression_node.setNodeValue(revert_expression)
                        #QgsMessageLog.logMessage(f"Field {field} setting expression: {revert_expression}", tag=__title__, level=Qgis.Info)

            featformsuppress_node = elem.namedItem('featformsuppress').namedItem("#text")
            featformsuppress_node.setNodeValue(str(revert_suppress))

    def to_xml(self, doc: QDomDocument) -> QDomElement:
    
        template_elem = doc.createElement('template')
        
        template_elem.setAttribute('name', self.get_name())
        template_elem.setAttribute('map_lyr', self.map_lyr_name())
        template_elem.setAttribute('shortcut', self.get_shortcut_str())

        default_values_elem = doc.createElement('default_values')
        
        for key, value in self.get_default_values().items():
                    
            default_value = doc.createElement('default_value')
            
            if isinstance(value, bool):
                if value:
                    value = 'true'
                else:
                    value = 'false'
            
            default_value.setAttribute('field', key)
            default_value.setAttribute('value', str(value))
            
            default_values_elem.appendChild(default_value)
            
        template_elem.appendChild(default_values_elem)
        
        return template_elem
        

    @staticmethod
    def confirm_deletion(self):
        ...
        #QgsMessageLog.logMessage(f"Confirm deletion!", tag=__title__, level=Qgis.Info)

    def delete_template(self):
        self.set_active(False)
        self.delete_shortcut()
        self.setParent(None)
        self.deleteLater()

def get_field_id(map_lyr: QgsVectorLayer, field_name: str) -> int:
    field_idx = map_lyr.fields().indexFromName(field_name)

    if field_idx == -1:
        raise Exception(f"Could not find '{field_name}'")

    return field_idx

def is_float(element: any) -> bool:

    if element is None:
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False