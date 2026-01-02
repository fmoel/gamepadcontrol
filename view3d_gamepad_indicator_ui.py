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

"""UI panels for gamepad mode indicator in View3D header."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

from typing import Optional

import bpy

from .controller_actions import get_controller_actions
from .preferences import get_addon_preferences, get_enabled_mode_indices
from .view3d_overlay_ui import build_gamepad_snapshot


class VIEW3D_PT_gamepad_status(bpy.types.Panel):
    """Gamepad status and controls popover panel in View3D header."""
    bl_label = "Gamepad"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        layout = self.layout
        prefs = get_addon_preferences(context)

        if not prefs or not prefs.modes:
            layout.label(text="Define at least one gamepad mode.", icon='INFO')
            return

        wm = context.window_manager
        running = getattr(wm, "cl_controller_running", False)
        active_index = get_controller_actions().mode_index if running else None
        prefs.update_mode_statuses(active_index=active_index)

        mode_col = layout.column(align=True)
        mode_col.label(text="Gamepad Modes")
        for idx, mode in enumerate(prefs.modes):
            row = mode_col.row(align=True)
            op = row.operator(
                "view3d.cl_set_gamepad_mode",
                text=mode.name,
                depress=prefs.modes_index == idx,
            )
            op.mode_index = idx
            if not getattr(mode, "use_mode", True):
                row.enabled = False

        layout.separator()

        controls = layout.column(align=True)
        controls.prop(wm, "cl_show_gamepad_overlay", text="Info Overlay", toggle=True)
        controls.prop(wm, "cl_show_mode_display", text="Mode Indicator", toggle=True)


def draw_gamepad_status_indicator(self, context):
    """Draw gamepad mode indicator and popover in View3D header."""
    wm = getattr(context, "window_manager", None)
    if not wm:
        return
    
    show_indicator = getattr(wm, "cl_show_mode_display", False)
    if not show_indicator:
        return

    snapshot = build_gamepad_snapshot(context)
    if not snapshot:
        return

    running = getattr(wm, "cl_controller_running", False)
    
    # Get custom icon
    from . import icon_collections
    icons = icon_collections.get("main")
    gamepad_icon = icons["gamepad"].icon_id if icons and "gamepad" in icons else 0
    
    layout = self.layout
    row = layout.row(align=True)
    row.active = running  # Apply active state to entire row
    
    # Toggle button for starting/stopping the gamepad
    if gamepad_icon:
        row.operator("wm.cl_controller_inputs", text="", icon_value=gamepad_icon, depress=running)
    else:
        row.operator("wm.cl_controller_inputs", text="", icon='MOUSE_LMB', emboss=not running)
    
    # Popover for mode selection and settings
    row.popover(
        panel="VIEW3D_PT_gamepad_status",
        text=snapshot.mode_name,
    )


def register_gamepad_indicator_ui():
    """Register gamepad indicator UI in View3D header."""
    bpy.types.VIEW3D_HT_header.append(draw_gamepad_status_indicator)


def unregister_gamepad_indicator_ui():
    """Unregister gamepad indicator UI from View3D header."""
    if hasattr(bpy.types, "VIEW3D_HT_header"):
        try:
            bpy.types.VIEW3D_HT_header.remove(draw_gamepad_status_indicator)
        except ValueError:
            pass


GAMEPAD_INDICATOR_UI_CLASSES = (
    VIEW3D_PT_gamepad_status,
)


__all__ = [
    "GAMEPAD_INDICATOR_UI_CLASSES",
    "register_gamepad_indicator_ui",
    "unregister_gamepad_indicator_ui",
    "draw_gamepad_status_indicator",
]
