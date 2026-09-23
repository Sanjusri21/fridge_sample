"""
Database initialization and session management.
Uses SQLite for local storage.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import settings, logger
from app.database.models import Base

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Creates database tables if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully at %s", settings.DATABASE_URL)
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise


def get_db():
    """FastAPI dependency to yield database sessions."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
