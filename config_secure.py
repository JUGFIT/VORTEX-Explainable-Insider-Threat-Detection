"""
Enhanced Security Configuration for VORTEX
This file contains secure configuration settings with environment variable support.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from datetime import time

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.
    Create a .env file in the project root to override these defaults.
    """
    
    # --- Data Paths ---
    DATA_DIR: Path = PROJECT_ROOT / "data"
    PROCESSED_DATA_FILE: Path = DATA_DIR / "processed_features.csv"
    RAW_DATA_FILE: Path = DATA_DIR / "raw_behavior_logs.csv"
    
    # --- Model Paths ---
    MODEL_DIR: Path = PROJECT_ROOT / "models"
    MODEL_FILE: Path = MODEL_DIR / "isolation_forest_model.pkl"
    
    # --- Model Security ---
    MODEL_HASH: Optional[str] = None
    VERIFY_MODEL_INTEGRITY: bool = False
    
    # --- API Security ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = PROJECT_ROOT / "logs" / "vortex.log"
    LOG_FORMAT: str = "json"
    
    # --- Model Training Parameters ---
    CONTAMINATION: float = 0.05
    N_ESTIMATORS: int = 100
    MAX_SAMPLES: int = 256
    RANDOM_STATE: int = 42
    
    # --- Feature Engineering ---
    TIME_WINDOW_HOURS: int = 24
    MIN_EVENTS_FOR_BASELINE: int = 10
    NORMAL_START_TIME: time = time(8, 0, 0)
    NORMAL_END_TIME: time = time(18, 0, 0)
    
    # --- Data Generation Parameters ---
    NUM_USERS: int = 50
    NUM_DAYS: int = 30
    BASE_EVENTS_PER_DAY: int = 15
    ANOMALY_RATE: float = 0.03
    
    # --- XAI Settings ---
    MAX_SHAP_SAMPLES: int = 1000
    SHAP_CHECK_ADDITIVITY: bool = False
    
    # --- Security Settings ---
    ALLOWED_FILE_EXTENSIONS: set[str] = {".csv", ".pkl", ".joblib"}
    MAX_FILE_SIZE_MB: int = 100
    SANITIZE_INPUTS: bool = True
    
    # --- Environment-specific settings ---
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATA_DIR.mkdir(exist_ok=True)
        self.MODEL_DIR.mkdir(exist_ok=True)
        self.LOG_FILE.parent.mkdir(exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    def get_model_hash_path(self) -> Path:
        return self.MODEL_FILE.with_suffix('.hash')


# Create a global settings instance
settings = Settings()

# Legacy compatibility - export constants for older code
PROCESSED_DATA_FILE = str(settings.PROCESSED_DATA_FILE)
MODEL_FILE = str(settings.MODEL_FILE)
RAW_DATA_FILE = str(settings.RAW_DATA_FILE)
DATA_DIR = str(settings.DATA_DIR)
MODEL_DIR = str(settings.MODEL_DIR)

# Model parameters (legacy compatibility)
CONTAMINATION = settings.CONTAMINATION
N_ESTIMATORS = settings.N_ESTIMATORS
MAX_SAMPLES = settings.MAX_SAMPLES
RANDOM_STATE = settings.RANDOM_STATE

# Data generation parameters (legacy compatibility)
NUM_USERS = settings.NUM_USERS
NUM_DAYS = settings.NUM_DAYS
BASE_EVENTS_PER_DAY = settings.BASE_EVENTS_PER_DAY
ANOMALY_RATE = settings.ANOMALY_RATE
TIME_WINDOW_HOURS = settings.TIME_WINDOW_HOURS
NORMAL_START_TIME = settings.NORMAL_START_TIME
NORMAL_END_TIME = settings.NORMAL_END_TIME


def validate_configuration():
    """Validate that all necessary paths and settings are correct."""
    errors = []
    
    if not settings.DATA_DIR.exists():
        errors.append(f"Data directory not found: {settings.DATA_DIR}")
    
    if not settings.MODEL_DIR.exists():
        errors.append(f"Model directory not found: {settings.MODEL_DIR}")
    
    if settings.is_production:
        if settings.DEBUG:
            errors.append("DEBUG mode should be disabled in production")
        if settings.API_RELOAD:
            errors.append("API auto-reload should be disabled in production")
        if not settings.VERIFY_MODEL_INTEGRITY:
            errors.append("Model integrity verification should be enabled in production")
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("VORTEX Configuration")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Data Directory: {settings.DATA_DIR}")
    print(f"Model Directory: {settings.MODEL_DIR}")
    print(f"Processed Data: {settings.PROCESSED_DATA_FILE}")
    print(f"Raw Data: {settings.RAW_DATA_FILE}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"API Host: {settings.API_HOST}:{settings.API_PORT}")
    print(f"Rate Limiting: {settings.RATE_LIMIT_ENABLED}")
    print(f"Model Verification: {settings.VERIFY_MODEL_INTEGRITY}")
    print("=" * 60)
    
    try:
        validate_configuration()
        print("✅ Configuration is valid")
    except ValueError as e:
        print(f"❌ Configuration errors:\n{e}")