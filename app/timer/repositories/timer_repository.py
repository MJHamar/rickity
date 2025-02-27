from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from typing import List, Optional

from utils.logging import setup_logger
from timer.database.models import Timer, TimerInstance
from timer.models import TimerDB, TimerCreate

logger = setup_logger(__name__)

class TimerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_timers(self) -> List[TimerDB]:
        """Get all timers"""
        logger.debug("Fetching all timers")
        return self.db.query(TimerDB).all()

    def get_timer(self, timer_id: UUID) -> Optional[TimerDB]:
        """Get a specific timer by ID"""
        logger.debug(f"Fetching timer with ID: {timer_id}")
        return self.db.query(TimerDB).filter(TimerDB.id == str(timer_id)).first()

    def create_timer(self, timer: TimerCreate) -> TimerDB:
        """Create a new timer"""
        logger.info(f"Creating new timer: {timer.name}")
        
        # Validate duration
        if timer.duration <= 0:
            raise ValueError("Timer duration must be greater than 0 seconds")
        
        db_timer = TimerDB(
            name=timer.name,
            duration=timer.duration
        )
        self.db.add(db_timer)
        self.db.commit()
        self.db.refresh(db_timer)
        logger.info(f"Created timer with ID: {db_timer.id}")
        return db_timer

    def update_timer(self, timer_id: UUID, timer: TimerCreate) -> Optional[TimerDB]:
        """Update an existing timer"""
        logger.info(f"Updating timer with ID: {timer_id}")
        db_timer = self.get_timer(timer_id)
        if db_timer is None:
            logger.warning(f"Timer with ID {timer_id} not found")
            return None
        
        # Validate duration
        if timer.duration <= 0:
            raise ValueError("Timer duration must be greater than 0 seconds")
        
        db_timer.name = timer.name
        db_timer.duration = timer.duration
        
        self.db.commit()
        self.db.refresh(db_timer)
        logger.info(f"Updated timer with ID: {timer_id}")
        return db_timer

    def delete_timer(self, timer_id: UUID) -> bool:
        """Delete a timer"""
        logger.info(f"Deleting timer with ID: {timer_id}")
        db_timer = self.get_timer(timer_id)
        if db_timer is None:
            logger.warning(f"Timer with ID {timer_id} not found")
            return False
        
        self.db.delete(db_timer)
        self.db.commit()
        logger.info(f"Deleted timer with ID: {timer_id}")
        return True 