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

"""Blender operator definitions for controller workflows."""

# pyright: reportInvalidTypeForm=false

import bpy

from .controller_actions import controller_actions
from .sdl_handler import create_reader
from .sdl_handler import SDL2_Controller_Handler


class CL_OT_ControllerInputs(bpy.types.Operator):
    """Listen for controller input events."""

    bl_idname = "wm.cl_controller_inputs"
    bl_label = "Use Gamepad"

    _timer = None

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            controller_actions.notify_mouse_move(event, context)
        if event.type == 'TIMER':
            CL_OT_ControllerInputs.sdl2_controller_handler.poll(context)
        wm = context.window_manager
        if not wm.cl_controller_running:
            self.cancel(context)
            return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        create_reader()

        wm = context.window_manager
        if wm.cl_controller_running:
            wm.cl_controller_running = False
            return {'CANCELLED'}

        CL_OT_ControllerInputs.sdl2_controller_handler = SDL2_Controller_Handler()

        wm = context.window_manager
        self._timer = wm.event_timer_add(time_step=1 / 60, window=context.window)
        wm.modal_handler_add(self)

        wm.cl_controller_running = True
        self.report({'INFO'}, "Gampad started")

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)

        wm.cl_controller_running = False

        controller_actions.reset(context)

        self.report({'INFO'}, "Gamepad stopped")


__all__ = ["CL_OT_ControllerInputs"]
