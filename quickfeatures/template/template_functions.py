from qgis.core import QgsMapLayer
from qgis.core import QgsDefaultValue
from typing import Dict
from qgis.core import QgsMessageLog, Qgis
from quickfeatures.__about__ import __title__


def set_default_definitions(map_lyr: QgsMapLayer, default_values: Dict[str, QgsDefaultValue]) -> None:
    #QgsMessageLog.logMessage(f"  Applying form default values of {str(default_values)} on {map_lyr.name()}", tag=__title__, level=Qgis.Info)
    # Get field IDs and values
    # NOTE: this way, missing fields will get caught before attempting to change anything
    field_ids = [get_field_id(map_lyr, field_name) for field_name in default_values]
    def_values = [default_values[field_name] for field_name in default_values]

    for i in range(len(default_values)):
        map_lyr.setDefaultValueDefinition(field_ids[i], def_values[i])


def get_existing_default_definitions(map_lyr: QgsMapLayer, field_names: list) -> dict:
    field_ids = [get_field_id(map_lyr, field_name) for field_name in field_names]
    default_values = {}

    for i in range(len(field_ids)):
        default_values[field_names[i]] = map_lyr.defaultValueDefinition(field_ids[i])

    return default_values


def set_form_suppress(map_lyr: QgsMapLayer, suppress: int) -> None:
    #QgsMessageLog.logMessage(f"  Applying form suppresion of {str(suppress)} on {map_lyr.name()}", tag=__title__, level=Qgis.Info)

    edit_form = map_lyr.editFormConfig()
    edit_form.setSuppress(suppress)
    map_lyr.setEditFormConfig(edit_form)


def get_existing_form_suppress(map_lyr: QgsMapLayer) -> int:
    return map_lyr.editFormConfig().suppress()


def get_field_id(map_lyr: QgsMapLayer, field_name: str) -> int:
    field_idx = map_lyr.fields().indexFromName(field_name)

    if field_idx == -1:
        raise Exception(f"Could not find '{field_name}'")

    return field_idx
