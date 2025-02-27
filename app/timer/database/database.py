from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from utils.logging import setup_logger

logger = setup_logger(__name__)

SQLALCHEMY_DATABASE_URL = "sqlite:///./timer.db"

logger.info(f"Initializing timer database connection: {SQLALCHEMY_DATABASE_URL}")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    logger.debug("Creating new timer database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing timer database session")
        db.close() 