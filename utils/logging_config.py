import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(level=logging.INFO, log_file=None):
    """Setup logging configuration for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate a timestamped log file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"bot_run_{timestamp}.log"
    log_file_path = log_dir / log_file_name
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Also log to the general log.txt for convenience
    general_log_handler = logging.FileHandler("log.txt", encoding='utf-8')
    general_log_handler.setLevel(level)
    general_log_handler.setFormatter(formatter)
    root_logger.addHandler(general_log_handler)
    
    logging.info(f"Logging initialized. Log file: {log_file_path}")
    
    return root_logger