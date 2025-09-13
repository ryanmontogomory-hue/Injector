"""
Retry handler utilities for robust operation handling.
"""
import time
import logging
from typing import Any, Callable, Optional, Type, Union, Tuple
from functools import wraps

class RetryHandler:
    """Handles retry logic for operations that may fail temporarily."""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """
        Initialize retry handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries in seconds
            backoff: Backoff multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        current_delay = self.delay
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= self.backoff
                else:
                    logging.error(f"All {self.max_retries + 1} attempts failed. Last error: {e}")
        
        # If we get here, all retries failed
        raise last_exception

def retry_operation(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0, 
                   exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for exponential backoff
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logging.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logging.error(f"{func.__name__} all {max_retries + 1} attempts failed. Last error: {e}")
                except Exception as e:
                    # Don't retry for exceptions not in the exceptions tuple
                    raise e
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator

# Convenience functions
def retry_with_exponential_backoff(func: Callable, max_retries: int = 3, 
                                 initial_delay: float = 1.0, max_delay: float = 60.0) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Function result
    """
    handler = RetryHandler(max_retries, initial_delay, 2.0)
    return handler.execute(func)

def retry_network_operation(func: Callable, *args, **kwargs) -> Any:
    """
    Retry a network operation with appropriate settings.
    
    Args:
        func: Network function to retry
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    @retry_operation(max_retries=5, delay=2.0, backoff=1.5, 
                    exceptions=(ConnectionError, TimeoutError, OSError))
    def network_func():
        return func(*args, **kwargs)
    
    return network_func()

def retry_file_operation(func: Callable, *args, **kwargs) -> Any:
    """
    Retry a file operation with appropriate settings.
    
    Args:
        func: File function to retry
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    @retry_operation(max_retries=3, delay=0.5, backoff=2.0, 
                    exceptions=(OSError, IOError, PermissionError))
    def file_func():
        return func(*args, **kwargs)
    
    return file_func()

def get_retry_handler(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0) -> RetryHandler:
    """
    Get a configured retry handler instance.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for exponential backoff
        
    Returns:
        Configured RetryHandler instance
    """
    return RetryHandler(max_retries, delay, backoff)

def with_retry(max_retries: int = 3, max_attempts: int = None, delay: float = 1.0, 
               base_delay: float = None, backoff: float = 2.0):
    """
    Decorator alias for retry_operation for backward compatibility.
    
    Args:
        max_retries: Maximum number of retry attempts
        max_attempts: Alternative parameter name for max_retries (for compatibility)
        delay: Initial delay between retries in seconds
        base_delay: Alternative parameter name for delay (for compatibility)
        backoff: Backoff multiplier for exponential backoff
        
    Returns:
        Decorator function
    """
    # Support both parameter names for backward compatibility
    if max_attempts is not None:
        max_retries = max_attempts
    if base_delay is not None:
        delay = base_delay
    return retry_operation(max_retries, delay, backoff)

# Backward compatibility
__all__ = [
    'RetryHandler',
    'retry_operation',
    'retry_with_exponential_backoff',
    'retry_network_operation',
    'retry_file_operation',
    'get_retry_handler',
    'with_retry'
]
