"""
Monitoring modules for Resume Customizer application.

This package contains performance monitoring, caching, circuit breaker,
and distributed cache functionality.
"""

# Monitoring modules imports for easier access
try:
    from .performance_monitor import *
    from .circuit_breaker import *
    from .distributed_cache import *
    from .performance_cache import *
except ImportError as e:
    # Handle missing dependencies gracefully
    pass

__version__ = "2.1.0"
__author__ = "Resume Customizer Team"



