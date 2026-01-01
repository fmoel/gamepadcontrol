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
 
"""SDL2-based controller polling logic and reader utilities."""

# pyright: reportInvalidTypeForm=false

import time

import bpy
import sdl2
from .controller_actions import controller_actions


def get_reader():
    """Return the shared controller reader object if it already exists."""
    return bpy.data.objects.get("CL_reader")


def create_reader():
    """Create the controller reader object if it does not yet exist."""
    cl_reader = get_reader()
    if cl_reader is None:
        cl_reader = bpy.data.objects.new("CL_reader", None)
        cl_reader.use_fake_user = True
    return cl_reader


def ensure_prop_range(id_block, prop_name, min_value, max_value):
    """Attach UI range metadata to an ID property if it differs from desired bounds."""
    if not id_block or prop_name not in id_block.keys():
        return
    ui_manager = getattr(id_block, "id_properties_ui", None)
    if not ui_manager:
        return
    try:
        ui_data = ui_manager(prop_name)
    except ReferenceError:
        return
    current = ui_data.as_dict() or {}
    needs_update = (
        current.get("min") != min_value
        or current.get("max") != max_value
        or current.get("soft_min") != min_value
        or current.get("soft_max") != max_value
    )
    if needs_update:
        ui_data.update(min=min_value, max=max_value, soft_min=min_value, soft_max=max_value)


class SDL2_Controller_Handler:
    """Poll SDL2 for controller input and forward the data to Blender."""

    RETRY_INTERVAL = 1.0

    def __init__(self):
        self.controller = None
        self.joystick = None
        self.controller_name = ""
        self._next_discovery = 0.0
        self._reported_missing = False

        sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_JOYSTICK)
        self._discover_devices(force=True)

    def _close_controller(self):
        if self.controller:
            sdl2.SDL_GameControllerClose(self.controller)
            self.controller = None
        if not self.joystick:
            self.controller_name = ""

    def _close_joystick(self):
        if self.joystick:
            sdl2.SDL_JoystickClose(self.joystick)
            self.joystick = None
        if not self.controller:
            self.controller_name = ""

    def _discover_devices(self, force=False):
        now = time.monotonic()
        if not force and now < self._next_discovery:
            return
        self._next_discovery = now + self.RETRY_INTERVAL

        if self.controller and not sdl2.SDL_GameControllerGetAttached(self.controller):
            self._close_controller()
        if self.joystick and not sdl2.SDL_JoystickGetAttached(self.joystick):
            self._close_joystick()

        if self.controller:
            self._reported_missing = False
            return

        for i in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(i):
                controller = sdl2.SDL_GameControllerOpen(i)
                if controller:
                    self._close_joystick()
                    self.controller = controller
                    name_ptr = sdl2.SDL_GameControllerName(controller)
                    self.controller_name = name_ptr.decode("utf-8") if name_ptr else "Unknown"
                    self._reported_missing = False
                    return

        if self.joystick:
            self._reported_missing = False
            return

        if sdl2.SDL_NumJoysticks() > 0:
            joystick = sdl2.SDL_JoystickOpen(0)
            if joystick:
                self.joystick = joystick
                name_ptr = sdl2.SDL_JoystickName(joystick)
                self.controller_name = name_ptr.decode("utf-8") if name_ptr else "Unknown"
                self._reported_missing = False
                return

        if not self._reported_missing:
            print("[SDL2_Controller_Handler] No game controller or joystick found. Retrying...")
            self._reported_missing = True

    def poll(self, context):
        self._discover_devices()
        if not self.controller and not self.joystick:
            return
        sdl2.SDL_PumpEvents()
        cl_reader = get_reader()
        if not cl_reader:
            return

        if self.controller:
            for axis in range(sdl2.SDL_CONTROLLER_AXIS_MAX):
                if sdl2.SDL_GameControllerHasAxis(self.controller, axis):
                    name = sdl2.SDL_GameControllerGetStringForAxis(axis).decode("utf-8")
                    prop_id = f"controller_axis_{name}"
                    raw = sdl2.SDL_GameControllerGetAxis(self.controller, axis)
                    value = max(-1.0, min(1.0, raw / 32767.0))
                    cl_reader[prop_id] = value
                    ensure_prop_range(cl_reader, prop_id, -1.0, 1.0)

            for button in range(sdl2.SDL_CONTROLLER_BUTTON_MAX):
                if sdl2.SDL_GameControllerHasButton(self.controller, button):
                    name = sdl2.SDL_GameControllerGetStringForButton(button).decode("utf-8")
                    prop_id = f"controller_button_{name}"
                    pressed = bool(sdl2.SDL_GameControllerGetButton(self.controller, button))
                    cl_reader[prop_id] = pressed

        elif self.joystick:
            num_axes = sdl2.SDL_JoystickNumAxes(self.joystick)
            for axis in range(num_axes):
                raw = sdl2.SDL_JoystickGetAxis(self.joystick, axis)
                value = max(-1.0, min(1.0, raw / 32767.0))
                prop_id = f"controller_axis_{axis}"
                cl_reader[prop_id] = value
                ensure_prop_range(cl_reader, prop_id, -1.0, 1.0)

            num_buttons = sdl2.SDL_JoystickNumButtons(self.joystick)
            for button in range(num_buttons):
                pressed = bool(sdl2.SDL_JoystickGetButton(self.joystick, button))
                prop_id = f"controller_button_{button}"
                cl_reader[prop_id] = pressed

        cl_reader.location = cl_reader.location

        if context:
            controller_actions.apply(context, cl_reader)


__all__ = ["SDL2_Controller_Handler", "get_reader", "create_reader", "ensure_prop_range"]
