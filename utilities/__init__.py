"""
Utility modules for Resume Customizer application.

This package contains helper utilities including logging, validation,
memory optimization, and retry handling.
"""

# Utility modules imports for easier access
try:
    from .logger import *
    from .validators import *
    from .memory_optimizer import *
    from .structured_logger import *
    from .lazy_imports import *
    from .retry_handler import *
except ImportError as e:
    # Handle missing dependencies gracefully
    pass

__version__ = "2.1.0"
__author__ = "Resume Customizer Team"



