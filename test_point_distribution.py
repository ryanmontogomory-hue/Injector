import os
from docx import Document
from document_processor import PointDistributor, DocumentProcessor

# Test the point distribution functionality
def test_point_distribution():
    print("Testing point distribution...")
    
    # Create test tech stacks
    tech_stacks = {
        'React': ['Built responsive UI', 'Used hooks', 'Created components'],
        'MongoDB': ['Created database schema', 'Optimized queries'],
        'Node.js': ['Built REST API', 'Used JWT']
    }
    
    # Test with different numbers of projects
    for num_projects in [1, 2, 3]:
        print(f"\nTesting with {num_projects} projects:")
        distributor = PointDistributor()
        result = distributor._calculate_round_robin_distribution(tech_stacks, num_projects)
        
        # Print the distribution
        for i, proj in enumerate(result):
            print(f"Project {i+1}:")
            for tech, points in proj.items():
                print(f"  {tech}: {points}")
        
        # Verify no duplicates within each project
        for i, proj in enumerate(result):
            all_points = []
            for tech, points in proj.items():
                all_points.extend(points)
            
            # Check for duplicates
            seen = set()
            duplicates = []
            for point in all_points:
                if point in seen:
                    duplicates.append(point)
                seen.add(point)
            
            if duplicates:
                print(f"ERROR: Project {i+1} has duplicate points: {duplicates}")
            else:
                print(f"Project {i+1} has no duplicates [OK]")

# Run the test
if __name__ == "__main__":
    test_point_distribution()