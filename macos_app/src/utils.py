import math
import platform
import subprocess
from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import QCursor, QScreen
from PyQt6.QtWidgets import QApplication

def format_time(seconds):
    """Format seconds into HH:MM:SS format."""
    if seconds < 0:
        seconds = 0
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def get_screen_geometry():
    """Get the geometry of the main screen."""
    screen = QApplication.primaryScreen()
    return screen.availableGeometry()

def is_dark_mode():
    """Detect if system is using dark mode."""
    if platform.system() == "Darwin":  # macOS
        try:
            # Use Apple Script to check dark mode on macOS
            cmd = 'defaults read -g AppleInterfaceStyle'
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            return result.stdout.strip() == "Dark"
        except:
            # If there's an error, default to light mode
            return False
    else:
        # For non-macOS, try to detect from the application palette
        app = QApplication.instance()
        if app:
            palette = app.palette()
            background_color = palette.color(palette.ColorRole.Window)
            # If the background is darker than middle gray, assume dark mode
            return background_color.lightness() < 128
        return False

def calculate_corners(screen_geometry, window_size, margin):
    """Calculate the four corner positions for window snapping."""
    top_left = QPoint(margin, margin)
    top_right = QPoint(screen_geometry.width() - window_size - margin, margin)
    bottom_left = QPoint(margin, screen_geometry.height() - window_size - margin)
    bottom_right = QPoint(screen_geometry.width() - window_size - margin, 
                          screen_geometry.height() - window_size - margin)
    
    return [top_left, top_right, bottom_left, bottom_right]

def find_nearest_corner(current_pos, corners):
    """Find the nearest corner to the current position."""
    min_distance = float('inf')
    nearest_corner = corners[0]
    
    for corner in corners:
        distance = math.sqrt((current_pos.x() - corner.x())**2 + 
                            (current_pos.y() - corner.y())**2)
        if distance < min_distance:
            min_distance = distance
            nearest_corner = corner
    
    return nearest_corner

def get_cursor_distance(window_rect):
    """Get the distance from cursor to the window center."""
    cursor_pos = QCursor.pos()
    window_center = window_rect.center()
    
    dx = cursor_pos.x() - window_center.x()
    dy = cursor_pos.y() - window_center.y()
    
    return math.sqrt(dx**2 + dy**2), dx, dy

def calculate_avoidance_position(window_rect, avoid_distance, dx, dy, corners):
    """Calculate a new position to avoid the cursor."""
    # If cursor is far enough, do nothing
    distance = math.sqrt(dx**2 + dy**2)
    if distance > avoid_distance:
        return None
    
    # Determine which direction to move (opposite of cursor)
    angle = math.atan2(dy, dx)
    move_angle = angle + math.pi  # Move in opposite direction
    
    # Calculate move distance (the closer the cursor, the further to move)
    move_factor = 1 - (distance / avoid_distance)
    move_distance = avoid_distance * move_factor
    
    # Calculate new position
    move_x = math.cos(move_angle) * move_distance
    move_y = math.sin(move_angle) * move_distance
    
    new_x = window_rect.x() + move_x
    new_y = window_rect.y() + move_y
    
    # Get screen boundaries
    screen_rect = get_screen_geometry()
    max_x = screen_rect.width() - window_rect.width()
    max_y = screen_rect.height() - window_rect.height()
    
    # Keep within screen boundaries
    new_x = max(0, min(new_x, max_x))
    new_y = max(0, min(new_y, max_y))
    
    # Check if we're close to any corner - if so, snap to it
    new_pos = QPoint(int(new_x), int(new_y))
    for corner in corners:
        corner_distance = math.sqrt((new_x - corner.x())**2 + (new_y - corner.y())**2)
        if corner_distance < avoid_distance:
            return corner
    
    return new_pos

def debug_window_info(window):
    """Print out detailed debugging information about a window."""
    print("\n--- WINDOW DEBUG INFO ---")
    print(f"Window Title: {window.windowTitle()}")
    print(f"Window Class: {window.__class__.__name__}")
    print(f"Is Visible: {window.isVisible()}")
    print(f"Is Active Window: {window.isActiveWindow()}")
    print(f"Has Focus: {window.hasFocus()}")
    print(f"Window Size: {window.size().width()}x{window.size().height()}")
    print(f"Window Position: {window.pos().x()},{window.pos().y()}")
    print(f"Window Geometry: {window.geometry().x()},{window.geometry().y()},{window.geometry().width()},{window.geometry().height()}")
    print(f"Parent: {window.parent()}")
    
    # Window flags
    flags = window.windowFlags()
    print("\nWindow Flags:")
    print(f"- Qt.WindowType.Tool: {bool(flags & Qt.WindowType.Tool)}")
    print(f"- Qt.WindowType.Window: {bool(flags & Qt.WindowType.Window)}")
    print(f"- Qt.WindowType.Dialog: {bool(flags & Qt.WindowType.Dialog)}")
    print(f"- Qt.WindowType.FramelessWindowHint: {bool(flags & Qt.WindowType.FramelessWindowHint)}")
    print(f"- Qt.WindowType.WindowStaysOnTopHint: {bool(flags & Qt.WindowType.WindowStaysOnTopHint)}")
    print(f"- Qt.WindowType.WindowDoesNotAcceptFocus: {bool(flags & Qt.WindowType.WindowDoesNotAcceptFocus)}")
    print(f"- Qt.WindowType.NoDropShadowWindowHint: {bool(flags & Qt.WindowType.NoDropShadowWindowHint)}")
    
    # Attributes
    print("\nWidget Attributes:")
    print(f"- WA_ShowWithoutActivating: {window.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)}")
    print(f"- WA_TranslucentBackground: {window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)}")
    try:
        print(f"- WA_MacNoActivate: {window.testAttribute(Qt.WidgetAttribute.WA_MacNoActivate)}")
    except Exception:
        print("- WA_MacNoActivate: Not supported in this Qt version")
    
    print("------------------------\n") 