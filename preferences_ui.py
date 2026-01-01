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

"""UI helpers and classes for the Gamepad Control preferences."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

from bpy.types import Panel, UIList, Operator
from bpy.props import EnumProperty, StringProperty, IntProperty

from .preferences import (
    CL_GamepadPreferences,
    GamepadAxisSettings,
    GamepadModeSettings,
    GamepadSideSettings,
    get_addon_preferences,
)
from .io_operations import (
    CL_OT_GamepadExportAll,
    CL_OT_GamepadImportAll,
    CL_OT_GamepadExportMode,
    CL_OT_GamepadImportMode,
    CL_OT_GamepadResetToDefaults,
)


class CL_UL_GamepadModes(UIList):
    bl_idname = "CL_UL_gamepad_modes"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mode: GamepadModeSettings = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(mode, "use_mode", text="")
            row.prop(mode, "name", text="", emboss=False)
            status_map = {
                'ACTIVE': "Active",
                'ENABLED': "Enabled",
                'DISABLED': "Disabled",
            }
            row.label(text=status_map.get(getattr(mode, "ui_status", 'ENABLED'), ""))
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.enabled = bool(getattr(mode, "use_mode", True))
            layout.label(text=mode.name)


class CL_OT_GamepadModeAdd(Operator):
    bl_idname = "cl.gamepad_mode_add"
    bl_label = "Add Mode"
    bl_description = "Add a new gamepad mode"

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs:
            return {'CANCELLED'}
        mode = prefs.modes.add()
        mode.name = f"Mode {len(prefs.modes)}"
        mode["_previous_name"] = mode.name  # Initialize previous name tracking
        prefs.modes_index = len(prefs.modes) - 1
        prefs.update_mode_statuses()
        return {'FINISHED'}


class CL_OT_GamepadModeRemove(Operator):
    bl_idname = "cl.gamepad_mode_remove"
    bl_label = "Remove Mode"
    bl_description = "Remove the selected gamepad mode"

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return prefs is not None and len(prefs.modes) > 1

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs or not prefs.modes:
            return {'CANCELLED'}
        
        # Get the mode name being deleted
        deleted_mode_name = prefs.modes[prefs.modes_index].name
        
        # Clear any extra data references to this mode
        self._clear_extra_references(prefs, deleted_mode_name)
        
        prefs.modes.remove(prefs.modes_index)
        prefs.modes_index = max(0, prefs.modes_index - 1)
        prefs.update_mode_statuses()
        return {'FINISHED'}

    def _clear_extra_references(self, prefs, mode_name):
        """Clear all extra data references to the deleted mode."""
        for mode in prefs.modes:
            # Check left side buttons
            if mode.left_side:
                for button in ["controller_button_dpup", "controller_button_dpdown", 
                             "controller_button_dpleft", "controller_button_dpright",
                             "controller_button_leftstick", "controller_button_leftshoulder"]:
                    extra_prop = f"{button}_extra"
                    if hasattr(mode.left_side, extra_prop):
                        if getattr(mode.left_side, extra_prop) == mode_name:
                            setattr(mode.left_side, extra_prop, "")
                # Check left trigger
                if hasattr(mode.left_side, "trigger_extra"):
                    if mode.left_side.trigger_extra == mode_name:
                        mode.left_side.trigger_extra = ""
            
            # Check right side buttons
            if mode.right_side:
                for button in ["controller_button_a", "controller_button_b",
                             "controller_button_x", "controller_button_y",
                             "controller_button_rightstick", "controller_button_rightshoulder"]:
                    extra_prop = f"{button}_extra"
                    if hasattr(mode.right_side, extra_prop):
                        if getattr(mode.right_side, extra_prop) == mode_name:
                            setattr(mode.right_side, extra_prop, "")
                # Check right trigger
                if hasattr(mode.right_side, "trigger_extra"):
                    if mode.right_side.trigger_extra == mode_name:
                        mode.right_side.trigger_extra = ""
            
            # Check misc buttons
            for button in ["controller_button_back", "controller_button_start"]:
                extra_prop = f"{button}_extra"
                if hasattr(mode, extra_prop):
                    if getattr(mode, extra_prop) == mode_name:
                        setattr(mode, extra_prop, "")


class CL_OT_GamepadModeMove(Operator):
    bl_idname = "cl.gamepad_mode_move"
    bl_label = "Move Mode"
    bl_description = "Move the selected mode up or down"

    direction: EnumProperty(items=[('UP', "Up", "Move up"), ('DOWN', "Down", "Move down")])

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return prefs is not None and len(prefs.modes) > 1

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs:
            return {'CANCELLED'}
        idx = prefs.modes_index
        if self.direction == 'UP' and idx > 0:
            prefs.modes.move(idx, idx - 1)
            prefs.modes_index -= 1
        elif self.direction == 'DOWN' and idx < len(prefs.modes) - 1:
            prefs.modes.move(idx, idx + 1)
            prefs.modes_index += 1
        return {'FINISHED'}


class CL_PT_GamepadInputPreferences(Panel):
    bl_label = "Gamepad"
    bl_space_type = 'PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_context = "input"

    def draw(self, context):
        prefs = get_addon_preferences(context)
        if not prefs:
            self.layout.label(text="Enable the add-on to configure the gamepad controller.", icon='INFO')
            return
        prefs.draw_in_input_panel(self.layout, context)


def draw_preferences_ui(prefs: CL_GamepadPreferences, layout, context) -> None:
    general_box = layout.column(align=True)
    general_box.prop(prefs, "enable", text="Auto Connect")
    general_box.prop(prefs, "show_mode_display_on_startup", text="Show Mode Display on Startup")
    general_box.prop(prefs, "show_info_overlay_on_startup", text="Show Info Overlay on Startup")
    general_box.separator()
    general_box.label(text="Gamepad Modes", icon="NODE_COMPOSITING")

    # Split the mode selection area into two columns
    main_row = layout.row()
    
    # Left column: Mode list with add/remove/move buttons
    left_col = main_row.column()
    row = left_col.row()
    row.template_list("CL_UL_gamepad_modes", "gamepad_modes", prefs, "modes", prefs, "modes_index")
    col = row.column(align=True)
    col.operator(CL_OT_GamepadModeAdd.bl_idname, icon='ADD', text="")
    col.operator(CL_OT_GamepadModeRemove.bl_idname, icon='REMOVE', text="")
    col.separator()
    move_up = col.operator(CL_OT_GamepadModeMove.bl_idname, icon='TRIA_UP', text="")
    move_up.direction = 'UP'
    move_down = col.operator(CL_OT_GamepadModeMove.bl_idname, icon='TRIA_DOWN', text="")
    move_down.direction = 'DOWN'
    
    # Right column: Import/Export buttons
    right_col = main_row.column()
    
    # All modes section
    box = right_col.box()
    box.label(text="All Modes & Settings", icon='PREFERENCES')
    row = box.row(align=True)
    row.operator(CL_OT_GamepadImportAll.bl_idname, text="Import All", icon='IMPORT')
    row.operator(CL_OT_GamepadExportAll.bl_idname, text="Export All", icon='EXPORT')
    row.operator(CL_OT_GamepadResetToDefaults.bl_idname, text="Reset to Defaults", icon='LOOP_BACK')
    
    # Single mode section
    box = right_col.box()
    box.label(text="Current Mode", icon='SOLO_ON')
    row = box.row(align=True)
    row.operator(CL_OT_GamepadImportMode.bl_idname, text="Import Mode", icon='IMPORT')
    row.operator(CL_OT_GamepadExportMode.bl_idname, text="Export Mode", icon='EXPORT')

    if not prefs.modes:
        return
    mode = prefs.modes[prefs.modes_index]
    box = layout.box()
    box.prop(mode, "name")
    col = box.column(align=True)
    
    # Back button with optional target mode
    row = col.row(align=True)
    row.prop(mode, "controller_button_back", text="Back")
    if mode.controller_button_back == 'TEMP_MODE_SHIFT':
        row.prop_search(mode, "controller_button_back_extra", prefs, "modes", text="", icon='NONE')
    
    # Start button with optional target mode
    row = col.row(align=True)
    row.prop(mode, "controller_button_start", text="Start")
    if mode.controller_button_start == 'TEMP_MODE_SHIFT':
        row.prop_search(mode, "controller_button_start_extra", prefs, "modes", text="", icon='NONE')
    
    columns = box.row()
    columns.scale_y = 1.0
    left_col = columns.column()
    right_col = columns.column()
    _draw_side(left_col.box(), mode.left_side, "Left Side (D-Pad / Left Stick)")
    _draw_side(right_col.box(), mode.right_side, "Right Side (ABXY / Right Stick)")


def _draw_side(layout, side: GamepadSideSettings, title: str) -> None:
    layout.label(text=title)
    button_column = layout.column(align=True)
    
    # Get preferences for mode selection
    prefs = get_addon_preferences()
    
    # Determine which buttons to show based on title
    if "Left" in title:
        button_fields = [
            ("controller_button_dpup", "D-Pad Up"),
            ("controller_button_dpdown", "D-Pad Down"),
            ("controller_button_dpleft", "D-Pad Left"),
            ("controller_button_dpright", "D-Pad Right"),
            ("controller_button_leftshoulder", "Left Shoulder"),
            ("trigger_action", "Left Trigger"),
            ("controller_button_leftstick", "Left Stick"),
        ]
    else:
        button_fields = [
            ("controller_button_a", "A Button"),
            ("controller_button_b", "B Button"),
            ("controller_button_x", "X Button"),
            ("controller_button_y", "Y Button"),
            ("controller_button_rightshoulder", "Right Shoulder"),
            ("trigger_action", "Right Trigger"),
            ("controller_button_rightstick", "Right Stick"),
        ]
    
    for attr, label in button_fields:
        row = button_column.row(align=True)
        row.prop(side, attr, text=label)
        
        # Show target mode selector if action is TEMP_MODE_SHIFT
        action_value = getattr(side, attr, 'NONE')
        if action_value == 'TEMP_MODE_SHIFT':
            # Determine the extra property name
            if attr == "trigger_action":
                extra_attr = "trigger_extra"
            else:
                extra_attr = f"{attr}_extra"
            row.prop_search(side, extra_attr, prefs, "modes", text="", icon='NONE')
    axis_box = layout
    axis_box.use_property_split = True
    axis_box.use_property_decorate = False
    axis = side.axis
    axis_box.label(text="Stick Settings")
    axis_box.prop(axis, "stick_mode", text="Mode")
    
    # Invert X/Y in horizontal layout (like Stretch UVs)
    row = axis_box.row(heading="Invert")
    row.prop(axis, "invert_x", text="X", toggle=True)
    row.prop(axis, "invert_y", text="Y", toggle=True)

    mode = axis.stick_mode
    if mode == 'COMBINED':
        axis_box.prop(axis, "combined_action", text="Combined")
        col = axis_box.column(align=True)
        _draw_combined_action_settings(col, axis)
        col.prop(axis, "axis_deadzone_x", text="X Deadzone")
        col.prop(axis, "axis_deadzone_y", text="Y Deadzone")
    elif mode == 'SEPARATE':
        axis_box.separator()
        x_col = axis_box.column(align=True)
        x_col.prop(axis, "axis_x_action", text="X Axis")
        _draw_axis_action_settings(x_col, axis, axis.axis_x_action)
        y_col = axis_box.column(align=True)
        y_col.prop(axis, "axis_y_action", text="Y Axis")
        y_col.prop(axis, "axis_deadzone_y", text="Y Deadzone")
        _draw_axis_action_settings(y_col, axis, axis.axis_y_action)
    else:
        include_diagonals = mode == 'EIGHT_BUTTONS'
        _draw_button_mode(axis_box, axis, include_diagonals)


def _draw_combined_action_settings(layout, axis: GamepadAxisSettings) -> None:
    action = axis.combined_action
    if action == 'MOUSE_POINTER':
        layout.prop(axis, "cursor_speed", text="Cursor Speed")
    elif action == 'PAN_VIEW':
        layout.prop(axis, "pan_speed", text="Pan Speed")
    elif action == 'ROTATE_VIEW':
        layout.prop(axis, "rotate_speed", text="Rotate Speed")
    elif action == 'ORBIT_SELECTED':
        layout.prop(axis, "orbit_speed", text="Orbit Speed")


def _draw_axis_action_settings(layout, axis: GamepadAxisSettings, action_id: str) -> None:
    if action_id == 'MOVE_VIEW':
        layout.prop(axis, "dolly_speed", text="Move Speed")
    elif action_id in {'PAN_LR', 'PAN_UD'}:
        layout.prop(axis, "pan_speed", text="Pan Speed")
    elif action_id in {'ROTATE_LOCAL_X', 'ROTATE_LOCAL_Y', 'ORBIT_LR', 'ORBIT_UD'}:
        layout.prop(axis, "orbit_speed", text="Orbit Speed")


def _draw_button_mode(layout, axis: GamepadAxisSettings, include_diagonals: bool) -> None:
    if include_diagonals:
        direction_fields = [
            ("dir_up_left_action", "Up-Left"),
            ("dir_up_action", "Up"),
            ("dir_up_right_action", "Up-Right"),
            ("dir_left_action", "Left"),
            ("dir_right_action", "Right"),
            ("dir_down_left_action", "Down-Left"),
            ("dir_down_action", "Down"),
            ("dir_down_right_action", "Down-Right"),
        ]
    else:
        direction_fields = [
            ("dir_up_action", "Up"),
            ("dir_down_action", "Down"),
            ("dir_left_action", "Left"),
            ("dir_right_action", "Right"),
        ]
    button_column = layout.column(align=True)
    for attr, label in direction_fields:
        row = button_column.row(align=True)
        row.prop(axis, attr, text=label)

    layout.prop(axis, "button_deadzone", text="Threshold")


PREFERENCE_UI_CLASSES = (
    CL_UL_GamepadModes,
    CL_OT_GamepadModeAdd,
    CL_OT_GamepadModeRemove,
    CL_OT_GamepadModeMove,
    CL_PT_GamepadInputPreferences,
)


__all__ = [
    "CL_UL_GamepadModes",
    "CL_OT_GamepadModeAdd",
    "CL_OT_GamepadModeRemove",
    "CL_OT_GamepadModeMove",
    "CL_PT_GamepadInputPreferences",
    "draw_preferences_ui",
    "PREFERENCE_UI_CLASSES",
]
