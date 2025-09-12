#!/usr/bin/env python3
"""
Comprehensive test script for the new restricted text parser.
Tests all 3 supported formats and various invalid format combinations.
"""

import sys
import os

# Add the current directory to Python path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.restricted_text_parser import parse_input_text_restricted, RestrictedFormatError


def test_format_1():
    """Test Format 1: Tech Stack (no colon) + Tabbed Bullet Points"""
    print("🔍 Testing Format 1: Tech Stack (no colon) + Tabbed Bullet Points")
    
    # Valid Format 1 - with actual tabs
    text1 = """Java
•	Designed and developed scalable enterprise-grade applications
•	Refactored legacy Java modules into modern code
•	Built backend services with Java and JDBC"""
    
    try:
        points, stacks = parse_input_text_restricted(text1)
        print(f"  ✅ Format 1 (tabs): {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
        print(f"    Sample point: {points[0][:50]}...")
    except Exception as e:
        print(f"  ❌ Format 1 (tabs) failed: {e}")
    
    # Valid Format 1 - with multiple spaces (flexible)
    text2 = """RESTful APIs
•    Designed and implemented secure RESTful APIs
•    Improved system integration with REST endpoints
•    Optimized API performance through caching"""
    
    try:
        points, stacks = parse_input_text_restricted(text2)
        print(f"  ✅ Format 1 (spaces): {len(points)} points, {len(stacks)} stacks")
    except Exception as e:
        print(f"  ❌ Format 1 (spaces) failed: {e}")
    print()


def test_format_2():
    """Test Format 2: Tech Stack with colon + Tabbed Bullet Points"""
    print("🔍 Testing Format 2: Tech Stack with colon + Tabbed Bullet Points")
    
    text = """Spring Framework:
•	Developed microservices-based applications
•	Implemented security best practices
•	Built batch jobs and schedulers"""
    
    try:
        points, stacks = parse_input_text_restricted(text)
        print(f"  ✅ Format 2: {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
        print(f"    Sample point: {points[0][:50]}...")
    except Exception as e:
        print(f"  ❌ Format 2 failed: {e}")
    print()


def test_format_3():
    """Test Format 3: Tech Stack (no colon) + Regular Bullet Points"""
    print("🔍 Testing Format 3: Tech Stack (no colon) + Regular Bullet Points")
    
    text = """Docker
• Containerized Java applications using Docker
• Integrated microservices with Kubernetes
• Built optimized Docker images"""
    
    try:
        points, stacks = parse_input_text_restricted(text)
        print(f"  ✅ Format 3: {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
        print(f"    Sample point: {points[0][:50]}...")
    except Exception as e:
        print(f"  ❌ Format 3 failed: {e}")
    print()


def test_mixed_formats():
    """Test mixing different formats in same input"""
    print("🔍 Testing Mixed Formats (should be allowed)")
    
    text = """Java
•	Developed scalable applications using Java
•	Built backend services with JDBC

Python:
•    Created data processing pipelines
•    Implemented machine learning models

AWS
• Deployed containerized applications
• Managed cloud infrastructure"""
    
    try:
        points, stacks = parse_input_text_restricted(text)
        print(f"  ✅ Mixed formats: {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
    except Exception as e:
        print(f"  ❌ Mixed formats failed: {e}")
    print()


def test_invalid_formats():
    """Test various invalid formats that should be rejected"""
    print("🔍 Testing Invalid Formats (should be rejected)")
    
    # Invalid: Single line format (old style)
    invalid1 = "Java: • Point 1 • Point 2 • Point 3"
    test_invalid_format("Single line format", invalid1)
    
    # Invalid: Mixed bullet types in same block
    invalid2 = """Java
• Regular bullet
- Dash bullet
* Star bullet"""
    test_invalid_format("Mixed bullet types", invalid2)
    
    # Invalid: No bullet points
    invalid3 = """Java
Just regular text without bullets
Another line without bullets"""
    test_invalid_format("No bullet points", invalid3)
    
    # Invalid: Bullet symbol in tech name
    invalid4 = """• Java Framework
•	Point 1
•	Point 2"""
    test_invalid_format("Bullet in tech name", invalid4)
    
    # Invalid: Mixed tabbed and regular bullets in same block
    invalid5 = """Java
•	Tabbed bullet point
• Regular bullet point"""
    test_invalid_format("Mixed tab/regular bullets", invalid5)
    
    print()


def test_invalid_format(test_name: str, text: str):
    """Helper to test a specific invalid format"""
    try:
        points, stacks = parse_input_text_restricted(text)
        print(f"  ❌ {test_name}: Should have failed but got {len(points)} points")
    except RestrictedFormatError as e:
        print(f"  ✅ {test_name}: Correctly rejected")
        # Show first line of error message
        error_lines = str(e).split('\n')
        print(f"    Error: {error_lines[0]}")
    except Exception as e:
        print(f"  ⚠️  {test_name}: Unexpected error: {e}")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("🔍 Testing Edge Cases")
    
    # Empty input
    try:
        points, stacks = parse_input_text_restricted("")
        print(f"  ✅ Empty input: {len(points)} points, {len(stacks)} stacks")
    except Exception as e:
        print(f"  ❌ Empty input failed: {e}")
    
    # Single tech stack, single point
    text = """Java
•	Single point"""
    try:
        points, stacks = parse_input_text_restricted(text)
        print(f"  ✅ Single point: {len(points)} points, {len(stacks)} stacks")
    except Exception as e:
        print(f"  ❌ Single point failed: {e}")
    
    # Extra whitespace (should be flexible)
    text_with_spaces = """  Java  
•	  Point with extra spaces  
•	  Another point  """
    try:
        points, stacks = parse_input_text_restricted(text_with_spaces)
        print(f"  ✅ Extra whitespace: {len(points)} points, {len(stacks)} stacks")
    except Exception as e:
        print(f"  ❌ Extra whitespace failed: {e}")
    
    print()


def test_your_original_examples():
    """Test the exact examples you provided"""
    print("🔍 Testing Your Original Examples")
    
    # Your Format 1 example
    format1_example = """Java
•	Designed and developed scalable enterprise-grade applications using Java 8–17, J2EE, and multithreading concepts, ensuring high performance and reliability across complex distributed systems.
•	Refactored legacy Java modules into modern object-oriented, modular code, leveraging Java Streams, Collections, and Concurrency APIs, improving maintainability and runtime efficiency.
•	Built backend services with Java, JDBC, and SQL Server, ensuring robust database connectivity, optimized query execution, and transaction management for critical financial workflows."""
    
    try:
        points, stacks = parse_input_text_restricted(format1_example)
        print(f"  ✅ Your Format 1: {len(points)} points, {len(stacks)} stacks")
    except Exception as e:
        print(f"  ❌ Your Format 1 failed: {e}")
    
    # Your Format 2 example
    format2_example = """Java:
•	Designed and developed scalable enterprise-grade applications using Java 8–17, J2EE, and multithreading concepts, ensuring high performance and reliability across complex distributed systems.
•	Refactored legacy Java modules into modern object-oriented, modular code, leveraging Java Streams, Collections, and Concurrency APIs, improving maintainability and runtime efficiency.
•	Built backend services with Java, JDBC, and SQL Server, ensuring robust database connectivity, optimized query execution, and transaction management for critical financial workflows.

RESTful APIs:
•	Designed and implemented secure, versioned RESTful APIs using Java, Spring Boot, and JSON, enabling smooth data exchange between microservices and external client applications.
•	Improved system integration by building REST endpoints with Spring MVC + Spring Security, handling authentication, authorization, and validation across multiple domains.
•	Optimized REST API performance through caching (Redis), pagination, and query optimizations, ensuring low-latency responses for high-traffic enterprise applications."""
    
    try:
        points, stacks = parse_input_text_restricted(format2_example)
        print(f"  ✅ Your Format 2: {len(points)} points, {len(stacks)} stacks")
        print(f"    Tech stacks: {stacks}")
    except Exception as e:
        print(f"  ❌ Your Format 2 failed: {e}")
    
    # Your Format 3 example
    format3_example = """Java
• Designed and developed scalable enterprise-grade applications using Java 8–17, J2EE, and multithreading concepts, ensuring high performance and reliability across complex distributed systems.
• Refactored legacy Java modules into modern object-oriented, modular code, leveraging Java Streams, Collections, and Concurrency APIs, improving maintainability and runtime efficiency.
• Built backend services with Java, JDBC, and SQL Server, ensuring robust database connectivity, optimized query execution, and transaction management for critical financial workflows."""
    
    try:
        points, stacks = parse_input_text_restricted(format3_example)
        print(f"  ✅ Your Format 3: {len(points)} points, {len(stacks)} stacks")
    except Exception as e:
        print(f"  ❌ Your Format 3 failed: {e}")
    
    print()


def main():
    """Run all tests"""
    print("🧪 RESTRICTED PARSER COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()
    
    test_format_1()
    test_format_2() 
    test_format_3()
    test_mixed_formats()
    test_invalid_formats()
    test_edge_cases()
    test_your_original_examples()
    
    print("🏁 Test suite completed!")
    print()
    print("📝 Summary:")
    print("  - Valid formats should pass ✅")
    print("  - Invalid formats should be rejected with detailed error messages ❌")
    print("  - Mixed formats should be allowed ✅")
    print("  - Edge cases should be handled gracefully ✅")


if __name__ == "__main__":
    main()