"""
Circuit breaker pattern implementation for Resume Customizer application.
Provides resilience against cascading failures in database and external services.
"""

import time
import threading
from typing import Any, Callable, Optional, Dict, Type
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
try:
    import psycopg2
except ImportError:
    psycopg2 = None
import smtplib

from utilities.logger import get_logger
from utilities.structured_logger import get_structured_logger

logger = get_logger()
structured_logger = get_structured_logger("circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: int = 30
    success_threshold: int = 2  # For half-open state
    timeout: float = 10.0
    expected_exceptions: tuple = field(default_factory=lambda: (Exception,))


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with thread safety and monitoring.
    """
    
    def __init__(self, 
                 name: str,
                 config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._lock = threading.RLock()
        
        # Monitoring
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        self._circuit_opened_count = 0
        
        # Create a JSON-serializable version of config
        config_dict = {
            'failure_threshold': self.config.failure_threshold,
            'recovery_timeout': self.config.recovery_timeout,
            'success_threshold': self.config.success_threshold,
            'timeout': self.config.timeout,
            'expected_exceptions': [str(exc) for exc in self.config.expected_exceptions]
        }
        structured_logger.info(
            f"Circuit breaker '{name}' initialized",
            operation="circuit_breaker_init",
            config=config_dict
        )
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator usage."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        with self._lock:
            self._total_calls += 1
            
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    structured_logger.info(
                        f"Circuit breaker '{self.name}' transitioning to HALF_OPEN",
                        operation="circuit_breaker_transition"
                    )
                else:
                    self._failed_calls += 1
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Last failure: {self._last_failure_time}"
                    )
            
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                self._on_success(duration)
                return result
                
            except self.config.expected_exceptions as e:
                self._on_failure(e)
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset."""
        return (self._last_failure_time and 
                time.time() - self._last_failure_time >= self.config.recovery_timeout)
    
    def _on_success(self, duration: float):
        """Handle successful call."""
        self._successful_calls += 1
        
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._reset()
                structured_logger.info(
                    f"Circuit breaker '{self.name}' reset to CLOSED",
                    operation="circuit_breaker_reset",
                    duration_ms=duration * 1000
                )
        else:
            self._failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed call."""
        self._failed_calls += 1
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.config.failure_threshold:
            self._trip()
        
        structured_logger.error(
            f"Circuit breaker '{self.name}' failure #{self._failure_count}",
            operation="circuit_breaker_failure",
            exception=exception,
            failure_count=self._failure_count,
            threshold=self.config.failure_threshold
        )
    
    def _trip(self):
        """Trip the circuit breaker to OPEN state."""
        self._state = CircuitState.OPEN
        self._circuit_opened_count += 1
        
        structured_logger.warning(
            f"Circuit breaker '{self.name}' OPENED",
            operation="circuit_breaker_trip",
            failure_count=self._failure_count,
            recovery_timeout=self.config.recovery_timeout
        )
    
    def _reset(self):
        """Reset circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
    
    def force_open(self):
        """Manually open the circuit breaker."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = time.time()
            structured_logger.warning(
                f"Circuit breaker '{self.name}' manually OPENED",
                operation="circuit_breaker_manual_open"
            )
    
    def force_close(self):
        """Manually close the circuit breaker."""
        with self._lock:
            self._reset()
            structured_logger.info(
                f"Circuit breaker '{self.name}' manually CLOSED",
                operation="circuit_breaker_manual_close"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._lock:
            success_rate = (
                self._successful_calls / self._total_calls 
                if self._total_calls > 0 else 0
            )
            
            return {
                'name': self.name,
                'state': self._state.value,
                'total_calls': self._total_calls,
                'successful_calls': self._successful_calls,
                'failed_calls': self._failed_calls,
                'success_rate': success_rate,
                'failure_count': self._failure_count,
                'circuit_opened_count': self._circuit_opened_count,
                'last_failure_time': self._last_failure_time,
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout': self.config.recovery_timeout,
                    'success_threshold': self.config.success_threshold
                }
            }


class CircuitBreakerManager:
    """Manages multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
    
    def get_breaker(self, 
                   name: str, 
                   config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        with self._lock:
            return {name: breaker.get_stats() 
                   for name, breaker in self._breakers.items()}


# Global circuit breaker manager
_circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker(name: str, 
                       config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """Get circuit breaker instance."""
    return _circuit_breaker_manager.get_breaker(name, config)


# Predefined circuit breakers for common services
# Create database circuit breaker with optional psycopg2 support
db_exceptions = [ConnectionError, TimeoutError]
if psycopg2 is not None:
    db_exceptions.append(psycopg2.Error)

DATABASE_BREAKER = get_circuit_breaker(
    "database",
    CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=30,
        expected_exceptions=tuple(db_exceptions)
    )
)

SMTP_BREAKER = get_circuit_breaker(
    "smtp",
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=60,
        expected_exceptions=(smtplib.SMTPException, ConnectionError, TimeoutError)
    )
)

FILE_PROCESSING_BREAKER = get_circuit_breaker(
    "file_processing",
    CircuitBreakerConfig(
        failure_threshold=10,
        recovery_timeout=30,
        expected_exceptions=(IOError, MemoryError, ValueError)
    )
)


def database_circuit_breaker(func: Callable) -> Callable:
    """Decorator for database operations."""
    return DATABASE_BREAKER(func)


def smtp_circuit_breaker(func: Callable) -> Callable:
    """Decorator for SMTP operations."""
    return SMTP_BREAKER(func)


def file_processing_circuit_breaker(func: Callable) -> Callable:
    """Decorator for file processing operations."""
    return FILE_PROCESSING_BREAKER(func)



