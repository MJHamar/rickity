from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from timer.database.database import Base

# SQLAlchemy Models
class TimerDB(Base):
    __tablename__ = "timers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # in seconds
    
    instances = relationship("TimerInstanceDB", back_populates="timer", cascade="all, delete-orphan")

class TimerInstanceDB(Base):
    __tablename__ = "timer_instances"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    timer_id = Column(String, ForeignKey("timers.id"), nullable=False)
    status = Column(Enum("started", "paused", "ended", name="timer_status"), default="started")
    created_at = Column(DateTime, default=datetime.utcnow)
    paused_at = Column(DateTime, nullable=True)
    
    timer = relationship("TimerDB", back_populates="instances")

# Pydantic Models for API
class TimerBase(BaseModel):
    name: str
    duration: int  # in seconds

class TimerCreate(TimerBase):
    pass

class Timer(TimerBase):
    id: UUID
    
    class Config:
        orm_mode = True

class TimerInstanceBase(BaseModel):
    timer_id: UUID
    status: str
    created_at: datetime
    paused_at: Optional[datetime] = None

class TimerInstance(TimerInstanceBase):
    id: UUID
    
    class Config:
        orm_mode = True

class TimerWithInstances(BaseModel):
    timer: Timer
    instances: List[TimerInstance]

    class Config:
        from_attributes = True 