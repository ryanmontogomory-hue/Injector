"""
Security enhancements module.
This module provides security utilities for the infrastructure layer.
"""
import hashlib
import secrets
import re
from typing import Dict, Any, Optional, List
from functools import wraps
import time

class SecurePasswordManager:
    """Manages secure password operations."""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password securely."""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{pwd_hash.hex()}"
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, pwd_hash = hashed.split(':')
            return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == pwd_hash
        except:
            return False

class InputSanitizer:
    """Sanitizes user input for security."""
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input."""
        if not isinstance(text, str):
            return ""
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', text)
        # Limit length
        return sanitized[:1000]
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage."""
        if not isinstance(filename, str):
            return "unnamed_file"
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        # Remove special characters except dots and underscores
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        # Limit length
        return filename[:100]

# Rate limiting functionality
_rate_limit_store = {}

def rate_limit(max_calls: int = 10, limit: int = None, window_seconds: int = 60, window: int = None):
    """Rate limiting decorator."""
    # Support both parameter names for backward compatibility
    if limit is not None:
        max_calls = limit
    if window is not None:
        window_seconds = window
        
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Clean old entries
            if func_name in _rate_limit_store:
                _rate_limit_store[func_name] = [
                    call_time for call_time in _rate_limit_store[func_name]
                    if now - call_time < window_seconds
                ]
            else:
                _rate_limit_store[func_name] = []
            
            # Check rate limit
            if len(_rate_limit_store[func_name]) >= max_calls:
                raise Exception(f"Rate limit exceeded for {func_name}")
            
            # Record this call
            _rate_limit_store[func_name].append(now)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate file type by extension."""
    if not filename:
        return False
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    return ext in [t.lower().strip('.') for t in allowed_types]

# Backward compatibility exports
__all__ = [
    'SecurePasswordManager',
    'InputSanitizer', 
    'rate_limit',
    'validate_email',
    'validate_file_type'
]
