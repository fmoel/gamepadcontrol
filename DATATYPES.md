# Gamepad Control Data Types

This document describes the JSON file structure used for importing and exporting gamepad modes and settings.

## Schema Version

Current schema version: `1.0`

## File Structure

### Full Export (All Modes and Settings)

```json
{
  "schema_version": "1.0",
  "export_type": "all",
  "settings": {
    "enable": true,
    "modes_index": 0
  },
  "modes": [
    {
      /* GamepadModeSettings */
    }
  ]
}
```

### Single Mode Export

```json
{
  "schema_version": "1.0",
  "export_type": "mode",
  "modes": [
    {
      /* GamepadModeSettings */
    }
  ]
}
```

## Data Types

### Root Object

| Field            | Type                  | Required | Description                                                |
| ---------------- | --------------------- | -------- | ---------------------------------------------------------- |
| `schema_version` | string                | Yes      | Version of the data schema (e.g., "1.0")                   |
| `export_type`    | string                | Yes      | Either `"all"` for full export or `"mode"` for single mode |
| `settings`       | Settings              | No       | Global addon settings (only in full export)                |
| `modes`          | GamepadModeSettings[] | Yes      | Array of gamepad mode configurations                       |

### Settings Object

| Field                          | Type    | Default | Description                                        |
| ------------------------------ | ------- | ------- | -------------------------------------------------- |
| `enable`                       | boolean | `true`  | Whether the gamepad input is enabled               |
| `modes_index`                  | integer | `0`     | Index of the currently active mode                 |
| `show_mode_display_on_startup` | boolean | `true`  | Whether to show the mode display when addon starts |
| `show_info_overlay_on_startup` | boolean | `false` | Whether to show the info overlay when addon starts |

### GamepadModeSettings

Represents a complete gamepad configuration profile.

| Field                     | Type                | Default  | Description                                 |
| ------------------------- | ------------------- | -------- | ------------------------------------------- |
| `name`                    | string              | `"Mode"` | Display name for the mode                   |
| `controller_button_back`  | ButtonAction        | `"NONE"` | Action for the Back/Select button           |
| `controller_button_start` | ButtonAction        | `"NONE"` | Action for the Start/Menu button            |
| `left_side`               | GamepadSideSettings | -        | Configuration for D-Pad, Left Stick, LB, LT |
| `right_side`              | GamepadSideSettings | -        | Configuration for ABXY, Right Stick, RB, RT |

### GamepadSideSettings

Configuration for one side of the controller (left or right). Uses SDL2 button naming.

**Left Side (D-Pad and Left Stick):**

| Field                            | Type                | Default  | Description               |
| -------------------------------- | ------------------- | -------- | ------------------------- |
| `controller_button_dpup`         | ButtonAction        | `"NONE"` | D-Pad Up button           |
| `controller_button_dpdown`       | ButtonAction        | `"NONE"` | D-Pad Down button         |
| `controller_button_dpleft`       | ButtonAction        | `"NONE"` | D-Pad Left button         |
| `controller_button_dpright`      | ButtonAction        | `"NONE"` | D-Pad Right button        |
| `controller_button_leftstick`    | ButtonAction        | `"NONE"` | Left Stick press (L3)     |
| `controller_button_leftshoulder` | ButtonAction        | `"NONE"` | Left Shoulder button (LB) |
| `trigger_action`                 | ButtonAction        | `"NONE"` | Left Trigger (LT)         |
| `axis`                           | GamepadAxisSettings | -        | Left analog stick config  |

**Right Side (ABXY and Right Stick):**

| Field                             | Type                | Default  | Description                |
| --------------------------------- | ------------------- | -------- | -------------------------- |
| `controller_button_a`             | ButtonAction        | `"NONE"` | A button (bottom)          |
| `controller_button_b`             | ButtonAction        | `"NONE"` | B button (right)           |
| `controller_button_x`             | ButtonAction        | `"NONE"` | X button (left)            |
| `controller_button_y`             | ButtonAction        | `"NONE"` | Y button (top)             |
| `controller_button_rightstick`    | ButtonAction        | `"NONE"` | Right Stick press (R3)     |
| `controller_button_rightshoulder` | ButtonAction        | `"NONE"` | Right Shoulder button (RB) |
| `trigger_action`                  | ButtonAction        | `"NONE"` | Right Trigger (RT)         |
| `axis`                            | GamepadAxisSettings | -        | Right analog stick config  |

### GamepadAxisSettings

Configuration for an analog stick.

| Field                   | Type               | Default           | Description                                                     |
| ----------------------- | ------------------ | ----------------- | --------------------------------------------------------------- |
| `stick_mode`            | StickMode          | `"COMBINED"`      | How stick input is interpreted                                  |
| `invert_x`              | boolean            | `false`           | Invert horizontal axis                                          |
| `invert_y`              | boolean            | `true`            | Invert vertical axis                                            |
| `combined_action`       | CombinedAxisAction | `"MOUSE_POINTER"` | Action when stick_mode is COMBINED                              |
| `cursor_speed`          | float              | `0.5`             | Speed multiplier for cursor movement (0.0-1.0, 0.5 recommended) |
| `pan_speed`             | float              | `0.08`            | Speed multiplier for panning (0.01-1.0)                         |
| `dolly_speed`           | float              | `0.2`             | Speed multiplier for dolly/move (0.01-1.0)                      |
| `orbit_speed`           | float              | `0.02`            | Speed multiplier for orbiting (0.005-0.2)                       |
| `rotate_speed`          | float              | `0.02`            | Speed multiplier for rotation (0.005-0.2)                       |
| `axis_x_action`         | SeparateAxisAction | `"PAN_LR"`        | X-axis action when stick_mode is SEPARATE                       |
| `axis_y_action`         | SeparateAxisAction | `"PAN_UD"`        | Y-axis action when stick_mode is SEPARATE                       |
| `axis_deadzone_x`       | float              | `0.1`             | X-axis deadzone threshold (0.0-1.0)                             |
| `axis_deadzone_y`       | float              | `0.1`             | Y-axis deadzone threshold (0.0-1.0)                             |
| `button_deadzone`       | float              | `0.6`             | Threshold for button-mode directions (0.0-1.0)                  |
| `dir_up_action`         | ButtonAction       | `"NONE"`          | Action for up direction (button modes)                          |
| `dir_down_action`       | ButtonAction       | `"NONE"`          | Action for down direction (button modes)                        |
| `dir_left_action`       | ButtonAction       | `"NONE"`          | Action for left direction (button modes)                        |
| `dir_right_action`      | ButtonAction       | `"NONE"`          | Action for right direction (button modes)                       |
| `dir_up_left_action`    | ButtonAction       | `"NONE"`          | Action for up-left diagonal (8-button mode)                     |
| `dir_up_right_action`   | ButtonAction       | `"NONE"`          | Action for up-right diagonal (8-button mode)                    |
| `dir_down_left_action`  | ButtonAction       | `"NONE"`          | Action for down-left diagonal (8-button mode)                   |
| `dir_down_right_action` | ButtonAction       | `"NONE"`          | Action for down-right diagonal (8-button mode)                  |

## Enumerations

### ButtonAction

Actions that can be assigned to buttons.

| Value              | Label                 | Description                                 |
| ------------------ | --------------------- | ------------------------------------------- |
| `NONE`             | None                  | Action disabled                             |
| `VIEW_LEFT`        | Left View             | Switch the viewport to the left view        |
| `VIEW_RIGHT`       | Right View            | Switch the viewport to the right view       |
| `VIEW_TOP`         | Top View              | Switch the viewport to the top view         |
| `VIEW_BOTTOM`      | Bottom View           | Switch the viewport to the bottom view      |
| `VIEW_FRONT`       | Front View            | Switch the viewport to the front view       |
| `VIEW_BACK`        | Rear View             | Switch the viewport to the rear view        |
| `VIEW_CAMERA`      | Camera View           | Switch to the active camera                 |
| `VIEW_PERSPECTIVE` | Toggle Perspective    | Toggle between orthographic and perspective |
| `MOUSE_LEFT`       | Mouse - Left Button   | Emulate the left mouse button               |
| `MOUSE_RIGHT`      | Mouse - Right Button  | Emulate the right mouse button              |
| `PIVOT_PIE`        | Pivot Pie Menu        | Show the Pivot Pie menu                     |
| `ORIENTATION_PIE`  | Orientation Pie Menu  | Show the Orientation Pie menu               |
| `NEXT_MODE`        | Next Gamepad Mode     | Switch to the next controller mode          |
| `PREV_MODE`        | Previous Gamepad Mode | Switch to the previous controller mode      |
| `GRAB`             | Grab (G)              | Trigger the Grab/Move tool                  |
| `ROTATE`           | Rotate (R)            | Trigger the Rotate tool                     |
| `SCALE`            | Scale (S)             | Trigger the Scale tool                      |
| `EXTRUDE`          | Extrude (E)           | Trigger the Extrude tool                    |
| `COPY`             | Copy (Ctrl+C)         | Copy the current selection                  |
| `PASTE`            | Paste (Ctrl+V)        | Paste from the clipboard                    |
| `DUPLICATE`        | Duplicate (Shift+D)   | Duplicate the current selection             |
| `CONSTRAINT_X`     | X Axis Constraint     | Constrain transform to the X axis           |
| `CONSTRAINT_Y`     | Y Axis Constraint     | Constrain transform to the Y axis           |
| `CONSTRAINT_Z`     | Z Axis Constraint     | Constrain transform to the Z axis           |
| `PLANE_X`          | X Plane Constraint    | Constrain transform to the X plane          |
| `PLANE_Y`          | Y Plane Constraint    | Constrain transform to the Y plane          |
| `PLANE_Z`          | Z Plane Constraint    | Constrain transform to the Z plane          |
| `KEYFRAME_ADD`     | Insert Keyframe       | Insert a keyframe                           |
| `KEYFRAME_REMOVE`  | Remove Keyframe       | Remove the active keyframe                  |
| `MODE_TOGGLE_EDIT` | Toggle Edit/Object    | Toggle Edit/Object mode                     |
| `SELECT_ALL`       | Select All            | Select all elements                         |
| `SELECT_NONE`      | Select None           | Deselect all elements                       |
| `NEXT_FRAME`       | Next Frame            | Move to the next frame                      |
| `PREV_FRAME`       | Previous Frame        | Move to the previous frame                  |
| `NEXT_KEYFRAME`    | Next Keyframe         | Jump to the next keyframe                   |
| `PREV_KEYFRAME`    | Previous Keyframe     | Jump to the previous keyframe               |
| `DELETE`           | Delete                | Delete the current selection                |
| `ZERO_KEY`         | Enter 0               | Send the 0 key                              |
| `MOUSE_WHEEL_UP`   | Mouse Wheel Up        | Scroll up                                   |
| `MOUSE_WHEEL_DOWN` | Mouse Wheel Down      | Scroll down                                 |

### StickMode

Defines how the analog stick input is interpreted.

| Value           | Label            | Description                                 |
| --------------- | ---------------- | ------------------------------------------- |
| `COMBINED`      | Combined Axis    | Treat both axes as a single input           |
| `SEPARATE`      | Separate Axis    | Configure each axis individually            |
| `FOUR_BUTTONS`  | As Four Buttons  | Map the stick to up/down/left/right buttons |
| `EIGHT_BUTTONS` | As Eight Buttons | Map the stick to all eight directions       |

### CombinedAxisAction

Actions available when stick_mode is `COMBINED`.

| Value            | Label  | Description                       |
| ---------------- | ------ | --------------------------------- |
| `NONE`           | None   | Disable the combined stick action |
| `MOUSE_POINTER`  | Mouse  | Move the virtual mouse cursor     |
| `PAN_VIEW`       | Pan    | Pan the viewport                  |
| `ROTATE_VIEW`    | Rotate | Orbit the viewport                |
| `ORBIT_SELECTED` | Orbit  | Orbit around the selection        |

### SeparateAxisAction

Actions available when stick_mode is `SEPARATE`.

| Value            | Label            | Description                             |
| ---------------- | ---------------- | --------------------------------------- |
| `NONE`           | None             | Disable the selected axis               |
| `MOVE_VIEW`      | Move             | Dolly the view forward/backward         |
| `PAN_LR`         | Pan Left/Right   | Pan the view horizontally               |
| `PAN_UD`         | Pan Up/Down      | Pan the view vertically                 |
| `ROTATE_LOCAL_X` | Rotate Local X   | Rotate the view around the local X axis |
| `ROTATE_LOCAL_Y` | Rotate Local Y   | Rotate the view around the local Y axis |
| `ORBIT_LR`       | Orbit Left/Right | Orbit around the selection horizontally |
| `ORBIT_UD`       | Orbit Up/Down    | Orbit around the selection vertically   |
| `ZOOM_VIEW`      | Zoom             | Zoom the view in and out                |

## Example Files

### Full Export Example

```json
{
  "schema_version": "1.0",
  "export_type": "all",
  "settings": {
    "enable": true,
    "modes_index": 0,
    "show_mode_display_on_startup": true,
    "show_info_overlay_on_startup": false
  },
  "modes": [
    {
      "name": "Mouse",
      "controller_button_back": "NONE",
      "controller_button_start": "NONE",
      "left_side": {
        "controller_button_dpup": "PREV_KEYFRAME",
        "controller_button_dpdown": "NEXT_KEYFRAME",
        "controller_button_dpleft": "PREV_FRAME",
        "controller_button_dpright": "NEXT_FRAME",
        "controller_button_leftstick": "NONE",
        "controller_button_leftshoulder": "PREV_MODE",
        "trigger_action": "MOUSE_LEFT",
        "axis": {
          "stick_mode": "EIGHT_BUTTONS",
          "invert_x": false,
          "invert_y": true,
          "combined_action": "MOUSE_POINTER",
          "cursor_speed": 0.5,
          "pan_speed": 0.08,
          "dolly_speed": 0.2,
          "orbit_speed": 0.02,
          "rotate_speed": 0.02,
          "axis_x_action": "PAN_LR",
          "axis_y_action": "PAN_UD",
          "axis_deadzone_x": 0.1,
          "axis_deadzone_y": 0.1,
          "button_deadzone": 0.6,
          "dir_up_action": "VIEW_TOP",
          "dir_down_action": "VIEW_BOTTOM",
          "dir_left_action": "VIEW_LEFT",
          "dir_right_action": "VIEW_RIGHT",
          "dir_up_left_action": "VIEW_PERSPECTIVE",
          "dir_up_right_action": "VIEW_TOP",
          "dir_down_left_action": "VIEW_BOTTOM",
          "dir_down_right_action": "VIEW_CAMERA"
        }
      },
      "right_side": {
        "controller_button_y": "NONE",
        "controller_button_a": "PIVOT_PIE",
        "controller_button_x": "MODE_TOGGLE_EDIT",
        "controller_button_b": "ORIENTATION_PIE",
        "controller_button_rightstick": "NONE",
        "controller_button_rightshoulder": "NEXT_MODE",
        "trigger_action": "MOUSE_RIGHT",
        "axis": {
          "stick_mode": "COMBINED",
          "invert_x": false,
          "invert_y": true,
          "combined_action": "MOUSE_POINTER",
          "cursor_speed": 0.5,
          "pan_speed": 0.08,
          "dolly_speed": 0.2,
          "orbit_speed": 0.02,
          "rotate_speed": 0.02,
          "axis_x_action": "PAN_LR",
          "axis_y_action": "PAN_UD",
          "axis_deadzone_x": 0.1,
          "axis_deadzone_y": 0.1,
          "button_deadzone": 0.6,
          "dir_up_action": "NONE",
          "dir_down_action": "NONE",
          "dir_left_action": "NONE",
          "dir_right_action": "NONE",
          "dir_up_left_action": "NONE",
          "dir_up_right_action": "NONE",
          "dir_down_left_action": "NONE",
          "dir_down_right_action": "NONE"
        }
      }
    }
  ]
}
```

### Single Mode Export Example

```json
{
  "schema_version": "1.0",
  "export_type": "mode",
  "modes": [
    {
      "name": "Custom Mode",
      "controller_button_back": "PIVOT_PIE",
      "controller_button_start": "ORIENTATION_PIE",
      "left_side": {
        "controller_button_dpup": "VIEW_TOP",
        "controller_button_dpdown": "VIEW_BOTTOM",
        "controller_button_dpleft": "VIEW_LEFT",
        "controller_button_dpright": "VIEW_RIGHT",
        "controller_button_leftstick": "NONE",
        "controller_button_leftshoulder": "PREV_MODE",
        "trigger_action": "MOUSE_LEFT",
        "axis": {
          "stick_mode": "COMBINED",
          "invert_x": false,
          "invert_y": true,
          "combined_action": "PAN_VIEW",
          "cursor_speed": 0.5,
          "pan_speed": 0.1,
          "dolly_speed": 0.2,
          "orbit_speed": 0.02,
          "rotate_speed": 0.02,
          "axis_x_action": "PAN_LR",
          "axis_y_action": "PAN_UD",
          "axis_deadzone_x": 0.1,
          "axis_deadzone_y": 0.1,
          "button_deadzone": 0.6,
          "dir_up_action": "NONE",
          "dir_down_action": "NONE",
          "dir_left_action": "NONE",
          "dir_right_action": "NONE",
          "dir_up_left_action": "NONE",
          "dir_up_right_action": "NONE",
          "dir_down_left_action": "NONE",
          "dir_down_right_action": "NONE"
        }
      },
      "right_side": {
        "controller_button_y": "SCALE",
        "controller_button_a": "GRAB",
        "controller_button_x": "EXTRUDE",
        "controller_button_b": "ROTATE",
        "controller_button_rightstick": "NONE",
        "controller_button_rightshoulder": "NEXT_MODE",
        "trigger_action": "MOUSE_RIGHT",
        "axis": {
          "stick_mode": "COMBINED",
          "invert_x": false,
          "invert_y": true,
          "combined_action": "MOUSE_POINTER",
          "cursor_speed": 0.5,
          "pan_speed": 0.08,
          "dolly_speed": 0.2,
          "orbit_speed": 0.02,
          "rotate_speed": 0.02,
          "axis_x_action": "PAN_LR",
          "axis_y_action": "PAN_UD",
          "axis_deadzone_x": 0.1,
          "axis_deadzone_y": 0.1,
          "button_deadzone": 0.6,
          "dir_up_action": "NONE",
          "dir_down_action": "NONE",
          "dir_left_action": "NONE",
          "dir_right_action": "NONE",
          "dir_up_left_action": "NONE",
          "dir_up_right_action": "NONE",
          "dir_down_left_action": "NONE",
          "dir_down_right_action": "NONE"
        }
      }
    }
  ]
}
```

## Compatibility Notes

- Files exported from newer versions may contain additional fields that older versions will ignore
- The `schema_version` field allows for future format changes while maintaining backward compatibility
- Unknown action values will default to `"NONE"`
- Missing optional fields will use their default values
