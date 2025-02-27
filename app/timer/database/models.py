from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from datetime import datetime
import uuid
import enum

# We no longer define the models here, they are defined in timer.models
# This file is kept for backward compatibility but doesn't define any models
from timer.database.database import Base

# We'll leave this here for reference
class TimerStatus(enum.Enum):
    STARTED = "started"
    PAUSED = "paused"
    ENDED = "ended" 