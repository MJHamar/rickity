from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from datetime import datetime
import uuid

from database.database import Base

class Habit(Base):
    __tablename__ = "habits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    recurrence = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    habit_id = Column(String, ForeignKey("habits.id"), nullable=False)
    due_date = Column(DateTime, nullable=False)

class HabitDuration(Base):
    __tablename__ = "habit_durations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    habit_id = Column(String, ForeignKey("habits.id"), nullable=False)
    type = Column(String, nullable=False)  # 'minutes' or 'count'
    amount = Column(String, nullable=False)  # Storing as string for flexibility

class HabitLogDuration(Base):
    __tablename__ = "habit_log_durations"
    
    habit_log_id = Column(String, ForeignKey("habit_logs.id"), primary_key=True)
    duration_id = Column(String, ForeignKey("habit_durations.id"), primary_key=True)
    amount = Column(String, nullable=False) 