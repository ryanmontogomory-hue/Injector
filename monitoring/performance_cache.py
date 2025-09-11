"""
High-performance caching system for Resume Customizer application.
Provides multi-level caching with TTL, LRU, and memory-aware eviction.
"""

import time
import threading
import hashlib
import pickle
import weakref
from typing import Any, Dict, Optional, Callable, Union, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
from functools import wraps
import psutil

from utilities.logger import get_logger

logger = get_logger()


@dataclass
class CacheEntry:
    """Cache entry with metadata and TTL support."""
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None
    
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        if self.ttl_seconds is None:
            return False
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)
    
    def touch(self) -> None:
        """Update access metadata."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class MemoryAwareLRUCache:
    """Memory-aware LRU cache with automatic eviction based on system memory."""
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 500, default_ttl: Optional[int] = 3600):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._total_size = 0
        self._hits = 0
        self._misses = 0
        
        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                self._remove_entry(key)
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._hits += 1
            
            logger.debug(f"Cache hit for key: {key[:50]}...")
            return entry.value
    
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Put value in cache."""
        with self._lock:
            # Calculate size
            try:
                size = len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
            except:
                size = 1024  # Fallback estimate
            
            # Check memory constraints
            if size > self.max_memory_bytes:
                logger.warning(f"Cache entry too large ({size} bytes), skipping")
                return
            
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Create new entry
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                size_bytes=size,
                ttl_seconds=ttl or self.default_ttl
            )
            
            self._cache[key] = entry
            self._total_size += size
            
            # Evict if necessary
            self._evict_if_necessary()
            
            logger.debug(f"Cache put for key: {key[:50]}... (size: {size} bytes)")
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache."""
        entry = self._cache.pop(key, None)
        if entry:
            self._total_size -= entry.size_bytes
    
    def _evict_if_necessary(self) -> None:
        """Evict entries based on size, memory, and LRU policy."""
        # Check memory pressure
        try:
            memory = psutil.virtual_memory()
            memory_pressure = memory.percent > 85
        except:
            memory_pressure = False
        
        # Evict expired entries first
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            self._remove_entry(key)
        
        # Evict based on memory pressure or cache size
        while (len(self._cache) > self.max_size or 
               self._total_size > self.max_memory_bytes or
               memory_pressure):
            
            if not self._cache:
                break
            
            # Remove least recently used
            key = next(iter(self._cache))
            self._remove_entry(key)
            
            # Recheck memory pressure
            try:
                memory_pressure = psutil.virtual_memory().percent > 85
            except:
                memory_pressure = False
    
    def _background_cleanup(self) -> None:
        """Background thread for cache maintenance."""
        while True:
            try:
                time.sleep(60)  # Run every minute
                with self._lock:
                    self._evict_if_necessary()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._total_size = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'total_size_mb': self._total_size / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'entries': [
                    {
                        'key': key[:50] + '...' if len(key) > 50 else key,
                        'size_kb': entry.size_bytes / 1024,
                        'age_seconds': (datetime.now() - entry.created_at).total_seconds(),
                        'access_count': entry.access_count
                    }
                    for key, entry in list(self._cache.items())[:10]  # Top 10 entries
                ]
            }


class CacheManager:
    """Central cache manager with multiple cache levels."""
    
    def __init__(self):
        # Different caches for different types of data
        self.document_cache = MemoryAwareLRUCache(max_size=100, max_memory_mb=200, default_ttl=1800)  # 30 min
        self.parsing_cache = MemoryAwareLRUCache(max_size=500, max_memory_mb=50, default_ttl=3600)   # 1 hour
        self.processing_cache = MemoryAwareLRUCache(max_size=200, max_memory_mb=100, default_ttl=900) # 15 min
        self.ui_cache = MemoryAwareLRUCache(max_size=1000, max_memory_mb=50, default_ttl=300)        # 5 min
        
    def get_cache(self, cache_type: str) -> MemoryAwareLRUCache:
        """Get specific cache by type."""
        caches = {
            'document': self.document_cache,
            'parsing': self.parsing_cache,
            'processing': self.processing_cache,
            'ui': self.ui_cache
        }
        return caches.get(cache_type, self.processing_cache)
    
    def clear_all(self) -> None:
        """Clear all caches."""
        for cache in [self.document_cache, self.parsing_cache, self.processing_cache, self.ui_cache]:
            cache.clear()
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all caches."""
        return {
            'document': self.document_cache.stats(),
            'parsing': self.parsing_cache.stats(),
            'processing': self.processing_cache.stats(),
            'ui': self.ui_cache.stats()
        }


# Global cache manager
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get singleton cache manager."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(cache_type: str = 'processing', ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            cache = cache_manager.get_cache(cache_type)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5('|'.join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the result
            cache.put(cache_key, result, ttl)
            
            logger.debug(f"Function {func.__name__} executed in {execution_time:.3f}s, result cached")
            return result
        
        # Add cache control methods
        wrapper.clear_cache = lambda: get_cache_manager().get_cache(cache_type).clear()
        wrapper.cache_stats = lambda: get_cache_manager().get_cache(cache_type).stats()
        
        return wrapper
    return decorator


def cache_key_for_file(file_obj, *args) -> str:
    """Generate cache key for file-based operations."""
    try:
        # Get file content hash for cache key
        if hasattr(file_obj, 'getvalue'):
            content = file_obj.getvalue()
        elif hasattr(file_obj, 'read'):
            pos = file_obj.tell() if hasattr(file_obj, 'tell') else 0
            content = file_obj.read()
            if hasattr(file_obj, 'seek'):
                file_obj.seek(pos)
        else:
            content = str(file_obj).encode()
        
        # Hash content + additional args
        key_parts = [hashlib.md5(content).hexdigest()]
        key_parts.extend(str(arg) for arg in args)
        
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    except Exception as e:
        logger.warning(f"Failed to generate file cache key: {e}")
        return hashlib.md5(str(time.time()).encode()).hexdigest()


def preload_cache():
    """Preload commonly used cache entries."""
    logger.info("Preloading cache with common operations...")
    # This can be extended to preload common patterns, templates, etc.
    pass



