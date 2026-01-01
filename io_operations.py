# GPL-3.0 - Frank Moelendoerp - Gamepad Control for Blender
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License Version 3 as 
# published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Import/Export operations for Gamepad Control modes and settings."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import bpy
from bpy.types import Operator, Context
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .preferences import (
    get_addon_preferences,
    GamepadAxisSettings,
    GamepadSideSettings,
    GamepadModeSettings,
    CL_GamepadPreferences,
)

# Current schema version for future compatibility
SCHEMA_VERSION = "1.0"


def axis_settings_to_dict(axis: GamepadAxisSettings) -> Dict[str, Any]:
    """Serialize GamepadAxisSettings to a dictionary."""
    return {
        "stick_mode": axis.stick_mode,
        "invert_x": axis.invert_x,
        "invert_y": axis.invert_y,
        "combined_action": axis.combined_action,
        "cursor_speed": axis.cursor_speed,
        "pan_speed": axis.pan_speed,
        "dolly_speed": axis.dolly_speed,
        "orbit_speed": axis.orbit_speed,
        "rotate_speed": axis.rotate_speed,
        "axis_x_action": axis.axis_x_action,
        "axis_y_action": axis.axis_y_action,
        "axis_deadzone_x": axis.axis_deadzone_x,
        "axis_deadzone_y": axis.axis_deadzone_y,
        "button_deadzone": axis.button_deadzone,
        "dir_up_action": axis.dir_up_action,
        "dir_down_action": axis.dir_down_action,
        "dir_left_action": axis.dir_left_action,
        "dir_right_action": axis.dir_right_action,
        "dir_up_left_action": axis.dir_up_left_action,
        "dir_up_right_action": axis.dir_up_right_action,
        "dir_down_left_action": axis.dir_down_left_action,
        "dir_down_right_action": axis.dir_down_right_action,
    }


def dict_to_axis_settings(data: Dict[str, Any], axis: GamepadAxisSettings) -> None:
    """Deserialize a dictionary into GamepadAxisSettings."""
    for key, value in data.items():
        if hasattr(axis, key):
            setattr(axis, key, value)


def side_settings_to_dict(side: GamepadSideSettings) -> Dict[str, Any]:
    """Serialize GamepadSideSettings to a dictionary."""
    data = {
        "controller_button_dpup": getattr(side, "controller_button_dpup", "NONE"),
        "controller_button_dpdown": getattr(side, "controller_button_dpdown", "NONE"),
        "controller_button_dpleft": getattr(side, "controller_button_dpleft", "NONE"),
        "controller_button_dpright": getattr(side, "controller_button_dpright", "NONE"),
        "controller_button_leftstick": getattr(side, "controller_button_leftstick", "NONE"),
        "controller_button_leftshoulder": getattr(side, "controller_button_leftshoulder", "NONE"),
        "controller_button_a": getattr(side, "controller_button_a", "NONE"),
        "controller_button_b": getattr(side, "controller_button_b", "NONE"),
        "controller_button_x": getattr(side, "controller_button_x", "NONE"),
        "controller_button_y": getattr(side, "controller_button_y", "NONE"),
        "controller_button_rightstick": getattr(side, "controller_button_rightstick", "NONE"),
        "controller_button_rightshoulder": getattr(side, "controller_button_rightshoulder", "NONE"),
        "trigger_action": side.trigger_action,
        "axis": axis_settings_to_dict(side.axis),
    }
    # Add extra data properties (only if non-empty)
    for button in ["controller_button_dpup", "controller_button_dpdown", "controller_button_dpleft",
                   "controller_button_dpright", "controller_button_leftstick", "controller_button_leftshoulder",
                   "controller_button_a", "controller_button_b", "controller_button_x", "controller_button_y",
                   "controller_button_rightstick", "controller_button_rightshoulder"]:
        extra_prop = f"{button}_extra"
        extra_value = getattr(side, extra_prop, "")
        if extra_value:
            data[extra_prop] = extra_value
    trigger_extra = getattr(side, "trigger_extra", "")
    if trigger_extra:
        data["trigger_extra"] = trigger_extra
    return data


def dict_to_side_settings(data: Dict[str, Any], side: GamepadSideSettings) -> None:
    """Deserialize a dictionary into GamepadSideSettings."""
    for key, value in data.items():
        if key == "axis":
            dict_to_axis_settings(value, side.axis)
        elif hasattr(side, key):
            setattr(side, key, value)


def mode_to_dict(mode: GamepadModeSettings) -> Dict[str, Any]:
    """Serialize GamepadModeSettings to a dictionary."""
    data = {
        "name": mode.name,
        "controller_button_back": mode.controller_button_back,
        "controller_button_start": mode.controller_button_start,
        "use_mode": bool(getattr(mode, "use_mode", True)),
        "left_side": side_settings_to_dict(mode.left_side),
        "right_side": side_settings_to_dict(mode.right_side),
    }
    # Add extra data properties for misc buttons (only if non-empty)
    back_extra = getattr(mode, "controller_button_back_extra", "")
    if back_extra:
        data["controller_button_back_extra"] = back_extra
    start_extra = getattr(mode, "controller_button_start_extra", "")
    if start_extra:
        data["controller_button_start_extra"] = start_extra
    return data


def dict_to_mode(data: Dict[str, Any], mode: GamepadModeSettings) -> None:
    """Deserialize a dictionary into GamepadModeSettings."""
    mode.name = data.get("name", "Imported Mode")
    mode.controller_button_back = data.get("controller_button_back", "NONE")
    mode.controller_button_start = data.get("controller_button_start", "NONE")
    mode.use_mode = data.get("use_mode", True)
    # Import extra data properties for misc buttons (support old temp_mode key for backward compatibility)
    mode.controller_button_back_extra = data.get("controller_button_back_extra", data.get("controller_button_back_temp_mode", ""))
    mode.controller_button_start_extra = data.get("controller_button_start_extra", data.get("controller_button_start_temp_mode", ""))
    if "left_side" in data:
        dict_to_side_settings(data["left_side"], mode.left_side)
    if "right_side" in data:
        dict_to_side_settings(data["right_side"], mode.right_side)


def export_all_data(prefs: CL_GamepadPreferences) -> Dict[str, Any]:
    """Export all modes and settings to a dictionary."""
    return {
        "schema_version": SCHEMA_VERSION,
        "export_type": "all",
        "settings": {
            "enable": prefs.enable,
            "modes_index": prefs.modes_index,
            "show_mode_display_on_startup": prefs.show_mode_display_on_startup,
            "show_info_overlay_on_startup": prefs.show_info_overlay_on_startup,
        },
        "modes": [mode_to_dict(mode) for mode in prefs.modes],
    }


def export_single_mode(mode: GamepadModeSettings) -> Dict[str, Any]:
    """Export a single mode to a dictionary."""
    return {
        "schema_version": SCHEMA_VERSION,
        "export_type": "mode",
        "modes": [mode_to_dict(mode)],
    }


def validate_import_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate imported JSON data structure."""
    if not isinstance(data, dict):
        return False, "Invalid file format: expected JSON object"
    
    if "schema_version" not in data:
        return False, "Invalid file format: missing schema_version"
    
    if "modes" not in data or not isinstance(data["modes"], list):
        return False, "Invalid file format: missing or invalid 'modes' array"
    
    if len(data["modes"]) == 0:
        return False, "No modes found in file"
    
    return True, ""


class CL_OT_GamepadExportAll(Operator, ExportHelper):
    """Export all gamepad modes and settings to a JSON file"""
    bl_idname = "cl.gamepad_export_all"
    bl_label = "Export All"
    bl_description = "Export all gamepad modes and settings to a JSON file"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context: Context):
        prefs = get_addon_preferences(context)
        if not prefs:
            self.report({'ERROR'}, "Could not access preferences")
            return {'CANCELLED'}

        data = export_all_data(prefs)
        
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.report({'INFO'}, f"Exported {len(prefs.modes)} modes to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export: {e}")
            return {'CANCELLED'}


class CL_OT_GamepadImportAll(Operator, ImportHelper):
    """Import all gamepad modes and settings from a JSON file (replaces existing)"""
    bl_idname = "cl.gamepad_import_all"
    bl_label = "Import All"
    bl_description = "Import all gamepad modes and settings from a JSON file. This will replace all existing modes and settings"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context: Context):
        prefs = get_addon_preferences(context)
        if not prefs:
            self.report({'ERROR'}, "Could not access preferences")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.report({'ERROR'}, f"Invalid JSON file: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {e}")
            return {'CANCELLED'}

        valid, error = validate_import_data(data)
        if not valid:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        # Clear existing modes
        prefs.modes.clear()

        # Import all modes
        for mode_data in data["modes"]:
            mode = prefs.modes.add()
            dict_to_mode(mode_data, mode)

        # Import settings if present
        if "settings" in data:
            settings = data["settings"]
            if "enable" in settings:
                prefs.enable = settings["enable"]
            if "modes_index" in settings:
                prefs.modes_index = min(settings["modes_index"], len(prefs.modes) - 1)
            if "show_mode_display_on_startup" in settings:
                prefs.show_mode_display_on_startup = settings["show_mode_display_on_startup"]
            if "show_info_overlay_on_startup" in settings:
                prefs.show_info_overlay_on_startup = settings["show_info_overlay_on_startup"]
            prefs.apply_display_preferences(context)
        else:
            prefs.modes_index = 0

        prefs.update_mode_statuses()

        self.report({'INFO'}, f"Imported {len(data['modes'])} modes from {self.filepath}")
        return {'FINISHED'}


class CL_OT_GamepadExportMode(Operator, ExportHelper):
    """Export the currently selected gamepad mode to a JSON file"""
    bl_idname = "cl.gamepad_export_mode"
    bl_label = "Export Mode"
    bl_description = "Export the currently selected gamepad mode to a JSON file"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    @classmethod
    def poll(cls, context: Context):
        prefs = get_addon_preferences(context)
        return prefs is not None and len(prefs.modes) > 0

    def invoke(self, context: Context, event):
        prefs = get_addon_preferences(context)
        if prefs and prefs.modes:
            mode = prefs.modes[prefs.modes_index]
            # Set default filename based on mode name
            self.filepath = f"{mode.name}.json"
        return super().invoke(context, event)

    def execute(self, context: Context):
        prefs = get_addon_preferences(context)
        if not prefs or not prefs.modes:
            self.report({'ERROR'}, "No mode selected")
            return {'CANCELLED'}

        mode = prefs.modes[prefs.modes_index]
        data = export_single_mode(mode)

        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.report({'INFO'}, f"Exported mode '{mode.name}' to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export: {e}")
            return {'CANCELLED'}


# Store pending import data for the selection dialog
_pending_import_data: Optional[Dict[str, Any]] = None
_pending_import_filepath: str = ""


def _get_mode_items(self, context) -> List[tuple]:
    """Generate items for mode selection dropdown."""
    global _pending_import_data
    items = []
    if _pending_import_data and "modes" in _pending_import_data:
        for i, mode in enumerate(_pending_import_data["modes"]):
            name = mode.get("name", f"Mode {i + 1}")
            items.append((str(i), name, f"Import '{name}'", i))
    if not items:
        items.append(('0', "No modes found", "", 0))
    return items


class CL_OT_GamepadImportModeSelect(Operator):
    """Select which mode to import from a multi-mode file"""
    bl_idname = "cl.gamepad_import_mode_select"
    bl_label = "Select Mode to Import"
    bl_description = "Select which mode to import from the file"
    bl_options = {'REGISTER', 'UNDO'}

    selected_mode: EnumProperty(
        name="Mode",
        description="Select the mode to import",
        items=_get_mode_items,
    )

    def invoke(self, context: Context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context):
        layout = self.layout
        layout.prop(self, "selected_mode", text="Select Mode")

    def execute(self, context: Context):
        global _pending_import_data
        
        prefs = get_addon_preferences(context)
        if not prefs:
            self.report({'ERROR'}, "Could not access preferences")
            return {'CANCELLED'}

        if not _pending_import_data or "modes" not in _pending_import_data:
            self.report({'ERROR'}, "No import data available")
            return {'CANCELLED'}

        mode_index = int(self.selected_mode)
        mode_data = _pending_import_data["modes"][mode_index]
        mode_name = mode_data.get("name", "Imported Mode")

        # Check if mode name already exists
        existing_index = None
        for i, existing_mode in enumerate(prefs.modes):
            if existing_mode.name == mode_name:
                existing_index = i
                break

        if existing_index is not None:
            # Store for replace confirmation dialog
            bpy.context.window_manager.cl_pending_mode_data = json.dumps(mode_data)
            bpy.context.window_manager.cl_pending_mode_index = existing_index
            bpy.ops.cl.gamepad_import_mode_confirm('INVOKE_DEFAULT')
        else:
            # Just import
            mode = prefs.modes.add()
            dict_to_mode(mode_data, mode)
            prefs.modes_index = len(prefs.modes) - 1
            self.report({'INFO'}, f"Imported mode '{mode_name}'")

        _pending_import_data = None
        prefs.update_mode_statuses()
        return {'FINISHED'}


class CL_OT_GamepadImportModeConfirm(Operator):
    """Confirm how to handle duplicate mode name"""
    bl_idname = "cl.gamepad_import_mode_confirm"
    bl_label = "Mode Already Exists"
    bl_description = "A mode with this name already exists"
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(
        name="Action",
        items=[
            ('REPLACE', "Replace", "Replace the existing mode with the imported one"),
            ('IMPORT', "Import as New", "Import as a new mode (will be renamed)"),
            ('CANCEL', "Cancel", "Cancel the import"),
        ],
        default='REPLACE',
    )

    def invoke(self, context: Context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: Context):
        layout = self.layout
        layout.label(text="A mode with this name already exists.")
        layout.prop(self, "action", expand=True)

    def execute(self, context: Context):
        prefs = get_addon_preferences(context)
        if not prefs:
            self.report({'ERROR'}, "Could not access preferences")
            return {'CANCELLED'}

        wm = context.window_manager
        mode_data = json.loads(wm.cl_pending_mode_data)
        existing_index = wm.cl_pending_mode_index
        mode_name = mode_data.get("name", "Imported Mode")

        if self.action == 'CANCEL':
            self.report({'INFO'}, "Import cancelled")
            return {'CANCELLED'}
        elif self.action == 'REPLACE':
            # Replace existing mode
            dict_to_mode(mode_data, prefs.modes[existing_index])
            prefs.modes_index = existing_index
            self.report({'INFO'}, f"Replaced mode '{mode_name}'")
        else:  # IMPORT
            # Find unique name
            base_name = mode_name
            counter = 1
            while any(m.name == mode_name for m in prefs.modes):
                mode_name = f"{base_name} ({counter})"
                counter += 1
            mode_data["name"] = mode_name
            mode = prefs.modes.add()
            dict_to_mode(mode_data, mode)
            prefs.modes_index = len(prefs.modes) - 1
            self.report({'INFO'}, f"Imported mode as '{mode_name}'")

        prefs.update_mode_statuses()

        return {'FINISHED'}


class CL_OT_GamepadImportMode(Operator, ImportHelper):
    """Import a single gamepad mode from a JSON file"""
    bl_idname = "cl.gamepad_import_mode"
    bl_label = "Import Mode"
    bl_description = "Import a single gamepad mode from a JSON file"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context: Context):
        global _pending_import_data, _pending_import_filepath

        prefs = get_addon_preferences(context)
        if not prefs:
            self.report({'ERROR'}, "Could not access preferences")
            return {'CANCELLED'}

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.report({'ERROR'}, f"Invalid JSON file: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to read file: {e}")
            return {'CANCELLED'}

        valid, error = validate_import_data(data)
        if not valid:
            self.report({'ERROR'}, error)
            return {'CANCELLED'}

        modes = data["modes"]
        
        if len(modes) > 1:
            # Multiple modes - show selection dialog
            _pending_import_data = data
            _pending_import_filepath = self.filepath
            bpy.ops.cl.gamepad_import_mode_select('INVOKE_DEFAULT')
            return {'FINISHED'}
        
        # Single mode - import directly or check for duplicates
        mode_data = modes[0]
        mode_name = mode_data.get("name", "Imported Mode")

        # Check if mode name already exists
        existing_index = None
        for i, existing_mode in enumerate(prefs.modes):
            if existing_mode.name == mode_name:
                existing_index = i
                break

        if existing_index is not None:
            # Store for replace confirmation dialog
            context.window_manager.cl_pending_mode_data = json.dumps(mode_data)
            context.window_manager.cl_pending_mode_index = existing_index
            bpy.ops.cl.gamepad_import_mode_confirm('INVOKE_DEFAULT')
        else:
            # Just import
            mode = prefs.modes.add()
            dict_to_mode(mode_data, mode)
            prefs.modes_index = len(prefs.modes) - 1
            self.report({'INFO'}, f"Imported mode '{mode_name}'")

        prefs.update_mode_statuses()

        return {'FINISHED'}


class CL_OT_GamepadResetToDefaults(Operator):
    """Reset all gamepad modes and settings to factory defaults"""
    bl_idname = "cl.gamepad_reset_to_defaults"
    bl_label = "Reset to Defaults"
    bl_description = "Reset all gamepad modes and settings to factory defaults. This will replace all existing modes"

    def invoke(self, context: Context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context: Context):
        prefs = get_addon_preferences(context)
        if not prefs:
            self.report({'ERROR'}, "Could not access preferences")
            return {'CANCELLED'}

        import os
        default_path = os.path.join(os.path.dirname(__file__), "assets", "default.json")
        
        if not os.path.exists(default_path):
            self.report({'ERROR'}, f"Default settings file not found: {default_path}")
            print(f"[Gamepad Controller] ERROR: Default settings file not found at {default_path}")
            return {'CANCELLED'}

        try:
            with open(default_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"[Gamepad Controller] Loading default settings from {default_path}")
            
        except json.JSONDecodeError as e:
            self.report({'ERROR'}, f"Invalid default settings file: {e}")
            print(f"[Gamepad Controller] ERROR: Invalid JSON in default settings: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load defaults: {e}")
            print(f"[Gamepad Controller] ERROR: Failed to load default settings: {e}")
            return {'CANCELLED'}

        valid, error = validate_import_data(data)
        if not valid:
            self.report({'ERROR'}, f"Invalid default settings: {error}")
            print(f"[Gamepad Controller] ERROR: Invalid default settings structure: {error}")
            return {'CANCELLED'}

        # Clear existing modes
        prefs.modes.clear()

        # Import all modes from defaults
        for mode_data in data["modes"]:
            mode = prefs.modes.add()
            dict_to_mode(mode_data, mode)

        # Import settings if present
        if "settings" in data:
            settings = data["settings"]
            if "enable" in settings:
                prefs.enable = settings["enable"]
            if "modes_index" in settings:
                prefs.modes_index = min(settings["modes_index"], len(prefs.modes) - 1)
            if "show_mode_display_on_startup" in settings:
                prefs.show_mode_display_on_startup = settings["show_mode_display_on_startup"]
            if "show_info_overlay_on_startup" in settings:
                prefs.show_info_overlay_on_startup = settings["show_info_overlay_on_startup"]
            prefs.apply_display_preferences(context)
        else:
            prefs.modes_index = 0

        prefs.update_mode_statuses()

        print(f"[Gamepad Controller] Successfully reset to defaults: {len(data['modes'])} modes loaded")
        self.report({'INFO'}, f"Reset to defaults: {len(data['modes'])} modes loaded")
        return {'FINISHED'}


IO_CLASSES = (
    CL_OT_GamepadExportAll,
    CL_OT_GamepadImportAll,
    CL_OT_GamepadExportMode,
    CL_OT_GamepadImportMode,
    CL_OT_GamepadImportModeSelect,
    CL_OT_GamepadImportModeConfirm,
    CL_OT_GamepadResetToDefaults,
)


def register_io_properties():
    """Register window manager properties for import dialogs."""
    bpy.types.WindowManager.cl_pending_mode_data = StringProperty(default="")
    bpy.types.WindowManager.cl_pending_mode_index = bpy.props.IntProperty(default=0)


def unregister_io_properties():
    """Unregister window manager properties."""
    del bpy.types.WindowManager.cl_pending_mode_data
    del bpy.types.WindowManager.cl_pending_mode_index


__all__ = [
    "CL_OT_GamepadExportAll",
    "CL_OT_GamepadImportAll",
    "CL_OT_GamepadExportMode",
    "CL_OT_GamepadImportMode",
    "CL_OT_GamepadImportModeSelect",
    "CL_OT_GamepadImportModeConfirm",
    "CL_OT_GamepadResetToDefaults",
    "IO_CLASSES",
    "register_io_properties",
    "unregister_io_properties",
]
