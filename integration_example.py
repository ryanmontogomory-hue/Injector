"""
Integration example for Resume Customizer application enhancements.
Shows how to use all the new features together in a coordinated way.
"""

import streamlit as st
import asyncio
import time
from typing import List, Any, Dict

# Import all enhanced modules
from circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
from distributed_cache import get_distributed_cache_manager, CacheConfig
from enhanced_error_recovery import RobustResumeProcessor, get_error_recovery_manager
from batch_processor_enhanced import get_batch_processor, BatchConfig, process_resumes_optimized
from progress_tracker_enhanced import get_progress_tracker, create_progress_session, StreamlitProgressDisplay
from email_templates_enhanced import get_template_manager, StreamlitTemplateInterface
from metrics_analytics_enhanced import get_application_metrics, start_metrics_collection, get_dashboard_metrics
from health_monitor_enhanced import get_health_monitor, start_health_monitoring
from health_endpoints import integrate_health_features, display_system_health_sidebar
from error_handling_enhanced import ErrorHandlerContext, ErrorSeverity
from logger import get_logger

logger = get_logger()


def initialize_enhanced_systems():
    """Initialize all enhanced systems and monitoring."""
    st.write("🚀 Initializing Enhanced Resume Customizer...")
    
    # Initialize distributed cache with Redis support
    cache_config = CacheConfig(
        redis_url="redis://localhost:6379/0",  # Configure as needed
        local_cache_size=1000,
        enable_compression=True
    )
    cache_manager = get_distributed_cache_manager(cache_config)
    
    # Initialize circuit breakers
    db_breaker = get_circuit_breaker(
        "database",
        CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30)
    )
    
    # Start metrics collection
    start_metrics_collection(interval=60)
    
    # Start health monitoring
    start_health_monitoring()
    
    st.success("✅ Enhanced systems initialized successfully!")
    
    return {
        'cache_manager': cache_manager,
        'db_breaker': db_breaker
    }


def enhanced_file_processing_demo():
    """Demonstrate enhanced file processing with all new features."""
    st.header("📄 Enhanced File Processing")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload resume files",
        type=['docx'],
        accept_multiple_files=True,
        key="enhanced_upload"
    )
    
    if not uploaded_files:
        st.info("📁 Upload one or more resume files to see the enhanced processing in action.")
        return
    
    # Processing configuration
    col1, col2 = st.columns(2)
    
    with col1:
        batch_size = st.slider("Batch Size", min_value=1, max_value=10, value=3)
        use_caching = st.checkbox("Enable Caching", value=True)
        use_progress_tracking = st.checkbox("Show Progress Tracking", value=True)
    
    with col2:
        memory_threshold = st.slider("Memory Threshold (MB)", min_value=100, max_value=1000, value=500)
        enable_circuit_breaker = st.checkbox("Circuit Breaker Protection", value=True)
        adaptive_batch_size = st.checkbox("Adaptive Batch Sizing", value=True)
    
    if st.button("🚀 Process Files with Enhancements", type="primary"):
        process_files_enhanced(
            uploaded_files,
            batch_size,
            use_caching,
            use_progress_tracking,
            memory_threshold,
            enable_circuit_breaker,
            adaptive_batch_size
        )


async def process_files_enhanced(
    files: List[Any],
    batch_size: int,
    use_caching: bool,
    use_progress_tracking: bool,
    memory_threshold: int,
    enable_circuit_breaker: bool,
    adaptive_batch_size: bool
):
    """Process files using all enhanced features."""
    
    # Create progress session if enabled
    progress_session_id = None
    progress_display = None
    
    if use_progress_tracking:
        progress_tracker = get_progress_tracker()
        
        # Create progress session
        tasks = [
            {'name': f'Process {file.name}', 'weight': 1.0, 'estimated_duration': 10}
            for file in files
        ]
        
        progress_session_id = create_progress_session(
            "Enhanced File Processing",
            tasks
        )
        
        # Create Streamlit progress display
        progress_display = StreamlitProgressDisplay.create_progress_container(
            "Enhanced File Processing"
        )
    
    # Configure batch processor
    batch_config = BatchConfig(
        batch_size=batch_size,
        memory_threshold_mb=memory_threshold,
        enable_caching=use_caching,
        adaptive_batch_size=adaptive_batch_size,
        use_processes=False  # Use threads for Streamlit compatibility
    )
    
    try:
        # Process files with enhanced batch processor
        with ErrorHandlerContext("batch_file_processing", severity=ErrorSeverity.HIGH):
            
            # Update progress
            if progress_session_id:
                progress_tracker = get_progress_tracker()
                for i, file in enumerate(files):
                    progress_tracker.start_task(progress_session_id, f"task_{i}")
            
            # Process files
            results = await process_resumes_optimized(files, batch_config)
            
            # Update progress as completed
            if progress_session_id:
                for i, result in enumerate(results):
                    success = result.success if hasattr(result, 'success') else True
                    progress_tracker.complete_task(
                        progress_session_id, 
                        f"task_{i}", 
                        success=success
                    )
            
            # Display results
            display_processing_results(results)
    
    except Exception as e:
        st.error(f"❌ Enhanced processing failed: {e}")
        logger.error(f"Enhanced processing error: {e}")


def display_processing_results(results):
    """Display processing results with enhanced information."""
    st.subheader("📊 Processing Results")
    
    if not results:
        st.warning("No results to display")
        return
    
    # Summary metrics
    successful = sum(1 for r in results if getattr(r, 'success', True))
    total = len(results)
    success_rate = (successful / total) * 100 if total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Total Files", total)
    
    with col2:
        st.metric("✅ Successful", successful)
    
    with col3:
        st.metric("❌ Failed", total - successful)
    
    with col4:
        st.metric("📈 Success Rate", f"{success_rate:.1f}%")
    
    # Detailed results
    for i, result in enumerate(results):
        with st.expander(f"📄 File {i+1} Results", expanded=False):
            if hasattr(result, 'success'):
                if result.success:
                    st.success("✅ Processing successful")
                    if hasattr(result, 'processing_time'):
                        st.info(f"⏱️ Processing time: {result.processing_time:.2f}s")
                    if hasattr(result, 'cache_hit'):
                        cache_status = "🎯 Cache hit" if result.cache_hit else "💾 Cache miss"
                        st.info(cache_status)
                else:
                    st.error("❌ Processing failed")
                    if hasattr(result, 'error'):
                        st.error(f"Error: {result.error}")
            else:
                st.info("📄 Legacy result format")


def enhanced_email_template_demo():
    """Demonstrate enhanced email templates."""
    st.header("📧 Enhanced Email Templates")
    
    # Get template manager
    template_manager = get_template_manager()
    
    # Template selection interface
    template_id = StreamlitTemplateInterface.template_selector(
        template_manager,
        key_prefix="demo_template"
    )
    
    if template_id:
        # Show template preview
        StreamlitTemplateInterface.template_preview(
            template_manager,
            template_id,
            key_prefix="demo_preview"
        )
        
        # Variable input form
        variables = StreamlitTemplateInterface.variable_input_form(
            template_manager,
            template_id,
            key_prefix="demo_vars"
        )
        
        # Generate email
        if st.button("📧 Generate Email", type="primary"):
            subject, body = template_manager.generate_email(template_id, variables)
            
            if subject and body:
                st.subheader("📩 Generated Email")
                
                st.text_input("Subject Line", value=subject, disabled=True)
                st.text_area("Email Body", value=body, height=300, disabled=True)
                
                # Download option
                email_content = f"Subject: {subject}\n\n{body}"
                st.download_button(
                    "📥 Download Email",
                    data=email_content,
                    file_name=f"email_{template_id}.txt",
                    mime="text/plain"
                )
            else:
                st.error("Failed to generate email")


def system_monitoring_demo():
    """Demonstrate system monitoring and health features."""
    st.header("🏥 System Monitoring")
    
    # Health status
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 System Health")
        # This would normally be in the sidebar
        display_system_health_sidebar()
    
    with col2:
        st.subheader("📊 Application Metrics")
        
        try:
            metrics = get_dashboard_metrics()
            kpis = metrics.get('kpis', {})
            
            st.metric("📈 Total Requests", kpis.get('total_requests', 0))
            st.metric("📄 Resumes Processed", kpis.get('total_resumes_processed', 0))
            st.metric("📧 Emails Sent", kpis.get('total_emails_sent', 0))
            st.metric("💾 Memory Usage", f"{kpis.get('current_memory_mb', 0):.1f}MB")
            
        except Exception as e:
            st.error(f"Failed to load metrics: {e}")
    
    # Circuit breaker status
    st.subheader("🔄 Circuit Breaker Status")
    
    try:
        from circuit_breaker import _circuit_breaker_manager
        stats = _circuit_breaker_manager.get_all_stats()
        
        for name, stat in stats.items():
            with st.expander(f"⚡ {name}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("State", stat['state'])
                
                with col2:
                    st.metric("Success Rate", f"{stat['success_rate']:.1%}")
                
                with col3:
                    st.metric("Total Calls", stat['total_calls'])
    
    except Exception as e:
        st.warning(f"Circuit breaker stats unavailable: {e}")


def cache_performance_demo():
    """Demonstrate cache performance and statistics."""
    st.header("💾 Cache Performance")
    
    try:
        cache_manager = get_distributed_cache_manager()
        stats = cache_manager.get_stats()
        
        # Cache metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Hit Rate", f"{stats.get('hit_rate', 0):.1%}")
        
        with col2:
            st.metric("L1 Hits", stats.get('l1_hits', 0))
        
        with col3:
            st.metric("L2 Hits", stats.get('l2_hits', 0))
        
        with col4:
            st.metric("Misses", stats.get('misses', 0))
        
        # L1 Cache details
        l1_cache = stats.get('l1_cache', {})
        if l1_cache:
            st.subheader("🚀 L1 Cache (Local)")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Size", l1_cache.get('size', 0))
                st.metric("Max Size", l1_cache.get('max_size', 0))
            
            with col2:
                st.metric("Memory Usage", f"{l1_cache.get('total_size_mb', 0):.1f}MB")
                st.metric("Hit Rate", f"{l1_cache.get('hit_rate', 0):.1%}")
        
        # L2 Cache details
        l2_cache = stats.get('l2_cache', {})
        if l2_cache and l2_cache.get('available'):
            st.subheader("🌐 L2 Cache (Redis)")
            
            st.success("✅ Redis cache available")
            st.info(f"Memory: {l2_cache.get('used_memory_human', 'N/A')}")
        else:
            st.subheader("🌐 L2 Cache (Redis)")
            st.warning("⚠️ Redis cache not available - using L1 only")
    
    except Exception as e:
        st.error(f"Failed to load cache stats: {e}")


def main():
    """Main enhanced application demo."""
    st.set_page_config(
        page_title="Resume Customizer Enhanced",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 Resume Customizer - Enhanced Edition")
    st.write("Demonstration of all enhanced features working together")
    
    # Initialize systems
    if 'enhanced_initialized' not in st.session_state:
        with st.spinner("Initializing enhanced systems..."):
            systems = initialize_enhanced_systems()
            st.session_state.enhanced_initialized = True
            st.session_state.systems = systems
    
    # Integration features in sidebar
    with st.sidebar:
        st.title("🎛️ Enhanced Features")
        integrate_health_features()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 File Processing",
        "📧 Email Templates", 
        "🏥 System Health",
        "💾 Cache Performance",
        "📊 Metrics Dashboard"
    ])
    
    with tab1:
        enhanced_file_processing_demo()
    
    with tab2:
        enhanced_email_template_demo()
    
    with tab3:
        system_monitoring_demo()
    
    with tab4:
        cache_performance_demo()
    
    with tab5:
        try:
            from health_endpoints import create_health_dashboard_page
            create_health_dashboard_page()
        except Exception as e:
            st.error(f"Health dashboard unavailable: {e}")


if __name__ == "__main__":
    main()


