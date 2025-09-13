"""
Logger utilities for backward compatibility.
"""
import logging
from typing import Optional

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (defaults to calling module)
        
    Returns:
        Configured logger instance
    """
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # Configure basic logging if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

# Backward compatibility
__all__ = ['get_logger']
