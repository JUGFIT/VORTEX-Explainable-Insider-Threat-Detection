import pandas as pd
import numpy as np
import os
import sys
import joblib # Library for saving/loading the trained model (pkl format)
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

# --- PATH CORRECTION ---
# Ensure the script can reliably import config.py from the project root.
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
    PROCESSED_DATA_FILE, MODEL_FILE, ANOMALY_RATE
)

# Define the features to be used for training the Isolation Forest model
# These are the Z-score normalized, temporal, and binary features
MODEL_FEATURES = [
    'sensitive_file_access',
    'external_ip_connection',
    'is_weekend',
    'is_off_hours',
    'sin_hour',
    'cos_hour',
    'file_access_count_zscore',
    'upload_size_mb_zscore',
    'total_files_24h_zscore',
    'avg_upload_24h_zscore',
    'event_count_24h_zscore'
]

def load_and_prepare_data(filepath):
    """Loads the processed data and separates features from metadata/labels."""
    if not os.path.exists(filepath):
        print(f"ERROR: Processed data file not found at {filepath}")
        print("Please run 'python src/feature_engineer.py' first.")
        return None, None, None

    print(f"Loading processed data from: {filepath}")
    df = pd.read_csv(filepath)

    # 1. Feature Set (X): Only include the numerical features for the model
    X = df[MODEL_FEATURES].copy()
    
    # 2. True Labels (y): The ground truth flag for evaluation (1 for anomaly, 0 for normal)
    y_true = df['anomaly_flag_truth']
    
    # Isolation Forest does not handle NaNs, fill with 0 (safe since normalization handled NaNs)
    X = X.fillna(0)

    return X, y_true, df

def train_isolation_forest(X):
    """
    Trains the Isolation Forest model, which is used for unsupervised anomaly detection.
    
    Isolation Forest outputs a score where lower values indicate anomalies (outliers).
    """
    print("-> Training Isolation Forest Model...")
    
    # Initialize the Isolation Forest model
    # contamination: This parameter estimates the proportion of outliers in the data.
    # We use the ANOMALY_RATE defined in config.py
    model = IsolationForest(
        contamination=ANOMALY_RATE,
        random_state=42, # Set for reproducibility
        n_estimators=100, # Number of base estimators (trees)
        max_features=1.0, # Use all features
        n_jobs=-1 # Use all available cores
    )

    # Train the model on the entire dataset (unsupervised learning)
    model.fit(X)
    
    return model

def evaluate_model(model, X, y_true):
    """
    Evaluates the trained Isolation Forest model against the ground truth labels.
    """
    print("-> Evaluating Model Performance...")
    
    # Isolation Forest predicts: 1 for inliers (normal), -1 for outliers (anomalies)
    y_pred_if = model.predict(X)

    # Convert the IF prediction (-1, 1) to (1, 0) format for standard metrics (1=Anomaly, 0=Normal)
    # y_pred_binary: 1 if IF predicted -1 (anomaly), 0 if IF predicted 1 (normal)
    y_pred_binary = np.where(y_pred_if == -1, 1, 0)
    
    # --- Performance Metrics ---
    # 1. AUC-ROC Score: Measures the model's ability to distinguish between classes.
    # We use the raw decision function score for a continuous probability measure.
    anomaly_scores = model.decision_function(X)
    # Decision function outputs: higher score = more normal. We invert it for AUC.
    auc_score = roc_auc_score(y_true, -anomaly_scores)
    
    # 2. Classification Report: Provides Precision, Recall, and F1-score
    report = classification_report(y_true, y_pred_binary, target_names=['Normal (0)', 'Anomaly (1)'], output_dict=True)
    
    # 3. Confusion Matrix for visibility
    cm = confusion_matrix(y_true, y_pred_binary)
    
    print("-" * 50)
    print(f"Model AUC-ROC Score: {auc_score:.4f}")
    print("--- Classification Report ---")
    print(classification_report(y_true, y_pred_binary, target_names=['Normal (0)', 'Anomaly (1)']))
    print("--- Confusion Matrix (True vs Predicted) ---")
    print(f"| TN | FP | \n| FN | TP |\n{cm}")
    print("-" * 50)
    
    # Store key metrics for documentation
    metrics = {
        'auc_roc': auc_score,
        'f1_anomaly': report['Anomaly (1)']['f1-score'],
        'precision_anomaly': report['Anomaly (1)']['precision'],
        'recall_anomaly': report['Anomaly (1)']['recall'],
        'confusion_matrix': cm.tolist()
    }
    return metrics, anomaly_scores

def save_model(model):
    """Saves the trained model using joblib."""
    # Ensure the models directory exists
    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print(f"✅ Trained Isolation Forest model saved to: {MODEL_FILE}")

def model_training_pipeline():
    """Main function to execute the model training process."""
    
    X, y_true, df_full = load_and_prepare_data(PROCESSED_DATA_FILE)
    if X is None:
        return

    # Train the model
    model = train_isolation_forest(X)
    
    # Evaluate the model
    metrics, anomaly_scores = evaluate_model(model, X, y_true)
    
    # Save the model artifact
    save_model(model)
    
    # --- Future Use: Save Scores for SHAP/API ---
    # We will save the anomaly scores back to the processed data file
    df_full['anomaly_score'] = -anomaly_scores # Invert score: Higher score = Higher risk
    df_full.to_csv(PROCESSED_DATA_FILE, index=False)
    print(f"Updated processed data with anomaly scores saved to: {PROCESSED_DATA_FILE}")

if __name__ == "__main__":
    model_training_pipeline()