from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List

class HabitDurationBase(BaseModel):
    type: str
    amount: str

class HabitDurationCreate(HabitDurationBase):
    pass

class HabitDuration(HabitDurationBase):
    id: UUID
    habit_id: UUID

    class Config:
        from_attributes = True

class HabitLogDuration(BaseModel):
    duration_id: UUID
    amount: str

    class Config:
        from_attributes = True 

class HabitBase(BaseModel):
    name: str
    recurrence: str

class HabitCreate(HabitBase):
    pass

class Habit(HabitBase):
    id: UUID
    created_at: datetime
    duration: Optional[HabitDuration] = None

    class Config:
        from_attributes = True

class HabitLog(BaseModel):
    id: UUID
    habit_id: UUID
    due_date: datetime
    completed: bool
    durations: List[HabitLogDuration] = []

    class Config:
        from_attributes = True

class HabitWithLog(BaseModel):
    habit: Habit
    latest_log: Optional[HabitLog] = None

    class Config:
        from_attributes = True
