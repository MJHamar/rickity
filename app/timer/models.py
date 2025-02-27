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
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # in seconds

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
        from_attributes = True 