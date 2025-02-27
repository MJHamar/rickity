from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from typing import List, Optional

from utils.logging import setup_logger
from timer.database.models import Timer, TimerInstance, TimerStatus
from timer.models import TimerCreate, TimerInstanceDB, TimerDB
from timer.repositories.timer_repository import TimerRepository

logger = setup_logger(__name__)

class TimerInstanceRepository:
    def __init__(self, db: Session):
        self.db = db
        self.timer_repo = TimerRepository(db)

    def get_timer_instances(self, timer_id: UUID) -> List[TimerInstanceDB]:
        """Get all instances for a specific timer"""
        logger.debug(f"Fetching all instances for timer with ID: {timer_id}")
        return self.db.query(TimerInstanceDB).filter(TimerInstanceDB.timer_id == str(timer_id)).all()

    def get_timer_instance(self, instance_id: UUID) -> Optional[TimerInstanceDB]:
        """Get a specific timer instance by ID"""
        logger.debug(f"Fetching timer instance with ID: {instance_id}")
        return self.db.query(TimerInstanceDB).filter(TimerInstanceDB.id == str(instance_id)).first()

    def create_timer_instance(self, timer_id: UUID) -> TimerInstanceDB:
        """Create a new timer instance"""
        logger.info(f"Creating new timer instance for timer ID: {timer_id}")
        
        timer = self.timer_repo.get_timer(timer_id)
        if timer is None:
            logger.warning(f"Timer with ID {timer_id} not found")
            raise ValueError(f"Timer with ID {timer_id} not found")
        
        instance = TimerInstanceDB(
            timer_id=str(timer_id),
            status="started",
            created_at=datetime.utcnow(),
            paused_at=None
        )
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        logger.info(f"Created timer instance with ID: {instance.id}")
        return instance

    def pause_timer_instance(self, instance_id: UUID) -> Optional[TimerInstanceDB]:
        """Pause a timer instance"""
        logger.info(f"Pausing timer instance with ID: {instance_id}")
        instance = self.get_timer_instance(instance_id)
        if instance is None:
            logger.warning(f"Timer instance with ID {instance_id} not found")
            return None
        
        # Check if the instance is already paused or ended
        if instance.status != "started":
            logger.warning(f"Cannot pause timer instance with ID {instance_id} because it is not in 'started' state")
            raise ValueError(f"Cannot pause timer instance with ID {instance_id} because it is not in 'started' state")
        
        instance.status = "paused"
        instance.paused_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(instance)
        logger.info(f"Paused timer instance with ID: {instance_id}")
        return instance

    def resume_timer_instance(self, instance_id: UUID) -> Optional[TimerInstanceDB]:
        """Resume a paused timer instance"""
        logger.info(f"Resuming timer instance with ID: {instance_id}")
        instance = self.get_timer_instance(instance_id)
        if instance is None:
            logger.warning(f"Timer instance with ID {instance_id} not found")
            return None
        
        # Check if the instance is paused
        if instance.status != "paused":
            logger.warning(f"Cannot resume timer instance with ID {instance_id} because it is not in 'paused' state")
            raise ValueError(f"Cannot resume timer instance with ID {instance_id} because it is not in 'paused' state")
        
        instance.status = "started"
        # Keep paused_at for reference of the last time it was paused
        
        self.db.commit()
        self.db.refresh(instance)
        logger.info(f"Resumed timer instance with ID: {instance_id}")
        return instance

    def end_timer_instance(self, instance_id: UUID) -> Optional[TimerInstanceDB]:
        """End a timer instance"""
        logger.info(f"Ending timer instance with ID: {instance_id}")
        instance = self.get_timer_instance(instance_id)
        if instance is None:
            logger.warning(f"Timer instance with ID {instance_id} not found")
            return None
        
        # Check if the instance is already ended
        if instance.status == "ended":
            logger.warning(f"Timer instance with ID {instance_id} is already ended")
            return instance
        
        instance.status = "ended"
        
        self.db.commit()
        self.db.refresh(instance)
        logger.info(f"Ended timer instance with ID: {instance_id}")
        return instance 