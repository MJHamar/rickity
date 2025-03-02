"""
Script to scan the dingutil/sounds directory and add all sound files to the database.
"""
import os
import sys
from sqlalchemy.orm import Session

# Add the app directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from timer.database.database import SessionLocal
from timer.repositories.sound_repository import SoundRepository
from utils.logging import setup_logger

logger = setup_logger(__name__)

def main():
    """
    Scan the sounds directory and add all sound files to the database.
    """
    # Path to the dingutil/sounds directory relative to this script
    sounds_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dingutil", "sounds")
    
    if not os.path.exists(sounds_dir):
        logger.error(f"Sounds directory not found: {sounds_dir}")
        return
    
    logger.info(f"Scanning sounds directory: {sounds_dir}")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create a sound repository
        repo = SoundRepository(db)
        
        # Sync sounds
        sounds = repo.sync_sounds_directory(sounds_dir)
        
        logger.info(f"Found {len(sounds)} sounds")
        for sound in sounds:
            logger.info(f"Sound: {sound.name} ({sound.id}) - {sound.file}")
        
        logger.info("Sounds synced successfully")
    finally:
        db.close()

if __name__ == "__main__":
    main() 