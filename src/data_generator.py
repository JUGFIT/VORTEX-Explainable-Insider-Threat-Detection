import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import os
import random
import sys # <-- NEW: Import sys for path modification

# --- PATH CORRECTION FOR LOCAL MODULES ---
# This block is essential because config.py is in the parent directory (project root)
# and python running from a subdirectory needs to know where to find it.
try:
    # Get the directory of the current script (src/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Add the project root directory (parent of src/) to the system path
    project_root = os.path.join(current_dir, '..')
    if project_root not in sys.path:
        sys.path.append(project_root)
except NameError:
    # Handle cases where __file__ is not defined (e.g., in an interactive session)
    pass
# --- END PATH CORRECTION ---


# Import configuration constants (Now should find config.py)
from config import (
    NUM_USERS, NUM_DAYS, BASE_EVENTS_PER_DAY, ANOMALY_RATE,
    RAW_DATA_FILE, DATA_DIR, NORMAL_START_TIME, NORMAL_END_TIME
)

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def generate_synthetic_logs():
    """Generates a synthetic dataset of user security logs."""
    
    # 1. Define User IDs
    user_ids = [f"user_{i:03d}" for i in range(NUM_USERS)]
    
    # 2. Define Time Range
    start_date = datetime(2025, 1, 1)
    # The end date is determined by the number of days specified in config
    # end_date = start_date + timedelta(days=NUM_DAYS) # Not strictly needed here
    
    all_events = []
    
    print(f"Generating data for {NUM_USERS} users over {NUM_DAYS} days...")

    # --- Data Generation Loop ---
    for user_id in user_ids:
        # Simulate a personalized baseline (e.g., slightly higher/lower file access)
        user_baseline_events = int(np.random.normal(BASE_EVENTS_PER_DAY, 1))

        for day in range(NUM_DAYS):
            current_date = start_date + timedelta(days=day)
            
            # Use random variation for event count based on user baseline
            num_events = int(np.random.normal(user_baseline_events, 2))
            
            for _ in range(max(1, num_events)):
                # Determine if this event should be an anomaly
                is_anomaly = random.random() < ANOMALY_RATE
                
                # --- Timestamp Generation ---
                if is_anomaly:
                    # Anomaly: Time outside normal hours (e.g., 8 PM to 7 AM)
                    if random.random() < 0.7:
                        # Deep night window
                        hour = random.choice(list(range(20, 24)) + list(range(0, 7)))
                    else:
                        # Immediate post-work/pre-work unusual time
                        hour = random.choice(list(range(7, 8)) + list(range(18, 20)))
                else:
                    # Normal: Time within normal hours
                    hour = random.randint(NORMAL_START_TIME.hour, NORMAL_END_TIME.hour)
                
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                timestamp = current_date.replace(hour=hour, minute=minute, second=second)
                
                # --- Behavior Feature Generation ---
                event = {
                    'event_id': f"{user_id}_{timestamp.timestamp()}", # Unique ID for later lookup
                    'timestamp': timestamp,
                    'user_id': user_id,
                    'file_access_count': 0,
                    'sensitive_file_access': 0,
                    'upload_size_mb': 0.0,
                    'external_ip_connection': 0,
                    'is_unusual_login': 0,
                    'privilege_escalation': 0,
                    'admin_action': 0,
                    'anomaly_flag_truth': 0 # Use a clear name for the ground truth label
                }
                
                if is_anomaly:
                    # Scenario 1: Data Exfiltration (High upload + Sensitive access)
                    if random.random() < 0.4:
                        event['file_access_count'] = random.randint(20, 50) 
                        event['sensitive_file_access'] = 1                 
                        event['upload_size_mb'] = np.random.uniform(500, 2000) 
                        event['anomaly_flag_truth'] = 1
                    
                    # Scenario 2: System Reconnaissance (High activity outside hours)
                    elif random.random() < 0.7:
                        # Keep time unusual (from timestamp logic) but activity high
                        event['file_access_count'] = random.randint(30, 80) 
                        event['upload_size_mb'] = np.random.uniform(0.1, 5)    
                        event['anomaly_flag_truth'] = 1

                    # Scenario 3: External Access
                    else:
                        event['external_ip_connection'] = 1
                        event['upload_size_mb'] = np.random.uniform(10, 50)
                        event['anomaly_flag_truth'] = 1
                
                # Normal behavior logic 
                else:
                    event['file_access_count'] = random.randint(1, 10)
                    event['upload_size_mb'] = np.random.uniform(0.1, 5)
                    event['external_ip_connection'] = random.choice([0, 0, 0, 1])
                
                all_events.append(event)
    
    # Create DataFrame and save
    # Convert to pandas DataFrame, sort chronologically, and reset index
    df = pd.DataFrame(all_events).sort_values(by='timestamp').reset_index(drop=True)
    
    # Save the file
    df.to_csv(RAW_DATA_FILE, index=False)
    
    total_events = len(df)
    actual_anomalies = df['anomaly_flag_truth'].sum()
    print("-" * 50)
    print(f"✅ Data Generation Complete.")
    print(f"Total events generated: {total_events}")
    print(f"Injected anomalies: {actual_anomalies} ({actual_anomalies/total_events:.2%})")
    print(f"File saved to: {RAW_DATA_FILE}")
    print("-" * 50)
    
if __name__ == "__main__":
    generate_synthetic_logs()