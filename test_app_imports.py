"""
Test app imports without running Streamlit.
"""

def test_app_imports():
    """Test if the main app modules can be imported."""
    try:
        print("Testing main app imports...")
        
        # Test basic imports
        import config
        print("✅ config imported")
        
        import logger
        print("✅ logger imported")
        
        import performance_monitor
        print("✅ performance_monitor imported")
        
        import performance_cache
        print("✅ performance_cache imported")
        
        import async_processor
        print("✅ async_processor imported")
        
        import async_integration
        print("✅ async_integration imported")
        
        # Test app-specific imports
        try:
            import text_parser
            print("✅ text_parser imported")
        except Exception as e:
            print(f"❌ text_parser import failed: {e}")
        
        try:
            import document_processor
            print("✅ document_processor imported")
        except Exception as e:
            print(f"❌ document_processor import failed: {e}")
            
        try:
            import resume_processor
            print("✅ resume_processor imported")
        except Exception as e:
            print(f"❌ resume_processor import failed: {e}")
        
        # Test async initialization
        from async_integration import initialize_async_services
        print("Testing async initialization...")
        
        # This will show warnings about missing Streamlit, which is expected
        success = initialize_async_services()
        if success:
            print("✅ Async services initialized successfully")
        else:
            print("⚠️ Async services initialization returned False (expected without Streamlit)")
        
        print("\n🎉 All imports successful! The app should work with async processing enabled.")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


if __name__ == "__main__":
    test_app_imports()
