from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from timer.database.database import Base

# SQLAlchemy Models
class SoundDB(Base):
    __tablename__ = "sounds"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    file = Column(String, nullable=False)
    
    # Relationship - one sound can be used by many timers
    timers = relationship("TimerDB", back_populates="sound")

class TimerDB(Base):
    __tablename__ = "timers"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)  # in seconds
    sound_id = Column(String, ForeignKey("sounds.id"), nullable=True)
    
    # Relationship - one timer has one sound
    sound = relationship("SoundDB", back_populates="timers")

# Pydantic Models for API
class SoundBase(BaseModel):
    name: str
    file: str

class Sound(SoundBase):
    id: UUID
    
    class Config:
        orm_mode = True
        from_attributes = True

class TimerBase(BaseModel):
    name: str
    duration: int  # in seconds
    sound_id: Optional[UUID] = None

class TimerCreate(TimerBase):
    pass

class Timer(TimerBase):
    id: UUID
    
    class Config:
        orm_mode = True
        from_attributes = True 