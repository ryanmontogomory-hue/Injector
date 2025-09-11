#!/usr/bin/env python3
"""
Test script to verify Celery task with realistic data.
"""

import sys
import os
import base64
from io import BytesIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_realistic_task():
    """Test the task with realistic resume data."""
    print("Testing Celery task with realistic data...")
    
    try:
        from tasks import process_resume_task
        
        # Create more realistic test data
        realistic_resume_content = b"""
        Dear Hiring Manager,
        
        I am a software developer with experience in Python, Flask, Django, JavaScript, React, and Node.js.
        I have worked on various projects involving database design and API development.
        
        My technical skills include:
        - Python web frameworks (Flask, Django)
        - JavaScript and modern frameworks (React, Vue.js)
        - Database technologies (PostgreSQL, MongoDB)
        - Cloud platforms (AWS, Azure)
        
        I am passionate about creating scalable web applications and have experience with DevOps tools.
        
        Best regards,
        John Doe
        """
        
        test_data = {
            'file_content_b64': base64.b64encode(realistic_resume_content).decode('utf-8'),
            'filename': 'john_doe_resume.docx',
            'text': 'Python Django Flask JavaScript React Node.js PostgreSQL AWS cloud computing',
            'recipient_email': 'hiring@company.com',
            'manual_text': ''
        }
        
        print("✓ Realistic test data created")
        
        # Test the task
        print("Processing resume with realistic data...")
        result = process_resume_task.run(test_data)
        
        print("✓ Task completed successfully")
        print(f"Result: {result}")
        
        # Check if we got expected results
        if result.get('success'):
            print("🎉 Task processed successfully!")
            print(f"Points added: {result.get('points_added', 0)}")
            print(f"Tech stacks: {result.get('tech_stacks_used', [])}")
        else:
            print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_realistic_task()
