from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from datetime import datetime
import uuid
import enum

from timer.database.database import Base

class TimerStatus(enum.Enum):
    STARTED = "started"
    PAUSED = "paused"
    ENDED = "ended"

class Timer(Base):
    __tablename__ = "timers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in seconds

class TimerInstance(Base):
    __tablename__ = "timer_instances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timer_id = Column(String, ForeignKey("timers.id"), nullable=False)
    status = Column(String, default=TimerStatus.STARTED.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    paused_at = Column(DateTime, nullable=True) 