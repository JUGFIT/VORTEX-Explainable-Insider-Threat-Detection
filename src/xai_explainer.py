import pandas as pd
import numpy as np
import os
import sys
import joblib
import shap
import hashlib
import logging
from sklearn.ensemble import IsolationForest
from pathlib import Path

# Configure logging
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

# Import configuration (try secure config first, fallback to basic)
try:
    from config_secure import settings
    PROCESSED_DATA_FILE = str(settings.PROCESSED_DATA_FILE)
    MODEL_FILE = str(settings.MODEL_FILE)
    ALLOWED_DATA_DIR = settings.DATA_DIR
    ALLOWED_MODEL_DIR = settings.MODEL_DIR
except ImportError:
    from config import PROCESSED_DATA_FILE, MODEL_FILE, DATA_DIR, MODEL_DIR
    ALLOWED_DATA_DIR = Path(DATA_DIR).resolve()
    ALLOWED_MODEL_DIR = Path(MODEL_DIR).resolve()

from src.model_train import MODEL_FEATURES

def validate_file_path(file_path, allowed_dir):
    """Validates that file path is within allowed directory."""
    try:
        resolved_path = Path(file_path).resolve()
        allowed_path = Path(allowed_dir).resolve()
        
        if not resolved_path.is_relative_to(allowed_path):
            raise ValueError(f"File path outside allowed directory: {file_path}")
        return resolved_path
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        raise

def verify_model_integrity(model_path, expected_hash=None):
    """Optionally verify model file hasn't been tampered with."""
    if expected_hash:
        with open(model_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        if file_hash != expected_hash:
            raise ValueError("Model file integrity check failed!")
    
def load_data_and_model():
    """Loads the processed data (with scores) and the trained Isolation Forest model."""
    
    try:
        # Validate paths
        data_path = validate_file_path(PROCESSED_DATA_FILE, ALLOWED_DATA_DIR)
        model_path = validate_file_path(MODEL_FILE, ALLOWED_MODEL_DIR)
        
        if not data_path.exists():
            logger.error(f"Processed data file not found: {data_path}")
            logger.error("Run 'python src/feature_engineer.py' first.")
            return None, None
            
        if not model_path.exists():
            logger.error(f"Trained model not found: {model_path}")
            logger.error("Run 'python src/model_train.py' first.")
            return None, None

        # Load data
        logger.info(f"Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        
        # Validate required columns
        required_cols = set(MODEL_FEATURES + ['event_id', 'anomaly_score'])
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return None, None
        
        # Check for missing values in critical columns
        if df[MODEL_FEATURES].isnull().any().any():
            logger.warning("Missing values detected in features. Will apply imputation.")
        
        # Verify model integrity (optional - add hash to config if needed)
        # verify_model_integrity(model_path, expected_hash="your_hash_here")
        
        # Load model
        logger.info(f"Loading model from: {model_path}")
        model = joblib.load(model_path)
        
        # Validate model type
        if not isinstance(model, IsolationForest):
            logger.error("Loaded model is not an IsolationForest instance.")
            return None, None
        
        logger.info(f"✅ Successfully loaded {len(df)} records and model.")
        return df, model
        
    except Exception as e:
        logger.error(f"Error loading data/model: {e}", exc_info=True)
        return None, None


def generate_shap_explanations(df, model, event_id=None):
    """
    Generates SHAP values for a specific event or the entire high-risk dataset.
    
    Args:
        df: DataFrame with processed features
        model: Trained IsolationForest model
        event_id: Optional specific event ID to explain
        
    Returns:
        Dictionary with event_id, base_value, and explanation details
    """
    
    try:
        logger.info("Preparing data for SHAP analysis...")

        # Validate event_id type if provided
        if event_id is not None:
            if not isinstance(event_id, (str, int, np.integer)):
                logger.error(f"Invalid event_id type: {type(event_id)}")
                return None
        
        # Filter data to only include the features the model was trained on
        X = df[MODEL_FEATURES].copy()
        
        # Handle missing values
        if X.isnull().any().any():
            logger.warning("NaN values detected. Filling with median.")
            X = X.fillna(X.median())

        # Initialize the SHAP Explainer
        logger.info("Initializing SHAP TreeExplainer...")
        explainer = shap.TreeExplainer(model)
        
        # Find the event to explain
        if event_id is not None:
            event_data = df[df['event_id'] == event_id]
            if event_data.empty:
                logger.error(f"Event ID {event_id} not found in dataset.")
                return None
            
            X_explain = event_data[MODEL_FEATURES]
            logger.info(f"Generating explanation for Event ID: {event_id}")
        
        else:
            # Default: Explain the single highest-risk event
            if 'anomaly_score' not in df.columns:
                logger.error("anomaly_score column not found. Run model training first.")
                return None
                
            highest_risk_event = df.sort_values(by='anomaly_score', ascending=False).iloc[0]
            event_id = highest_risk_event['event_id']
            X_explain = highest_risk_event[MODEL_FEATURES].to_frame().T 

            logger.info(f"No event_id specified. Explaining highest risk event: {event_id}")

        # Calculate SHAP values
        logger.info("Calculating SHAP values...")
        shap_values = explainer.shap_values(X_explain)
        
        # Handle list output (some versions of SHAP return lists)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]

        # Format Explanation for API/Frontend
        explanation_data = []
        base_value = explainer.expected_value
        
        # Handle base_value if it's an array
        if isinstance(base_value, np.ndarray):
            base_value = float(base_value[0])
        else:
            base_value = float(base_value)
        
        # Create a structured list of contributions
        for i, feature in enumerate(MODEL_FEATURES):
            # In Isolation Forest, negative SHAP values indicate increased anomaly risk
            is_increasing_risk = shap_values[0][i] < 0
            
            explanation_data.append({
                'feature': feature,
                'value_at_risk': float(X_explain.iloc[0][feature]),
                'shap_contribution': float(shap_values[0][i]), 
                'is_high_risk_contributor': bool(is_increasing_risk)
            })
        
        # Sort contributions by magnitude (absolute value)
        explanation_data.sort(key=lambda x: abs(x['shap_contribution']), reverse=True)
        
        result = {
            'event_id': str(event_id),
            'base_value': base_value,
            'explanation': explanation_data
        }
        
        logger.info("✅ SHAP explanation generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating SHAP explanations: {e}", exc_info=True)
        return None


def xai_pipeline(event_id=None):
    """
    Main pipeline function to run the XAI explanation.
    
    Args:
        event_id: Optional event ID to explain. If None, explains highest risk event.
        
    Returns:
        Dictionary with explanation details or None if failed
    """
    
    try:
        logger.info("=" * 60)
        logger.info("Starting XAI Explanation Pipeline")
        logger.info("=" * 60)
        
        # Load data and model
        df, model = load_data_and_model()
        if df is None or model is None:
            logger.error("Failed to load data or model. Exiting pipeline.")
            return None

        # Generate explanation
        explanation = generate_shap_explanations(df, model, event_id)
        
        if explanation:
            logger.info("-" * 60)
            logger.info(f"✅ SHAP Explanation Generated for Event: {explanation['event_id']}")
            logger.info(f"Base Value (Expected): {explanation['base_value']:.4f}")
            logger.info("\n📊 Top 5 Feature Contributions:")
            
            for i, item in enumerate(explanation['explanation'][:5], 1):
                contribution_type = "INCREASED RISK" if item['is_high_risk_contributor'] else "DECREASED RISK"
                logger.info(
                    f"  {i}. {item['feature']:25s} = {item['value_at_risk']:8.2f} | "
                    f"{contribution_type:15s} by {abs(item['shap_contribution']):8.4f}"
                )
            
            logger.info("-" * 60)
            logger.info("Pipeline completed successfully")
            logger.info("=" * 60)
            
            return explanation
        else:
            logger.warning("No explanation generated.")
            return None
            
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        logger.error("=" * 60)
        return None


if __name__ == "__main__":
    # Test the pipeline
    result = xai_pipeline()
    
    if result:
        print("\n" + "=" * 60)
        print("EXPLANATION SUMMARY")
        print("=" * 60)
        print(f"Event ID: {result['event_id']}")
        print(f"Total Features Analyzed: {len(result['explanation'])}")
        print(f"High Risk Contributors: {sum(1 for e in result['explanation'] if e['is_high_risk_contributor'])}")
        print("=" * 60)
    else:
        print("\n❌ Failed to generate explanation")