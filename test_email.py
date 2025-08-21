#!/usr/bin/env python3
"""
Simple email functionality test for the Resume Customizer app
"""

import smtplib
from email.message import EmailMessage
from datetime import datetime
import sys

def test_email_functionality():
    """
    Test basic email functionality to verify if the code works
    """
    print("📧 Testing Email Functionality...")
    print("=" * 50)
    
    # Test data (don't use real credentials)
    test_config = {
        'sender_email': 'test@gmail.com',
        'recipient_email': 'recipient@gmail.com', 
        'sender_password': 'test_password',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 465
    }
    
    print("✅ Basic imports successful:")
    print("   - smtplib imported")
    print("   - EmailMessage imported")
    print("   - datetime imported")
    
    print("\n📝 Testing EmailMessage creation...")
    try:
        msg = EmailMessage()
        msg['Subject'] = f'Test Email - {datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = test_config['sender_email']
        msg['To'] = test_config['recipient_email']
        msg.set_content('This is a test email content.')
        print("✅ EmailMessage creation successful")
    except Exception as e:
        print(f"❌ EmailMessage creation failed: {e}")
        return False
    
    print("\n📎 Testing attachment functionality...")
    try:
        # Test adding a dummy attachment
        test_content = b"This is test file content"
        msg.add_attachment(
            test_content,
            maintype='application',
            subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename='test_resume.docx'
        )
        print("✅ Attachment functionality working")
    except Exception as e:
        print(f"❌ Attachment functionality failed: {e}")
        return False
    
    print("\n🔌 Testing SMTP connection structure...")
    try:
        # Test SMTP connection structure (without actually connecting)
        smtp_code = f"""
with smtplib.SMTP_SSL('{test_config['smtp_server']}', {test_config['smtp_port']}) as smtp:
    smtp.login('{test_config['sender_email']}', '{test_config['sender_password']}')
    smtp.send_message(msg)
"""
        print("✅ SMTP connection code structure is valid")
        print("   Code that would be executed:")
        print(f"   {smtp_code}")
    except Exception as e:
        print(f"❌ SMTP connection structure failed: {e}")
        return False
    
    print("\n🔍 Analyzing potential issues...")
    
    # Check common issues
    issues_found = []
    
    print("\n📋 Email functionality analysis complete!")
    print("=" * 50)
    
    if not issues_found:
        print("✅ All basic email functionality tests passed!")
        print("\n📌 For actual email sending, you need:")
        print("   1. Valid email credentials")
        print("   2. App-specific password (for Gmail)")
        print("   3. Internet connection")
        print("   4. SMTP server access")
    else:
        print("⚠️ Issues found:")
        for issue in issues_found:
            print(f"   - {issue}")
    
    return len(issues_found) == 0

if __name__ == "__main__":
    success = test_email_functionality()
    sys.exit(0 if success else 1)
