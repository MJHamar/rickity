from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey
from datetime import datetime
import uuid

from habits.database.database import Base

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
    completed = Column(Boolean, default=False) 