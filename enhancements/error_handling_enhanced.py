"""
Enhanced error handling system for Resume Customizer application.
Provides structured error responses, user-friendly messages, and detailed logging.
"""

import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Type, List
from dataclasses import dataclass, field
from enum import Enum
import streamlit as st

from utilities.logger import get_logger
from audit_logger import audit_logger

logger = get_logger()


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation: Optional[str] = None
    file_name: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredError:
    """Structured error with comprehensive information."""
    error_id: str
    error_type: str
    message: str
    user_message: str
    severity: ErrorSeverity
    timestamp: datetime
    context: ErrorContext
    traceback_info: Optional[str] = None
    suggested_actions: List[str] = field(default_factory=list)


class ErrorMessageGenerator:
    """Generate user-friendly error messages."""
    
    ERROR_MESSAGES = {
        # File processing errors
        "FileNotFoundError": "The file you're trying to process could not be found. Please check the file and try uploading again.",
        "PermissionError": "We don't have permission to access this file. Please check the file permissions or try a different file.",
        "FileProcessingError": "There was an issue processing your file. Please ensure it's a valid Word document (.docx) and try again.",
        
        # Network/Email errors
        "ConnectionError": "We're having trouble connecting to the email server. Please check your internet connection and try again.",
        "SMTPAuthenticationError": "Email authentication failed. Please verify your email address and password (use app-specific password for Gmail).",
        "SMTPServerDisconnected": "Lost connection to the email server. Please try again in a moment.",
        
        # Processing errors
        "ValidationError": "The input data doesn't meet our requirements. Please check your entries and try again.",
        "ProcessingTimeoutError": "The operation took too long to complete. Please try with fewer files or smaller documents.",
        "MemoryError": "The system is running low on memory. Please try processing fewer files at once or restart the application.",
        
        # Generic errors
        "UnexpectedError": "Something unexpected happened. Our team has been notified and will investigate the issue."
    }
    
    SUGGESTED_ACTIONS = {
        "FileNotFoundError": [
            "Re-upload the file",
            "Check if the file was moved or deleted",
            "Try a different file"
        ],
        "PermissionError": [
            "Close the file in other applications",
            "Save the file to a different location",
            "Check file permissions"
        ],
        "SMTPAuthenticationError": [
            "Verify your email address is correct",
            "Use an app-specific password for Gmail/Office365",
            "Check if 2-factor authentication is enabled",
            "Try a different email account"
        ],
        "ConnectionError": [
            "Check your internet connection",
            "Try again in a few minutes",
            "Use a different network if possible"
        ],
        "MemoryError": [
            "Process fewer files at once",
            "Restart the application",
            "Close other browser tabs",
            "Try smaller document files"
        ]
    }
    
    @classmethod
    def get_user_message(cls, error_type: str, original_message: str = "") -> str:
        """Get user-friendly error message."""
        base_message = cls.ERROR_MESSAGES.get(error_type, cls.ERROR_MESSAGES["UnexpectedError"])
        
        # Add specific details if available
        if original_message and error_type not in ["UnexpectedError"]:
            base_message += f" Technical details: {original_message}"
        
        return base_message
    
    @classmethod
    def get_suggested_actions(cls, error_type: str) -> List[str]:
        """Get suggested actions for error type."""
        return cls.SUGGESTED_ACTIONS.get(error_type, [
            "Refresh the page and try again",
            "Contact support if the problem persists"
        ])


class ErrorHandler:
    """Central error handler for the application."""
    
    def __init__(self):
        self.message_generator = ErrorMessageGenerator()
    
    def handle_error(
        self,
        exception: Exception,
        context: ErrorContext,
        show_to_user: bool = True,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> StructuredError:
        """Handle an error with comprehensive logging and user feedback."""
        
        # Generate unique error ID
        error_id = str(uuid.uuid4())[:8]
        
        # Determine error type
        error_type = type(exception).__name__
        
        # Get user-friendly message
        user_message = self.message_generator.get_user_message(error_type, str(exception))
        suggested_actions = self.message_generator.get_suggested_actions(error_type)
        
        # Create structured error
        structured_error = StructuredError(
            error_id=error_id,
            error_type=error_type,
            message=str(exception),
            user_message=user_message,
            severity=severity,
            timestamp=datetime.now(),
            context=context,
            traceback_info=traceback.format_exc(),
            suggested_actions=suggested_actions
        )
        
        # Log error with appropriate level
        self._log_error(structured_error)
        
        # Show to user if requested
        if show_to_user:
            self._display_error_to_user(structured_error)
        
        # Audit log for security-related errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            audit_logger.log(
                action="error_occurred",
                user=context.user_id,
                details={
                    "error_id": error_id,
                    "error_type": error_type,
                    "operation": context.operation,
                    "severity": severity.value
                },
                status="error"
            )
        
        return structured_error
    
    def _log_error(self, error: StructuredError):
        """Log error with appropriate level based on severity."""
        log_message = (
            f"[{error.error_id}] {error.error_type} in {error.context.operation}: {error.message}"
        )
        
        if error.severity == ErrorSeverity.LOW:
            logger.info(log_message, error_id=error.error_id)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, error_id=error.error_id)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message, error_id=error.error_id, exception=Exception(error.message))
        else:  # CRITICAL
            logger.critical(log_message, error_id=error.error_id, exception=Exception(error.message))
    
    def _display_error_to_user(self, error: StructuredError):
        """Display error to user with contextual information."""
        try:
            # Create contextual error message
            contextual_message = self._create_contextual_error_message(error)
            
            if error.severity == ErrorSeverity.LOW:
                st.info(f"ℹ️ {contextual_message}")
            elif error.severity == ErrorSeverity.MEDIUM:
                st.warning(f"⚠️ {contextual_message}")
            else:  # HIGH or CRITICAL
                st.error(f"🚨 {contextual_message}")
            
            # Show suggested actions in expandable section
            if error.suggested_actions:
                with st.expander("💡 Suggested Solutions", expanded=False):
                    for i, action in enumerate(error.suggested_actions, 1):
                        st.write(f"{i}. {action}")
            
            # Show error ID for critical errors
            if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                st.caption(f"Error ID: {error.error_id} (Please provide this ID when contacting support)")
        
        except Exception as e:
            logger.error(f"Failed to display error to user: {e}")
    
    def _create_contextual_error_message(self, error: StructuredError) -> str:
        """Create contextual error message with helpful information."""
        base_message = error.user_message
        
        # Add context based on operation
        if error.context.operation:
            if "upload" in error.context.operation.lower():
                base_message += " Please ensure your file is a valid Word document (.docx) and try again."
            elif "email" in error.context.operation.lower():
                base_message += " Please check your email settings and internet connection."
            elif "process" in error.context.operation.lower():
                base_message += " Please try with a different file or contact support if the issue persists."
        
        # Add file context if available
        if error.context.file_name:
            base_message += f" (File: {error.context.file_name})"
        
        return base_message


# Decorator for automatic error handling
def handle_errors(
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    show_to_user: bool = True,
    return_on_error: Any = None
):
    """Decorator for automatic error handling."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            
            context = ErrorContext(
                user_id=st.session_state.get('user_id', 'anonymous'),
                session_id=st.session_state.get('session_id'),
                operation=operation,
                additional_data={"function": func.__name__}
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(e, context, show_to_user, severity)
                return return_on_error
        
        return wrapper
    return decorator


# Context manager for operation-specific error handling
class ErrorHandlerContext:
    """Context manager for handling errors in specific operations."""
    
    def __init__(
        self,
        operation: str,
        file_name: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        show_to_user: bool = True
    ):
        self.operation = operation
        self.file_name = file_name
        self.severity = severity
        self.show_to_user = show_to_user
        self.error_handler = ErrorHandler()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            context = ErrorContext(
                user_id=st.session_state.get('user_id', 'anonymous'),
                session_id=st.session_state.get('session_id'),
                operation=self.operation,
                file_name=self.file_name
            )
            
            self.error_handler.handle_error(
                exc_val, context, self.show_to_user, self.severity
            )
            
            # Suppress the exception (return True)
            return True
        return False


# Usage examples:

@handle_errors("file_processing", ErrorSeverity.HIGH, show_to_user=True, return_on_error=None)
def process_resume_with_error_handling(file_obj, tech_stacks):
    """Example function with automatic error handling."""
    # Your processing logic here
    pass

def example_context_usage():
    """Example of using the error handler context manager."""
    with ErrorHandlerContext("email_sending", "resume.docx", ErrorSeverity.HIGH):
        # Email sending logic here
        # Any exceptions will be handled automatically
        pass



