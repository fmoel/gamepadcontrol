"""Run in Blender: blender --background --factory-startup --python tests/test_analog_triggers.py.

Requires the bundled SDL wheels to be installed or on PYTHONPATH.
Uses actual Blender RNA and RegionView3D; no physical controller is simulated as hardware evidence.
"""
import importlib
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import bpy
from mathutils import Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
# Optional path for an isolated local test environment, outside the add-on.
if (ROOT.parent / 'deps').exists():
    sys.path.insert(0, str(ROOT.parent / 'deps'))
addon = importlib.import_module(ROOT.name)
prefs = importlib.import_module(ROOT.name + '.preferences')
actions = importlib.import_module(ROOT.name + '.controller_actions')
io = importlib.import_module(ROOT.name + '.io_operations')
sdl = importlib.import_module(ROOT.name + '.sdl_handler')
import sdl2


class AnalogTriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for c in prefs.PREFERENCE_CLASSES:
            bpy.utils.register_class(c)
        bpy.types.WindowManager.test_gamepad_modes = bpy.props.CollectionProperty(type=prefs.GamepadModeSettings)

    @classmethod
    def tearDownClass(cls):
        del bpy.types.WindowManager.test_gamepad_modes
        for c in reversed(prefs.PREFERENCE_CLASSES):
            bpy.utils.unregister_class(c)

    def setUp(self):
        modes = bpy.context.window_manager.test_gamepad_modes
        modes.clear()
        self.mode = modes.add()
        self.mode.name = 'Test'
        self.side = self.mode.left_side
        self.side.trigger_mode = 'ANALOG'
        self.side.trigger_deadzone = 0.05
        self.executor = actions.ControllerActionExecutor()
        self.area = next(a for a in bpy.context.screen.areas if a.type == 'VIEW_3D')
        self.rv = self.area.spaces.active.region_3d
        self.rv.view_perspective = 'PERSP'
        self.rv.view_distance = 10.0
        self.snapshot = {o.name: tuple(tuple(row) for row in o.matrix_world) for o in bpy.data.objects}

    def tearDown(self):
        self.assertEqual(self.snapshot, {o.name: tuple(tuple(row) for row in o.matrix_world) for o in bpy.data.objects})

    def press(self, pressure, side=None, key=None):
        side = side or self.side
        key = key or self.executor.LEFT_TRIGGER_KEY
        self.executor._reader = {key: pressure}
        self.executor._process_trigger(key, self.mode, side.trigger_action, side)

    def test_deadzone_release_and_clamping(self):
        for p in (-1.0, 0.0, 0.04, 0.05, float('nan')):
            self.press(p)
            self.assertEqual(self.rv.view_distance, 10.0)
        self.press(2.0)
        self.assertAlmostEqual(self.rv.view_distance, 10 * math.exp(-0.05), places=5)
        stopped = self.rv.view_distance
        self.press(0.0)
        self.assertEqual(self.rv.view_distance, stopped)

    def test_pressure_is_continuous_and_hold_repeats(self):
        self.press(0.525)  # Half of the usable travel after deadzone.
        self.assertAlmostEqual(self.rv.view_distance, 10 * math.exp(-0.025), places=5)
        self.press(0.525)
        self.assertAlmostEqual(self.rv.view_distance, 10 * math.exp(-0.05), places=5)
        self.press(1.0)
        self.assertAlmostEqual(self.rv.view_distance, 10 * math.exp(-0.10), places=5)

    def test_sensitivity_invert_and_simultaneous_triggers(self):
        self.side.trigger_sensitivity = 2.0
        self.press(1.0)
        self.assertAlmostEqual(self.rv.view_distance, 10 * math.exp(-0.10), places=5)
        self.side.trigger_invert = True
        self.press(1.0)
        self.assertAlmostEqual(self.rv.view_distance, 10.0, places=5)
        right = self.mode.right_side
        right.trigger_mode = 'ANALOG'
        self.side.trigger_sensitivity = 1.0
        self.press(0.525)
        self.press(0.525, right, self.executor.RIGHT_TRIGGER_KEY)
        self.assertAlmostEqual(self.rv.view_distance, 10.0, places=5)

    def test_poll_rate_independence(self):
        results = []
        for rate in (30, 60, 120):
            self.rv.view_distance = 10.0
            self.executor._analog_frame_scale = 60.0 / rate
            for _ in range(rate):
                self.press(0.525)
            results.append(self.rv.view_distance)
        for result in results:
            self.assertAlmostEqual(result, 10 * math.exp(-1.5), places=5)

    def test_all_navigation_actions_and_camera_lock(self):
        self.area.spaces.active.lock_camera = True
        for action, *_ in prefs.SEPARATE_AXIS_ACTION_ITEMS:
            self.side.trigger_axis_action = action
            self.rv.view_perspective = 'CAMERA'
            with patch.object(self.executor, '_event_simulate', side_effect=AssertionError('OS event')):
                self.press(1.0)
            self.assertEqual(self.rv.view_perspective, 'CAMERA' if action == 'NONE' else 'PERSP')
        self.area.spaces.active.lock_camera = False

    def test_each_supported_action_dispatches_proportional_value(self):
        for action, *_ in prefs.SEPARATE_AXIS_ACTION_ITEMS:
            if action in {'NONE', 'ZOOM_VIEW'} | self.executor.WORLD_AXIS_ACTIONS:
                continue
            self.side.trigger_axis_action = action
            with patch.object(self.executor, '_execute_separate_axis_action') as call:
                self.press(0.525)
                call.assert_called_once()
                self.assertEqual(call.call_args.args[1], action)
                self.assertAlmostEqual(call.call_args.args[2], 0.5, places=6)

    def test_missing_viewport_and_zero_sensitivity(self):
        with patch.object(self.executor, '_find_view3d_area', return_value=(None, None)):
            self.press(1.0)
        self.side.trigger_sensitivity = 0.0
        self.press(1.0)
        self.assertEqual(self.rv.view_distance, 10.0)

    def test_legacy_button_edges_and_switch_to_analog(self):
        self.side.trigger_mode = 'BUTTON'
        self.side.trigger_action = 'MOUSE_LEFT'
        with patch.object(self.executor, '_execute_button_press') as down, patch.object(self.executor, '_execute_button_release') as up:
            for p in (0.2, 0.5, 1.0, 0.0):
                self.press(p)
            down.assert_called_once_with('MOUSE_LEFT')
            up.assert_called_once_with('MOUSE_LEFT')
            self.press(1.0)
            self.side.trigger_mode = 'ANALOG'
            self.press(1.0)
            self.assertEqual(up.call_count, 2)

    def test_serialization_roundtrip_and_old_settings(self):
        self.side.trigger_axis_action = 'PAN_LR'
        self.side.trigger_sensitivity = 2.5
        self.side.trigger_deadzone = 0.2
        self.side.trigger_invert = True
        data = io.side_settings_to_dict(self.side)
        io.dict_to_side_settings(data, self.mode.right_side)
        self.assertEqual(data, io.side_settings_to_dict(self.mode.right_side))
        legacy = bpy.context.window_manager.test_gamepad_modes.add().left_side
        io.dict_to_side_settings({'trigger_action': 'MOUSE_WHEEL_UP'}, legacy)
        self.assertEqual(legacy.trigger_mode, 'BUTTON')
        self.assertEqual(legacy.trigger_action, 'MOUSE_WHEEL_UP')

    def test_elapsed_time_clamped_and_reset(self):
        with patch.object(actions, 'get_addon_preferences', return_value=None), patch.object(actions.time, 'monotonic', side_effect=[1.0, 1.02, 5.0]):
            self.executor.apply(bpy.context, {})
            self.assertAlmostEqual(self.executor._analog_frame_scale, 1.0)
            self.executor.apply(bpy.context, {})
            self.assertAlmostEqual(self.executor._analog_frame_scale, 1.2)
            self.executor.apply(bpy.context, {})
            self.assertAlmostEqual(self.executor._analog_frame_scale, 6.0)
        self.executor.reset()
        self.assertIsNone(self.executor._analog_last_time)

    def test_sdl_poll_preserves_trigger_pressure(self):
        class Reader(dict):
            location = (0, 0, 0)
        reader = Reader(keep=True)
        handler = object.__new__(sdl.SDL2_Controller_Handler)
        handler.controller, handler.joystick = object(), None
        for raw in (0, 8192, 16384, 32767):
            with patch.object(handler, '_discover_devices'), patch.object(sdl, 'get_reader', return_value=reader), patch.object(sdl2, 'SDL_PumpEvents'), patch.object(sdl2, 'SDL_GameControllerHasAxis', return_value=True), patch.object(sdl2, 'SDL_GameControllerGetAxis', return_value=raw), patch.object(sdl2, 'SDL_GameControllerHasButton', return_value=False):
                handler.poll(None)
            self.assertAlmostEqual(reader[self.executor.LEFT_TRIGGER_KEY], raw / 32767.0)
            self.assertAlmostEqual(reader[self.executor.RIGHT_TRIGGER_KEY], raw / 32767.0)

    def held_button(self, action, pressed=True):
        key = 'controller_button_rightshoulder'
        self.executor._reader = {key: pressed}
        self.executor._process_button_action(key, self.mode, action)

    def test_world_z_hold_release_speed_and_camera_lock(self):
        self.rv.view_location = Vector((1, 2, 3))
        self.rv.view_rotation = Quaternion((1, 0, 0), 1.2)
        rotation = self.rv.view_rotation.copy()
        self.area.spaces.active.lock_camera = True
        self.rv.view_perspective = 'CAMERA'
        self.mode.viewport_move_speed = 3.0
        for _ in range(60):
            self.held_button('VIEWPORT_MOVE_UP')
        self.assertAlmostEqual(self.rv.view_location.z, 6.0, places=4)
        self.assertEqual(tuple(self.rv.view_location)[:2], (1.0, 2.0))
        self.assertEqual(self.rv.view_rotation, rotation)
        self.assertEqual(self.rv.view_perspective, 'PERSP')
        location = self.rv.view_location.copy()
        for _ in range(10):
            self.held_button('VIEWPORT_MOVE_UP', False)
        self.assertEqual(self.rv.view_location, location)
        self.held_button('VIEWPORT_MOVE_DOWN')
        self.assertAlmostEqual(self.rv.view_location.z, 5.95, places=4)
        self.area.spaces.active.lock_camera = False

    def test_world_z_poll_rates_and_opposing_buttons(self):
        self.mode.viewport_move_speed = 2.0
        for rate in (30, 60, 120):
            self.rv.view_location = Vector((0, 0, 0))
            self.executor._analog_frame_scale = 60 / rate
            for _ in range(rate):
                self.held_button('VIEWPORT_MOVE_UP')
            self.assertAlmostEqual(self.rv.view_location.z, 2.0, places=4)
        self.rv.view_location = Vector((0, 0, 0))
        for _ in range(120):
            self.held_button('VIEWPORT_MOVE_UP')
            self.held_button('VIEWPORT_MOVE_DOWN')
        self.assertAlmostEqual(self.rv.view_location.z, 0.0, places=6)

    def test_world_z_with_stick_pan_and_analog_zoom(self):
        side = self.mode.right_side
        side.controller_button_rightshoulder = 'VIEWPORT_MOVE_UP'
        side.trigger_mode = 'ANALOG'
        side.axis.stick_mode = 'COMBINED'
        side.axis.combined_action = 'PAN_VIEW'
        side.axis.invert_y = False
        self.rv.view_location = Vector((0, 0, 0))
        self.rv.view_rotation = Quaternion((1, 0, 0), 1.2)
        expected = self.rv.view_rotation @ (Vector((-.5, .4, 0)) * side.axis.pan_speed)
        expected.z += self.mode.viewport_move_speed / 60
        self.executor._reader = {
            'controller_button_rightshoulder': True,
            self.executor.RIGHT_TRIGGER_KEY: .525,
            'controller_axis_rightx': .5,
            'controller_axis_righty': .4,
        }
        with patch.object(self.executor, '_event_simulate', side_effect=AssertionError('OS event')):
            self.executor._process_side(self.mode, side, self.executor.RIGHT_BUTTONS,
                                        self.executor.RIGHT_AXIS_KEYS, self.executor.RIGHT_TRIGGER_KEY)
        self.assertLess((self.rv.view_location - expected).length, 1e-6)
        self.assertLess(self.rv.view_distance, 10.0)

    def test_world_z_settings_roundtrip_and_legacy_default(self):
        self.mode.viewport_move_speed = 4.0
        self.mode.left_side.controller_button_leftshoulder = 'VIEWPORT_MOVE_DOWN'
        self.mode.right_side.controller_button_rightshoulder = 'VIEWPORT_MOVE_UP'
        data = io.mode_to_dict(self.mode)
        other = bpy.context.window_manager.test_gamepad_modes.add()
        io.dict_to_mode(data, other)
        self.assertEqual(other.viewport_move_speed, 4.0)
        self.assertEqual(other.right_side.controller_button_rightshoulder, 'VIEWPORT_MOVE_UP')
        io.dict_to_mode({'name': 'Legacy'}, other)
        self.assertEqual(other.viewport_move_speed, 2.0)

    def test_world_z_zero_speed_and_missing_viewport(self):
        before = self.rv.view_location.copy()
        self.mode.viewport_move_speed = 0
        self.held_button('VIEWPORT_MOVE_UP')
        self.assertEqual(self.rv.view_location, before)
        self.mode.viewport_move_speed = 2
        with patch.object(self.executor, '_find_view3d_area', return_value=(None, None)):
            self.held_button('VIEWPORT_MOVE_UP')
        self.assertEqual(self.rv.view_location, before)

    def world_stick(self, x, y):
        self.executor._reader = dict(zip(self.executor.LEFT_AXIS_KEYS, (x, y)))
        self.executor._process_axes(self.executor.LEFT_AXIS_KEYS, self.mode, self.side.axis)

    def test_world_plane_is_horizontal_at_all_pitches_and_headings(self):
        axis = self.side.axis
        axis.combined_action = 'MOVE_WORLD_PLANE'
        for yaw in (0.0, .7, 2.4):
            expected_right = Vector((math.cos(yaw), math.sin(yaw), 0))
            expected_forward = Vector((-math.sin(yaw), math.cos(yaw), 0))
            for pitch in (-math.pi/2, 0, .7, math.pi/2, 2.8):
                self.rv.view_rotation = Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), pitch)
                for raw, expected in (((1, 0), expected_right), ((0, -1), expected_forward)):
                    self.rv.view_location = Vector((0, 0, 7))
                    self.world_stick(*raw)
                    delta = self.rv.view_location - Vector((0, 0, 7))
                    self.assertLess((delta - expected * (2 / 60)).length, 1e-6)
                    self.assertEqual(self.rv.view_location.z, 7)

    def test_world_plane_deadzone_sensitivity_inversion_and_diagonal(self):
        axis = self.side.axis
        axis.combined_action = 'MOVE_WORLD_PLANE'
        self.rv.view_rotation = Quaternion((1, 0, 0), 1.0)
        self.rv.view_location = Vector((0, 0, 7))
        self.world_stick(.05, -.05)
        self.assertEqual(tuple(self.rv.view_location), (0, 0, 7))
        self.world_stick(.55, 0)
        self.assertAlmostEqual(self.rv.view_location.x, 1 / 60, places=6)
        axis.world_move_sensitivity = 2
        axis.invert_x = True
        self.world_stick(.55, 0)
        self.assertAlmostEqual(self.rv.view_location.x, -1 / 60, places=6)
        axis.world_move_sensitivity = 1
        axis.invert_x = False
        before = self.rv.view_location.copy()
        self.world_stick(1, -1)
        self.assertAlmostEqual((self.rv.view_location - before).length, 2 / 60, places=6)
        axis.axis_deadzone_x = axis.axis_deadzone_y = 1
        before = self.rv.view_location.copy()
        self.world_stick(1, -1)
        self.assertEqual(self.rv.view_location, before)

    def test_world_plane_roll_fallback_camera_lock_and_missing_viewport(self):
        self.rv.view_rotation = Quaternion((0, 1, 0), math.pi / 2)
        self.rv.view_location = Vector((0, 0, 7))
        self.rv.view_perspective = 'CAMERA'
        self.area.spaces.active.lock_camera = True
        self.side.axis.combined_action = 'MOVE_WORLD_PLANE'
        self.world_stick(1, 0)
        self.assertAlmostEqual(self.rv.view_location.y, 2 / 60, places=6)
        self.assertEqual(self.rv.view_location.z, 7)
        self.assertEqual(self.rv.view_perspective, 'PERSP')
        before = self.rv.view_location.copy()
        with patch.object(self.executor, '_find_view3d_area', return_value=(None, None)):
            self.world_stick(1, 0)
        self.assertEqual(self.rv.view_location, before)
        self.area.spaces.active.lock_camera = False

    def test_world_plane_and_analog_z_are_rate_independent(self):
        self.side.axis.combined_action = 'MOVE_WORLD_PLANE'
        self.side.trigger_axis_action = 'VIEWPORT_MOVE_UP'
        self.mode.viewport_move_speed = 3
        self.rv.view_rotation = Quaternion((1, 0, 0), .7)
        for rate in (30, 60, 120):
            self.rv.view_location = Vector((0, 0, 0))
            self.executor._analog_frame_scale = 60 / rate
            for _ in range(rate):
                self.world_stick(0, -1)
                self.press(.525)
            self.assertAlmostEqual(self.rv.view_location.y, 2.0, places=4)
            self.assertAlmostEqual(self.rv.view_location.z, 1.5, places=4)

    def test_analog_z_pressure_direction_invert_and_release(self):
        self.rv.view_location = Vector((1, 2, 3))
        self.side.trigger_axis_action = 'VIEWPORT_MOVE_UP'
        self.side.trigger_sensitivity = 2
        self.mode.viewport_move_speed = 3
        self.press(.525)
        self.assertAlmostEqual(self.rv.view_location.z, 3.05, places=5)
        self.press(1)
        self.assertAlmostEqual(self.rv.view_location.z, 3.15, places=5)
        self.press(.04)
        self.assertAlmostEqual(self.rv.view_location.z, 3.15, places=5)
        self.side.trigger_invert = True
        self.press(.525)
        self.assertAlmostEqual(self.rv.view_location.z, 3.10, places=5)
        self.side.trigger_invert = False
        self.side.trigger_axis_action = 'VIEWPORT_MOVE_DOWN'
        self.press(.525)
        self.assertAlmostEqual(self.rv.view_location.z, 3.05, places=5)
        self.assertEqual(tuple(self.rv.view_location)[:2], (1, 2))

    def test_separate_world_axes_and_world_actions_on_triggers(self):
        axis = self.side.axis
        axis.stick_mode = 'SEPARATE'
        axis.axis_x_action = 'MOVE_WORLD_LR'
        axis.axis_y_action = 'VIEWPORT_MOVE_UP'
        self.rv.view_rotation = Quaternion((1, 0, 0), .7)
        self.rv.view_location = Vector((0, 0, 0))
        self.world_stick(.55, -.55)
        self.assertAlmostEqual(self.rv.view_location.x, 1 / 60, places=6)
        self.assertAlmostEqual(self.rv.view_location.z, 1 / 60, places=6)
        self.side.trigger_axis_action = 'MOVE_WORLD_FB'
        self.press(.525)
        self.assertAlmostEqual(self.rv.view_location.y, 1 / 60, places=6)

    def test_world_settings_roundtrip_preserves_old_mappings_and_enum_ids(self):
        axis = self.side.axis
        axis.combined_action = 'MOVE_WORLD_PLANE'
        axis.world_move_speed = 3.5
        axis.world_move_sensitivity = .7
        axis.invert_x = True
        axis.axis_deadzone_x = .2
        self.side.trigger_axis_action = 'VIEWPORT_MOVE_DOWN'
        data = io.side_settings_to_dict(self.side)
        io.dict_to_side_settings(data, self.mode.right_side)
        self.assertEqual(data, io.side_settings_to_dict(self.mode.right_side))
        legacy = bpy.context.window_manager.test_gamepad_modes.add().left_side
        io.dict_to_side_settings({'axis': {'combined_action': 'PAN_VIEW', 'pan_speed': .2},
                                 'trigger_action': 'MOUSE_LEFT'}, legacy)
        self.assertEqual(legacy.axis.combined_action, 'PAN_VIEW')
        self.assertAlmostEqual(legacy.axis.pan_speed, .2)
        self.assertEqual(legacy.trigger_mode, 'BUTTON')
        self.assertEqual([item[3] for item in prefs.COMBINED_AXIS_ACTION_ITEMS[:5]], list(range(5)))
        self.assertEqual([item[3] for item in prefs.SEPARATE_AXIS_ACTION_ITEMS[:9]], list(range(9)))

    def test_legacy_screen_pan_remains_distinct(self):
        axis = self.side.axis
        self.rv.view_rotation = Quaternion((1, 0, 0), math.pi / 2)
        self.rv.view_location = Vector((0, 0, 7))
        axis.combined_action = 'PAN_VIEW'
        self.world_stick(0, -1)
        self.assertGreater(self.rv.view_location.z, 7)
        before_z = self.rv.view_location.z
        axis.combined_action = 'MOVE_WORLD_PLANE'
        self.world_stick(0, -1)
        self.assertEqual(self.rv.view_location.z, before_z)


if __name__ == '__main__':
    print('Runtime:', bpy.app.version_string, sys.platform)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AnalogTriggerTests))
    if not result.wasSuccessful():
        raise SystemExit(1)
