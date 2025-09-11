"""
Comprehensive health monitoring and check system for Resume Customizer application.
Provides system health checks, service monitoring, and alerting capabilities.
"""

import time
import threading
import psutil
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from utilities.logger import get_logger
from utilities.structured_logger import get_structured_logger
from metrics_analytics_enhanced import get_application_metrics

logger = get_logger()
structured_logger = get_structured_logger("health_monitor")


class HealthStatus(Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'duration_ms': self.duration_ms
        }


@dataclass
class HealthCheck:
    """Health check definition."""
    name: str
    description: str
    check_function: Callable[[], HealthCheckResult]
    interval_seconds: int = 60
    timeout_seconds: int = 10
    critical: bool = False
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


class SystemHealthMonitor:
    """
    Comprehensive health monitoring system with automated checks,
    alerting, and dashboard integration.
    """
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_results: Dict[str, HealthCheckResult] = {}
        self._lock = threading.RLock()
        self._monitoring_thread = None
        self._running = False
        self.metrics = get_application_metrics()
        
        # Alert thresholds
        self.alert_thresholds = {
            'memory_usage_percent': 85,
            'cpu_usage_percent': 80,
            'disk_usage_percent': 90,
            'response_time_ms': 5000,
            'error_rate_percent': 10
        }
        
        # Initialize built-in health checks
        self._initialize_builtin_checks()
        
        structured_logger.info(
            "Health monitoring system initialized",
            operation="health_monitor_init",
            check_count=len(self.health_checks)
        )
    
    def _initialize_builtin_checks(self):
        """Initialize built-in health checks."""
        builtin_checks = [
            HealthCheck(
                name="system_memory",
                description="System memory usage check",
                check_function=self._check_system_memory,
                interval_seconds=30,
                critical=True,
                tags=["system", "memory"]
            ),
            HealthCheck(
                name="system_cpu",
                description="System CPU usage check", 
                check_function=self._check_system_cpu,
                interval_seconds=30,
                tags=["system", "cpu"]
            ),
            HealthCheck(
                name="system_disk",
                description="System disk usage check",
                check_function=self._check_system_disk,
                interval_seconds=60,
                critical=True,
                tags=["system", "disk"]
            ),
            HealthCheck(
                name="database_connection",
                description="Database connection health",
                check_function=self._check_database_connection,
                interval_seconds=60,
                critical=True,
                tags=["database", "connection"]
            ),
            HealthCheck(
                name="cache_system",
                description="Cache system health",
                check_function=self._check_cache_system,
                interval_seconds=60,
                tags=["cache", "performance"]
            ),
            HealthCheck(
                name="email_service",
                description="Email service connectivity",
                check_function=self._check_email_service,
                interval_seconds=300,  # Every 5 minutes
                tags=["email", "external"]
            ),
            HealthCheck(
                name="application_performance",
                description="Application performance metrics",
                check_function=self._check_application_performance,
                interval_seconds=60,
                tags=["performance", "application"]
            ),
            HealthCheck(
                name="error_rate",
                description="Application error rate check",
                check_function=self._check_error_rate,
                interval_seconds=60,
                critical=True,
                tags=["errors", "application"]
            )
        ]
        
        for check in builtin_checks:
            self.health_checks[check.name] = check
    
    def add_health_check(self, health_check: HealthCheck) -> bool:
        """
        Add a custom health check.
        
        Args:
            health_check: Health check to add
            
        Returns:
            True if check was added successfully
        """
        with self._lock:
            if health_check.name in self.health_checks:
                logger.warning(f"Health check {health_check.name} already exists")
                return False
            
            self.health_checks[health_check.name] = health_check
            
            structured_logger.info(
                f"Health check added: {health_check.name}",
                operation="health_check_add",
                check_name=health_check.name,
                critical=health_check.critical
            )
            
            return True
    
    def remove_health_check(self, check_name: str) -> bool:
        """
        Remove a health check.
        
        Args:
            check_name: Name of check to remove
            
        Returns:
            True if check was removed successfully
        """
        with self._lock:
            if check_name not in self.health_checks:
                return False
            
            del self.health_checks[check_name]
            if check_name in self.check_results:
                del self.check_results[check_name]
            
            structured_logger.info(
                f"Health check removed: {check_name}",
                operation="health_check_remove",
                check_name=check_name
            )
            
            return True
    
    def run_check(self, check_name: str) -> Optional[HealthCheckResult]:
        """
        Run a specific health check manually.
        
        Args:
            check_name: Name of check to run
            
        Returns:
            Health check result or None if check not found
        """
        with self._lock:
            health_check = self.health_checks.get(check_name)
            if not health_check or not health_check.enabled:
                return None
            
            return self._execute_check(health_check)
    
    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """
        Run all enabled health checks.
        
        Returns:
            Dictionary of check results
        """
        results = {}
        
        with self._lock:
            enabled_checks = [
                check for check in self.health_checks.values()
                if check.enabled
            ]
        
        for health_check in enabled_checks:
            result = self._execute_check(health_check)
            results[health_check.name] = result
            
            with self._lock:
                self.check_results[health_check.name] = result
        
        return results
    
    def _execute_check(self, health_check: HealthCheck) -> HealthCheckResult:
        """Execute a single health check with timeout and error handling."""
        start_time = time.time()
        
        try:
            # Execute with timeout (simplified - in production you'd want proper timeout handling)
            result = health_check.check_function()
            result.duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            self.metrics.record_gauge(
                "health_check_duration_seconds",
                result.duration_ms / 1000,
                {"check_name": health_check.name}
            )
            
            self.metrics.record_gauge(
                "health_check_status",
                1 if result.status == HealthStatus.HEALTHY else 0,
                {"check_name": health_check.name}
            )
            
            structured_logger.debug(
                f"Health check completed: {health_check.name}",
                operation="health_check_complete",
                check_name=health_check.name,
                status=result.status.value,
                duration_ms=result.duration_ms
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            error_result = HealthCheckResult(
                name=health_check.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e), "exception_type": type(e).__name__},
                duration_ms=duration_ms
            )
            
            structured_logger.error(
                f"Health check failed: {health_check.name}",
                operation="health_check_error",
                check_name=health_check.name,
                error=str(e),
                duration_ms=duration_ms
            )
            
            return error_result
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health summary.
        
        Returns:
            Overall health status and summary
        """
        with self._lock:
            if not self.check_results:
                return {
                    'status': HealthStatus.UNKNOWN.value,
                    'message': 'No health check results available',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Count statuses
            status_counts = {
                HealthStatus.HEALTHY.value: 0,
                HealthStatus.WARNING.value: 0,
                HealthStatus.CRITICAL.value: 0,
                HealthStatus.UNKNOWN.value: 0
            }
            
            critical_failures = []
            warnings = []
            
            for name, result in self.check_results.items():
                status_counts[result.status.value] += 1
                
                if result.status == HealthStatus.CRITICAL:
                    health_check = self.health_checks.get(name)
                    if health_check and health_check.critical:
                        critical_failures.append(name)
                elif result.status == HealthStatus.WARNING:
                    warnings.append(name)
            
            # Determine overall status
            if critical_failures:
                overall_status = HealthStatus.CRITICAL
                message = f"Critical health issues detected: {', '.join(critical_failures)}"
            elif status_counts[HealthStatus.CRITICAL.value] > 0:
                overall_status = HealthStatus.WARNING
                message = f"Non-critical health issues detected"
            elif warnings:
                overall_status = HealthStatus.WARNING
                message = f"Warnings detected: {', '.join(warnings)}"
            else:
                overall_status = HealthStatus.HEALTHY
                message = "All health checks passing"
            
            return {
                'status': overall_status.value,
                'message': message,
                'summary': {
                    'total_checks': len(self.check_results),
                    'healthy': status_counts[HealthStatus.HEALTHY.value],
                    'warning': status_counts[HealthStatus.WARNING.value],
                    'critical': status_counts[HealthStatus.CRITICAL.value],
                    'unknown': status_counts[HealthStatus.UNKNOWN.value]
                },
                'critical_failures': critical_failures,
                'warnings': warnings,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_health_dashboard(self) -> Dict[str, Any]:
        """
        Get health data formatted for dashboard display.
        
        Returns:
            Dashboard-ready health data
        """
        overall_health = self.get_overall_health()
        
        # Get detailed check results
        detailed_results = {}
        with self._lock:
            for name, result in self.check_results.items():
                check = self.health_checks.get(name)
                detailed_results[name] = {
                    **result.to_dict(),
                    'description': check.description if check else '',
                    'critical': check.critical if check else False,
                    'tags': check.tags if check else []
                }
        
        # Get recent health trends (simplified)
        trends = self._calculate_health_trends()
        
        return {
            'overall_health': overall_health,
            'detailed_results': detailed_results,
            'trends': trends,
            'alert_thresholds': self.alert_thresholds,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _calculate_health_trends(self) -> Dict[str, Any]:
        """Calculate health trends over time (simplified implementation)."""
        # This is a simplified version - in practice you'd want to store
        # historical data and calculate proper trends
        return {
            'uptime_hours': (datetime.utcnow() - self.metrics.start_time).total_seconds() / 3600,
            'total_checks_run': len(self.check_results),
            'health_score': self._calculate_health_score()
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        if not self.check_results:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for name, result in self.check_results.items():
            check = self.health_checks.get(name)
            weight = 2.0 if check and check.critical else 1.0
            
            if result.status == HealthStatus.HEALTHY:
                score = 100.0
            elif result.status == HealthStatus.WARNING:
                score = 70.0
            elif result.status == HealthStatus.CRITICAL:
                score = 0.0
            else:  # UNKNOWN
                score = 50.0
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def start_monitoring(self):
        """Start background health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        structured_logger.info(
            "Health monitoring started",
            operation="health_monitoring_start"
        )
    
    def stop_monitoring(self):
        """Stop background health monitoring."""
        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        
        structured_logger.info(
            "Health monitoring stopped",
            operation="health_monitoring_stop"
        )
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        last_check_times = {}
        
        while self._running:
            try:
                current_time = time.time()
                
                for name, health_check in self.health_checks.items():
                    if not health_check.enabled:
                        continue
                    
                    last_check = last_check_times.get(name, 0)
                    if current_time - last_check >= health_check.interval_seconds:
                        result = self._execute_check(health_check)
                        
                        with self._lock:
                            self.check_results[name] = result
                        
                        last_check_times[name] = current_time
                
                time.sleep(10)  # Check every 10 seconds for due checks
                
            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")
                time.sleep(30)  # Wait before retrying
    
    # Built-in health check functions
    def _check_system_memory(self) -> HealthCheckResult:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            
            if usage_percent >= self.alert_thresholds['memory_usage_percent']:
                status = HealthStatus.CRITICAL
                message = f"High memory usage: {usage_percent:.1f}%"
            elif usage_percent >= 70:
                status = HealthStatus.WARNING
                message = f"Moderate memory usage: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {usage_percent:.1f}%"
            
            return HealthCheckResult(
                name="system_memory",
                status=status,
                message=message,
                details={
                    'usage_percent': usage_percent,
                    'used_gb': memory.used / (1024**3),
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="system_memory",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check memory: {e}"
            )
    
    def _check_system_cpu(self) -> HealthCheckResult:
        """Check system CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent >= self.alert_thresholds['cpu_usage_percent']:
                status = HealthStatus.CRITICAL
                message = f"High CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent >= 60:
                status = HealthStatus.WARNING
                message = f"Moderate CPU usage: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            
            return HealthCheckResult(
                name="system_cpu",
                status=status,
                message=message,
                details={
                    'usage_percent': cpu_percent,
                    'cpu_count': psutil.cpu_count()
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="system_cpu",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check CPU: {e}"
            )
    
    def _check_system_disk(self) -> HealthCheckResult:
        """Check system disk usage."""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent >= self.alert_thresholds['disk_usage_percent']:
                status = HealthStatus.CRITICAL
                message = f"High disk usage: {usage_percent:.1f}%"
            elif usage_percent >= 75:
                status = HealthStatus.WARNING
                message = f"Moderate disk usage: {usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {usage_percent:.1f}%"
            
            return HealthCheckResult(
                name="system_disk",
                status=status,
                message=message,
                details={
                    'usage_percent': usage_percent,
                    'used_gb': disk.used / (1024**3),
                    'total_gb': disk.total / (1024**3),
                    'free_gb': disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="system_disk",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk: {e}"
            )
    
    def _check_database_connection(self) -> HealthCheckResult:
        """Check database connection health."""
        try:
            # Try to import and test database connection
            from database.connection_manager import get_connection_manager
            
            connection_manager = get_connection_manager()
            
            # Simple connection test
            start_time = time.time()
            with connection_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            response_time_ms = (time.time() - start_time) * 1000
            
            if response_time_ms > 5000:  # 5 seconds
                status = HealthStatus.WARNING
                message = f"Slow database response: {response_time_ms:.0f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = f"Database connection healthy: {response_time_ms:.0f}ms"
            
            return HealthCheckResult(
                name="database_connection",
                status=status,
                message=message,
                details={
                    'response_time_ms': response_time_ms,
                    'connection_pool_status': 'active'
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                name="database_connection",
                status=HealthStatus.UNKNOWN,
                message="Database module not available"
            )
        except Exception as e:
            return HealthCheckResult(
                name="database_connection",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {e}"
            )
    
    def _check_cache_system(self) -> HealthCheckResult:
        """Check cache system health."""
        try:
            from distributed_cache import get_distributed_cache_manager
            
            cache_manager = get_distributed_cache_manager()
            stats = cache_manager.get_stats()
            
            hit_rate = stats.get('hit_rate', 0) * 100
            
            if hit_rate < 50:
                status = HealthStatus.WARNING
                message = f"Low cache hit rate: {hit_rate:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Cache system healthy: {hit_rate:.1f}% hit rate"
            
            return HealthCheckResult(
                name="cache_system",
                status=status,
                message=message,
                details={
                    'hit_rate_percent': hit_rate,
                    'l1_cache_size': stats.get('l1_cache', {}).get('size', 0),
                    'l2_cache_available': stats.get('l2_cache', {}).get('available', False)
                }
            )
            
        except ImportError:
            return HealthCheckResult(
                name="cache_system",
                status=HealthStatus.UNKNOWN,
                message="Cache system not available"
            )
        except Exception as e:
            return HealthCheckResult(
                name="cache_system",
                status=HealthStatus.WARNING,
                message=f"Cache check failed: {e}"
            )
    
    def _check_email_service(self) -> HealthCheckResult:
        """Check email service connectivity."""
        try:
            # This is a simplified check - in practice you'd want to test
            # actual SMTP connectivity without sending emails
            return HealthCheckResult(
                name="email_service",
                status=HealthStatus.HEALTHY,
                message="Email service check placeholder",
                details={'note': 'Implement actual SMTP connectivity test'}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="email_service",
                status=HealthStatus.WARNING,
                message=f"Email service check failed: {e}"
            )
    
    def _check_application_performance(self) -> HealthCheckResult:
        """Check application performance metrics."""
        try:
            # Get recent performance data from metrics
            dashboard_data = self.metrics.get_dashboard_data()
            
            # Check various performance indicators
            issues = []
            
            # Check memory usage
            memory_mb = dashboard_data['kpis'].get('current_memory_mb', 0)
            if memory_mb > 1000:  # 1GB threshold
                issues.append(f"High memory usage: {memory_mb:.0f}MB")
            
            # Check processing success rate
            success_rate = dashboard_data['kpis'].get('processing_success_rate', 100)
            if success_rate < 95:
                issues.append(f"Low success rate: {success_rate:.1f}%")
            
            if issues:
                status = HealthStatus.WARNING
                message = f"Performance issues: {'; '.join(issues)}"
            else:
                status = HealthStatus.HEALTHY
                message = "Application performance normal"
            
            return HealthCheckResult(
                name="application_performance",
                status=status,
                message=message,
                details=dashboard_data['kpis']
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="application_performance",
                status=HealthStatus.UNKNOWN,
                message=f"Performance check failed: {e}"
            )
    
    def _check_error_rate(self) -> HealthCheckResult:
        """Check application error rate."""
        try:
            # Get error metrics from the metrics system
            error_summary = self.metrics.get_metric_summary("app_errors_total", 60)
            request_summary = self.metrics.get_metric_summary("app_requests_total", 60)
            
            if not error_summary or not request_summary:
                return HealthCheckResult(
                    name="error_rate",
                    status=HealthStatus.HEALTHY,
                    message="No recent error data available"
                )
            
            total_errors = error_summary['current_value'] or 0
            total_requests = request_summary['current_value'] or 0
            
            if total_requests > 0:
                error_rate = (total_errors / total_requests) * 100
                
                if error_rate >= self.alert_thresholds['error_rate_percent']:
                    status = HealthStatus.CRITICAL
                    message = f"High error rate: {error_rate:.1f}%"
                elif error_rate >= 5:
                    status = HealthStatus.WARNING
                    message = f"Elevated error rate: {error_rate:.1f}%"
                else:
                    status = HealthStatus.HEALTHY
                    message = f"Error rate normal: {error_rate:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "No requests processed"
                error_rate = 0
            
            return HealthCheckResult(
                name="error_rate",
                status=status,
                message=message,
                details={
                    'error_rate_percent': error_rate,
                    'total_errors': total_errors,
                    'total_requests': total_requests
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="error_rate",
                status=HealthStatus.UNKNOWN,
                message=f"Error rate check failed: {e}"
            )


# Global health monitor instance
_health_monitor = None
_monitor_lock = threading.Lock()


def get_health_monitor() -> SystemHealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor
    
    with _monitor_lock:
        if _health_monitor is None:
            _health_monitor = SystemHealthMonitor()
        return _health_monitor


# Convenience functions
def get_system_health() -> Dict[str, Any]:
    """Get overall system health status."""
    monitor = get_health_monitor()
    return monitor.get_overall_health()


def get_health_dashboard() -> Dict[str, Any]:
    """Get health dashboard data."""
    monitor = get_health_monitor()
    return monitor.get_health_dashboard()


def run_health_checks() -> Dict[str, HealthCheckResult]:
    """Run all health checks."""
    monitor = get_health_monitor()
    return monitor.run_all_checks()


def start_health_monitoring():
    """Start background health monitoring."""
    monitor = get_health_monitor()
    monitor.start_monitoring()


def stop_health_monitoring():
    """Stop background health monitoring."""
    monitor = get_health_monitor()
    monitor.stop_monitoring()



