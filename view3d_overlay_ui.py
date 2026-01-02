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

"""GPU-based gamepad overlay rendering in View3D."""

# pyright: reportInvalidTypeForm=false

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from .controller_actions import get_controller_actions
from .preferences import (
    format_action_label,
    format_combined_axis_label,
    format_separate_axis_label,
    get_addon_preferences,
    get_enabled_mode_indices,
)

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
OVERLAY_IMAGE_PATH = os.path.join(ASSETS_DIR, "Controller outline mask.png")
ICONS_MAP_PATH = os.path.join(ASSETS_DIR, "icons.png")

# Icon map configuration (8x8 grid of 16x16 icons)
ICON_MAP_GRID_SIZE = 8
ICON_SIZE = 16

# Icon indices in the sprite sheet (0-63 for 8x8 grid)
# Mapping direction names to icon positions
ICON_INDICES = {
    "left": 0,
    "up_left": 1,
    "up": 2,
    "up_right": 3,
    "right": 4,
    "down_right": 5,
    "down": 6,
    "down_left": 7,
    "combined": 8,
    "left_right": 9,
    "up_down": 10,
    "gamepad": 16,  # Example positions - adjust based on your actual icon map
}

# Unicode arrow characters for direction indicators (fallback)
ARROW_CHARS = {
    # Cardinal directions
    "left": "←",
    "up": "↑",
    "right": "→",
    "down": "↓",
    # Diagonal directions
    "up_left": "↖",
    "up_right": "↗",
    "down_right": "↘",
    "down_left": "↙",
    # Axis modes
    "left_right": "↔",
    "up_down": "↕",
    "combined": "✛",
}

STICK_DIRECTION_ORDER = [
    "left",
    "up_left",
    "up",
    "up_right",
    "down_right",
    "right",
    "down",
    "down_left",
]

STICK_SIDES = ["LEFT", "RIGHT"]  # Controller stick sides

# Colors
TEXT_COLOR = (0.9, 0.97, 1.0, 1.0)
MODE_COLOR = (0.95, 0.95, 0.95, 1.0)
COLUMN_HEADER_COLOR = (0.8, 0.9, 1.0, 1.0)
BACKGROUND_COLOR = (0.02, 0.02, 0.02, 0.50)
CALLOUT_LINE_COLOR = (0.2, 0.6, 0.9, 0.9)

# Layout dimensions
OVERLAY_WIDTH = 420
OVERLAY_HEIGHT = 250
OVERLAY_MARGIN = 20
TEXT_LINE_HEIGHT = 12
LABEL_MARGIN = 110
LINE_TEXT_MARGIN = 3
MAX_ACTION_LENGTH = 25
STICK_BRANCH_LENGTH = 4

# Anchor points for callout lines (normalized 0-1 coordinates on controller image)
OUTLINES = {
    "L2": ("LEFT", (0.20, 0.93), (0.13, 1.00), (0.00, 1.00)),
    "L1": ("LEFT", (0.18, 0.82), (0.11, 0.89), (0.00, 0.89)),
    "SHARE": ("LEFT", (0.27, 0.64), (0.13, 0.78), (0.00, 0.78)),
    "DPAD_UP": ("LEFT", (0.20, 0.52), (0.12, 0.67), (0.00, 0.67)),
    "DPAD_LEFT": ("LEFT", (0.16, 0.46), (0.08, 0.54), (0.00, 0.54)),
    "DPAD_DOWN": ("LEFT", (0.20, 0.40), (0.03, 0.40), (0.00, 0.43)),
    "DPAD_RIGHT": ("LEFT", (0.24, 0.46), (0.22, 0.32), (0.00, 0.32)),
    "L3": ("LEFT", (0.34, 0.25), (0.30, 0.21), (0.00, 0.21)),
    "LEFT_STICK": ("LEFT", (0.34, 0.20), (0.16, 0.03), (0.16, -0.11)),
    "R2": ("RIGHT", (0.80, 0.93), (0.87, 1.00), (1.00, 1.00)),
    "R1": ("RIGHT", (0.82, 0.82), (0.89, 0.89), (1.00, 0.89)),
    "OPTIONS": ("RIGHT", (0.74, 0.64), (0.86, 0.78), (1.00, 0.78)),
    "Y": ("RIGHT", (0.84, 0.58), (0.93, 0.67), (1.00, 0.67)),
    "X": ("RIGHT", (0.77, 0.48), (0.88, 0.54), (1.00, 0.54)),
    "B": ("RIGHT", (0.91, 0.48), (0.96, 0.43), (1.00, 0.43)),
    "A": ("RIGHT", (0.84, 0.39), (0.91, 0.32), (1.00, 0.32)),
    "R3": ("RIGHT", (0.68, 0.25), (0.72, 0.21), (1.00, 0.21)),
    "RIGHT_STICK": ("RIGHT", (0.66, 0.20), (0.84, 0.03), (0.84, -0.11)),
}


@dataclass
class StickDisplay:
    """Display configuration for a stick (analog or button mode)."""
    mode: str
    lines: List[str]
    directions: Dict[str, Tuple[str, str]]
    include_diagonals: bool


@dataclass
class GamepadLayoutSnapshot:
    """Complete snapshot of gamepad configuration for display."""
    mode_name: str
    controls: Dict[str, str]
    sticks: Dict[str, StickDisplay]


def _build_control_labels(mode) -> Dict[str, str]:
    """Build labels for all button controls."""
    left = mode.left_side
    right = mode.right_side
    return {
        "L2": format_action_label(left.trigger_action),
        "L1": format_action_label(left.controller_button_leftshoulder),
        "L3": format_action_label(left.controller_button_leftstick),
        "R2": format_action_label(right.trigger_action),
        "R1": format_action_label(right.controller_button_rightshoulder),
        "R3": format_action_label(right.controller_button_rightstick),
        "SHARE": format_action_label(mode.controller_button_back),
        "OPTIONS": format_action_label(mode.controller_button_start),
        "DPAD_UP": format_action_label(left.controller_button_dpup),
        "DPAD_DOWN": format_action_label(left.controller_button_dpdown),
        "DPAD_LEFT": format_action_label(left.controller_button_dpleft),
        "DPAD_RIGHT": format_action_label(left.controller_button_dpright),
        "Y": format_action_label(right.controller_button_y),
        "B": format_action_label(right.controller_button_b),
        "A": format_action_label(right.controller_button_a),
        "X": format_action_label(right.controller_button_x),
    }


def _describe_stick(axis_settings) -> StickDisplay:
    """Build display configuration for a stick based on its settings."""
    if not axis_settings:
        return StickDisplay("COMBINED", ["Disabled"], {}, False)
    
    mode = axis_settings.stick_mode
    if mode == 'COMBINED':
        lines = [f"Combined: {format_combined_axis_label(axis_settings.combined_action)}"]
        return StickDisplay(mode, lines, {}, False)
    
    if mode == 'SEPARATE':
        lines = [
            f"Horizontal: {format_separate_axis_label(axis_settings.axis_x_action)}",
            f"Vertical: {format_separate_axis_label(axis_settings.axis_y_action)}",
        ]
        return StickDisplay(mode, lines, {}, False)
    
    include_diagonals = mode == 'EIGHT_BUTTONS'
    dir_map = {
        "up": ("Up", format_action_label(axis_settings.dir_up_action)),
        "down": ("Down", format_action_label(axis_settings.dir_down_action)),
        "left": ("Left", format_action_label(axis_settings.dir_left_action)),
        "right": ("Right", format_action_label(axis_settings.dir_right_action)),
    }
    if include_diagonals:
        dir_map.update({
            "up_left": ("Up-Left", format_action_label(axis_settings.dir_up_left_action)),
            "up_right": ("Up-Right", format_action_label(axis_settings.dir_up_right_action)),
            "down_left": ("Down-Left", format_action_label(axis_settings.dir_down_left_action)),
            "down_right": ("Down-Right", format_action_label(axis_settings.dir_down_right_action)),
        })
    return StickDisplay(mode, [], dir_map, include_diagonals)


def build_gamepad_snapshot(context) -> Optional[GamepadLayoutSnapshot]:
    """Build a complete snapshot of the current gamepad configuration."""
    prefs = get_addon_preferences(context)
    if not prefs or not prefs.modes:
        return None
    
    mode_index = prefs.modes_index
    enabled_indices = get_enabled_mode_indices(prefs)
    wm = getattr(context, "window_manager", None)
    
    if wm and getattr(wm, "cl_controller_running", False):
        if enabled_indices:
            runtime_index = get_controller_actions().mode_index
            if runtime_index not in enabled_indices:
                runtime_index = enabled_indices[0]
            mode_index = runtime_index
        else:
            mode_index = prefs.modes_index
    
    mode_index = max(0, min(mode_index, len(prefs.modes) - 1))
    mode = prefs.modes[mode_index]
    controls = _build_control_labels(mode)
    sticks = {
        "LEFT": _describe_stick(mode.left_side.axis),
        "RIGHT": _describe_stick(mode.right_side.axis),
    }
    return GamepadLayoutSnapshot(mode.name, controls, sticks)


class GamepadOverlayRenderer:
    """Handles GPU-based rendering of gamepad overlay in View3D."""

    def __init__(self):
        self._handler = None
        self._image = None
        self._texture = None
        self._line_shader = None
        self._image_shader = None
        self._icons_image = None
        self._icons_texture = None

    def _ensure_shaders(self):
        """Lazily initialize shaders when GPU context is available."""
        if self._line_shader is None:
            self._line_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        if self._image_shader is None:
            # Use built-in IMAGE shader which supports alpha blending
            self._image_shader = gpu.shader.from_builtin('IMAGE')
            # Note: The IMAGE shader expects textures with proper alpha channel

    def enable(self):
        """Enable overlay rendering."""
        if self._handler:
            return
        self._handler = bpy.types.SpaceView3D.draw_handler_add(
            self._draw, (), 'WINDOW', 'POST_PIXEL'
        )

    def disable(self):
        """Disable overlay rendering."""
        if not self._handler:
            return
        bpy.types.SpaceView3D.draw_handler_remove(self._handler, 'WINDOW')
        self._handler = None

    def _ensure_image(self):
        """Load controller image if needed."""
        if self._image and self._image.filepath == OVERLAY_IMAGE_PATH:
            return self._image
        if not os.path.exists(OVERLAY_IMAGE_PATH):
            return None
        try:
            self._image = bpy.data.images.load(OVERLAY_IMAGE_PATH, check_existing=True)
            # Ensure alpha channel is enabled when supported
            if hasattr(self._image, "alpha_mode"):
                self._image.alpha_mode = 'STRAIGHT'
            if hasattr(self._image, "use_alpha"):
                self._image.use_alpha = True
        except RuntimeError:
            self._image = None
        return self._image

    def _ensure_texture(self):
        """Create GPU texture from image."""
        image = self._ensure_image()
        if not image:
            return None
        if self._texture and self._texture.width == image.size[0] and self._texture.height == image.size[1]:
            return self._texture
        self._texture = gpu.texture.from_image(image)
        return self._texture

    def _ensure_icons(self):
        """Load icon map image if needed."""
        if self._icons_image and self._icons_image.filepath == ICONS_MAP_PATH:
            return self._icons_image
        if not os.path.exists(ICONS_MAP_PATH):
            return None
        try:
            self._icons_image = bpy.data.images.load(ICONS_MAP_PATH, check_existing=True)
        except RuntimeError:
            self._icons_image = None
        return self._icons_image

    def _ensure_icons_texture(self):
        """Create GPU texture from icon map."""
        image = self._ensure_icons()
        if not image:
            return None
        if self._icons_texture:
            return self._icons_texture
        self._icons_texture = gpu.texture.from_image(image)
        return self._icons_texture

    def _draw_icon(self, x: float, y: float, icon_key: str, size: float = 12):
        """Draw an icon from the sprite sheet at the given position."""
        if icon_key not in ICON_INDICES:
            return False
        
        texture = self._ensure_icons_texture()
        if not texture:
            return False
        
        icon_index = ICON_INDICES[icon_key]
        grid_x = icon_index % ICON_MAP_GRID_SIZE
        grid_y = icon_index // ICON_MAP_GRID_SIZE
        
        # UV coordinates for the icon in the sprite sheet
        u_step = 1.0 / ICON_MAP_GRID_SIZE
        v_step = 1.0 / ICON_MAP_GRID_SIZE
        
        u0 = grid_x * u_step
        v0 = 1.0 - (grid_y + 1) * v_step  # Flip V coordinate
        u1 = u0 + u_step
        v1 = v0 + v_step
        
        # Screen coordinates
        x0, y0 = x, y
        x1, y1 = x + size, y + size
        
        # Create batch with UV coordinates
        coords = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
        uvs = ((u0, v0), (u1, v0), (u1, v1), (u0, v1))
        indices = ((0, 1, 2), (0, 2, 3))
        
        shader = self._image_shader
        batch = batch_for_shader(
            shader, 'TRIS',
            {"pos": coords, "texCoord": uvs},
            indices=indices
        )
        
        shader.bind()
        shader.uniform_sampler("image", texture)
        batch.draw(shader)
        
        return True

    def _draw(self):
        """Main drawing callback."""
        context = bpy.context
        region = getattr(context, "region", None)
        if not region:
            return
        
        snapshot = build_gamepad_snapshot(context)
        if not snapshot:
            return
        
        self._ensure_shaders()
        origin = (region.width - OVERLAY_WIDTH - OVERLAY_MARGIN, OVERLAY_MARGIN)
        
        gpu.state.blend_set('ALPHA')
        self._draw_background(origin)
        self._draw_image_centered(origin)
        self._draw_mode_label(origin, snapshot.mode_name)
        self._draw_callout_labels(origin, snapshot.controls, snapshot.sticks)
        gpu.state.blend_set('NONE')

    def _draw_background(self, origin):
        """Draw overlay background."""
        x, y = origin
        coords = (
            (x, y),
            (x + OVERLAY_WIDTH, y),
            (x + OVERLAY_WIDTH, y + OVERLAY_HEIGHT),
            (x, y + OVERLAY_HEIGHT),
        )
        batch = batch_for_shader(self._line_shader, 'TRI_FAN', {"pos": coords})
        self._line_shader.bind()
        self._line_shader.uniform_float("color", BACKGROUND_COLOR)
        batch.draw(self._line_shader)

    def _draw_image_centered(self, origin):
        """Draw controller image centered with proper scaling."""
        texture = self._ensure_texture()
        if not texture:
            return
        
        img_width = OVERLAY_WIDTH - (LABEL_MARGIN * 2)
        img_height = OVERLAY_HEIGHT
        
        aspect = 2.0
        if img_width / aspect > img_height:
            img_width = img_height * aspect
        else:
            img_height = img_width / aspect
        
        x = origin[0] + (OVERLAY_WIDTH - img_width) * 0.5
        y = origin[1] + 30 + (OVERLAY_HEIGHT - img_height) * 0.5
        
        self._img_rect = (x, y, img_width, img_height)
        
        coords = (
            (x, y),
            (x + img_width, y),
            (x + img_width, y + img_height),
            (x, y + img_height),
        )
        tex_coords = ((0, 0), (1, 0), (1, 1), (0, 1))
        batch = batch_for_shader(
            self._image_shader,
            'TRI_FAN',
            {"pos": coords, "texCoord": tex_coords},
        )
        self._image_shader.bind()
        self._image_shader.uniform_sampler("image", texture)
        batch.draw(self._image_shader)

    def _draw_mode_label(self, origin, mode_name: str):
        """Draw mode label at top of overlay."""
        font_id = 0
        blf.color(font_id, *MODE_COLOR)
        blf.size(font_id, 10)
        
        x = origin[0] + LINE_TEXT_MARGIN + 5
        y = origin[1] + LINE_TEXT_MARGIN + 20
        
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, "Mode")
        
        blf.size(font_id, 12)
        blf.color(font_id, *COLUMN_HEADER_COLOR)
        blf.position(font_id, x, y - 14, 0)
        blf.draw(font_id, mode_name)

    def _get_anchor_screen_pos(self, origin, anchor: Tuple[float, float]) -> Tuple[float, float]:
        """Convert normalized anchor position to screen coordinates."""
        if not hasattr(self, '_img_rect'):
            return (origin[0], origin[1])
        img_x, img_y, img_w, img_h = self._img_rect
        return (img_x + anchor[0] * img_w, img_y + anchor[1] * img_h)

    def _draw_callout_line(self, points: List[Tuple[float, float]]):
        """Draw callout polyline through given points."""
        if len(points) < 2:
            return
        for i in range(len(points) - 1):
            coords = [points[i], points[i + 1]]
            batch = batch_for_shader(self._line_shader, 'LINES', {"pos": coords})
            self._line_shader.bind()
            self._line_shader.uniform_float("color", CALLOUT_LINE_COLOR)
            gpu.state.line_width_set(1.0)
            batch.draw(self._line_shader)

    def _draw_arrow(self, x: float, y: float, arrow_key: str, font_id: int = 0):
        """Draw direction indicator - tries icon first, falls back to Unicode arrow."""
        # Try to draw icon from sprite sheet
        if self._draw_icon(x, y, arrow_key, size=12):
            return
        
        # Fallback to Unicode arrow character
        if arrow_key not in ARROW_CHARS:
            return
        arrow = ARROW_CHARS[arrow_key]
        blf.position(font_id, x, y, 0)
        blf.draw(font_id, arrow)

    def _draw_callout_labels(self, origin, controls: Dict[str, str], sticks: Dict[str, StickDisplay]):
        """Draw all callout labels for buttons and sticks."""
        font_id = 0
        blf.size(font_id, 9)
        
        # Draw button controls
        for control_id, action in controls.items():
            if control_id not in OUTLINES:
                continue
            
            outline_side, anchor, mid_point, end_point = OUTLINES[control_id]
            
            if len(action) > MAX_ACTION_LENGTH:
                action = action[:MAX_ACTION_LENGTH - 2] + ".."
            
            p1 = self._get_anchor_screen_pos(origin, anchor)
            p2 = self._get_anchor_screen_pos(origin, mid_point)
            p3 = self._get_anchor_screen_pos(origin, end_point)
            
            self._draw_callout_line([p1, p2, p3])
            
            blf.color(font_id, *TEXT_COLOR)
            text_width, text_height = blf.dimensions(font_id, action)
            
            if outline_side == "LEFT":
                text_x = p3[0] - text_width - LINE_TEXT_MARGIN
            elif outline_side == "RIGHT":
                text_x = p3[0] + LINE_TEXT_MARGIN
            else:
                text_x = p3[0] - text_width * 0.5
            
            text_y = p3[1] - text_height * 0.4
            blf.position(font_id, text_x, text_y, 0)
            blf.draw(font_id, action)
        
        # Draw stick info
        for side in STICK_SIDES:
            stick_key = f"{side}_STICK"
            if stick_key not in OUTLINES:
                continue
            
            stick = sticks.get(side)
            if not stick:
                continue
            
            outline_side, anchor, mid_point, end_point = OUTLINES[stick_key]
            p1 = self._get_anchor_screen_pos(origin, anchor)
            p2 = self._get_anchor_screen_pos(origin, mid_point)
            p3 = self._get_anchor_screen_pos(origin, end_point)
            
            self._draw_stick_info(p1, p2, p3, stick)

    def _draw_stick_info(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                         p3: Tuple[float, float], stick: StickDisplay):
        """Draw stick information with arrow indicators."""
        font_id = 0
        blf.size(font_id, 9)
        blf.color(font_id, *TEXT_COLOR)
        
        line_height = TEXT_LINE_HEIGHT
        arrow_width = 12
        
        items = []
        
        if stick.mode == 'COMBINED':
            action = stick.lines[0] if stick.lines else "-"
            action = action.removeprefix("Combined: ")
            if len(action) > MAX_ACTION_LENGTH:
                action = action[:MAX_ACTION_LENGTH - 2] + ".."
            items.append(("combined", action))
        elif stick.mode == 'SEPARATE':
            for arrow_key, line in [("left_right", stick.lines[0] if len(stick.lines) > 0 else ""),
                                    ("up_down", stick.lines[1] if len(stick.lines) > 1 else "")]:
                action = line.split(": ", 1)[1] if ": " in line else line
                if len(action) > MAX_ACTION_LENGTH:
                    action = action[:MAX_ACTION_LENGTH - 2] + ".."
                items.append((arrow_key, action))
        else:
            for dir_key in STICK_DIRECTION_ORDER:
                if dir_key not in stick.directions:
                    continue
                label, action = stick.directions[dir_key]
                if len(action) > MAX_ACTION_LENGTH:
                    action = action[:MAX_ACTION_LENGTH - 2] + ".."
                items.append((dir_key, action))
        
        if not items:
            self._draw_callout_line([p1, p2, p3])
            return
        
        start_y = p3[1]
        num_items = len(items)
        last_item_y = start_y - (num_items - 1) * line_height
        last_item_center_y = last_item_y + line_height * 0.5
        
        if num_items > 1:
            p3_extended = (p3[0], last_item_center_y)
            self._draw_callout_line([p1, p2, p3, p3_extended])
        else:
            self._draw_callout_line([p1, p2, p3])
        
        for idx, (arrow_key, action) in enumerate(items):
            row_y = start_y - idx * line_height
            row_center_y = row_y + line_height * 0.5
            text_width, text_height = blf.dimensions(font_id, action)
            
            branch_start = (p3[0], row_center_y)
            branch_end = (p3[0] + STICK_BRANCH_LENGTH, row_center_y)
            arrow_x = branch_end[0] + LINE_TEXT_MARGIN
            text_x = arrow_x + arrow_width + LINE_TEXT_MARGIN
            
            self._draw_callout_line([branch_start, branch_end])
            
            arrow_y = row_y + (line_height - text_height) * 0.5
            blf.color(font_id, *CALLOUT_LINE_COLOR)
            self._draw_arrow(arrow_x, arrow_y, arrow_key, font_id)
            
            blf.color(font_id, *TEXT_COLOR)
            text_y = row_y + (line_height - text_height) * 0.5
            blf.position(font_id, text_x, text_y, 0)
            blf.draw(font_id, action)


overlay_renderer = GamepadOverlayRenderer()


def sync_overlay_state(_self=None, context=None):
    """Sync overlay renderer state with user preferences."""
    if context is None:
        context = bpy.context
    if not context:
        return
    wm = context.window_manager
    if getattr(wm, "cl_show_gamepad_overlay", False):
        overlay_renderer.enable()
    else:
        overlay_renderer.disable()


def unregister_overlay():
    """Disable overlay rendering on unregister."""
    overlay_renderer.disable()


__all__ = [
    "build_gamepad_snapshot",
    "sync_overlay_state",
    "unregister_overlay",
]
