#!/usr/bin/env python3

import os
import sys
import subprocess

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import PyQt6
        import websocket
        import requests
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Installing dependencies...")
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            return True
        except subprocess.CalledProcessError:
            print("Failed to install dependencies. Please install them manually:")
            print("pip install -r requirements.txt")
            return False

def main():
    """Main entry point for the application launcher."""
    if not check_dependencies():
        sys.exit(1)
    
    # Import the main module
    try:
        from src.main import main as app_main
        app_main()
    except Exception as e:
        print(f"Error launching application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 