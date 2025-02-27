from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class HabitBase(BaseModel):
    name: str
    recurrence: str

class HabitCreate(HabitBase):
    pass

class Habit(HabitBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class HabitLog(BaseModel):
    id: UUID
    habit_id: UUID
    due_date: datetime
    completed: bool

    class Config:
        from_attributes = True

class HabitWithLog(BaseModel):
    habit: Habit
    latest_log: Optional[HabitLog] = None

    class Config:
        from_attributes = True 