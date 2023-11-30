import logging
import logging.handlers
import sys
from pathlib import Path

def setup_logging():
    """Setup logging configuration for the Digital Twin platform"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Configure specific loggers
    loggers = {
        "uvicorn": logging.INFO,
        "fastapi": logging.INFO,
        "sqlalchemy": logging.WARNING,
        "mqtt": logging.INFO,
        "opcua": logging.INFO,
        "data_processing": logging.INFO
    }
    
    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    logging.info("Digital Twin Data Integration Platform logging initialized")