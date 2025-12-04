import pandas as pd
import numpy as np
import os
import sys
import json
import joblib
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

# --- PATH CORRECTION ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    if project_root not in sys.path:
        sys.path.append(project_root)
except NameError:
    pass

# Import configuration (try secure config first, fallback to basic)
try:
    from config_secure import settings
    PROCESSED_DATA_FILE = str(settings.PROCESSED_DATA_FILE)
    MODEL_FILE = str(settings.MODEL_FILE)
    MODEL_DIR = str(settings.MODEL_DIR)
    ANOMALY_RATE = settings.CONTAMINATION
except ImportError:
    from config import PROCESSED_DATA_FILE, MODEL_FILE, MODEL_DIR, ANOMALY_RATE

# Define the features to be used for training the Isolation Forest model
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
    
    # 2. True Labels (y): The ground truth flag for evaluation
    y_true = df['anomaly_flag_truth']
    
    # Isolation Forest does not handle NaNs, fill with 0
    X = X.fillna(0)

    return X, y_true, df

def train_isolation_forest(X):
    """
    Trains the Isolation Forest model for unsupervised anomaly detection.
    """
    print("-> Training Isolation Forest Model...")
    
    model = IsolationForest(
        contamination=ANOMALY_RATE,
        random_state=42,
        n_estimators=100,
        max_features=1.0,
        n_jobs=-1
    )

    model.fit(X)
    
    return model

def evaluate_model(model, X, y_true):
    """
    Evaluates the trained Isolation Forest model against ground truth labels.
    """
    print("-> Evaluating Model Performance...")
    
    # Isolation Forest predicts: 1 for inliers (normal), -1 for outliers (anomalies)
    y_pred_if = model.predict(X)
    y_pred_binary = np.where(y_pred_if == -1, 1, 0)
    
    # Calculate metrics
    anomaly_scores = model.decision_function(X)
    auc_score = roc_auc_score(y_true, -anomaly_scores)
    
    report = classification_report(
        y_true, 
        y_pred_binary, 
        target_names=['Normal (0)', 'Anomaly (1)'], 
        output_dict=True
    )
    
    cm = confusion_matrix(y_true, y_pred_binary)
    
    print("-" * 50)
    print(f"Model AUC-ROC Score: {auc_score:.4f}")
    print("--- Classification Report ---")
    print(classification_report(
        y_true, 
        y_pred_binary, 
        target_names=['Normal (0)', 'Anomaly (1)']
    ))
    print("--- Confusion Matrix (True vs Predicted) ---")
    print(f"| TN | FP | \n| FN | TP |\n{cm}")
    print("-" * 50)
    
    # Store metrics for persistence
    metrics = {
        'auc_roc': float(auc_score),
        'f1_anomaly': float(report['Anomaly (1)']['f1-score']),
        'precision_anomaly': float(report['Anomaly (1)']['precision']),
        'recall_anomaly': float(report['Anomaly (1)']['recall']),
        'total_events': int(len(y_true)),
        'total_anomalies': int(y_true.sum()),
        'confusion_matrix': cm.tolist(),
        'model_last_trained': datetime.now().isoformat()
    }
    
    return metrics, anomaly_scores

def save_model(model):
    """Saves the trained model using joblib."""
    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print(f"✅ Trained Isolation Forest model saved to: {MODEL_FILE}")

def save_metrics(metrics):
    """Saves model performance metrics to JSON file."""
    metrics_file = Path(MODEL_FILE).parent / "model_metrics.json"
    
    # Ensure the directory exists
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Model metrics saved to: {metrics_file}")
    except Exception as e:
        print(f"⚠️ Warning: Could not save metrics file: {e}")

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
    
    # Save metrics to JSON file
    save_metrics(metrics)
    
    # Save anomaly scores back to processed data
    df_full['anomaly_score'] = -anomaly_scores
    df_full.to_csv(PROCESSED_DATA_FILE, index=False)
    print(f"✅ Updated processed data with anomaly scores: {PROCESSED_DATA_FILE}")
    
    print("\n" + "=" * 50)
    print("🎉 MODEL TRAINING PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 50)

if __name__ == "__main__":
    model_training_pipeline()