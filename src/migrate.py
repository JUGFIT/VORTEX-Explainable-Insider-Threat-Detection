"""
VORTEX SQLite Migration Script
================================
Reads the existing CSV files and imports them into the SQLite database,
preserving ALL columns so that downstream consumers (SHAP explainer, etc.)
continue to work without modification.

Usage (one-time):
    python -m src.migrate

Safe to re-run: drops and re-creates the tables cleanly each time.
"""

import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
try:
    from config import PROCESSED_DATA_FILE, RAW_DATA_FILE, DB_FILE
except ImportError:
    from config import PROCESSED_DATA_FILE, RAW_DATA_FILE
    DB_FILE = str(_root / "data" / "vortex.db")

from src.database import engine


# ---------------------------------------------------------------------------
# Migration: processed_features → events table (ALL columns preserved)
# ---------------------------------------------------------------------------
def migrate_events() -> int:
    """Import ALL columns from processed_features.csv → events table."""
    if not os.path.exists(PROCESSED_DATA_FILE):
        print(f"  ⚠️  Processed features not found: {PROCESSED_DATA_FILE}")
        return 0

    print(f"  Loading {PROCESSED_DATA_FILE} ...")
    df = pd.read_csv(PROCESSED_DATA_FILE, low_memory=False)

    # Add risk_level if not present (matches main.py logic)
    if "risk_level" not in df.columns:
        q_low      = df["anomaly_score"].quantile(0.80)
        q_high     = df["anomaly_score"].quantile(0.95)
        q_critical = df["anomaly_score"].quantile(0.99)

        def _cat(score):
            if score >= q_critical: return "Critical"
            elif score >= q_high:   return "High"
            elif score >= q_low:    return "Medium"
            return "Low"

        df["risk_level"] = df["anomaly_score"].apply(_cat)

    print(f"  Writing {len(df):,} rows × {len(df.columns)} columns to SQLite ...")
    df.to_sql(
        "events",
        con=engine,
        if_exists="replace",   # Drop + recreate so all columns are always in sync
        index=False,
        chunksize=1000,
    )
    print(f"  ✅ events table written.")
    return len(df)


# ---------------------------------------------------------------------------
# Migration: raw_behavior_logs → raw_events table
# ---------------------------------------------------------------------------
def migrate_raw_events() -> int:
    """Import raw_behavior_logs.csv → raw_events table."""
    if not os.path.exists(RAW_DATA_FILE):
        print(f"  ⚠️  Raw data not found: {RAW_DATA_FILE}")
        return 0

    print(f"  Loading {RAW_DATA_FILE} ...")
    df = pd.read_csv(RAW_DATA_FILE, low_memory=False)
    print(f"  Writing {len(df):,} rows to SQLite ...")
    df.to_sql(
        "raw_events",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=5000,
        method="multi",
    )
    print(f"  ✅ raw_events table written.")
    return len(df)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run_migration():
    print("=" * 60)
    print("  VORTEX → SQLite Migration")
    print("=" * 60)
    print(f"  Target DB : {DB_FILE}\n")

    t_start = time.time()

    print("[1/2] Migrating processed events (ALL columns) ...")
    n_events = migrate_events()
    print()

    print("[2/2] Migrating raw events ...")
    n_raw = migrate_raw_events()

    elapsed = time.time() - t_start
    print()
    print("=" * 60)
    print(f"  ✅ Migration complete in {elapsed:.1f}s")
    print(f"     events table      : {n_events:,} rows")
    print(f"     raw_events table  : {n_raw:,} rows")
    print(f"     Database file     : {DB_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()
