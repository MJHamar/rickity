from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Response, Query, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from uuid import UUID
import json
import os
from starlette.responses import FileResponse
from starlette.background import BackgroundTask
from fastapi.responses import JSONResponse
import subprocess
import tempfile

from timer.database.database import get_db
from timer.models import Timer, TimerCreate, Sound
from timer.repositories.timer_repository import TimerRepository
from timer.repositories.sound_repository import SoundRepository
from timer.websocket_manager import timer_manager
from utils.logging import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Sound routes
@router.get("/sounds", response_model=List[Sound])
async def get_sounds(db: Session = Depends(get_db)):
    """Get all sounds"""
    logger.info("Fetching all sounds")
    repo = SoundRepository(db)
    return repo.get_sounds()

@router.get("/sounds/{sound_id}")
async def get_sound_file(
    sound_id: UUID, 
    convert_format: Optional[str] = Query(None, description="Format to convert to (mp3, wav)"),
    db: Session = Depends(get_db)
):
    """Get a sound file by ID"""
    logger.info(f"Fetching sound file for ID: {sound_id}")
    repo = SoundRepository(db)
    sound = repo.get_sound(sound_id)
    
    if sound is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sound with ID {sound_id} not found"
        )
    
    # Check if the file exists
    if not os.path.exists(sound.file):
        raise HTTPException(
            status_code=404,
            detail=f"Sound file {sound.file} not found"
        )
    
    # Determine the correct media type based on file extension
    file_ext = os.path.splitext(sound.file)[1].lower()
    media_type = "audio/mpeg"  # Default to MP3
    
    if file_ext == ".aiff" or file_ext == ".aif":
        media_type = "audio/aiff"
    elif file_ext == ".wav":
        media_type = "audio/wav"
    elif file_ext == ".ogg":
        media_type = "audio/ogg"
    elif file_ext == ".mp3":
        media_type = "audio/mpeg"
    
    # Log the file and media type for debugging
    logger.info(f"Serving sound file: {sound.file} with media type: {media_type}")
    
    # Check if format conversion is requested
    if convert_format and file_ext in ['.aiff', '.aif'] and convert_format.lower() in ['mp3', 'wav']:
        try:
            # Create a temporary file for the converted audio
            with tempfile.NamedTemporaryFile(suffix=f'.{convert_format.lower()}', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # Attempt to run ffmpeg to convert the file
                logger.info(f"Converting {file_ext} to {convert_format} using ffmpeg")
                subprocess.run(
                    ['ffmpeg', '-i', sound.file, '-y', tmp_path],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Update media type based on conversion format
                if convert_format.lower() == 'mp3':
                    media_type = "audio/mpeg"
                elif convert_format.lower() == 'wav':
                    media_type = "audio/wav"
                
                # Return the converted file
                logger.info(f"Serving converted sound file: {tmp_path} with media type: {media_type}")
                return FileResponse(
                    tmp_path,
                    media_type=media_type,
                    filename=f"{os.path.splitext(os.path.basename(sound.file))[0]}.{convert_format.lower()}",
                    background=BackgroundTask(lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None)
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                logger.error(f"Failed to convert audio: {str(e)}")
                # If conversion fails, fall back to original file
                pass
        except Exception as e:
            logger.error(f"Error during audio conversion: {str(e)}")
            # Fall back to original file
    
    # Return the original file if no conversion or conversion failed
    return FileResponse(
        sound.file,
        media_type=media_type,
        filename=os.path.basename(sound.file)
    )

@router.patch("/sounds", response_model=List[Sound])
async def sync_sounds(db: Session = Depends(get_db)):
    """Scan the sounds directory and update the database"""
    logger.info("Syncing sounds directory")
    repo = SoundRepository(db)
    sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dingutil", "sounds")
    
    logger.info(f"Using sounds directory: {sounds_dir}")
    if not os.path.exists(sounds_dir):
        return JSONResponse(
            status_code=404,
            content={"detail": f"Sounds directory not found: {sounds_dir}"}
        )
    
    sounds = repo.sync_sounds_directory(sounds_dir)
    return sounds

# Timer routes
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
        await timer_manager.register_timer(timer_id, timer.name, timer.duration, timer.sound_id)
        
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
                                            duration=timer_state.duration,
                                            sound_id=updated_timer.sound_id
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
