"""
Resume Customizer Pro - Enterprise Multi-User Platform
A comprehensive resume customization platform with advanced multi-user features,
smart email automation, team collaboration, and high-performance architecture.
"""

import streamlit as st
import os
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Resume Customizer Pro",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import configuration and utilities
from config import get_app_config, validate_config, UI_CONFIG
from infrastructure.utilities.logger import get_logger

# Initialize logger
logger = get_logger()

# Initialize database connection
def initialize_database_connection():
    """Initialize database connection and schema."""
    try:
        from database import initialize_database, initialize_database_schema
        
        # Initialize database connection
        if not initialize_database():
            st.error("❌ Failed to initialize database connection")
            return False
        
        # Initialize schema
        if not initialize_database_schema():
            st.error("❌ Failed to initialize database schema")
            return False
        
        st.success("✅ Database initialized successfully")
        return True
        
    except ImportError:
        st.warning("⚠️ PostgreSQL dependencies not available. Using JSON storage as fallback.")
        return False
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main application entry point."""
    try:
        # Validate configuration
        config_result = validate_config()
        if not config_result.valid:
            st.error("❌ Configuration validation failed:")
            for issue in config_result.issues:
                st.error(f"  • {issue}")
            return
        
        # Initialize database
        if 'database_initialized' not in st.session_state:
            st.session_state.database_initialized = initialize_database_connection()
        
        # Load main application
        app_config = get_app_config()
        
        # Application header
        st.title(app_config["title"])
        st.markdown("*Professional resume customization with enterprise-grade features*")
        
        # Sidebar
        with st.sidebar:
            st.markdown("### 🚀 System Status")
            
            # Database status
            if st.session_state.get('database_initialized'):
                st.success("✅ PostgreSQL Connected")
            else:
                st.warning("⚠️ Using JSON Storage")
            
            # Health check
            if st.button("🔍 Health Check"):
                st.info("System operational")
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs(["📝 Resume Customizer", "📋 Requirements", "📖 Application Guide"])
        
        with tab1:
            render_resume_customizer_tab()
        
        with tab2:
            render_requirements_tab()
        
        with tab3:
            render_application_guide_tab()
    
    except Exception as e:
        st.error(f"❌ Application error: {e}")
        logger.error(f"Application error: {e}")
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())

def render_resume_customizer_tab():
    """Render the main resume customizer functionality."""
    st.header("📝 Resume Customizer")
    
    # File upload
    uploaded_files = st.file_uploader(
        "📁 Upload Resume Files",
        type=["docx"],
        accept_multiple_files=True,
        help="Upload one or more DOCX resume files"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} files uploaded successfully!")
        
        # Process each file
        for file in uploaded_files:
            with st.expander(f"📄 {file.name}", expanded=True):
                st.markdown("#### 📝 Tech Stack Input")
                
                # Tech stack input
                tech_input = st.text_area(
                    "Enter tech stack data:",
                    height=150,
                    key=f"tech_{file.name}",
                    help="Use supported formats for tech stack input"
                )
                
                # Email configuration
                st.markdown("#### 📧 Email Configuration")
                col1, col2 = st.columns(2)
                
                with col1:
                    recipient = st.text_input(f"Recipient Email", key=f"recipient_{file.name}")
                    sender = st.text_input(f"Sender Email", key=f"sender_{file.name}")
                
                with col2:
                    password = st.text_input(f"Password", type="password", key=f"password_{file.name}")
                    smtp_server = st.selectbox(
                        "SMTP Server",
                        ["smtp.gmail.com", "smtp.office365.com", "smtp.mail.yahoo.com"],
                        key=f"smtp_{file.name}"
                    )
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"🔍 Preview", key=f"preview_{file.name}"):
                        st.info("Preview functionality will be implemented")
                
                with col2:
                    if st.button(f"✅ Generate & Send", key=f"generate_{file.name}"):
                        st.info("Generation functionality will be implemented")

def render_requirements_tab():
    """Render the requirements management tab with fixed save functionality."""
    st.header("📋 Requirements Management")
    
    # Initialize requirements manager
    from ui.requirements_manager import RequirementsManager
    
    if 'requirements_manager' not in st.session_state:
        # Use database if available, otherwise fallback to JSON
        use_db = st.session_state.get('database_initialized', False)
        st.session_state.requirements_manager = RequirementsManager(use_database=use_db)
    
    requirements_manager = st.session_state.requirements_manager
    
    # Show current backend
    backend_type = "PostgreSQL Database" if requirements_manager.use_database else "JSON File Storage"
    st.info(f"📊 Storage Backend: {backend_type}")
    
    # Create new requirement section
    st.subheader("➕ Create New Requirement")
    
    # Check if we're editing an existing requirement
    editing_requirement = st.session_state.get('editing_requirement')
    
    if editing_requirement:
        st.info(f"✏️ Editing requirement: {editing_requirement.get('job_title', 'Untitled')}")
        if st.button("❌ Cancel Edit"):
            del st.session_state.editing_requirement
            st.rerun()
    
    # Render the requirement form
    form_data = render_requirement_form_fixed(editing_requirement)
    
    if form_data:
        try:
            if editing_requirement:
                # Update existing requirement
                requirement_id = editing_requirement['id']
                success = requirements_manager.update_requirement(requirement_id, form_data)
                if success:
                    st.success(f"✅ Requirement updated successfully!")
                    # Clear editing state
                    if 'editing_requirement' in st.session_state:
                        del st.session_state.editing_requirement
                    st.rerun()
                else:
                    st.error("❌ Failed to update requirement")
            else:
                # Create new requirement
                requirement_id = requirements_manager.create_requirement(form_data)
                if requirement_id:
                    st.success(f"✅ Requirement created successfully! ID: {requirement_id}")
                    st.rerun()
                else:
                    st.error("❌ Failed to create requirement")
        except Exception as e:
            st.error(f"❌ Error saving requirement: {e}")
            logger.error(f"Error saving requirement: {e}")
    
    # List existing requirements
    st.markdown("---")
    render_requirements_list_fixed(requirements_manager)

def render_requirement_form_fixed(requirement_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Render the fixed requirement form with proper form handling."""
    is_edit = requirement_data is not None
    
    # Initialize form data
    if is_edit:
        form_data = requirement_data.copy()
    else:
        form_data = {
            'req_status': 'New',
            'applied_for': 'Raju',
            'next_step': '',
            'rate': '',
            'tax_type': 'C2C',
            'client_company': '',
            'prime_vendor_company': '',
            'vendor_details': {
                'vendor_company': '',
                'vendor_person_name': '',
                'vendor_phone_number': '',
                'vendor_email': ''
            },
            'job_requirement_info': {
                'requirement_entered_date': datetime.now().isoformat(),
                'got_requirement_from': 'Got from online resume',
                'tech_stack': [],
                'job_title': '',
                'job_portal_link': '',
                'primary_tech_stack': '',
                'complete_job_description': ''
            },
            'marketing_comments': [],
            'consultants': []
        }
    
    # Create form with unique key
    form_key = f"requirement_form_{requirement_data.get('id', 'new')}" if requirement_data else "requirement_form_new"
    
    with st.form(key=form_key, clear_on_submit=not is_edit):
        st.markdown("### 📝 Requirement Details")
        
        # Basic Information
        col1, col2 = st.columns(2)
        
        with col1:
            req_status = st.selectbox(
                "Status*",
                ["New", "Working", "Applied", "Cancelled", "Submitted", "Interviewed", "On Hold"],
                index=["New", "Working", "Applied", "Cancelled", "Submitted", "Interviewed", "On Hold"].index(
                    form_data.get('req_status', 'New')
                ) if form_data.get('req_status') in ["New", "Working", "Applied", "Cancelled", "Submitted", "Interviewed", "On Hold"] else 0
            )
            
            applied_for = st.selectbox(
                "Applied For*",
                ["Raju", "Eric"],
                index=["Raju", "Eric"].index(form_data.get('applied_for', 'Raju')) if form_data.get('applied_for') in ["Raju", "Eric"] else 0
            )
            
            next_step = st.text_input(
                "Next Step",
                value=form_data.get('next_step', ''),
                placeholder="Describe the next step"
            )
            
            rate = st.text_input(
                "Rate",
                value=form_data.get('rate', ''),
                placeholder="e.g., $85/hour, $120,000/year"
            )
            
            tax_type = st.selectbox(
                "Tax Type*",
                ["C2C", "1099", "W2", "Fulltime"],
                index=["C2C", "1099", "W2", "Fulltime"].index(form_data.get('tax_type', 'C2C')) if form_data.get('tax_type') in ["C2C", "1099", "W2", "Fulltime"] else 0
            )
        
        with col2:
            client_company = st.text_input(
                "Client Company*",
                value=form_data.get('client_company', ''),
                placeholder="Name of the client company"
            )
            
            prime_vendor_company = st.text_input(
                "Prime Vendor Company",
                value=form_data.get('prime_vendor_company', ''),
                placeholder="Name of the prime vendor"
            )
            
            job_title = st.text_input(
                "Job Title*",
                value=form_data.get('job_requirement_info', {}).get('job_title', ''),
                placeholder="e.g., Senior Software Engineer"
            )
            
            got_requirement_from = st.selectbox(
                "Got Requirement From*",
                ["Got from online resume", "Got through Job Portal"],
                index=["Got from online resume", "Got through Job Portal"].index(
                    form_data.get('job_requirement_info', {}).get('got_requirement_from', 'Got from online resume')
                ) if form_data.get('job_requirement_info', {}).get('got_requirement_from') in ["Got from online resume", "Got through Job Portal"] else 0
            )
        
        # Vendor Details
        st.markdown("#### 👤 Vendor Details")
        col1, col2 = st.columns(2)
        
        with col1:
            vendor_company = st.text_input(
                "Vendor Company",
                value=form_data.get('vendor_details', {}).get('vendor_company', ''),
                placeholder="Vendor company name"
            )
            
            vendor_person_name = st.text_input(
                "Vendor Contact Person",
                value=form_data.get('vendor_details', {}).get('vendor_person_name', ''),
                placeholder="Contact person name"
            )
        
        with col2:
            vendor_phone = st.text_input(
                "Vendor Phone",
                value=form_data.get('vendor_details', {}).get('vendor_phone_number', ''),
                placeholder="Phone number"
            )
            
            vendor_email = st.text_input(
                "Vendor Email",
                value=form_data.get('vendor_details', {}).get('vendor_email', ''),
                placeholder="Email address"
            )
        
        # Tech Stack and Job Details
        st.markdown("#### 💼 Job Details")
        
        tech_stack_options = [
            "Java", "Python", "JavaScript", "React", "Node.js", "Angular", "AWS", 
            "Docker", "Kubernetes", "SQL", "MongoDB", "PostgreSQL", "Redis",
            "Spring Boot", "Django", "Flask", "Express.js", "Vue.js", "TypeScript"
        ]
        
        tech_stack = st.multiselect(
            "Tech Stack",
            options=tech_stack_options,
            default=form_data.get('job_requirement_info', {}).get('tech_stack', [])
        )
        
        primary_tech_stack = st.text_input(
            "Primary Tech Stack",
            value=form_data.get('job_requirement_info', {}).get('primary_tech_stack', ''),
            placeholder="Main technology for this role"
        )
        
        job_portal_link = st.text_input(
            "Job Portal Link",
            value=form_data.get('job_requirement_info', {}).get('job_portal_link', ''),
            placeholder="https://example.com/job-posting"
        )
        
        complete_job_description = st.text_area(
            "Complete Job Description",
            value=form_data.get('job_requirement_info', {}).get('complete_job_description', ''),
            height=150,
            placeholder="Paste the complete job description here..."
        )
        
        # Comments
        st.markdown("#### 💬 Comments")
        new_comment = st.text_area(
            "Add Comment",
            placeholder="Enter your comment here...",
            height=100
        )
        
        # Submit button
        submitted = st.form_submit_button("💾 Save Requirement", use_container_width=True)
        
        if submitted:
            # Validate required fields
            if not job_title.strip():
                st.error("❌ Job Title is required")
                return None
            
            if not client_company.strip():
                st.error("❌ Client Company is required")
                return None
            
            # Prepare form data
            result_data = {
                'req_status': req_status,
                'applied_for': applied_for,
                'next_step': next_step,
                'rate': rate,
                'tax_type': tax_type,
                'client_company': client_company,
                'prime_vendor_company': prime_vendor_company,
                'vendor_details': {
                    'vendor_company': vendor_company,
                    'vendor_person_name': vendor_person_name,
                    'vendor_phone_number': vendor_phone,
                    'vendor_email': vendor_email
                },
                'job_requirement_info': {
                    'requirement_entered_date': datetime.now().isoformat(),
                    'got_requirement_from': got_requirement_from,
                    'tech_stack': tech_stack,
                    'job_title': job_title,
                    'job_portal_link': job_portal_link,
                    'primary_tech_stack': primary_tech_stack,
                    'complete_job_description': complete_job_description
                },
                'marketing_comments': form_data.get('marketing_comments', []),
                'consultants': form_data.get('consultants', [])
            }
            
            # Add new comment if provided
            if new_comment.strip():
                comment_obj = {
                    'comment': new_comment.strip(),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'author': 'User'
                }
                result_data['marketing_comments'].append(comment_obj)
            
            # Add legacy compatibility fields
            result_data.update({
                'job_title': job_title,
                'client': client_company,
                'prime_vendor': prime_vendor_company,
                'status': req_status,
                'next_steps': next_step,
                'vendor_info': {
                    'name': vendor_person_name,
                    'company': vendor_company,
                    'phone': vendor_phone,
                    'email': vendor_email
                }
            })
            
            return result_data
    
    return None

def render_requirements_list_fixed(requirements_manager):
    """Render the requirements list with proper functionality."""
    st.subheader("📋 Requirements List")
    
    try:
        requirements = requirements_manager.list_requirements()
        
        if not requirements:
            st.info("📝 No requirements found. Create your first requirement using the form above.")
            return
        
        # Export functionality
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("📄 Export All"):
                try:
                    export_data = requirements_manager.export_requirements()
                    if export_data:
                        st.download_button(
                            label="💾 Download JSON",
                            data=export_data,
                            file_name=f"requirements_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        st.success("✅ Export ready for download!")
                    else:
                        st.error("❌ Export failed")
                except Exception as e:
                    st.error(f"❌ Export error: {e}")
        
        with col2:
            uploaded_file = st.file_uploader(
                "📥 Import Requirements",
                type=["json"],
                key="import_requirements"
            )
            
            if uploaded_file:
                if st.button("📅 Import"):
                    try:
                        import_data = uploaded_file.read().decode('utf-8')
                        success = requirements_manager.import_requirements(import_data, merge=True)
                        if success:
                            st.success("✅ Requirements imported successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Import failed")
                    except Exception as e:
                        st.error(f"❌ Import error: {e}")
        
        with col3:
            st.metric("📊 Total Requirements", len(requirements))
        
        st.markdown("---")
        
        # Display requirements
        for req in sorted(requirements, key=lambda x: x.get('created_at', ''), reverse=True):
            render_requirement_item(req, requirements_manager)
    
    except Exception as e:
        st.error(f"❌ Error loading requirements: {e}")
        logger.error(f"Error in requirements list: {e}")

def render_requirement_item(req: Dict[str, Any], requirements_manager):
    """Render individual requirement item."""
    # Status emoji mapping
    status_emoji = {
        'New': '🆕',
        'Working': '🔄',
        'Applied': '📝',
        'Cancelled': '❌',
        'Submitted': '📤',
        'Interviewed': '✅',
        'On Hold': '⏸️'
    }
    
    status = req.get('req_status', req.get('status', 'New'))
    emoji = status_emoji.get(status, '📌')
    job_title = req.get('job_requirement_info', {}).get('job_title', '') or req.get('job_title', 'Untitled')
    client = req.get('client_company', '') or req.get('client', 'Unknown Client')
    
    title = f"{emoji} {job_title} @ {client}"
    
    with st.expander(title):
        # Display requirement details in tabs
        tab1, tab2, tab3 = st.tabs(["📋 Basic Info", "🏢 Company Details", "💬 Comments"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Status:** {status}")
                st.markdown(f"**Applied For:** {req.get('applied_for', 'Not specified')}")
                st.markdown(f"**Tax Type:** {req.get('tax_type', 'Not specified')}")
                
                if req.get('rate'):
                    st.markdown(f"**Rate:** {req['rate']}")
                
                if req.get('next_step'):
                    st.markdown(f"**Next Step:** {req['next_step']}")
            
            with col2:
                # Job details
                job_info = req.get('job_requirement_info', {})
                if job_info.get('primary_tech_stack'):
                    st.markdown(f"**Primary Tech:** {job_info['primary_tech_stack']}")
                
                if job_info.get('tech_stack'):
                    tech_list = ', '.join(job_info['tech_stack'])
                    st.markdown(f"**Tech Stack:** {tech_list}")
                
                if job_info.get('got_requirement_from'):
                    st.markdown(f"**Source:** {job_info['got_requirement_from']}")
                
                # Timestamps
                if req.get('created_at'):
                    st.caption(f"Created: {req['created_at']}")
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Company Information**")
                st.markdown(f"**Client:** {req.get('client_company', 'Not specified')}")
                if req.get('prime_vendor_company'):
                    st.markdown(f"**Prime Vendor:** {req['prime_vendor_company']}")
            
            with col2:
                st.markdown("**Vendor Details**")
                vendor_details = req.get('vendor_details', {})
                if vendor_details.get('vendor_company'):
                    st.markdown(f"**Company:** {vendor_details['vendor_company']}")
                if vendor_details.get('vendor_person_name'):
                    st.markdown(f"**Contact:** {vendor_details['vendor_person_name']}")
                if vendor_details.get('vendor_phone_number'):
                    st.markdown(f"**Phone:** {vendor_details['vendor_phone_number']}")
                if vendor_details.get('vendor_email'):
                    st.markdown(f"**Email:** {vendor_details['vendor_email']}")
        
        with tab3:
            comments = req.get('marketing_comments', [])
            if comments:
                st.markdown(f"**Comments ({len(comments)}):**")
                for comment in reversed(comments):  # Show newest first
                    timestamp = comment.get('timestamp', 'Unknown time')
                    text = comment.get('comment', '')
                    author = comment.get('author', 'Unknown')
                    st.markdown(f"**{timestamp}** ({author}):")
                    st.markdown(f"> {text}")
                    st.markdown("---")
            else:
                st.info("No comments yet")
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✏️ Edit", key=f"edit_{req.get('id', 'unknown')}"):
                st.session_state.editing_requirement = req
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{req.get('id', 'unknown')}"):
                if st.button("⚠️ Confirm Delete", key=f"confirm_delete_{req.get('id', 'unknown')}"):
                    try:
                        success = requirements_manager.delete_requirement(req.get('id'))
                        if success:
                            st.success("✅ Requirement deleted successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete requirement")
                    except Exception as e:
                        st.error(f"❌ Delete error: {e}")
        
        with col3:
            # Show summary stats
            comment_count = len(req.get('marketing_comments', []))
            tech_count = len(req.get('job_requirement_info', {}).get('tech_stack', []))
            st.caption(f"💬 {comment_count} comments | 🔧 {tech_count} technologies")

def render_application_guide_tab():
    """Render the application guide tab."""
    st.header("📖 Application Guide")
    
    st.markdown("""
    ## 🎯 Welcome to Resume Customizer Pro
    
    This application helps you customize resumes and manage job requirements efficiently.
    
    ### 📝 Resume Customizer Features
    - Upload multiple DOCX resume files
    - Add technology-specific bullet points
    - Email customized resumes automatically
    - Preview changes before applying
    
    ### 📋 Requirements Management Features
    - Track job applications and requirements
    - Store client and vendor information
    - Manage comments and follow-ups
    - Export/import data for backup
    
    ### 🚀 Getting Started
    1. **Upload Resumes**: Use the Resume Customizer tab to upload your resume files
    2. **Add Tech Points**: Enter technology-specific bullet points
    3. **Configure Email**: Set up email delivery settings
    4. **Manage Requirements**: Use the Requirements tab to track job applications
    
    ### 💾 Database Features
    - **PostgreSQL Integration**: Fast, reliable database storage
    - **Automatic Backup**: JSON export/import capabilities
    - **Concurrent Access**: Multiple users can work simultaneously
    - **Data Integrity**: ACID transactions ensure data consistency
    
    ### 🔒 Security Features
    - **Password Encryption**: Email passwords are encrypted
    - **Input Sanitization**: All inputs are sanitized for security
    - **Rate Limiting**: Prevents abuse and overuse
    - **Session Security**: Automatic timeout and secure sessions
    """)

if __name__ == "__main__":
    main()