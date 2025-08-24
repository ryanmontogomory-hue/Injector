from document_processor import PointDistributor

# Create a test instance
distributor = PointDistributor()

# Create sample tech stacks with points
tech_stacks = {
    'Python': ['Django', 'Flask', 'FastAPI'],
    'JavaScript': ['React', 'Vue', 'Angular']
}

# Calculate distribution for 3 projects
result = distributor._calculate_round_robin_distribution(tech_stacks, 3)

# Print the distribution
print('Distribution:')
for i, proj in enumerate(result):
    print(f'Project {i+1}:', proj)

# Verify no duplicates in any project
for i, proj in enumerate(result):
    all_points = []
    for tech, points in proj.items():
        all_points.extend(points)
    
    # Check for duplicates
    if len(all_points) != len(set(all_points)):
        print(f'ERROR: Project {i+1} has duplicate points!')
    else:
        print(f'Project {i+1} has no duplicates. Points: {all_points}')