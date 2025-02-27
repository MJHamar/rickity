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

from timer.routes import router as timer_router

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

# Timer endpoints
from timer.database.database import get_db as get_timer_db, Base as TimerBase, engine as timer_engine
from timer.models import Timer, TimerCreate, TimerInstance
from timer.repositories.timer_repository import TimerRepository
from timer.repositories.timer_instance_repository import TimerInstanceRepository

# Create timer tables
TimerBase.metadata.create_all(bind=timer_engine)
logger.info("Timer database tables created")

@app.get("/timer", response_model=List[Timer])
def get_timers(db: Session = Depends(get_timer_db)):
    logger.info("Fetching all timers")
    repo = TimerRepository(db)
    return repo.get_timers()

@app.post("/timer", response_model=Timer)
def create_timer(timer: TimerCreate, db: Session = Depends(get_timer_db)):
    logger.info(f"Creating new timer: {timer.name}")
    repo = TimerRepository(db)
    try:
        new_timer = repo.create_timer(timer)
        return new_timer
    except ValueError as e:
        logger.warning(f"Invalid timer data: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.get("/timer/{timer_id}", response_model=List[TimerInstance])
def get_timer_instances(timer_id: UUID, db: Session = Depends(get_timer_db)):
    logger.info(f"Fetching instances for timer: {timer_id}")
    repo = TimerInstanceRepository(db)
    return repo.get_timer_instances(timer_id)

@app.put("/timer/start/{timer_id}", response_model=TimerInstance)
def start_timer(timer_id: UUID, db: Session = Depends(get_timer_db)):
    logger.info(f"Starting timer: {timer_id}")
    repo = TimerInstanceRepository(db)
    try:
        timer_instance = repo.create_timer_instance(timer_id)
        return timer_instance
    except ValueError as e:
        logger.warning(f"Error starting timer: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@app.put("/timer/pause/{timer_instance_id}", response_model=TimerInstance)
def pause_timer(timer_instance_id: UUID, db: Session = Depends(get_timer_db)):
    logger.info(f"Pausing timer instance: {timer_instance_id}")
    repo = TimerInstanceRepository(db)
    try:
        timer_instance = repo.pause_timer_instance(timer_instance_id)
        if timer_instance is None:
            raise HTTPException(status_code=404, detail="Timer instance not found")
        return timer_instance
    except ValueError as e:
        logger.warning(f"Error pausing timer: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# Add the timer router to the main app
app.include_router(timer_router, prefix="/timer", tags=["timer"]) 