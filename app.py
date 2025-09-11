"""
Main application file for Resume Customizer - Refactored version.
Uses modular components for better maintainability and code organization.
"""


import streamlit as st
import base64
import time
from io import BytesIO
from typing import Dict, Any, Optional

# Import custom modules
from config import get_app_config, get_smtp_servers, get_default_email_subject, get_default_email_body, APP_CONFIG, validate_config
from core.text_parser import parse_input_text, LegacyParser
from core.resume_processor import get_resume_manager
from core.email_handler import get_email_manager
from utilities.logger import get_logger, display_logs_in_sidebar
from utilities.validators import validate_session_state
from monitoring.performance_monitor import get_performance_monitor
from utilities.retry_handler import get_retry_handler

# Import refactored UI and handlers
from ui.components import UIComponents
from ui.secure_components import get_secure_ui_components
from ui.resume_tab_handler import ResumeTabHandler
from ui.bulk_processor import BulkProcessor
from ui.requirements_manager import RequirementsManager, render_requirement_form, render_requirements_list
from ui.utils import check_file_readiness, prepare_bulk_data

# Import application guide
from application_guide import app_guide

# Import async processing components
from core.async_integration import (
    initialize_async_services,
    process_documents_async,
    get_async_results,
    validate_files_async,
    track_async_progress
)

# Import reliability and error handling
from enhancements.error_handling_enhanced import (
    ErrorHandler, 
    ErrorContext, 
    ErrorSeverity,
    handle_errors,
    ErrorHandlerContext
)

# Import memory optimization
from utilities.memory_optimizer import (
    get_memory_optimizer,
    with_memory_management,
    memory_efficient_batch
)

# Import structured logging
from utilities.structured_logger import (
    get_structured_logger,
    with_structured_logging,
    log_performance,
    app_logger
)

# Initialize components
logger = get_logger()
performance_monitor = get_performance_monitor()
memory_optimizer = get_memory_optimizer()
# Resume manager will be initialized when needed to avoid caching issues
email_manager = get_email_manager()
config = get_app_config()

# Admin resource panel integration

@handle_errors("application_health_check", ErrorSeverity.HIGH, return_on_error={"healthy": False, "issues": ["Health check failed"]})
@with_structured_logging("application", "health_check")
def check_application_health() -> Dict[str, Any]:
    """Check application health and return status."""
    health_status = {
        'healthy': True,
        'issues': [],
        'warnings': []
    }
    
    try:
        # Check if all required modules can be imported
        import streamlit
        import docx
        import io
        
        # Check performance monitor
        if not performance_monitor:
            health_status['warnings'].append("Performance monitor not available")
        
        # Check memory usage
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                health_status['warnings'].append(f"High memory usage: {memory.percent:.1f}%")
                
                # Suggest memory cleanup
                if memory.percent > 95:
                    health_status['warnings'].append("⚠️ Critical memory usage - consider restarting the application")
                else:
                    health_status['warnings'].append("💡 Try processing fewer files at once or restart the application")
                    
                # Attempt automatic cleanup
                try:
                    cleanup_result = memory_optimizer.optimize_memory(force=True)
                    if cleanup_result['status'] == 'completed':
                        health_status['warnings'].append(f"🧹 Memory cleanup performed - saved {cleanup_result['memory_saved_mb']:.1f}MB")
                    else:
                        health_status['warnings'].append("🧹 Memory cleanup attempted")
                except Exception as e:
                    logger.warning(f"Memory optimization failed: {e}")
                    health_status['warnings'].append("⚠️ Memory cleanup failed - consider manual restart")
                    
        except ImportError:
            health_status['warnings'].append("psutil not available - memory monitoring disabled")
        
        # Check disk space
        try:
            import psutil
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                health_status['warnings'].append(f"Low disk space: {disk.percent:.1f}% used")
        except ImportError:
            pass
        except Exception as e:
            health_status['warnings'].append(f"Disk space check failed: {e}")
        
    except ImportError as e:
        health_status['healthy'] = False
        health_status['issues'].append(f"Missing required dependency: {e}")
    
    return health_status

def render_requirements_tab():
    """Render the Requirements Management tab."""
    try:
        st.title("📋 Requirements Manager")
        st.write("Create and manage job requirements to customize your resume for specific positions.")
        
        # Initialize requirements manager
        if 'requirements_manager' not in st.session_state:
            st.session_state.requirements_manager = RequirementsManager()
        
        logger.info("Requirements tab rendered successfully")
        
        # Tabs for different views
        tab1, tab2 = st.tabs(["📝 Create/Edit Requirement", "📋 View Requirements"])
        
        with tab1:
            # Check if we're editing an existing requirement
            edit_id = st.query_params.get("edit")
            requirement_to_edit = None
            
            if edit_id and 'requirements_manager' in st.session_state:
                requirement_to_edit = st.session_state.requirements_manager.get_requirement(edit_id)
                if not requirement_to_edit:
                    st.warning("The requirement you're trying to edit doesn't exist.")
            
            # Render the form
            form_data = render_requirement_form(requirement_to_edit)
            
            # Handle form submission
            if form_data:
                try:
                    if requirement_to_edit:
                        # Update existing requirement
                        if st.session_state.requirements_manager.update_requirement(edit_id, form_data):
                            st.success("✅ Requirement updated successfully!")
                            # Don't use st.rerun() to prevent tab switching, just show success message
                        else:
                            st.error("Failed to update requirement. It may have been deleted.")
                    else:
                        # Create new requirement
                        requirement_id = st.session_state.requirements_manager.create_requirement(form_data)
                        if requirement_id:
                            st.success("✅ Requirement created successfully!")
                            st.info(f"📝 Requirement ID: {requirement_id}")
                            # Don't use st.rerun() to prevent tab switching
                        else:
                            st.error("Failed to create requirement. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    logger.error(f"Error saving requirement: {str(e)}")
                    # Add more detailed error information for debugging
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
        
        with tab2:
            render_requirements_list(st.session_state.requirements_manager)
            
    except Exception as e:
        st.error(f"An error occurred in the Requirements tab: {str(e)}")
        logger.error(f"Requirements tab error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Provide fallback functionality
        st.info("There was an error loading the requirements manager. Please refresh the page.")

@handle_errors("main_application", ErrorSeverity.CRITICAL, show_to_user=True)
def main():
    """Main application function."""
    # Set page config as early as possible to avoid reruns and layout recalculations
    st.set_page_config(
        page_title=APP_CONFIG["title"],
        page_icon="📝",
        layout=APP_CONFIG["layout"],
        initial_sidebar_state="expanded"
    )
    
    # Preload essential modules for better performance
    try:
        from utilities.lazy_imports import preload_essential_modules, get_lazy_module_stats
        preload_essential_modules()
    except ImportError:
        pass  # Lazy loading system not available
    
    # Initialize async services early
    if 'async_initialized' not in st.session_state:
        with st.spinner("Initializing high-performance async services..."):
            async_success = initialize_async_services()
            st.session_state.async_initialized = async_success
            if async_success:
                st.success("⚡ High-performance mode enabled!")
                time.sleep(0.5)  # Brief pause to show message
    
    # Check application health first
    health_status = check_application_health()
    if not health_status['healthy']:
        st.error("❌ Application Health Check Failed")
        for issue in health_status['issues']:
            st.error(issue)
        return
    
    # Initialize session state with fresh manager instances
    # Force refresh if version changed or handlers missing async methods
    force_refresh = False
    if 'resume_tab_handler' in st.session_state:
        handler = st.session_state.resume_tab_handler
        if not hasattr(handler.resume_manager, 'process_single_resume_async'):
            force_refresh = True
    
    if 'resume_tab_handler' not in st.session_state or force_refresh:
        from core.resume_processor import get_resume_manager
        st.session_state.resume_tab_handler = ResumeTabHandler(resume_manager=get_resume_manager("v2.2"))
    
    if 'bulk_processor' not in st.session_state or force_refresh:
        from core.resume_processor import get_resume_manager
        st.session_state.bulk_processor = BulkProcessor(resume_manager=get_resume_manager("v2.2"))
    

    # Validate configuration first
    config_validation = validate_config()
    if not config_validation.valid:
        st.error("❌ Configuration Error")
        for issue in config_validation.issues:
            st.error(f"• {issue}")
        st.stop()
    
    # Display configuration warnings if any
    if config_validation.warnings:
        with st.sidebar:
            st.warning("⚠️ Configuration Warnings")
            for warning in config_validation.warnings:
                st.warning(f"• {warning}")
    
    validate_session_state()
    if 'resume_inputs' not in st.session_state:
        st.session_state.resume_inputs = {}
    if 'user_id' not in st.session_state:
        import uuid
        st.session_state.user_id = str(uuid.uuid4())
    logger.info("Application started")

    ui = UIComponents()
    secure_ui = get_secure_ui_components()
    # Use session state handlers to ensure consistency
    tab_handler = st.session_state.resume_tab_handler
    bulk_processor = st.session_state.bulk_processor

    # Main app layout
    st.title(APP_CONFIG["title"])
    st.markdown("Customize your resume and send it to multiple recipients")
    
    # Create tabs
    tab_labels = [
        "📄 Resume Customizer", 
        "📤 Bulk Processor", 
        "📋 Requirements",
        "📚 Know About The Application",
        "⚙️ Settings"
    ]
    if st.session_state.get('show_preview_all_tab') and st.session_state.get('all_resume_previews'):
        tab_labels.insert(1, "👁️ Preview ALL")
    tabs = st.tabs(tab_labels)

    tab_idx = 0
    tab_customizer = tabs[tab_idx]
    tab_idx += 1
    if "👁️ Preview ALL" in tab_labels:
        tab_preview_all = tabs[tab_idx]
        tab_idx += 1
    tab_bulk = tabs[tab_idx]
    tab_idx += 1
    tab_requirements = tabs[tab_idx]
    tab_idx += 1
    tab_application_guide = tabs[tab_idx]
    tab_idx += 1
    tab_settings = tabs[tab_idx]

    with tab_customizer:
        # Resume Customizer Tab
        ui.render_sidebar()
        secure_ui.display_security_status()
        display_logs_in_sidebar()
        
        # Add async progress tracking to sidebar
        track_async_progress()
        
        # Performance metrics are now displayed in the sidebar via the UI components
        
        # File upload UI - moved inside the Resume Customizer tab
        st.markdown("**Choose file source:**")
        file_source = st.radio("Select file source", ["Local Upload", "Google Drive"], horizontal=True)
        all_files = []
        if file_source == "Local Upload":
            # Local upload is lightweight, render immediately
            with st.spinner("Loading local file upload..."):
                uploaded_files = ui.render_file_upload(key="file_upload_customizer")
            if uploaded_files:
                all_files.extend([(file.name, file) for file in uploaded_files])
        else:
            # Lazy load the Google Drive picker only on demand
            if st.button("Open Google Drive Picker", key="open_gdrive_picker"):
                with st.spinner("Loading Google Drive picker..."):
                    gdrive_files = ui.render_gdrive_picker(key="gdrive_picker_customizer")
                if gdrive_files:
                    all_files.extend(gdrive_files)

        if all_files:
            # Add async file validation option
            if len(all_files) > 1 and st.session_state.get('async_initialized'):
                if st.button("⚡ Validate All Files (Async)", help="Validate all files simultaneously using async processing"):
                    with st.spinner("Starting async validation..."):
                        validation_result = validate_files_async([f[1] for f in all_files])
                        if validation_result['success']:
                            st.info(validation_result['message'])
                            st.balloons()
                        else:
                            st.error(validation_result['message'])
            
            st.markdown("### 🔽 Paste Tech Stack + Points for Each Resume")
            # Lazy-render file tabs to avoid heavy UI cost on first load
            with st.expander("Show resume inputs", expanded=True):
                tabs = st.tabs([f[0] for f in all_files])
                for i, (file_name, file_obj) in enumerate(all_files):
                    with tabs[i]:
                        tab_handler.render_tab(file_obj)
            
            # Enhanced bulk operations section
            st.markdown("---")
            st.markdown("## 🚀 Bulk Operations (High Performance Mode)")
            if st.session_state.get('async_initialized'):
                st.success("⚡ Async processing enabled - Up to 6x faster bulk operations!")
            else:
                st.warning("Async processing not available - using standard processing")
            
            st.info("This tab is for individual resume processing only.\n\nFor bulk operations (generate/send all resumes), please go to the 'Bulk Processor' tab.")
        else:
            st.info("👆 Please upload or pick one or more DOCX resumes to get started.")

    if "👁️ Preview ALL" in tab_labels:
        with tab_preview_all:
            st.header("👁️ Preview ALL Resumes")
            previews = st.session_state.get('all_resume_previews', [])
            if not previews:
                st.info("No previews available. Please generate all resumes first.")
            else:
                for preview in previews:
                    file_name = preview.get('file_name') or preview.get('filename') or "Resume"
                    st.subheader(f"📄 {file_name}")
                    # Try to show HTML preview if available, else fallback to text
                    if 'preview_html' in preview:
                        st.markdown(preview['preview_html'], unsafe_allow_html=True)
                    elif 'preview_content' in preview:
                        st.text_area("Preview Content", value=preview['preview_content'], height=400)
                    else:
                        st.info("No preview content available for this resume.")
            if st.button("❌ Close Preview ALL Tab", key="close_preview_all_tab"):
                st.session_state['show_preview_all_tab'] = False
                st.experimental_rerun()

    with tab_bulk:
        # Bulk Processor Tab
        st.header("📤 Bulk Processor")
        st.write("Process multiple resumes simultaneously for maximum speed.")
        st.info("For individual resume processing, use the 'Resume Customizer' tab.\n\nFor bulk operations (generate/send all resumes), use this tab.")

        uploaded_files = st.session_state.get('file_upload_customizer', None)
        if not uploaded_files:
            st.warning("No resumes uploaded. Please upload resumes in the 'Resume Customizer' tab first.")
        else:
            st.markdown("### 📧 Bulk Resume Actions")
            st.info("You can generate all resumes or send all via email with one click.")
            bulk_processor.render_bulk_actions(uploaded_files)

    with tab_requirements:
        # Requirements Management Tab with Enhanced Features
        try:
            from requirements_integration import render_smart_customization_panel, render_requirements_analytics
            
            # Tabs within the requirements tab for better organization
            req_subtabs = st.tabs(["📝 Create/View", "🎯 Smart Customization", "📊 Analytics"])
            
            with req_subtabs[0]:
                render_requirements_tab()
            
            with req_subtabs[1]:
                render_smart_customization_panel()
            
            with req_subtabs[2]:
                render_requirements_analytics()
                
        except ImportError as e:
            logger.warning(f"Enhanced requirements features not available: {e}")
            # Fallback to basic requirements tab
            render_requirements_tab()

    with tab_application_guide:
        # Application Guide Tab
        app_guide.render_main_tab()

    with tab_settings:
        # Settings Tab
        st.header("⚙️ Application Settings")
        st.write("Configure application settings and preferences.")
        
        # Async Processing Status
        st.subheader("⚡ High-Performance Mode")
        if st.session_state.get('async_initialized'):
            st.success("✅ Async processing enabled - Experience up to 6x faster processing!")
            
            # Cache statistics
            try:
                from monitoring.performance_cache import get_cache_manager
                cache_manager = get_cache_manager()
                st.markdown("**Cache Performance:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    doc_cache = cache_manager.get_cache('document')
                    st.metric("Document Cache", f"{doc_cache.size}/{doc_cache.max_size}")
                with col2:
                    parse_cache = cache_manager.get_cache('parsing')
                    st.metric("Parse Cache", f"{parse_cache.size}/{parse_cache.max_size}")
                with col3:
                    file_cache = cache_manager.get_cache('file')
                    st.metric("File Cache", f"{file_cache.size}/{file_cache.max_size}")
            except Exception as e:
                st.warning(f"Cache stats unavailable: {e}")
                
            # Memory cleanup option
            if st.button("🧹 Force Memory Cleanup"):
                try:
                    background_manager = st.session_state.background_task_manager
                    task_id = background_manager.start_memory_cleanup()
                    st.success("Memory cleanup task started in background")
                    
                    # Also clear lazy import cache if available
                    try:
                        from utilities.lazy_imports import clear_lazy_cache
                        clear_lazy_cache()
                        st.info("Lazy import cache cleared")
                    except ImportError:
                        pass
                except Exception as e:
                    st.error(f"Failed to start memory cleanup: {e}")
        else:
            st.error("❌ Async processing disabled - Performance may be slower")
            if st.button("🔄 Retry Async Initialization"):
                st.session_state.async_initialized = initialize_async_services()
                st.experimental_rerun()
        
        st.markdown("---")
        
        # Display application health status
        st.subheader("🔍 Application Health")
        if health_status['healthy']:
            st.success("✅ Application is healthy")
        else:
            st.error("❌ Application has issues")
        if health_status['warnings']:
            st.warning("\n".join(["⚠️ " + w for w in health_status['warnings']]))
        
        # Performance Summary - moved inside settings tab
        st.markdown("---")
        st.subheader("📊 Performance Summary")
        if st.checkbox("Show Performance Details", value=False, key="settings_performance_checkbox"):
            with st.spinner("Collecting performance summary..."):
                summary = performance_monitor.get_performance_summary()
            if summary.get('system'):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("CPU Usage", f"{summary['system'].get('cpu_percent', 0):.1f}%")
                with col2:
                    st.metric("Memory Usage", f"{summary['system'].get('memory_percent', 0):.1f}%")
                with col3:
                    st.metric("Memory Used", f"{summary['system'].get('memory_used_mb', 0):.0f}MB")
                    
                # Show lazy loading stats if available
                try:
                    from utilities.lazy_imports import get_lazy_module_stats
                    lazy_stats = get_lazy_module_stats()
                    if lazy_stats['loaded_count'] > 0:
                        st.markdown("**Lazy Loading:**")
                        st.text(f"Loaded modules: {lazy_stats['loaded_count']}")
                        if lazy_stats['loaded_modules']:
                            with st.expander("Loaded modules details"):
                                for module in lazy_stats['loaded_modules']:
                                    st.text(f"• {module}")
                except ImportError:
                    pass
            else:
                st.info("Performance data not available.")

    # Footer with version info
    version = config.get('version', '1.0.0')
    st.markdown(
        f"""
        <style>
        .footer {{
            text-align: center;
            padding: 10px;
            border-top: 1px solid #e0e0e0;
            margin-top: 20px;
        }}
        .footer a {{
            color: #1f77b4;
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        </style>
        <div class="footer">
            <p>
                <strong>Resume Customizer Pro v{version}</strong> | 
                Enhanced with Security & Performance Monitoring |
                <a href="#" onclick="alert('Support: contact@resumecustomizer.com')">Support</a> |
                <a href="#" onclick="alert('Documentation available in README.md')">Docs</a>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def cleanup_on_exit():
    """Cleanup resources on application exit."""
    try:
        # Cleanup performance monitor
        from monitoring.performance_monitor import cleanup_performance_monitor
        cleanup_performance_monitor()
        
        # Cleanup document resources
        from core.document_processor import cleanup_document_resources
        cleanup_document_resources()
        
        # Cleanup email connections
        email_manager.close_all_connections()
        
        logger.info("Application cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        main()
    finally:
        cleanup_on_exit()


