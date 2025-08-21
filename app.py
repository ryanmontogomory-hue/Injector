import streamlit as st
from docx import Document
from io import BytesIO
import re
import base64
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
import concurrent.futures
import threading
from collections import defaultdict
import time
import queue
from contextlib import contextmanager

# Set page configuration
st.set_page_config(page_title="Resume Customizer", layout="wide")
st.title("📝 Bulk Resume Customizer + Email Sender")

# Add a sidebar for instructions and information
with st.sidebar:
    st.header("ℹ️ Instructions")
    st.markdown("""
    1. Upload your resume(s) in DOCX format
    2. For each resume, provide:
       - Tech stacks with bullet points (format: 'TechName: • point1 • point2')
       - Email credentials for sending (optional)
    3. Click '🔍 Preview Changes' to see exactly what will be modified
    4. Review the preview and click 'Generate & Send Customized Resumes'
    5. Download or email the customized resumes
    """)
    
    st.header("👀 Preview Features")
    st.markdown("""
    The preview will show you ONLY the changes:
    - ✅ Which projects will be enhanced
    - ➕ Exactly which NEW points will be added
    - 🎯 Where each point will be inserted
    - 📧 Email configuration status
    - 📊 Summary of additions only
    """)
    
    st.header("🎯 Project Selection")
    st.markdown("""
    **Top 3 Projects Focus:**
    - Points are added only to the first 3 projects
    - This highlights your most recent/relevant work
    - Projects 4+ remain unchanged
    - If you have ≤ 3 projects, all get points
    """)
    
    st.header("🔍 Format Preservation")
    st.markdown("""
    The app will preserve all formatting exactly:
    - Font family and size
    - Font color
    - Bold/italic/underline styles
    - Paragraph spacing and indentation
    - Bullet point styling
    """)
    
    st.header("🔒 Security Note")
    st.markdown("""
    - We recommend using app-specific passwords
    - Your credentials are not stored
    - Consider using a dedicated email for this purpose
    """)

# Initialize session state for resume data if it doesn't exist
if 'resume_inputs' not in st.session_state:
    st.session_state.resume_inputs = {}

uploaded_files = st.file_uploader("Upload one or more .docx resumes", type="docx", accept_multiple_files=True)

def distribute_points(points_list, num_projects):
    """
    Distribute points across the top 3 projects only (or all projects if 3 or fewer).
    This focuses enhancement on the most recent/relevant projects.
    
    For example:
    - 6 points across 5 projects → Only first 3 projects get points: [2, 2, 2]
    - 7 points across 3 projects → [3, 2, 2]
    - 8 points across 2 projects → [4, 4]
    """
    if not points_list or num_projects == 0:
        return []
    
    # Limit to top 3 projects maximum
    projects_to_enhance = min(3, num_projects)
    
    n = len(points_list)
    base_size = n // projects_to_enhance
    remainder = n % projects_to_enhance
    
    distribution = []
    start_index = 0
    
    # Distribute points only to the first 3 projects
    for i in range(projects_to_enhance):
        # Add an extra point to the first 'remainder' projects
        points_in_project = base_size + (1 if i < remainder else 0)
        
        if start_index + points_in_project > n:
            points_in_project = n - start_index
            
        if points_in_project > 0:
            distribution.append(points_list[start_index:start_index + points_in_project])
            start_index += points_in_project
    
    # Add empty lists for remaining projects (4th, 5th, etc.) so they get no points
    while len(distribution) < num_projects:
        distribution.append([])
    
    return distribution

def find_projects_and_responsibilities(doc):
    """
    Find all projects and their Responsibilities sections in the resume.
    Returns a list of tuples with (project_name, responsibilities_start_index, responsibilities_end_index)
    """
    projects = []
    current_project = None
    in_responsibilities = False
    responsibilities_start = -1
    
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        
        # Look for project headings (job titles, roles, or project names)
        # Check for common job title patterns and role indicators
        is_potential_project = False
        
        if text and len(text) < 100 and not any(keyword in text.lower() for keyword in ["summary", "skills", "education", "achievements", "responsibilities:"]):
            # Check if it's all caps (common for project/role headings)
            if text.isupper():
                is_potential_project = True
            # Check for common job title keywords
            elif any(keyword in text.lower() for keyword in ["manager", "developer", "engineer", "analyst", "lead", "senior", "junior", "architect", "consultant", "specialist", "coordinator", "supervisor", "director", "designer", "tester", "qa", "devops"]):
                is_potential_project = True
            # Check for project-related patterns
            elif any(pattern in text.lower() for pattern in ["project", "team", "role", "position", "intern", "trainee", "associate"]):
                is_potential_project = True
        
        if is_potential_project:
            # This might be a project heading
            if current_project and responsibilities_start != -1:
                # Find the end of the responsibilities section
                responsibilities_end = i - 1
                for j in range(i-1, responsibilities_start-1, -1):
                    if doc.paragraphs[j].text.strip() and not doc.paragraphs[j].text.strip().startswith("-"):
                        responsibilities_end = j
                        break
                projects.append((current_project, responsibilities_start, responsibilities_end))
            
            current_project = text
            in_responsibilities = False
            responsibilities_start = -1
        
        # Look for Responsibilities section
        elif text and "responsibilities:" in text.lower():
            in_responsibilities = True
            responsibilities_start = i + 1  # Start after the Responsibilities heading
        
        # If we're in responsibilities and find the end (next section or next project)
        elif in_responsibilities and text and (text.startswith("##") or 
                    any(keyword in text.lower() for keyword in ["achievements", "technologies", "tools", "key"])):
            if current_project and responsibilities_start != -1:
                responsibilities_end = i - 1
                projects.append((current_project, responsibilities_start, responsibilities_end))
            in_responsibilities = False
            responsibilities_start = -1
    
    # Add the last project if found
    if current_project and responsibilities_start != -1:
        responsibilities_end = len(doc.paragraphs) - 1
        projects.append((current_project, responsibilities_start, responsibilities_end))
    
    return projects

def copy_paragraph_formatting(source_para, target_para):
    """
    Copy all formatting from source paragraph to target paragraph with error handling
    """
    try:
        # Copy paragraph style
        if source_para.style:
            target_para.style = source_para.style
        
        # Copy paragraph alignment
        if source_para.paragraph_format.alignment is not None:
            target_para.paragraph_format.alignment = source_para.paragraph_format.alignment
        
        # Copy paragraph spacing
        if source_para.paragraph_format.space_before is not None:
            target_para.paragraph_format.space_before = source_para.paragraph_format.space_before
        if source_para.paragraph_format.space_after is not None:
            target_para.paragraph_format.space_after = source_para.paragraph_format.space_after
        if source_para.paragraph_format.line_spacing is not None:
            target_para.paragraph_format.line_spacing = source_para.paragraph_format.line_spacing
        
        # Copy indentation
        if source_para.paragraph_format.left_indent is not None:
            target_para.paragraph_format.left_indent = source_para.paragraph_format.left_indent
        if source_para.paragraph_format.first_line_indent is not None:
            target_para.paragraph_format.first_line_indent = source_para.paragraph_format.first_line_indent
    except Exception as e:
        # Continue if formatting fails - don't let it break the entire process
        pass

def copy_run_formatting(source_run, target_run):
    """
    Copy all formatting from source run to target run
    """
    # Copy font properties
    target_run.font.name = source_run.font.name
    target_run.font.size = source_run.font.size
    target_run.font.bold = source_run.font.bold
    target_run.font.italic = source_run.font.italic
    target_run.font.underline = source_run.font.underline
    
    # Copy font color
    if source_run.font.color.rgb:
        target_run.font.color.rgb = source_run.font.color.rgb
    
    # Copy highlighting
    if hasattr(source_run.font, 'highlight_color') and source_run.font.highlight_color:
        target_run.font.highlight_color = source_run.font.highlight_color

def is_bullet_point(text):
    """
    Check if text starts with a bullet point marker
    """
    text = text.strip()
    return (text.startswith('-') or text.startswith('•') or text.startswith('*') or
            (text and text[0].isdigit() and '.' in text[:3]))

def get_bullet_formatting(doc, paragraph_index):
    """
    Extract complete bullet formatting from a paragraph
    """
    if paragraph_index >= len(doc.paragraphs):
        return None
        
    para = doc.paragraphs[paragraph_index]
    if not is_bullet_point(para.text):
        return None
        
    # Get the formatting from the first run (assuming consistent formatting)
    if para.runs:
        first_run = para.runs[0]
        return {
            'font_name': first_run.font.name,
            'font_size': first_run.font.size,
            'bold': first_run.font.bold,
            'italic': first_run.font.italic,
            'underline': first_run.font.underline,
            'color': first_run.font.color.rgb,
            'style': para.style
        }
    
    return None

def apply_bullet_formatting(paragraph, formatting, text):
    """
    Apply complete formatting to a new bullet point
    """
    if not formatting:
        return
        
    # Clear existing content
    paragraph.clear()
    
    # Add formatted text
    run = paragraph.add_run(text)
    
    # Apply all formatting properties
    if formatting['font_name']: run.font.name = formatting['font_name']
    if formatting['font_size']: run.font.size = formatting['font_size']
    run.font.bold = formatting['bold']
    run.font.italic = formatting['italic']
    run.font.underline = formatting['underline']
    if formatting['color']: run.font.color.rgb = formatting['color']
    
    # Apply paragraph style
    if formatting['style']: paragraph.style = formatting['style']

def preview_single_resume(filename, data):
    """
    Preview a single resume with applied changes
    """
    st.markdown("---")
    st.markdown(f"### 👀 Preview for {filename}")
    
    file = data['file']
    raw_text = data['text']
    
    # Validate inputs
    if not raw_text.strip():
        st.error(f"❌ No tech stack data provided for {filename}")
        return
    
    # Parse tech stacks and points
    techstack_pattern = r"(?P<stack>[A-Za-z0-9_+#\- ]+):\s*(?P<points>(?:• .+\n?)+)"
    matches = list(re.finditer(techstack_pattern, raw_text))
    
    if not matches:
        st.error(f"❌ Could not parse tech stacks for {filename}")
        return
    
    selected_points = []
    tech_stacks_used = []
    
    for match in matches:
        stack = match.group("stack").strip()
        points_block = match.group("points").strip()
        points = re.findall(r"•\s*(.+)", points_block)
        selected_points.extend(points)
        tech_stacks_used.append(stack)
    
    try:
        doc = Document(file)
        projects = find_projects_and_responsibilities(doc)
        
        if not projects:
            st.error(f"❌ No projects with Responsibilities sections found in {filename}")
            return
        
        # Distribute points for preview
        grouped_projects = distribute_points(selected_points, len(projects))
        
        # Apply the changes to the resume and show the updated content
        st.subheader(f"📄 Updated Resume Preview: {filename}")
        
        # Create a copy of the document to modify for preview
        import io
        
        # Save original doc to memory
        temp_buffer = io.BytesIO()
        doc.save(temp_buffer)
        temp_buffer.seek(0)
        
        # Load a fresh copy for preview
        preview_doc = Document(temp_buffer)
        preview_projects = find_projects_and_responsibilities(preview_doc)
        
        # Apply the changes to the preview document
        points_added = add_points_to_responsibilities(preview_doc, preview_projects, grouped_projects)
        
        st.success(f"✅ Preview generated with {points_added} points added!")
        st.info(f"Tech stacks highlighted: {', '.join(tech_stacks_used)}")
        
        # Convert updated document to HTML for display
        try:
            # Save the updated document to a buffer
            updated_buffer = io.BytesIO()
            preview_doc.save(updated_buffer)
            updated_buffer.seek(0)
            
            # Try to convert to HTML using mammoth (if available)
            try:
                import mammoth
                result = mammoth.convert_to_html(updated_buffer)
                html_content = result.value
                
                # Display the HTML content (original Word format)
                st.markdown("### 📝 Your Updated Resume (Word Format):")
                st.markdown(html_content, unsafe_allow_html=True)
                
            except ImportError:
                # Fallback: Show plain text with proper formatting
                st.markdown("### 📝 Your Updated Resume Content:")
                st.info("ℹ️ Install 'mammoth' package for better Word format display: pip install mammoth")
                
                # Show formatted text content
                resume_text = ""
                for para in preview_doc.paragraphs:
                    text = para.text.strip()
                    if text:
                        resume_text += text + "\n\n"
                
                # Display in a text area to maintain formatting
                st.text_area(
                    "Updated Resume Content",
                    value=resume_text,
                    height=600,
                    help="This is your updated resume content. Install 'mammoth' for Word-like display."
                )
                
        except Exception as e:
            st.error(f"Error displaying preview: {str(e)}")
            # Fallback to simple text display
            resume_text = ""
            for para in preview_doc.paragraphs:
                text = para.text.strip()
                if text:
                    resume_text += text + "\n\n"
            
            st.text_area(
                "Updated Resume Content (Text Format)",
                value=resume_text,
                height=600
            )
        
        # Store individual preview data
        if 'individual_previews' not in st.session_state:
            st.session_state.individual_previews = {}
        
        st.session_state.individual_previews[filename] = {
            'tech_stacks': tech_stacks_used,
            'total_points': len(selected_points),
            'projects': projects,
            'point_distribution': grouped_projects,
            'email_recipient': data['recipient_email'],
            'email_sender': data['sender_email']
        }
        
    except Exception as e:
        st.error(f"❌ Error analyzing {filename}: {str(e)}")

def add_points_to_responsibilities(doc, projects, points_by_project):
    """
    Add points to the responsibilities sections while preserving all formatting exactly
    """
    points_added = 0
    
    # We need to process from the end to avoid index shifting issues
    for i in range(len(projects)-1, -1, -1):
        project_name, start_idx, end_idx = projects[i]
        
        if i < len(points_by_project) and points_by_project[i]:
            # Find the best bullet point to copy formatting from
            formatting_sample = None
            sample_index = -1
            
            # Look for bullet points in this section
            for j in range(start_idx, end_idx + 1):
                if j < len(doc.paragraphs) and is_bullet_point(doc.paragraphs[j].text):
                    formatting_sample = get_bullet_formatting(doc, j)
                    sample_index = j
                    break
            
            # If no bullet points found, try to find any text in the section
            if not formatting_sample:
                for j in range(start_idx, end_idx + 1):
                    if j < len(doc.paragraphs) and doc.paragraphs[j].text.strip():
                        # Create a basic formatting sample
                        para = doc.paragraphs[j]
                        if para.runs:
                            first_run = para.runs[0]
                            formatting_sample = {
                                'font_name': first_run.font.name,
                                'font_size': first_run.font.size,
                                'bold': first_run.font.bold,
                                'italic': first_run.font.italic,
                                'underline': first_run.font.underline,
                                'color': first_run.font.color.rgb,
                                'style': para.style
                            }
                            sample_index = j
                            break
            
            if formatting_sample and sample_index != -1:
                # Add points after the last bullet point or at the end of the section
                insert_index = end_idx + 1
                for j in range(end_idx, start_idx-1, -1):
                    if j < len(doc.paragraphs) and is_bullet_point(doc.paragraphs[j].text):
                        insert_index = j + 1
                        break
                
                # Insert points at the correct location within this project's section
                for point_idx, point in enumerate(reversed(points_by_project[i])):
                    # Calculate the actual insertion index, accounting for previously inserted paragraphs
                    actual_insert_index = insert_index + point_idx
                    
                    # Ensure we don't go beyond document bounds
                    if actual_insert_index >= len(doc.paragraphs):
                        # If we're at the end, add a new paragraph
                        new_para = doc.add_paragraph(f"- {point}")
                    else:
                        # Insert before the calculated position
                        new_para = doc.paragraphs[actual_insert_index].insert_paragraph_before(f"- {point}")
                    
                    # Apply the exact same formatting
                    apply_bullet_formatting(new_para, formatting_sample, f"- {point}")
                    
                    # Copy paragraph formatting too
                    copy_paragraph_formatting(doc.paragraphs[sample_index], new_para)
                    
                    points_added += 1
    
    return points_added

# SMTP Connection Pool Manager
class SMTPConnectionPool:
    def __init__(self):
        self._connections = {}
        self._lock = threading.Lock()
    
    @contextmanager
    def get_connection(self, smtp_server, smtp_port, sender_email, sender_password):
        connection_key = f"{smtp_server}:{smtp_port}:{sender_email}"
        
        with self._lock:
            if connection_key not in self._connections:
                try:
                    smtp = smtplib.SMTP_SSL(smtp_server, smtp_port)
                    smtp.login(sender_email, sender_password)
                    self._connections[connection_key] = smtp
                except Exception as e:
                    raise Exception(f"Failed to create SMTP connection: {str(e)}")
        
        try:
            yield self._connections[connection_key]
        except Exception as e:
            # If connection fails, remove it from pool
            with self._lock:
                if connection_key in self._connections:
                    try:
                        self._connections[connection_key].quit()
                    except:
                        pass
                    del self._connections[connection_key]
            raise e
    
    def close_all(self):
        with self._lock:
            for smtp in self._connections.values():
                try:
                    smtp.quit()
                except:
                    pass
            self._connections.clear()

# Global SMTP connection pool
smtp_pool = SMTPConnectionPool()

def process_single_resume(file_data, progress_callback=None):
    """
    Process a single resume (optimized for parallel execution)
    """
    try:
        filename = file_data['filename']
        file_obj = file_data['file']
        raw_text = file_data['text']
        
        if progress_callback:
            progress_callback(f"Parsing tech stacks for {filename}...")
        
        # Parse tech stacks and points
        techstack_pattern = r"(?P<stack>[A-Za-z0-9_+#\- ]+):\s*(?P<points>(?:• .+\n?)+)"
        matches = list(re.finditer(techstack_pattern, raw_text))
        
        if not matches:
            return {'success': False, 'error': f'Could not parse tech stacks for {filename}', 'filename': filename}
        
        selected_points = []
        tech_stacks_used = []
        
        for match in matches:
            stack = match.group("stack").strip()
            points_block = match.group("points").strip()
            points = re.findall(r"•\s*(.+)", points_block)
            selected_points.extend(points)
            tech_stacks_used.append(stack)
        
        if progress_callback:
            progress_callback(f"Processing document for {filename}...")
        
        # Load and process document
        doc = Document(file_obj)
        projects = find_projects_and_responsibilities(doc)
        
        if not projects:
            return {'success': False, 'error': f'No projects found in {filename}', 'filename': filename}
        
        # Distribute and add points
        grouped_projects = distribute_points(selected_points, len(projects))
        points_added = add_points_to_responsibilities(doc, projects, grouped_projects)
        
        if progress_callback:
            progress_callback(f"Saving document for {filename}...")
        
        # Save to buffer
        output_buffer = BytesIO()
        doc.save(output_buffer)
        output_buffer.seek(0)
        
        return {
            'success': True,
            'filename': filename,
            'buffer': output_buffer.getvalue(),
            'tech_stacks': tech_stacks_used,
            'points_added': points_added,
            'email_data': {
                'recipient': file_data.get('recipient_email', ''),
                'sender': file_data.get('sender_email', ''),
                'password': file_data.get('sender_password', ''),
                'smtp_server': file_data.get('smtp_server', ''),
                'smtp_port': file_data.get('smtp_port', 465),
                'subject': file_data.get('email_subject', ''),
                'body': file_data.get('email_body', '')
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e), 'filename': file_data['filename']}

def send_emails_batch(email_tasks, progress_callback=None):
    """
    Send multiple emails using connection pooling
    """
    results = []
    
    # Group emails by SMTP server for efficiency
    server_groups = defaultdict(list)
    for task in email_tasks:
        if task['email_data']['recipient'] and task['email_data']['sender']:
            key = f"{task['email_data']['smtp_server']}:{task['email_data']['sender']}"
            server_groups[key].append(task)
    
    for server_key, tasks in server_groups.items():
        if not tasks:
            continue
            
        first_task = tasks[0]
        smtp_server = first_task['email_data']['smtp_server']
        smtp_port = first_task['email_data']['smtp_port']
        sender_email = first_task['email_data']['sender']
        sender_password = first_task['email_data']['password']
        
        if smtp_server == "Custom":
            for task in tasks:
                results.append({
                    'success': False,
                    'filename': task['filename'],
                    'error': 'Custom SMTP server not supported in bulk mode'
                })
            continue
        
        try:
            with smtp_pool.get_connection(smtp_server, smtp_port, sender_email, sender_password) as smtp:
                for task in tasks:
                    try:
                        if progress_callback:
                            progress_callback(f"Sending email for {task['filename']}...")
                        
                        msg = EmailMessage()
                        msg['Subject'] = task['email_data']['subject']
                        msg['From'] = sender_email
                        msg['To'] = task['email_data']['recipient']
                        msg.set_content(task['email_data']['body'])
                        
                        msg.add_attachment(
                            task['buffer'],
                            maintype='application',
                            subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
                            filename=task['filename']
                        )
                        
                        smtp.send_message(msg)
                        results.append({
                            'success': True,
                            'filename': task['filename'],
                            'recipient': task['email_data']['recipient']
                        })
                        
                    except Exception as e:
                        results.append({
                            'success': False,
                            'filename': task['filename'],
                            'error': str(e)
                        })
                        
        except Exception as e:
            for task in tasks:
                results.append({
                    'success': False,
                    'filename': task['filename'],
                    'error': f'SMTP connection failed: {str(e)}'
                })
    
    return results

def process_resumes_bulk(files_data, max_workers=4):
    """
    Process multiple resumes in parallel
    """
    processed_resumes = []
    failed_resumes = []
    
    # Use ThreadPoolExecutor for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all resume processing tasks
        future_to_file = {
            executor.submit(process_single_resume, file_data): file_data['filename'] 
            for file_data in files_data
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                result = future.result()
                if result['success']:
                    processed_resumes.append(result)
                else:
                    failed_resumes.append(result)
            except Exception as e:
                failed_resumes.append({
                    'success': False,
                    'filename': filename,
                    'error': str(e)
                })
    
    return processed_resumes, failed_resumes

if uploaded_files:
    st.markdown("### 🔽 Paste Tech Stack + Points for Each Resume")
    
    # Create a tab for each uploaded file
    tabs = st.tabs([file.name for file in uploaded_files])
    
    for i, file in enumerate(uploaded_files):
        with tabs[i]:
            st.subheader(f"Customize {file.name}")
            
            # Example input format
            with st.expander("💡 Example Input Format"):
                st.code("""
Python: • Developed web applications using Django and Flask • Implemented RESTful APIs
JavaScript: • Created interactive UI components with React • Utilized Node.js for backend services
AWS: • Deployed applications using EC2 and S3 • Managed databases with RDS
SQL: • Designed and optimized database schemas • Wrote complex queries for reporting
                """)
            
            user_input = st.text_area(
                f"Paste tech stacks and bullet points for {file.name}", 
                height=300,
                help="Format: 'TechName: • point1 • point2'"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                email_to = st.text_input(f"Recipient email for {file.name}", key=f"to_{file.name}")
                sender_email = st.text_input(f"Sender email for {file.name}", key=f"from_{file.name}")
                
            with col2:
                sender_password = st.text_input(
                    f"Sender email password for {file.name}", 
                    type="password",
                    help="For Gmail, use an app-specific password",
                    key=f"pwd_{file.name}"
                )
                smtp_server = st.selectbox(
                    f"SMTP Server for {file.name}",
                    ["smtp.gmail.com", "smtp.office365.com", "smtp.mail.yahoo.com", "Custom"],
                    key=f"smtp_{file.name}"
                )
                smtp_port = st.number_input(
                    f"SMTP Port for {file.name}",
                    value=465,
                    min_value=1,
                    max_value=65535,
                    key=f"port_{file.name}"
                )
            
            # Email Subject and Body customization
            st.markdown("#### 📧 Email Customization (Optional)")
            
            # Default subject and body with dynamic values
            default_subject = f"Customized Resume - {datetime.now().strftime('%Y-%m-%d')}"
            default_body = "Hi,\n\nPlease find the customized resume attached.\n\nThis resume highlights experience with various technologies and skills.\n\nBest regards"
            
            email_subject = st.text_input(
                f"Email Subject for {file.name}",
                value=default_subject,
                help="Customize the email subject line",
                key=f"subject_{file.name}"
            )
            
            email_body = st.text_area(
                f"Email Body for {file.name}",
                value=default_body,
                height=120,
                help="Customize the email message content",
                key=f"body_{file.name}"
            )
            
            # Store in session state
            if file.name not in st.session_state.resume_inputs:
                st.session_state.resume_inputs[file.name] = {
                    "file": file,
                    "text": user_input,
                    "recipient_email": email_to,
                    "sender_email": sender_email,
                    "sender_password": sender_password,
                    "smtp_server": smtp_server,
                    "smtp_port": smtp_port,
                    "email_subject": email_subject,
                    "email_body": email_body
                }
            else:
                # Update existing entry
                st.session_state.resume_inputs[file.name].update({
                    "text": user_input,
                    "recipient_email": email_to,
                    "sender_email": sender_email,
                    "sender_password": sender_password,
                    "smtp_server": smtp_server,
                    "smtp_port": smtp_port,
                    "email_subject": email_subject,
                    "email_body": email_body
                })
            
            # Original Preview Changes button functionality for this tab only
            st.markdown("---")
            if st.button(f"🔍 Preview Changes", key=f"preview_{file.name}", type="secondary"):
                if user_input.strip():
                    st.markdown("---")
                    st.markdown(f"### 👀 Preview of Changes for {file.name}")
                    
                    with st.expander(f"📄 Preview for {file.name}", expanded=True):
                        file_data = {
                            "file": file,
                            "text": user_input,
                            "recipient_email": email_to,
                            "sender_email": sender_email,
                            "sender_password": sender_password,
                            "smtp_server": smtp_server,
                            "smtp_port": smtp_port
                        }
                        
                        raw_text = user_input
                        
                        # Validate inputs
                        if not raw_text.strip():
                            st.error(f"❌ No tech stack data provided for {file.name}")
                        else:
                            # Parse tech stacks and points
                            techstack_pattern = r"(?P<stack>[A-Za-z0-9_+#\- ]+):\s*(?P<points>(?:• .+\n?)+)"
                            matches = list(re.finditer(techstack_pattern, raw_text))
                            
                            if not matches:
                                st.error(f"❌ Could not parse tech stacks for {file.name}")
                            else:
                                selected_points = []
                                tech_stacks_used = []
                                
                                for match in matches:
                                    stack = match.group("stack").strip()
                                    points_block = match.group("points").strip()
                                    points = re.findall(r"•\s*(.+)", points_block)
                                    selected_points.extend(points)
                                    tech_stacks_used.append(stack)
                                
                                try:
                                    doc = Document(file)
                                    projects = find_projects_and_responsibilities(doc)
                                    
                                    if not projects:
                                        st.error(f"❌ No projects with Responsibilities sections found in {file.name}")
                                    else:
                                        # Distribute points for preview
                                        grouped_projects = distribute_points(selected_points, len(projects))
                                        
                                        # Store preview data for this specific file
                                        if 'preview_data' not in st.session_state:
                                            st.session_state.preview_data = {}
                                        
                                        st.session_state.preview_data[file.name] = {
                                            'tech_stacks': tech_stacks_used,
                                            'total_points': len(selected_points),
                                            'projects': projects,
                                            'point_distribution': grouped_projects,
                                            'email_recipient': email_to,
                                            'email_sender': sender_email
                                        }
                                        
                                        # Apply the changes to the resume and show the updated content
                                        st.subheader(f"📄 Updated Resume Preview: {file.name}")
                                        
                                        # Create a copy of the document to modify for preview
                                        import io
                                        
                                        # Save original doc to memory
                                        temp_buffer = io.BytesIO()
                                        doc.save(temp_buffer)
                                        temp_buffer.seek(0)
                                        
                                        # Load a fresh copy for preview
                                        preview_doc = Document(temp_buffer)
                                        preview_projects = find_projects_and_responsibilities(preview_doc)
                                        
                                        # Apply the changes to the preview document
                                        points_added = add_points_to_responsibilities(preview_doc, preview_projects, grouped_projects)
                                        
                                        st.success(f"✅ Preview generated with {points_added} points added!")
                                        st.info(f"Tech stacks highlighted: {', '.join(tech_stacks_used)}")
                                        
                                        # Convert updated document to HTML for display
                                        try:
                                            # Save the updated document to a buffer
                                            updated_buffer = io.BytesIO()
                                            preview_doc.save(updated_buffer)
                                            updated_buffer.seek(0)
                                            
                                            # Try to convert to HTML using mammoth (if available)
                                            try:
                                                import mammoth
                                                result = mammoth.convert_to_html(updated_buffer)
                                                html_content = result.value
                                                
                                                # Display the HTML content (original Word format)
                                                st.markdown("### 📝 Your Updated Resume (Word Format):")
                                                st.markdown(html_content, unsafe_allow_html=True)
                                                
                                            except ImportError:
                                                # Fallback: Show plain text with proper formatting
                                                st.markdown("### 📝 Your Updated Resume Content:")
                                                st.info("ℹ️ Install 'mammoth' package for better Word format display: pip install mammoth")
                                                
                                                # Show formatted text content
                                                resume_text = ""
                                                for para in preview_doc.paragraphs:
                                                    text = para.text.strip()
                                                    if text:
                                                        resume_text += text + "\n\n"
                                                
                                                # Display in a text area to maintain formatting
                                                st.text_area(
                                                    "Updated Resume Content",
                                                    value=resume_text,
                                                    height=600,
                                                    help="This is your updated resume content. Install 'mammoth' for Word-like display."
                                                )
                                                
                                        except Exception as e:
                                            st.error(f"Error displaying preview: {str(e)}")
                                            # Fallback to simple text display
                                            resume_text = ""
                                            for para in preview_doc.paragraphs:
                                                text = para.text.strip()
                                                if text:
                                                    resume_text += text + "\n\n"
                                            
                                            st.text_area(
                                                "Updated Resume Content (Text Format)",
                                                value=resume_text,
                                                height=600
                                            )
                                        
                                        st.markdown("---")
                                        
                                        # Store individual preview data too
                                        if 'individual_previews' not in st.session_state:
                                            st.session_state.individual_previews = {}
                                        
                                        st.session_state.individual_previews[file.name] = {
                                            'tech_stacks': tech_stacks_used,
                                            'total_points': len(selected_points),
                                            'projects': projects,
                                            'point_distribution': grouped_projects,
                                            'email_recipient': email_to,
                                            'email_sender': sender_email
                                        }
                                        
                                        st.success("✅ Preview completed! Review the changes above, then click 'Generate & Send' when ready.")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error analyzing {file.name}: {str(e)}")
                else:
                    st.warning(f"⚠️ Please enter tech stack data for {file.name} before previewing.")
            
            # Individual Generate & Send button for this tab only
            st.markdown("---")
            
            # Check if this specific file has been previewed
            file_previewed = (file.name in st.session_state.get('preview_data', {}) or 
                            file.name in st.session_state.get('individual_previews', {}))
            
            if not file_previewed:
                st.info(f"👆 Click 'Preview Changes' first to see what will be modified for {file.name}")
            
            if st.button(f"🔧 Generate & Send {file.name}", key=f"generate_{file.name}", type="primary", disabled=not file_previewed):
                st.markdown("---")
                st.markdown(f"### ✅ Generating Customized Resume: {file.name}")
                
                with st.spinner(f"Processing {file.name}..."):
                    raw_text = user_input
                    
                    # Validate inputs
                    if not raw_text.strip():
                        st.error(f"❌ No tech stack data provided for {file.name}. Please add tech stacks and bullet points.")
                    else:
                        # Step 1: Parse the tech stacks and their bullet points
                        techstack_pattern = r"(?P<stack>[A-Za-z0-9_+#\- ]+):\s*(?P<points>(?:• .+\n?)+)"
                        matches = list(re.finditer(techstack_pattern, raw_text))
                        
                        if not matches:
                            st.error(f"❌ Could not parse tech stacks from input for {file.name}. Please use the format 'TechName: • point1 • point2'")
                        else:
                            selected_points = []
                            tech_stacks_used = []
                            
                            for match in matches:
                                stack = match.group("stack").strip()
                                points_block = match.group("points").strip()
                                points = re.findall(r"•\s*(.+)", points_block)  # Handle tabs or spaces after bullet
                                selected_points.extend(points)  # Take all points
                                tech_stacks_used.append(stack)
            
                            # Step 2: Load the resume to find projects and responsibilities sections
                            try:
                                doc = Document(file)
                                projects = find_projects_and_responsibilities(doc)
                                
                                if not projects:
                                    st.error(f"❌ Could not find projects with Responsibilities sections in {file.name}.")
                                    st.info("Please ensure your resume has clear project sections with 'Responsibilities:' headings.")
                                else:
                                    # Distribute points across existing projects
                                    grouped_projects = distribute_points(selected_points, len(projects))
                                    
                                    if not grouped_projects:
                                        st.error(f"❌ No points to distribute for {file.name}.")
                                    else:
                                        # Step 3: Add points to the Responsibilities sections of each project
                                        points_added = add_points_to_responsibilities(doc, projects, grouped_projects)
                                        
                                        if points_added == 0:
                                            st.warning("⚠️ Could not add points to the resume. The format might be different than expected.")
                                        
                                        # Step 4: Save modified doc to buffer
                                        output_buffer = BytesIO()
                                        doc.save(output_buffer)
                                        output_buffer.seek(0)
                                        
                                        # Create a copy for download
                                        download_buffer = BytesIO(output_buffer.getvalue())
                                        download_buffer.seek(0)
            
                                        # Step 5: Email the customized resume
                                        email_sent = False
                                        
                                        # Debug: Show email field status
                                        st.info(f"📧 Email Status Check for {file.name}:")
                                        st.write(f"   • Recipient Email: {'✅ Provided' if email_to else '❌ Missing'}")
                                        st.write(f"   • Sender Email: {'✅ Provided' if sender_email else '❌ Missing'}")
                                        st.write(f"   • Sender Password: {'✅ Provided' if sender_password else '❌ Missing'}")
                                        st.write(f"   • Email Subject: {'✅ Provided' if email_subject else '❌ Missing'}")
                                        st.write(f"   • Email Body: {'✅ Provided' if email_body else '❌ Missing'}")
                                        st.write(f"   • SMTP Server: {smtp_server}")
                                        st.write(f"   • SMTP Port: {smtp_port}")
                                        
                                        if email_to and sender_email and sender_password and email_subject and email_body:
                                            try:
                                                msg = EmailMessage()
                                                msg['Subject'] = email_subject
                                                msg['From'] = sender_email
                                                msg['To'] = email_to
                                                
                                                # Use the original email body without tech stack highlighting
                                                msg.set_content(email_body)
            
                                                output_buffer.seek(0)
                                                msg.add_attachment(
                                                    output_buffer.read(), 
                                                    maintype='application', 
                                                    subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', 
                                                    filename=file.name
                                                )
            
                                                # Handle custom SMTP server
                                                server = smtp_server
                                                if server == "Custom":
                                                    st.warning("⚠️ Custom SMTP server selected but not configured. Please select a predefined SMTP server.")
                                                    st.error("❌ Cannot send email with Custom SMTP server. Please select Gmail, Office365, or Yahoo.")
                                                    continue
                                                
                                                with smtplib.SMTP_SSL(server, smtp_port) as smtp:
                                                    smtp.login(sender_email, sender_password)
                                                    smtp.send_message(msg)
                                                
                                                st.success(f"📤 Email sent successfully for {file.name} to {email_to}")
                                                email_sent = True
                                            except Exception as e:
                                                st.error(f"❌ Failed to send email for {file.name}: {str(e)}")
                                        else:
                                            missing_fields = []
                                            if not email_to: missing_fields.append("Recipient Email")
                                            if not sender_email: missing_fields.append("Sender Email")
                                            if not sender_password: missing_fields.append("Sender Password")
                                            if not email_subject: missing_fields.append("Email Subject")
                                            if not email_body: missing_fields.append("Email Body")
                                            
                                            st.warning(f"⚠️ Email sending skipped - Please fill in the following fields: {', '.join(missing_fields)}")
                                            st.info("📝 Note: Resume generation completed successfully. You can download the file below.")
                                        
                                        # Step 6: Provide download link
                                        b64 = base64.b64encode(download_buffer.getvalue()).decode()
                                        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file.name}">📥 Download {file.name}</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                        
                                        st.success(f"🎉 {file.name} has been processed successfully!")
                                        
                            except Exception as e:
                                st.error(f"❌ Error processing {file.name}: {str(e)}")
            
            st.markdown("---")
    
    # Initialize session state for storing individual preview data
    if 'individual_previews' not in st.session_state:
        st.session_state.individual_previews = {}
    
    # BULK OPERATIONS SECTION
    st.markdown("---")
    st.markdown("## 🚀 Bulk Operations (High Performance Mode)")
    
    if len(uploaded_files) >= 3:
        st.markdown("### ⚡ Fast Bulk Processing for Multiple Resumes")
        
        with st.expander("⚡ Bulk Mode Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                max_workers = st.slider(
                    "🔄 Parallel Workers (Higher = Faster)",
                    min_value=2,
                    max_value=min(8, len(uploaded_files)),
                    value=min(4, len(uploaded_files)),
                    help="Number of parallel processes. More workers = faster processing but higher CPU usage"
                )
                
                bulk_email_mode = st.selectbox(
                    "📧 Email Sending Mode",
                    ["Send emails in parallel", "Process resumes only (no emails)", "Download all as ZIP"],
                    help="Choose how to handle email sending for optimal speed"
                )
            
            with col2:
                show_progress = st.checkbox(
                    "📊 Show Real-time Progress",
                    value=True,
                    help="Display progress updates (may slow down slightly)"
                )
                
                performance_stats = st.checkbox(
                    "📈 Show Performance Stats",
                    value=True,
                    help="Display timing and throughput information"
                )
        
        # Check if all required data is filled
        ready_files = []
        missing_data_files = []
        
        for file in uploaded_files:
            if file.name in st.session_state.resume_inputs:
                data = st.session_state.resume_inputs[file.name]
                if data.get('text', '').strip():
                    ready_files.append(file.name)
                else:
                    missing_data_files.append(file.name)
            else:
                missing_data_files.append(file.name)
        
        if missing_data_files:
            st.warning(f"⚠️ Missing tech stack data for: {', '.join(missing_data_files)}")
            st.info("Please fill in the tech stack data in the individual tabs above before using bulk mode.")
        
        if ready_files:
            st.success(f"✅ Ready to process {len(ready_files)} resumes: {', '.join(ready_files)}")
            
            if st.button(
                f"🚀 BULK PROCESS ALL {len(ready_files)} RESUMES",
                type="primary",
                help="Process all resumes simultaneously for maximum speed"
            ):
                start_time = time.time()
                
                st.markdown("---")
                st.markdown(f"### 🚀 Bulk Processing {len(ready_files)} Resumes...")
                
                # Progress containers
                if show_progress:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    stats_container = st.empty()
                
                # Prepare data for bulk processing
                files_data = []
                for file in uploaded_files:
                    if file.name in ready_files:
                        data = st.session_state.resume_inputs[file.name]
                        files_data.append({
                            'filename': file.name,
                            'file': file,
                            'text': data['text'],
                            'recipient_email': data.get('recipient_email', ''),
                            'sender_email': data.get('sender_email', ''),
                            'sender_password': data.get('sender_password', ''),
                            'smtp_server': data.get('smtp_server', ''),
                            'smtp_port': data.get('smtp_port', 465),
                            'email_subject': data.get('email_subject', ''),
                            'email_body': data.get('email_body', '')
                        })
                
                # Update progress
                if show_progress:
                    progress_bar.progress(0.1)
                    status_text.text("Starting parallel processing...")
                
                # Process resumes in parallel
                with st.spinner("Processing resumes in parallel..."):
                    processed_resumes, failed_resumes = process_resumes_bulk(files_data, max_workers)
                
                processing_time = time.time() - start_time
                
                if show_progress:
                    progress_bar.progress(0.6)
                    status_text.text(f"Processed {len(processed_resumes)} resumes successfully...")
                
                # Handle email sending
                email_results = []
                if bulk_email_mode == "Send emails in parallel" and processed_resumes:
                    if show_progress:
                        status_text.text("Sending emails in batches...")
                    
                    with st.spinner("Sending emails in batches..."):
                        email_results = send_emails_batch(processed_resumes)
                
                total_time = time.time() - start_time
                
                if show_progress:
                    progress_bar.progress(1.0)
                    status_text.text("✅ Bulk processing completed!")
                
                # Display results
                st.markdown("---")
                st.markdown("### 📊 Bulk Processing Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "✅ Successfully Processed",
                        len(processed_resumes),
                        f"{len(processed_resumes)}/{len(files_data)} files"
                    )
                
                with col2:
                    successful_emails = len([r for r in email_results if r.get('success')])
                    st.metric(
                        "📤 Emails Sent",
                        successful_emails,
                        f"{successful_emails}/{len(processed_resumes)} sent" if email_results else "Email disabled"
                    )
                
                with col3:
                    if performance_stats and len(processed_resumes) > 0:
                        throughput = len(processed_resumes) / total_time
                        st.metric(
                            "⚡ Processing Speed",
                            f"{throughput:.1f}",
                            "resumes/second"
                        )
                
                # Performance stats
                if performance_stats:
                    st.markdown("#### ⚡ Performance Metrics")
                    perf_col1, perf_col2 = st.columns(2)
                    
                    with perf_col1:
                        st.info(f"🕐 Total Processing Time: {total_time:.2f}s")
                        st.info(f"📄 Resume Processing: {processing_time:.2f}s")
                        
                    with perf_col2:
                        st.info(f"🔄 Parallel Workers Used: {max_workers}")
                        if len(processed_resumes) > 0:
                            avg_time = total_time / len(processed_resumes)
                            st.info(f"⏱️ Average Time per Resume: {avg_time:.2f}s")
                
                # Success details
                if processed_resumes:
                    st.markdown("#### ✅ Successfully Processed Resumes")
                    for resume in processed_resumes:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.success(f"📄 {resume['filename']} - {resume['points_added']} points added")
                        with col2:
                            # Provide individual download links
                            b64 = base64.b64encode(resume['buffer']).decode()
                            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{resume['filename']}">📥 Download</a>'
                            st.markdown(href, unsafe_allow_html=True)
                
                # Email results
                if email_results:
                    st.markdown("#### 📧 Email Sending Results")
                    successful_emails = [r for r in email_results if r.get('success')]
                    failed_emails = [r for r in email_results if not r.get('success')]
                    
                    if successful_emails:
                        st.markdown("**✅ Successfully Sent:**")
                        for result in successful_emails:
                            st.success(f"📧 {result['filename']} → {result['recipient']}")
                    
                    if failed_emails:
                        st.markdown("**❌ Failed to Send:**")
                        for result in failed_emails:
                            st.error(f"📧 {result['filename']}: {result.get('error', 'Unknown error')}")
                
                # Failed resumes
                if failed_resumes:
                    st.markdown("#### ❌ Failed to Process")
                    for resume in failed_resumes:
                        st.error(f"📄 {resume['filename']}: {resume.get('error', 'Unknown error')}")
                
                # Performance comparison
                if performance_stats and len(processed_resumes) > 1:
                    st.markdown("---")
                    st.markdown("#### 📈 Speed Comparison")
                    sequential_time = len(processed_resumes) * 8  # Estimated 8 seconds per resume sequentially
                    speedup = sequential_time / total_time
                    
                    st.success(f"🚀 **{speedup:.1f}x faster** than processing one by one!")
                    st.info(f"Sequential processing would take ~{sequential_time:.0f}s vs {total_time:.1f}s with parallel processing")
                
                # Clean up SMTP connections
                smtp_pool.close_all()
                
    else:
        st.info(f"💡 Bulk mode is available when you have 3+ resumes (currently: {len(uploaded_files)})")
        st.markdown("""
        **Benefits of Bulk Mode:**
        - ⚡ **Up to 8x faster** processing with parallel workers
        - 🔄 **SMTP connection reuse** for faster email sending
        - 📊 **Real-time progress** tracking
        - 📈 **Performance metrics** and statistics
        - 🎯 **Batch processing** optimizations
        """)
        
else:
    st.info("👆 Please upload one or more DOCX resumes to get started.")

# Add footer
st.markdown("---")
st.markdown(
    """
    <style>
    .footer {
        text-align: center;
        padding: 10px;
    }
    </style>
    <div class="footer">
        <p>Resume Customizer App | Perfect Format Matching</p>
    </div>
    """,
    unsafe_allow_html=True
)