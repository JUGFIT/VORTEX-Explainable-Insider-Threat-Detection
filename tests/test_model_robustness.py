# Save as: tests/test_model_robustness.py

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
import joblib
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from config_secure import settings
    PROCESSED_DATA_FILE = str(settings.PROCESSED_DATA_FILE)
    MODEL_FILE = str(settings.MODEL_FILE)
except ImportError:
    from config import PROCESSED_DATA_FILE, MODEL_FILE

from src.model_train import MODEL_FEATURES

def test_model_robustness():
    """Test if current dataset size is sufficient."""
    
    print("="*60)
    print("MODEL ROBUSTNESS TEST")
    print("="*60)
    
    # Load data
    df = pd.read_csv(PROCESSED_DATA_FILE)
    X = df[MODEL_FEATURES].fillna(0)
    y = df['anomaly_flag_truth']
    
    # Load model
    model = joblib.load(MODEL_FILE)
    
    # 1. Data Statistics
    print("\n📊 DATASET STATISTICS")
    print("-"*60)
    print(f"Total Events: {len(df):,}")
    print(f"Total Anomalies: {y.sum():,} ({y.mean()*100:.2f}%)")
    print(f"Total Normal: {len(y) - y.sum():,} ({(1-y.mean())*100:.2f}%)")
    print(f"Features: {len(MODEL_FEATURES)}")
    print(f"Users: {df['user_id'].nunique()}")
    
    # 2. Performance Metrics
    print("\n🎯 CURRENT PERFORMANCE")
    print("-"*60)
    scores = -model.decision_function(X)
    auc = roc_auc_score(y, scores)
    
    y_pred = np.where(model.predict(X) == -1, 1, 0)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, y_pred, average='binary', pos_label=1
    )
    
    print(f"AUC-ROC: {auc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    
    # 3. Sample Size Adequacy Test
    print("\n📏 SAMPLE SIZE ADEQUACY")
    print("-"*60)
    
    # Rule of thumb: 10-20 samples per feature for ML
    min_samples_needed = len(MODEL_FEATURES) * 20
    print(f"Minimum Recommended: {min_samples_needed:,} events")
    print(f"Your Dataset: {len(df):,} events")
    
    if len(df) >= min_samples_needed:
        print("✅ Dataset size is ADEQUATE")
        adequacy = "SUFFICIENT"
    else:
        print("⚠️ Consider increasing dataset size")
        adequacy = "INSUFFICIENT"
    
    # 4. Anomaly Sample Adequacy
    print("\n🚨 ANOMALY SAMPLE ADEQUACY")
    print("-"*60)
    min_anomalies_needed = 100  # Minimum for reliable statistics
    actual_anomalies = y.sum()
    
    print(f"Minimum Recommended: {min_anomalies_needed} anomalies")
    print(f"Your Dataset: {actual_anomalies} anomalies")
    
    if actual_anomalies >= min_anomalies_needed:
        print("✅ Anomaly samples are ADEQUATE")
        anomaly_adequacy = "SUFFICIENT"
    else:
        print("⚠️ Consider increasing anomaly samples")
        anomaly_adequacy = "INSUFFICIENT"
    
    # 5. Learning Curve Analysis (sample different sizes)
    print("\n📈 LEARNING CURVE ANALYSIS")
    print("-"*60)
    
    sample_sizes = [0.3, 0.5, 0.7, 0.9, 1.0]
    aucs = []
    
    for size in sample_sizes:
        sample_idx = np.random.choice(len(df), int(len(df)*size), replace=False)
        X_sample = X.iloc[sample_idx]
        y_sample = y.iloc[sample_idx]
        
        model_temp = model
        scores_temp = -model_temp.decision_function(X_sample)
        auc_temp = roc_auc_score(y_sample, scores_temp)
        aucs.append(auc_temp)
        
        print(f"{int(size*100):3d}% data ({int(len(df)*size):6,} events): AUC = {auc_temp:.4f}")
    
    # Check if performance plateaus
    auc_improvement = aucs[-1] - aucs[-2]
    print(f"\nImprovement from 90% to 100%: {auc_improvement:.4f}")
    
    if auc_improvement < 0.01:
        print("✅ Performance has PLATEAUED (more data won't help much)")
        plateau_status = "PLATEAUED"
    else:
        print("📈 Performance still IMPROVING (more data could help)")
        plateau_status = "IMPROVING"
    
    # 6. Final Recommendation
    print("\n" + "="*60)
    print("💡 RECOMMENDATION")
    print("="*60)
    
    if adequacy == "SUFFICIENT" and anomaly_adequacy == "SUFFICIENT" and plateau_status == "PLATEAUED" and auc >= 0.95:
        print("✅ Your current dataset size (20K) is EXCELLENT!")
        print("   No need to increase unless:")
        print("   - Adding more diverse user behaviors")
        print("   - Showcasing enterprise-scale capabilities")
        print("   - Real production deployment")
    elif auc >= 0.95:
        print("✅ Your model performs WELL with current data")
        print("   Consider 2-3x increase only if:")
        print("   - You want more robust statistics")
        print("   - You're deploying to production")
    else:
        print("⚠️ Consider increasing dataset size to:")
        print("   - 50K-100K events (2-5x current)")
        print("   - More diverse anomaly scenarios")
        print("   - Longer time period (60-90 days)")
    
    print("="*60)

if __name__ == "__main__":
    test_model_robustness()