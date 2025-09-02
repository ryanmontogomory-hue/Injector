"""
Requirements Management Module for Resume Customizer
Handles CRUD operations for job requirements
"""
import streamlit as st
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path
from datetime import datetime
from logger import get_logger

logger = get_logger()

class RequirementsManager:
    """Manages job requirements CRUD operations."""
    
    def __init__(self, storage_file: str = "requirements.json"):
        """Initialize RequirementsManager with storage file."""
        self.storage_file = storage_file
        self.requirements = self._load_requirements()
        
    def _get_storage_path(self) -> Path:
        """Get the full path to the requirements storage file."""
        return Path(__file__).parent.parent / self.storage_file
    
    def _load_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Load requirements from JSON file."""
        try:
            path = self._get_storage_path()
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading requirements: {e}")
        return {}
    
    def _save_requirements(self):
        """Save requirements to JSON file."""
        try:
            path = self._get_storage_path()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.requirements, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving requirements: {e}")
            st.error("Failed to save requirements. Please check logs for details.")
    
    def create_requirement(self, requirement_data: Dict[str, Any]) -> str:
        """Create a new requirement."""
        requirement_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        requirement_data.update({
            'id': requirement_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        self.requirements[requirement_id] = requirement_data
        self._save_requirements()
        return requirement_id
    
    def get_requirement(self, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Get a requirement by ID."""
        return self.requirements.get(requirement_id)
    
    def update_requirement(self, requirement_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing requirement."""
        if requirement_id not in self.requirements:
            return False
        
        update_data['updated_at'] = datetime.now().isoformat()
        self.requirements[requirement_id].update(update_data)
        self._save_requirements()
        return True
    
    def delete_requirement(self, requirement_id: str) -> bool:
        """Delete a requirement."""
        if requirement_id in self.requirements:
            del self.requirements[requirement_id]
            self._save_requirements()
            return True
        return False
    
    def list_requirements(self) -> List[Dict[str, Any]]:
        """List all requirements."""
        return list(self.requirements.values())


def render_requirement_form(requirement_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Render the requirement form and return form data."""
    is_edit = requirement_data is not None
    
    # Initialize form data with defaults or existing values
    form_data = {
        'job_title': '',
        'job_description': '',
        'required_skills': '',
        'experience_level': 'Mid-Level',
        'location': '',
        'job_type': 'Full-time',
        'company': '',
        'salary_range': ''
    }
    
    if is_edit:
        form_data.update(requirement_data)
    
    # Create form
    with st.form(key='requirement_form'):
        st.subheader("📝 " + ("Edit" if is_edit else "Create New") + " Job Requirement")
        
        # Form fields
        col1, col2 = st.columns(2)
        
        with col1:
            form_data['job_title'] = st.text_input(
                "Job Title*", 
                value=form_data['job_title'],
                help="Enter the job title (e.g., 'Senior Software Engineer')"
            )
            
            form_data['company'] = st.text_input(
                "Company*", 
                value=form_data['company'],
                help="Name of the company"
            )
            
            form_data['location'] = st.text_input(
                "Location", 
                value=form_data['location'],
                help="Job location (e.g., 'Remote', 'New York, NY')"
            )
            
            form_data['experience_level'] = st.selectbox(
                "Experience Level",
                options=["Entry Level", "Mid-Level", "Senior", "Lead", "Manager", "Director", "Executive"],
                index=["Entry Level", "Mid-Level", "Senior", "Lead", "Manager", "Director", "Executive"].index(
                    form_data['experience_level'] if form_data['experience_level'] in ["Entry Level", "Mid-Level", "Senior", "Lead", "Manager", "Director", "Executive"] 
                    else "Mid-Level"
                )
            )
            
        with col2:
            form_data['job_type'] = st.selectbox(
                "Job Type",
                options=["Full-time", "Part-time", "Contract", "Temporary", "Internship"],
                index=["Full-time", "Part-time", "Contract", "Temporary", "Internship"].index(
                    form_data['job_type'] if form_data['job_type'] in ["Full-time", "Part-time", "Contract", "Temporary", "Internship"] 
                    else "Full-time"
                )
            )
            
            form_data['salary_range'] = st.text_input(
                "Salary Range", 
                value=form_data['salary_range'],
                placeholder="e.g., $80,000 - $120,000",
                help="Expected or offered salary range"
            )
        
        # Full-width fields
        form_data['job_description'] = st.text_area(
            "Job Description*", 
            value=form_data['job_description'],
            height=200,
            help="Paste the job description here"
        )
        
        form_data['required_skills'] = st.text_area(
            "Required Skills & Technologies", 
            value=form_data['required_skills'],
            height=100,
            help="List required skills, one per line or comma-separated"
        )
        
        # Form actions
        submitted = st.form_submit_button("💾 Save Requirement")
        
        if submitted:
            # Basic validation
            if not form_data['job_title'] or not form_data['job_description'] or not form_data['company']:
                st.error("Please fill in all required fields (marked with *)")
                return None
            return form_data
    
    return None

def render_requirements_list(requirements_manager: RequirementsManager):
    """Render the list of requirements with actions."""
    st.subheader("📋 Saved Job Requirements")
    
    requirements = requirements_manager.list_requirements()
    
    if not requirements:
        st.info("No job requirements found. Create one using the form above.")
        return
    
    for req in requirements:
        with st.expander(f"{req.get('job_title', 'Untitled')} at {req.get('company', 'Unknown Company')}"):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**Experience Level:** {req.get('experience_level', 'Not specified')}")
                st.markdown(f"**Location:** {req.get('location', 'Not specified')}")
                st.markdown(f"**Job Type:** {req.get('job_type', 'Not specified')}")
                if req.get('salary_range'):
                    st.markdown(f"**Salary Range:** {req['salary_range']}")
                
                if st.checkbox("View Details", key=f"view_{req['id']}"):
                    st.markdown("**Job Description:**")
                    st.text_area("", value=req.get('job_description', ''), height=150, disabled=True, key=f"desc_{req['id']}")
                    
                    st.markdown("**Required Skills:**")
                    st.text_area("", value=req.get('required_skills', ''), height=100, disabled=True, key=f"skills_{req['id']}")
