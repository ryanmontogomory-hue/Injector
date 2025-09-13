"""
Fast UI components with aggressive caching and lazy loading for super fast performance.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import time

@st.cache_resource
def get_fast_ui_manager():
    """Cached UI manager instance."""
    return FastUIManager()

class FastUIManager:
    """Ultra-fast UI component manager with aggressive caching."""
    
    def __init__(self):
        self.component_cache = {}
        self.render_cache = {}
    
    @st.cache_data(ttl=300)
    def fast_sidebar(_self, _config_data: Dict[str, Any]):
        """Super fast sidebar with caching."""
        with st.sidebar:
            st.title("🚀 Resume Customizer")
            st.markdown("**Ultra-Fast Mode Enabled**")
            
            # Performance metrics
            if st.session_state.get('show_perf_metrics', False):
                st.metric("⚡ Load Time", f"{st.session_state.get('load_time', 0):.2f}s")
                st.metric("📦 Cached Components", len(self.component_cache))
    
    @st.cache_data(ttl=60)
    def fast_file_uploader(_self, _key: str, max_files: int = 10):
        """Cached file uploader that remembers previous uploads."""
        return st.file_uploader(
            "📁 Upload Resume Files",
            type=['docx'],
            accept_multiple_files=True,
            key=f"fast_uploader_{_key}",
            help="Drag and drop DOCX files here for lightning-fast processing"
        )
    
    @st.cache_data(ttl=300)
    def fast_tabs(_self, tab_names: List[str], _key: str):
        """Ultra-fast tabs with minimal rerendering."""
        return st.tabs(tab_names)
    
    def render_fast_progress(_self, progress: float, text: str = ""):
        """Fast progress bar with minimal updates."""
        if not hasattr(st.session_state, 'last_progress_update'):
            st.session_state.last_progress_update = 0
        
        # Only update if significant change to reduce redraws
        if abs(progress - st.session_state.last_progress_update) > 0.05:
            st.progress(progress, text=text)
            st.session_state.last_progress_update = progress

@st.cache_resource
def get_lazy_processors():
    """Lazy load processors only when needed."""
    class LazyProcessors:
        def __init__(self):
            self._resume_processor = None
            self._bulk_processor = None
        
        @property
        def resume_processor(self):
            if self._resume_processor is None:
                from resume_customizer.processors.resume_processor import get_resume_manager
                self._resume_processor = get_resume_manager("v2.2")
            return self._resume_processor
        
        @property
        def bulk_processor(self):
            if self._bulk_processor is None:
                from ui.bulk_processor import BulkProcessor
                self._bulk_processor = BulkProcessor(resume_manager=self.resume_processor)
            return self._bulk_processor
    
    return LazyProcessors()

# Performance tracking
def track_load_time(func):
    """Decorator to track component load times."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        load_time = time.time() - start_time
        
        if 'component_load_times' not in st.session_state:
            st.session_state.component_load_times = {}
        st.session_state.component_load_times[func.__name__] = load_time
        
        return result
    return wrapper

@st.cache_data(ttl=3600)
def cached_template_data():
    """Cache template data for super fast access."""
    return {
        'email_templates': [
            "Professional Resume Submission",
            "Follow-up Application", 
            "Custom Message"
        ],
        'default_subjects': [
            "Resume - [Your Name] - [Position]",
            "Application for [Position] - [Your Name]",
            "Professional Resume Submission"
        ]
    }