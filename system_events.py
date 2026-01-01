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

    def inject(self, event):
        if not self.available:
            return False
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


__all__ = ["SystemEventInjector"]
