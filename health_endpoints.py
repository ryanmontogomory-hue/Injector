"""
Health endpoint integration for Resume Customizer Streamlit application.
Provides health check endpoints and dashboard integration.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, Optional

from health_monitor_enhanced import get_health_monitor, get_system_health, get_health_dashboard
from metrics_analytics_enhanced import get_dashboard_metrics
from logger import get_logger

logger = get_logger()


def display_system_health_sidebar():
    """Display system health status in sidebar."""
    try:
        health_status = get_system_health()
        
        # Health status indicator
        status = health_status['status']
        if status == 'healthy':
            st.sidebar.success("🟢 System Healthy")
        elif status == 'warning':
            st.sidebar.warning("🟡 System Warning")
        elif status == 'critical':
            st.sidebar.error("🔴 System Critical")
        else:
            st.sidebar.info("⚪ System Unknown")
        
        # Show basic metrics
        if 'summary' in health_status:
            summary = health_status['summary']
            with st.sidebar.expander("📊 Health Summary", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("✅ Healthy", summary.get('healthy', 0))
                    st.metric("🔴 Critical", summary.get('critical', 0))
                with col2:
                    st.metric("⚠️ Warning", summary.get('warning', 0))
                    st.metric("❓ Unknown", summary.get('unknown', 0))
    
    except Exception as e:
        st.sidebar.error(f"Health check failed: {e}")
        logger.error(f"Health sidebar display failed: {e}")


def create_health_dashboard_page():
    """Create comprehensive health dashboard page."""
    st.title("🏥 System Health Dashboard")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.rerun()
    
    # Manual refresh button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh Now", type="primary"):
            st.rerun()
    
    with col2:
        if st.button("📊 Export Health Data"):
            health_data = get_health_dashboard()
            st.download_button(
                "💾 Download JSON",
                data=json.dumps(health_data, indent=2),
                file_name=f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    try:
        # Get health dashboard data
        dashboard_data = get_health_dashboard()
        overall_health = dashboard_data['overall_health']
        
        # Overall health status
        st.subheader("🎯 Overall System Health")
        
        status = overall_health['status']
        message = overall_health['message']
        
        if status == 'healthy':
            st.success(f"✅ {message}")
        elif status == 'warning':
            st.warning(f"⚠️ {message}")
        elif status == 'critical':
            st.error(f"🚨 {message}")
        else:
            st.info(f"❓ {message}")
        
        # Health metrics overview
        summary = overall_health.get('summary', {})
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "✅ Healthy Checks",
                    summary.get('healthy', 0),
                    delta=f"{summary.get('total_checks', 0)} total"
                )
            
            with col2:
                st.metric(
                    "⚠️ Warnings",
                    summary.get('warning', 0)
                )
            
            with col3:
                st.metric(
                    "🔴 Critical Issues",
                    summary.get('critical', 0)
                )
            
            with col4:
                health_score = dashboard_data.get('trends', {}).get('health_score', 0)
                st.metric(
                    "🏆 Health Score",
                    f"{health_score:.1f}%",
                    delta="100% = Perfect Health"
                )
        
        # Critical failures and warnings
        if overall_health.get('critical_failures'):
            st.subheader("🚨 Critical Issues")
            for failure in overall_health['critical_failures']:
                st.error(f"❌ {failure}")
        
        if overall_health.get('warnings'):
            st.subheader("⚠️ Warnings")
            for warning in overall_health['warnings']:
                st.warning(f"⚠️ {warning}")
        
        # Detailed health checks
        st.subheader("📋 Detailed Health Checks")
        
        detailed_results = dashboard_data.get('detailed_results', {})
        
        # Group by category
        system_checks = {}
        application_checks = {}
        external_checks = {}
        
        for check_name, result in detailed_results.items():
            tags = result.get('tags', [])
            if 'system' in tags:
                system_checks[check_name] = result
            elif 'external' in tags:
                external_checks[check_name] = result
            else:
                application_checks[check_name] = result
        
        # Display checks by category
        if system_checks:
            with st.expander("🖥️ System Health Checks", expanded=True):
                _display_health_checks(system_checks)
        
        if application_checks:
            with st.expander("🚀 Application Health Checks", expanded=True):
                _display_health_checks(application_checks)
        
        if external_checks:
            with st.expander("🌐 External Service Checks", expanded=False):
                _display_health_checks(external_checks)
        
        # System trends and metrics
        if 'trends' in dashboard_data:
            st.subheader("📈 System Trends")
            trends = dashboard_data['trends']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                uptime_hours = trends.get('uptime_hours', 0)
                st.metric("⏱️ Uptime", f"{uptime_hours:.1f}h")
            
            with col2:
                checks_run = trends.get('total_checks_run', 0)
                st.metric("🔍 Total Checks", checks_run)
            
            with col3:
                # Get application metrics
                try:
                    app_metrics = get_dashboard_metrics()
                    kpis = app_metrics.get('kpis', {})
                    
                    memory_mb = kpis.get('current_memory_mb', 0)
                    st.metric("💾 Memory Usage", f"{memory_mb:.0f}MB")
                except:
                    st.metric("💾 Memory Usage", "N/A")
        
        # Show last updated time
        last_updated = dashboard_data.get('last_updated', '')
        if last_updated:
            st.caption(f"Last updated: {last_updated}")
    
    except Exception as e:
        st.error(f"❌ Failed to load health dashboard: {e}")
        logger.error(f"Health dashboard error: {e}")


def _display_health_checks(checks: Dict[str, Any]):
    """Display health checks in a formatted way."""
    for check_name, result in checks.items():
        status = result['status']
        message = result['message']
        duration_ms = result.get('duration_ms', 0)
        critical = result.get('critical', False)
        
        # Status icon and color
        if status == 'healthy':
            icon = "✅"
            status_color = "success"
        elif status == 'warning':
            icon = "⚠️"
            status_color = "warning"
        elif status == 'critical':
            icon = "🔴"
            status_color = "error"
        else:
            icon = "❓"
            status_color = "info"
        
        # Display check result
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            critical_badge = " 🔥" if critical else ""
            if status_color == "success":
                st.success(f"{icon} **{check_name}**{critical_badge}: {message}")
            elif status_color == "warning":
                st.warning(f"{icon} **{check_name}**{critical_badge}: {message}")
            elif status_color == "error":
                st.error(f"{icon} **{check_name}**{critical_badge}: {message}")
            else:
                st.info(f"{icon} **{check_name}**{critical_badge}: {message}")
        
        with col2:
            st.caption(f"⏱️ {duration_ms:.0f}ms")
        
        with col3:
            st.caption("🔥 Critical" if critical else "")
        
        # Show details if available
        details = result.get('details', {})
        if details and len(details) > 0:
            with st.expander(f"📊 Details for {check_name}", expanded=False):
                for key, value in details.items():
                    if isinstance(value, (int, float)):
                        if key.endswith('_percent'):
                            st.metric(key.replace('_', ' ').title(), f"{value:.1f}%")
                        elif key.endswith('_gb'):
                            st.metric(key.replace('_', ' ').title(), f"{value:.2f}GB")
                        elif key.endswith('_mb'):
                            st.metric(key.replace('_', ' ').title(), f"{value:.1f}MB")
                        elif key.endswith('_ms'):
                            st.metric(key.replace('_', ' ').title(), f"{value:.0f}ms")
                        else:
                            st.metric(key.replace('_', ' ').title(), value)
                    else:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")


def get_health_status_simple() -> Dict[str, Any]:
    """
    Get simple health status for quick checks.
    
    Returns:
        Simple health status dictionary
    """
    try:
        health_status = get_system_health()
        
        return {
            'status': health_status['status'],
            'timestamp': datetime.utcnow().isoformat(),
            'healthy': health_status['status'] == 'healthy',
            'message': health_status.get('message', 'Unknown'),
            'summary': health_status.get('summary', {})
        }
    
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        return {
            'status': 'unknown',
            'timestamp': datetime.utcnow().isoformat(),
            'healthy': False,
            'message': f'Health check failed: {e}',
            'summary': {}
        }


# Streamlit page integration
def add_health_check_page():
    """Add health check page to Streamlit app navigation."""
    if 'show_health_dashboard' not in st.session_state:
        st.session_state.show_health_dashboard = False
    
    # Add to sidebar navigation
    if st.sidebar.button("🏥 Health Dashboard"):
        st.session_state.show_health_dashboard = True
    
    # Show health dashboard if requested
    if st.session_state.show_health_dashboard:
        create_health_dashboard_page()
        if st.button("← Back to Main App"):
            st.session_state.show_health_dashboard = False
            st.rerun()


def create_simple_health_endpoint() -> Dict[str, Any]:
    """Create a simple health endpoint response."""
    return get_health_status_simple()


# Usage example for integration with main app
def integrate_health_features():
    """
    Example integration of health features with main application.
    Call this in your main app.py file.
    """
    # Display health status in sidebar
    display_system_health_sidebar()
    
    # Add health dashboard page option
    add_health_check_page()


