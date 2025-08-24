from document_processor import PointDistributor

# Test the point distribution functionality with debug output
def test_point_distribution_debug():
    print("Testing point distribution with debug output...")
    
    # Create test tech stacks
    tech_stacks = {
        'React': ['Built responsive UI', 'Used hooks', 'Created components'],
        'MongoDB': ['Created database schema', 'Optimized queries'],
        'Node.js': ['Built REST API', 'Used JWT']
    }
    
    # Create test projects
    projects = [
        {'title': 'Project 1', 'index': 0, 'responsibilities_start': 5, 'responsibilities_end': 10},
        {'title': 'Project 2', 'index': 1, 'responsibilities_start': 15, 'responsibilities_end': 20},
        {'title': 'Project 3', 'index': 2, 'responsibilities_start': 25, 'responsibilities_end': 30}
    ]
    
    print(f"Input tech stacks: {tech_stacks}")
    print(f"Input projects: {[p['title'] for p in projects]}")
    
    # Create distributor and distribute points
    distributor = PointDistributor()
    result = distributor.distribute_points_to_projects(projects, tech_stacks)
    
    print(f"\nDistribution result success: {result['success']}")
    if not result['success']:
        print(f"Error: {result['error']}")
        return
    
    print(f"Points added: {result['points_added']}")
    print(f"Projects used: {result['projects_used']}")
    
    print("\nDetailed distribution:")
    for project_title, project_info in result['distribution'].items():
        print(f"\n{project_title}:")
        print(f"  Project index: {project_info['project_index']}")
        print(f"  Insertion point: {project_info['insertion_point']}")
        print(f"  Responsibilities end: {project_info['responsibilities_end']}")
        print(f"  Total points: {project_info['total_points']}")
        print(f"  Mixed tech stacks: {project_info['mixed_tech_stacks']}")
        
        # Check for duplicates in this project
        all_points = []
        for tech, points in project_info['mixed_tech_stacks'].items():
            all_points.extend(points)
        
        seen = set()
        duplicates = []
        for point in all_points:
            if point in seen:
                duplicates.append(point)
            seen.add(point)
        
        if duplicates:
            print(f"  ERROR: Duplicate points: {duplicates}")
        else:
            print(f"  No duplicates found")

# Run the test
if __name__ == "__main__":
    test_point_distribution_debug()