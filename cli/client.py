import requests
from configparser import ConfigParser
from datetime import datetime
from typing import List, Dict, Any
import os
from pathlib import Path

class HabitClient:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / 'config.ini'
            
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
        config = ConfigParser()
        config.read(config_path)
        
        if 'api' not in config:
            raise KeyError("Configuration file must contain an [api] section")
        
        if 'host' not in config['api'] or 'port' not in config['api']:
            raise KeyError("Configuration must specify both 'host' and 'port' under [api] section")
        
        host = config['api']['host']
        port = config['api']['port']
        self.api_endpoint = f"{host.rstrip('/')}:{port}"
        
    def list_habits(self) -> List[Dict[str, Any]]:
        """Get all habits"""
        response = requests.get(f"{self.api_endpoint}/habits")
        response.raise_for_status()
        return response.json()
    
    def create_habit(self, name: str, recurrence: str) -> Dict[str, Any]:
        """Create a new habit"""
        payload = {
            "name": name,
            "recurrence": recurrence
        }
        response = requests.post(f"{self.api_endpoint}/habits", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_due_habits(self, date: str = None) -> List[Dict[str, Any]]:
        """Get habits due for a specific date or today"""
        if date:
            response = requests.get(f"{self.api_endpoint}/habits/due", params={"date": date})
        else:
            response = requests.get(f"{self.api_endpoint}/habits/due/today")
        response.raise_for_status()
        return response.json()
    
    def complete_habit(self, log_id: str) -> bool:
        """Mark a habit log as completed"""
        response = requests.put(f"{self.api_endpoint}/habits/check/{log_id}")
        response.raise_for_status()
        return response.json()["status"] == "success" 