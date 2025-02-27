from database.database import engine, SessionLocal
from database.models import Base, Habit, HabitLog, HabitDuration, HabitLogDuration

def migrate_schema():
    """Drop completed column and create new tables"""
    db = SessionLocal()
    try:
        # Drop completed column if exists
        db.execute("""
            ALTER TABLE habit_logs 
            DROP COLUMN IF EXISTS completed
        """)
        
        # Create new tables if not exists
        Base.metadata.create_all(bind=engine, tables=[
            HabitDuration.__table__,
            HabitLogDuration.__table__
        ])
        
        db.commit()
        print("Schema migration completed")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def backfill_durations(completed_log_ids):
    """Updated to use pre-collected log IDs"""
    db = SessionLocal()
    try:
        # 1. Ensure all habits have duration
        habits = db.query(Habit).all()
        for habit in habits:
            if not habit.duration:
                db_duration = HabitDuration(
                    habit_id=habit.id,
                    type="count",
                    amount="1"
                )
                db.add(db_duration)
        
        # 2. Convert pre-collected completed logs
        for log_id in completed_log_ids:
            log = db.query(HabitLog).get(log_id)
            if not log:
                continue
                
            duration_type = log.habit.duration.type if log.habit.duration else "count"
            
            existing = db.query(HabitLogDuration).filter(
                HabitLogDuration.log_id == log_id
            ).first()
            
            if not existing:
                db_duration = HabitLogDuration(
                    log_id=log_id,
                    amount=1,
                    type=duration_type
                )
                db.add(db_duration)
        
        db.commit()
        print(f"Backfilled durations for {len(completed_log_ids)} completed logs")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    db = SessionLocal()
    try:
        # First collect completed log IDs BEFORE schema changes
        completed_log_ids = [
            log.id for log in 
            db.query(HabitLog.id)
            .filter(HabitLog.completed == True)
            .all()
        ]
    finally:
        db.close()

    print("Running schema migration...")
    migrate_schema()  # This drops the completed column
    
    print("Running data backfill...")
    backfill_durations(completed_log_ids)  # Pass the pre-collected IDs
    
    print("Migration completed successfully") 