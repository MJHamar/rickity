from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict
from uuid import UUID
import json

from timer.database.database import get_db
from timer.models import Timer, TimerCreate
from timer.repositories.timer_repository import TimerRepository
from timer.websocket_manager import timer_manager

from utils.logging import setup_logger
logger = setup_logger(__name__)

router = APIRouter()

@router.get("/", response_model=List[Timer])
async def get_timers(db: Session = Depends(get_db)):
    """Get all timer definitions"""
    logger.info("Fetching all timers")
    repo = TimerRepository(db)
    return repo.get_timers()

@router.post("/", response_model=Timer)
async def create_timer(timer: TimerCreate, db: Session = Depends(get_db)):
    """Create a new timer definition"""
    logger.info(f"Creating new timer: {timer.name}")
    repo = TimerRepository(db)
    try:
        new_timer = repo.create_timer(timer)
        return new_timer
    except ValueError as e:
        logger.warning(f"Invalid timer data: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/active", response_model=Dict)
async def get_active_timers():
    """Get all currently active timers"""
    return timer_manager.get_active_timers()

@router.delete("/{timer_id}", response_model=Dict)
async def delete_timer(timer_id: UUID, db: Session = Depends(get_db)):
    """Delete a timer by ID"""
    logger.info(f"Request to delete timer: {timer_id}")
    repo = TimerRepository(db)
    success = repo.delete_timer(timer_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Timer with ID {timer_id} not found"
        )
    
    return {"message": f"Timer with ID {timer_id} deleted successfully"}

@router.put("/{timer_id}", response_model=Timer)
async def update_timer(timer_id: UUID, timer: TimerCreate, db: Session = Depends(get_db)):
    """Update an existing timer"""
    logger.info(f"Updating timer: {timer_id}")
    repo = TimerRepository(db)
    
    try:
        updated_timer = repo.update_timer(timer_id, timer)
        if updated_timer is None:
            raise HTTPException(
                status_code=404,
                detail=f"Timer with ID {timer_id} not found"
            )
        return updated_timer
    except ValueError as e:
        logger.warning(f"Invalid timer data: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.websocket("/ws/{timer_id}")
async def websocket_endpoint(websocket: WebSocket, timer_id: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for timer updates"""
    await websocket.accept()
    
    try:
        # Get timer from database
        repo = TimerRepository(db)
        timer = repo.get_timer(UUID(timer_id))
        if timer is None:
            await websocket.close(code=1000, reason="Timer not found")
            return
        
        # Register timer with manager
        await timer_manager.register_timer(timer_id, timer.name, timer.duration)
        
        # Subscribe to timer updates
        await timer_manager.subscribe(websocket, timer_id)
        
        # Ensure the update loop is running
        await timer_manager.start_update_loop()
        
        # Listen for commands from the client
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                action = command.get("action")
                
                if action == "start":
                    await timer_manager.start_timer(timer_id)
                elif action == "pause":
                    await timer_manager.pause_timer(timer_id)
                elif action == "stop":
                    await timer_manager.stop_timer(timer_id)
                elif action == "resume":
                    await timer_manager.resume_timer(timer_id)
                # Handle 'set' command for updating timer value
                elif 'set' in command:
                    new_time = command.get('set')
                    if new_time and isinstance(new_time, str):
                        try:
                            # Update timer value
                            success = await timer_manager.set_timer_value(timer_id, new_time)
                            if success:
                                # If successful, also update in the database
                                updated_timer = repo.get_timer(UUID(timer_id))
                                if updated_timer:
                                    # Get current timer state to get the new duration in seconds
                                    timer_state = timer_manager.active_timers.get(timer_id)
                                    if timer_state:
                                        # Create a TimerCreate object with the current name and new duration
                                        timer_update = TimerCreate(
                                            name=updated_timer.name,
                                            duration=timer_state.duration
                                        )
                                        repo.update_timer(UUID(timer_id), timer_update)
                        except ValueError as e:
                            logger.error(f"Error setting timer value: {e}")
                else:
                    logger.warning(f"Unknown action: {action}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
            except Exception as e:
                logger.error(f"Error processing command: {e}")
    
    except WebSocketDisconnect:
        # Client disconnected
        logger.info(f"Client disconnected from timer {timer_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Ensure cleanup
        try:
            await timer_manager.unsubscribe(websocket, timer_id)
        except:
            pass
