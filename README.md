# Gamepad Control

_for Blender_

**Gamepad Control** is a Blender add-on that lets you use a game controller or gamepad to navigate and control the 3D viewport in real-time. It provides intuitive camera controls, view manipulation, and customizable gamepad modes that make working in Blender more comfortable and efficient.

![Gamepad overlay in the View3D](assets/Screenshot%20overlay.png)

## Features

- Real-time gamepad input for 3D viewport navigation
- Customizable gamepad modes with different control schemes
- Visual overlay showing current controller mappings in the viewport
- Header indicator for active gamepad mode
- Multiple control modes: orbit, pan, dolly, and direct view switching
- Configurable button and axis mappings
- Export/import settings for sharing configurations
- Custom icon support for better visual feedback

![Status indicator at the top of the View3D](assets/Screenshot%20status%20indicator.png)

![Preferences for the gamepad control add-on](assets/Screenshot%20Preferences.png)

Configuration can be done in Preferences -> Input -> Gamepad

Tested currently on Windows-x64 with a PS5 controller

## Installation

1. Download the ZIP of this repository.
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click **Install...** and select the ZIP file.
4. Enable **Gamepad Controller** in the list.

## Usage

### Basic Setup

1. Connect your gamepad/controller to your computer
2. In the 3D Viewport header, you'll see a gamepad icon when the addon is active
3. Click the icon to access mode controls and settings
4. Enable "Show Overlay" to see current controller mappings in the viewport

### Configuration

1. Go to **Edit > Preferences > Input** and find **Gamepad**
2. Expand the addon preferences to configure:
   - Gamepad modes (create multiple control schemes)
   - Button and axis mappings
   - Sensitivity settings
   - Display preferences
3. Export your settings to share with others or back up your configuration

### View Menu

Access gamepad controls from the **View** menu in the 3D viewport:

- Toggle Gamepad Overlay
- Toggle Mode Indicator

## Extension Inspired By

BCL - Blender Controller Link  
[https://github.com/globglob3D/Blender_Controller_Link](https://github.com/globglob3D/Blender_Controller_Link)

## Requirements

- Blender 5.0 or newer
- Game controller/gamepad (PlayStation, Xbox, or compatible)

## Known Issues

### Analog LT / RT navigation

In Preferences > Input > Gamepad, expand a mode and set each trigger's
Mode to **Analog**. Select **Zoom**, Move (dolly), horizontal/vertical Pan,
local Rotate, or horizontal/vertical Orbit. Button mode remains the default
and preserves existing mappings, including mouse wheel emulation.

For Xbox zoom, set both triggers to Analog / Zoom, enable **Invert** on LT,
and leave it disabled on RT. LT zooms out and RT zooms in. Start with
Sensitivity **0.35** and Dead Zone **0.05** on both; adjust to taste.
Pressure above the dead zone is rescaled continuously to the full range.
Sensitivity is independent of stick speeds. Invert reverses the direction
for every analog action. Both triggers work independently and may have
different actions. Equal opposing zoom pressure cancels away from the
minimum view distance.

Analog actions only change RegionView3D navigation state and do not send
mouse wheel, mouse button, or transform events. Starting analog navigation
in camera view leaves camera view for perspective, including when Lock
Camera to View is enabled, so the scene camera is not moved. Trigger
settings are included in the existing JSON import/export system and the
overlay shows the analog action and direction.

Regression tests use actual Blender RNA and viewport data. With the bundled
SDL dependencies installed, run:

```sh
blender --background --factory-startup --python-exit-code 1 --python tests/test_analog_triggers.py
```

These automated tests do not replace physical controller acceptance tests.

### World-plane stick movement and analog world Z

For ground-plane navigation, set a stick to **Combined Axis / Move in World
Horizontal Plane**. Right/left moves sideways and up/down moves forward/backward
in world XY relative to the view heading. View pitch does not turn this into
vertical movement. A vertical view remains usable: heading comes from the view's
right vector projected onto XY, with a forward-vector fallback when right is
vertical. World Z stays unchanged. Screen-plane **Pan** remains a separate action.

Configure **World Move Speed** (units/second), **World Move Sensitivity**, X/Y
dead zones and X/Y inversion. Each dead zone rescales the remaining axis travel;
diagonal input is capped at the same maximum speed as straight movement.
Separate Axis mode also offers world-plane left/right and forward/back actions.

**Viewport Move Up** and **Viewport Move Down** are available for analog triggers
as well as buttons. Select Analog and the desired action for LT/RT; pressure,
trigger sensitivity, dead zone and inversion control movement along world Z.
Analog trigger Z uses the mode's **Viewport Vertical Speed**, shared with the
held button actions. Invert reverses the chosen action, so disable it when
assigning Down if you want that trigger to move downward. Existing Zoom trigger
assignments and all previous stick modes retain their behavior. These options
are saved by the existing JSON import/export system.

### Hold buttons to move along world Z

Assign **Viewport Move Up** and **Viewport Move Down** to any button (for example
RB and LB). The view moves along world +Z or -Z for as long as the button is held
and stops on release. **Viewport Vertical Speed**, configured per mode, is in
Blender units per second. Both buttons together cancel. Stick navigation and
analog triggers continue to work at the same time. Only the viewport location
changes; camera view is exited before moving, and scene objects are untouched.

### Window Control Freeze (Currently Unresolvable)

When using mouse button actions mapped to gamepad triggers (e.g., left trigger for LEFTMOUSE), clicking on Blender's window controls (titlebar, minimize, maximize, close) or dragging the window may cause the interface to freeze.

**What happens:**

- Blender's script execution completely stops when window chrome is interacted with
- If a trigger is released during this freeze, the mouse button release event is never sent
- The window remains "grabbed" by the cursor until you physically click and release the mouse button

**Workaround:**

- Click and release the physical left mouse button to reset the state
- Avoid dragging the window using gamepad mouse button while trigger is pressed

**Why this can't be fixed:**
This is a fundamental limitation of how Blender halts Python script execution during window system interactions. The addon cannot detect or respond to input events while execution is frozen.

## Changelog

### Version 0.1.0 (Beta)

- Initial release
- Multiple gamepad mode support
- Customizable button and axis mappings
- Visual overlay with controller layout
- Header mode indicator with custom icon
- Export/import configuration system
- View menu integration
- Real-time 3D viewport control (orbit, pan, dolly, zoom)
- Direct view switching (top, bottom, front, back, left, right, camera, perspective)
