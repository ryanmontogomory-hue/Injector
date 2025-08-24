import os
from docx import Document
from document_processor import PointDistributor, DocumentProcessor

# Test with real-world tech stacks similar to what we see in the images
def test_resume_points():
    print("Testing with real-world resume data...")
    
    # Create tech stacks similar to what we see in the images
    tech_stacks = {
        'React': ['Built responsive UI with React.js and Bootstrap', 'Used hooks for state management'],
        'MongoDB': ['Created database schema', 'Optimized queries with indexes and aggregation pipelines'],
        'Node.js': ['Built REST API', 'Used JWT for secure authentication'],
        'AWS': ['Implemented serverless model using Lambda', 'Configured CloudFront for CDN'],
        'Docker': ['Containerized applications using Docker', 'Set up CI/CD pipelines']
    }
    
    # Test with 2 projects (similar to Boeing and Cardinal Health)
    print("\nTesting with 2 projects (like Boeing and Cardinal Health):")
    distributor = PointDistributor()
    result = distributor._calculate_round_robin_distribution(tech_stacks, 2)
    
    # Print the distribution
    for i, proj in enumerate(result):
        print(f"Project {i+1}:")
        for tech, points in proj.items():
            print(f"  {tech}: {points}")
    
    # Verify all points are distributed
    all_original_points = []
    for tech, points in tech_stacks.items():
        all_original_points.extend(points)
    
    all_distributed_points = []
    for proj in result:
        for tech, points in proj.items():
            all_distributed_points.extend(points)
    
    # Check if all original points are in the distributed points
    missing_points = [p for p in all_original_points if p not in all_distributed_points]
    if missing_points:
        print(f"ERROR: Some points are missing from distribution: {missing_points}")
    else:
        print("All points are distributed ✓")
    
    # Check for duplicates across projects
    seen_points = {}
    for i, proj in enumerate(result):
        for tech, points in proj.items():
            for point in points:
                if point in seen_points:
                    print(f"WARNING: Point '{point}' appears in both Project {seen_points[point]+1} and Project {i+1}")
                else:
                    seen_points[point] = i

# Run the test
if __name__ == "__main__":
    test_resume_points()