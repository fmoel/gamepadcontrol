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

"""Gamepad Control for Blender - Add-on initialization."""

# pyright: reportInvalidTypeForm=false

import os
import bpy
import bpy.utils.previews
from bpy.app.handlers import persistent
from . import main
from . import preferences
from . import preferences_ui
from . import enablement
from . import io_operations
from . import view3d_overlay_ui
from . import view3d_overlay_op
from . import view3d_gamepad_indicator_ui
from . import view3d_gamepad_indicator_op
from . import view_menu_entries

# Global store for custom icons
icon_collections = {}

classes = (
    preferences.PREFERENCE_CLASSES
    + preferences_ui.PREFERENCE_UI_CLASSES
    + view3d_overlay_op.GAMEPAD_OVERLAY_OPERATOR_CLASSES
    + view3d_gamepad_indicator_op.GAMEPAD_INDICATOR_OPERATOR_CLASSES
    + view3d_gamepad_indicator_ui.GAMEPAD_INDICATOR_UI_CLASSES
    + io_operations.IO_CLASSES
    + (
        main.CL_OT_ControllerInputs,
    )
)


def _safe_register_class(cls):
    try:
        bpy.utils.register_class(cls)
    except ValueError:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
        bpy.utils.register_class(cls)


def _safe_unregister_class(cls):
    try:
        bpy.utils.unregister_class(cls)
    except RuntimeError:
        pass


@persistent
def _cl_sync_controller_handler(_=None):
    enablement.sync_with_preferences()
    prefs = preferences.get_addon_preferences()
    if prefs:
        prefs.apply_display_preferences()
        prefs.update_mode_statuses()

def register_icons():
    """Register custom icons for the addon."""
    global icon_collections
    pcoll = bpy.utils.previews.new()
    
    icons_dir = os.path.join(os.path.dirname(__file__), "assets")
    
    # Load single gamepad icon for header
    icon_path = os.path.join(icons_dir, "icon.png")
    if os.path.exists(icon_path):
        pcoll.load("gamepad", icon_path, 'IMAGE')
    
    # Load icon map (8x8 grid of 16x16 icons)
    icons_map_path = os.path.join(icons_dir, "icons.png")
    if os.path.exists(icons_map_path):
        # Load the full image - individual icons will be accessed via coordinates
        # This allows overlay to use sprite sheet rendering
        # Store the path for the overlay to load directly
        pcoll.icons_map_path = icons_map_path
    
    icon_collections["main"] = pcoll

def unregister_icons():
    """Unregister custom icons."""
    global icon_collections
    for pcoll in icon_collections.values():
        bpy.utils.previews.remove(pcoll)
    icon_collections.clear()

def register():
    register_icons()
    
    for cls in classes:
        _safe_register_class(cls)

    io_operations.register_io_properties()

    bpy.types.WindowManager.cl_show_gamepad_overlay = bpy.props.BoolProperty(
        name="Show Gamepad Overlay",
        description="Render the controller info graphic in the 3D View",
        default=False,
        update=view3d_overlay_ui.sync_overlay_state,
    )

    bpy.types.WindowManager.cl_show_mode_display = bpy.props.BoolProperty(
        name="Show Mode Indicator",
        description="Show the current gamepad mode indicator in the 3D View header",
        default=True,
        update=lambda self, context: view3d_gamepad_indicator_op.redraw_view3d_headers(),
    )

    bpy.types.WindowManager.cl_controller_running = bpy.props.BoolProperty(default=False)
    
    # Reset controller running state on reload to ensure clean state
    wm = bpy.context.window_manager
    if wm:
        wm.cl_controller_running = False

    view3d_gamepad_indicator_ui.register_gamepad_indicator_ui()
    view_menu_entries.register_view_menu_entries()

    prefs = preferences.get_addon_preferences()
    if prefs:
        prefs.ensure_default_modes()
        prefs.apply_display_preferences()
        prefs.update_mode_statuses()
        enablement.sync_with_preferences()

    if _cl_sync_controller_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_cl_sync_controller_handler)

def unregister():
    view_menu_entries.unregister_view_menu_entries()
    view3d_gamepad_indicator_ui.unregister_gamepad_indicator_ui()
    view3d_overlay_ui.unregister_overlay()

    io_operations.unregister_io_properties()

    if _cl_sync_controller_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_cl_sync_controller_handler)

    if hasattr(bpy.types.WindowManager, "cl_show_gamepad_overlay"):
        del bpy.types.WindowManager.cl_show_gamepad_overlay

    if hasattr(bpy.types.WindowManager, "cl_show_mode_display"):
        del bpy.types.WindowManager.cl_show_mode_display

    if hasattr(bpy.types.WindowManager, "cl_controller_running"):
        del bpy.types.WindowManager.cl_controller_running

    for cls in reversed(classes):
        _safe_unregister_class(cls)
    
    unregister_icons()
