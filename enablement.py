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

"""Runtime helpers for enabling and disabling the controller operator."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

from typing import Dict, Optional

import bpy

_PENDING_STATE: Optional[bool] = None
_RETRY_SCHEDULED = False

__all__ = [
    "request_enable_state",
    "is_controller_running",
    "sync_with_preferences",
]


def request_enable_state(enable: bool) -> None:
    """Try to match the controller's running state to *enable*.

    When a suitable 3D View context is not yet available (for example during
    startup), the desired state is stored and retried via a timer until it
    succeeds.
    """    

    if _apply_enable_state(enable):
        print("Controller enablement state applied immediately.")
        _clear_pending()
    else:
        print("Controller enablement state deferred, will retry.")
        _queue_retry(enable)


def is_controller_running() -> bool:
    wm = bpy.context.window_manager
    return getattr(wm, "cl_controller_running", False)


def sync_with_preferences() -> None:
    from . import preferences

    prefs = preferences.get_addon_preferences()
    if not prefs:
        return
    request_enable_state(bool(getattr(prefs, "enable", False)))


def _apply_enable_state(enable: bool) -> bool:
    ctx = bpy.context
    wm = getattr(ctx, "window_manager", None)
    if not wm or not getattr(wm, "windows", None):
        return False

    for window in wm.windows:
        screen = window.screen
        if not screen or getattr(screen, "is_temp_screen", False):
            continue

        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            region = next((r for r in area.regions if r.type == 'WINDOW'), None)
            if not region:
                continue

            scene = window.scene or getattr(ctx, "scene", None)
            running = getattr(wm, "cl_controller_running", False)
            if enable == running:
                print(f"Controller already {'running' if running else 'stopped'} in suitable context.")
                return True

            override = _build_operator_override(ctx, window, screen, area, region, scene, wm)
            if _invoke_controller_operator(override):
                print(f"Controller {'enabled' if enable else 'disabled'} successfully.")
                return True
    return False


def _build_operator_override(
    ctx: bpy.types.Context,
    window: bpy.types.Window,
    screen: bpy.types.Screen,
    area: bpy.types.Area,
    region: bpy.types.Region,
    scene: Optional[bpy.types.Scene],
    wm: bpy.types.WindowManager,
) -> Dict[str, object]:
    view3d_space = next((space for space in area.spaces if space.type == 'VIEW_3D'), None)
    region_data = getattr(view3d_space, "region_3d", None) if view3d_space else None

    ctx_override: Dict[str, object] = {}
    if hasattr(ctx, "copy"):
        try:
            ctx_override.update(ctx.copy())
        except TypeError as e:
            # Context copy may fail in some situations, continue without it
            print(f"Context copy failed: {e}")

    ctx_override.update({
        'window': window,
        'window_manager': wm,
        'screen': screen,
        'workspace': getattr(window, "workspace", None),
        'area': area,
        'region': region,
        'space_data': view3d_space,
        'region_data': region_data,
        'scene': scene,
        'view_layer': getattr(window, "view_layer", None),
    })
    return {key: value for key, value in ctx_override.items() if value is not None}


def _invoke_controller_operator(override: Dict[str, object]) -> bool:
    if 'view_layer' not in override:
        return False

    temp_override = getattr(bpy.context, "temp_override", None)
    ctx_screen = getattr(bpy.context, "screen", None)
    ctx_is_temp = getattr(ctx_screen, "is_temp_screen", False)

    if not callable(temp_override) or ctx_is_temp:
        return False

    override_kwargs = {
        key: override[key]
        for key in (
            'window',
            'screen',
            'workspace',
            'area',
            'region',
            'space_data',
            'region_data',
            'scene',
            'view_layer',
        )
        if key in override
    }

    try:
        with temp_override(**override_kwargs):
            bpy.ops.wm.cl_controller_inputs('INVOKE_DEFAULT')
        return True
    except (TypeError, RuntimeError):
        return False


def _queue_retry(enable: bool) -> None:
    global _PENDING_STATE
    _PENDING_STATE = enable
    _ensure_retry_timer()


def _clear_pending() -> None:
    global _PENDING_STATE
    _PENDING_STATE = None


def _ensure_retry_timer() -> None:
    global _RETRY_SCHEDULED
    if _RETRY_SCHEDULED:
        return

    bpy.app.timers.register(_retry_pending_state, first_interval=0.5)
    _RETRY_SCHEDULED = True


def _retry_pending_state():
    global _PENDING_STATE, _RETRY_SCHEDULED
    if _PENDING_STATE is None:
        _RETRY_SCHEDULED = False
        return None
    if _apply_enable_state(_PENDING_STATE):
        _PENDING_STATE = None
        _RETRY_SCHEDULED = False
        return None
    return 0.5
