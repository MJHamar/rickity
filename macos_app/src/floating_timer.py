import sys
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QGraphicsDropShadowEffect
)

from config import FLOATING_WINDOW_SIZE, CORNER_MARGIN, TRANSPARENCY, AVOID_CURSOR_DISTANCE
from utils import (
    format_time, get_screen_geometry, calculate_corners, find_nearest_corner,
    get_cursor_distance, calculate_avoidance_position, is_dark_mode, debug_window_info
)


class FloatingTimerWindow(QWidget):
    """A floating window that displays the timer and avoids the cursor when needed."""
    
    # Signals
    closed = pyqtSignal()  # Emitted when window is closed
    
    def __init__(self, timer_name, timer_id, parent=None, dark_mode=None):
        # Create the window first with basic flags
        super().__init__(parent)
        
        # Set these critical attributes immediately
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Initialize fields
        self.timer_id = timer_id
        self.timer_name = timer_name
        self.timer_seconds = 0
        self.timer_status = "stopped"
        self.window_size = FLOATING_WINDOW_SIZE
        self.is_focused = False
        self.is_hovered = False
        self.dragging = False
        self.drag_start_position = None
        self.dark_mode = dark_mode if dark_mode is not None else is_dark_mode()
        self.compact_mode = True  # Start in compact mode by default
        self.allow_activation = False  # Control when we want to accept focus
        self.visibility_checked = False  # Flag to track if we've checked visibility
        self.active_app_window = None  # Track the active window of our app
        
        # Set up UI and other features
        self.init_ui()
        self.setup_corner_snapping()
        self.setup_cursor_avoidance()
        
        # Now apply window flags properly - do this after UI setup but before show
        self.apply_window_flags()
        
        # Set up the global event filter
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
            self.active_app_window = app.activeWindow()
        
        # First approach: Raise the window periodically
        self.stay_on_top_timer = QTimer(self)
        self.stay_on_top_timer.timeout.connect(self.ensure_on_top)
        self.stay_on_top_timer.start(300)  # More frequent checks
        
        # Second approach: Check hover state separately
        self.hover_check_timer = QTimer(self)
        self.hover_check_timer.timeout.connect(self.check_hover_state)
        self.hover_check_timer.start(50)  # Very frequent checks
        
        # Add visibility check timer
        self.visibility_timer = QTimer(self)
        self.visibility_timer.timeout.connect(self.check_visibility)
        self.visibility_timer.setSingleShot(True)
        
        # Add focus restoration timer
        self.focus_restore_timer = QTimer(self)
        self.focus_restore_timer.timeout.connect(self.restore_focus)
        self.focus_restore_timer.setSingleShot(True)
        
        # Log that window was created
        print(f"Timer window created: {timer_name} (ID: {timer_id})")
    
    def apply_window_flags(self):
        """Apply window flags properly - this order is important."""
        print("Applying window flags...")
        flags = (
            Qt.WindowType.Tool |  # Use Tool for non-focus window
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowDoesNotAcceptFocus  # Critical for preventing focus
        )
        self.setWindowFlags(flags)
        print("Window flags applied.")
    
    def restore_focus(self):
        """Restore focus to the previously active window."""
        app = QApplication.instance()
        if app and self.active_app_window and self.active_app_window != self:
            print(f"Restoring focus to: {self.active_app_window.windowTitle()}")
            self.active_app_window.raise_()
            self.active_app_window.activateWindow()
            # Force the active window to be in front
            self.raise_()  # Put ourselves topmost but not active
    
    def check_visibility(self):
        """Check if the window is actually visible and take corrective action if not."""
        if not self.isVisible() and not self.visibility_checked:
            print(f"Window for timer {self.timer_name} is not visible! Attempting fallback...")
            debug_window_info(self)
            self.visibility_checked = True
            
            # Try more aggressive approach - recreate with different flags
            current_pos = self.pos()
            current_geometry = self.geometry()
            
            # Try different set of flags
            self.setWindowFlags(
                Qt.WindowType.Window |  # Use Window instead of Tool
                Qt.WindowType.FramelessWindowHint | 
                Qt.WindowType.WindowStaysOnTopHint
            )
            
            # Show again with new flags
            self.show()
            self.setGeometry(current_geometry)
            print(f"Fallback: Recreated window for {self.timer_name} with different flags")
            debug_window_info(self)
        
        # Schedule another check if still needed
        if not self.isVisible():
            print(f"Window for timer {self.timer_name} still not visible. Will check again...")
            self.visibility_timer.start(500)  # Check again in 500ms
    
    def check_hover_state(self):
        """Check if mouse is hovering over this window without relying on enter/leave events."""
        if not self.underMouse() and self.is_hovered:
            self.is_hovered = False
            self.update_ui_mode()
        elif self.underMouse() and not self.is_hovered:
            self.is_hovered = True
            self.update_ui_mode()
    
    def ensure_on_top(self):
        """Ensure this window stays on top by raising it without stealing focus."""
        # Only if we're not already handling a user interaction
        if not self.dragging:
            # Keep track of the active window before we do anything
            app = QApplication.instance()
            if app and app.activeWindow() and app.activeWindow() != self:
                self.active_app_window = app.activeWindow()
            
            # Raise this window without activating it
            self.raise_()
    
    def eventFilter(self, watched, event):
        """Global event filter to handle application-wide focus changes."""
        # If any window gets focus, update our active window reference
        if event.type() == QEvent.Type.WindowActivate:
            # Keep track of the active window (but not ourselves)
            app = QApplication.instance()
            if app and app.activeWindow() and app.activeWindow() != self:
                self.active_app_window = app.activeWindow()
                # Also force an update of our UI state
                self.update_ui_mode()
        
        # If our window gets focus, immediately restore focus to the previous window
        if event.type() == QEvent.Type.WindowActivate and watched == self:
            self.focus_restore_timer.start(10)  # Very fast response
            
        return super().eventFilter(watched, event)
    
    def init_ui(self):
        """Initialize the UI components."""
        # Set window properties
        self.setWindowTitle(f"Timer: {self.timer_name}")
        self.setFixedSize(self.window_size, self.window_size)
        self.setWindowOpacity(TRANSPARENCY)
        
        # Create layouts
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title Label
        self.title_label = QLabel(self.timer_name)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Time Label (always visible)
        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        
        # Status Label
        self.status_label = QLabel("Stopped")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Control Buttons Container (will be hidden when unfocused)
        self.controls_widget = QWidget()
        control_layout = QVBoxLayout(self.controls_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status label inside controls
        control_layout.addWidget(self.status_label)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.toggle_button = QPushButton("Start")
        self.toggle_button.setFixedHeight(25)
        self.toggle_button.clicked.connect(self.toggle_timer)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.setFixedHeight(25)
        self.reset_button.clicked.connect(self.reset_timer)
        
        self.close_button = QPushButton("Close")
        self.close_button.setFixedHeight(25)
        self.close_button.clicked.connect(self.close_window)
        
        button_layout.addWidget(self.toggle_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.close_button)
        
        control_layout.addLayout(button_layout)
        
        # Add widgets to main layout
        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.time_label)
        self.main_layout.addWidget(self.controls_widget)
        self.main_layout.addStretch()
        
        self.setLayout(self.main_layout)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
        
        # Apply theme
        self.apply_theme()
        
        # Initial UI mode
        self.update_ui_mode()
    
    def apply_theme(self):
        """Apply the appropriate theme based on system settings."""
        if self.dark_mode:
            # Dark mode
            self.title_label.setStyleSheet("color: white; font-weight: bold;")
            self.time_label.setStyleSheet("color: white;")
            self.status_label.setStyleSheet("color: white;")
            self.controls_widget.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)
        else:
            # Light mode
            self.title_label.setStyleSheet("color: black; font-weight: bold;")
            self.time_label.setStyleSheet("color: black;")
            self.status_label.setStyleSheet("color: black;")
            self.controls_widget.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    color: black;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
    
    def update_ui_mode(self):
        """Update UI based on hover/focus state."""
        # Simplify the logic - if hovering or has focus, show controls
        if self.is_hovered or self.is_focused:
            if self.compact_mode:
                self.compact_mode = False
                self.title_label.show()
                self.controls_widget.show()
                self.time_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
                self.main_layout.setContentsMargins(10, 10, 10, 10)
        else:
            if not self.compact_mode:
                self.compact_mode = True
                self.title_label.hide()
                self.controls_widget.hide()
                self.time_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
                self.main_layout.setContentsMargins(5, 5, 5, 5)
    
    def setup_corner_snapping(self):
        """Set up corner snapping functionality."""
        # Get screen geometry and calculate corners
        self.screen_geometry = get_screen_geometry()
        self.corners = calculate_corners(self.screen_geometry, self.window_size, CORNER_MARGIN)
        
        # Initially position at top-right corner
        self.move(self.corners[1])  # Top-right
    
    def setup_cursor_avoidance(self):
        """Set up cursor avoidance functionality."""
        self.cursor_check_timer = QTimer(self)
        self.cursor_check_timer.timeout.connect(self.check_cursor_proximity)
        self.cursor_check_timer.start(100)  # Check every 100ms
    
    def check_cursor_proximity(self):
        """Check if cursor is near the window and avoid if needed."""
        # Only avoid cursor when window is not focused and not hovered
        if self.is_focused or self.is_hovered:
            return
            
        window_rect = QRect(self.pos(), self.size())
        distance, dx, dy = get_cursor_distance(window_rect)
        
        # If cursor is close enough to window center, calculate new position
        if distance < AVOID_CURSOR_DISTANCE:
            new_pos = calculate_avoidance_position(
                window_rect, AVOID_CURSOR_DISTANCE, dx, dy, self.corners
            )
            
            if new_pos:
                self.move(new_pos)
    
    def update_timer_state(self, state_data):
        """Update the timer state with data from WebSocket."""
        self.timer_seconds = state_data.get("timer_state", 0)
        self.timer_status = state_data.get("timer_status", "stopped")
        
        # Update the UI
        self.time_label.setText(format_time(self.timer_seconds))
        
        status_text = ""
        background_color = "rgba(50, 50, 50, 200)"  # Default dark background
        
        if self.timer_status == "rolling":
            status_text = "Running"
            background_color = "rgba(0, 120, 180, 200)"  # Blue
            self.toggle_button.setText("Pause")
        elif self.timer_status == "paused":
            status_text = "Paused"
            background_color = "rgba(180, 120, 0, 200)"  # Orange
            self.toggle_button.setText("Resume")
        elif self.timer_status == "stopped":
            status_text = "Stopped"
            background_color = "rgba(50, 50, 50, 200)"  # Dark gray
            self.toggle_button.setText("Start")
        elif self.timer_status == "finished":
            status_text = "Finished!"
            background_color = "rgba(0, 150, 50, 200)"  # Green
            self.toggle_button.setText("Start")
            
        self.status_label.setText(status_text)
        
        # Adjust background color based on dark mode
        if self.dark_mode:
            # Darken colors slightly for dark mode
            self.setStyleSheet(f"background-color: {background_color}; border-radius: 10px;")
        else:
            # Keep original colors for light mode
            self.setStyleSheet(f"background-color: {background_color}; border-radius: 10px;")
    
    def toggle_timer(self):
        """Toggle the timer state (start/pause/resume)."""
        # This will emit a signal that the main app will handle
        if self.timer_status == "rolling":
            self.toggle_button.setText("Resume")
            self.emit_command("pause")
        elif self.timer_status == "paused":
            self.toggle_button.setText("Pause")
            self.emit_command("resume")
        else:  # stopped or finished
            self.toggle_button.setText("Pause")
            self.emit_command("start")
    
    def reset_timer(self):
        """Reset the timer."""
        self.toggle_button.setText("Start")
        self.emit_command("stop")
    
    def emit_command(self, command):
        """Emit a command to be handled by the main app."""
        # This will be implemented by connection to the main app's signals
        pass
    
    def close_window(self):
        """Close the window and emit signal."""
        self.closed.emit()
        self.close()
    
    def focusInEvent(self, event):
        """Handle focus in event."""
        self.is_focused = True
        self.update_ui_mode()
        
        # Immediately transfer focus back to the main app window
        self.focus_restore_timer.start(10)
        
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """Handle focus out event."""
        self.is_focused = False
        self.update_ui_mode()
        super().focusOutEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter event."""
        self.is_hovered = True
        self.update_ui_mode()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event."""
        self.is_hovered = False
        self.update_ui_mode()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_position = event.position().toPoint()
            
            # Store the current active window before handling the press
            app = QApplication.instance()
            if app and app.activeWindow() and app.activeWindow() != self:
                self.active_app_window = app.activeWindow()
        
        # Process the event but don't pass to parent (to avoid focus)
        event.accept()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for dragging."""
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            
            # Snap to nearest corner
            nearest = find_nearest_corner(self.pos(), self.corners)
            self.move(nearest)
            
            # Restore focus to the previous window
            self.focus_restore_timer.start(10)
        
        # Process the event but don't pass to parent (to avoid focus)
        event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for dragging."""
        if self.dragging and self.drag_start_position:
            delta = event.position().toPoint() - self.drag_start_position
            self.move(self.pos() + delta.toPoint())
        
        # Process the event but don't pass to parent
        event.accept()
    
    def paintEvent(self, event):
        """Custom paint event to create rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        # Set the window mask to the rounded rectangle
        painter.setClipPath(path)
        
        # Let the style handle the background painting
        super().paintEvent(event)
    
    def showEvent(self, event):
        """Handle show event to ensure window appears on top."""
        super().showEvent(event)
        
        # Just raise the window without changing any flags or attributes here
        self.raise_()
        
        # Log that window is being shown
        print(f"Timer window shown: {self.timer_name}")
        
        # Debug window info
        debug_window_info(self)
        
        # Start visibility check timer
        self.visibility_timer.start(300)  # Check visibility after 300ms 