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

"""Controller axis and button to Blender viewport action mapping."""

# pyright: reportInvalidTypeForm=false

import math

import bpy
from mathutils import Vector, Quaternion

from .preferences import get_addon_preferences, get_enabled_mode_indices
from .system_events import SystemEventInjector
from .enablement import is_controller_running


class ControllerActionExecutor:
    """Map controller axes/buttons to Blender viewport actions with mode support."""

    AXIS_GATE = 0.6
    CURSOR_GATE = 0.15
    CURSOR_SPEED_MULTIPLIER = 15.0  # Converts UI value (0.0-1.0) to effective speed
    MODE_SWITCH_ACTIONS = {'NEXT_MODE', 'PREV_MODE', 'TEMP_MODE_SHIFT'}
    OVERLAY_ACTIONS = {'TOGGLE_OVERLAY', 'SHOW_OVERLAY'}

    LEFT_BUTTONS = (
        "controller_button_dpup",
        "controller_button_dpdown",
        "controller_button_dpleft",
        "controller_button_dpright",
        "controller_button_leftstick",
        "controller_button_leftshoulder",
    )
    RIGHT_BUTTONS = (
        "controller_button_a",
        "controller_button_b",
        "controller_button_x",
        "controller_button_y",
        "controller_button_rightstick",
        "controller_button_rightshoulder",
    )
    MISC_BUTTONS = (
        "controller_button_back",
        "controller_button_start",
    )

    LEFT_AXIS_KEYS = ("controller_axis_leftx", "controller_axis_lefty")
    RIGHT_AXIS_KEYS = ("controller_axis_rightx", "controller_axis_righty")
    LEFT_TRIGGER_KEY = "controller_axis_lefttrigger"
    RIGHT_TRIGGER_KEY = "controller_axis_righttrigger"

    DIRECTION_ATTRS = ("up", "down", "left", "right", "up_left", "up_right", "down_left", "down_right")
    CARDINAL_ATTRS = ("up", "down", "left", "right", "dir_right_action")

    HOLDABLE_ACTIONS = {"MOUSE_LEFT", "MOUSE_RIGHT"}

    DEFAULT_AXIS_DEADZONE = 0.1
    DEFAULT_CURSOR_SPEED = 0.5
    DEFAULT_PAN_SPEED = 0.08
    DEFAULT_DOLLY_SPEED = 0.2
    DEFAULT_ORBIT_SPEED = 0.02
    DEFAULT_ROTATE_SPEED = 0.02
    DEFAULT_ROLL_SPEED = 0.05
    DEFAULT_ZOOM_SPEED = 0.05

    def __init__(self):
        self.button_state = {}
        self.axis_state = {}
        self.active_mouse_buttons = set()
        self.cursor_owner = 'controller'
        self.cursor_window = None
        self.cursor_position = None
        self.cursor_fractional_x = 0.0
        self.cursor_fractional_y = 0.0
        self._last_mouse_event = None
        self.mode_index = 0
        self.last_mode_index = None
        self.current_mode_label = ""
        self.injector = SystemEventInjector()
        self.event_warning_shown = False
        self.mode_button_state = {}
        self.temp_mode_shift_active = False
        self.temp_mode_previous_index = None
        self.temp_mode_shift_button = None  # Track which physical button activated temp mode
        self.show_overlay_button_held = False
        self._context = None
        self._window = None
        self._reader = None
        self._rv3d = None

    def notify_mouse_move(self, event, context):
        window = getattr(context, "window", None)
        if not window or not hasattr(event, "mouse_x"):
            return
        if event.mouse_x < 0 or event.mouse_y < 0:
            return
        self.cursor_window = window
        if self.cursor_position is None:
            self.cursor_position = Vector((event.mouse_x, event.mouse_y))
        else:
            self.cursor_position.x = event.mouse_x
            self.cursor_position.y = event.mouse_y
        self.cursor_owner = 'mouse'
        self._last_mouse_event = (event.mouse_x, event.mouse_y)
        # Reset fractional accumulators when mouse takes control
        self.cursor_fractional_x = 0.0
        self.cursor_fractional_y = 0.0

    def apply(self, context, reader):
        self._context = context
        self._reader = reader
        
        # Verify that mouse buttons we think are pressed are actually still pressed
        # (This handles the case where Blender froze during window drag and missed the release)
        self._verify_mouse_button_states()
        
        prefs = get_addon_preferences(context)
        if not prefs or not prefs.modes:
            return
        
        # Always try to locate view3d, even if we had it before
        # (context can change when clicking window controls)
        if not self._locate_and_store_view3d():
            # Keep processing input even if we can't find VIEW_3D
            # This ensures buttons still work
            pass
        
        if self._window:
            self._ensure_cursor_defaults()

        modes = prefs.modes
        self.mode_index = max(0, min(self.mode_index, len(modes) - 1))
        enabled_indices = get_enabled_mode_indices(prefs)
        if not enabled_indices:
            self._flush_inputs()
            prefs.update_mode_statuses(active_index=None)
            return
        if self.mode_index not in enabled_indices:
            self.mode_index = self._fallback_enabled_index(enabled_indices)
        mode = modes[self.mode_index]
        if self.last_mode_index != self.mode_index:
            self._flush_inputs()
            self.last_mode_index = self.mode_index
        self.current_mode_label = mode.name
        prefs.update_mode_statuses(active_index=self.mode_index if is_controller_running() else None)
        
        # Check if temp mode shift button was released (before processing new mode's mappings)
        if self.temp_mode_shift_active and self.temp_mode_shift_button:
            button_pressed = bool(self._reader.get(self.temp_mode_shift_button, False))
            if not button_pressed:
                self._deactivate_temp_mode_shift()
                return  # Re-process with correct mode
        
        self._apply_mode(mode)

    def _apply_mode(self, mode):
        self._process_side(
            mode,
            mode.left_side,
            self.LEFT_BUTTONS,
            self.LEFT_AXIS_KEYS,
            self.LEFT_TRIGGER_KEY,
        )
        self._process_side(
            mode,
            mode.right_side,
            self.RIGHT_BUTTONS,
            self.RIGHT_AXIS_KEYS,
            self.RIGHT_TRIGGER_KEY,
        )
        self._process_misc_buttons(mode)

    def _process_side(self, mode, side, buttons, axis_keys, trigger_key):
        if not side:
            return
        for button in buttons:
            action = getattr(side, button, 'NONE')
            self._process_button_action(button, mode, action, side)
        self._process_trigger(trigger_key, mode, side.trigger_action, side)
        self._process_axes(axis_keys, mode, side.axis)

    def _set_overlay_visibility(self, enabled: bool):
        """Helper to toggle the overlay window-manager property and force a redraw."""
        context = self._context if self._context else bpy.context
        wm = getattr(context, "window_manager", None)
        if not wm or not hasattr(wm, "cl_show_gamepad_overlay"):
            return
        if bool(wm.cl_show_gamepad_overlay) == bool(enabled):
            return
        wm.cl_show_gamepad_overlay = bool(enabled)
        try:
            from . import view3d_overlay_ui
            view3d_overlay_ui.sync_overlay_state(context=context)
        except Exception:
            pass

    def _process_button_action(self, button, mode, action, side=None):
        if action == 'NONE' or not button:
            return
        current = bool(self._reader.get(button, False))
        if action in self.MODE_SWITCH_ACTIONS:
            extra_data = getattr(side, f"{button}_extra", "") if side else ""
            self._process_mode_switch_button(action, button, current, extra_data)
            return
        if action in self.OVERLAY_ACTIONS:
            self._process_overlay_button(action, button, current)
            return
        state_key = self._state_key(mode, button)
        previous = self.button_state.get(state_key, False)
        if current == previous:
            return
        self.button_state[state_key] = current
        if current:
            self._execute_button_press(action)
        else:
            self._execute_button_release(action)

    def _process_trigger(self, trigger, mode, action, side=None):
        if action == 'NONE' or not trigger:
            return
        value = self._reader.get(trigger, 0.0)
        pressed = value > 0.45
        state_key = self._state_key(mode, trigger)
        previous = self.button_state.get(state_key, False)
        if pressed == previous:
            return
        self.button_state[state_key] = pressed
        if pressed:
            if action in self.MODE_SWITCH_ACTIONS:
                extra_data = getattr(side, "trigger_extra", "") if side else ""
                self._process_mode_switch_button(action, trigger, True, extra_data)
            else:
                self._execute_button_press(action)
        else:
            if action not in self.MODE_SWITCH_ACTIONS:
                self._execute_button_release(action)
                # Also force release the actual mouse button if it's a mouse action
                if action == 'MOUSE_LEFT' and 'LEFTMOUSE' in self.active_mouse_buttons:
                    self.active_mouse_buttons.discard('LEFTMOUSE')
                elif action == 'MOUSE_RIGHT' and 'RIGHTMOUSE' in self.active_mouse_buttons:
                    self.active_mouse_buttons.discard('RIGHTMOUSE')

    def _process_axes(self, axis_keys, mode, axis_settings):
        if not axis_settings or not axis_keys:
            return
        x = self._reader.get(axis_keys[0], 0.0)
        y = self._reader.get(axis_keys[1], 0.0)
        if getattr(axis_settings, "invert_x", False):
            x = -x
        if getattr(axis_settings, "invert_y", True):
            y = -y
        stick_mode = axis_settings.stick_mode
        if stick_mode == 'COMBINED':
            self._apply_combined_axis(axis_settings, x, y)
        elif stick_mode == 'SEPARATE':
            self._apply_separate_axis(axis_settings, x, y)
        elif stick_mode in {'FOUR_BUTTONS', 'EIGHT_BUTTONS'}:
            include_diagonals = stick_mode == 'EIGHT_BUTTONS'
            # Use first axis key as base for state tracking (e.g., controller_axis_leftx)
            self._apply_button_axis(mode, axis_settings, x, y, axis_keys[0], include_diagonals)

    def _apply_combined_axis(self, axis_settings, x, y):
        action = axis_settings.combined_action
        if action == 'NONE':
            return
        magnitude = math.sqrt(x * x + y * y)
        threshold = max(self._combined_deadzone(axis_settings), self.DEFAULT_AXIS_DEADZONE)
        if magnitude < threshold:
            return
        if action == 'MOUSE_POINTER':
            cursor_speed = getattr(axis_settings, "cursor_speed", self.DEFAULT_CURSOR_SPEED)
            self._update_virtual_cursor(x, y, cursor_speed, threshold)
        elif action == 'PAN_VIEW':
            pan_speed = getattr(axis_settings, "pan_speed", self.DEFAULT_PAN_SPEED)
            self._pan_view(x, y, pan_speed)
        elif action == 'ROTATE_VIEW':
            rotate_speed = getattr(axis_settings, "rotate_speed", self.DEFAULT_ROTATE_SPEED)
            self._rotate_view(yaw=-x * rotate_speed, pitch=y * rotate_speed)
        elif action == 'ZOOM_VIEW':
            zoom_speed = getattr(axis_settings, "zoom_speed", self.DEFAULT_ZOOM_SPEED)
            self._zoom_view(y * zoom_speed)
        else:
            orbit_speed = getattr(axis_settings, "orbit_speed", self.DEFAULT_ORBIT_SPEED)
            self._orbit_view(yaw=-x * orbit_speed, pitch=y * orbit_speed)

    def _apply_separate_axis(self, axis_settings, x, y):
        x_threshold = max(getattr(axis_settings, "axis_deadzone_x", 0.0), self.DEFAULT_AXIS_DEADZONE)
        y_threshold = max(getattr(axis_settings, "axis_deadzone_y", 0.0), self.DEFAULT_AXIS_DEADZONE)
        x_value = x if abs(x) >= x_threshold else 0.0
        y_value = y if abs(y) >= y_threshold else 0.0
        self._execute_separate_axis_action(axis_settings, axis_settings.axis_x_action, x_value)
        self._execute_separate_axis_action(axis_settings, axis_settings.axis_y_action, y_value)

    def _execute_separate_axis_action(self, axis_settings, action, value):
        if action == 'NONE' or abs(value) < 1e-6:
            return
        if action == 'MOVE_VIEW':
            dolly_speed = getattr(axis_settings, "dolly_speed", self.DEFAULT_DOLLY_SPEED)
            self._dolly_view(-value, dolly_speed)
        elif action == 'PAN_LR':
            pan_speed = getattr(axis_settings, "pan_speed", self.DEFAULT_PAN_SPEED)
            self._pan_view(value, 0.0, pan_speed)
        elif action == 'PAN_UD':
            pan_speed = getattr(axis_settings, "pan_speed", self.DEFAULT_PAN_SPEED)
            self._pan_view(0.0, value, pan_speed)
        elif action == 'ZOOM_VIEW':
            zoom_speed = getattr(axis_settings, "zoom_speed", self.DEFAULT_ZOOM_SPEED)
            self._zoom_view(value * zoom_speed)
        elif action == 'ROTATE_LOCAL_X':
            rotate_speed = getattr(axis_settings, "rotate_speed", self.DEFAULT_ROTATE_SPEED)
            self._rotate_view(pitch=value * rotate_speed)
        elif action == 'ROTATE_LOCAL_Y':
            rotate_speed = getattr(axis_settings, "rotate_speed", self.DEFAULT_ROTATE_SPEED)
            self._rotate_view(yaw=-value * rotate_speed)
        elif action == 'ORBIT_UD':
            orbit_speed = getattr(axis_settings, "orbit_speed", self.DEFAULT_ORBIT_SPEED)
            self._orbit_view(pitch=value * orbit_speed)
        elif action == 'ORBIT_LR':
            orbit_speed = getattr(axis_settings, "orbit_speed", self.DEFAULT_ORBIT_SPEED)
            self._orbit_view(yaw=-value * orbit_speed)

    def _apply_button_axis(self, mode, axis_settings, x, y, axis_key, include_diagonals):
        combined_deadzone = self._combined_deadzone(axis_settings)
        button_deadzone = getattr(axis_settings, "button_deadzone", 0.6)
        threshold = max(combined_deadzone, button_deadzone)
        magnitude = math.sqrt(x * x + y * y)
        if magnitude < threshold:
            direction = None
        else:
            direction = self._direction_from_axes(x, y, button_deadzone, include_diagonals)

        for name in self.DIRECTION_ATTRS:
            allowed = include_diagonals or name in self.CARDINAL_ATTRS
            action = getattr(axis_settings, f"dir_{name}_action")
            # Use axis_key + direction for unique state key (e.g., controller_axis_leftx_up)
            state_key = self._state_key(mode, f"{axis_key}_{name}")
            active = allowed and direction == name and action != 'NONE'
            previous = self.axis_state.get(state_key, False)
            if active == previous:
                continue
            self.axis_state[state_key] = active
            if active:
                self._execute_button_press(action)
            else:
                self._execute_button_release(action)

    def _direction_from_axes(self, x, y, threshold, include_diagonals=True):
        magnitude = math.sqrt(x * x + y * y)
        if magnitude < threshold:
            return None
        if not include_diagonals:
            if abs(x) >= abs(y):
                return "right" if x > 0 else "left"
            return "up" if y > 0 else "down"
        angle = math.degrees(math.atan2(y, x))
        if -22.5 <= angle < 22.5:
            return "right"
        if 22.5 <= angle < 67.5:
            return "up_right"
        if 67.5 <= angle < 112.5:
            return "up"
        if 112.5 <= angle < 157.5:
            return "up_left"
        if angle >= 157.5 or angle < -157.5:
            return "left"
        if -157.5 <= angle < -112.5:
            return "down_left"
        if -112.5 <= angle < -67.5:
            return "down"
        if -67.5 <= angle < -22.5:
            return "down_right"
        return None

    def _combined_deadzone(self, axis_settings):
        deadzone_x = getattr(axis_settings, "axis_deadzone_x", self.DEFAULT_AXIS_DEADZONE)
        deadzone_y = getattr(axis_settings, "axis_deadzone_y", self.DEFAULT_AXIS_DEADZONE)
        return max(deadzone_x, deadzone_y, self.DEFAULT_AXIS_DEADZONE)

    def _process_misc_buttons(self, mode):
        for button in self.MISC_BUTTONS:
            action = getattr(mode, button, 'NONE')
            self._process_button_action(button, mode, action, mode)

    def _execute_button_press(self, action):
        if action == 'NONE':
            return
        if action == 'MOUSE_LEFT':
            self._press_mouse_button('LEFTMOUSE')
        elif action == 'MOUSE_RIGHT':
            self._press_mouse_button('RIGHTMOUSE')
        elif action == 'PIVOT_PIE':
            bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name="VIEW3D_MT_pivot_pie")
        elif action == 'ORIENTATION_PIE':
            bpy.ops.wm.call_menu_pie('INVOKE_DEFAULT', name="VIEW3D_MT_orientations_pie")
        elif action == 'NEXT_MODE':
            self._change_mode(1)
        elif action == 'PREV_MODE':
            self._change_mode(-1)
        elif action == 'GRAB':
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        elif action == 'ROTATE':
            bpy.ops.transform.rotate('INVOKE_DEFAULT')
        elif action == 'SCALE':
            bpy.ops.transform.resize('INVOKE_DEFAULT')
        elif action == 'EXTRUDE':
            # Context-aware extrude: works in both edit and object mode
            if self._context.mode == 'EDIT_MESH':
                bpy.ops.mesh.extrude_region_move('INVOKE_DEFAULT')
            else:
                self._tap_key('E')  # Fallback for non-mesh contexts
        elif action == 'COPY':
            self._perform_chord(['LEFT_CTRL', 'C'])
        elif action == 'PASTE':
            self._perform_chord(['LEFT_CTRL', 'V'])
        elif action == 'DUPLICATE':
            bpy.ops.object.duplicate_move('INVOKE_DEFAULT')
        elif action == 'CONSTRAINT_X':
            self._tap_key('X')
        elif action == 'CONSTRAINT_Y':
            self._tap_key('Y')
        elif action == 'CONSTRAINT_Z':
            self._tap_key('Z')
        elif action == 'PLANE_X':
            self._perform_chord(['LEFT_SHIFT', 'X'])
        elif action == 'PLANE_Y':
            self._perform_chord(['LEFT_SHIFT', 'Y'])
        elif action == 'PLANE_Z':
            self._perform_chord(['LEFT_SHIFT', 'Z'])
        elif action == 'KEYFRAME_ADD':
            bpy.ops.anim.keyframe_insert_menu('INVOKE_DEFAULT')
        elif action == 'KEYFRAME_REMOVE':
            bpy.ops.anim.keyframe_delete_v3d('INVOKE_DEFAULT')
        elif action == 'MODE_TOGGLE_EDIT':
            bpy.ops.object.mode_set(mode='EDIT', toggle=True)
        elif action == 'SELECT_ALL':
            # Context-aware selection
            if self._context.mode == 'OBJECT':
                bpy.ops.object.select_all(action='SELECT')
            else:
                bpy.ops.mesh.select_all(action='SELECT')
        elif action == 'SELECT_NONE':
            # Context-aware deselection
            if self._context.mode == 'OBJECT':
                bpy.ops.object.select_all(action='DESELECT')
            else:
                bpy.ops.mesh.select_all(action='DESELECT')
        elif action == 'NEXT_FRAME':
            self._frame_offset(1)
        elif action == 'PREV_FRAME':
            self._frame_offset(-1)
        elif action == 'NEXT_KEYFRAME':
            self._keyframe_jump(True)
        elif action == 'PREV_KEYFRAME':
            self._keyframe_jump(False)
        elif action == 'DELETE':
            # Context-aware delete
            if self._context.mode == 'OBJECT':
                bpy.ops.object.delete('INVOKE_DEFAULT')
            elif self._context.mode == 'EDIT_MESH':
                bpy.ops.mesh.delete('INVOKE_DEFAULT', type='VERT')
            else:
                self._tap_key('DEL')  # Fallback for other contexts
        elif action == 'ZERO_KEY':
            self._tap_key('ZERO')
        elif action == 'MOUSE_WHEEL_UP':
            self._mouse_wheel(1)
        elif action == 'MOUSE_WHEEL_DOWN':
            self._mouse_wheel(-1)
        elif action == 'VIEW_LEFT':
            bpy.ops.view3d.view_axis('INVOKE_DEFAULT', type='LEFT', align_active=False)
        elif action == 'VIEW_RIGHT':
            bpy.ops.view3d.view_axis('INVOKE_DEFAULT', type='RIGHT', align_active=False)
        elif action == 'VIEW_TOP':
            bpy.ops.view3d.view_axis('INVOKE_DEFAULT', type='TOP', align_active=False)
        elif action == 'VIEW_BOTTOM':
            bpy.ops.view3d.view_axis('INVOKE_DEFAULT', type='BOTTOM', align_active=False)
        elif action == 'VIEW_FRONT':
            bpy.ops.view3d.view_axis('INVOKE_DEFAULT', type='FRONT', align_active=False)
        elif action == 'VIEW_BACK':
            bpy.ops.view3d.view_axis('INVOKE_DEFAULT', type='BACK', align_active=False)
        elif action == 'VIEW_CAMERA':
            bpy.ops.view3d.view_camera('INVOKE_DEFAULT')
        elif action == 'VIEW_PERSPECTIVE':
            bpy.ops.view3d.view_persportho('INVOKE_DEFAULT')

    def _execute_button_release(self, action):
        if action not in self.HOLDABLE_ACTIONS:
            return
        if action == 'MOUSE_LEFT':
            self._release_mouse_button('LEFTMOUSE')
        elif action == 'MOUSE_RIGHT':
            self._release_mouse_button('RIGHTMOUSE')

    def _process_mode_switch_button(self, action, reader_key, pressed, temp_mode_name=""):
        previous = self.mode_button_state.get(reader_key, False)
        if pressed == previous:
            return
        if pressed:
            self.mode_button_state[reader_key] = True
            if action == 'TEMP_MODE_SHIFT':
                self._activate_temp_mode_shift(reader_key, temp_mode_name)
            else:
                delta = 1 if action == 'NEXT_MODE' else -1
                self._change_mode(delta)
        else:
            self.mode_button_state.pop(reader_key, None)
            # Note: temp mode shift release is handled in apply() before mode processing

    def _process_overlay_button(self, action, reader_key, pressed):
        """Handle overlay toggle and temporary show actions."""
        previous = self.button_state.get(reader_key, False)
        if pressed == previous:
            return
        self.button_state[reader_key] = pressed

        wm = getattr(self._context, "window_manager", None)
        current_visibility = bool(getattr(wm, "cl_show_gamepad_overlay", False)) if wm else False

        if action == 'TOGGLE_OVERLAY':
            if pressed:
                self._set_overlay_visibility(not current_visibility)
        elif action == 'SHOW_OVERLAY':
            if pressed:
                self.show_overlay_button_held = True
                self._set_overlay_visibility(True)
            else:
                if self.show_overlay_button_held:
                    self._set_overlay_visibility(False)
                    self.show_overlay_button_held = False

    def _activate_temp_mode_shift(self, button_name, temp_mode_name=""):
        """Activate temporary mode shift - store current mode and switch to target or next mode."""
        if self.temp_mode_shift_active:
            return
        prefs = get_addon_preferences(self._context)
        if not prefs or not prefs.modes:
            return
        enabled_indices = get_enabled_mode_indices(prefs)
        if len(enabled_indices) < 2:
            return
        
        # Store current mode and physical button
        self.temp_mode_shift_active = True
        self.temp_mode_previous_index = self.mode_index
        self.temp_mode_shift_button = button_name
        
        # Find target mode by name (if specified)
        if temp_mode_name:
            target_index = self._find_mode_index_by_name(temp_mode_name, enabled_indices)
            if target_index is not None and target_index != self.mode_index:
                self.mode_index = target_index
                self._flush_inputs()
                self.last_mode_index = self.mode_index
                prefs.update_mode_statuses(active_index=self.mode_index)
                from . import view3d_gamepad_indicator_op
                view3d_gamepad_indicator_op.redraw_view3d_headers()
                return
        
        # Fallback: switch to next mode
        self._change_mode(1)

    def _find_mode_index_by_name(self, mode_name, enabled_indices=None):
        """Find mode index by name, only considering enabled modes if list provided."""
        prefs = get_addon_preferences(self._context)
        if not prefs or not prefs.modes:
            return None
        
        for i, mode in enumerate(prefs.modes):
            if mode.name == mode_name:
                if enabled_indices is None or i in enabled_indices:
                    return i
        return None

    def _deactivate_temp_mode_shift(self):
        """Deactivate temporary mode shift - return to previous mode."""
        if not self.temp_mode_shift_active:
            return
        self.temp_mode_shift_active = False
        self.temp_mode_shift_button = None
        if self.temp_mode_previous_index is not None:
            prefs = get_addon_preferences(self._context)
            if prefs:
                enabled_indices = get_enabled_mode_indices(prefs)
                if self.temp_mode_previous_index in enabled_indices:
                    self.mode_index = self.temp_mode_previous_index
                    self._flush_inputs()
                    self.last_mode_index = self.mode_index
                    prefs.update_mode_statuses(active_index=self.mode_index)
                    from . import view3d_gamepad_indicator_op
                    view3d_gamepad_indicator_op.redraw_view3d_headers()
            self.temp_mode_previous_index = None

    def _change_mode(self, delta):
        prefs = get_addon_preferences(self._context)
        if not prefs or not prefs.modes:
            return False
        enabled_indices = get_enabled_mode_indices(prefs)
        total = len(enabled_indices)
        if total == 0:
            self._flush_inputs()
            return False
        if self.mode_index not in enabled_indices:
            self.mode_index = enabled_indices[0]
        if total == 1:
            return False
        current_slot = enabled_indices.index(self.mode_index)
        new_slot = (current_slot + delta) % total
        if new_slot == current_slot:
            return False
        self.mode_index = enabled_indices[new_slot]
        self._flush_inputs()
        self.last_mode_index = self.mode_index
        prefs = get_addon_preferences(self._context)
        if prefs:
            prefs.update_mode_statuses(active_index=self.mode_index)
        # Force header redraw to update mode display (lazy import to avoid circular dependency)
        from . import view3d_gamepad_indicator_op
        view3d_gamepad_indicator_op.redraw_view3d_headers()
        return True

    def set_mode(self, context, target_index):
        self._context = context
        prefs = get_addon_preferences(context)
        if not prefs or not prefs.modes:
            return False
        enabled_indices = get_enabled_mode_indices(prefs)
        if target_index not in enabled_indices:
            return False
        if self.mode_index == target_index:
            return False
        self.mode_index = target_index
        self._flush_inputs()
        self.last_mode_index = self.mode_index
        prefs.modes_index = target_index
        prefs.update_mode_statuses(active_index=self.mode_index)
        from . import view3d_gamepad_indicator_op
        view3d_gamepad_indicator_op.redraw_view3d_headers()
        return True

    def _state_key(self, mode, identifier):
        return f"{mode.name}:{identifier}"

    def _update_virtual_cursor(self, dx, dy, cursor_speed, deadzone):
        if not self._window:
            return
        
        self.cursor_owner = 'controller'
        self.cursor_window = self._window
        self._ensure_cursor_defaults()

        # Calculate floating-point movement
        float_dx = dx * cursor_speed * self.CURSOR_SPEED_MULTIPLIER
        float_dy = -dy * cursor_speed * self.CURSOR_SPEED_MULTIPLIER
        
        # Add to accumulated fractional remainder
        self.cursor_fractional_x += float_dx
        self.cursor_fractional_y += float_dy
        
        # Extract integer pixels to send
        delta_x = int(self.cursor_fractional_x)
        delta_y = int(self.cursor_fractional_y)
        
        # Keep the fractional remainder for next frame
        self.cursor_fractional_x -= delta_x
        self.cursor_fractional_y -= delta_y
        
        # Update cursor position with integer delta
        if delta_x != 0 or delta_y != 0:
            self.cursor_position.x = self.cursor_position.x + delta_x 
            self.cursor_position.y = self.cursor_position.y + delta_y 
            self._send_mouse_move(delta_x, delta_y)

    def _ensure_cursor_defaults(self):
        if not self._window:
            return
        if self.cursor_window is not self._window or self.cursor_position is None:
            self.cursor_window = self._window
            self.cursor_position = Vector((self._window.width * 0.5, self._window.height * 0.5))

    def _verify_mouse_button_states(self):
        """Check if any mouse buttons we think are pressed should actually be released."""
        if not self.active_mouse_buttons or not self._reader:
            return
        
        # Check if triggers that map to mouse buttons are still pressed
        triggers_to_check = [
            (self.LEFT_TRIGGER_KEY, 'LEFTMOUSE'),
            (self.RIGHT_TRIGGER_KEY, 'RIGHTMOUSE'),
        ]
        
        for trigger_key, mouse_button in triggers_to_check:
            if mouse_button in self.active_mouse_buttons:
                trigger_value = self._reader.get(trigger_key, 0.0)
                if trigger_value <= 0.45:  # Trigger released
                    self._event_simulate({'type': mouse_button, 'value': 'RELEASE'})
                    self.active_mouse_buttons.discard(mouse_button)

    def _press_mouse_button(self, event_key):
        if event_key in self.active_mouse_buttons:
            return
        self.active_mouse_buttons.add(event_key)
        self._event_simulate({'type': event_key, 'value': 'PRESS'})

    def _release_mouse_button(self, event_key):
        if event_key not in self.active_mouse_buttons:
            return
        self.active_mouse_buttons.discard(event_key)
        self._event_simulate({'type': event_key, 'value': 'RELEASE'})

    def _mouse_wheel(self, direction):
        event_type = 'WHEELUPMOUSE' if direction > 0 else 'WHEELDOWNMOUSE'
        self._event_simulate({'type': event_type, 'value': 'PRESS'})

    def _frame_offset(self, delta):
        if not self._window:
            return
        override = self._window_override()
        self._execute_operator(
            override,
            bpy.ops.screen.frame_offset,
            "Failed to change frame",
            delta=delta,
        )

    def _keyframe_jump(self, next_key):
        override = self._window_override()
        self._execute_operator(
            override,
            bpy.ops.screen.keyframe_jump,
            "Failed to jump keyframe",
            next=next_key,
        )

    def _dolly_view(self, amount, speed):
        if self._rv3d is None:
            return
        direction = self._rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))
        self._rv3d.view_location = self._rv3d.view_location + direction * (amount * speed)

    def _pan_view(self, leftx, lefty, speed):
        if self._rv3d is None:
            return
        offset = Vector((-leftx, lefty, 0.0)) * speed
        self._rv3d.view_location = self._rv3d.view_location + (self._rv3d.view_rotation @ offset)

    def _orbit_view(self, yaw=0.0, pitch=0.0):
        """Orbit camera around view_location (camera moves, keeps looking at same point)."""
        if self._rv3d is None:
            return
        if abs(yaw) > 1e-5:
            self._rv3d.view_rotation = Quaternion((0.0, 0.0, 1.0), yaw) @ self._rv3d.view_rotation
        if abs(pitch) > 1e-5:
            axis = (self._rv3d.view_rotation @ Vector((1.0, 0.0, 0.0))).normalized()
            self._rv3d.view_rotation = Quaternion(axis, pitch) @ self._rv3d.view_rotation

    def _rotate_view(self, yaw=0.0, pitch=0.0):
        """Rotate camera in place (camera stays still, looks in different direction)."""
        if self._rv3d is None:
            return
        # Calculate current camera position
        view_dir = self._rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))
        cam_pos = self._rv3d.view_location - view_dir * self._rv3d.view_distance
        
        # Apply rotation
        if abs(yaw) > 1e-5:
            self._rv3d.view_rotation = Quaternion((0.0, 0.0, 1.0), yaw) @ self._rv3d.view_rotation
        if abs(pitch) > 1e-5:
            axis = (self._rv3d.view_rotation @ Vector((1.0, 0.0, 0.0))).normalized()
            self._rv3d.view_rotation = Quaternion(axis, pitch) @ self._rv3d.view_rotation
        
        # Update view_location to keep camera position fixed
        new_view_dir = self._rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))
        self._rv3d.view_location = cam_pos + new_view_dir * self._rv3d.view_distance

    def _roll_view(self, amount):
        if self._rv3d is None:
            return
        axis = (self._rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))).normalized()
        self._rv3d.view_rotation = Quaternion(axis, amount * self.DEFAULT_ROLL_SPEED) @ self._rv3d.view_rotation

    def _zoom_view(self, amount):
        if self._rv3d is None:
            return
        factor = 1.0 - amount
        self._rv3d.view_distance = max(0.01, self._rv3d.view_distance * factor)

    def _simulate_key_event(self, key, value):
        self._event_simulate({'type': key, 'value': value})

    def _tap_key(self, key):
        self._simulate_key_event(key, 'PRESS')
        self._simulate_key_event(key, 'RELEASE')

    def _perform_chord(self, keys):
        if not keys:
            return
        modifiers = keys[:-1]
        primary = keys[-1]
        for modifier in modifiers:
            self._simulate_key_event(modifier, 'PRESS')
        self._tap_key(primary)
        for modifier in reversed(modifiers):
            self._simulate_key_event(modifier, 'RELEASE')

    def _send_mouse_move(self, dx, dy):
        if dx == 0 and dy == 0:
            return
        event = {'type': 'MOUSEMOVE', 'value': 'NOTHING', 'dx': dx, 'dy': dy}
        self._event_simulate(event)

    def _event_simulate(self, event):
        if self.cursor_position is not None:
            event.setdefault('mouse_x', int(self.cursor_position.x))
            event.setdefault('mouse_y', int(self.cursor_position.y))

        event_type = event.get('type')
        if not event_type:
            return

        if event_type == 'MOUSEMOVE':
            current = (event.get('mouse_x', 0), event.get('mouse_y', 0))
            if self._last_mouse_event is None:
                self._last_mouse_event = current
            else:
                dx = event.get('dx')
                dy = event.get('dy')
                if dx is None or dy is None:
                    dx = current[0] - self._last_mouse_event[0]
                    dy = current[1] - self._last_mouse_event[1]
                    event['dx'] = dx
                    event['dy'] = dy
                self._last_mouse_event = current

        if self.injector.inject(event):
            return

        if not self.event_warning_shown:
            self.event_warning_shown = True
            print("[ControllerActions] Event injection unavailable. Controller button mapping requires Windows SendInput support.")

    def _execute_operator(self, override, operator, error_label, **kwargs):
        if not override or not operator:
            return False
        cleaned_override = {key: value for key, value in override.items() if value is not None}
        if not cleaned_override:
            return False
        temp_override = getattr(bpy.context, "temp_override", None)
        try:
            if callable(temp_override):
                with temp_override(**cleaned_override):
                    operator(**kwargs)
            else:
                operator(cleaned_override, **kwargs)
            return True
        except Exception as exc:
            print(f"[ControllerActions] {error_label}: {exc}")
            return False

    def _window_override(self):
        override = {'window': self._window, 'screen': self._window.screen}
        override['scene'] = getattr(self._context, "scene", None)
        override['view_layer'] = getattr(self._context, "view_layer", None)
        return override

    def _fallback_enabled_index(self, enabled_indices):
        if not enabled_indices:
            return 0
        for index in enabled_indices:
            if index >= self.mode_index:
                return index
        return enabled_indices[0]

    def _clamp(self, value, minimum, maximum):
        return max(min(value, maximum), minimum)

    def _flush_inputs(self):
        window = self._window or self.cursor_window
        if window:
            for mouse_key in list(self.active_mouse_buttons):
                self._event_simulate({'type': mouse_key, 'value': 'RELEASE'})
        self.active_mouse_buttons.clear()
        self.button_state.clear()
        self.axis_state.clear()


    def reset(self, context):
        self._context = context
        self._flush_inputs()
        self.cursor_owner = 'controller'
        self._last_mouse_event = None
        self.mode_index = 0
        self.last_mode_index = None
        self.current_mode_label = ""
        self.mode_button_state.clear()
        self.temp_mode_shift_active = False
        self.temp_mode_previous_index = None
        self.temp_mode_shift_button = None
        self.show_overlay_button_held = False

    def _locate_and_store_view3d(self):
        """Find a VIEW_3D area and set window and rv3d member variables."""
        def try_area(win, area):
            if area.type != 'VIEW_3D':
                return False
            space = area.spaces.active
            if space and space.region_3d:
                self._window = win
                self._rv3d = space.region_3d
                return True
            return False

        # Try current context first
        window = getattr(self._context, "window", None)
        area = getattr(self._context, "area", None)
        if window and area and try_area(window, area):
            return True

        # Try current window's areas
        if window and window.screen:
            for area in window.screen.areas:
                if try_area(window, area):
                    return True

        # Try all windows
        wm = getattr(self._context, "window_manager", None)
        if wm:
            for win in wm.windows:
                if win.screen:
                    for area in win.screen.areas:
                        if try_area(win, area):
                            return True
        
        return False


controller_actions = ControllerActionExecutor()


__all__ = ["ControllerActionExecutor", "controller_actions"]
