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

"""Platform-specific helpers for injecting mouse and keyboard events."""

# pyright: reportInvalidTypeForm=false

import ctypes
import platform


class SystemEventInjector:
    """Inject OS-level mouse/keyboard events without requiring Blender event simulation."""

    def __init__(self):
        self.available = False
        self._vk_map = {}
        self._platform = platform.system()
        if self._platform == "Windows":
            self._init_windows()
        elif self._platform == "Darwin":
            self._init_macos()

    def _init_windows(self):
        try:
            from ctypes import wintypes
        except ImportError:
            return

        try:
            self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        except OSError:
            return

        ULONG_PTR = getattr(wintypes, "ULONG_PTR", None)
        if ULONG_PTR is None:
            if ctypes.sizeof(ctypes.c_void_p) == ctypes.sizeof(ctypes.c_ulonglong):
                ULONG_PTR = ctypes.c_ulonglong
            else:
                ULONG_PTR = ctypes.c_ulong

        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]

        class INPUTUNION(ctypes.Union):
            _fields_ = [
                ("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT),
            ]

        class INPUT(ctypes.Structure):
            _fields_ = [
                ("type", wintypes.DWORD),
                ("union", INPUTUNION),
            ]

        self._MOUSEINPUT = MOUSEINPUT
        self._KEYBDINPUT = KEYBDINPUT
        self._INPUT = INPUT
        self._INPUTUNION = INPUTUNION

        self._INPUT_MOUSE = 0
        self._INPUT_KEYBOARD = 1
        self._MOUSEEVENTF_MOVE = 0x0001
        self._MOUSEEVENTF_LEFTDOWN = 0x0002
        self._MOUSEEVENTF_LEFTUP = 0x0004
        self._MOUSEEVENTF_RIGHTDOWN = 0x0008
        self._MOUSEEVENTF_RIGHTUP = 0x0010
        self._MOUSEEVENTF_WHEEL = 0x0800
        self._KEYEVENTF_KEYUP = 0x0002
        self._WHEEL_DELTA = 120
        self._vk_map = {
            'ZERO': 0x30,
            'LEFT_SHIFT': 0xA0,
            'LEFT_CTRL': 0xA2,
            'LEFT_ALT': 0xA4,
            'DEL': 0x2E,
        }
        self.available = True

    def _init_macos(self):
        # Quartz Event Services via ctypes; works on both Apple Silicon and Intel.
        try:
            self._cg = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
            self._cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        except OSError:
            return

        class CGPoint(ctypes.Structure):
            _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

        self._CGPoint = CGPoint
        cg = self._cg
        cg.CGEventCreate.restype = ctypes.c_void_p
        cg.CGEventCreate.argtypes = [ctypes.c_void_p]
        cg.CGEventGetLocation.restype = CGPoint
        cg.CGEventGetLocation.argtypes = [ctypes.c_void_p]
        cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
        cg.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, CGPoint, ctypes.c_uint32]
        cg.CGEventCreateKeyboardEvent.restype = ctypes.c_void_p
        cg.CGEventCreateKeyboardEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_bool]
        # Non-variadic variant (macOS 10.13+); the variadic one is unsafe through ctypes on arm64.
        cg.CGEventCreateScrollWheelEvent2.restype = ctypes.c_void_p
        cg.CGEventCreateScrollWheelEvent2.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ]
        cg.CGEventSetIntegerValueField.restype = None
        cg.CGEventSetIntegerValueField.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int64]
        cg.CGEventSetFlags.restype = None
        cg.CGEventSetFlags.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        cg.CGEventPost.restype = None
        cg.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        cg.AXIsProcessTrusted.restype = ctypes.c_bool
        cg.AXIsProcessTrusted.argtypes = []
        self._cf.CFRelease.restype = None
        self._cf.CFRelease.argtypes = [ctypes.c_void_p]

        self._kCGHIDEventTap = 0
        self._kCGEventLeftMouseDown = 1
        self._kCGEventLeftMouseUp = 2
        self._kCGEventRightMouseDown = 3
        self._kCGEventRightMouseUp = 4
        self._kCGEventMouseMoved = 5
        self._kCGEventLeftMouseDragged = 6
        self._kCGEventRightMouseDragged = 7
        self._kCGMouseButtonLeft = 0
        self._kCGMouseButtonRight = 1
        self._kCGMouseEventDeltaX = 4
        self._kCGMouseEventDeltaY = 5
        self._kCGScrollEventUnitLine = 1
        self._mac_held_buttons = set()
        self._mac_flags = 0
        self._ax_warning_shown = False
        # Virtual key code -> modifier flag mask (Shift, Control, Option, Command).
        self._mac_modifier_flags = {
            56: 0x00020000,
            59: 0x00040000,
            58: 0x00080000,
            55: 0x00100000,
        }
        # ANSI virtual key codes (Carbon kVK_*). LEFT_CTRL maps to Command because
        # Blender's macOS keymap binds Ctrl shortcuts such as copy/paste to Cmd.
        self._vk_map = {
            'A': 0, 'S': 1, 'D': 2, 'F': 3, 'H': 4, 'G': 5, 'Z': 6, 'X': 7,
            'C': 8, 'V': 9, 'B': 11, 'Q': 12, 'W': 13, 'E': 14, 'R': 15,
            'Y': 16, 'T': 17, 'O': 31, 'U': 32, 'I': 34, 'P': 35, 'L': 37,
            'J': 38, 'K': 40, 'N': 45, 'M': 46,
            '1': 18, '2': 19, '3': 20, '4': 21, '5': 23, '6': 22,
            '7': 26, '8': 28, '9': 25, '0': 29,
            'ZERO': 29, 'ONE': 18, 'TWO': 19, 'THREE': 20, 'FOUR': 21,
            'FIVE': 23, 'SIX': 22, 'SEVEN': 26, 'EIGHT': 28, 'NINE': 25,
            'LEFT_SHIFT': 56,
            'LEFT_CTRL': 55,
            'LEFT_ALT': 58,
            'OSKEY': 55,
            'DEL': 117,
            'BACK_SPACE': 51,
        }
        self.available = True

    def inject(self, event):
        if not self.available:
            return False
        if self._platform == "Darwin":
            return self._inject_macos(event)
        event_type = event.get('type')
        if not event_type:
            return False
        value = event.get('value', 'PRESS')
        if event_type == 'MOUSEMOVE':
            return self._mouse_move(event)
        if event_type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
            return self._mouse_button(event_type, value)
        if event_type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            delta = self._WHEEL_DELTA if event_type == 'WHEELUPMOUSE' else -self._WHEEL_DELTA
            return self._mouse_wheel(delta)
        return self._key_event(event_type, value)

    def _mouse_move(self, event):
        dx = int(event.get('dx', 0))
        dy = int(event.get('dy', 0))
        if dx == 0 and dy == 0:
            return True
        mi = self._MOUSEINPUT(dx, dy, 0, self._MOUSEEVENTF_MOVE, 0, 0)
        return self._send_input(self._INPUT_MOUSE, mi=mi)

    def _mouse_button(self, button, value):
        if button == 'LEFTMOUSE':
            flag = self._MOUSEEVENTF_LEFTDOWN if value == 'PRESS' else self._MOUSEEVENTF_LEFTUP
        else:
            flag = self._MOUSEEVENTF_RIGHTDOWN if value == 'PRESS' else self._MOUSEEVENTF_RIGHTUP
        mi = self._MOUSEINPUT(0, 0, 0, flag, 0, 0)
        return self._send_input(self._INPUT_MOUSE, mi=mi)

    def _mouse_wheel(self, delta):
        mi = self._MOUSEINPUT(0, 0, delta, self._MOUSEEVENTF_WHEEL, 0, 0)
        return self._send_input(self._INPUT_MOUSE, mi=mi)

    def _key_event(self, key, value):
        vk_code = self._vk_from_key(key)
        if vk_code is None:
            return False
        flags = 0 if value != 'RELEASE' else self._KEYEVENTF_KEYUP
        ki = self._KEYBDINPUT(vk_code, 0, flags, 0, 0)
        return self._send_input(self._INPUT_KEYBOARD, ki=ki)

    def _vk_from_key(self, key):
        name = key.upper()
        if name in self._vk_map:
            return self._vk_map[name]
        if len(name) == 1 and (name.isalpha() or name.isdigit()):
            return ord(name)
        return None

    def _send_input(self, input_type, mi=None, ki=None):
        inp = self._INPUT()
        inp.type = input_type
        if input_type == self._INPUT_MOUSE and mi is not None:
            inp.union.mi = mi
        elif input_type == self._INPUT_KEYBOARD and ki is not None:
            inp.union.ki = ki
        else:
            return False
        try:
            sent = self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(self._INPUT))
        except Exception:
            return False
        return sent == 1

    # macOS backend

    def _inject_macos(self, event):
        if not self._cg.AXIsProcessTrusted():
            if not self._ax_warning_shown:
                self._ax_warning_shown = True
                print(
                    "[SystemEventInjector] Blender needs Accessibility permission to send "
                    "mouse/keyboard events. Enable Blender in System Settings > Privacy & "
                    "Security > Accessibility, then restart Blender."
                )
            return False
        event_type = event.get('type')
        value = event.get('value', 'PRESS')
        if event_type == 'MOUSEMOVE':
            return self._mac_mouse_move(int(event.get('dx', 0)), int(event.get('dy', 0)))
        if event_type in {'LEFTMOUSE', 'RIGHTMOUSE'}:
            return self._mac_mouse_button(event_type, value)
        if event_type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return self._mac_mouse_wheel(1 if event_type == 'WHEELUPMOUSE' else -1)
        return self._mac_key_event(event_type, value)

    def _mac_cursor_location(self):
        ref = self._cg.CGEventCreate(None)
        if not ref:
            return self._CGPoint(0.0, 0.0)
        try:
            return self._cg.CGEventGetLocation(ref)
        finally:
            self._cf.CFRelease(ref)

    def _mac_post(self, ref):
        if not ref:
            return False
        try:
            # Apply held modifiers explicitly so chords like Shift+X are seen as such.
            self._cg.CGEventSetFlags(ref, self._mac_flags)
            self._cg.CGEventPost(self._kCGHIDEventTap, ref)
        finally:
            self._cf.CFRelease(ref)
        return True

    def _mac_mouse_move(self, dx, dy):
        if dx == 0 and dy == 0:
            return True
        location = self._mac_cursor_location()
        target = self._CGPoint(location.x + dx, location.y + dy)
        if 'LEFTMOUSE' in self._mac_held_buttons:
            event_kind, button = self._kCGEventLeftMouseDragged, self._kCGMouseButtonLeft
        elif 'RIGHTMOUSE' in self._mac_held_buttons:
            event_kind, button = self._kCGEventRightMouseDragged, self._kCGMouseButtonRight
        else:
            event_kind, button = self._kCGEventMouseMoved, self._kCGMouseButtonLeft
        ref = self._cg.CGEventCreateMouseEvent(None, event_kind, target, button)
        if ref:
            self._cg.CGEventSetIntegerValueField(ref, self._kCGMouseEventDeltaX, dx)
            self._cg.CGEventSetIntegerValueField(ref, self._kCGMouseEventDeltaY, dy)
        return self._mac_post(ref)

    def _mac_mouse_button(self, button, value):
        pressed = value == 'PRESS'
        if button == 'LEFTMOUSE':
            event_kind = self._kCGEventLeftMouseDown if pressed else self._kCGEventLeftMouseUp
            cg_button = self._kCGMouseButtonLeft
        else:
            event_kind = self._kCGEventRightMouseDown if pressed else self._kCGEventRightMouseUp
            cg_button = self._kCGMouseButtonRight
        if pressed:
            self._mac_held_buttons.add(button)
        else:
            self._mac_held_buttons.discard(button)
        ref = self._cg.CGEventCreateMouseEvent(None, event_kind, self._mac_cursor_location(), cg_button)
        return self._mac_post(ref)

    def _mac_mouse_wheel(self, lines):
        ref = self._cg.CGEventCreateScrollWheelEvent2(None, self._kCGScrollEventUnitLine, 1, lines, 0, 0)
        return self._mac_post(ref)

    def _mac_key_event(self, key, value):
        key_code = self._vk_from_key(key)
        if key_code is None:
            return False
        key_down = value != 'RELEASE'
        flag = self._mac_modifier_flags.get(key_code)
        if flag is not None:
            if key_down:
                self._mac_flags |= flag
            else:
                self._mac_flags &= ~flag
        ref = self._cg.CGEventCreateKeyboardEvent(None, key_code, key_down)
        return self._mac_post(ref)


__all__ = ["SystemEventInjector"]
