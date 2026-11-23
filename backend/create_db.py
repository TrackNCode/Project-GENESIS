"""Create the development SQLite database and initial tables.
Runs SQLAlchemy metadata creation.
"""
import os
from pathlib import Path
from app.database import engine, Base

def main():
    # Ensure the directory exists
    db_path = Path(os.getenv("GENESIS_SQLITE_PATH", Path(__file__).resolve().parents[2] / "genesis_dev.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"Database created at {db_path}")

if __name__ == "__main__":
    main()
