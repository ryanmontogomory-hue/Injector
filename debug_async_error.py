#!/usr/bin/env python3
"""
Debug script to reproduce the exact async task submission error.
"""

import sys
import os
from io import BytesIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_async_submission():
    """Test the exact async submission scenario that's failing."""
    
    print("🔍 DEBUGGING ASYNC TASK SUBMISSION")
    print("=" * 50)
    
    try:
        from core.resume_processor import ResumeProcessor
        
        # Create test data exactly like Streamlit would
        processor = ResumeProcessor()
        
        # Create dummy file data (similar to what Streamlit app creates)
        dummy_content = b"Test resume content"
        file_data = {
            'filename': 'test_resume.docx',
            'file': BytesIO(dummy_content),
            'text': 'Python Django Flask',
            'recipient_email': 'test@example.com',
            'manual_text': ''
        }
        
        print("📋 Test data prepared")
        print(f"   Filename: {file_data['filename']}")
        print(f"   Text: {file_data['text']}")
        print(f"   File type: {type(file_data['file'])}")
        
        # Try the async submission (this is where it fails)
        print("\n🚀 Attempting async task submission...")
        
        async_result = processor.process_single_resume_async(file_data)
        
        print("✅ SUCCESS!")
        print(f"   Task ID: {async_result.id}")
        print(f"   Task state: {async_result.state}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        
        # Print full traceback for debugging
        import traceback
        print("\n🔍 Full traceback:")
        traceback.print_exc()
        
        return False

def check_current_state():
    """Check the current state of imports and modules."""
    print("\n📊 CURRENT STATE CHECK")
    print("=" * 30)
    
    # Check if files exist
    print(f"tasks.py exists: {os.path.exists('tasks.py')}")
    print(f"celeryconfig.py exists: {os.path.exists('celeryconfig.py')}")
    print(f"core/resume_processor.py exists: {os.path.exists('core/resume_processor.py')}")
    
    # Check celery app
    try:
        from celeryconfig import celery_app
        print(f"✅ Celery app imported successfully")
        
        # Check registered tasks
        registered_tasks = list(celery_app.tasks.keys())
        print(f"📋 Registered tasks ({len(registered_tasks)}):")
        for task in registered_tasks:
            if 'process_resume_task' in task:
                print(f"   ✅ {task}")
            elif not task.startswith('celery.'):
                print(f"   📋 {task}")
        
        # Check specific task
        task = celery_app.tasks.get('tasks.process_resume_task')
        if task:
            print(f"✅ process_resume_task found: {task}")
        else:
            print(f"❌ process_resume_task NOT found")
            
    except Exception as e:
        print(f"❌ Celery app import failed: {e}")

if __name__ == "__main__":
    check_current_state()
    success = test_async_submission()
    
    print("\n" + "="*50)
    if success:
        print("🎉 Async task submission works!")
    else:
        print("❌ Async task submission failed!")
        print("\n💡 Troubleshooting suggestions:")
        print("   1. Make sure Celery worker is running")
        print("   2. Check Redis server is running")
        print("   3. Verify tasks.py is properly configured")
        print("   4. Try restarting the Streamlit app")
    print("="*50)
