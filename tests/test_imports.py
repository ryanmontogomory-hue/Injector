#!/usr/bin/env python3
"""
Test script to diagnose import issues with tasks.py module.
"""

import os
import sys
import traceback

def test_imports():
    """Test importing tasks module from different contexts."""
    
    print("🔍 IMPORT DIAGNOSTICS")
    print("=" * 50)
    
    # Show current environment
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path (first 5):")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}: {path}")
    
    print("\n📁 File system check:")
    print(f"tasks.py exists: {os.path.exists('tasks.py')}")
    print(f"celeryconfig.py exists: {os.path.exists('celeryconfig.py')}")
    print(f"core/resume_processor.py exists: {os.path.exists('core/resume_processor.py')}")
    
    print("\n🧪 Testing imports:")
    
    # Test 1: Direct import
    print("\n1. Testing direct import 'from tasks import process_resume_task'...")
    try:
        from tasks import process_resume_task
        print("   ✅ SUCCESS: Direct import works")
    except ImportError as e:
        print(f"   ❌ FAILED: {e}")
    
    # Test 2: Import with path manipulation
    print("\n2. Testing import with path manipulation...")
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from tasks import process_resume_task
        print("   ✅ SUCCESS: Path manipulation works")
    except ImportError as e:
        print(f"   ❌ FAILED: {e}")
    
    # Test 3: Import celeryconfig
    print("\n3. Testing celeryconfig import...")
    try:
    from config.celeryconfig import celery_app
        print("   ✅ SUCCESS: celeryconfig import works")
        print(f"   📋 Registered tasks: {list(celery_app.tasks.keys())}")
    except ImportError as e:
        print(f"   ❌ FAILED: {e}")
    
    # Test 4: Test the ResumeProcessor import
    print("\n4. Testing ResumeProcessor async method...")
    try:
        from core.resume_processor import ResumeProcessor
        processor = ResumeProcessor()
        # Create dummy file data
        from io import BytesIO
        dummy_data = {
            'filename': 'test.docx',
            'file': BytesIO(b'dummy'),
            'text': 'test',
            'recipient_email': 'test@example.com',
            'manual_text': ''
        }
        # This should fail at the import level if there's an issue
        try:
            result = processor.process_single_resume_async(dummy_data)
            print("   ✅ SUCCESS: ResumeProcessor async import works")
            print(f"   📝 Task ID: {result.id}")
        except RuntimeError as e:
            if "tasks module not found" in str(e):
                print(f"   ❌ IMPORT ISSUE: {e}")
            else:
                print(f"   ⚠️  RUNTIME ISSUE (import OK): {e}")
        except Exception as e:
            print(f"   ⚠️  OTHER ISSUE (import likely OK): {e}")
            
    except ImportError as e:
        print(f"   ❌ FAILED: {e}")
        traceback.print_exc()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_imports()
