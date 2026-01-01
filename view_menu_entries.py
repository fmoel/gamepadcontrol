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
# along with this program. If not, see <http://www.gnu.org/licenses/>.#

"""View menu entries for gamepad overlay and mode display controls."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

import bpy


def draw_gamepad_view_menu(self, context):
    """Add Gamepad Overlay and Mode Display toggles to View menu."""
    layout = self.layout
    wm = context.window_manager
    
    overlay_on = getattr(wm, "cl_show_gamepad_overlay", False)
    layout.operator(
        "view3d.cl_toggle_gamepad_overlay",
        icon='CHECKBOX_HLT' if overlay_on else 'CHECKBOX_DEHLT',
        depress=overlay_on
    )
    
    mode_on = getattr(wm, "cl_show_mode_display", False)
    layout.operator(
        "view3d.cl_toggle_mode_indicator",
        icon='CHECKBOX_HLT' if mode_on else 'CHECKBOX_DEHLT',
        depress=mode_on
    )


def register_view_menu_entries():
    """Register view menu entries."""
    bpy.types.VIEW3D_MT_view.prepend(draw_gamepad_view_menu)


def unregister_view_menu_entries():
    """Unregister view menu entries."""
    if hasattr(bpy.types, "VIEW3D_MT_view"):
        try:
            bpy.types.VIEW3D_MT_view.remove(draw_gamepad_view_menu)
        except ValueError:
            pass


__all__ = [
    "draw_gamepad_view_menu",
    "register_view_menu_entries",
    "unregister_view_menu_entries",
]
