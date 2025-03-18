import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def configure_logging(app_name='todolist', log_level=None):
    """
    Configure logging for the application.
    
    Args:
        app_name: The name of the application
        log_level: The log level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, defaults to INFO, or can be set via LOG_LEVEL env var
    """
    # Determine log level from environment or parameter
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {log_level}, defaulting to INFO")
        numeric_level = logging.INFO
    
    # Determine if we should log to console or file
    log_to_file = os.environ.get('LOG_TO_FILE', 'false').lower() == 'true'
    log_file_path = os.environ.get('LOG_FILE_PATH', '/var/log/todolist/app.log')
    
    # Create log directory if it doesn't exist and we're logging to file
    if log_to_file:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates during reloads
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    log_format = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    
    # Always add console handler for container logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Use rotating file handler to avoid filling up disk
        file_handler = RotatingFileHandler(
            log_file_path, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create application logger
    logger = logging.getLogger(app_name)
    logger.info(f"Logging configured with level {log_level}")
    
    return logger