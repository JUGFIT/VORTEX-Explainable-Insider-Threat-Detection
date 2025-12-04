import os
from datetime import time

# --- Corrected Base Directories ---
# ROOT_DIR is the directory containing config.py, which is the VORTEX project root.
# os.path.abspath(__file__) resolves the path of config.py itself.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) 
DATA_DIR = os.path.join(ROOT_DIR, 'data')
MODEL_DIR = os.path.join(ROOT_DIR, 'models')

# --- Data Generation Parameters (Week 1 Focus) ---
NUM_USERS = 50           # Number of unique users to simulate
NUM_DAYS = 30            # Number of days of data to generate
BASE_EVENTS_PER_DAY = 15 # Average number of normal events per user per day
ANOMALY_RATE = 0.03      # Target percentage of events that should be anomalies (3%)

# --- File Paths ---
RAW_DATA_FILE = os.path.join(DATA_DIR, 'raw_behavior_logs.csv')
PROCESSED_DATA_FILE = os.path.join(DATA_DIR, 'processed_features.csv')
MODEL_FILE = os.path.join(MODEL_DIR, 'isolation_forest_model.pkl')

# --- Feature Engineering Parameters (Future Use) ---
TIME_WINDOW_HOURS = 24  # For aggregating features (e.g., total files accessed in 24h)

# --- Normal Behavior Profile ---
# Define a "normal" working hour window (8 AM to 6 PM IST)
NORMAL_START_TIME = time(8, 0, 0)
NORMAL_END_TIME = time(18, 0, 0)