"""
Test script for Phase 1 security implementations.
Verifies that all security enhancements work correctly.
"""

import sys
import traceback
from typing import Dict, Any

def test_imports():
    """Test that all security modules can be imported."""
    print("🔍 Testing security module imports...")
    
    try:
        from security_enhancements import (
            SecurePasswordManager, 
            InputSanitizer, 
            RateLimiter,
            SessionSecurityManager
        )
        print("✅ Security enhancements imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import security enhancements: {e}")
        return False

def test_password_encryption():
    """Test password encryption/decryption."""
    print("\n🔍 Testing password encryption...")
    
    try:
        from security_enhancements import SecurePasswordManager
        
        manager = SecurePasswordManager()
        test_password = "test_password_123"
        
        # Encrypt
        encrypted = manager.encrypt_password(test_password)
        print(f"✅ Password encrypted (length: {len(encrypted)} bytes)")
        
        # Decrypt
        decrypted = manager.decrypt_password(encrypted)
        print(f"✅ Password decrypted successfully")
        
        # Verify
        if decrypted == test_password:
            print("✅ Password encryption/decryption working correctly")
            return True
        else:
            print("❌ Password mismatch after encryption/decryption")
            return False
            
    except Exception as e:
        print(f"❌ Password encryption test failed: {e}")
        traceback.print_exc()
        return False

def test_input_sanitization():
    """Test input sanitization."""
    print("\n🔍 Testing input sanitization...")
    
    try:
        from security_enhancements import InputSanitizer
        
        sanitizer = InputSanitizer()
        
        # Test email sanitization
        dirty_email = "user@example.com<script>alert('xss')</script>"
        clean_email = sanitizer.sanitize_email(dirty_email)
        
        if "<script>" not in clean_email and "user@example.com" in clean_email:
            print("✅ Email sanitization working correctly")
        else:
            print(f"❌ Email sanitization failed: {clean_email}")
            return False
        
        # Test filename sanitization
        dirty_filename = "../../../etc/passwd"
        clean_filename = sanitizer.sanitize_filename(dirty_filename)
        
        if ".." not in clean_filename and "/" not in clean_filename:
            print("✅ Filename sanitization working correctly")
        else:
            print(f"❌ Filename sanitization failed: {clean_filename}")
            return False
        
        # Test text sanitization
        dirty_text = "Normal text\x00\x01\x02with control characters"
        clean_text = sanitizer.sanitize_text_input(dirty_text)
        
        if "Normal text" in clean_text and "\x00" not in clean_text:
            print("✅ Text sanitization working correctly")
            return True
        else:
            print(f"❌ Text sanitization failed: {repr(clean_text)}")
            return False
            
    except Exception as e:
        print(f"❌ Input sanitization test failed: {e}")
        traceback.print_exc()
        return False

def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n🔍 Testing rate limiting...")
    
    try:
        from security_enhancements import RateLimiter
        
        limiter = RateLimiter()
        user_id = "test_user"
        action = "test_action"
        
        # Should allow first few requests
        success_count = 0
        for i in range(5):
            if limiter.check_rate_limit(user_id, action, limit=10, window=60):
                success_count += 1
        
        if success_count == 5:
            print("✅ Rate limiting allows valid requests")
        else:
            print(f"❌ Rate limiting blocked valid requests: {success_count}/5")
            return False
        
        # Exceed limit
        for i in range(10):
            limiter.check_rate_limit(user_id, action, limit=5, window=60)
        
        # Should be blocked now
        if not limiter.check_rate_limit(user_id, action, limit=5, window=60):
            print("✅ Rate limiting blocks excess requests")
            return True
        else:
            print("❌ Rate limiting failed to block excess requests")
            return False
            
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        traceback.print_exc()
        return False

def test_csrf_protection():
    """Test CSRF token generation and validation."""
    print("\n🔍 Testing CSRF protection...")
    
    try:
        from security_enhancements import SessionSecurityManager
        
        manager = SessionSecurityManager()
        
        # Generate token
        token1 = manager.generate_csrf_token()
        token2 = manager.generate_csrf_token()
        
        if len(token1) > 20 and token1 != token2:
            print("✅ CSRF token generation working correctly")
        else:
            print(f"❌ CSRF token generation failed: {token1}, {token2}")
            return False
        
        # Validate token
        if manager.validate_csrf_token(token1, token1):
            print("✅ CSRF token validation working correctly")
        else:
            print("❌ CSRF token validation failed for valid token")
            return False
        
        # Invalid token
        if not manager.validate_csrf_token("invalid_token", token1):
            print("✅ CSRF token validation rejects invalid tokens")
            return True
        else:
            print("❌ CSRF token validation accepted invalid token")
            return False
            
    except Exception as e:
        print(f"❌ CSRF protection test failed: {e}")
        traceback.print_exc()
        return False

def test_email_handler_integration():
    """Test email handler security integration."""
    print("\n🔍 Testing email handler security integration...")
    
    try:
        # Check if email handler imports security modules
        from email_handler import EmailSender, SMTPConnectionPool
        
        pool = SMTPConnectionPool()
        sender = EmailSender(pool)
        
        # Check if security components are initialized
        if hasattr(sender, 'password_manager') and hasattr(sender, 'sanitizer'):
            print("✅ Email handler has security components")
        else:
            print("❌ Email handler missing security components")
            return False
        
        # Test password decryption method
        if hasattr(sender, '_decrypt_password_if_needed'):
            test_password = "plain_password"
            result = sender._decrypt_password_if_needed(test_password)
            if result == test_password:
                print("✅ Email handler password handling working")
                return True
            else:
                print(f"❌ Email handler password handling failed: {result}")
                return False
        else:
            print("❌ Email handler missing password decryption method")
            return False
            
    except Exception as e:
        print(f"❌ Email handler integration test failed: {e}")
        traceback.print_exc()
        return False

def test_ui_components():
    """Test secure UI components."""
    print("\n🔍 Testing secure UI components...")
    
    try:
        from ui.secure_components import get_secure_ui_components
        
        secure_ui = get_secure_ui_components()
        
        # Check if components are initialized
        if (hasattr(secure_ui, 'password_manager') and 
            hasattr(secure_ui, 'sanitizer') and
            hasattr(secure_ui, 'rate_limiter') and
            hasattr(secure_ui, 'session_manager')):
            print("✅ Secure UI components initialized correctly")
            return True
        else:
            print("❌ Secure UI components missing attributes")
            return False
            
    except Exception as e:
        print(f"❌ Secure UI components test failed: {e}")
        traceback.print_exc()
        return False

def run_all_tests() -> Dict[str, bool]:
    """Run all security tests."""
    print("🚀 Starting Phase 1 Security Tests")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Password Encryption", test_password_encryption),
        ("Input Sanitization", test_input_sanitization),
        ("Rate Limiting", test_rate_limiting),
        ("CSRF Protection", test_csrf_protection),
        ("Email Handler Integration", test_email_handler_integration),
        ("UI Components", test_ui_components),
    ]
    
    results = {}
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
            failed += 1
    
    print("\n" + "=" * 50)
    print("🎯 Test Results Summary")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All Phase 1 security tests passed!")
        print("✅ Phase 1 implementation is ready for production")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please fix before proceeding to Phase 2.")
    
    return results

if __name__ == "__main__":
    # Change to the application directory
    import os
    app_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(app_dir)
    
    # Add current directory to Python path
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    results = run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if all(results.values()) else 1
    sys.exit(exit_code)
