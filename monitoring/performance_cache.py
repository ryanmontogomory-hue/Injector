"""
Performance cache module for backward compatibility.
"""
from typing import Any, Dict, Optional
import time
from threading import Lock

class CacheManager:
    """Simple cache manager for performance optimization."""
    
    def __init__(self):
        self._caches = {}
        self._lock = Lock()
    
    def get_cache(self, name: str) -> 'Cache':
        """Get or create a cache by name."""
        with self._lock:
            if name not in self._caches:
                self._caches[name] = Cache(name)
            return self._caches[name]
    
    def clear_all(self):
        """Clear all caches."""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()

class Cache:
    """Simple cache implementation."""
    
    def __init__(self, name: str, max_size: int = 100):
        self.name = name
        self.max_size = max_size
        self._data = {}
        self._access_times = {}
        self._lock = Lock()
    
    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        with self._lock:
            if key in self._data:
                self._access_times[key] = time.time()
                return self._data[key]
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            if len(self._data) >= self.max_size and key not in self._data:
                # Remove oldest entry
                oldest_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
                del self._data[oldest_key]
                del self._access_times[oldest_key]
            
            self._data[key] = value
            self._access_times[key] = time.time()
    
    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._data.clear()
            self._access_times.clear()
    
    def clear_expired(self, force: bool = False) -> None:
        """Clear expired entries."""
        if force:
            self.clear()

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

# Backward compatibility
__all__ = ['get_cache_manager', 'CacheManager', 'Cache']
