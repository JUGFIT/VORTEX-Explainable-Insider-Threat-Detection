import pandas as pd
import os
import requests

processed_path = r'c:\Users\offic\Documents\Code\Antigravity\VORTEX_old\VORTEX-Explainable-Insider-Threat-Detection-main\data\processed_features.csv'
raw_path = r'c:\Users\offic\Documents\Code\Antigravity\VORTEX_old\VORTEX-Explainable-Insider-Threat-Detection-main\data\raw_behavior_logs.csv'

for path in [processed_path, raw_path]:
    if os.path.exists(path):
        print(f"Loading {os.path.basename(path)}...")
        df = pd.read_csv(path, low_memory=False)
        initial_len = len(df)
        df = df[~df['event_id'].astype(str).str.startswith('sim_')]
        final_len = len(df)
        if initial_len != final_len:
            df.to_csv(path, index=False)
        print(f"Cleaned {os.path.basename(path)}: removed {initial_len - final_len} simulated rows.")
    else:
        print(f"File not found: {path}")

try:
    print("Triggering API reload...")
    resp = requests.post('http://localhost:8000/reload')
    print("API Reload status:", resp.status_code)
except Exception as e:
    print("Could not trigger API reload:", e)
