import pandas as pd
import numpy as np
import os
import sys
import joblib
import shap # The Explainable AI library
from sklearn.ensemble import IsolationForest 

# --- PATH CORRECTION ---
# Ensure the script can reliably import config.py and model_train.py (for feature list)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    if project_root not in sys.path:
        sys.path.append(project_root)
except NameError:
    pass
# --- END PATH CORRECTION ---

# Import configuration constants and the feature list
from config import PROCESSED_DATA_FILE, MODEL_FILE
# Import the list of features the model was trained on
# Note: Ensure model_train.py is executed before this script runs.
from model_train import MODEL_FEATURES 

def load_data_and_model():
    """Loads the processed data (with scores) and the trained Isolation Forest model."""
    
    if not os.path.exists(PROCESSED_DATA_FILE):
        print("ERROR: Processed data file not found.")
        return None, None
        
    if not os.path.exists(MODEL_FILE):
        print("ERROR: Trained model not found. Run 'python src/model_train.py' first.")
        return None, None

    # Load data which includes the calculated anomaly_score
    df = pd.read_csv(PROCESSED_DATA_FILE)
    
    # Load the trained model using joblib
    model = joblib.load(MODEL_FILE)
    
    return df, model


def generate_shap_explanations(df, model, event_id=None):
    """
    Generates SHAP values for a specific event or the entire high-risk dataset.
    """
    
    print("-> Preparing data for SHAP analysis...")

    # Filter data to only include the features the model was trained on
    X = df[MODEL_FEATURES].copy()

    # 1. Initialize the SHAP Explainer
    # Use TreeExplainer as Isolation Forest is a tree-based model; it's fast and accurate.
    explainer = shap.TreeExplainer(model)
    
    # Find the event to explain
    if event_id:
        event_data = df[df['event_id'] == event_id]
        if event_data.empty:
            print(f"ERROR: Event ID {event_id} not found.")
            return None
        
        X_explain = event_data[MODEL_FEATURES]
        print(f"-> Generating explanation for Event ID: {event_id}")
    
    else:
        # Default: Explain the single highest-risk event 
        highest_risk_event = df.sort_values(by='anomaly_score', ascending=False).iloc[0]
        event_id = highest_risk_event['event_id']
        X_explain = highest_risk_event[MODEL_FEATURES].to_frame().T 

        print(f"-> No event_id specified. Explaining highest risk event: {event_id}")


    # 2. Calculate SHAP values
    shap_values = explainer.shap_values(X_explain)
    
    # Take the first element of shap_values, which corresponds to the anomaly detection score
    if isinstance(shap_values, list):
        shap_values = shap_values[0]

    # 3. Format Explanation for API/Frontend
    explanation_data = []
    base_value = explainer.expected_value
    
    # Create a structured list of contributions
    for i, feature in enumerate(MODEL_FEATURES):
        
        # --- FIX IMPLEMENTATION START ---
        # Isolation Forest: Negative SHAP value pushes towards anomaly (high risk).
        # Since we use an inverted anomaly_score (Higher score = Higher risk), 
        # we must INVERT the SHAP sign for interpretation clarity.
        #
        # If SHAP contribution is negative (original model output -> anomaly), 
        # it MEANS it increased the risk score in our inverted metric.
        #
        is_increasing_risk = shap_values[0][i] < 0
        
        explanation_data.append({
            'feature': feature,
            'value_at_risk': X_explain.iloc[0][feature], 
            'shap_contribution': shap_values[0][i], 
            'is_high_risk_contributor': is_increasing_risk # This is the corrected boolean flag
        })
        # --- FIX IMPLEMENTATION END ---
        
    # Sort contributions by magnitude for better display
    explanation_data.sort(key=lambda x: abs(x['shap_contribution']), reverse=True)
    
    return {
        'event_id': event_id,
        'base_value': base_value,
        'explanation': explanation_data
    }


def xai_pipeline(event_id=None):
    """Main pipeline function to run the XAI explanation."""
    
    df, model = load_data_and_model()
    if df is None:
        return

    explanation = generate_shap_explanations(df, model, event_id)
    
    if explanation:
        print("-" * 50)
        print(f"✅ SHAP Explanation Generated for {explanation['event_id']}:")
        print("\nTop 3 Feature Contributions:")
        for item in explanation['explanation'][:3]:
            # Use the corrected boolean flag for display
            # If the contribution is < 0 (pushes to anomaly), it increases risk in our VORTEX metric.
            contribution_type = "INCREASED RISK" if item['is_high_risk_contributor'] else "DECREASED RISK"
            
            # The magnitude of the SHAP value shows the strength of the contribution
            print(f"  - {item['feature']} ({item['value_at_risk']:.2f}): {contribution_type} by {abs(item['shap_contribution']):.4f}")
        print("-" * 50)
        
        return explanation


if __name__ == "__main__":
    # Example usage: Find the highest risk event and explain it
    xai_pipeline() 
    
    # You can later test this with a specific event ID for the API
    # xai_pipeline(event_id='user_041_1761936362.0')