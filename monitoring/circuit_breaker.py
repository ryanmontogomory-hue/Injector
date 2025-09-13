"""
Circuit breaker module for backward compatibility.
"""
import time
import threading
from typing import Any, Callable, Optional, List, Type
from functools import wraps
from enum import Enum

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Simple circuit breaker implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30, 
                 success_threshold: int = 2, timeout: float = 10.0,
                 expected_exceptions: List[Type[Exception]] = None):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            success_threshold: Number of successes needed to close circuit
            timeout: Operation timeout in seconds
            expected_exceptions: List of exceptions that trigger circuit opening
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exceptions = expected_exceptions or [Exception]
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if any(isinstance(e, exc_type) for exc_type in self.expected_exceptions):
                self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN

def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 30,
                   success_threshold: int = 2, timeout: float = 10.0,
                   expected_exceptions: List[Type[Exception]] = None):
    """
    Circuit breaker decorator.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting recovery
        success_threshold: Number of successes needed to close circuit
        timeout: Operation timeout in seconds
        expected_exceptions: List of exceptions that trigger circuit opening
        
    Returns:
        Decorated function with circuit breaker protection
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout, 
                           success_threshold, timeout, expected_exceptions)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

# Global circuit breakers registry
_circuit_breakers = {}

def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(**kwargs)
    return _circuit_breakers[name]

def reset_circuit_breaker(name: str):
    """Reset a named circuit breaker."""
    if name in _circuit_breakers:
        breaker = _circuit_breakers[name]
        with breaker._lock:
            breaker._state = CircuitState.CLOSED
            breaker._failure_count = 0
            breaker._success_count = 0
            breaker._last_failure_time = None

def smtp_circuit_breaker(*args, **kwargs):
    """Get SMTP-specific circuit breaker."""
    return get_circuit_breaker('smtp')

# Backward compatibility
__all__ = [
    'CircuitBreaker',
    'CircuitState', 
    'circuit_breaker',
    'get_circuit_breaker',
    'reset_circuit_breaker',
    'smtp_circuit_breaker'
]
