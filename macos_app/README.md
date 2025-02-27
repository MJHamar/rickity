# Rickity Timer - macOS App

A native macOS app for the Rickity Timer functionality that provides a floating, transparent window which stays on top of other windows and avoids the cursor when not in focus.

## Features

- List all available timers from the backend
- Create new timers with customizable names and durations
- Open timers in floating, transparent windows
- Floating windows stay on top of other applications
- Windows snap to screen corners
- Windows avoid the cursor when not in focus
- Real-time timer updates via WebSockets
- Full timer controls (start, pause, resume, stop)
- Visual feedback for timer status
- Proper error handling and reconnection logic

## Requirements

- macOS 10.13 or later
- Python 3.6 or later
- PyQt6
- websocket-client
- requests

## Installation

1. Make sure you have Python 3.6+ installed
2. Clone the repository
3. Navigate to the `macos_app` directory
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the App

1. Make sure the Rickity Timer backend server is running
2. Run the app using:
   ```
   python run.py
   ```
   
3. The launcher will check for dependencies and install them if necessary

## Using the App

1. **Main Window**:
   - Displays all available timers
   - Create new timers using the "New Timer" button
   - Open a timer by clicking the "Open" button on a timer card
   - Delete timers with the "Delete" button

2. **Floating Timer Window**:
   - Displays the current timer status and time remaining
   - Control buttons for starting, pausing, and resetting the timer
   - Can be dragged to any position on screen and will snap to the nearest corner
   - Automatically avoids the cursor when not in focus
   - Always stays on top of other windows
   - Close with the "Close" button

## Configuration

You can modify the app's behavior by editing the `src/config.py` file:

- `API_URL`: The URL of the Rickity Timer backend API
- `WINDOW_WIDTH`, `WINDOW_HEIGHT`: Size of the main window
- `FLOATING_WINDOW_SIZE`: Size of the floating timer windows
- `CORNER_MARGIN`: Distance from screen corners for snapping
- `TRANSPARENCY`: Opacity of floating windows (0.0 to 1.0)
- `AVOID_CURSOR_DISTANCE`: Distance to trigger cursor avoidance

## Troubleshooting

- If the app fails to connect to the backend, ensure the API server is running and the URL in `config.py` is correct
- For WebSocket connection issues, check if the server supports WebSockets and the URL format is correct
- If the app doesn't start, make sure all dependencies are installed properly

## Development

- The app is built with PyQt6 for native macOS integration
- WebSocket client for real-time updates from the backend
- Code is organized in a modular pattern for easy maintenance
- Follows macOS design guidelines for a native look and feel 