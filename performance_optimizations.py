"""
Performance Optimization Module for Resume Customizer
Implements lazy loading, caching, and other performance improvements
"""

import streamlit as st
from functools import wraps
import time
from typing import Any, Callable, Dict, Optional

class PerformanceOptimizer:
    """Centralized performance optimization utilities."""
    
    def __init__(self):
        self._lazy_cache = {}
        self._import_cache = {}
    
    def lazy_import(self, module_name: str, import_path: str):
        """Lazy import a module only when needed."""
        if module_name not in self._import_cache:
            try:
                module = __import__(import_path, fromlist=[module_name])
                self._import_cache[module_name] = getattr(module, module_name)
            except ImportError as e:
                st.error(f"Failed to import {module_name}: {e}")
                return None
        return self._import_cache[module_name]
    
    def fast_cache(self, key: str, factory_func: Callable, ttl: int = 300):
        """Fast in-memory cache with TTL."""
        current_time = time.time()
        
        if key in self._lazy_cache:
            cached_item = self._lazy_cache[key]
            if current_time - cached_item['timestamp'] < ttl:
                return cached_item['value']
        
        # Cache expired or doesn't exist, create new
        value = factory_func()
        self._lazy_cache[key] = {
            'value': value,
            'timestamp': current_time
        }
        return value
    
    def clear_cache(self):
        """Clear all performance caches."""
        self._lazy_cache.clear()
        self._import_cache.clear()

# Global performance optimizer instance
perf_optimizer = PerformanceOptimizer()

def performance_timer(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Only log if execution takes more than 100ms
        if end_time - start_time > 0.1:
            st.sidebar.caption(f"⏱️ {func.__name__}: {end_time - start_time:.2f}s")
        
        return result
    return wrapper

@st.cache_resource
def get_optimized_ui_components():
    """Get UI components with performance optimizations."""
    return perf_optimizer.fast_cache(
        'ui_components',
        lambda: perf_optimizer.lazy_import('UIComponents', 'ui.components')()
    )

@st.cache_resource  
def get_optimized_requirements_manager():
    """Get requirements manager with lazy loading."""
    return perf_optimizer.fast_cache(
        'requirements_manager',
        lambda: perf_optimizer.lazy_import('RequirementsManager', 'ui.requirements_manager')()
    )

def optimize_streamlit_config():
    """Apply Streamlit-specific performance optimizations."""
    # Reduce rerun frequency
    if 'last_rerun' not in st.session_state:
        st.session_state.last_rerun = time.time()
    
    # Batch session state updates
    if 'pending_updates' not in st.session_state:
        st.session_state.pending_updates = {}

def batch_session_update(updates: Dict[str, Any]):
    """Batch multiple session state updates for better performance."""
    st.session_state.pending_updates.update(updates)
    
    # Apply updates if batch is large enough or timeout reached
    if (len(st.session_state.pending_updates) > 5 or 
        time.time() - st.session_state.last_rerun > 1.0):
        
        for key, value in st.session_state.pending_updates.items():
            st.session_state[key] = value
        
        st.session_state.pending_updates.clear()
        st.session_state.last_rerun = time.time()

def preload_critical_modules():
    """Preload only the most critical modules at startup."""
    critical_modules = [
        ('logger', 'infrastructure.utilities.logger'),
        ('config', 'config'),
    ]
    
    for module_name, import_path in critical_modules:
        perf_optimizer.lazy_import(module_name, import_path)

# Performance monitoring
class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.metrics[operation] = {'start': time.time()}
    
    def end_timer(self, operation: str):
        """End timing an operation."""
        if operation in self.metrics:
            self.metrics[operation]['duration'] = time.time() - self.metrics[operation]['start']
    
    def get_metrics(self) -> Dict[str, float]:
        """Get all performance metrics."""
        return {op: data.get('duration', 0) for op, data in self.metrics.items()}
    
    def display_metrics(self):
        """Display performance metrics in sidebar."""
        metrics = self.get_metrics()
        if metrics:
            with st.sidebar.expander("⚡ Performance Metrics", expanded=False):
                for operation, duration in metrics.items():
                    if duration > 0:
                        color = "🔴" if duration > 1.0 else "🟡" if duration > 0.5 else "🟢"
                        st.caption(f"{color} {operation}: {duration:.2f}s")

# Global performance monitor
perf_monitor = PerformanceMonitor()
