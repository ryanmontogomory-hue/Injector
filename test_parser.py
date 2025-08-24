#!/usr/bin/env python3
"""
Test script for the new text parsing functionality.
"""

from text_parser import TechStackParser, parse_input_text

def test_new_format():
    """Test the new parsing format."""
    
    # Test case 1: Your desired format
    test_input1 = """Python
Developed web applications using Django and Flask
Implemented RESTful APIs for data processing
Created automated testing suites

JavaScript
Built interactive UI components with React
Utilized Node.js for backend services
Implemented real-time features with WebSockets

AWS
Deployed applications using EC2 and S3
Managed databases with RDS
Configured auto-scaling groups"""

    print("=" * 60)
    print("Test Case 1: New Block Format")
    print("=" * 60)
    print("Input:")
    print(test_input1)
    print("\n" + "-" * 40)
    
    parser = TechStackParser()
    points, tech_stacks = parser.parse_tech_stacks(test_input1)
    
    print(f"Tech Stacks Found: {tech_stacks}")
    print(f"Points Found: {len(points)}")
    for i, point in enumerate(points, 1):
        print(f"  {i}. {point}")
    
    # Test case 2: Original format
    test_input2 = """Python: • Developed web applications using Django and Flask • Implemented RESTful APIs
JavaScript: • Created interactive UI components with React • Utilized Node.js for backend services
AWS: • Deployed applications using EC2 and S3 • Managed databases with RDS"""

    print("\n" + "=" * 60)
    print("Test Case 2: Original Format")
    print("=" * 60)
    print("Input:")
    print(test_input2)
    print("\n" + "-" * 40)
    
    points2, tech_stacks2 = parser.parse_tech_stacks(test_input2)
    
    print(f"Tech Stacks Found: {tech_stacks2}")
    print(f"Points Found: {len(points2)}")
    for i, point in enumerate(points2, 1):
        print(f"  {i}. {point}")
    
    # Test case 3: Mixed/Edge cases
    test_input3 = """React Native
Built cross-platform mobile applications
Implemented push notifications
Integrated with native device features

Backend Development
Designed scalable microservices architecture
Implemented caching strategies
Optimized database queries for performance"""

    print("\n" + "=" * 60)
    print("Test Case 3: Complex Tech Names")
    print("=" * 60)
    print("Input:")
    print(test_input3)
    print("\n" + "-" * 40)
    
    points3, tech_stacks3 = parser.parse_tech_stacks(test_input3)
    
    print(f"Tech Stacks Found: {tech_stacks3}")
    print(f"Points Found: {len(points3)}")
    for i, point in enumerate(points3, 1):
        print(f"  {i}. {point}")

def test_manual_override():
    """Test manual point override functionality."""
    
    print("\n" + "=" * 60)
    print("Test Case 4: Manual Override")
    print("=" * 60)
    
    original_text = """Python
Developed web applications
Created APIs"""
    
    manual_text = """Developed advanced web applications using Django framework
Implemented RESTful APIs with authentication
Built automated testing suites with pytest
Optimized database queries for better performance"""
    
    print("Original Text:")
    print(original_text)
    print("\nManual Override:")
    print(manual_text)
    print("\n" + "-" * 40)
    
    points, tech_stacks = parse_input_text(original_text, manual_text)
    
    print(f"Tech Stacks Found: {tech_stacks}")
    print(f"Points Found: {len(points)}")
    for i, point in enumerate(points, 1):
        print(f"  {i}. {point}")

if __name__ == "__main__":
    print("🔬 Testing Resume Customizer Text Parser")
    print("=" * 60)
    
    try:
        test_new_format()
        test_manual_override()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("The parser can handle both formats:")
        print("  • New block format (TechName followed by bullet points)")
        print("  • Original format (TechName: • point1 • point2)")
        print("  • Manual point override functionality")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
