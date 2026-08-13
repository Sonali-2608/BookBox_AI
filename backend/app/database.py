"""
SQLAlchemy engine, session factory, and declarative Base.

Uses PostgreSQL in production (DATABASE_URL from settings). SQLite is
supported transparently for local testing (see tests/conftest.py).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # Needed so the same SQLite connection can be reused across threads
    # in FastAPI's threadpool during tests.
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
