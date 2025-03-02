from sqlalchemy.orm import Session
import os
from uuid import UUID
from typing import List, Optional

from utils.logging import setup_logger
from timer.models import SoundDB

logger = setup_logger(__name__)

class SoundRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_sounds(self) -> List[SoundDB]:
        """Get all sounds"""
        logger.debug("Fetching all sounds")
        return self.db.query(SoundDB).all()

    def get_sound(self, sound_id: UUID) -> Optional[SoundDB]:
        """Get a specific sound by ID"""
        logger.debug(f"Fetching sound with ID: {sound_id}")
        return self.db.query(SoundDB).filter(SoundDB.id == str(sound_id)).first()
    
    def get_sound_by_file(self, file_path: str) -> Optional[SoundDB]:
        """Get a sound by file path"""
        logger.debug(f"Fetching sound with file path: {file_path}")
        return self.db.query(SoundDB).filter(SoundDB.file == file_path).first()

    def create_sound(self, name: str, file_path: str) -> SoundDB:
        """Create a new sound"""
        logger.info(f"Creating new sound: {name}")
        
        # Check if a sound with this file path already exists
        existing_sound = self.get_sound_by_file(file_path)
        if existing_sound:
            logger.info(f"Sound with file path {file_path} already exists, returning existing record")
            return existing_sound
        
        db_sound = SoundDB(
            name=name,
            file=file_path
        )
        self.db.add(db_sound)
        self.db.commit()
        self.db.refresh(db_sound)
        logger.info(f"Created sound with ID: {db_sound.id}")
        return db_sound

    def sync_sounds_directory(self, sounds_dir: str) -> List[SoundDB]:
        """
        Scan the sounds directory and ensure all files have corresponding records in the database.
        Returns the list of all sounds in the database after the sync.
        """
        logger.info(f"Syncing sounds directory: {sounds_dir}")
        
        # Ensure the directory exists
        if not os.path.exists(sounds_dir):
            logger.error(f"Sounds directory not found: {sounds_dir}")
            return []
        
        sound_files = []
        
        # Get all sound files in the directory
        for file in os.listdir(sounds_dir):
            if file.endswith(('.wav', '.aiff', '.mp3', '.ogg')):
                sound_files.append(file)
        
        # Ensure each file has a record in the database
        for file in sound_files:
            file_path = os.path.join(sounds_dir, file)
            # Use the file stem (filename without extension) as the name
            name = os.path.splitext(file)[0]
            
            # Check if a sound with this file already exists
            existing_sound = self.get_sound_by_file(file_path)
            if not existing_sound:
                # Create a new sound record
                self.create_sound(name, file_path)
        
        # Return all sounds after sync
        return self.get_sounds() 