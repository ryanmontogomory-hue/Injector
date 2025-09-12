"""
Test the emergency bullet consistency patch
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Apply the patch first
from bullet_consistency_patch import apply_emergency_patch
apply_emergency_patch()

# Now test the patched components
from core.document_processor import DocumentProcessor
from docx import Document

def test_patch():
    print("=== TESTING EMERGENCY BULLET CONSISTENCY PATCH ===")
    
    test_file = r"C:\Users\HP\Downloads\Resume Format 1.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Test the patched DocumentProcessor
        print("1. Testing patched DocumentProcessor...")
        processor = DocumentProcessor()
        
        doc = Document(test_file)
        detected_marker = processor._detect_document_bullet_marker(doc)
        print(f"✅ Detected marker: '{detected_marker}'")
        
        # Test the patched BulletFormatter
        print("2. Testing patched BulletFormatter...")
        marker = processor.formatter.get_document_bullet_marker(doc)
        print(f"✅ Formatter detected marker: '{marker}'")
        
        # Test full document processing
        print("3. Testing full document processing with patch...")
        
        with open(test_file, 'rb') as f:
            file_content = f.read()
        
        file_data = {
            'file_content': file_content,
            'filename': 'test_resume.docx',
            'tech_stacks': {
                'Test Tech': [
                    'Test bullet point 1',
                    'Test bullet point 2'
                ]
            }
        }
        
        result = processor.process_document(file_data)
        
        if result.get('success'):
            print("✅ Document processing with patch succeeded!")
            print(f"   - Points added: {result.get('points_added', 0)}")
            return True
        else:
            print(f"❌ Document processing failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Patch test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_patch()
    if success:
        print("🎉 PATCH TEST PASSED! Emergency patch is working correctly.")
    else:
        print("❌ PATCH TEST FAILED! There may be an issue with the patch.")
    exit(0 if success else 1)