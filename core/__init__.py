"""
Core modules for Resume Customizer application.

This package contains the core functionality including resume processing,
email handling, document processing, and async operations.
"""

# Core modules imports for easier access
try:
    from .resume_processor import *
    from .email_handler import *
    from .document_processor import *
    from .text_parser import *
    from .async_processor import *
    from .async_integration import *
except ImportError as e:
    # Handle missing dependencies gracefully
    pass

__version__ = "2.1.0"
__author__ = "Resume Customizer Team"


