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

# =============================================================================
# FEATURE NAME MAPPING (Human Readable)
# =============================================================================

FEATURE_NAME_MAP = {
    # Temporal Features
    'hour_of_day': 'Time of Day',
    'day_of_week': 'Day of Week',
    'is_off_hours': 'Off-Hours Activity',
    'hour_sin': 'Time Pattern (Sine)',
    'hour_cos': 'Time Pattern (Cosine)',
    'day_sin': 'Day Pattern (Sine)',
    'day_cos': 'Day Pattern (Cosine)',
    
    # File Activity Features
    'file_access_count': 'File Access Frequency',
    'upload_count': 'File Upload Frequency',
    'download_count': 'File Download Frequency',
    'upload_size_mb': 'Upload Data Volume (MB)',
    'download_size_mb': 'Download Data Volume (MB)',
    
    # Risk Indicators
    'sensitive_file_access': 'Sensitive File Access',
    'external_ip_connection': 'External IP Connection',
    'failed_login_attempts': 'Failed Login Attempts',
    
    # Behavioral Rolling Averages (24h)
    'file_access_count_24h': '24h File Access Average',
    'upload_count_24h': '24h Upload Average',
    'download_count_24h': '24h Download Average',
    'upload_size_mb_24h': '24h Upload Volume Average',
    'download_size_mb_24h': '24h Download Volume Average',
    'sensitive_access_24h': '24h Sensitive Access Average',
    'external_conn_24h': '24h External Connection Average',
    'failed_login_24h': '24h Failed Login Average',
    
    # Z-Score Normalized Features
    'file_access_count_zscore': 'Abnormal File Access Pattern',
    'upload_size_mb_zscore': 'Abnormal Upload Volume',
    'download_size_mb_zscore': 'Abnormal Download Volume',
    'sensitive_file_access_zscore': 'Abnormal Sensitive Access',
    'external_ip_connection_zscore': 'Abnormal External Connection',
    'failed_login_attempts_zscore': 'Abnormal Failed Login Pattern',
    
    # Behavioral Indicators
    'is_unusual_login': 'Unusual Login Location/Method',
    'privilege_escalation': 'Privilege Escalation Attempt',
    'admin_action': 'Administrative Action',
}

def get_human_readable_feature(feature_name: str) -> str:
    """Convert technical feature name to human-readable format."""
    return FEATURE_NAME_MAP.get(feature_name, feature_name.replace('_', ' ').title())


# =============================================================================
# ATTACK NARRATIVE BUILDER
# =============================================================================

class AttackNarrative:
    """
    Converts SHAP feature contributions into human-readable threat narratives.
    Uses rule-based templates to generate contextual explanations for security analysts.
    """
    
    @staticmethod
    def _generate_feature_description(feature: str, value: float, contribution: float) -> str:
        """
        Generate a human-readable description for a specific feature contribution.
        
        Args:
            feature: Technical feature name
            value: Actual feature value at time of risk
            contribution: SHAP contribution value
            
        Returns:
            Human-readable description string
        """
        
        # Upload Volume
        if 'upload_size_mb' in feature:
            if value > 2.0:  # Z-score threshold
                return f"unusually large data upload ({abs(value):.1f}x above normal behavior)"
            else:
                return f"elevated data upload activity ({value:.2f} MB)"
        
        # Off-Hours Activity
        if 'is_off_hours' in feature:
            if value > 0.5:
                return "activity occurring outside standard business hours (high risk period)"
            else:
                return "activity during off-hours period"
        
        # Sensitive File Access
        if 'sensitive_file' in feature or 'sensitive_access' in feature:
            if value > 1.5:
                return f"abnormally high access to sensitive/classified files ({abs(value):.1f}x above baseline)"
            else:
                return "access to sensitive or restricted files"
        
        # External IP Connections
        if 'external_ip' in feature or 'external_conn' in feature:
            if value > 1.5:
                return f"suspicious connections to external/unknown IP addresses ({abs(value):.1f}x above normal)"
            else:
                return "connection to external network destinations"
        
        # File Access Count
        if 'file_access_count' in feature:
            if value > 2.0:
                return f"abnormally high file access activity ({abs(value):.1f}x above typical behavior)"
            else:
                return "elevated file access frequency"
        
        # Failed Login Attempts
        if 'failed_login' in feature:
            if value > 1.5:
                return f"multiple failed authentication attempts ({abs(value):.1f}x above baseline)"
            else:
                return "failed login attempts detected"
        
        # Download Volume
        if 'download_size_mb' in feature:
            if value > 2.0:
                return f"unusually large data download ({abs(value):.1f}x above normal)"
            else:
                return f"elevated data download activity ({value:.2f} MB)"
        
        # Time-based patterns
        if 'hour_of_day' in feature:
            hour = int(value) if value >= 0 else 0
            return f"activity at unusual time of day ({hour:02d}:00 hours)"
        
        # Generic fallback
        human_name = get_human_readable_feature(feature)
        return f"{human_name.lower()} showing abnormal pattern (value: {value:.2f})"
    
    @staticmethod
    def generate(explanation_data: list, event_id: str = None, top_n: int = 5) -> str:
        """
        Generate a comprehensive attack narrative from SHAP explanation data.
        
        Args:
            explanation_data: List of feature contribution dictionaries from SHAP
            event_id: Optional event ID for context
            top_n: Number of top contributors to include in narrative
            
        Returns:
            Human-readable narrative string
        """
        
        if not explanation_data:
            return "No significant risk indicators detected for this event."
        
        # Filter only high-risk contributors
        high_risk_features = [
            item for item in explanation_data 
            if item.get('is_high_risk_contributor', False)
        ]
        
        if not high_risk_features:
            return "Event flagged for review, but no strong risk indicators identified. Manual investigation recommended."
        
        # Get top N contributors
        top_features = high_risk_features[:top_n]
        
        # Build narrative
        narrative_parts = []
        
        # Opening statement
        risk_count = len(high_risk_features)
        if risk_count == 1:
            narrative_parts.append("**High-risk event detected** due to:")
        elif risk_count <= 3:
            narrative_parts.append(f"**High-risk event detected** with {risk_count} suspicious indicators:")
        else:
            narrative_parts.append(f"**Critical threat detected** with {risk_count} anomalous behavioral indicators:")
        
        # Detail each top contributor
        for i, item in enumerate(top_features, 1):
            feature = item['feature']
            value = item['value_at_risk']
            contribution = item['shap_contribution']
            
            description = AttackNarrative._generate_feature_description(feature, value, contribution)
            narrative_parts.append(f"{i}. **{get_human_readable_feature(feature)}**: {description}")
        
        # Contextual conclusion
        if risk_count > top_n:
            remaining = risk_count - top_n
            narrative_parts.append(f"\n*Additional {remaining} risk indicator(s) also contributing to threat score.*")
        
        # Threat assessment summary
        max_contribution = abs(top_features[0]['shap_contribution'])
        if max_contribution > 0.05:
            narrative_parts.append("\n⚠️ **Threat Level**: CRITICAL - Immediate investigation required.")
        elif max_contribution > 0.02:
            narrative_parts.append("\n⚠️ **Threat Level**: HIGH - Priority investigation recommended.")
        else:
            narrative_parts.append("\n⚠️ **Threat Level**: MODERATE - Review and monitor activity.")
        
        return "\n".join(narrative_parts)


# =============================================================================
# MITIGATION SUGGESTIONS GENERATOR
# =============================================================================

def get_mitigation_suggestions(explanation_data: list, top_n: int = 5) -> list:
    """
    Generate actionable mitigation suggestions based on top risk contributors.
    
    Args:
        explanation_data: List of feature contribution dictionaries from SHAP
        top_n: Number of top contributors to generate mitigations for
        
    Returns:
        List of actionable mitigation recommendation strings
    """
    
    if not explanation_data:
        return ["No specific mitigations identified. Continue standard monitoring."]
    
    # Filter high-risk contributors
    high_risk_features = [
        item for item in explanation_data 
        if item.get('is_high_risk_contributor', False)
    ]
    
    if not high_risk_features:
        return [
            "Verify user activity manually.",
            "Review recent access logs for this user.",
            "Continue monitoring for pattern changes."
        ]
    
    # Get top contributors
    top_features = high_risk_features[:top_n]
    
    suggestions = []
    seen_categories = set()  # Avoid duplicate suggestions
    
    for item in top_features:
        feature = item['feature']
        value = item['value_at_risk']
        
        # Upload Volume
        if 'upload_size_mb' in feature and 'upload' not in seen_categories:
            seen_categories.add('upload')
            suggestions.append(
                "**Data Exfiltration Risk**: Investigate data destination IP addresses and block if unknown. "
                "Review DLP (Data Loss Prevention) logs for unauthorized data transfers."
            )
        
        # Off-Hours Activity
        elif 'is_off_hours' in feature and 'off_hours' not in seen_categories:
            seen_categories.add('off_hours')
            suggestions.append(
                "**Off-Hours Access**: Verify user authorization for after-hours access. "
                "Consider restricting VPN access times and require manager approval for off-hours work."
            )
        
        # Sensitive File Access
        elif ('sensitive_file' in feature or 'sensitive_access' in feature) and 'sensitive' not in seen_categories:
            seen_categories.add('sensitive')
            suggestions.append(
                "**Sensitive Data Access**: Temporarily revoke access to sensitive files pending investigation. "
                "Audit file permissions and verify user clearance level. Review file access logs for unauthorized viewing."
            )
        
        # External IP Connections
        elif ('external_ip' in feature or 'external_conn' in feature) and 'external' not in seen_categories:
            seen_categories.add('external')
            suggestions.append(
                "**External Network Activity**: Block suspicious IP addresses immediately. "
                "Review firewall logs and check threat intelligence databases for known malicious IPs. "
                "Scan endpoint for C2 (Command & Control) malware."
            )
        
        # File Access Count
        elif 'file_access_count' in feature and 'file_access' not in seen_categories:
            seen_categories.add('file_access')
            suggestions.append(
                "**Abnormal File Activity**: Scan user endpoint for ransomware, automated scraping scripts, or data harvesting malware. "
                "Review file access patterns and compare with role-based normal behavior."
            )
        
        # Failed Login Attempts
        elif 'failed_login' in feature and 'failed_login' not in seen_categories:
            seen_categories.add('failed_login')
            suggestions.append(
                "**Authentication Anomaly**: Force password reset and verify user identity. "
                "Check for credential stuffing or brute-force attack patterns. Enable MFA if not already active."
            )
        
        # Download Volume
        elif 'download_size_mb' in feature and 'download' not in seen_categories:
            seen_categories.add('download')
            suggestions.append(
                "**Data Download Risk**: Investigate source and purpose of large downloads. "
                "Verify files are work-related and check for unauthorized bulk data extraction."
            )
    
    # Add general security best practices if < 3 specific suggestions
    if len(suggestions) < 3:
        suggestions.extend([
            "**User Interview**: Conduct security interview to verify legitimate business purpose for flagged activity.",
            "**Endpoint Security**: Run full endpoint security scan (antivirus, EDR tools) on user's device.",
            "**Access Review**: Perform comprehensive access rights review for this user account."
        ])
    
    # Always add monitoring recommendation
    suggestions.append(
        "**Continuous Monitoring**: Escalate to Tier-2 SOC analysts and maintain enhanced monitoring for this user for the next 7 days."
    )
    
    # Return top 5 most relevant suggestions
    return suggestions[:5]


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
            # Cast column and search ID to string for robust matching
            event_id_str = str(event_id)
            event_data = df[df['event_id'].astype(str) == event_id_str]
            if event_data.empty:
                logger.error(f"Event ID {event_id} not found in dataset.")
                return None
            
            X_explain = X.loc[event_data.index]
            logger.info(f"Generating explanation for Event ID: {event_id}")
        
        else:
            # Default: Explain the single highest-risk event
            if 'anomaly_score' not in df.columns:
                logger.error("anomaly_score column not found. Run model training first.")
                return None
                
            highest_risk_event_idx = df.sort_values(by='anomaly_score', ascending=False).index[0]
            event_id = df.loc[highest_risk_event_idx, 'event_id']
            X_explain = X.loc[[highest_risk_event_idx]]

            logger.info(f"No event_id specified. Explaining highest risk event: {event_id}")

        # Final safety check on X_explain (ensure no NaNs reach the explainer)
        X_explain = X_explain.fillna(0)

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
            
        # Final NaN check for base_value
        if not np.isfinite(base_value):
            base_value = 0.0
        
        # Create a structured list of contributions
        for i, feature in enumerate(MODEL_FEATURES):
            # Resolve potential NaN issues for JSON serialization
            val = float(X_explain.iloc[0][feature])
            contrib = float(shap_values[0][i])
            
            if not np.isfinite(val): val = 0.0
            if not np.isfinite(contrib): contrib = 0.0
            
            # In Isolation Forest, negative SHAP values indicate increased anomaly risk
            is_increasing_risk = contrib < 0
            
            explanation_data.append({
                'feature': feature,
                'value_at_risk': val,
                'shap_contribution': contrib, 
                'is_high_risk_contributor': bool(is_increasing_risk)
            })
        
        # Sort contributions by magnitude (absolute value)
        explanation_data.sort(key=lambda x: abs(x['shap_contribution']), reverse=True)
        
        # Generate human-readable narrative
        narrative = AttackNarrative.generate(
            explanation_data=explanation_data,
            event_id=event_id,
            top_n=5
        )
        
        # Generate mitigation suggestions
        mitigation_suggestions = get_mitigation_suggestions(
            explanation_data=explanation_data,
            top_n=5
        )
        
        result = {
            'event_id': str(event_id),
            'base_value': base_value,
            'explanation': explanation_data,
            'narrative': narrative,
            'mitigation_suggestions': mitigation_suggestions
        }
        
        logger.info("✅ SHAP explanation generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating SHAP explanations: {e}", exc_info=True)
        return None


def xai_pipeline(event_id=None, df=None, model=None):
    """
    Main pipeline function to run the XAI explanation.
    
    Args:
        event_id: Optional event ID to explain. If None, explains highest risk event.
        df: Optional pre-loaded DataFrame
        model: Optional pre-loaded Model
        
    Returns:
        Dictionary with explanation details or None if failed
    """
    
    try:
        logger.info("=" * 60)
        logger.info("Starting XAI Explanation Pipeline")
        logger.info("=" * 60)
        
        # Load data and model if not provided
        if df is None or model is None:
            df_disk, model_disk = load_data_and_model()
            df = df if df is not None else df_disk
            model = model if model is not None else model_disk

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