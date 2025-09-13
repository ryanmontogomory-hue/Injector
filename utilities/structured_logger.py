"""
Structured logger module for backward compatibility.
"""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime

class StructuredLogger:
    """Logger that outputs structured JSON logs."""
    
    def __init__(self, name: str = None):
        self.logger = logging.getLogger(name or __name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_structured(self, level: str, message: str, **kwargs):
        """Log a structured message."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'message': message,
            **kwargs
        }
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.log_structured('info', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.log_structured('error', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.log_structured('warning', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.log_structured('debug', message, **kwargs)

def get_structured_logger(name: str = None) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)

# Create a default processing logger instance
processing_logger = get_structured_logger("processing")

# Backward compatibility
__all__ = ['StructuredLogger', 'get_structured_logger', 'processing_logger']
