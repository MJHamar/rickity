import json
import threading
import time
import requests
import websocket
from PyQt6.QtCore import QObject, pyqtSignal

from config import API_URL, WS_URL


class TimerApiClient(QObject):
    """Client for interacting with the Timer API."""
    
    # Signal emitted when timer state updates
    timer_state_updated = pyqtSignal(dict)
    
    # Signal emitted when connection status changes
    connection_status_changed = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.ws = None
        self.ws_thread = None
        self.is_connected = False
        self.current_timer_id = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 3  # seconds
        self.stop_reconnecting = False

    def get_all_timers(self):
        """Fetch all timers from the API."""
        try:
            response = requests.get(f"{API_URL}/timer")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching timers: {e}")
            return []

    def create_timer(self, name, duration):
        """Create a new timer."""
        try:
            data = {"name": name, "duration": duration}
            response = requests.post(f"{API_URL}/timer", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating timer: {e}")
            return None

    def delete_timer(self, timer_id):
        """Delete a timer by ID."""
        try:
            response = requests.delete(f"{API_URL}/timer/{timer_id}")
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error deleting timer: {e}")
            return False

    def update_timer(self, timer_id, name=None, duration=None):
        """Update an existing timer."""
        try:
            data = {}
            if name is not None:
                data["name"] = name
            if duration is not None:
                data["duration"] = duration
                
            response = requests.put(f"{API_URL}/timer/{timer_id}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error updating timer: {e}")
            return None

    def connect_to_timer(self, timer_id):
        """Connect to WebSocket for a specific timer."""
        if self.ws and self.ws.connected:
            self.ws.close()
            
        self.current_timer_id = timer_id
        self.stop_reconnecting = False
        self.reconnect_attempts = 0
        
        def _websocket_thread():
            websocket.enableTrace(False)
            ws_url = f"{WS_URL}/timer/ws/{timer_id}"
            
            def on_message(ws, message):
                try:
                    # Parse the message and emit signal
                    data = json.loads(message)
                    self.timer_state_updated.emit(data)
                except json.JSONDecodeError:
                    print(f"Error decoding message: {message}")
            
            def on_error(ws, error):
                print(f"WebSocket error: {error}")
                self.connection_status_changed.emit(False, f"Error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                print(f"WebSocket closed: {close_status_code}, {close_msg}")
                self.is_connected = False
                self.connection_status_changed.emit(False, "Disconnected")
                
                # Attempt to reconnect
                if not self.stop_reconnecting and self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    time.sleep(self.reconnect_delay)
                    if not self.stop_reconnecting:  # Check again after delay
                        print(f"Attempting to reconnect... (Attempt {self.reconnect_attempts})")
                        self.connect_to_timer(self.current_timer_id)
            
            def on_open(ws):
                print(f"WebSocket connected to timer {timer_id}")
                self.is_connected = True
                self.reconnect_attempts = 0
                self.connection_status_changed.emit(True, "Connected")
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            self.ws.run_forever()
        
        self.ws_thread = threading.Thread(target=_websocket_thread)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        return True

    def disconnect(self):
        """Disconnect from the current timer WebSocket."""
        self.stop_reconnecting = True
        if self.ws:
            self.ws.close()
            self.ws = None
        self.current_timer_id = None
        self.is_connected = False

    def send_command(self, action):
        """Send a command to the connected timer."""
        if not self.ws or not self.is_connected:
            print("Not connected to any timer")
            return False
            
        try:
            command = json.dumps({"action": action})
            self.ws.send(command)
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False
            
    def start_timer(self):
        """Start the timer."""
        return self.send_command("start")
    
    def pause_timer(self):
        """Pause the timer."""
        return self.send_command("pause")
    
    def resume_timer(self):
        """Resume the timer."""
        return self.send_command("resume")
    
    def stop_timer(self):
        """Stop/reset the timer."""
        return self.send_command("stop") 