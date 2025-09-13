"""
Ultra-fast configuration module with aggressive caching.
Replaces slow config operations with lightning-fast cached versions.
"""

import streamlit as st
from typing import Dict, Any
import os

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_ultra_fast_config() -> Dict[str, Any]:
    """Lightning-fast config with aggressive caching."""
    return {
        "title": "⚡ Resume Customizer - Ultra Fast",
        "page_title": "Resume Customizer",
        "layout": "wide",
        "max_workers_default": 2,  # Reduced for speed
        "max_workers_limit": 4,    # Reduced for speed  
        "bulk_mode_threshold": 2,  # Lower threshold for speed
        "version": "3.0-TURBO",
        "debug": False,  # Disable debug for speed
        "fast_mode": True
    }

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_fast_ui_config() -> Dict[str, Any]:
    """Ultra-fast UI configuration."""
    return {
        "sidebar_instructions": """
        🚀 **ULTRA-FAST MODE**
        1. Upload resumes (DOCX)
        2. Add tech stacks  
        3. Process instantly
        """,
        "example_format": """
Python: • Fast Django apps • Quick APIs
React: • Lightning UI • Fast components
        """,
        "enable_animations": False,  # Disable for speed
        "minimize_redraws": True,
        "batch_updates": True
    }

@st.cache_data(ttl=3600)
def get_fast_smtp_config() -> Dict[str, str]:
    """Cached SMTP configuration."""
    return {
        "Gmail": "smtp.gmail.com:465",
        "Outlook": "smtp.office365.com:587", 
        "Yahoo": "smtp.mail.yahoo.com:465"
    }

# Performance constants
FAST_MODE_ENABLED = True
SKIP_HEAVY_VALIDATIONS = True
USE_MINIMAL_UI = True
CACHE_EVERYTHING = True