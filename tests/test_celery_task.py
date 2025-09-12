#!/usr/bin/env python3
"""
Test script to diagnose Celery task signature issues.
"""

import sys
import os
import base64
from io import BytesIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_task_signature():
    """Test the task signature directly."""
    print("Testing Celery task signature...")
    
    try:
        # Import the task
        from tasks import process_resume_task
        print(f"✓ Task imported successfully")
        print(f"Task function: {process_resume_task}")
        
        # Check if it's bound (has 'self')
        import inspect
        sig = inspect.signature(process_resume_task.run)  # Use .run for actual function
        print(f"Task signature: {sig}")
        print(f"Parameters: {list(sig.parameters.keys())}")
        
        # Create test data
        test_content = b"Test resume content"
        test_data = {
            'file_content_b64': base64.b64encode(test_content).decode('utf-8'),
            'filename': 'test_resume.docx',
            'text': 'Python Flask Django',
            'recipient_email': 'test@example.com',
            'manual_text': ''
        }
        
        print(f"✓ Test data created")
        
        # Try to call the task function directly (not through Celery)
        print("Attempting direct task call...")
        
        # Create a mock task instance
        class MockTask:
            def update_state(self, state, meta=None):
                print(f"Mock update_state: {state} - {meta}")
        
        mock_task = MockTask()
        
        # For bound tasks, call the original function directly
        # The .run method expects only the task arguments, not 'self'
        result = process_resume_task.run(test_data)
        print(f"✓ Direct task call successful")
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_task_signature()
