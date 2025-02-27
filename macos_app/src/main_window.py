import sys
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QListWidget, QListWidgetItem,
    QDialog, QFormLayout, QMessageBox, QScrollArea, QFrame
)

from config import WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME
from api_client import TimerApiClient
from floating_timer import FloatingTimerWindow
from utils import format_time, is_dark_mode


class NewTimerDialog(QDialog):
    """Dialog for creating a new timer."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Timer")
        self.setFixedSize(300, 150)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 86400)  # 1 second to 24 hours
        self.duration_input.setValue(60)  # Default: 1 minute
        self.duration_input.setSuffix(" seconds")
        
        layout.addRow("Timer Name:", self.name_input)
        layout.addRow("Duration:", self.duration_input)
        
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
    
    def get_timer_data(self):
        """Get the timer data from the dialog."""
        return {
            "name": self.name_input.text(),
            "duration": self.duration_input.value()
        }


class TimerItem(QWidget):
    """Custom widget for displaying a timer in the list."""
    
    def __init__(self, timer_data, parent=None, dark_mode=False):
        super().__init__(parent)
        
        self.timer_id = timer_data.get("id")
        self.timer_name = timer_data.get("name", "Unnamed Timer")
        self.timer_duration = timer_data.get("duration", 0)
        self.dark_mode = dark_mode
        
        # Create layout
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Timer info
        info_layout = QVBoxLayout()
        
        self.name_label = QLabel(self.timer_name)
        self.name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.duration_label = QLabel(f"Duration: {format_time(self.timer_duration)}")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.duration_label)
        
        # Control buttons
        button_layout = QVBoxLayout()
        
        self.start_button = QPushButton("Open")
        self.delete_button = QPushButton("Delete")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.delete_button)
        
        # Add layouts to main layout
        layout.addLayout(info_layout, 3)
        layout.addLayout(button_layout, 1)
        
        # Set up the widget
        self.setLayout(layout)
        self.apply_theme()
        
        # Set fixed height for consistent list appearance
        self.setFixedHeight(80)
    
    def apply_theme(self):
        """Apply appropriate styling based on theme."""
        if self.dark_mode:
            self.setStyleSheet("""
                background-color: #333333;
                color: #ffffff;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            """)
            self.name_label.setStyleSheet("color: #ffffff;")
            self.duration_label.setStyleSheet("color: #cccccc;")
        else:
            self.setStyleSheet("""
                background-color: #f5f5f5;
                color: #000000;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            """)
            self.name_label.setStyleSheet("color: #000000;")
            self.duration_label.setStyleSheet("color: #333333;")


class MainWindow(QMainWindow):
    """Main application window that lists all timers and allows creating new ones."""
    
    def __init__(self):
        super().__init__()
        
        self.api_client = TimerApiClient()
        self.floating_windows = {}  # Map of timer_id to window
        self.dark_mode = is_dark_mode()
        
        self.init_ui()
        self.load_timers()
        
        # Set up theme detection timer
        self.theme_check_timer = QTimer(self)
        self.theme_check_timer.timeout.connect(self.check_theme)
        self.theme_check_timer.start(1000)  # Check every second
    
    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        app_title = QLabel(APP_NAME)
        app_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_timers)
        
        new_timer_button = QPushButton("New Timer")
        new_timer_button.clicked.connect(self.show_new_timer_dialog)
        
        header_layout.addWidget(app_title)
        header_layout.addStretch()
        header_layout.addWidget(refresh_button)
        header_layout.addWidget(new_timer_button)
        
        # Timer list
        self.timer_list = QListWidget()
        
        # Create scroll area for timer list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.timer_list)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        # Add components to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(QLabel("Available Timers:"))
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(status_layout)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Apply initial theme
        self.apply_theme()
        
        # Set up update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
    
    def apply_theme(self):
        """Apply theme-specific styling."""
        if self.dark_mode:
            # Dark mode
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #222222;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QListWidget {
                    background-color: #333333;
                    border: 1px solid #444444;
                    border-radius: 5px;
                    color: #ffffff;
                }
                QListWidget::item {
                    padding: 5px;
                }
                QPushButton {
                    background-color: #444444;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #666666;
                }
                QScrollArea {
                    background-color: #222222;
                    border: none;
                }
            """)
        else:
            # Light mode
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QListWidget {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    color: #000000;
                }
                QListWidget::item {
                    padding: 5px;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #000000;
                    border: 1px solid #cccccc;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                }
                QScrollArea {
                    background-color: #f0f0f0;
                    border: none;
                }
            """)
    
    def check_theme(self):
        """Check if the system theme has changed."""
        current_dark_mode = is_dark_mode()
        if current_dark_mode != self.dark_mode:
            self.dark_mode = current_dark_mode
            self.apply_theme()
            self.load_timers()  # Reload timers to apply new theme to items
    
    def update_status(self):
        """Update status information."""
        active_windows = len(self.floating_windows)
        self.status_label.setText(f"Active Timers: {active_windows}")
    
    def load_timers(self):
        """Load all timers from the API."""
        self.timer_list.clear()
        timers = self.api_client.get_all_timers()
        
        for timer_data in timers:
            self.add_timer_to_list(timer_data)
        
        self.status_label.setText(f"Loaded {len(timers)} timers")
    
    def add_timer_to_list(self, timer_data):
        """Add a timer to the list widget."""
        item = QListWidgetItem()
        
        # Create custom widget for this timer
        timer_widget = TimerItem(timer_data, dark_mode=self.dark_mode)
        
        # Connect signals
        timer_widget.start_button.clicked.connect(
            lambda checked=False, timer_id=timer_data.get("id"), 
            timer_name=timer_data.get("name"): self.open_floating_timer(timer_id, timer_name)
        )
        timer_widget.delete_button.clicked.connect(
            lambda checked=False, timer_id=timer_data.get("id"): self.delete_timer(timer_id)
        )
        
        # Set up list item
        item.setSizeHint(timer_widget.sizeHint())
        self.timer_list.addItem(item)
        self.timer_list.setItemWidget(item, timer_widget)
    
    def show_new_timer_dialog(self):
        """Show dialog to create a new timer."""
        dialog = NewTimerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            timer_data = dialog.get_timer_data()
            
            if not timer_data["name"]:
                QMessageBox.warning(self, "Error", "Timer name cannot be empty.")
                return
            
            # Create timer via API
            response = self.api_client.create_timer(timer_data["name"], timer_data["duration"])
            
            if response:
                self.add_timer_to_list(response)
                self.status_label.setText(f"Created timer: {timer_data['name']}")
            else:
                QMessageBox.warning(self, "Error", "Failed to create timer.")
    
    def open_floating_timer(self, timer_id, timer_name):
        """Open a floating timer window for the specified timer."""
        print(f"Attempting to open timer window for: {timer_name} (ID: {timer_id})")
        
        # Remember the current active window before creating a new one
        active_window = QApplication.activeWindow()
        
        # Check if window already exists
        if timer_id in self.floating_windows:
            self.floating_windows[timer_id].activateWindow()
            return
        
        # Create new floating window
        floating_window = FloatingTimerWindow(timer_name, timer_id, dark_mode=self.dark_mode)
        
        # Connect signals
        floating_window.closed.connect(
            lambda timer_id=timer_id: self.on_floating_window_closed(timer_id)
        )
        
        # Connect API client to floating window
        self.api_client.timer_state_updated.connect(
            lambda data, window=floating_window: window.update_timer_state(data)
        )
        
        self.api_client.connection_status_changed.connect(
            lambda connected, message: self.on_connection_status_changed(connected, message)
        )
        
        # Set up command emission
        original_emit_command = floating_window.emit_command
        
        def new_emit_command(command):
            if command == "start":
                self.api_client.start_timer()
            elif command == "pause":
                self.api_client.pause_timer()
            elif command == "resume":
                self.api_client.resume_timer()
            elif command == "stop":
                self.api_client.stop_timer()
            
            original_emit_command(command)
        
        floating_window.emit_command = new_emit_command
        
        # Connect to timer via WebSocket
        self.api_client.connect_to_timer(timer_id)
        
        # Show window and store reference
        floating_window.show()
        print(f"Floating window show() method called for: {timer_name}")
        
        # Ensure the window stays on top but doesn't steal focus
        floating_window.raise_()
        
        # Restore focus to the main window
        if active_window:
            print(f"Restoring focus to: {active_window.windowTitle()}")
            active_window.activateWindow()
        
        self.floating_windows[timer_id] = floating_window
    
    def on_floating_window_closed(self, timer_id):
        """Handle floating window closed event."""
        if timer_id in self.floating_windows:
            del self.floating_windows[timer_id]
        
        # Disconnect from WebSocket if no windows are open for this timer
        if timer_id not in self.floating_windows:
            self.api_client.disconnect()
    
    def on_connection_status_changed(self, connected, message):
        """Handle connection status changes."""
        if connected:
            self.status_label.setText(f"Connection: {message}")
        else:
            self.status_label.setText(f"Connection: {message}")
    
    def delete_timer(self, timer_id):
        """Delete a timer after confirmation."""
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this timer?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.api_client.delete_timer(timer_id)
            
            if success:
                # Close floating window if open
                if timer_id in self.floating_windows:
                    self.floating_windows[timer_id].close()
                
                # Reload timers
                self.load_timers()
                self.status_label.setText("Timer deleted")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete timer.")
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Close all floating windows
        for window in self.floating_windows.values():
            window.close()
        
        # Disconnect from WebSocket
        self.api_client.disconnect()
        
        super().closeEvent(event) 