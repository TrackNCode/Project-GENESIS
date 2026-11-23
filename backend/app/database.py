"""Database utilities for GENESIS backend.
Creates a SQLite engine for development and a session factory.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parents[2]

# SQLite file for local dev (will be replaced by PostgreSQL in prod)
SQLITE_PATH = os.getenv("GENESIS_SQLITE_PATH", BASE_DIR / "genesis_dev.db")

engine = create_engine(f"sqlite+pysqlite:///{SQLITE_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

Base = declarative_base()

def get_db():
    """Dependency for FastAPI routes to provide a DB session.
    Usage: `db = Depends(get_db)`
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
