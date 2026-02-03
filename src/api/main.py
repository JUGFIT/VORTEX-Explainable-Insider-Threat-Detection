import pandas as pd
import numpy as np
import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import joblib

# --- PATH CORRECTION ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..')
    if project_root not in sys.path:
        sys.path.append(project_root)
except NameError:
    pass

# Import configuration (try secure config first, fallback to basic)
try:
    from config_secure import settings
    PROCESSED_DATA_FILE = str(settings.PROCESSED_DATA_FILE)
    MODEL_FILE = str(settings.MODEL_FILE)
    RAW_DATA_FILE = str(settings.RAW_DATA_FILE)
except ImportError:
    from config import PROCESSED_DATA_FILE, MODEL_FILE, RAW_DATA_FILE
    
# Import core components
from src.xai_explainer import xai_pipeline, load_data_and_model
from src.data_generator import generate_synthetic_logs
from src.feature_engineer import feature_engineering_pipeline
from src.model_train import model_training_pipeline, MODEL_FEATURES
from src.user_profile import UserProfile, UserProfileManager, initialize_profile_manager, get_profile_manager
from src.risk_trajectory import RiskTrajectory, TrajectoryManager, initialize_trajectory_manager, get_trajectory_manager
from src.event_chains import EventChainDetector, ChainDetectorManager, initialize_chain_detector, get_chain_detector_manager

# Import logging
try:
    from utils.logging_config import get_logger
    logger = get_logger("vortex.api")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("vortex.api")

# =============================================================================
# FASTAPI APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title="VORTEX X-ADS API",
    description="Explainable Anomaly Detection System for Insider Threat Detection",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- CORS Configuration ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class RiskEvent(BaseModel):
    """Schema for a summarized risk event visible in the dashboard table."""
    event_id: str
    user_id: str
    timestamp: str
    anomaly_score: float
    risk_level: str
    anomaly_flag_truth: int

class FeatureContribution(BaseModel):
    """Schema for a single feature's SHAP contribution."""
    feature: str
    value_at_risk: float
    shap_contribution: float
    is_high_risk_contributor: bool

class ExplanationResponse(BaseModel):
    """Schema for the full SHAP explanation response."""
    event_id: str
    base_value: float
    explanation: List[FeatureContribution]
    narrative: str
    mitigation_suggestions: List[str]

class HealthStatus(BaseModel):
    """System health check response."""
    status: str
    timestamp: str
    data_loaded: bool
    model_loaded: bool
    total_events: Optional[int] = None
    high_risk_events: Optional[int] = None
    model_file_exists: bool
    processed_data_exists: bool

class PipelineStatus(BaseModel):
    """Pipeline execution status."""
    task: str
    status: str
    message: str
    timestamp: str

class ModelMetrics(BaseModel):
    """Model performance metrics."""
    auc_roc: float
    f1_anomaly: float
    precision_anomaly: float
    recall_anomaly: float
    total_events: int
    total_anomalies: int
    model_last_trained: Optional[str] = None

class UserRiskSummary(BaseModel):
    """Risk summary for a specific user."""
    user_id: str
    total_events: int
    high_risk_events: int
    medium_risk_events: int
    low_risk_events: int
    average_anomaly_score: float
    max_anomaly_score: float
    recent_events: List[RiskEvent]

class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions."""
    events: List[Dict[str, Any]]

class BatchPredictionResponse(BaseModel):
    """Response schema for batch predictions."""
    predictions: List[Dict[str, Any]]
    total_processed: int
    high_risk_count: int

# Phase 2A: User Baseline Schemas
class UserSummary(BaseModel):
    """Summary information for a user (for listing)."""
    user_id: str
    event_count: int
    baseline_risk_level: str
    baseline_score: float
    confidence: float

class UserBaseline(BaseModel):
    """Detailed baseline information for a user."""
    user_id: str
    baseline: Dict[str, Any]
    behavioral_fingerprint: Dict[str, Any]
    baseline_risk_level: str
    is_baseline_elevated: bool
    data_quality: Dict[str, Any]

class DivergenceAnalysis(BaseModel):
    """Divergence analysis for an event compared to user's baseline."""
    divergence_score: float
    divergence_level: str
    divergence_details: List[str]
    baseline_comparison: Dict[str, Any]

# Phase 2A Session 3: Risk Trajectory Schemas
class TrajectoryTimepoint(BaseModel):
    """Single data point in risk trajectory timeline."""
    date: str
    events: int
    avg_risk: float
    cumulative_risk: float
    avg_decay_factor: float
    high_risk_events: int
    medium_risk_events: int
    low_risk_events: int
    running_cumulative_risk: Optional[float] = None

class EscalationDetails(BaseModel):
    """Details about risk escalation detection."""
    recent_7d_avg: float
    previous_7d_avg: float
    percent_change: float
    recent_event_count: int
    previous_event_count: int
    threshold_met: bool
    severity: str

class TrajectoryData(BaseModel):
    """Complete risk trajectory data for a user."""
    user_id: str
    trajectory: List[TrajectoryTimepoint]
    current_cumulative_risk: float
    trend: str
    is_escalating: bool
    escalation_details: Optional[EscalationDetails] = None
    summary: Dict[str, Any]

class TrajectoryStatistics(BaseModel):
    """Overall trajectory statistics across all users."""
    total_users: int
    escalating_count: int
    stable_count: int
    declining_count: int
    avg_cumulative_risk: float
    escalation_rate: float

# Phase 2A Session 4: Event Chain Schemas
class ChainEvent(BaseModel):
    """Simplified event information within a chain."""
    event_id: str
    timestamp: str
    tags: List[str]
    anomaly_score: float
    risk_level: str

class EventChain(BaseModel):
    """Detected sequence of suspicious events forming a pattern."""
    chain_id: str
    user_id: str
    pattern_type: str
    pattern_name: str
    severity: str
    pattern_description: str
    events: List[ChainEvent]
    event_count: int
    start_time: str
    end_time: str
    duration_hours: float
    individual_risk_sum: float
    chain_risk: float
    amplification_factor: float
    matched_sequence: List[str]
    narrative: str

class ChainSummary(BaseModel):
    """Summary of chains detected for a specific user."""
    user_id: str
    total_chains: int
    chains_by_severity: Dict[str, int]
    chains_by_type: Dict[str, int]
    highest_risk: float
    most_dangerous_pattern: Optional[str] = None
    critical_count: int
    high_count: int
    medium_count: int

class ChainStatistics(BaseModel):
    """Global statistics for all detected event chains."""
    total_users: int
    total_chains: int
    critical_chains: int
    high_chains: int
    medium_chains: int
    users_with_chains: int
    avg_chains_per_user: float

# =============================================================================
# GLOBAL DATA STORE
# =============================================================================

class DataStore:
    """Global data store for caching loaded data and model."""
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.model = None
        self.last_loaded: Optional[datetime] = None
        self.metrics: Optional[Dict] = None
        self.profile_manager: Optional[UserProfileManager] = None  # Phase 2A: User baselines
        self.trajectory_manager: Optional[TrajectoryManager] = None  # Phase 2A: Risk trajectories
        self.chain_manager: Optional[ChainDetectorManager] = None  # Phase 2A: Event chains
    
    def load(self):
        """Load or reload data and model."""
        try:
            self.df = load_processed_data()
            self.model = load_model()
            self.last_loaded = datetime.now()
            
            # Phase 2A: Initialize user profiles
            if self.df is not None:
                logger.info("Initializing user profile baselines...")
                self.profile_manager = initialize_profile_manager(self.df)
                logger.info(f"✅ Loaded {len(self.profile_manager.profiles)} user profiles")
                
                # Phase 2A Session 3: Initialize risk trajectories
                logger.info("Initializing risk trajectories...")
                self.trajectory_manager = initialize_trajectory_manager(self.df)
                logger.info(f"✅ Calculated {len(self.trajectory_manager.trajectories)} risk trajectories")
                
                # Phase 2A Session 4: Initialize event chains
                logger.info("Initializing event chain detection...")
                self.chain_manager = initialize_chain_detector(self.df)
                logger.info(f"✅ Detected {len(self.chain_manager.get_all_chains())} attack chains")
            
            logger.info("Data and model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading data/model: {e}")
            raise
    
    def is_loaded(self) -> bool:
        """Check if data and model are loaded."""
        return self.df is not None and self.model is not None
    
    def reload(self):
        """Force reload of data and model."""
        logger.info("Reloading data and model...")
        self.load()

# Initialize global data store
data_store = DataStore()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def load_processed_data():
    """Load the processed dataset with anomaly scores."""
    if not os.path.exists(PROCESSED_DATA_FILE):
        logger.warning(f"Processed data file not found: {PROCESSED_DATA_FILE}")
        return None
    
    df = pd.read_csv(PROCESSED_DATA_FILE)
    
    # Risk categorization
    q_low = df['anomaly_score'].quantile(0.80)
    q_high = df['anomaly_score'].quantile(0.95)
    
    def categorize_risk(score):
        if score >= q_high:
            return "High"
        elif score >= q_low:
            return "Medium"
        else:
            return "Low"
    
    df['risk_level'] = df['anomaly_score'].apply(categorize_risk)
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"Loaded {len(df)} events from processed data")
    return df

def load_model():
    """Load the trained Isolation Forest model."""
    if not os.path.exists(MODEL_FILE):
        logger.warning(f"Model file not found: {MODEL_FILE}")
        return None
    
    try:
        model = joblib.load(MODEL_FILE)
        logger.info("Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

def load_model_metrics():
    """Load or calculate model metrics."""
    try:
        # Try to load from secure config first
        try:
            from config_secure import settings
            metrics_file = settings.MODEL_FILE.parent / "model_metrics.json"
        except ImportError:
            metrics_file = Path(MODEL_FILE).parent / "model_metrics.json"
        
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
                logger.info(f"Loaded metrics from {metrics_file}")
                return metrics
        else:
            logger.warning(f"Metrics file not found: {metrics_file}")
            logger.warning("Run model training to generate metrics.")
            return None
    except Exception as e:
        logger.error(f"Error loading metrics: {e}")
        return None

# =============================================================================
# STARTUP EVENT
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize data and model on startup."""
    logger.info("🚀 Starting VORTEX X-ADS API...")
    try:
        data_store.load()
        if data_store.is_loaded():
            logger.info("✅ API ready with data and model loaded")
        else:
            logger.warning("⚠️ API started but data/model not available")
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", summary="API Status Check")
def root():
    """Returns the API status and basic information."""
    return {
        "status": "ok",
        "project": "VORTEX X-ADS",
        "version": "2.0.0",
        "description": "Explainable Anomaly Detection System",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "risks": "/risks",
            "explain": "/explain/{event_id}",
            "user_risks": "/risks/user/{user_id}",
            "metrics": "/metrics",
            "pipeline": "/pipeline/*"
        }
    }

@app.get("/health", response_model=HealthStatus, summary="Detailed Health Check")
def health_check():
    """Returns detailed system health status."""
    try:
        data_loaded = data_store.is_loaded()
        model_exists = os.path.exists(MODEL_FILE)
        data_exists = os.path.exists(PROCESSED_DATA_FILE)
        
        total_events = len(data_store.df) if data_store.df is not None else None
        high_risk = None
        
        if data_store.df is not None:
            high_risk = len(data_store.df[data_store.df['risk_level'] == 'High'])
        
        return HealthStatus(
            status="healthy" if data_loaded else "degraded",
            timestamp=datetime.now().isoformat(),
            data_loaded=data_loaded,
            model_loaded=data_store.model is not None,
            total_events=total_events,
            high_risk_events=high_risk,
            model_file_exists=model_exists,
            processed_data_exists=data_exists
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risks", response_model=List[RiskEvent], summary="Get All Risk Events")
def get_risk_events(
    risk_level: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0
):
    """
    Returns filtered risk events.
    
    - **risk_level**: Filter by 'High', 'Medium', or 'Low' (optional)
    - **limit**: Maximum number of events to return (optional)
    - **offset**: Number of events to skip (pagination)
    """
    if not data_store.is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Service data not loaded. Run /pipeline/generate-data first."
        )
    
    df = data_store.df
    
    # Filter by risk level if specified
    if risk_level:
        if risk_level not in ['High', 'Medium', 'Low']:
            raise HTTPException(status_code=400, detail="Invalid risk_level. Use 'High', 'Medium', or 'Low'")
        df = df[df['risk_level'] == risk_level]
    else:
        # Default: show Medium and High risks
        df = df[df['risk_level'].isin(['Medium', 'High'])]
    
    # Sort by anomaly score descending
    df = df.sort_values(by='anomaly_score', ascending=False)
    
    # Apply pagination
    if limit:
        df = df.iloc[offset:offset + limit]
    else:
        df = df.iloc[offset:]
    
    if df.empty:
        return []
    
    alerts_list = df[[
        'event_id', 'user_id', 'timestamp', 'anomaly_score', 'risk_level', 'anomaly_flag_truth'
    ]].to_dict('records')
    
    return alerts_list

@app.get("/risks/user/{user_id}", response_model=UserRiskSummary, summary="Get User Risk Summary")
def get_user_risks(user_id: str, limit: int = 10):
    """
    Returns risk summary and recent events for a specific user.
    
    - **user_id**: User ID to analyze
    - **limit**: Number of recent events to include
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    user_df = data_store.df[data_store.df['user_id'] == user_id]
    
    if user_df.empty:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Calculate statistics
    total_events = len(user_df)
    high_risk = len(user_df[user_df['risk_level'] == 'High'])
    medium_risk = len(user_df[user_df['risk_level'] == 'Medium'])
    low_risk = len(user_df[user_df['risk_level'] == 'Low'])
    avg_score = float(user_df['anomaly_score'].mean())
    max_score = float(user_df['anomaly_score'].max())
    
    # Get recent events
    recent = user_df.sort_values(by='timestamp', ascending=False).head(limit)
    recent_events = recent[[
        'event_id', 'user_id', 'timestamp', 'anomaly_score', 'risk_level', 'anomaly_flag_truth'
    ]].to_dict('records')
    
    return UserRiskSummary(
        user_id=user_id,
        total_events=total_events,
        high_risk_events=high_risk,
        medium_risk_events=medium_risk,
        low_risk_events=low_risk,
        average_anomaly_score=avg_score,
        max_anomaly_score=max_score,
        recent_events=recent_events
    )

# =============================================================================
# Phase 2A: USER BASELINE ENDPOINTS
# =============================================================================

@app.get("/users", response_model=List[UserSummary], summary="Get All Users with Baselines")
def get_all_users():
    """
    Returns a list of all users with their baseline information.
    
    Useful for populating user selection dropdowns in frontend.
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.profile_manager is None:
        raise HTTPException(status_code=503, detail="User profiles not initialized")
    
    try:
        users = data_store.profile_manager.get_all_users()
        return [UserSummary(**user) for user in users]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/baseline", response_model=UserBaseline, summary="Get User Baseline Details")
def get_user_baseline(user_id: str):
    """
    Returns detailed baseline information for a specific user.
    
    Includes:
    - Baseline metrics (avg file access, upload sizes, typical hours, etc.)
    - Behavioral fingerprint (USB usage, sensitive file patterns, etc.)
    - Baseline risk level
    - Data quality/confidence metrics
    
    - **user_id**: User ID to get baseline for
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.profile_manager is None:
        raise HTTPException(status_code=503, detail="User profiles not initialized")
    
    try:
        profile = data_store.profile_manager.get_profile(user_id)
        
        if profile is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return UserBaseline(**profile.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting baseline for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/divergence/{event_id}", response_model=DivergenceAnalysis,
         summary="Get Divergence Analysis for Event")
def get_divergence_analysis(user_id: str, event_id: str):
    """
    Calculates how much an event diverges from the user's baseline behavior.
    
    Returns:
    - Divergence score (0.0 to 2.0+)
    - Divergence level (Low/Medium/High)
    - Detailed explanations of what diverged
    - Comparison with user's baseline
    
    - **user_id**: User ID
    - **event_id**: Event ID to analyze
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.profile_manager is None:
        raise HTTPException(status_code=503, detail="User profiles not initialized")
    
    try:
        # Get user profile
        profile = data_store.profile_manager.get_profile(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get event
        event_row = data_store.df[data_store.df['event_id'] == event_id]
        if event_row.empty:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        
        # Calculate divergence
        event = event_row.iloc[0]
        divergence = profile.calculate_divergence(event)
        
        return DivergenceAnalysis(**divergence)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating divergence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Phase 2A Session 3: RISK TRAJECTORY ENDPOINTS
# =============================================================================

@app.get("/users/{user_id}/trajectory", response_model=TrajectoryData, 
         summary="Get User Risk Trajectory")
def get_user_trajectory(user_id: str, lookback_days: Optional[int] = None):
    """
    Returns risk trajectory timeline for a user.
    
    Shows how user's risk has evolved over time with temporal decay.
    
    Args:
        user_id: User ID to analyze
        lookback_days: Optional number of days to include (default: all)
    
    Returns:
        Complete trajectory data with timeline, escalation status, trend
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.trajectory_manager is None:
        raise HTTPException(status_code=503, detail="Trajectory manager not initialized")
    
    try:
        trajectory = data_store.trajectory_manager.get_trajectory(user_id)
        
        if trajectory is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        # Get trajectory data (optionally filtered by lookback)
        timeline = trajectory.get_trajectory(lookback_days=lookback_days)
        
        # Build response
        escalation_details = None
        if hasattr(trajectory, 'escalation_details') and trajectory.escalation_details:
            escalation_details = EscalationDetails(**trajectory.escalation_details)
        
        return TrajectoryData(
            user_id=trajectory.user_id,
            trajectory=[TrajectoryTimepoint(**tp) for tp in timeline],
            current_cumulative_risk=trajectory.cumulative_risk,
            trend=trajectory.trend,
            is_escalating=trajectory.is_escalating,
            escalation_details=escalation_details,
            summary=trajectory.get_summary()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trajectory for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/escalation", summary="Get Escalation Analysis")
def get_escalation_analysis(user_id: str):
    """
    Returns detailed escalation analysis for a user.
    
    Analyzes whether user's risk is escalating by comparing recent vs previous activity.
    
    Args:
        user_id: User ID to analyze
        
    Returns:
        Escalation status, details, and severity
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.trajectory_manager is None:
        raise HTTPException(status_code=503, detail="Trajectory manager not initialized")
    
    try:
        trajectory = data_store.trajectory_manager.get_trajectory(user_id)
        
        if trajectory is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return {
            'user_id': user_id,
            'is_escalating': trajectory.is_escalating,
            'trend': trajectory.trend,
            'escalation_details': trajectory.escalation_details if hasattr(trajectory, 'escalation_details') else {},
            'current_cumulative_risk': trajectory.cumulative_risk,
            'recommendation': _get_escalation_recommendation(trajectory)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting escalation for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/trending-users", summary="Get Trending Users")
def get_trending_users(trend: str = 'escalating', limit: int = 20):
    """
    Returns users filtered by risk trend.
    
    Useful for identifying which users are escalating in risk.
    
    Args:
        trend: Filter by 'escalating', 'stable', or 'declining' (default: escalating)
        limit: Max number of users to return (default: 20)
        
    Returns:
        List of users matching trend criteria, sorted by cumulative risk
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.trajectory_manager is None:
        raise HTTPException(status_code=503, detail="Trajectory manager not initialized")
    
    try:
        if trend == 'escalating':
            users = data_store.trajectory_manager.get_escalating_users()
        else:
            users = data_store.trajectory_manager.get_users_by_trend(trend)
        
        # Limit results
        return users[:limit]
    except Exception as e:
        logger.error(f"Error getting trending users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/trajectory-statistics", response_model=TrajectoryStatistics,
         summary="Get Trajectory Statistics")
def get_trajectory_statistics():
    """
    Returns overall statistics across all user trajectories.
    
    Provides high-level metrics:
    - Total users tracked
    - Count by trend (escalating/stable/declining)
    - Average cumulative risk
    - Escalation rate percentage
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.trajectory_manager is None:
        raise HTTPException(status_code=503, detail="Trajectory manager not initialized")
    
    try:
        stats = data_store.trajectory_manager.get_statistics()
        return TrajectoryStatistics(**stats)
    except Exception as e:
        logger.error(f"Error getting trajectory statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_escalation_recommendation(trajectory: RiskTrajectory) -> str:
    """Generate recommendation based on escalation status."""
    if not trajectory.is_escalating:
        return "No immediate action required. Continue monitoring."
    
    severity = trajectory.escalation_details.get('severity', 'Low') if hasattr(trajectory, 'escalation_details') else 'Low'
    
    recommendations = {
        'Critical': "⚠️ URGENT: Immediate investigation required. User shows critical risk escalation.",
        'High': "⚠️ High priority: Schedule detailed review of user activity within 24 hours.",
        'Medium': "⚠️ Monitor closely: Increase monitoring frequency and review within 48 hours.",
        'Low': "ℹ️ Low priority: Continue monitoring and review at next scheduled interval."
    }
    
    return recommendations.get(severity, recommendations['Low'])


# =============================================================================
# Phase 2A Session 4: EVENT CHAIN ENDPOINTS
# =============================================================================

@app.get("/users/{user_id}/chains", response_model=List[EventChain], 
         summary="Get User Event Chains")
def get_user_chains(user_id: str, min_severity: Optional[str] = None):
    """
    Returns detected attack chains for a specific user.
    
    Chains are sequences of events that match known attack patterns
    (e.g., Data Exfiltration, Privilege Abuse).
    
    Args:
        user_id: User ID to analyze
        min_severity: Optional filter ('Medium', 'High', 'Critical')
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.chain_manager is None:
        raise HTTPException(status_code=503, detail="Chain manager not initialized")
    
    try:
        detector = data_store.chain_manager.get_detector(user_id)
        if detector is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        chains = detector.get_chains(min_severity=min_severity)
        
        # Format for response
        response = []
        for chain in chains:
            # Convert timestamp and nested events
            formatted_chain = chain.copy()
            formatted_chain['start_time'] = chain['start_time'].isoformat()
            formatted_chain['end_time'] = chain['end_time'].isoformat()
            
            formatted_events = []
            for evt in chain['events']:
                formatted_events.append({
                    'event_id': evt['event_id'],
                    'timestamp': evt['timestamp'].isoformat(),
                    'tags': list(evt['tags']),
                    'anomaly_score': evt['anomaly_score'],
                    'risk_level': evt['risk_level']
                })
            
            formatted_chain['events'] = formatted_events
            response.append(EventChain(**formatted_chain))
            
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chains for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}/chains/summary", response_model=ChainSummary,
         summary="Get User Chain Summary")
def get_user_chain_summary(user_id: str):
    """Returns a high-level summary of attack chains for a user."""
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.chain_manager is None:
        raise HTTPException(status_code=503, detail="Chain manager not initialized")
    
    try:
        detector = data_store.chain_manager.get_detector(user_id)
        if detector is None:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return ChainSummary(**detector.get_summary())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chain summary for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/chains", response_model=List[EventChain],
         summary="Get All Detected Chains")
def get_all_detected_chains(min_severity: Optional[str] = None, limit: int = 50):
    """
    Returns all detected attack chains across all users in the system.
    Sorted by chain risk (highest first).
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.chain_manager is None:
        raise HTTPException(status_code=503, detail="Chain manager not initialized")
    
    try:
        all_chains = data_store.chain_manager.get_all_chains(min_severity=min_severity)
        
        # Limit results
        all_chains = all_chains[:limit]
        
        # Format for response
        response = []
        for chain in all_chains:
            formatted_chain = chain.copy()
            formatted_chain['start_time'] = chain['start_time'].isoformat()
            formatted_chain['end_time'] = chain['end_time'].isoformat()
            
            formatted_events = []
            for evt in chain['events']:
                formatted_events.append({
                    'event_id': evt['event_id'],
                    'timestamp': evt['timestamp'].isoformat(),
                    'tags': list(evt['tags']),
                    'anomaly_score': evt['anomaly_score'],
                    'risk_level': evt['risk_level']
                })
            
            formatted_chain['events'] = formatted_events
            response.append(EventChain(**formatted_chain))
            
        return response
    except Exception as e:
        logger.error(f"Error getting all chains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/chain-statistics", response_model=ChainStatistics,
         summary="Get Chain Statistics")
def get_chain_statistics():
    """Returns global statistics about all detected attack chains."""
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    if data_store.chain_manager is None:
        raise HTTPException(status_code=503, detail="Chain manager not initialized")
    
    try:
        return ChainStatistics(**data_store.chain_manager.get_statistics())
    except Exception as e:
        logger.error(f"Error getting chain statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/explain/{event_id}", response_model=ExplanationResponse, summary="Get SHAP Explanation")
def get_explanation(event_id: str):
    """
    Generates SHAP explanation for a specific event.
    
    - **event_id**: The event ID to explain
    """
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    try:
        explanation_result = xai_pipeline(event_id=event_id)
        
        if explanation_result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Event ID {event_id} not found or explanation generation failed"
            )
        
        return explanation_result
    
    except Exception as e:
        logger.error(f"Explanation error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@app.get("/metrics", response_model=ModelMetrics, summary="Get Model Performance Metrics")
def get_metrics():
    """Returns model performance metrics if available."""
    if not data_store.is_loaded():
        raise HTTPException(status_code=503, detail="Service data not loaded")
    
    metrics = load_model_metrics()
    
    if metrics is None:
        # Calculate basic metrics from data
        df = data_store.df
        total_events = len(df)
        total_anomalies = int(df['anomaly_flag_truth'].sum())
        
        return ModelMetrics(
            auc_roc=0.0,
            f1_anomaly=0.0,
            precision_anomaly=0.0,
            recall_anomaly=0.0,
            total_events=total_events,
            total_anomalies=total_anomalies,
            model_last_trained=None
        )
    
    return ModelMetrics(**metrics)

# =============================================================================
# PIPELINE ENDPOINTS
# =============================================================================

@app.post("/pipeline/generate-data", response_model=PipelineStatus, summary="Generate Synthetic Data")
def pipeline_generate_data(background_tasks: BackgroundTasks):
    """
    Triggers synthetic data generation.
    This will create raw_behavior_logs.csv with synthetic insider threat data.
    """
    try:
        logger.info("Starting data generation...")
        generate_synthetic_logs()
        
        return PipelineStatus(
            task="generate_data",
            status="completed",
            message=f"Successfully generated synthetic data at {RAW_DATA_FILE}",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Data generation failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Data generation failed: {str(e)}")

@app.post("/pipeline/engineer-features", response_model=PipelineStatus, summary="Engineer Features")
def pipeline_engineer_features():
    """
    Triggers feature engineering pipeline.
    This processes raw data and creates processed_features.csv.
    """
    if not os.path.exists(RAW_DATA_FILE):
        raise HTTPException(
            status_code=404,
            detail="Raw data file not found. Run /pipeline/generate-data first."
        )
    
    try:
        logger.info("Starting feature engineering...")
        feature_engineering_pipeline()
        
        return PipelineStatus(
            task="engineer_features",
            status="completed",
            message=f"Successfully engineered features at {PROCESSED_DATA_FILE}",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Feature engineering failed: {str(e)}")

@app.post("/pipeline/train-model", response_model=PipelineStatus, summary="Train Anomaly Detection Model")
def pipeline_train_model():
    """
    Triggers model training pipeline.
    This trains the Isolation Forest model and saves it.
    """
    if not os.path.exists(PROCESSED_DATA_FILE):
        raise HTTPException(
            status_code=404,
            detail="Processed data not found. Run /pipeline/engineer-features first."
        )
    
    try:
        logger.info("Starting model training...")
        model_training_pipeline()
        
        # Reload data and model
        data_store.reload()
        
        return PipelineStatus(
            task="train_model",
            status="completed",
            message=f"Successfully trained model at {MODEL_FILE}",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Model training failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")

@app.post("/pipeline/run-all", response_model=List[PipelineStatus], summary="Run Full Pipeline")
def pipeline_run_all():
    """
    Runs the complete pipeline: Data Generation → Feature Engineering → Model Training.
    This is a comprehensive workflow that may take several minutes.
    """
    results = []
    
    try:
        # Step 1: Generate Data
        logger.info("Pipeline Step 1: Generating data...")
        generate_synthetic_logs()
        results.append(PipelineStatus(
            task="generate_data",
            status="completed",
            message="Data generation successful",
            timestamp=datetime.now().isoformat()
        ))
        
        # Step 2: Engineer Features
        logger.info("Pipeline Step 2: Engineering features...")
        feature_engineering_pipeline()
        results.append(PipelineStatus(
            task="engineer_features",
            status="completed",
            message="Feature engineering successful",
            timestamp=datetime.now().isoformat()
        ))
        
        # Step 3: Train Model
        logger.info("Pipeline Step 3: Training model...")
        model_training_pipeline()
        results.append(PipelineStatus(
            task="train_model",
            status="completed",
            message="Model training successful",
            timestamp=datetime.now().isoformat()
        ))
        
        # Reload data and model
        data_store.reload()
        
        logger.info("✅ Full pipeline completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}\n{traceback.format_exc()}")
        results.append(PipelineStatus(
            task="pipeline_run_all",
            status="failed",
            message=str(e),
            timestamp=datetime.now().isoformat()
        ))
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

@app.post("/reload", summary="Reload Data and Model")
def reload_data():
    """Forces a reload of data and model from disk."""
    try:
        data_store.reload()
        return {
            "status": "success",
            "message": "Data and model reloaded successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Reload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")

# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)