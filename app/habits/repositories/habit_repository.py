from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from typing import List, Optional

from utils.logging import setup_logger
from utils.date_utils import parse_recurrence
from habits.database.models import Habit, HabitLog
from habits.models import HabitCreate
from habits.repositories.habit_log_repository import HabitLogRepository

logger = setup_logger(__name__)

class HabitRepository:
    def __init__(self, db: Session):
        self.db = db

    def validate_recurrence(self, recurrence: str) -> bool:
        """Validate recurrence string by attempting to parse it"""
        try:
            parse_recurrence(recurrence)
            return True
        except ValueError as e:
            logger.warning(f"Invalid recurrence format: {recurrence}. {str(e)}")
            return False

    def get_habits(self) -> List[Habit]:
        logger.debug("Fetching all habits")
        return self.db.query(Habit).all()

    def create_habit(self, habit: HabitCreate) -> Habit:
        logger.info(f"Creating new habit: {habit.name}")
        
        # Validate recurrence format
        if not self.validate_recurrence(habit.recurrence):
            raise ValueError(
                "Invalid recurrence format. Valid formats: '7', '7 days', 'day', '1 day', 'week', '2 weeks', 'month', '2 months'"
            )
        
        db_habit = Habit(
            name=habit.name,
            recurrence=habit.recurrence
        )
        self.db.add(db_habit)
        self.db.commit()
        self.db.refresh(db_habit)
        logger.info(f"Created habit with ID: {db_habit.id}")
        return db_habit

    def get_habit(self, habit_id: UUID) -> Optional[Habit]:
        return self.db.query(Habit).filter(Habit.id == habit_id).first()

    def update_habit(self, habit_id: UUID, habit: HabitCreate) -> Optional[Habit]:
        # Validate recurrence format
        if not self.validate_recurrence(habit.recurrence):
            raise ValueError(
                "Invalid recurrence format. Valid formats: '7', '7 days', 'day', '1 day', 'week', '2 weeks', 'month', '2 months'"
            )
            
        db_habit = self.get_habit(habit_id)
        if db_habit:
            db_habit.name = habit.name
            db_habit.recurrence = habit.recurrence
            self.db.commit()
            self.db.refresh(db_habit)
        return db_habit

    def delete_habit(self, habit_id: UUID) -> bool:
        db_habit = self.get_habit(habit_id)
        if db_habit:
            self.db.delete(db_habit)
            self.db.commit()
            return True
        return False

    def create_due_habit_logs(self) -> List[HabitLog]:
        """Create initial logs for all habits"""
        logger.info("Creating due habit logs")
        habits = self.get_habits()
        now = datetime.now()
        
        log_repo = HabitLogRepository(self.db)
        all_new_logs = []
        
        for habit in habits:
            new_logs = log_repo.create_due_logs(habit, now)
            all_new_logs.extend(new_logs)
            
        return all_new_logs 