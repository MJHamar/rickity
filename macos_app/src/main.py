#!/usr/bin/env python3

import sys
import os
import signal
import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt

from main_window import MainWindow
from config import APP_NAME

def configure_macos_app(app):
    """Apply macOS-specific configurations to the application."""
    if platform.system() != "Darwin":
        return
        
    print("Configuring for macOS...")
    
    # Simple, more reliable approach for macOS that prioritizes only what works
    # Instead of trying to set many attributes that might not be supported
    
    try:
        # Set platform-specific environment variables
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
        print("- Set QT_MAC_WANTS_LAYER=1")
    except Exception:
        pass
        
    try:
        # This disables native widgets where possible, which can reduce focus issues
        app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
        print("- Enabled AA_DontCreateNativeWidgetSiblings")
    except Exception:
        pass
    
    try:
        # This helps with key events on macOS
        os.environ['QT_ENABLE_NATIVE_VIRTUALKEY'] = '1'
        print("- Set QT_ENABLE_NATIVE_VIRTUALKEY=1")
    except Exception:
        pass
    
    # Additional settings for more reliable focus behavior
    try:
        # This setting can help with preventing focus stealing in some Qt versions
        os.environ['QT_MAC_DISABLE_TOOLTIP'] = '1'
        print("- Set QT_MAC_DISABLE_TOOLTIP=1 to reduce focus interference")
    except Exception:
        pass

def main():
    """Main application entry point."""
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Apply macOS-specific configurations
    configure_macos_app(app)
    
    # Create main window
    main_window = MainWindow()
    main_window.show()
    
    # Start event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 