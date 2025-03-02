# app/timer/websocket_manager.py
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect

from utils.logging import setup_logger
logger = setup_logger(__name__)

class TimerState:
    def __init__(self, timer_id: str, name: str, duration: int):
        self.timer_id = timer_id
        self.name = name
        self.duration = duration  # Total duration in seconds
        self.remaining = duration  # Remaining time in seconds
        self.status = "stopped"   # stopped, rolling, paused, finished
        self.subscribers: Set[WebSocket] = set()
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
    
    def seconds_to_hhmmss(self, seconds: int) -> str:
        """Convert seconds to HHmmss format"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}{minutes:02d}{seconds:02d}"
    
    def hhmmss_to_seconds(self, hhmmss: str) -> int:
        """Convert HHmmss format to seconds"""
        if len(hhmmss) != 6:
            raise ValueError("Time must be in HHmmss format")
        
        hours = int(hhmmss[0:2])
        minutes = int(hhmmss[2:4])
        seconds = int(hhmmss[4:6])
        
        return hours * 3600 + minutes * 60 + seconds
    
    def to_dict(self):
        return {
            "timer_id": self.timer_id,
            "name": self.name,
            "duration": self.seconds_to_hhmmss(self.duration),
            "timer_state": self.seconds_to_hhmmss(self.remaining),
            "timer_status": self.status,
            "subscribers": len(self.subscribers)
        }

class TimerManager:
    def __init__(self):
        self.active_timers: Dict[str, TimerState] = {}
        self.update_task = None
    
    async def start_update_loop(self):
        """Start the background task that updates all timers"""
        if self.update_task is None:
            self.update_task = asyncio.create_task(self._update_timers())
    
    async def _update_timers(self):
        """Background task that updates timer states and notifies subscribers"""
        while True:
            try:
                current_time = datetime.utcnow()
                
                for timer_id, timer in list(self.active_timers.items()):
                    if timer.status == "rolling":
                        elapsed = (current_time - timer.start_time).total_seconds()
                        timer.remaining = max(0, timer.duration - elapsed)
                        
                        # Timer has finished
                        if timer.remaining <= 0:
                            timer.status = "finished"
                            timer.remaining = 0
                        
                        # Notify all subscribers
                        await self._notify_subscribers(timer_id)
                        
                        # Remove timer if no subscribers (for both stopped and finished statuses)
                        if (timer.status == "stopped" or timer.status == "finished") and not timer.subscribers:
                            del self.active_timers[timer_id]
                
                await asyncio.sleep(1)  # Update every second
            except Exception as e:
                logger.error(f"Error in timer update loop: {e}")
                await asyncio.sleep(1)  # Continue even if there's an error
    
    async def register_timer(self, timer_id: str, name: str, duration: int) -> TimerState:
        """Register a new timer or get existing one"""
        if timer_id not in self.active_timers:
            self.active_timers[timer_id] = TimerState(timer_id, name, duration)
        return self.active_timers[timer_id]
    
    async def subscribe(self, websocket: WebSocket, timer_id: str):
        """Subscribe a client to timer updates"""
        if timer_id not in self.active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        self.active_timers[timer_id].subscribers.add(websocket)
        # Send initial state
        await self._notify_subscriber(timer_id, websocket)
    
    async def unsubscribe(self, websocket: WebSocket, timer_id: str):
        """Unsubscribe a client from timer updates"""
        if timer_id in self.active_timers and websocket in self.active_timers[timer_id].subscribers:
            self.active_timers[timer_id].subscribers.remove(websocket)
            
            # Clean up timer if no subscribers and not running
            if not self.active_timers[timer_id].subscribers and self.active_timers[timer_id].status not in ["rolling", "paused"]:
                del self.active_timers[timer_id]
    
    async def start_timer(self, timer_id: str):
        """Start a timer"""
        if timer_id not in self.active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self.active_timers[timer_id]
        if timer.status == "stopped":
            # Starting from the beginning
            timer.remaining = timer.duration
        
        timer.status = "rolling"
        timer.start_time = datetime.utcnow()
        await self._notify_subscribers(timer_id)
    
    async def pause_timer(self, timer_id: str):
        """Pause a timer"""
        if timer_id not in self.active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self.active_timers[timer_id]
        if timer.status != "rolling":
            raise ValueError("Cannot pause a timer that is not running")
        
        timer.status = "paused"
        timer.pause_time = datetime.utcnow()
        # Calculate remaining time at pause
        elapsed = (timer.pause_time - timer.start_time).total_seconds()
        timer.remaining = max(0, timer.duration - elapsed)
        await self._notify_subscribers(timer_id)
    
    async def stop_timer(self, timer_id: str):
        """Stop a timer"""
        if timer_id not in self.active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self.active_timers[timer_id]
        timer.status = "stopped"  # Explicitly set as stopped, not finished
        timer.remaining = timer.duration  # Reset to full duration
        await self._notify_subscribers(timer_id)
    
    async def resume_timer(self, timer_id: str):
        """Resume a paused timer"""
        if timer_id not in self.active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self.active_timers[timer_id]
        if timer.status != "paused":
            raise ValueError("Cannot resume a timer that is not paused")
        
        # Set the status to rolling
        timer.status = "rolling"
        
        # Calculate a new start_time that accounts for the time already spent
        # This ensures the timer continues from where it was paused
        current_time = datetime.utcnow()
        time_already_spent = timer.duration - timer.remaining
        timer.start_time = current_time - timedelta(seconds=time_already_spent)
        
        # Notify subscribers about the state change
        await self._notify_subscribers(timer_id)
    
    async def _notify_subscribers(self, timer_id: str):
        """Send updates to all subscribers of a timer"""
        if timer_id not in self.active_timers:
            return
            
        timer = self.active_timers[timer_id]
        closed_websockets = set()
        
        for websocket in timer.subscribers:
            try:
                await self._notify_subscriber(timer_id, websocket)
            except Exception:
                closed_websockets.add(websocket)
        
        # Remove closed websockets
        for ws in closed_websockets:
            timer.subscribers.remove(ws)
    
    async def _notify_subscriber(self, timer_id: str, websocket: WebSocket):
        """Send timer update to a single subscriber"""
        if timer_id not in self.active_timers:
            return
            
        timer = self.active_timers[timer_id]
        message = {
            "timer_state": timer.seconds_to_hhmmss(int(timer.remaining)),
            "timer_status": timer.status
        }
        await websocket.send_text(json.dumps(message))
    
    def get_active_timers(self):
        """Get all active timers"""
        return {timer_id: timer.to_dict() for timer_id, timer in self.active_timers.items()}
    
    async def set_timer_value(self, timer_id: str, hhmmss: str):
        """Set a new value for the timer"""
        if timer_id not in self.active_timers:
            raise ValueError(f"Timer {timer_id} not found")
        
        timer = self.active_timers[timer_id]
        
        # Only allow changing the timer if it's not running
        if timer.status == "rolling":
            raise ValueError("Cannot change timer value while it is running")
            
        try:
            # Convert HHmmss to seconds
            new_seconds = timer.hhmmss_to_seconds(hhmmss)
            
            # Update timer values
            timer.duration = new_seconds
            timer.remaining = new_seconds
            
            # Notify subscribers about the state change
            await self._notify_subscribers(timer_id)
            
            return True
        except ValueError as e:
            logger.error(f"Error setting timer value: {e}")
            return False

# Create a global instance of the timer manager
timer_manager = TimerManager()