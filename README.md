# Gamepad Controller

_for Blender_

**Gamepad Controller** is a Blender add-on that lets you use a game controller or gamepad to navigate and control the 3D viewport in real-time. It provides intuitive camera controls, view manipulation, and customizable gamepad modes that make working in Blender more comfortable and efficient.

## Features

- Real-time gamepad input for 3D viewport navigation
- Customizable gamepad modes with different control schemes
- Visual overlay showing current controller mappings in the viewport
- Header indicator for active gamepad mode
- Multiple control modes: orbit, pan, dolly, and direct view switching
- Configurable button and axis mappings
- Export/import settings for sharing configurations
- Custom icon support for better visual feedback

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

1. Go to **Edit > Preferences > Add-ons** and find **Gamepad Controller**
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

## Project Inspired By

BCL - Blender Controller Link  
[https://github.com/globglob3D/Blender_Controller_Link](https://github.com/globglob3D/Blender_Controller_Link)

## Requirements

- Blender 5.0 or newer
- Game controller/gamepad (PlayStation, Xbox, or compatible)

## Known Issues

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
