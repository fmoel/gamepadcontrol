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

"""User preference definitions and helpers for the Gamepad Control add-on."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

import bpy
from bpy.types import AddonPreferences, PropertyGroup
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty,
                       FloatProperty, IntProperty, PointerProperty,
                       StringProperty)

ADDON_PACKAGE = __package__

BUTTON_ACTION_ITEMS: List[Tuple[str, str, str, int]] = [
    ("NONE", "None", "Action disabled", 0),
    ("VIEW_LEFT", "Left View", "Switch the viewport to the left view", 1),
    ("VIEW_RIGHT", "Right View", "Switch the viewport to the right view", 2),
    ("VIEW_TOP", "Top View", "Switch the viewport to the top view", 3),
    ("VIEW_BOTTOM", "Bottom View", "Switch the viewport to the bottom view", 4),
    ("VIEW_FRONT", "Front View", "Switch the viewport to the front view", 5),
    ("VIEW_BACK", "Rear View", "Switch the viewport to the rear view", 6),
    ("VIEW_CAMERA", "Camera View", "Switch to the active camera", 7),
    ("VIEW_PERSPECTIVE", "Toggle Perspective", "Toggle between orthographic and perspective", 8),
    ("MOUSE_LEFT", "Mouse - Left Button", "Emulate the left mouse button", 9),
    ("MOUSE_RIGHT", "Mouse - Right Button", "Emulate the right mouse button", 10),
    ("PIVOT_PIE", "Pivot Pie Menu", "Show the Pivot Pie menu", 11),
    ("ORIENTATION_PIE", "Orientation Pie Menu", "Show the Orientation Pie menu", 12),
    ("NEXT_MODE", "Next Gamepad Mode", "Switch to the next controller mode", 13),
    ("PREV_MODE", "Previous Gamepad Mode", "Switch to the previous controller mode", 14),
    ("TEMP_MODE_SHIFT", "Temporary Mode Shift", "Switch mode while button held, return on release", 15),
    ("TOGGLE_OVERLAY", "Toggle Overlay", "Toggle the gamepad overlay display", 16),
    ("SHOW_OVERLAY", "Show Overlay", "Show overlay while button is held", 17),
    ("GRAB", "Grab (G)", "Trigger the Grab/Move tool", 18),
    ("ROTATE", "Rotate (R)", "Trigger the Rotate tool", 19),
    ("SCALE", "Scale (S)", "Trigger the Scale tool", 20),
    ("EXTRUDE", "Extrude (E)", "Trigger the Extrude tool", 21),
    ("COPY", "Copy (Ctrl+C)", "Copy the current selection", 22),
    ("PASTE", "Paste (Ctrl+V)", "Paste from the clipboard", 23),
    ("DUPLICATE", "Duplicate (Shift+D)", "Duplicate the current selection", 24),
    ("CONSTRAINT_X", "X Axis Constraint", "Constrain transform to the X axis", 25),
    ("CONSTRAINT_Y", "Y Axis Constraint", "Constrain transform to the Y axis", 26),
    ("CONSTRAINT_Z", "Z Axis Constraint", "Constrain transform to the Z axis", 27),
    ("PLANE_X", "X Plane Constraint", "Constrain transform to the X plane", 28),
    ("PLANE_Y", "Y Plane Constraint", "Constrain transform to the Y plane", 29),
    ("PLANE_Z", "Z Plane Constraint", "Constrain transform to the Z plane", 30),
    ("KEYFRAME_ADD", "Insert Keyframe", "Insert a keyframe", 31),
    ("KEYFRAME_REMOVE", "Remove Keyframe", "Remove the active keyframe", 32),
    ("MODE_TOGGLE_EDIT", "Toggle Edit/Object", "Toggle Edit/Object mode", 33),
    ("SELECT_ALL", "Select All", "Select all elements", 34),
    ("SELECT_NONE", "Select None", "Deselect all elements", 35),
    ("NEXT_FRAME", "Next Frame", "Move to the next frame", 36),
    ("PREV_FRAME", "Previous Frame", "Move to the previous frame", 37),
    ("NEXT_KEYFRAME", "Next Keyframe", "Jump to the next keyframe", 38),
    ("PREV_KEYFRAME", "Previous Keyframe", "Jump to the previous keyframe", 39),
    ("DELETE", "Delete", "Delete the current selection", 40),
    ("ZERO_KEY", "Enter 0", "Send the 0 key", 41),
    ("MOUSE_WHEEL_UP", "Mouse Wheel Up", "Scroll up", 42),
    ("MOUSE_WHEEL_DOWN", "Mouse Wheel Down", "Scroll down", 43),
]

STICK_MODE_ITEMS: List[Tuple[str, str, str, int]] = [
    ("COMBINED", "Combined Axis", "Treat both axes as a single input", 0),
    ("SEPARATE", "Separate Axis", "Configure each axis individually", 1),
    ("FOUR_BUTTONS", "As Four Buttons", "Map the stick to up/down/left/right buttons", 2),
    ("EIGHT_BUTTONS", "As Eight Buttons", "Map the stick to all eight directions", 3),
]

COMBINED_AXIS_ACTION_ITEMS: List[Tuple[str, str, str, int]] = [
    ("NONE", "None", "Disable the combined stick action", 0),
    ("MOUSE_POINTER", "Mouse", "Move the virtual mouse cursor", 1),
    ("PAN_VIEW", "Pan", "Pan the viewport", 2),
    ("ROTATE_VIEW", "Rotate", "Orbit the viewport", 3),
    ("ORBIT_SELECTED", "Orbit", "Orbit around the selection", 4),
]

SEPARATE_AXIS_ACTION_ITEMS: List[Tuple[str, str, str, int]] = [
    ("NONE", "None", "Disable the selected axis", 0),
    ("MOVE_VIEW", "Move", "Dolly the view forward/backward", 1),
    ("PAN_LR", "Pan Left/Right", "Pan the view horizontally", 2),
    ("PAN_UD", "Pan Up/Down", "Pan the view vertically", 3),
    ("ROTATE_LOCAL_X", "Rotate Local X", "Rotate the view around the local X axis", 4),
    ("ROTATE_LOCAL_Y", "Rotate Local Y", "Rotate the view around the local Y axis", 5),
    ("ORBIT_LR", "Orbit Left/Right", "Orbit around the selection horizontally", 6),
    ("ORBIT_UD", "Orbit Up/Down", "Orbit around the selection vertically", 7),
    ("ZOOM_VIEW", "Zoom", "Zoom the view in and out", 8),
]

def _make_label_dict(items: List[Tuple[str, str, str, int]]) -> Dict[str, str]:
    """Create a dictionary mapping identifiers to labels from action items."""
    return {identifier: label for identifier, label, *_ in items}


ACTION_LABELS: Dict[str, str] = _make_label_dict(BUTTON_ACTION_ITEMS)
COMBINED_AXIS_LABELS: Dict[str, str] = _make_label_dict(COMBINED_AXIS_ACTION_ITEMS)
SEPARATE_AXIS_LABELS: Dict[str, str] = _make_label_dict(SEPARATE_AXIS_ACTION_ITEMS)


def _format_label(identifier: str, label_dict: Dict[str, str]) -> str:
    """Format an action identifier to a display label."""
    if identifier == 'NONE':
        return "-"
    return label_dict.get(identifier, identifier.replace("_", " ").title())


def format_action_label(identifier: str) -> str:
    return _format_label(identifier, ACTION_LABELS)


def format_combined_axis_label(identifier: str) -> str:
    return _format_label(identifier, COMBINED_AXIS_LABELS)


def format_separate_axis_label(identifier: str) -> str:
    return _format_label(identifier, SEPARATE_AXIS_LABELS)


class GamepadAxisSettings(PropertyGroup):
    stick_mode: EnumProperty(
        name="Stick Mode",
        items=STICK_MODE_ITEMS,
        description="How the stick movement should be interpreted",
        default='COMBINED',
    )
    invert_x: BoolProperty(
        name="Invert X",
        description="Reverse the horizontal axis",
        default=False,
    )
    invert_y: BoolProperty(
        name="Invert Y",
        description="Reverse the vertical axis",
        default=True,
    )
    combined_action: EnumProperty(
        name="Combined Action",
        items=COMBINED_AXIS_ACTION_ITEMS,
        description="Action performed when treating the stick as a single input",
        default='NONE',
    )
    cursor_speed: FloatProperty(
        name="Cursor Speed",
        description="Pointer speed when the stick controls the cursor (0.5 recommended)",
        min=0.0,
        max=1.0,
        default=0.5,
    )
    pan_speed: FloatProperty(
        name="Pan Speed",
        description="Pan strength applied when this stick drives the view",
        min=0.01,
        max=1.0,
        default=0.08,
    )
    dolly_speed: FloatProperty(
        name="Move Speed",
        description="Move intensity when using this stick",
        min=0.01,
        max=1.0,
        default=0.2,
    )
    orbit_speed: FloatProperty(
        name="Orbit Speed",
        description="Rotation speed for orbit actions",
        min=0.005,
        max=0.2,
        default=0.02,
    )
    rotate_speed: FloatProperty(
        name="Rotate Speed",
        description="Rotation speed for view rotation",
        min=0.005,
        max=0.2,
        default=0.02,
    )
    axis_x_action: EnumProperty(
        name="X Axis",
        items=SEPARATE_AXIS_ACTION_ITEMS,
        description="Behavior of the horizontal axis",
        default='NONE',
    )
    axis_y_action: EnumProperty(
        name="Y Axis",
        items=SEPARATE_AXIS_ACTION_ITEMS,
        description="Behavior of the vertical axis",
        default='NONE',
    )
    axis_deadzone_x: FloatProperty(
        name="X Deadzone",
        description="Threshold for the horizontal axis",
        min=0.0,
        max=1.0,
        default=0.1,
    )
    axis_deadzone_y: FloatProperty(
        name="Y Deadzone",
        description="Threshold for the vertical axis",
        min=0.0,
        max=1.0,
        default=0.1,
    )
    button_deadzone: FloatProperty(
        name="Button Threshold",
        description="Minimum magnitude before button directions trigger",
        min=0.0,
        max=1.0,
        default=0.6,
    )
    dir_up_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Up", default='NONE')
    dir_down_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Down", default='NONE')
    dir_left_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Left", default='NONE')
    dir_right_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Right", default='NONE')
    dir_up_left_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Up-Left", default='NONE')
    dir_up_right_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Up-Right", default='NONE')
    dir_down_left_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Down-Left", default='NONE')
    dir_down_right_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Down-Right", default='NONE')

class GamepadSideSettings(PropertyGroup):
    controller_button_dpup: EnumProperty(items=BUTTON_ACTION_ITEMS, name="D-Pad Up", default='NONE')
    controller_button_dpup_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_dpdown: EnumProperty(items=BUTTON_ACTION_ITEMS, name="D-Pad Down", default='NONE')
    controller_button_dpdown_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_dpleft: EnumProperty(items=BUTTON_ACTION_ITEMS, name="D-Pad Left", default='NONE')
    controller_button_dpleft_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_dpright: EnumProperty(items=BUTTON_ACTION_ITEMS, name="D-Pad Right", default='NONE')
    controller_button_dpright_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_leftstick: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Left Stick Button", default='NONE')
    controller_button_leftstick_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_leftshoulder: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Left Shoulder", default='NONE')
    controller_button_leftshoulder_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_a: EnumProperty(items=BUTTON_ACTION_ITEMS, name="A Button", default='NONE')
    controller_button_a_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_b: EnumProperty(items=BUTTON_ACTION_ITEMS, name="B Button", default='NONE')
    controller_button_b_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_x: EnumProperty(items=BUTTON_ACTION_ITEMS, name="X Button", default='NONE')
    controller_button_x_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_y: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Y Button", default='NONE')
    controller_button_y_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_rightstick: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Right Stick Button", default='NONE')
    controller_button_rightstick_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_rightshoulder: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Right Shoulder", default='NONE')
    controller_button_rightshoulder_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    trigger_action: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Trigger", default='NONE')
    trigger_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    axis: PointerProperty(type=GamepadAxisSettings)


def _on_use_mode_toggle(self, _context):
    prefs = getattr(self, "id_data", None)
    if prefs and hasattr(prefs, "update_mode_statuses"):
        prefs.update_mode_statuses()


def _on_mode_name_update(self, _context):
    """Update extra data references when mode name changes."""
    prefs = getattr(self, "id_data", None)
    if prefs and hasattr(prefs, "update_extra_references"):
        old_name = getattr(self, "previous_name", None)
        if old_name and old_name != self.name:
            prefs.update_extra_references(old_name, self.name)
        self["previous_name"] = self.name


class GamepadModeSettings(PropertyGroup):
    name: StringProperty(name="Name", default="Mode", update=_on_mode_name_update)
    previous_name: StringProperty(name="Previous Name", default="Mode", options={'HIDDEN', 'SKIP_SAVE'})
    use_mode: BoolProperty(
        name="Use Mode",
        description="Include this mode when cycling through controller modes",
        default=True,
        update=_on_use_mode_toggle,
    )
    ui_status: EnumProperty(
        name="Status",
        description="Display state for this mode",
        items=[
            ('ACTIVE', "Active", "Controller is currently using this mode"),
            ('ENABLED', "Enabled", "Mode is available when cycling"),
            ('DISABLED', "Disabled", "Mode is excluded when cycling"),
        ],
        default='ENABLED',
        options={'SKIP_SAVE'},
    )
    left_side: PointerProperty(type=GamepadSideSettings)
    right_side: PointerProperty(type=GamepadSideSettings)
    controller_button_back: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Back Button", default='NONE')
    controller_button_back_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")
    controller_button_start: EnumProperty(items=BUTTON_ACTION_ITEMS, name="Start Button", default='NONE')
    controller_button_start_extra: StringProperty(name="Target Mode", description="Target mode for temporary mode shift", default="")

class CL_GamepadPreferences(AddonPreferences):
    bl_idname = ADDON_PACKAGE

    enable: BoolProperty(
        name="Auto Connect",
        description="Automatically start the controller listener when Blender loads",
        default=True,
    )
    show_mode_display_on_startup: BoolProperty(
        name="Show Mode Display on Startup",
        description="Display the gamepad mode text in the 3D View header when Blender opens",
        default=True,
    )
    show_info_overlay_on_startup: BoolProperty(
        name="Show Info Overlay on Startup",
        description="Show the controller info overlay in the 3D View when Blender opens",
        default=False,
    )
    modes: CollectionProperty(type=GamepadModeSettings)
    modes_index: IntProperty(name="Active Mode", default=0, min=0)

    def draw(self, context):
        self.ensure_default_modes()
        self.update_mode_statuses()
        from .io_operations import CL_OT_GamepadResetToDefaults

        layout = self.layout
        
        # Welcome and quick start guide
        box = layout.box()
        box.label(text="Gamepad Controller - Quick Start", icon='INFO')
        
        col = box.column(align=True)
        col.label(text="Welcome! This addon lets you navigate Blender's 3D viewport with a gamepad.")
        col.separator()
        
        col.label(text="Getting Started:")
        col.label(text="1. Connect your gamepad (PlayStation, Xbox, or compatible controller)")
        col.label(text="2. The gamepad icon will appear in the 3D View header when ready")
        col.label(text="3. Click the icon to start using your gamepad")
        col.separator()
        
        col.label(text="Where to Find Controls:")
        split = col.split(factor=0.3)
        split.label(text="• Main Settings:", icon='PREFERENCES')
        split.label(text="Edit > Preferences > Input > Gamepad")
        
        split = col.split(factor=0.3)
        split.label(text="• Gamepad Modes:", icon='SETTINGS')
        split.label(text="Configure multiple control schemes for different tasks")
        
        split = col.split(factor=0.3)
        split.label(text="• Header Controls:", icon='VIEW3D')
        split.label(text="Click the gamepad icon in 3D View header to toggle and switch modes")
        
        split = col.split(factor=0.3)
        split.label(text="• Visual Overlay:", icon='OVERLAY')
        split.label(text="Enable 'Info Overlay' to see current button mappings in viewport")
        
        col.separator()
        col.label(text="Tip: Use 'View > Toggle Gamepad Overlay' to show/hide controller info.")
        col.label(text="Customize button mappings and create multiple modes in Input preferences.")
        
        layout.separator()
        
        # Add factory reset button
        reset_box = layout.box()
        reset_box.label(text="Factory Reset", icon='ERROR')
        reset_box.operator(CL_OT_GamepadResetToDefaults.bl_idname, text="Reset All Settings to Defaults", icon='LOOP_BACK')
        reset_box.label(text="Use this if settings become corrupted or you want to start fresh.", icon='INFO')


    def draw_in_input_panel(self, layout, context):
        self.ensure_default_modes()
        self.update_mode_statuses()
        from . import preferences_ui

        preferences_ui.draw_preferences_ui(self, layout, context)

    def ensure_default_modes(self):
        if self.modes:
            self.update_mode_statuses()
            return
        print("[Gamepad Control] No modes found, initializing default modes with json.")

        # Try to load from default.json first
        if self._load_from_default_json():
            return
        
        print("[Gamepad Control] No modes found, initializing default modes with hardcoded templates.")
        # Fallback to hardcoded templates
        for template in DEFAULT_MODE_TEMPLATES:
            self._create_mode_from_template(template)
        self.modes_index = 0
        self.update_mode_statuses()

    def _load_from_default_json(self) -> bool:
        """Try to load default settings from assets/default.json. Returns True if successful."""
        import os
        import json
        print("[Gamepad Control] Attempting to load default modes from assets/default.json")
        try:
            # Get the addon directory
            addon_dir = os.path.dirname(os.path.abspath(__file__))
            default_json_path = os.path.join(addon_dir, "assets", "default.json")
            
            if not os.path.exists(default_json_path):
                return False
            
            with open(default_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate basic structure
            if not isinstance(data, dict) or "modes" not in data:
                return False
            
            # Import from io_operations for proper deserialization
            from .io_operations import dict_to_mode
            
            # Load modes
            for mode_data in data["modes"]:
                mode = self.modes.add()
                dict_to_mode(mode_data, mode)
                # Initialize previous_name tracking
                mode["previous_name"] = mode.name
            
            self.update_mode_statuses()
            return True
            
        except Exception as e:
            print(f"[Gamepad Control] Failed to load default.json: {e}")
            return False

    def _create_mode_from_template(self, template: Dict[str, Dict[str, str]]):
        mode = self.modes.add()
        mode.name = template.get("name", "Mode")
        assign_side(mode.left_side, template.get("left", {}))
        assign_side(mode.right_side, template.get("right", {}))
        mode.controller_button_back = template.get("controller_button_back", 'NONE')
        mode.controller_button_start = template.get("controller_button_start", 'NONE')

    def apply_display_preferences(self, context=None):
        if context is None:
            context = bpy.context
        wm = getattr(context, "window_manager", None)
        if not wm:
            wm = getattr(bpy.context, "window_manager", None)
        if not wm:
            return

        overlay_property_defined = hasattr(wm, "cl_show_gamepad_overlay")
        if overlay_property_defined:
            desired_overlay = bool(self.show_info_overlay_on_startup)
            if wm.cl_show_gamepad_overlay != desired_overlay:
                wm.cl_show_gamepad_overlay = desired_overlay

        mode_property_defined = hasattr(wm, "cl_show_mode_display")
        if mode_property_defined:
            desired_mode = bool(self.show_mode_display_on_startup)
            if wm.cl_show_mode_display != desired_mode:
                wm.cl_show_mode_display = desired_mode

        try:
            from . import view3d_overlay_ui, view3d_gamepad_indicator_op
        except ImportError:
            return

        if overlay_property_defined:
            view3d_overlay_ui.sync_overlay_state(context=context)
        view3d_gamepad_indicator_op.redraw_view3d_headers()

    def _detect_active_mode_index(self) -> Optional[int]:
        try:
            from .enablement import is_controller_running  # Local import to avoid cycles
            from .controller_actions import controller_actions
        except Exception:
            return None
        if not is_controller_running():
            return None
        return getattr(controller_actions, "mode_index", None)

    def update_mode_statuses(self, active_index: Optional[int] = None) -> None:
        if not self.modes:
            return
        if active_index is None:
            active_index = self._detect_active_mode_index()
        if isinstance(active_index, int):
            if active_index < 0 or active_index >= len(self.modes):
                active_index = None
        else:
            active_index = None

        for idx, mode in enumerate(self.modes):
            if not getattr(mode, "use_mode", True):
                mode.ui_status = 'DISABLED'
            elif active_index is not None and idx == active_index:
                mode.ui_status = 'ACTIVE'
            else:
                mode.ui_status = 'ENABLED'

    def update_extra_references(self, old_name: str, new_name: str) -> None:
        """Update all extra data references when a mode is renamed."""
        for mode in self.modes:
            # Check left side buttons
            if mode.left_side:
                for button in ["controller_button_dpup", "controller_button_dpdown",
                             "controller_button_dpleft", "controller_button_dpright",
                             "controller_button_leftstick", "controller_button_leftshoulder"]:
                    extra_prop = f"{button}_extra"
                    if hasattr(mode.left_side, extra_prop):
                        if getattr(mode.left_side, extra_prop) == old_name:
                            setattr(mode.left_side, extra_prop, new_name)
                # Check left trigger
                if hasattr(mode.left_side, "trigger_extra"):
                    if mode.left_side.trigger_extra == old_name:
                        mode.left_side.trigger_extra = new_name
            
            # Check right side buttons
            if mode.right_side:
                for button in ["controller_button_a", "controller_button_b",
                             "controller_button_x", "controller_button_y",
                             "controller_button_rightstick", "controller_button_rightshoulder"]:
                    extra_prop = f"{button}_extra"
                    if hasattr(mode.right_side, extra_prop):
                        if getattr(mode.right_side, extra_prop) == old_name:
                            setattr(mode.right_side, extra_prop, new_name)
                # Check right trigger
                if hasattr(mode.right_side, "trigger_extra"):
                    if mode.right_side.trigger_extra == old_name:
                        mode.right_side.trigger_extra = new_name
            
            # Check misc buttons
            for button in ["controller_button_back", "controller_button_start"]:
                extra_prop = f"{button}_extra"
                if hasattr(mode, extra_prop):
                    if getattr(mode, extra_prop) == old_name:
                        setattr(mode, extra_prop, new_name)


DEFAULT_MODE_TEMPLATES: List[Dict[str, Dict[str, str]]] = [
    {
        "name": "Mouse",
        "left": {
            "controller_button_dpup": "PREV_KEYFRAME",
            "controller_button_dpdown": "NEXT_KEYFRAME",
            "controller_button_dpleft": "PREV_FRAME",
            "controller_button_dpright": "NEXT_FRAME",
            "controller_button_leftshoulder": "PREV_MODE",
            "trigger_action": "MOUSE_LEFT",
            "axis.stick_mode": "EIGHT_BUTTONS",
            "axis.dir_left_action": "VIEW_LEFT",
            "axis.dir_right_action": "VIEW_RIGHT",
            "axis.dir_up_action": "VIEW_TOP",
            "axis.dir_down_action": "VIEW_BOTTOM",
            "axis.dir_up_right_action": "VIEW_TOP",
            "axis.dir_down_left_action": "VIEW_BOTTOM",
            "axis.dir_up_left_action": "VIEW_PERSPECTIVE",
            "axis.dir_down_right_action": "VIEW_CAMERA",
        },
        "right": {
            "controller_button_a": "PIVOT_PIE",
            "controller_button_b": "ORIENTATION_PIE",
            "controller_button_x": "MODE_TOGGLE_EDIT",
            "controller_button_rightshoulder": "NEXT_MODE",
            "trigger_action": "MOUSE_RIGHT",
            "axis.stick_mode": "COMBINED",
            "axis.combined_action": "MOUSE_POINTER",
        },
    },
    {
        "name": "Edit",
        "left": {
            "controller_button_dpup": "MOUSE_WHEEL_UP",
            "controller_button_dpdown": "MOUSE_WHEEL_DOWN",
            "controller_button_dpleft": "PREV_FRAME",
            "controller_button_dpright": "NEXT_FRAME",
            "controller_button_leftshoulder": "PREV_MODE",
            "trigger_action": "MOUSE_LEFT",
            "axis.stick_mode": "SEPARATE",
            "axis.axis_x_action": "ROTATE_LOCAL_Y",
            "axis.axis_y_action": "MOVE_VIEW",
        },
        "right": {
            "controller_button_a": "GRAB",
            "controller_button_b": "ROTATE",
            "controller_button_y": "SCALE",
            "controller_button_x": "EXTRUDE",
            "controller_button_rightshoulder": "NEXT_MODE",
            "trigger_action": "MOUSE_RIGHT",
            "axis.stick_mode": "COMBINED",
            "axis.combined_action": "MOUSE_POINTER",
        },
        "controller_button_back": "PIVOT_PIE",
        "controller_button_start": "ORIENTATION_PIE",
    },
    {
        "name": "Move/Pan",
        "left": {
            "controller_button_dpright": "CONSTRAINT_X",
            "controller_button_dpup": "CONSTRAINT_Y",
            "controller_button_dpdown": "CONSTRAINT_Z",
            "controller_button_leftshoulder": "PREV_MODE",
            "trigger_action": "MOUSE_LEFT",
            "axis.stick_mode": "SEPARATE",
            "axis.axis_x_action": "ROTATE_LOCAL_Y",
            "axis.axis_y_action": "MOVE_VIEW",
        },
        "right": {
            "controller_button_b": "ZERO_KEY",
            "controller_button_a": "KEYFRAME_ADD",
            "controller_button_x": "COPY",
            "controller_button_y": "PASTE",
            "controller_button_rightshoulder": "NEXT_MODE",
            "trigger_action": "MOUSE_RIGHT",
            "axis.stick_mode": "COMBINED",
            "axis.combined_action": "PAN_VIEW",
        },
    },
    {
        "name": "Orientation",
        "left": {
            "controller_button_dpright": "PLANE_X",
            "controller_button_dpup": "PLANE_Y",
            "controller_button_dpdown": "PLANE_Z",
            "controller_button_leftshoulder": "PREV_MODE",
            "trigger_action": "MOUSE_LEFT",
            "axis.stick_mode": "COMBINED",
            "axis.combined_action": "ROTATE_VIEW",
        },
        "right": {
            "controller_button_x": "KEYFRAME_REMOVE",
            "controller_button_b": "DELETE",
            "controller_button_y": "DUPLICATE",
            "controller_button_rightshoulder": "NEXT_MODE",
            "trigger_action": "MOUSE_RIGHT",
            "axis.stick_mode": "SEPARATE",
            "axis.axis_x_action": "PAN_LR",
            "axis.axis_y_action": "ORBIT_UD",
        },
    },
]


def assign_side(side: GamepadSideSettings, data: Dict[str, str]):
    for key, value in data.items():
        if key.startswith("axis."):
            attr = key.split(".", 1)[1]
            if hasattr(side.axis, attr):
                setattr(side.axis, attr, value)
        elif hasattr(side, key):
            setattr(side, key, value)


def _is_gamepad_preferences(prefs) -> bool:
    if not prefs:
        return False
    required = ("modes", "ensure_default_modes", "enable")
    if not all(hasattr(prefs, attr) for attr in required):
        print(f"[Gamepad Control] Preferences missing required attributes: {[attr for attr in required if not hasattr(prefs, attr)]}")
    return all(hasattr(prefs, attr) for attr in required)


def get_addon_preferences(context=None) -> Optional[CL_GamepadPreferences]:
    prefs_source = getattr(context, "preferences", None)
    if not prefs_source:
        prefs_source = getattr(bpy.context, "preferences", None)
    if not prefs_source:
        return None

    addon_ids = {
        ADDON_PACKAGE,
        getattr(CL_GamepadPreferences, "bl_idname", None),
    }

    for addon_id in addon_ids:
        if not addon_id:
            continue
        addon = prefs_source.addons.get(addon_id)
        if addon:
            # print(f"[Gamepad Control] Found preferences in addon '{addon_id}'")
            prefs = getattr(addon, "preferences", None)
            if _is_gamepad_preferences(prefs):
                # print(f"[Gamepad Control] Returning preferences from addon '{addon_id}'")
                getattr(prefs, "ensure_default_modes", lambda: None)()
                return prefs  # type: ignore[return-value]

    for addon in prefs_source.addons.values():
        prefs = getattr(addon, "preferences", None)
        if _is_gamepad_preferences(prefs):
            print(f"[Gamepad Control] Found preferences in addon '{addon.module}'")
            getattr(prefs, "ensure_default_modes", lambda: None)()
            return prefs  # type: ignore[return-value]
    return None


def get_enabled_mode_indices(prefs: Optional[CL_GamepadPreferences]) -> List[int]:
    if not prefs or not getattr(prefs, "modes", None):
        return []
    return [index for index, mode in enumerate(prefs.modes) if getattr(mode, "use_mode", True)]


PREFERENCE_CLASSES = (
    GamepadAxisSettings,
    GamepadSideSettings,
    GamepadModeSettings,
    CL_GamepadPreferences,
)


__all__ = [
    "BUTTON_ACTION_ITEMS",
    "STICK_MODE_ITEMS",
    "COMBINED_AXIS_ACTION_ITEMS",
    "SEPARATE_AXIS_ACTION_ITEMS",
    "format_action_label",
    "format_combined_axis_label",
    "format_separate_axis_label",
    "get_addon_preferences",
    "get_enabled_mode_indices",
    "PREFERENCE_CLASSES",
]
