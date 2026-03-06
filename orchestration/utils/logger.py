"""
Logging utility for EVA system
Provides colored console output and file logging with agent decision tracking
"""

import logging
import os
from datetime import datetime
from pathlib import Path
import colorlog


class EVALogger:
    """Custom logger for EVA with colored output and agent tracking"""
    
    def __init__(self, name: str = "EVA", log_file: str = "logs/eva.log", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create logs directory if it doesn't exist
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler with colors
        console_handler = colorlog.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_format = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def critical(self, message: str):
        self.logger.critical(message)
    
    def agent_decision(self, agent_name: str, decision: str, details: dict = None):
        """Log agent decision with structured format"""
        message = f"[{agent_name}] Decision: {decision}"
        if details:
            message += f" | Details: {details}"
        self.info(message)
    
    def agent_input(self, agent_name: str, input_data: str):
        """Log agent input"""
        self.debug(f"[{agent_name}] Input: {input_data[:200]}...")
    
    def agent_output(self, agent_name: str, output_data: str):
        """Log agent output"""
        self.debug(f"[{agent_name}] Output: {output_data[:200]}...")
    
    def tool_call(self, tool_name: str, parameters: dict):
        """Log tool invocation"""
        self.info(f"[TOOL] Calling {tool_name} with params: {parameters}")
    
    def tool_result(self, tool_name: str, result: str):
        """Log tool result"""
        self.debug(f"[TOOL] {tool_name} result: {result[:200]}...")


# Global logger instance
_logger_instance = None


def get_logger(name: str = "EVA", log_file: str = "logs/eva.log", level: str = "INFO") -> EVALogger:
    """Get or create logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = EVALogger(name, log_file, level)
    return _logger_instance

# Made with Bob
