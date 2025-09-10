"""
Comprehensive test suite for Resume Customizer application.
Includes unit tests, integration tests, and performance tests.
"""

import pytest
import tempfile
import os
import time
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from datetime import datetime
import sys
sys.path.append('..')

# Import modules to test
from config import validate_config, APP_CONFIG
from text_parser import TechStackParser
from validators import FileValidator, EmailValidator
from error_handling_enhanced import ErrorHandler, ErrorContext, ErrorSeverity
from memory_optimizer import MemoryOptimizer, MemoryMonitor
from security_enhancements import SecurePasswordManager, InputSanitizer, RateLimiter


class TestConfiguration:
    """Test configuration validation and settings."""
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        result = validate_config()
        assert result.valid, f"Config validation failed: {result.issues}"
    
    def test_required_config_keys(self):
        """Test that all required configuration keys exist."""
        required_keys = [
            'title', 'page_title', 'layout', 'max_workers_default',
            'max_workers_limit', 'bulk_mode_threshold', 'version'
        ]
        
        for key in required_keys:
            assert key in APP_CONFIG, f"Missing required config key: {key}"
            assert APP_CONFIG[key] is not None, f"Config key {key} is None"
    
    def test_worker_limits(self):
        """Test worker configuration limits."""
        assert 1 <= APP_CONFIG['max_workers_default'] <= 16
        assert 1 <= APP_CONFIG['max_workers_limit'] <= 32
        assert APP_CONFIG['max_workers_limit'] >= APP_CONFIG['max_workers_default']
    
    def test_bulk_threshold(self):
        """Test bulk processing threshold."""
        assert 1 <= APP_CONFIG['bulk_mode_threshold'] <= 10


class TestTextParser:
    """Test text parsing functionality."""
    
    def setUp(self):
        self.parser = TechStackParser()
    
    def test_parse_original_format(self):
        """Test parsing of original format."""
        text = "Python: • Developed web apps • Used Django\nJavaScript: • Created UI • Used React"
        points, stacks = self.parser.parse_original_format(text)
        
        assert len(points) == 4
        assert "Python" in stacks
        assert "JavaScript" in stacks
        assert "Developed web apps" in points
    
    def test_parse_new_format(self):
        """Test parsing of new block format."""
        text = """Python
Developed web applications
Used Django framework

JavaScript
Created interactive UI
Used React library"""
        
        points, stacks = self.parser.parse_new_format(text)
        
        assert len(points) >= 4
        assert "Python" in stacks
        assert "JavaScript" in stacks
    
    def test_empty_input(self):
        """Test parsing with empty input."""
        points, stacks = self.parser.parse_tech_stacks("")
        assert points == []
        assert stacks == []
    
    def test_fallback_parsing(self):
        """Test fallback bullet point extraction."""
        text = "• First point\n• Second point\n• Third point"
        points = self.parser._extract_fallback_points(text)
        
        assert len(points) == 3
        assert "First point" in points
        assert "Second point" in points
        assert "Third point" in points
    
    def test_tech_keyword_detection(self):
        """Test technology keyword detection."""
        test_cases = [
            ("python", True),
            ("javascript", True),
            ("react", True),
            ("cooking", False),  # Should not be recognized as tech
            ("management", False)
        ]
        
        for keyword, expected in test_cases:
            result = keyword.lower() in self.parser.TECH_KEYWORDS
            assert result == expected, f"Keyword '{keyword}' detection failed"


class TestFileValidator:
    """Test file validation functionality."""
    
    def setUp(self):
        self.validator = FileValidator()
    
    def create_mock_file(self, name: str, size: int, content: bytes = b""):
        """Create a mock file object for testing."""
        mock_file = Mock()
        mock_file.name = name
        mock_file.size = size
        mock_file.getvalue.return_value = content if content else b"PK" + b"x" * (size - 2)
        return mock_file
    
    def test_valid_docx_file(self):
        """Test validation of valid DOCX file."""
        mock_file = self.create_mock_file("test.docx", 1024 * 1024)  # 1MB
        result = self.validator.validate_file(mock_file)
        
        assert result['valid']
        assert result['file_info']['name'] == "test.docx"
        assert result['file_info']['size_mb'] == 1.0
    
    def test_file_too_large(self):
        """Test validation of oversized file."""
        mock_file = self.create_mock_file("large.docx", 60 * 1024 * 1024)  # 60MB
        result = self.validator.validate_file(mock_file)
        
        assert not result['valid']
        assert any("too large" in error for error in result['errors'])
    
    def test_invalid_extension(self):
        """Test validation of file with invalid extension."""
        mock_file = self.create_mock_file("test.exe", 1024)
        result = self.validator.validate_file(mock_file)
        
        assert not result['valid']
        assert any("suspicious extension" in error.lower() for error in result['errors'])
    
    def test_empty_file(self):
        """Test validation of empty file."""
        mock_file = self.create_mock_file("empty.docx", 0)
        result = self.validator.validate_file(mock_file)
        
        assert not result['valid']
        assert any("empty" in error for error in result['errors'])
    
    def test_batch_validation(self):
        """Test batch file validation."""
        files = [
            self.create_mock_file("file1.docx", 1024),
            self.create_mock_file("file2.docx", 2048),
            self.create_mock_file("invalid.exe", 1024)
        ]
        
        result = self.validator.validate_batch(files)
        
        assert 'summary' in result
        assert result['summary']['total_files'] == 3
        assert result['summary']['valid_files'] == 2


class TestEmailValidator:
    """Test email validation functionality."""
    
    def test_valid_emails(self):
        """Test validation of valid email addresses."""
        valid_emails = [
            "user@example.com",
            "test.user@gmail.com",
            "user+tag@company.org",
            "user123@domain.co.uk"
        ]
        
        for email in valid_emails:
            result = EmailValidator.validate_email(email)
            assert result['valid'], f"Valid email '{email}' failed validation"
    
    def test_invalid_emails(self):
        """Test validation of invalid email addresses."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user space@example.com",
            ""
        ]
        
        for email in invalid_emails:
            result = EmailValidator.validate_email(email)
            assert not result['valid'], f"Invalid email '{email}' passed validation"
    
    def test_smtp_server_validation(self):
        """Test SMTP server configuration validation."""
        valid_servers = ["smtp.gmail.com", "smtp.office365.com"]
        
        for server in valid_servers:
            result = EmailValidator.validate_smtp_server(server, 587)
            assert result['valid'], f"Valid SMTP server '{server}' failed validation"


class TestSecurityFeatures:
    """Test security enhancements."""
    
    def test_password_encryption(self):
        """Test password encryption and decryption."""
        manager = SecurePasswordManager()
        original_password = "test_password_123"
        
        encrypted = manager.encrypt_password(original_password)
        decrypted = manager.decrypt_password(encrypted)
        
        assert decrypted == original_password
        assert encrypted != original_password.encode()
    
    def test_input_sanitization(self):
        """Test input sanitization."""
        sanitizer = InputSanitizer()
        
        # Test email sanitization
        dirty_email = "user@example.com<script>alert('xss')</script>"
        clean_email = sanitizer.sanitize_email(dirty_email)
        assert "<script>" not in clean_email
        assert "user@example.com" in clean_email
        
        # Test filename sanitization
        dirty_filename = "../../../etc/passwd"
        clean_filename = sanitizer.sanitize_filename(dirty_filename)
        assert ".." not in clean_filename
        assert "/" not in clean_filename
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        limiter = RateLimiter()
        user_id = "test_user"
        action = "test_action"
        
        # Should allow first few requests
        for i in range(5):
            assert limiter.check_rate_limit(user_id, action, limit=10, window=60)
        
        # Should block after limit
        for i in range(10):
            limiter.check_rate_limit(user_id, action, limit=5, window=60)
        
        # Should be blocked now
        assert not limiter.check_rate_limit(user_id, action, limit=5, window=60)


class TestErrorHandling:
    """Test error handling system."""
    
    def test_error_context_creation(self):
        """Test error context creation."""
        context = ErrorContext(
            user_id="test_user",
            operation="file_processing",
            file_name="test.docx"
        )
        
        assert context.user_id == "test_user"
        assert context.operation == "file_processing"
        assert context.file_name == "test.docx"
    
    def test_error_handler(self):
        """Test error handler functionality."""
        handler = ErrorHandler()
        context = ErrorContext(operation="test_operation")
        
        try:
            raise ValueError("Test error")
        except Exception as e:
            structured_error = handler.handle_error(
                e, context, show_to_user=False, severity=ErrorSeverity.LOW
            )
            
            assert structured_error.error_type == "ValueError"
            assert structured_error.message == "Test error"
            assert structured_error.severity == ErrorSeverity.LOW
            assert structured_error.error_id is not None


class TestMemoryOptimization:
    """Test memory optimization features."""
    
    def test_memory_monitor(self):
        """Test memory monitoring."""
        monitor = MemoryMonitor(alert_threshold=90.0)
        stats = monitor.get_memory_stats()
        
        assert hasattr(stats, 'used_mb')
        assert hasattr(stats, 'available_mb')
        assert hasattr(stats, 'percent_used')
        assert hasattr(stats, 'timestamp')
    
    def test_memory_suggestions(self):
        """Test memory cleanup suggestions."""
        monitor = MemoryMonitor()
        
        # Mock high memory usage
        with patch.object(monitor, 'get_memory_stats') as mock_stats:
            mock_stats.return_value = Mock(percent_used=95.0)
            suggestions = monitor.suggest_cleanup()
            
            assert len(suggestions) > 0
            assert any("restart" in suggestion.lower() for suggestion in suggestions)
    
    def test_memory_optimizer(self):
        """Test memory optimizer functionality."""
        optimizer = MemoryOptimizer()
        
        # Test optimization report
        report = optimizer.get_optimization_report()
        assert 'memory_stats' in report
        assert 'suggestions' in report
        assert 'needs_cleanup' in report


class TestPerformance:
    """Performance tests."""
    
    def test_text_parsing_performance(self):
        """Test text parsing performance."""
        parser = TechStackParser()
        
        # Generate large test input
        large_input = ""
        for i in range(100):
            large_input += f"Tech{i}: • Point 1 • Point 2 • Point 3\n"
        
        start_time = time.time()
        points, stacks = parser.parse_tech_stacks(large_input)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 1.0, f"Parsing took too long: {processing_time:.2f}s"
        assert len(stacks) == 100
        assert len(points) == 300
    
    def test_file_validation_performance(self):
        """Test file validation performance."""
        validator = FileValidator()
        
        # Create multiple mock files
        files = []
        for i in range(50):
            files.append(Mock(
                name=f"file{i}.docx",
                size=1024 * i,
                getvalue=lambda: b"PK" + b"x" * 1000
            ))
        
        start_time = time.time()
        result = validator.validate_batch(files)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 2.0, f"Validation took too long: {processing_time:.2f}s"


class TestIntegration:
    """Integration tests."""
    
    def test_end_to_end_processing(self):
        """Test end-to-end document processing flow."""
        # This would test the complete flow from file upload to processing
        # Mock the various components and ensure they work together
        
        # 1. File validation
        validator = FileValidator()
        mock_file = Mock(name="test.docx", size=1024, getvalue=lambda: b"PK" + b"x" * 1000)
        validation_result = validator.validate_file(mock_file)
        assert validation_result['valid']
        
        # 2. Text parsing
        parser = TechStackParser()
        tech_input = "Python: • Built web apps • Used Django"
        points, stacks = parser.parse_tech_stacks(tech_input)
        assert len(points) > 0
        assert len(stacks) > 0
        
        # 3. Memory optimization would be called
        optimizer = MemoryOptimizer()
        report = optimizer.get_optimization_report()
        assert 'memory_stats' in report


# Fixtures for pytest
@pytest.fixture
def sample_docx_file():
    """Create a sample DOCX file for testing."""
    # Create a temporary file with DOCX-like content
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
        temp_file.write(b'PK\x03\x04')  # ZIP signature
        temp_file.write(b'[Content_Types].xml')  # DOCX indicator
        temp_file.write(b'word/document.xml')  # DOCX structure
        temp_file.write(b'x' * 1000)  # Padding
        temp_file.flush()
        yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit session state for testing."""
    with patch('streamlit.session_state', {}) as mock_state:
        yield mock_state


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
