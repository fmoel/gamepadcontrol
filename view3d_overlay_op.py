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

"""Operators for gamepad overlay in View3D."""

#pyright: reportInvalidTypeForm=false

from __future__ import annotations

import bpy


class CL_OT_toggle_gamepad_overlay(bpy.types.Operator):
    """Toggle gamepad info overlay visibility in View3D"""
    bl_idname = "view3d.cl_toggle_gamepad_overlay"
    bl_label = "Gamepad Overlay"
    bl_description = "Show or hide the gamepad info overlay in the 3D View"

    def execute(self, context):
        wm = context.window_manager
        wm.cl_show_gamepad_overlay = not getattr(wm, "cl_show_gamepad_overlay", False)
        return {'FINISHED'}


GAMEPAD_OVERLAY_OPERATOR_CLASSES = (
    CL_OT_toggle_gamepad_overlay,
)


__all__ = [
    "GAMEPAD_OVERLAY_OPERATOR_CLASSES",
]
