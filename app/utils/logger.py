"""
Logging configuration using Loguru
"""

import os
import sys
from loguru import logger as loguru_logger
from datetime import datetime

# Remove default handler
loguru_logger.remove()

# Get log level from environment
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_to_file = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'

# Console handler with colors
loguru_logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=log_level,
    colorize=True
)

# File handler for all logs
if log_to_file:
    loguru_logger.add(
        "logs/combined.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    # Error-only file handler
    loguru_logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

# Export logger
logger = loguru_logger
