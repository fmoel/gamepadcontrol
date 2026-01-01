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

"""Operators for gamepad mode indicator in View3D header."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

import bpy
from bpy.props import IntProperty

from .controller_actions import controller_actions
from .preferences import get_addon_preferences


def redraw_view3d_headers():
    """Force redraw of all View3D headers to update mode display."""
    wm = getattr(bpy.context, "window_manager", None)
    if not wm:
        return
    for window in wm.windows:
        screen = window.screen
        if not screen:
            continue
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


class CL_OT_toggle_mode_indicator(bpy.types.Operator):
    """Toggle gamepad mode indicator visibility in View3D header"""
    bl_idname = "view3d.cl_toggle_mode_indicator"
    bl_label = "Gamepad Mode Indicator"
    bl_description = "Show or hide the gamepad mode indicator in the 3D View header"

    def execute(self, context):
        wm = context.window_manager
        wm.cl_show_mode_display = not getattr(wm, "cl_show_mode_display", False)
        redraw_view3d_headers()
        return {'FINISHED'}


class CL_OT_set_gamepad_mode(bpy.types.Operator):
    """Set the active gamepad mode"""
    bl_idname = "view3d.cl_set_gamepad_mode"
    bl_label = "Set Gamepad Mode"
    bl_description = "Activate the selected gamepad mode"

    mode_index: IntProperty(name="Mode Index", min=0)

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs or not prefs.modes:
            return {'CANCELLED'}
        target = int(self.mode_index)
        if target < 0 or target >= len(prefs.modes):
            return {'CANCELLED'}
        mode = prefs.modes[target]
        if not getattr(mode, "use_mode", True):
            self.report({'INFO'}, "Mode is disabled")
            return {'CANCELLED'}

        prefs.modes_index = target
        wm = context.window_manager
        running = getattr(wm, "cl_controller_running", False)
        if running:
            controller_actions.set_mode(context, target)
        else:
            controller_actions.mode_index = target
            controller_actions.last_mode_index = None
            prefs.update_mode_statuses(active_index=None)
            redraw_view3d_headers()
        return {'FINISHED'}


GAMEPAD_INDICATOR_OPERATOR_CLASSES = (
    CL_OT_toggle_mode_indicator,
    CL_OT_set_gamepad_mode,
)


__all__ = [
    "GAMEPAD_INDICATOR_OPERATOR_CLASSES",
    "redraw_view3d_headers",
]
