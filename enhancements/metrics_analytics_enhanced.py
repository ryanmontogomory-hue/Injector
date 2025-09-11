"""
Advanced metrics collection and analytics system for Resume Customizer application.
Provides comprehensive performance monitoring, user analytics, and business intelligence.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
import json
import hashlib

from utilities.logger import get_logger
from utilities.structured_logger import get_structured_logger

logger = get_logger()
structured_logger = get_structured_logger("metrics_analytics")


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricPoint:
    """Individual metric data point."""
    timestamp: datetime
    value: Union[int, float]
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'labels': self.labels
        }


@dataclass
class Metric:
    """Metric definition and data storage."""
    name: str
    metric_type: MetricType
    description: str
    unit: str = ""
    labels: List[str] = field(default_factory=list)
    data_points: deque = field(default_factory=lambda: deque(maxlen=10000))
    
    def add_point(self, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Add a data point to the metric."""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            labels=labels or {}
        )
        self.data_points.append(point)
    
    def get_current_value(self) -> Optional[Union[int, float]]:
        """Get the most recent value."""
        if not self.data_points:
            return None
        return self.data_points[-1].value
    
    def get_values_in_range(self, start: datetime, end: datetime) -> List[MetricPoint]:
        """Get all values within a time range."""
        return [
            point for point in self.data_points
            if start <= point.timestamp <= end
        ]


class ApplicationMetrics:
    """
    Advanced metrics collection system with performance monitoring,
    user analytics, and business intelligence.
    """
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self._lock = threading.RLock()
        self.start_time = datetime.utcnow()
        
        # Initialize core metrics
        self._initialize_core_metrics()
        
        # Background statistics calculation
        self._stats_cache = {}
        self._last_stats_calculation = datetime.utcnow()
        
        structured_logger.info(
            "Advanced metrics system initialized",
            operation="metrics_init"
        )
    
    def _initialize_core_metrics(self):
        """Initialize core application metrics."""
        core_metrics = [
            # Performance Metrics
            Metric("app_requests_total", MetricType.COUNTER, "Total number of requests", labels=["operation", "status"]),
            Metric("app_request_duration_seconds", MetricType.HISTOGRAM, "Request duration in seconds", "seconds", ["operation"]),
            Metric("app_errors_total", MetricType.COUNTER, "Total number of errors", labels=["type", "severity"]),
            
            # Resource Metrics
            Metric("app_memory_usage_bytes", MetricType.GAUGE, "Memory usage in bytes", "bytes"),
            Metric("app_cpu_usage_percent", MetricType.GAUGE, "CPU usage percentage", "%"),
            Metric("app_cache_hit_rate", MetricType.GAUGE, "Cache hit rate", "%", ["cache_type"]),
            
            # Business Metrics
            Metric("resumes_processed_total", MetricType.COUNTER, "Total resumes processed", labels=["status"]),
            Metric("resumes_processing_time_seconds", MetricType.HISTOGRAM, "Resume processing time", "seconds"),
            Metric("emails_sent_total", MetricType.COUNTER, "Total emails sent", labels=["status", "template"]),
            Metric("user_sessions_total", MetricType.COUNTER, "Total user sessions", labels=["user_type"]),
            
            # Quality Metrics
            Metric("processing_success_rate", MetricType.GAUGE, "Processing success rate", "%"),
            Metric("email_delivery_rate", MetricType.GAUGE, "Email delivery rate", "%"),
            Metric("user_satisfaction_score", MetricType.GAUGE, "User satisfaction score", "score"),
            
            # System Metrics
            Metric("circuit_breaker_trips", MetricType.COUNTER, "Circuit breaker trips", labels=["service"]),
            Metric("database_queries_total", MetricType.COUNTER, "Database queries", labels=["operation", "status"]),
            Metric("database_query_duration_seconds", MetricType.HISTOGRAM, "Database query duration", "seconds"),
        ]
        
        for metric in core_metrics:
            self.metrics[metric.name] = metric
    
    def record_counter(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Record a counter metric."""
        with self._lock:
            metric = self.metrics.get(metric_name)
            if not metric:
                logger.warning(f"Metric {metric_name} not found")
                return
            
            if metric.metric_type != MetricType.COUNTER:
                logger.error(f"Metric {metric_name} is not a counter")
                return
            
            # For counters, add to the previous value
            current = metric.get_current_value() or 0
            metric.add_point(current + value, labels)
    
    def record_gauge(self, metric_name: str, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Record a gauge metric."""
        with self._lock:
            metric = self.metrics.get(metric_name)
            if not metric:
                logger.warning(f"Metric {metric_name} not found")
                return
            
            if metric.metric_type != MetricType.GAUGE:
                logger.error(f"Metric {metric_name} is not a gauge")
                return
            
            metric.add_point(value, labels)
    
    def record_histogram(self, metric_name: str, value: Union[int, float], labels: Optional[Dict[str, str]] = None):
        """Record a histogram metric."""
        with self._lock:
            metric = self.metrics.get(metric_name)
            if not metric:
                logger.warning(f"Metric {metric_name} not found")
                return
            
            if metric.metric_type != MetricType.HISTOGRAM:
                logger.error(f"Metric {metric_name} is not a histogram")
                return
            
            metric.add_point(value, labels)
    
    def record_timer(self, metric_name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record a timer metric."""
        self.record_histogram(metric_name, duration, labels)
    
    def get_metric_summary(self, metric_name: str, time_range_minutes: int = 60) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a metric over a time range."""
        with self._lock:
            metric = self.metrics.get(metric_name)
            if not metric:
                return None
            
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_range_minutes)
            
            points = metric.get_values_in_range(start_time, end_time)
            if not points:
                return None
            
            values = [p.value for p in points]
            
            summary = {
                'metric_name': metric_name,
                'metric_type': metric.metric_type.value,
                'time_range_minutes': time_range_minutes,
                'data_points': len(values),
                'current_value': values[-1] if values else None,
                'statistics': self._calculate_statistics(values, metric.metric_type)
            }
            
            return summary
    
    def _calculate_statistics(self, values: List[Union[int, float]], metric_type: MetricType) -> Dict[str, Any]:
        """Calculate statistics for a list of values."""
        if not values:
            return {}
        
        stats = {
            'count': len(values),
            'min': min(values),
            'max': max(values)
        }
        
        if metric_type == MetricType.HISTOGRAM or metric_type == MetricType.TIMER:
            stats.update({
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99),
                'stddev': statistics.stdev(values) if len(values) > 1 else 0
            })
        elif metric_type == MetricType.GAUGE:
            stats.update({
                'mean': statistics.mean(values),
                'latest': values[-1]
            })
        elif metric_type == MetricType.COUNTER:
            stats.update({
                'total': values[-1],
                'rate_per_minute': self._calculate_rate(values)
            })
        
        return stats
    
    def _percentile(self, values: List[Union[int, float]], percentile: int) -> float:
        """Calculate percentile of values."""
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f == len(sorted_values) - 1:
            return sorted_values[f]
        else:
            return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
    
    def _calculate_rate(self, values: List[Union[int, float]]) -> float:
        """Calculate rate per minute for counter values."""
        if len(values) < 2:
            return 0.0
        
        # Approximate rate based on first and last values
        # This is simplified - in practice, you'd want more sophisticated rate calculation
        return (values[-1] - values[0]) / max(1, len(values) / 60)
    
    def get_all_metrics_summary(self, time_range_minutes: int = 60) -> Dict[str, Dict[str, Any]]:
        """Get summary for all metrics."""
        summaries = {}
        
        for metric_name in self.metrics:
            summary = self.get_metric_summary(metric_name, time_range_minutes)
            if summary:
                summaries[metric_name] = summary
        
        return summaries
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data formatted for dashboard display."""
        uptime = datetime.utcnow() - self.start_time
        
        # Get key performance indicators
        kpis = {
            'uptime_hours': uptime.total_seconds() / 3600,
            'total_requests': self._get_current_counter_value('app_requests_total'),
            'total_resumes_processed': self._get_current_counter_value('resumes_processed_total'),
            'total_emails_sent': self._get_current_counter_value('emails_sent_total'),
            'current_memory_mb': self._get_current_gauge_value('app_memory_usage_bytes', 0) / (1024 * 1024),
            'current_cpu_percent': self._get_current_gauge_value('app_cpu_usage_percent'),
            'processing_success_rate': self._get_current_gauge_value('processing_success_rate'),
            'cache_hit_rate': self._get_current_gauge_value('app_cache_hit_rate')
        }
        
        # Get recent performance data
        recent_performance = {}
        performance_metrics = [
            'app_request_duration_seconds',
            'resumes_processing_time_seconds',
            'database_query_duration_seconds'
        ]
        
        for metric in performance_metrics:
            summary = self.get_metric_summary(metric, 15)  # Last 15 minutes
            if summary:
                recent_performance[metric] = summary['statistics']
        
        return {
            'kpis': kpis,
            'recent_performance': recent_performance,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': uptime.total_seconds()
        }
    
    def _get_current_counter_value(self, metric_name: str) -> int:
        """Get current value of a counter metric."""
        metric = self.metrics.get(metric_name)
        if metric and metric.metric_type == MetricType.COUNTER:
            return int(metric.get_current_value() or 0)
        return 0
    
    def _get_current_gauge_value(self, metric_name: str, default: Union[int, float] = 0) -> Union[int, float]:
        """Get current value of a gauge metric."""
        metric = self.metrics.get(metric_name)
        if metric and metric.metric_type == MetricType.GAUGE:
            return metric.get_current_value() or default
        return default
    
    def record_request(self, operation: str, duration: float, success: bool = True):
        """Record a request with duration and success status."""
        status = "success" if success else "error"
        self.record_counter("app_requests_total", 1, {"operation": operation, "status": status})
        self.record_histogram("app_request_duration_seconds", duration, {"operation": operation})
        
        if not success:
            self.record_counter("app_errors_total", 1, {"type": "request", "severity": "medium"})
    
    def record_resume_processing(self, duration: float, success: bool, tech_stacks_count: int = 0):
        """Record resume processing metrics."""
        status = "success" if success else "error"
        self.record_counter("resumes_processed_total", 1, {"status": status})
        self.record_histogram("resumes_processing_time_seconds", duration)
        
        # Update success rate
        self._update_success_rate()
    
    def record_email_sent(self, success: bool, template_type: str = "default"):
        """Record email sending metrics."""
        status = "success" if success else "error"
        self.record_counter("emails_sent_total", 1, {"status": status, "template": template_type})
        
        # Update delivery rate
        self._update_email_delivery_rate()
    
    def record_user_session(self, user_type: str = "regular"):
        """Record user session start."""
        self.record_counter("user_sessions_total", 1, {"user_type": user_type})
    
    def record_database_query(self, operation: str, duration: float, success: bool = True):
        """Record database query metrics."""
        status = "success" if success else "error"
        self.record_counter("database_queries_total", 1, {"operation": operation, "status": status})
        self.record_histogram("database_query_duration_seconds", duration)
    
    def record_circuit_breaker_trip(self, service: str):
        """Record circuit breaker trip."""
        self.record_counter("circuit_breaker_trips", 1, {"service": service})
    
    def update_system_metrics(self):
        """Update system metrics (memory, CPU, etc.)."""
        try:
            import psutil
            
            # Memory usage
            memory_info = psutil.virtual_memory()
            self.record_gauge("app_memory_usage_bytes", memory_info.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge("app_cpu_usage_percent", cpu_percent)
            
        except ImportError:
            logger.warning("psutil not available for system metrics")
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def _update_success_rate(self):
        """Update processing success rate."""
        total_metric = self.metrics.get("resumes_processed_total")
        if not total_metric:
            return
        
        # Calculate success rate from recent data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)  # Last hour
        
        recent_points = total_metric.get_values_in_range(start_time, end_time)
        if not recent_points:
            return
        
        success_count = sum(1 for p in recent_points if p.labels.get("status") == "success")
        total_count = len(recent_points)
        
        if total_count > 0:
            success_rate = (success_count / total_count) * 100
            self.record_gauge("processing_success_rate", success_rate)
    
    def _update_email_delivery_rate(self):
        """Update email delivery rate."""
        email_metric = self.metrics.get("emails_sent_total")
        if not email_metric:
            return
        
        # Calculate delivery rate from recent data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)  # Last hour
        
        recent_points = email_metric.get_values_in_range(start_time, end_time)
        if not recent_points:
            return
        
        success_count = sum(1 for p in recent_points if p.labels.get("status") == "success")
        total_count = len(recent_points)
        
        if total_count > 0:
            delivery_rate = (success_count / total_count) * 100
            self.record_gauge("email_delivery_rate", delivery_rate)
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format."""
        if format_type == "json":
            return self._export_json()
        elif format_type == "prometheus":
            return self._export_prometheus()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_json(self) -> str:
        """Export metrics as JSON."""
        export_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {}
        }
        
        for name, metric in self.metrics.items():
            recent_points = list(metric.data_points)[-100:]  # Last 100 points
            export_data['metrics'][name] = {
                'name': name,
                'type': metric.metric_type.value,
                'description': metric.description,
                'unit': metric.unit,
                'data_points': [p.to_dict() for p in recent_points]
            }
        
        return json.dumps(export_data, indent=2)
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        for name, metric in self.metrics.items():
            current_value = metric.get_current_value()
            if current_value is not None:
                # Add help and type comments
                lines.append(f"# HELP {name} {metric.description}")
                lines.append(f"# TYPE {name} {metric.metric_type.value}")
                
                # Add metric line
                if metric.data_points and metric.data_points[-1].labels:
                    labels = ','.join([f'{k}="{v}"' for k, v in metric.data_points[-1].labels.items()])
                    lines.append(f"{name}{{{labels}}} {current_value}")
                else:
                    lines.append(f"{name} {current_value}")
                lines.append("")
        
        return '\n'.join(lines)


# Context manager for timing operations
class MetricsTimer:
    """Context manager for timing operations and recording metrics."""
    
    def __init__(self, metrics: ApplicationMetrics, metric_name: str, labels: Optional[Dict[str, str]] = None):
        self.metrics = metrics
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.time() - self.start_time
            success = exc_type is None
            
            self.metrics.record_timer(self.metric_name, duration, self.labels)
            
            # Also record success/failure
            operation = self.labels.get('operation', 'unknown')
            self.metrics.record_request(operation, duration, success)


# Decorator for automatic metrics collection
def record_metrics(operation: str, metric_name: Optional[str] = None):
    """Decorator to automatically record metrics for function calls."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            metrics = get_application_metrics()
            timer_metric = metric_name or f"{func.__name__}_duration_seconds"
            labels = {'operation': operation}
            
            with MetricsTimer(metrics, timer_metric, labels):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global metrics instance
_application_metrics = None
_metrics_lock = threading.Lock()


def get_application_metrics() -> ApplicationMetrics:
    """Get global application metrics instance."""
    global _application_metrics
    
    with _metrics_lock:
        if _application_metrics is None:
            _application_metrics = ApplicationMetrics()
        return _application_metrics


# Convenience functions for common metrics
def record_resume_processed(duration: float, success: bool, tech_stacks: int = 0):
    """Record resume processing completion."""
    metrics = get_application_metrics()
    metrics.record_resume_processing(duration, success, tech_stacks)


def record_email_sent(success: bool, template: str = "default"):
    """Record email sent."""
    metrics = get_application_metrics()
    metrics.record_email_sent(success, template)


def record_user_action(action: str, success: bool = True):
    """Record user action."""
    metrics = get_application_metrics()
    operation = f"user_action_{action}"
    metrics.record_request(operation, 0, success)


def get_dashboard_metrics() -> Dict[str, Any]:
    """Get metrics formatted for dashboard display."""
    metrics = get_application_metrics()
    return metrics.get_dashboard_data()


# Background metrics collection
class MetricsCollector:
    """Background service for collecting system metrics."""
    
    def __init__(self, metrics: ApplicationMetrics, interval: int = 60):
        self.metrics = metrics
        self.interval = interval
        self._running = False
        self._thread = None
    
    def start(self):
        """Start background metrics collection."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        
        structured_logger.info(
            "Metrics collector started",
            operation="metrics_collector_start",
            interval=self.interval
        )
    
    def stop(self):
        """Stop background metrics collection."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def _collect_loop(self):
        """Background collection loop."""
        while self._running:
            try:
                self.metrics.update_system_metrics()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(self.interval)


# Global metrics collector
_metrics_collector = None


def start_metrics_collection(interval: int = 60):
    """Start background metrics collection."""
    global _metrics_collector
    
    if _metrics_collector is None:
        metrics = get_application_metrics()
        _metrics_collector = MetricsCollector(metrics, interval)
    
    _metrics_collector.start()


def stop_metrics_collection():
    """Stop background metrics collection."""
    global _metrics_collector
    
    if _metrics_collector:
        _metrics_collector.stop()



