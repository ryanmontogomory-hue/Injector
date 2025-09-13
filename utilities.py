"""
Utilities module for backward compatibility.
This module provides utility functions that were previously imported directly.
"""
import os
import sys
import logging
from typing import Any, Dict, Optional, List
import tempfile
import shutil

def get_temp_directory() -> str:
    """Get a temporary directory for file operations."""
    return tempfile.gettempdir()

def ensure_directory_exists(path: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def safe_file_operation(func, *args, **kwargs):
    """Safely execute a file operation with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"File operation failed: {e}")
        return None

def cleanup_temp_files(directory: str) -> None:
    """Clean up temporary files in a directory."""
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    except Exception as e:
        logging.error(f"Failed to cleanup temp files: {e}")

def get_file_size(filepath: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

def is_valid_file_path(filepath: str) -> bool:
    """Check if a file path is valid and exists."""
    return os.path.isfile(filepath)

# Backward compatibility exports
__all__ = [
    'get_temp_directory',
    'ensure_directory_exists', 
    'safe_file_operation',
    'cleanup_temp_files',
    'get_file_size',
    'is_valid_file_path'
]
