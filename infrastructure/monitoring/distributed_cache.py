"""
Enhanced distributed caching system for Resume Customizer application.
Provides multi-level caching with Redis support, automatic failover, and smart eviction.
"""

import json
import pickle
import time
import hashlib
import threading
from typing import Any, Dict, Optional, Union, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import weakref

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .performance_cache import MemoryAwareLRUCache, CacheEntry
from utilities.logger import get_logger
from utilities.structured_logger import get_structured_logger

logger = get_logger()
structured_logger = get_structured_logger("distributed_cache")


@dataclass
class CacheConfig:
    """Configuration for distributed cache."""
    redis_url: Optional[str] = "redis://localhost:6379/0"
    redis_timeout: float = 5.0
    local_cache_size: int = 1000
    local_cache_ttl: int = 3600
    compression_threshold: int = 1024  # Compress values larger than this
    serialization_format: str = "pickle"  # "pickle" or "json"
    enable_compression: bool = True
    circuit_breaker_threshold: int = 3


class CacheSerializer:
    """Handles serialization/deserialization of cache values."""
    
    @staticmethod
    def serialize(value: Any, format_type: str = "pickle", compress: bool = False) -> bytes:
        """Serialize value to bytes."""
        try:
            if format_type == "json":
                serialized = json.dumps(value, default=str).encode('utf-8')
            else:  # pickle
                serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            
            if compress and len(serialized) > 1024:
                try:
                    import zlib
                    compressed = zlib.compress(serialized)
                    # Only use compression if it actually reduces size
                    if len(compressed) < len(serialized) * 0.9:
                        return b'COMPRESSED:' + compressed
                except ImportError:
                    pass
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    @staticmethod
    def deserialize(data: bytes, format_type: str = "pickle") -> Any:
        """Deserialize bytes to value."""
        try:
            # Check if compressed
            if data.startswith(b'COMPRESSED:'):
                try:
                    import zlib
                    data = zlib.decompress(data[11:])  # Remove 'COMPRESSED:' prefix
                except ImportError:
                    raise ValueError("Compressed data found but zlib not available")
            
            if format_type == "json":
                return json.loads(data.decode('utf-8'))
            else:  # pickle
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise


class RedisCache:
    """Redis-based cache with connection pooling and error handling."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client = None
        self.connection_pool = None
        self._connection_failures = 0
        self._last_failure_time = None
        self._lock = threading.RLock()
        
        if REDIS_AVAILABLE and config.redis_url:
            self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection with connection pooling."""
        try:
            self.connection_pool = redis.ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=20,
                socket_timeout=self.config.redis_timeout,
                socket_connect_timeout=self.config.redis_timeout,
                retry_on_timeout=True,
                decode_responses=False  # We handle bytes explicitly
            )
            
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            self.redis_client.ping()
            self._connection_failures = 0
            
            structured_logger.info(
                "Redis cache initialized successfully",
                operation="redis_init",
                url=self.config.redis_url
            )
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
            self.redis_client = None
            self._connection_failures += 1
            self._last_failure_time = time.time()
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open for Redis."""
        if self._connection_failures < self.config.circuit_breaker_threshold:
            return False
        
        if self._last_failure_time:
            # Try to reconnect after 60 seconds
            if time.time() - self._last_failure_time > 60:
                self._initialize_redis()
                return self._connection_failures >= self.config.circuit_breaker_threshold
        
        return True
    
    def get(self, key: str) -> Optional[bytes]:
        """Get value from Redis."""
        if not self.redis_client or self._is_circuit_open():
            return None
        
        try:
            with self._lock:
                result = self.redis_client.get(key)
                if result:
                    structured_logger.debug("Redis cache hit", operation="redis_get", key=key[:50])
                return result
                
        except Exception as e:
            self._connection_failures += 1
            self._last_failure_time = time.time()
            logger.warning(f"Redis get failed: {e}")
            return None
    
    def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """Set value in Redis."""
        if not self.redis_client or self._is_circuit_open():
            return False
        
        try:
            with self._lock:
                if ttl:
                    result = self.redis_client.setex(key, ttl, value)
                else:
                    result = self.redis_client.set(key, value)
                
                if result:
                    structured_logger.debug(
                        "Redis cache set",
                        operation="redis_set",
                        key=key[:50],
                        size_bytes=len(value),
                        ttl=ttl
                    )
                
                return bool(result)
                
        except Exception as e:
            self._connection_failures += 1
            self._last_failure_time = time.time()
            logger.warning(f"Redis set failed: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        if not self.redis_client or self._is_circuit_open():
            return False
        
        try:
            with self._lock:
                result = self.redis_client.delete(key)
                return bool(result)
                
        except Exception as e:
            self._connection_failures += 1
            self._last_failure_time = time.time()
            logger.warning(f"Redis delete failed: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all values from Redis."""
        if not self.redis_client or self._is_circuit_open():
            return False
        
        try:
            with self._lock:
                result = self.redis_client.flushdb()
                return bool(result)
                
        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        stats = {
            'available': self.redis_client is not None,
            'circuit_open': self._is_circuit_open(),
            'connection_failures': self._connection_failures,
            'last_failure_time': self._last_failure_time
        }
        
        if self.redis_client and not self._is_circuit_open():
            try:
                info = self.redis_client.info('memory')
                stats.update({
                    'used_memory': info.get('used_memory', 0),
                    'used_memory_human': info.get('used_memory_human', '0B'),
                    'connected_clients': self.redis_client.info('clients').get('connected_clients', 0)
                })
            except Exception as e:
                logger.warning(f"Could not get Redis stats: {e}")
        
        return stats


class DistributedCacheManager:
    """
    Multi-level cache manager with local cache (L1) and Redis cache (L2).
    Provides automatic failover, smart eviction, and performance monitoring.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.serializer = CacheSerializer()
        
        # L1 Cache: Local memory cache
        self.local_cache = MemoryAwareLRUCache(
            max_size=self.config.local_cache_size,
            default_ttl=self.config.local_cache_ttl
        )
        
        # L2 Cache: Distributed Redis cache
        self.redis_cache = RedisCache(self.config) if REDIS_AVAILABLE else None
        
        # Statistics
        self._stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0,
            'total_requests': 0
        }
        self._stats_lock = threading.Lock()
        
        structured_logger.info(
            "Distributed cache manager initialized",
            operation="cache_init",
            redis_available=REDIS_AVAILABLE,
            local_cache_size=self.config.local_cache_size
        )
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace."""
        return f"{namespace}:{hashlib.md5(key.encode()).hexdigest()}"
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2 -> miss)."""
        cache_key = self._generate_key(namespace, key)
        
        with self._stats_lock:
            self._stats['total_requests'] += 1
        
        try:
            # L1: Check local cache first
            local_result = self.local_cache.get(cache_key)
            if local_result is not None:
                with self._stats_lock:
                    self._stats['l1_hits'] += 1
                structured_logger.debug("L1 cache hit", operation="cache_get", namespace=namespace)
                return local_result
            
            # L2: Check Redis cache
            if self.redis_cache:
                redis_data = self.redis_cache.get(cache_key)
                if redis_data is not None:
                    try:
                        # Deserialize and store in L1
                        value = self.serializer.deserialize(
                            redis_data,
                            self.config.serialization_format
                        )
                        
                        # Store in L1 for faster future access
                        self.local_cache.put(cache_key, value, ttl=self.config.local_cache_ttl)
                        
                        with self._stats_lock:
                            self._stats['l2_hits'] += 1
                        
                        structured_logger.debug(
                            "L2 cache hit, promoted to L1",
                            operation="cache_get",
                            namespace=namespace
                        )
                        return value
                        
                    except Exception as e:
                        logger.warning(f"Failed to deserialize cache value: {e}")
                        # Remove corrupted data
                        self.redis_cache.delete(cache_key)
            
            # Cache miss
            with self._stats_lock:
                self._stats['misses'] += 1
            
            return None
            
        except Exception as e:
            with self._stats_lock:
                self._stats['errors'] += 1
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, 
           namespace: str, 
           key: str, 
           value: Any, 
           ttl: Optional[int] = None) -> bool:
        """Set value in cache (both L1 and L2)."""
        cache_key = self._generate_key(namespace, key)
        
        with self._stats_lock:
            self._stats['sets'] += 1
        
        try:
            # Set in L1 cache
            local_ttl = min(ttl or self.config.local_cache_ttl, self.config.local_cache_ttl)
            self.local_cache.put(cache_key, value, ttl=local_ttl)
            
            # Set in L2 cache
            if self.redis_cache:
                try:
                    serialized_data = self.serializer.serialize(
                        value,
                        self.config.serialization_format,
                        self.config.enable_compression
                    )
                    
                    self.redis_cache.set(cache_key, serialized_data, ttl)
                    
                    structured_logger.debug(
                        "Cache set in both L1 and L2",
                        operation="cache_set",
                        namespace=namespace,
                        size_bytes=len(serialized_data),
                        ttl=ttl
                    )
                    
                except Exception as e:
                    logger.warning(f"Failed to set L2 cache: {e}")
                    # L1 is still set, so partially successful
            
            return True
            
        except Exception as e:
            with self._stats_lock:
                self._stats['errors'] += 1
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache (both L1 and L2)."""
        cache_key = self._generate_key(namespace, key)
        
        try:
            # Delete from L1
            self.local_cache.clear()  # Simple clear for now
            
            # Delete from L2
            if self.redis_cache:
                self.redis_cache.delete(cache_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_namespace(self, namespace: str) -> bool:
        """Clear all values in a namespace."""
        try:
            # For simplicity, clear entire local cache
            self.local_cache.clear()
            
            # For Redis, we'd need to scan and delete by pattern
            # This is a simplified implementation
            if self.redis_cache:
                # In production, use SCAN with pattern matching
                logger.info(f"Namespace clear requested for: {namespace}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._stats_lock:
            stats = self._stats.copy()
        
        # Calculate hit rates
        total_hits = stats['l1_hits'] + stats['l2_hits']
        if stats['total_requests'] > 0:
            stats['hit_rate'] = total_hits / stats['total_requests']
            stats['l1_hit_rate'] = stats['l1_hits'] / stats['total_requests']
            stats['l2_hit_rate'] = stats['l2_hits'] / stats['total_requests']
        else:
            stats['hit_rate'] = 0
            stats['l1_hit_rate'] = 0
            stats['l2_hit_rate'] = 0
        
        # Add L1 cache stats
        stats['l1_cache'] = self.local_cache.stats()
        
        # Add L2 cache stats
        if self.redis_cache:
            stats['l2_cache'] = self.redis_cache.get_stats()
        else:
            stats['l2_cache'] = {'available': False}
        
        return stats


# Global distributed cache manager
_distributed_cache_manager = None
_cache_lock = threading.Lock()


def get_distributed_cache_manager(config: Optional[CacheConfig] = None) -> DistributedCacheManager:
    """Get global distributed cache manager instance."""
    global _distributed_cache_manager
    
    with _cache_lock:
        if _distributed_cache_manager is None:
            _distributed_cache_manager = DistributedCacheManager(config)
        return _distributed_cache_manager


def cached_distributed(namespace: str, 
                      ttl: Optional[int] = None,
                      key_func: Optional[Callable] = None):
    """
    Decorator for distributed caching.
    
    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments
    """
    def decorator(func: Callable) -> Callable:
        cache_manager = get_distributed_cache_manager()
        
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = "|".join(key_parts)
            
            # Try to get from cache
            result = cache_manager.get(namespace, cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(namespace, cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Convenience functions for common cache namespaces
def cached_processing(ttl: int = 3600):
    """Cache processing results."""
    return cached_distributed("processing", ttl)


def cached_parsing(ttl: int = 1800):
    """Cache text parsing results."""
    return cached_distributed("parsing", ttl)


def cached_document(ttl: int = 900):
    """Cache document operations."""
    return cached_distributed("document", ttl)



