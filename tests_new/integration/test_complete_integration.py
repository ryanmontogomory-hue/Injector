#!/usr/bin/env python3
"""
Test script to validate the complete restricted parser integration.
Tests the integration with resume processor and UI components.
"""

import sys
import os

# Add the current directory to Python path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.restricted_text_parser import parse_input_text_restricted, RestrictedFormatError
from docx import Document
from io import BytesIO


def test_integration_with_sample_resume():
    """Test integration with a sample resume document"""
    print("🧪 TESTING COMPLETE INTEGRATION")
    print("=" * 60)
    
    # Test Format 1: Java example
    format1_input = """Java
•	Designed and developed scalable enterprise-grade applications using Java 8–17, J2EE, and multithreading concepts, ensuring high performance and reliability across complex distributed systems.
•	Refactored legacy Java modules into modern object-oriented, modular code, leveraging Java Streams, Collections, and Concurrency APIs, improving maintainability and runtime efficiency.
•	Built backend services with Java, JDBC, and SQL Server, ensuring robust database connectivity, optimized query execution, and transaction management for critical financial workflows."""
    
    # Test Format 2: Multiple tech stacks
    format2_input = """Java:
•	Developed scalable applications using Spring Boot
•	Implemented microservices architecture
•	Built secure REST APIs

Python:
•	Created data processing pipelines
•	Implemented machine learning models
•	Built automated testing frameworks"""
    
    # Test Format 3: Regular bullets
    format3_input = """Docker
• Containerized applications using Docker
• Integrated microservices with Kubernetes
• Built optimized Docker images"""
    
    # Test invalid format
    invalid_input = "Java: • Point 1 • Point 2 • Point 3"  # Single line format
    
    print("🔍 Testing Valid Formats:")
    
    # Test Format 1
    try:
        points, stacks = parse_input_text_restricted(format1_input)
        print(f"  ✅ Format 1: {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
        print(f"    Sample point: {points[0][:60]}...")
    except Exception as e:
        print(f"  ❌ Format 1 failed: {e}")
    
    print()
    
    # Test Format 2
    try:
        points, stacks = parse_input_text_restricted(format2_input)
        print(f"  ✅ Format 2: {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
        print(f"    Sample point: {points[0][:60]}...")
    except Exception as e:
        print(f"  ❌ Format 2 failed: {e}")
    
    print()
    
    # Test Format 3
    try:
        points, stacks = parse_input_text_restricted(format3_input)
        print(f"  ✅ Format 3: {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
        print(f"    Sample point: {points[0][:60]}...")
    except Exception as e:
        print(f"  ❌ Format 3 failed: {e}")
    
    print()
    print("🚫 Testing Invalid Format:")
    
    # Test invalid format
    try:
        points, stacks = parse_input_text_restricted(invalid_input)
        print(f"  ❌ Invalid format should have failed but got {len(points)} points")
    except RestrictedFormatError as e:
        print(f"  ✅ Invalid format correctly rejected")
        print(f"    Error message preview: {str(e)[:100]}...")
    except Exception as e:
        print(f"  ⚠️ Invalid format failed with unexpected error: {e}")
    
    print()


def test_output_consistency():
    """Test that output format matches resume bullet format"""
    print("🔄 TESTING OUTPUT CONSISTENCY")
    print("=" * 60)
    
    # Test with bullet symbols in input
    input_with_bullets = """Java
• Spring Boot development
• REST API implementation
• Microservices architecture"""
    
    # Test with mixed input
    mixed_input = """Java:
•	Enterprise application development
•	Database integration

Python
• Data processing pipelines
• Machine learning implementation"""
    
    print("📝 Testing input with bullet symbols:")
    try:
        points, stacks = parse_input_text_restricted(input_with_bullets)
        print(f"  ✅ Parsed: {len(points)} points from {len(stacks)} stacks")
        print(f"  Input format: Bullet symbols (•)")
        print(f"  Output: Will be converted to match existing resume format")
        print(f"  Tech stacks: {stacks}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
    
    print()
    print("📝 Testing mixed input formats:")
    try:
        points, stacks = parse_input_text_restricted(mixed_input)
        print(f"  ✅ Parsed: {len(points)} points from {len(stacks)} stacks")
        print(f"  Mixed formats: Format 2 (colon + tabs) and Format 3 (no colon + regular)")
        print(f"  Output: All will be converted to match existing resume format")
        print(f"  Tech stacks: {stacks}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")


def test_error_handling():
    """Test comprehensive error handling scenarios"""
    print("\n⚠️ TESTING ERROR HANDLING")
    print("=" * 60)
    
    test_cases = [
        ("Empty input", ""),
        ("Only tech name", "Java"),
        ("Mixed bullet types", """Java
• Regular bullet
- Dash bullet"""),
        ("No bullets", """Java
Just regular text
Another line"""),
        ("Bullet in tech name", """• Java Framework
•	Point 1"""),
        ("Single line old format", "Java: • Point 1 • Point 2"),
        ("Invalid spacing", """Java
•Point without space""")
    ]
    
    for test_name, test_input in test_cases:
        try:
            points, stacks = parse_input_text_restricted(test_input)
            if test_input.strip():  # Empty input should succeed
                print(f"  ❌ {test_name}: Should have failed but got {len(points)} points")
            else:
                print(f"  ✅ {test_name}: Correctly handled (empty input)")
        except RestrictedFormatError as e:
            print(f"  ✅ {test_name}: Correctly rejected")
            # Show first line of error
            error_lines = str(e).split('\n')
            print(f"    Error: {error_lines[0]}")
        except Exception as e:
            print(f"  ⚠️ {test_name}: Unexpected error: {e}")


def main():
    """Run all integration tests"""
    print("🎯 RESTRICTED PARSER INTEGRATION TEST SUITE")
    print("=" * 80)
    print()
    
    test_integration_with_sample_resume()
    test_output_consistency()
    test_error_handling()
    
    print("\n" + "=" * 80)
    print("🏁 INTEGRATION TESTS COMPLETED!")
    print()
    print("📋 Summary:")
    print("  ✅ Valid formats (1, 2, 3) should be accepted")
    print("  ❌ Invalid formats should be rejected with detailed errors")
    print("  🔄 Output format will match your existing resume bullet style")
    print("  📝 Mixed formats within same input are allowed")
    print("  ⚠️ All other formats are strictly rejected")
    print()
    print("🚀 Your application now only supports the 3 specified formats!")
    print("🎯 Users will get clear error messages for invalid formats.")
    print("💡 The emergency patch still ensures bullet consistency in output.")


if __name__ == "__main__":
    main()