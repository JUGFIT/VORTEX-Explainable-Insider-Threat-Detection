import pandas as pd
import numpy as np
import os
import sys
from scipy.stats import zscore # For normalizing features

# --- PATH CORRECTION ---
# This block ensures the script can reliably import config.py from the project root.
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    if project_root not in sys.path:
        sys.path.append(project_root)
except NameError:
    pass
# --- END PATH CORRECTION ---

# Import configuration constants
from config import (
    RAW_DATA_FILE, PROCESSED_DATA_FILE,
    TIME_WINDOW_HOURS, NORMAL_START_TIME, NORMAL_END_TIME
)


def create_temporal_features(df):
    """
    Extracts time-based features crucial for detecting anomalous usage times.
    """
    print("-> Creating temporal features...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Simple Temporal Features
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek # Monday=0, Sunday=6
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)

    # Complex Temporal/Contextual Feature: Is the event outside of standard working hours?
    def check_working_hours(ts):
        current_time = ts.time()
        
        # Check if the time is between NORMAL_START_TIME and NORMAL_END_TIME
        if NORMAL_START_TIME <= NORMAL_END_TIME:
            return 1 if NORMAL_START_TIME <= current_time <= NORMAL_END_TIME else 0
        else: # Handles overnight shifts (e.g., 22:00 to 06:00)
            return 1 if NORMAL_START_TIME <= current_time or current_time <= NORMAL_END_TIME else 0

    df['is_working_hours'] = df['timestamp'].apply(check_working_hours)
    # The anomaly is more likely if the event is NOT during working hours
    df['is_off_hours'] = 1 - df['is_working_hours']
    
    # Features for cyclical patterns
    df['sin_hour'] = np.sin(2 * np.pi * df['hour_of_day'] / 24)
    df['cos_hour'] = np.cos(2 * np.pi * df['hour_of_day'] / 24)

    return df.drop(columns=['is_working_hours'])


def create_aggregated_features(df):
    """
    Creates contextual features by aggregating user behavior over a rolling time window.
    This helps detect sudden spikes relative to the user's typical activity (a local anomaly).
    """
    print(f"-> Creating aggregated features over {TIME_WINDOW_HOURS}h window...")

    # Ensure data is sorted for rolling calculations
    df = df.sort_values(by=['user_id', 'timestamp']).reset_index(drop=True)

    # Define the rolling window size
    window = f'{TIME_WINDOW_HOURS}h'

    # Group by user_id
    grouped = df.groupby('user_id', group_keys=False)

    # Function to apply rolling calculation efficiently
    def apply_rolling(group):
        # Set timestamp as index for rolling function
        group = group.set_index('timestamp')

        # Rolling Sum: Total files accessed in the last X hours
        group['total_files_24h'] = group['file_access_count'].rolling(window=window, closed='left').sum().fillna(0)

        # Rolling Mean: Average upload size in the last X hours
        group['avg_upload_24h'] = group['upload_size_mb'].rolling(window=window, closed='left').mean().fillna(0)

        # Rolling Count: Number of events in the last X hours
        group['event_count_24h'] = group.index.to_series().rolling(window=window, closed='left').count().fillna(0)
        
        # Reset index before returning
        return group.reset_index()

    # Apply rolling calculations across all user groups
    df = grouped.apply(apply_rolling)

    return df


def normalize_features(df):
    """
    Applies Z-Score normalization to continuous features.
    This is essential for Isolation Forest as it improves performance when features have different scales.
    """
    print("-> Applying Z-Score normalization...")

    # Identify numerical features to scale (excluding IDs, flags, and sin/cos features which are already scaled/encoded)
    features_to_scale = [
        'file_access_count', 'upload_size_mb', 'total_files_24h', 
        'avg_upload_24h', 'event_count_24h'
    ]
    
    # Apply Z-score normalization
    for feature in features_to_scale:
        # We handle NaN/Inf values that might appear due to zscore on constant arrays
        df[f'{feature}_zscore'] = zscore(df[feature].replace([np.inf, -np.inf], np.nan).fillna(0))

    # Drop the original unscaled feature columns
    df = df.drop(columns=features_to_scale)

    return df


def feature_engineering_pipeline():
    """
    Main pipeline to load raw data, engineer features, and save the final dataset.
    """
    if not os.path.exists(RAW_DATA_FILE):
        print(f"ERROR: Raw data file not found at {RAW_DATA_FILE}")
        print("Please ensure you run 'python src/data_generator.py' with the corrected config.py first.")
        return

    print(f"Loading raw data from: {RAW_DATA_FILE}")
    # Use 'low_memory=False' for potentially large synthetic datasets
    df = pd.read_csv(RAW_DATA_FILE, low_memory=False)

    # --- Step 1: Temporal Feature Creation ---
    df = create_temporal_features(df)
    
    # --- Step 2: Aggregation Feature Creation ---
    df = create_aggregated_features(df)
    
    # --- Step 3: Feature Normalization ---
    df = normalize_features(df)

    # --- Step 4: Final Cleanup and Save ---
    
    # Identify the feature columns used for ML training
    # Exclude IDs, timestamp, and the ground truth label
    ml_features = [
        col for col in df.columns 
        if col not in ['event_id', 'timestamp', 'user_id', 'anomaly_flag_truth']
    ]

    # Final DataFrame for saving (keep key identifiers for later SHAP/API lookups)
    df_processed = df[['event_id', 'timestamp', 'user_id', 'anomaly_flag_truth'] + ml_features].copy()
    
    # Save the processed data
    df_processed.to_csv(PROCESSED_DATA_FILE, index=False)
    
    print("-" * 50)
    print("✅ Feature Engineering Complete.")
    print(f"Processed dataset shape: {df_processed.shape}")
    print(f"Processed features saved to: {PROCESSED_DATA_FILE}")
    print("-" * 50)
    
if __name__ == "__main__":
    feature_engineering_pipeline()