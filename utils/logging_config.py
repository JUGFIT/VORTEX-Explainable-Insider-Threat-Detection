"""
Structured logging configuration for VORTEX
Provides JSON logging for production and readable logs for development.
"""

import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger

# Try to import settings, fallback to defaults if not available
try:
    from config_secure import settings
except ImportError:
    class FallbackSettings:
        LOG_LEVEL = "INFO"
        LOG_FILE = Path("logs/vortex.log")
        LOG_FORMAT = "json"
        ENVIRONMENT = "development"
    settings = FallbackSettings()


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context."""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add custom fields
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add environment info
        log_record['environment'] = settings.ENVIRONMENT


def setup_logging(
    name: str = "vortex",
    log_level: str = None,
    log_file: Path = None,
    log_format: str = None
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Format type ("json" or "text")
    
    Returns:
        Configured logger instance
    """
    
    # Use settings defaults if not provided
    log_level = log_level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    log_format = log_format or settings.LOG_FORMAT
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if log_format.lower() == "json":
        # JSON format for production
        json_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        console_handler.setFormatter(json_formatter)
    else:
        # Human-readable format for development
        text_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(text_formatter)
    
    logger.addHandler(console_handler)
    
    # File handler (always JSON for easier parsing)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        json_formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the current configuration.
    
    Args:
        name: Logger name (uses calling module name if not provided)
    
    Returns:
        Logger instance
    """
    if name is None:
        # Get the name of the calling module
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals['__name__']
    
    # Return existing logger or create new one
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up
    if not logger.handlers:
        return setup_logging(name)
    
    return logger


# Create default logger for the application
default_logger = setup_logging()


if __name__ == "__main__":
    # Test logging
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test with extra context
    logger.info("User action", extra={
        'user_id': 'user123',
        'action': 'view_dashboard',
        'event_id': 'evt_456'
    })
    
    print(f"\n✅ Logs written to: {settings.LOG_FILE}")
    print(f"Log format: {settings.LOG_FORMAT}")
    print(f"Log level: {settings.LOG_LEVEL}")