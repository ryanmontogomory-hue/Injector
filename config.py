"""
Configuration module for Resume Customizer application.
Contains all constants, default values, and configuration settings with validation.
"""

import os
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote_plus
import logging

# Try to import python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False
    
logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationResult:
    """Result of configuration validation."""
    valid: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_issue(self, issue: str) -> None:
        """Add a validation issue."""
        self.issues.append(issue)
        self.valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)


class EnvironmentConfig:
    """Environment variable configuration manager."""
    
    @staticmethod
    def load_env_file(env_path: str = ".env") -> bool:
        """Load environment variables from .env file if available."""
        if not _DOTENV_AVAILABLE:
            logger.warning("python-dotenv not available, using system environment variables only")
            return False
            
        env_file = Path(env_path)
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_path}")
            return True
        else:
            logger.info(f"No .env file found at {env_path}, using system environment variables")
            return False
    
    @staticmethod
    def get_env_int(key: str, default: int) -> int:
        """Get integer value from environment variable."""
        try:
            return int(os.getenv(key, default))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def get_env_bool(key: str, default: bool) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_env_list(key: str, default: List[str], separator: str = ',') -> List[str]:
        """Get list value from environment variable."""
        value = os.getenv(key)
        if value:
            return [item.strip() for item in value.split(separator) if item.strip()]
        return default
    
    @staticmethod
    def create_env_template(file_path: str = ".env.template") -> bool:
        """Create a template .env file with all configuration variables."""
        try:
            template_content = '''# Resume Customizer Configuration
# Copy this to .env and modify values as needed

# Application Settings
APP_TITLE="📝 Resume Customizer + Email Sender"
APP_PAGE_TITLE="Resume Customizer"
APP_LAYOUT=wide
APP_VERSION=2.1.0
APP_MAX_WORKERS_DEFAULT=4
APP_MAX_WORKERS_LIMIT=8
APP_BULK_MODE_THRESHOLD=3

# Environment Settings
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# Email Configuration (Optional - can be set in UI)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true

# Security Settings
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# Redis Configuration (Optional - for caching)
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=10
REDIS_TIMEOUT=30

# Performance Settings
CACHE_TTL=3600
MEMORY_CLEANUP_THRESHOLD=10
CONNECTION_POOL_TIMEOUT=30

# File Processing Settings
MAX_FILE_SIZE_MB=50
MAX_PROJECTS_ENHANCED=3
DEFAULT_BULLET_MARKERS="-,•,*"

# UI Settings
SIDEBAR_EXPANDED=true
SHOW_PERFORMANCE_METRICS=true
ENABLE_PREVIEW_MODE=true

# Monitoring Settings
ENABLE_HEALTH_CHECK=true
HEALTH_CHECK_INTERVAL=300
ENABLE_METRICS_COLLECTION=true
'''
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            logger.info(f"✅ Environment template created: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create environment template: {e}")
            return False


class ConfigValidator:
    """Configuration validation utility class."""
    
    REQUIRED_APP_CONFIGS = [
        'title', 'page_title', 'layout', 'max_workers_default', 
        'max_workers_limit', 'bulk_mode_threshold', 'version'
    ]
    
    @staticmethod
    def validate_numeric_range(value: Any, min_val: int, max_val: int, name: str) -> Optional[str]:
        """Validate that a numeric value is within a specified range."""
        try:
            num_val = int(value)
            if num_val < min_val or num_val > max_val:
                return f"{name} must be between {min_val} and {max_val}, got {num_val}"
        except (ValueError, TypeError):
            return f"{name} must be a valid integer, got {type(value).__name__}"
        return None
    
    @staticmethod
    def validate_string_not_empty(value: Any, name: str) -> Optional[str]:
        """Validate that a string value is not empty."""
        if not isinstance(value, str) or not value.strip():
            return f"{name} must be a non-empty string"
        return None


# Initialize environment configuration
env_config = EnvironmentConfig()
env_config.load_env_file()  # Try to load .env file

# Application Configuration with Environment Variable Support
def _get_app_config() -> Dict[str, Any]:
    """Get application configuration with environment variable overrides."""
    return {
        "title": os.getenv("APP_TITLE", "📝 Resume Customizer + Email Sender"),
        "page_title": os.getenv("APP_PAGE_TITLE", "Resume Customizer"),
        "layout": os.getenv("APP_LAYOUT", "wide"),
        "max_workers_default": env_config.get_env_int("APP_MAX_WORKERS_DEFAULT", 4),
        "max_workers_limit": env_config.get_env_int("APP_MAX_WORKERS_LIMIT", 8),
        "bulk_mode_threshold": env_config.get_env_int("APP_BULK_MODE_THRESHOLD", 3),
        "version": os.getenv("APP_VERSION", "2.1.0"),
        "build_date": os.getenv("BUILD_DATE", "2024-01-15"),
        "author": os.getenv("APP_AUTHOR", "Resume Customizer Team"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": env_config.get_env_bool("DEBUG", False),
        "secret_key": os.getenv("SECRET_KEY"),
        "encryption_key": os.getenv("ENCRYPTION_KEY"),
    }

# Cache the app config
APP_CONFIG = _get_app_config()

# SMTP Configuration with Environment Variable Support
def _get_smtp_config() -> Dict[str, Dict[str, Any]]:
    """Get SMTP configuration with environment variable overrides."""
    # Base configuration
    smtp_config = {
        "Gmail": {"server": "smtp.gmail.com", "port": 465},
        "Office365": {"server": "smtp.office365.com", "port": 587},
        "Yahoo": {"server": "smtp.mail.yahoo.com", "port": 465},
        "Custom": {"server": "Custom", "port": 587}
    }
    
    # Environment variable overrides
    custom_smtp = os.getenv("SMTP_SERVER")
    custom_port = env_config.get_env_int("SMTP_PORT", 587)
    
    if custom_smtp and custom_smtp != "Custom":
        smtp_config["Custom"] = {"server": custom_smtp, "port": custom_port}
    
    return smtp_config


# Cache the SMTP config
SMTP_SERVERS = _get_smtp_config()

SMTP_SERVER_OPTIONS = ["smtp.gmail.com", "smtp.office365.com", "smtp.mail.yahoo.com", "Custom"]

# Default Email Configuration with Environment Variable Support
def _get_email_config() -> Dict[str, Any]:
    """Get email configuration with environment variable overrides."""
    return {
        "subject": lambda: f"Customized Resume - {datetime.now().strftime('%Y-%m-%d')}",
        "body": os.getenv("EMAIL_BODY", "Hi,\n\nPlease find the customized resume attached.\n\nThis resume highlights experience with various technologies and skills.\n\nBest regards"),
        "smtp_port": env_config.get_env_int("SMTP_PORT", 465),
        "smtp_username": os.getenv("SMTP_USERNAME"),
        "smtp_password": os.getenv("SMTP_PASSWORD"),
        "smtp_use_tls": env_config.get_env_bool("SMTP_USE_TLS", True),
    }

DEFAULT_EMAIL_CONFIG = _get_email_config()

# Text Parsing Configuration
PARSING_CONFIG = {
    "tech_name_exclude_words": [
        'developed', 'created', 'implemented', 'designed', 
        'built', 'worked', 'managed', 'used', 'wrote', 'configured'
    ],
    "project_exclude_keywords": [
        "summary", "skills", "education", "achievements", "responsibilities:"
    ],
    "job_title_keywords": [
        "manager", "developer", "engineer", "analyst", "lead", 
        "senior", "junior", "architect", "consultant", "specialist", 
        "coordinator", "supervisor", "director", "designer", 
        "tester", "qa", "devops"
    ],
    "project_keywords": [
        "project", "team", "role", "position", "intern", 
        "trainee", "associate"
    ],
    "section_end_keywords": [
        "achievements", "technologies", "tools", "key"
    ]
}

# Document Processing Configuration with Environment Variable Support
def _get_doc_config() -> Dict[str, Any]:
    """Get document processing configuration with environment variable overrides."""
    return {
        "max_projects_enhanced": env_config.get_env_int("MAX_PROJECTS_ENHANCED", 3),
        "bullet_markers": env_config.get_env_list("DEFAULT_BULLET_MARKERS", ['-', '•', '*']),
        "default_filename": os.getenv("DEFAULT_FILENAME", "resume.docx"),
        "max_project_title_length": env_config.get_env_int("MAX_PROJECT_TITLE_LENGTH", 100),
        "max_file_size_mb": env_config.get_env_int("MAX_FILE_SIZE_MB", 50),
    }

DOC_CONFIG = _get_doc_config()

# UI Configuration
UI_CONFIG = {
    "sidebar_instructions": """
    1. Upload your resume(s) in DOCX format
    2. For each resume, provide:
       - Tech stacks with bullet points (format: 'TechName: • point1 • point2')
       - Email credentials for sending (optional)
    3. Click '🔍 Preview Changes' to see exactly what will be modified
    4. Review the preview and click 'Generate & Send Customized Resumes'
    5. Download or email the customized resumes
    """,
    
    "preview_features": """
    The preview will show you ONLY the changes:
    - ✅ Which projects will be enhanced
    - ➕ Exactly which NEW points will be added
    - 🎯 Where each point will be inserted
    - 📧 Email configuration status
    - 📊 Summary of additions only
    """,
    
    "project_selection_info": """
    **Top 3 Projects Focus:**
    - Points are added only to the first 3 projects
    - This highlights your most recent/relevant work
    - Projects 4+ remain unchanged
    - If you have ≤ 3 projects, all get points
    """,
    
    "format_preservation_info": """
    The app will preserve all formatting exactly:
    - Font family and size
    - Font color
    - Bold/italic/underline styles
    - Paragraph spacing and indentation
    - Bullet point styling
    """,
    
    "security_note": """
    - We recommend using app-specific passwords
    - Your credentials are not stored
    - Consider using a dedicated email for this purpose
    """,
    
    "bulk_benefits": """
    **Benefits of Bulk Mode:**
    - ⚡ **Up to 8x faster** processing with parallel workers
    - 🔄 **SMTP connection reuse** for faster email sending
    - 📊 **Real-time progress** tracking
    - 📈 **Performance metrics** and statistics
    - 🎯 **Batch processing** optimizations
    """,
    
    "example_format": """
Python: • Developed web applications using Django and Flask • Implemented RESTful APIs
JavaScript: • Created interactive UI components with React • Utilized Node.js for backend services
AWS: • Deployed applications using EC2 and S3 • Managed databases with RDS
SQL: • Designed and optimized database schemas • Wrote complex queries for reporting
    """,
    
    "file_upload_help": "Upload one or more .docx resumes",
    "tech_stack_help": "Format: 'TechName: • point1 • point2'",
}

# Performance Configuration with Environment Variable Support
def _get_performance_config() -> Dict[str, Any]:
    """Get performance configuration with environment variable overrides."""
    return {
        "estimated_sequential_time_per_resume": env_config.get_env_int("ESTIMATED_TIME_PER_RESUME", 8),
        "memory_cleanup_threshold": env_config.get_env_int("MEMORY_CLEANUP_THRESHOLD", 10),
        "connection_pool_timeout": env_config.get_env_int("CONNECTION_POOL_TIMEOUT", 30),
        "cache_ttl": env_config.get_env_int("CACHE_TTL", 3600),
        "enable_metrics_collection": env_config.get_env_bool("ENABLE_METRICS_COLLECTION", True),
        "health_check_interval": env_config.get_env_int("HEALTH_CHECK_INTERVAL", 300),
    }

PERFORMANCE_CONFIG = _get_performance_config()

# Error Messages
ERROR_MESSAGES = {
    "no_tech_stacks": "Could not parse tech stacks for {filename}. Please check your input format.",
    "no_projects": "No projects found in {filename}. Ensure your resume has project sections.",
    "parsing_failed": "Could not parse tech stacks from input for {filename}. Please use the format 'TechName: • point1 • point2' or the new block format.",
    "no_responsibilities": "Could not find projects with Responsibilities sections or bullet points in {filename}. Please ensure your resume has work experience sections with bullet points describing your responsibilities.",
    "custom_smtp_not_supported": "Custom SMTP server not supported in bulk mode. Please use Gmail, Office365, or Yahoo.",
    "smtp_connection_failed": "Failed to create SMTP connection: {error}. Please check your email credentials and network connection.",
    "email_send_failed": "Failed to send email for {filename}: {error}. Please verify your email settings.",
    "file_validation_failed": "File validation failed: {error}. Please check file format and size.",
    "memory_error": "Memory error during processing. Please try with fewer files or restart the application.",
    "processing_timeout": "Processing timeout. Please try again or reduce the number of files.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "preview_generated": "✅ Preview generated with {points_added} points added!",
    "email_sent": "📧 Email sent successfully for {filename} to {recipient}",
    "processing_complete": "✅ {filename} has been processed successfully!",
    "bulk_complete": "🚀 Bulk processing completed successfully!",
    "file_uploaded": "📁 {filename} uploaded successfully ({size_mb:.1f}MB)",
    "validation_passed": "✅ All files validated successfully",
    "health_check_passed": "✅ Application health check passed",
    "config_validated": "✅ Configuration validated successfully",
}

@st.cache_data
def get_app_config() -> Dict[str, Any]:
    """Get application configuration.
    
    Returns:
        Dict[str, Any]: Application configuration dictionary
    """
    return APP_CONFIG.copy()

@st.cache_data
def get_smtp_servers() -> List[str]:
    """Get list of available SMTP servers.
    
    Returns:
        List[str]: List of available SMTP server options
    """
    return SMTP_SERVER_OPTIONS.copy()

def get_default_email_subject() -> str:
    """Get default email subject with current date."""
    try:
        return DEFAULT_EMAIL_CONFIG["subject"]()
    except Exception:
        return f"Customized Resume - {datetime.now().strftime('%Y-%m-%d')}"

def get_default_email_body() -> str:
    """Get default email body."""
    return DEFAULT_EMAIL_CONFIG["body"]

def validate_config() -> ConfigValidationResult:
    """Comprehensive configuration validation with detailed feedback.
    
    Returns:
        ConfigValidationResult: Detailed validation results
    """
    result = ConfigValidationResult(valid=True)
    validator = ConfigValidator()
    
    try:
        # Validate required configurations
        for config_key in validator.REQUIRED_APP_CONFIGS:
            if config_key not in APP_CONFIG:
                result.add_issue(f"Missing required config: {config_key}")
            elif APP_CONFIG[config_key] is None:
                result.add_issue(f"Config {config_key} cannot be None")
        
        # Validate string configurations
        string_configs = ['title', 'page_title', 'layout', 'version']
        for config_key in string_configs:
            if config_key in APP_CONFIG:
                error = validator.validate_string_not_empty(APP_CONFIG[config_key], config_key)
                if error:
                    result.add_issue(error)
        
        # Validate numeric configurations
        if 'max_workers_default' in APP_CONFIG:
            error = validator.validate_numeric_range(
                APP_CONFIG['max_workers_default'], 1, 16, 'max_workers_default'
            )
            if error:
                result.add_issue(error)
        
        if 'max_workers_limit' in APP_CONFIG:
            error = validator.validate_numeric_range(
                APP_CONFIG['max_workers_limit'], 1, 32, 'max_workers_limit'
            )
            if error:
                result.add_issue(error)
        
        if 'bulk_mode_threshold' in APP_CONFIG:
            error = validator.validate_numeric_range(
                APP_CONFIG['bulk_mode_threshold'], 1, 10, 'bulk_mode_threshold'
            )
            if error:
                result.add_issue(error)
        
        # Validate performance settings relationships
        max_default = APP_CONFIG.get('max_workers_default', 0)
        max_limit = APP_CONFIG.get('max_workers_limit', 0)
        if max_limit < max_default:
            result.add_issue(f"max_workers_limit ({max_limit}) should be >= max_workers_default ({max_default})")
        
        # Validate SMTP servers
        if not SMTP_SERVER_OPTIONS:
            result.add_issue("No SMTP servers configured")
        elif len(SMTP_SERVER_OPTIONS) < 2:
            result.add_warning("Only one SMTP server configured, consider adding backup options")
        
        # Validate SMTP server configuration
        for server_name, server_config in SMTP_SERVERS.items():
            if not isinstance(server_config, dict):
                result.add_issue(f"SMTP server {server_name} configuration must be a dictionary")
                continue
            
            if 'server' not in server_config or 'port' not in server_config:
                result.add_issue(f"SMTP server {server_name} missing required 'server' or 'port' configuration")
            
            # Validate port numbers
            port = server_config.get('port')
            if port and not isinstance(port, int) or port < 1 or port > 65535:
                result.add_issue(f"SMTP server {server_name} has invalid port: {port}")
        
        # Validate parsing configuration
        if not PARSING_CONFIG.get('tech_name_exclude_words'):
            result.add_warning("No tech_name_exclude_words configured, may affect parsing accuracy")
        
        # Check environment-dependent settings
        if not Path('logs').exists():
            result.add_warning("Logs directory does not exist, will be created automatically")
        
        # Performance warnings
        if max_default > 8:
            result.add_warning(f"max_workers_default ({max_default}) is quite high, may impact system performance")
        
    except Exception as e:
        result.add_issue(f"Configuration validation failed with error: {str(e)}")
    
    return result


def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration from environment variables."""
    return {
        "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        "max_connections": env_config.get_env_int("REDIS_MAX_CONNECTIONS", 10),
        "timeout": env_config.get_env_int("REDIS_TIMEOUT", 30),
        "enabled": env_config.get_env_bool("REDIS_ENABLED", False),
    }


def get_security_config() -> Dict[str, Any]:
    """Get security configuration from environment variables."""
    return {
        "secret_key": os.getenv("SECRET_KEY"),
        "encryption_key": os.getenv("ENCRYPTION_KEY"),
        "enable_csrf_protection": env_config.get_env_bool("ENABLE_CSRF_PROTECTION", True),
        "session_timeout": env_config.get_env_int("SESSION_TIMEOUT", 3600),
        "max_login_attempts": env_config.get_env_int("MAX_LOGIN_ATTEMPTS", 5),
    }


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration from environment variables."""
    return {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        "file_path": os.getenv("LOG_FILE_PATH", "logs/app.log"),
        "max_file_size": env_config.get_env_int("LOG_MAX_FILE_SIZE", 10485760),  # 10MB
        "backup_count": env_config.get_env_int("LOG_BACKUP_COUNT", 5),
    }


def is_production() -> bool:
    """Check if running in production environment."""
    return os.getenv("ENVIRONMENT", "development").lower() == "production"


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return env_config.get_env_bool("DEBUG", False)


def create_env_template() -> bool:
    """Create environment variable template file."""
    return env_config.create_env_template()


def reload_config() -> None:
    """Reload configuration from environment variables."""
    global APP_CONFIG, SMTP_SERVERS, DEFAULT_EMAIL_CONFIG, DOC_CONFIG, PERFORMANCE_CONFIG
    
    # Reload environment variables
    env_config.load_env_file()
    
    # Reload configurations
    APP_CONFIG = _get_app_config()
    SMTP_SERVERS = _get_smtp_config()
    DEFAULT_EMAIL_CONFIG = _get_email_config()
    DOC_CONFIG = _get_doc_config()
    PERFORMANCE_CONFIG = _get_performance_config()
    
    logger.info("Configuration reloaded from environment variables")

