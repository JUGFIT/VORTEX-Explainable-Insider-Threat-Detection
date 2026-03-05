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
    
    all_events = []
    
    print(f"Generating data for {NUM_USERS} users over {NUM_DAYS} days...")

    # --- Data Generation Loop ---
    for user_id in user_ids:
        # Simulate a personalized baseline
        user_baseline_events = int(np.random.normal(BASE_EVENTS_PER_DAY, 5))
        user_baseline_events = max(10, user_baseline_events) # Consistent minimum

        for day in range(NUM_DAYS):
            current_date = start_date + timedelta(days=day)
            
            # --- High Variability Event Count ---
            # Using a mix of distributions for "spikes"
            if random.random() < 0.1: # 10% chance of a "busy day" spike
                num_events = random.randint(35, 60)
            else:
                num_events = int(np.random.normal(user_baseline_events, 4))
            
            for _ in range(max(5, num_events)):
                # Determine if this event should be "suspicious" (for off-hours/alerting)
                is_suspicious = False
                
                # --- Behavior Feature Generation (Base) ---
                event = {
                    'event_id': None, # Set later
                    'timestamp': None, # Set later
                    'user_id': user_id,
                    'file_access_count': random.randint(1, 15),
                    'sensitive_file_access': 0,
                    'upload_size_mb': random.uniform(0.1, 8.0),
                    'external_ip_connection': random.choice([0, 0, 0, 1]),
                    'is_unusual_login': 0,
                    'privilege_escalation': 0,
                    'admin_action': 0,
                    'explanation': '',
                    'anomaly_flag_truth': 0
                }

                # --- Specialized Insider Logic ---
                if user_id == "user_012": # SMART
                    # Smart user: Stealthy periodic activity
                    is_anomaly_day = (day % 15 == 0)
                    if is_anomaly_day and random.random() < 0.3:
                        event['sensitive_file_access'] = 1
                        event['file_access_count'] = random.randint(20, 30)
                        event['explanation'] = 'Discovery: Target identification in sensitive silos'
                        event['anomaly_flag_truth'] = 1
                        is_suspicious = True
                    elif day > 70 and random.random() < 0.1:
                        event['upload_size_mb'] = random.uniform(15, 25)
                        event['explanation'] = 'Action: Slow exfiltration of encrypted blobs'
                        event['anomaly_flag_truth'] = 1
                        is_suspicious = True

                elif user_id == "user_024": # AVERAGE
                    # Consistently elevated
                    if random.random() < 0.15:
                        event['file_access_count'] = random.randint(25, 45)
                        event['sensitive_file_access'] = random.choice([0, 1])
                        event['upload_size_mb'] = random.uniform(10, 30)
                        event['explanation'] = 'Average risk: Sustained elevated activity'
                        event['anomaly_flag_truth'] = 1
                        is_suspicious = True if random.random() < 0.5 else False

                elif user_id == "user_048": # DUMB
                    # High volume bursts
                    if random.random() < 0.08:
                        event['file_access_count'] = random.randint(200, 500)
                        event['sensitive_file_access'] = random.randint(10, 30)
                        event['upload_size_mb'] = random.uniform(2000, 5000)
                        event['admin_action'] = random.choice([0, 1])
                        event['explanation'] = 'Critical: Massive data exfiltration/harvesting spike'
                        event['anomaly_flag_truth'] = 1
                        is_suspicious = True

                # --- Regular User Logic (5-10% False Positive Rate) ---
                else:
                    if random.random() < 0.08: # ~8% rate
                        if random.random() < 0.6: 
                            is_suspicious = True
                            event['is_unusual_login'] = 1
                            event['explanation'] = 'Likely False Positive: Remote login during maintenance'
                        else:
                            event['upload_size_mb'] = random.uniform(50, 200)
                            event['explanation'] = 'Likely False Positive: Large legitimate cloud sync'
                        event['anomaly_flag_truth'] = 0

                # --- Final Timestamp and ID Generation ---
                if is_suspicious:
                    # Off-hours: 8 PM to 6 AM
                    hour = random.choice(list(range(20, 24)) + list(range(0, 6)))
                else:
                    # Normal: 8 AM to 6 PM
                    hour = random.randint(NORMAL_START_TIME.hour, NORMAL_END_TIME.hour)
                
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                ts = current_date.replace(hour=hour, minute=minute, second=second)
                
                event['timestamp'] = ts
                event['event_id'] = f"{user_id}_{ts.timestamp()}_{random.randint(1000, 9999)}"
                
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