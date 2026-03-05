import pandas as pd
import numpy as np
import os
import sys
import joblib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PATH CORRECTION ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    if project_root not in sys.path:
        sys.path.append(project_root)
except NameError:
    pass

from config import PROCESSED_DATA_FILE, MODEL_FILE
from src.model_train import MODEL_FEATURES

def load_model():
    """Load the trained Isolation Forest model."""
    if not os.path.exists(MODEL_FILE):
        logger.error(f"Model file not found: {MODEL_FILE}")
        logger.error("Please run 'python src/model_train.py' first to train the model.")
        return None
    
    try:
        model = joblib.load(MODEL_FILE)
        logger.info(f"Model loaded successfully from {MODEL_FILE}")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

def prepare_features(events: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Prepare and validate features for prediction.
    
    Args:
        events: List of event dictionaries containing features
    
    Returns:
        DataFrame with properly formatted features
    """
    df = pd.DataFrame(events)
    
    # Validate that all required features are present
    missing_features = set(MODEL_FEATURES) - set(df.columns)
    if missing_features:
        logger.error(f"Missing required features: {missing_features}")
        raise ValueError(f"Missing features: {missing_features}")
    
    # Extract only the model features in the correct order
    X = df[MODEL_FEATURES].copy()
    
    # Handle missing values (fill with 0 as in training)
    if X.isnull().any().any():
        logger.warning("NaN values detected. Filling with 0.")
        X = X.fillna(0)
    
    return X, df

def predict_anomaly_scores(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Predict anomaly scores for a batch of events.
    
    Args:
        events: List of event dictionaries with features
    
    Returns:
        List of predictions with anomaly scores and risk levels
    """
    model = load_model()
    if model is None:
        raise ValueError("Model not available. Train the model first.")
    
    try:
        # Prepare features
        X, df_original = prepare_features(events)
        
        # Get anomaly scores (decision_function)
        # Isolation Forest: lower score = more anomalous
        scores = model.decision_function(X)
        
        # Invert scores so higher = more anomalous (for consistency)
        anomaly_scores = -scores
        
        # Get binary predictions (-1 for anomaly, 1 for normal)
        predictions = model.predict(X)
        anomaly_flags = np.where(predictions == -1, 1, 0)
        
        # Calculate risk levels based on score distribution
        # Use quantiles from the scores
        q_low = np.percentile(anomaly_scores, 80)
        q_high = np.percentile(anomaly_scores, 95)
        
        def categorize_risk(score):
            if score >= q_high:
                return "High"
            elif score >= q_low:
                return "Medium"
            else:
                return "Low"
        
        risk_levels = [categorize_risk(score) for score in anomaly_scores]
        
        # Combine results
        results = []
        for i, event in enumerate(events):
            result = {
                'event_data': event,
                'anomaly_score': float(anomaly_scores[i]),
                'anomaly_flag': int(anomaly_flags[i]),
                'risk_level': risk_levels[i],
                'prediction_confidence': abs(float(scores[i]))  # Distance from decision boundary
            }
            results.append(result)
        
        logger.info(f"Successfully predicted {len(results)} events")
        logger.info(f"High risk: {sum(1 for r in results if r['risk_level'] == 'High')}")
        logger.info(f"Medium risk: {sum(1 for r in results if r['risk_level'] == 'Medium')}")
        logger.info(f"Low risk: {sum(1 for r in results if r['risk_level'] == 'Low')}")
        
        return results
        
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise

def predict_from_csv(csv_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Predict anomaly scores for events in a CSV file.
    
    Args:
        csv_path: Path to input CSV file
        output_path: Optional path to save predictions
    
    Returns:
        DataFrame with predictions
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    logger.info(f"Loading data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Convert to list of dictionaries
    events = df[MODEL_FEATURES].to_dict('records')
    
    # Get predictions
    predictions = predict_anomaly_scores(events)
    
    # Create results DataFrame
    results_df = pd.DataFrame([p['event_data'] for p in predictions])
    results_df['anomaly_score'] = [p['anomaly_score'] for p in predictions]
    results_df['anomaly_flag'] = [p['anomaly_flag'] for p in predictions]
    results_df['risk_level'] = [p['risk_level'] for p in predictions]
    results_df['prediction_confidence'] = [p['prediction_confidence'] for p in predictions]
    
    # Save if output path provided
    if output_path:
        results_df.to_csv(output_path, index=False)
        logger.info(f"Predictions saved to {output_path}")
    
    return results_df

def batch_predict_pipeline(input_csv: Optional[str] = None):
    """
    Main pipeline for batch prediction.
    
    Args:
        input_csv: Optional path to input CSV. Defaults to processed data file.
    """
    if input_csv is None:
        input_csv = PROCESSED_DATA_FILE
    
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        logger.error("Please run feature engineering first.")
        return None
    
    # Generate output filename
    input_path = Path(input_csv)
    output_path = input_path.parent / f"{input_path.stem}_predictions.csv"
    
    try:
        results = predict_from_csv(input_csv, str(output_path))
        
        logger.info("=" * 60)
        logger.info("✅ Batch Prediction Complete")
        logger.info(f"Total events: {len(results)}")
        logger.info(f"High risk: {len(results[results['risk_level'] == 'High'])}")
        logger.info(f"Medium risk: {len(results[results['risk_level'] == 'Medium'])}")
        logger.info(f"Low risk: {len(results[results['risk_level'] == 'Low'])}")
        logger.info(f"Results saved to: {output_path}")
        logger.info("=" * 60)
        
        return results
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="VORTEX Batch Prediction")
    parser.add_argument(
        '--input', 
        type=str, 
        default=None,
        help='Input CSV file path (default: processed_features.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output CSV file path (default: auto-generated)'
    )
    
    args = parser.parse_args()
    
    if args.output:
        predict_from_csv(args.input or PROCESSED_DATA_FILE, args.output)
    else:
        batch_predict_pipeline(args.input)