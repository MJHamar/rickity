from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from uuid import UUID
from fastapi.middleware.cors import CORSMiddleware

from habits.database.database import get_db, Base, engine
from habits.models import Habit, HabitCreate, HabitLog, HabitWithLog
from habits.repositories.habit_repository import HabitRepository
from habits.repositories.habit_log_repository import HabitLogRepository
from utils.logging import setup_logger

logger = setup_logger(__name__)

app = FastAPI()

# Add this before your route definitions
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://34.118.115.23",     # Production frontend
        "http://localhost:3000",     # Local development
        "http://127.0.0.1:3000"     # Local development alternative
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
logger.info("Database tables created")

@app.get("/habits", response_model=List[Habit])
def get_habits(db: Session = Depends(get_db)):
    logger.info("Fetching all habits")
    repo = HabitRepository(db)
    return repo.get_habits()

@app.post("/habits", response_model=Habit)
def create_habit(habit: HabitCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new habit: {habit.name}")
    repo = HabitRepository(db)
    try:
        new_habit = repo.create_habit(habit)
        logger.info("Creating initial habit logs")
        repo.create_due_habit_logs()
        return new_habit
    except ValueError as e:
        logger.warning(f"Invalid habit data: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.put("/habits/{habit_id}", response_model=Habit)
def update_habit(habit_id: UUID, habit: HabitCreate, db: Session = Depends(get_db)):
    repo = HabitRepository(db)
    try:
        db_habit = repo.update_habit(habit_id, habit)
        if db_habit is None:
            raise HTTPException(status_code=404, detail="Habit not found")
        return db_habit
    except ValueError as e:
        logger.warning(f"Invalid habit data for update: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.delete("/habits/{habit_id}")
def delete_habit(habit_id: UUID, db: Session = Depends(get_db)):
    repo = HabitRepository(db)
    if not repo.delete_habit(habit_id):
        raise HTTPException(status_code=404, detail="Habit not found")
    return {"status": "success"}

@app.get("/habits/due", response_model=List[HabitWithLog])
def get_due_habits(date: str, db: Session = Depends(get_db)):
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    repo = HabitLogRepository(db)
    return repo.get_due_habits(parsed_date)

@app.get("/habits/due/today", response_model=List[HabitWithLog])
def get_due_habits_today(db: Session = Depends(get_db)):
    repo = HabitLogRepository(db)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return repo.get_due_habits(today)

@app.put("/habits/check/{log_id}")
def complete_habit(log_id: UUID, db: Session = Depends(get_db)):
    repo = HabitLogRepository(db)
    if not repo.complete_habit_log(log_id):
        raise HTTPException(status_code=404, detail="Habit log not found")
    return {"status": "success"}

@app.put("/habits/uncheck/{log_id}")
def uncomplete_habit(log_id: UUID, db: Session = Depends(get_db)):
    repo = HabitLogRepository(db)
    if not repo.uncomplete_habit_log(log_id):
        raise HTTPException(status_code=404, detail="Habit log not found")
    return {"status": "success"} 