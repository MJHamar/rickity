from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from uuid import UUID
from typing import List, Optional
from sqlalchemy import func
from utils.logging import setup_logger
from utils.date_utils import parse_recurrence, end_of_day
from database.models import Habit, HabitLog, HabitDuration, HabitLogDuration
from models import HabitWithLog

logger = setup_logger(__name__)

class HabitLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def calculate_next_due_date(self, habit: Habit, reference_date: datetime) -> datetime:
        """Calculate the next due date based on habit recurrence"""
        logger.debug(f"Calculating next due date for habit {habit.id} from reference date {reference_date}")
        recurrence_delta = parse_recurrence(habit.recurrence)
        # Set the due date to end of the day
        next_due = end_of_day(reference_date + recurrence_delta)
        logger.debug(f"Next due date calculated: {next_due}")
        return next_due

    def get_latest_log(self, habit_id: str) -> Optional[HabitLog]:
        """Get the latest log for a habit based on due_date"""
        return (self.db.query(HabitLog)
                .filter(HabitLog.habit_id == habit_id)
                .order_by(HabitLog.due_date.desc())
                .first())

    def create_due_logs(self, habit: Habit, current_date: datetime) -> List[HabitLog]:
        """Create all necessary logs until current_date"""
        new_logs = []
        latest_log = self.get_latest_log(habit.id)
        
        # If no logs exist, start from habit creation date
        if not latest_log:
            # For first log, use end of creation day as reference
            next_due = self.calculate_next_due_date(habit, habit.created_at)
        else:
            next_due = self.calculate_next_due_date(habit, latest_log.due_date)

        # Create logs until we reach a future date
        current_eod = end_of_day(current_date)  # Compare with end of current day
        while next_due <= current_eod:
            logger.debug(f"Creating log for habit {habit.id} due at {next_due}")
            new_log = HabitLog(
                habit_id=habit.id,
                due_date=next_due,
                completed=False
            )
            new_logs.append(new_log)
            next_due = self.calculate_next_due_date(habit, next_due)

        if new_logs:
            self.db.bulk_save_objects(new_logs)
            self.db.commit()

        return new_logs

    def get_due_habits(self, date: datetime) -> List[HabitWithLog]:
        """Get habits with their most relevant log for the given date"""
        logger.debug(f"Fetching habits due on {date}")
        
        habits = self.db.query(Habit).all()
        habits_with_logs = []

        for habit in habits:
            # Get or create logs up to the query date
            self.create_due_logs(habit, date)
            
            # Get the most relevant log (first log with due_date >= today)
            date_eod = end_of_day(date)
            relevant_log = (self.db.query(HabitLog)
                          .filter(HabitLog.habit_id == habit.id,
                                 HabitLog.due_date <= date_eod)
                          .order_by(HabitLog.due_date.desc())
                          .first())
            
            if relevant_log:
                # Get associated durations
                durations = self.db.query(HabitLogDuration).filter(
                    HabitLogDuration.habit_log_id == relevant_log.id
                ).all()
                
                habits_with_logs.append(HabitWithLog(
                    habit=habit,
                    latest_log=relevant_log,
                    durations=[HabitLogDuration.from_orm(d) for d in durations]
                ))

        return habits_with_logs

    def create_habit_log(self, habit_id: UUID, date: datetime) -> HabitLog:
        logger.info(f"Creating habit log for habit {habit_id} on {date}")
        db_log = HabitLog(
            habit_id=habit_id,
            due_date=date,
            completed=False
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        logger.info(f"Created habit log with ID: {db_log.id}")
        return db_log

    def add_log_duration(self, log_id: UUID, amount: str) -> bool:
        logger.info(f"Adding duration to log {log_id}")
        log_id_str = str(log_id)
        db_log = self.db.query(HabitLog).filter(HabitLog.id == log_id_str).first()
        
        if db_log:
            # Get the habit's duration
            duration = self.db.query(HabitDuration).filter(
                HabitDuration.habit_id == db_log.habit_id
            ).first()
            
            if duration:
                log_duration = HabitLogDuration(
                    habit_log_id=log_id_str,
                    duration_id=duration.id,
                    amount=str(amount)
                )
                self.db.add(log_duration)
                self.db.commit()
                return True
        return False

    def remove_log_duration(self, duration_id: UUID) -> bool:
        logger.info(f"Removing log duration {duration_id}")
        duration_id_str = str(duration_id)
        db_duration = self.db.query(HabitLogDuration).filter(
            HabitLogDuration.id == duration_id_str
        ).first()
        
        if db_duration:
            self.db.delete(db_duration)
            self.db.commit()
            return True
        return False