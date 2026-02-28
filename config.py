"""
Basic Configuration for VORTEX
For production use, prefer config_secure.py with environment variables.
"""

import os
from datetime import time
from pathlib import Path

# --- Base Directories (Using pathlib for better cross-platform support) ---
ROOT_DIR = Path(__file__).parent.absolute()
DATA_DIR = ROOT_DIR / 'data'
MODEL_DIR = ROOT_DIR / 'models'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# --- File Paths (Convert to strings for backward compatibility) ---
RAW_DATA_FILE = str(DATA_DIR / 'raw_behavior_logs.csv')
PROCESSED_DATA_FILE = str(DATA_DIR / 'processed_features.csv')
MODEL_FILE = str(MODEL_DIR / 'isolation_forest_model.pkl')

# --- Data Generation Parameters ---
NUM_USERS = 50
NUM_DAYS = 365
BASE_EVENTS_PER_DAY = 15
ANOMALY_RATE = 0.03  # 3% anomaly rate

# --- Feature Engineering Parameters ---
TIME_WINDOW_HOURS = 24

# --- Normal Behavior Profile ---
NORMAL_START_TIME = time(8, 0, 0)
NORMAL_END_TIME = time(18, 0, 0)

# --- Model Training Parameters ---
CONTAMINATION = ANOMALY_RATE  # Alias for consistency
N_ESTIMATORS = 100
MAX_SAMPLES = 256
RANDOM_STATE = 42

# Export as strings for legacy compatibility
DATA_DIR = str(DATA_DIR)
MODEL_DIR = str(MODEL_DIR)

if __name__ == "__main__":
    print("=" * 60)
    print("VORTEX Basic Configuration")
    print("=" * 60)
    print(f"Root Directory: {ROOT_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Model Directory: {MODEL_DIR}")
    print(f"Raw Data File: {RAW_DATA_FILE}")
    print(f"Processed Data File: {PROCESSED_DATA_FILE}")
    print(f"Model File: {MODEL_FILE}")
    print(f"Anomaly Rate: {ANOMALY_RATE:.1%}")
    print("=" * 60)