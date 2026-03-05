"""
VORTEX SQLite Database Layer

Uses a flexible approach: stores ALL columns from the processed_features.csv
into SQLite so that any downstream consumer (SHAP explainer, managers, etc.)
always gets the full column set it expects.
"""

import os
import sys
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
try:
    _current = Path(__file__).resolve().parent
    _root = _current.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
except NameError:
    _root = Path.cwd()

# ---------------------------------------------------------------------------
# Engine / Session setup
# ---------------------------------------------------------------------------
try:
    from config import DB_FILE
except ImportError:
    DB_FILE = str(_root / "data" / "vortex.db")

DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,
)

SessionLocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# ORM Base (kept for compatibility)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Helper: create all tables (creates nothing — tables are created via Pandas
# to_sql in the migration script, preserving all CSV columns dynamically)
# ---------------------------------------------------------------------------
def create_tables() -> None:
    """No-op — tables are created dynamically by the migration script via Pandas to_sql."""
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency: yields a DB session and closes it after the request
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Convenience: load events table into Pandas DataFrame (drop-in replacement
# for pd.read_csv — same column structure because ALL csv columns are stored)
# ---------------------------------------------------------------------------
def load_events_as_dataframe():
    """
    Returns a Pandas DataFrame of all events, with ALL original columns from
    processed_features.csv (including z-score, rolling averages, etc.).
    """
    import pandas as pd
    with engine.connect() as conn:
        df = pd.read_sql_table("events", conn)
    return df


# ---------------------------------------------------------------------------
# Check if both required tables exist
# ---------------------------------------------------------------------------
def tables_exist() -> bool:
    """Returns True if the events table exists and has rows."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM events")).scalar()
            return result > 0
    except Exception:
        return False


if __name__ == "__main__":
    if tables_exist():
        print(f"✅ Database exists at: {DB_FILE}")
    else:
        print(f"⚠️  Database not yet populated. Run: python -m src.migrate")
