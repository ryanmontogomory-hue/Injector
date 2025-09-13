"""
Performance monitor module for backward compatibility.
"""
import time
import threading
from typing import Dict, Any, Optional
from collections import defaultdict

class PerformanceMonitor:
    """Simple performance monitoring utility."""
    
    def __init__(self):
        self._metrics = defaultdict(list)
        self._lock = threading.Lock()
        self._start_times = {}
    
    def start_operation(self, operation_name: str) -> str:
        """Start timing an operation."""
        operation_id = f"{operation_name}_{time.time()}"
        with self._lock:
            self._start_times[operation_id] = time.time()
        return operation_id
    
    def end_operation(self, operation_id: str) -> float:
        """End timing an operation and return duration."""
        end_time = time.time()
        with self._lock:
            if operation_id in self._start_times:
                start_time = self._start_times.pop(operation_id)
                duration = end_time - start_time
                operation_name = operation_id.split('_')[0]
                self._metrics[operation_name].append(duration)
                return duration
        return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        with self._lock:
            metrics = {}
            for operation, durations in self._metrics.items():
                if durations:
                    metrics[operation] = {
                        'count': len(durations),
                        'total_time': sum(durations),
                        'average_time': sum(durations) / len(durations),
                        'min_time': min(durations),
                        'max_time': max(durations)
                    }
            return metrics
    
    def clear_metrics(self):
        """Clear all metrics."""
        with self._lock:
            self._metrics.clear()
            self._start_times.clear()

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor

def cleanup_performance_monitor():
    """Cleanup performance monitor resources."""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.clear_metrics()
        _performance_monitor = None

# Backward compatibility
__all__ = ['get_performance_monitor', 'cleanup_performance_monitor', 'PerformanceMonitor']
