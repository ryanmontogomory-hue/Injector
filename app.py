"""
Main application file for Resume Customizer - Refactored version.
Uses modular components for better maintainability and code organization.
"""

import streamlit as st
import base64
import time
from io import BytesIO

# Import our custom modules
from config import (
    get_app_config, get_smtp_servers, get_default_email_subject, 
    get_default_email_body, UI_CONFIG, APP_CONFIG
)
from text_parser import parse_input_text, LegacyParser
from resume_processor import get_resume_manager
from email_handler import get_email_manager
from logger import get_logger, display_logs_in_sidebar
from validators import get_file_validator, EmailValidator, TextValidator, get_rate_limiter, validate_session_state
from performance_monitor import get_performance_monitor, display_performance_metrics, performance_decorator
from retry_handler import get_retry_handler

# Initialize components
logger = get_logger()
file_validator = get_file_validator()
performance_monitor = get_performance_monitor()
rate_limiter = get_rate_limiter()

# Get configuration
config = get_app_config()

# Set page configuration
st.set_page_config(page_title=config["page_title"], layout=config["layout"])

# Initialize managers
resume_manager = get_resume_manager()
email_manager = get_email_manager()


class UIComponents:
    """Handles UI component rendering and interactions."""
    
    @staticmethod
    def render_sidebar():
        """Render the application sidebar with instructions."""
        with st.sidebar:
            st.header("ℹ️ Instructions")
            st.markdown(UI_CONFIG["sidebar_instructions"])
            
            st.header("👀 Preview Features")
            st.markdown(UI_CONFIG["preview_features"])
            
            st.header("🎯 Project Selection")
            st.markdown(UI_CONFIG["project_selection_info"])
            
            st.header("🔍 Format Preservation")
            st.markdown(UI_CONFIG["format_preservation_info"])
            
            st.header("🔒 Security Note")
            st.markdown(UI_CONFIG["security_note"])

    @staticmethod
    def render_file_upload():
        """Render the file upload component with validation."""
        uploaded_files = st.file_uploader(
            UI_CONFIG["file_upload_help"], 
            type="docx", 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            # Validate uploaded files
            validation_result = file_validator.validate_batch(uploaded_files)
            
            if not validation_result['valid']:
                for error in validation_result['summary']['errors']:
                    st.error(f"❌ {error}")
                return None
            
            # Show validation warnings
            for warning in validation_result['summary']['warnings']:
                st.warning(f"⚠️ {warning}")
            
            # Show file summary
            summary = validation_result['summary']
            if summary['valid_files'] > 0:
                st.success(
                    f"✅ {summary['valid_files']} valid files uploaded "
                    f"({summary['total_size_mb']:.1f}MB total)"
                )
                logger.log_user_action("file_upload", files_count=summary['valid_files'], total_size_mb=summary['total_size_mb'])
        
        return uploaded_files

    @staticmethod
    def render_example_format():
        """Render the example format section."""
        with st.expander("💡 Example Input Format"):
            st.code(UI_CONFIG["example_format"])

    @staticmethod
    def render_email_fields(file_name):
        """Render email configuration fields for a file with validation."""
        col1, col2 = st.columns(2)
        
        with col1:
            email_to = st.text_input(f"Recipient email for {file_name}", key=f"to_{file_name}")
            if email_to:
                validation = EmailValidator.validate_email(email_to)
                if not validation['valid']:
                    st.error(f"Invalid recipient email: {', '.join(validation['errors'])}")
            
            sender_email = st.text_input(f"Sender email for {file_name}", key=f"from_{file_name}")
            if sender_email:
                validation = EmailValidator.validate_email(sender_email)
                if not validation['valid']:
                    st.error(f"Invalid sender email: {', '.join(validation['errors'])}")
            
        with col2:
            sender_password = st.text_input(
                f"Sender email password for {file_name}", 
                type="password",
                help="For Gmail, use an app-specific password",
                key=f"pwd_{file_name}"
            )
            smtp_server = st.selectbox(
                f"SMTP Server for {file_name}",
                get_smtp_servers(),
                key=f"smtp_{file_name}"
            )
            smtp_port = st.number_input(
                f"SMTP Port for {file_name}",
                value=465,
                min_value=1,
                max_value=65535,
                key=f"port_{file_name}"
            )
        
        return email_to, sender_email, sender_password, smtp_server, smtp_port

    @staticmethod
    def render_email_customization(file_name):
        """Render email customization fields."""
        st.markdown("#### 📧 Email Customization (Optional)")
        
        email_subject = st.text_input(
            f"Email Subject for {file_name}",
            value=get_default_email_subject(),
            help="Customize the email subject line",
            key=f"subject_{file_name}"
        )
        
        email_body = st.text_area(
            f"Email Body for {file_name}",
            value=get_default_email_body(),
            height=120,
            help="Customize the email message content",
            key=f"body_{file_name}"
        )
        
        return email_subject, email_body

    @staticmethod
    def render_manual_points_editor(file_name, user_input):
        """Render the manual points editor section."""
        with st.expander("✏️ Optional: Edit points before preview", expanded=False):
            edit_enable_key = f"edit_points_enable_{file_name}"
            edit_text_key = f"edit_points_text_{file_name}"
            
            edit_points_enabled = st.checkbox(
                "Enable manual edit of points (one point per line)",
                key=edit_enable_key
            )
            
            if edit_points_enabled:
                # Initialize default editable points from current input once
                if edit_text_key not in st.session_state:
                    # Use legacy parser for backward compatibility
                    legacy_parser = LegacyParser()
                    default_points, _ = legacy_parser.extract_points_from_legacy_format(user_input or "")
                    st.session_state[edit_text_key] = "\n".join(default_points)
                
                st.text_area(
                    "Points to add (one per line)",
                    key=edit_text_key,
                    height=200,
                    help="These points will be used instead of the auto-parsed ones when previewing or generating."
                )
                
                if st.button("Reset edited points to parsed defaults", key=f"reset_points_{file_name}"):
                    legacy_parser = LegacyParser()
                    default_points, _ = legacy_parser.extract_points_from_legacy_format(user_input or "")
                    st.session_state[edit_text_key] = "\n".join(default_points)
                    st.success("✅ Points reset to parsed defaults.")
                    st.rerun()
        
        return edit_points_enabled

    @staticmethod
    def render_bulk_settings(num_files):
        """Render bulk processing settings."""
        with st.expander("⚡ Bulk Mode Settings", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                max_workers = st.slider(
                    "🔄 Parallel Workers (Higher = Faster)",
                    min_value=2,
                    max_value=min(config["max_workers_limit"], num_files),
                    value=min(config["max_workers_default"], num_files),
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
        
        return max_workers, bulk_email_mode, show_progress, performance_stats


class ResumeTabHandler:
    """Handles individual resume tab functionality."""
    
    def __init__(self, resume_manager):
        self.resume_manager = resume_manager
        self.ui = UIComponents()

    @performance_decorator("preview_generation")
    def handle_preview(self, file, user_input, manual_text=""):
        """Handle preview generation for a single file."""
        if not user_input.strip() and not manual_text:
            st.warning(f"⚠️ Please enter tech stack data for {file.name} before previewing.")
            return
        
        # Rate limiting check
        user_id = st.session_state.get('user_id', 'anonymous')
        if rate_limiter.is_rate_limited(user_id, 'preview', max_requests=10, time_window=60):
            st.error("⚠️ Too many preview requests. Please wait a moment before trying again.")
            return
        
        st.markdown("---")
        st.markdown(f"### 👀 Preview of Changes for {file.name}")
        
        with st.expander(f"📄 Preview for {file.name}", expanded=True):
            try:
                preview_result = self.resume_manager.generate_preview(file, user_input, manual_text)
                
                if not preview_result['success']:
                    st.error(f"❌ {preview_result['error']}")
                    return
                
                st.success(f"✅ Preview generated with {preview_result['points_added']} points added!")
                st.info(f"Tech stacks highlighted: {', '.join(preview_result['tech_stacks_used'])}")
                st.info(f"📂 Number of projects in resume: {preview_result['projects_count']}")
                
                # Display which points are added to which project
                st.markdown("### 📊 Points Distribution by Project")
                for project_title, tech_points in preview_result['project_points_mapping'].items():
                    with st.expander(f"Project: {project_title}"):
                        for tech_name, points in tech_points.items():
                            st.markdown(f"**{tech_name}**")
                            for point in points:
                                st.markdown(f"- {point}")
                            st.markdown("")
                st.markdown("---")
                
                # Display preview content
                try:
                    import mammoth
                    # Save preview document to buffer for mammoth
                    preview_buffer = BytesIO()
                    preview_result['preview_doc'].save(preview_buffer)
                    preview_buffer.seek(0)
                    
                    result = mammoth.convert_to_html(preview_buffer)
                    st.markdown("### 📝 Your Updated Resume (Word Format):")
                    st.markdown(result.value, unsafe_allow_html=True)
                    
                except ImportError:
                    # Fallback to text display
                    st.markdown("### 📝 Your Updated Resume Content:")
                    st.info("ℹ️ Install 'mammoth' package for better Word format display: pip install mammoth")
                    
                    st.text_area(
                        "Updated Resume Content",
                        value=preview_result['preview_content'],
                        height=600,
                        help="This is your updated resume content. Install 'mammoth' for Word-like display."
                    )
                
                st.success("✅ Preview completed! Review the changes above, then click 'Generate & Send' when ready.")
                
            except Exception as e:
                st.error(f"❌ Error generating preview: {str(e)}")

    @performance_decorator("resume_generation")
    def handle_generation(self, file, file_data):
        """Handle resume generation and email sending."""
        # Rate limiting check
        user_id = st.session_state.get('user_id', 'anonymous')
        if rate_limiter.is_rate_limited(user_id, 'generation', max_requests=20, time_window=300):
            st.error("⚠️ Too many generation requests. Please wait before trying again.")
            return
        
        st.markdown("---")
        st.markdown(f"### ✅ Generating Customized Resume: {file.name}")
        
        logger.log_user_action("resume_generation", file_name=file.name)
        
        with st.spinner(f"Processing {file.name}..."):
            # Process the resume
            result = self.resume_manager.process_single_resume(file_data)
            
            if not result['success']:
                st.error(f"❌ {result['error']}")
                return
            
            st.success(f"✅ Resume processed with {result['points_added']} points added!")
            
            # Handle email sending
            email_data = result['email_data']
            validation_result = self.resume_manager.validate_email_config(email_data)
            
            if validation_result['valid']:
                try:
                    email_result = self.resume_manager.send_single_email(
                        email_data['smtp_server'],
                        email_data['smtp_port'],
                        email_data['sender'],
                        email_data['password'],
                        email_data['recipient'],
                        email_data['subject'],
                        email_data['body'],
                        result['buffer'],
                        file.name
                    )
                    
                    if email_result['success']:
                        st.success(f"📤 Email sent successfully to {email_data['recipient']}")
                    else:
                        st.error(f"❌ Failed to send email: {email_result['error']}")
                        
                except Exception as e:
                    st.error(f"❌ Email sending failed: {str(e)}")
            else:
                st.warning(f"⚠️ Email sending skipped - Missing fields: {', '.join(validation_result['missing_fields'])}")
            
            # Provide download link
            b64 = base64.b64encode(result['buffer']).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file.name}">📥 Download {file.name}</a>'
            st.markdown(href, unsafe_allow_html=True)
            
            st.success(f"🎉 {file.name} has been processed successfully!")

    def render_tab(self, file):
        """Render a complete tab for a single file."""
        st.subheader(f"Customize {file.name}")
        
        # Example format
        self.ui.render_example_format()
        
        # Main text input with validation
        user_input = st.text_area(
            f"Enter ONLY the new tech stack points you want to add. These will be distributed across your projects using round-robin logic.{file.name}",
            height=300,
            help="Enter ONLY the new tech stack points you want to add. These will be distributed across your projects using round-robin logic."
        )
        st.info("📝 **Input Format**: Provide your tech stack points in one of these formats:\n\n**Format 1 (Recommended):**\n```\nPython\n• Developed REST APIs using Django\n• Built data processing pipelines\n\nJavaScript\n• Created React components\n• Implemented Node.js services\n```\n\n**Format 2:**\n```\nPython: • Developed REST APIs • Built data pipelines\nJavaScript: • Created React components • Node.js services\n```\n\n⚠️ **Important**: Only the points YOU provide will be added to your resume. No existing content will be extracted or modified.")
        
        # Validate text input
        if user_input:
            text_validation = TextValidator.validate_text_input(user_input, "Tech stack input")
            if not text_validation['valid']:
                for error in text_validation['errors']:
                    st.error(f"❌ {error}")
            for warning in text_validation['warnings']:
                st.warning(f"⚠️ {warning}")
        
        # Manual points editor
        manual_enabled = self.ui.render_manual_points_editor(file.name, user_input)
        manual_text = st.session_state.get(f"edit_points_text_{file.name}", "").strip() if manual_enabled else ""
        
        # Email configuration
        email_to, sender_email, sender_password, smtp_server, smtp_port = self.ui.render_email_fields(file.name)
        email_subject, email_body = self.ui.render_email_customization(file.name)
        
        # Store in session state
        file_data = {
            "filename": file.name,
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
        
        if file.name not in st.session_state.resume_inputs:
            st.session_state.resume_inputs[file.name] = file_data
        else:
            st.session_state.resume_inputs[file.name].update(file_data)
        
        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(f"🔍 Preview Changes", key=f"preview_{file.name}", type="secondary"):
                self.handle_preview(file, user_input, manual_text)
        
        with col2:
            if st.button(f"🔧 Generate & Send {file.name}", key=f"generate_{file.name}", type="primary"):
                if not user_input.strip() and not manual_text:
                    st.error(f"❌ No tech stack data provided for {file.name}.")
                else:
                    # Override with manual text if provided
                    if manual_text:
                        file_data["text"] = manual_text
                    self.handle_generation(file, file_data)


class BulkProcessor:
    """Handles bulk processing operations."""
    
    def __init__(self, resume_manager):
        self.resume_manager = resume_manager
        self.ui = UIComponents()

    @performance_decorator("bulk_processing")
    def process_bulk_resumes(self, ready_files, files_data, max_workers, show_progress, performance_stats, bulk_email_mode):
        """Process multiple resumes in bulk mode."""
        # Rate limiting check
        user_id = st.session_state.get('user_id', 'anonymous')
        if rate_limiter.is_rate_limited(user_id, 'bulk_processing', max_requests=5, time_window=600):
            st.error("⚠️ Bulk processing rate limit reached. Please wait before trying again.")
            return
        
        start_time = time.time()
        logger.log_user_action("bulk_processing", files_count=len(ready_files), max_workers=max_workers)
        
        st.markdown("---")
        st.markdown(f"### 🚀 Bulk Processing {len(ready_files)} Resumes...")
        
        # Progress containers
        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        # Update progress
        if show_progress:
            progress_bar.progress(0.1)
            status_text.text("Starting parallel processing...")
        
        # Process resumes in parallel
        with st.spinner("Processing resumes in parallel..."):
            processed_resumes, failed_resumes = self.resume_manager.process_bulk_resumes(
                files_data, max_workers
            )
        
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
                email_results = self.resume_manager.send_batch_emails(processed_resumes)
        
        total_time = time.time() - start_time
        
        if show_progress:
            progress_bar.progress(1.0)
            status_text.text("✅ Bulk processing completed!")
        
        self.display_bulk_results(processed_resumes, failed_resumes, email_results, 
                                files_data, total_time, processing_time, max_workers, performance_stats)

    def display_bulk_results(self, processed_resumes, failed_resumes, email_results, 
                           files_data, total_time, processing_time, max_workers, performance_stats):
        """Display bulk processing results."""
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
            self.display_performance_stats(total_time, processing_time, max_workers, len(processed_resumes))
        
        # Success details
        self.display_success_details(processed_resumes)
        
        # Email results
        self.display_email_results(email_results)
        
        # Failed resumes
        self.display_failed_resumes(failed_resumes)

    def display_performance_stats(self, total_time, processing_time, max_workers, num_processed):
        """Display detailed performance statistics."""
        st.markdown("#### ⚡ Performance Metrics")
        perf_col1, perf_col2 = st.columns(2)
        
        with perf_col1:
            st.info(f"🕐 Total Processing Time: {total_time:.2f}s")
            st.info(f"📄 Resume Processing: {processing_time:.2f}s")
            
        with perf_col2:
            st.info(f"🔄 Parallel Workers Used: {max_workers}")
            if num_processed > 0:
                avg_time = total_time / num_processed
                st.info(f"⏱️ Average Time per Resume: {avg_time:.2f}s")

    def display_success_details(self, processed_resumes):
        """Display details of successfully processed resumes."""
        if processed_resumes:
            st.markdown("#### ✅ Successfully Processed Resumes")
            for resume in processed_resumes:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.success(f"📄 {resume['filename']} - {resume['points_added']} points added")
                with col2:
                    # Provide individual download links
                    b64 = base64.b64encode(resume['buffer']).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{resume["filename"]}">📥 Download</a>'
                    st.markdown(href, unsafe_allow_html=True)

    def display_email_results(self, email_results):
        """Display email sending results."""
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

    def display_failed_resumes(self, failed_resumes):
        """Display failed resume processing results."""
        if failed_resumes:
            st.markdown("#### ❌ Failed to Process")
            for resume in failed_resumes:
                st.error(f"📄 {resume['filename']}: {resume.get('error', 'Unknown error')}")


def main():
    """Main application function."""
    # Validate session state for security
    validate_session_state()
    
    # Initialize session state
    if 'resume_inputs' not in st.session_state:
        st.session_state.resume_inputs = {}
    
    # Generate user ID for rate limiting
    if 'user_id' not in st.session_state:
        import uuid
        st.session_state.user_id = str(uuid.uuid4())
    
    logger.info("Application started")
    
    # Initialize UI components
    ui = UIComponents()
    tab_handler = ResumeTabHandler(resume_manager)
    bulk_processor = BulkProcessor(resume_manager)
    
    # Application title
    st.title(config["title"])
    
    # Render sidebar with enhanced features
    ui.render_sidebar()
    display_logs_in_sidebar()
    display_performance_metrics()
    
    # File upload
    uploaded_files = ui.render_file_upload()
    
    if uploaded_files:
        st.markdown("### 🔽 Paste Tech Stack + Points for Each Resume")
        
        # Create tabs for individual files
        tabs = st.tabs([file.name for file in uploaded_files])
        
        for i, file in enumerate(uploaded_files):
            with tabs[i]:
                tab_handler.render_tab(file)
        
        # Bulk operations section
        st.markdown("---")
        st.markdown("## 🚀 Bulk Operations (High Performance Mode)")
        
        if len(uploaded_files) >= config["bulk_mode_threshold"]:
            st.markdown("### ⚡ Fast Bulk Processing for Multiple Resumes")
            
            # Bulk settings
            max_workers, bulk_email_mode, show_progress, performance_stats = ui.render_bulk_settings(len(uploaded_files))
            
            # Check readiness
            ready_files, missing_data_files = check_file_readiness(uploaded_files)
            
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
                    # Prepare data for bulk processing
                    files_data = prepare_bulk_data(uploaded_files, ready_files)
                    
                    # Process in bulk
                    bulk_processor.process_bulk_resumes(
                        ready_files, files_data, max_workers, show_progress, 
                        performance_stats, bulk_email_mode
                    )
        else:
            st.info(f"💡 Bulk mode is available when you have {config['bulk_mode_threshold']}+ resumes (currently: {len(uploaded_files)})")
            st.markdown(UI_CONFIG["bulk_benefits"])
    
    else:
        st.info("👆 Please upload one or more DOCX resumes to get started.")
    
    # Footer with enhanced information
    st.markdown("---")
    
    # Performance summary
    if st.checkbox("Show Performance Summary", value=False):
        summary = performance_monitor.get_performance_summary()
        if summary.get('system'):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CPU Usage", f"{summary['system'].get('cpu_percent', 0):.1f}%")
            with col2:
                st.metric("Memory Usage", f"{summary['system'].get('memory_percent', 0):.1f}%")
            with col3:
                st.metric("Memory Used", f"{summary['system'].get('memory_used_mb', 0):.0f}MB")
    
    st.markdown(
        """
        <style>
        .footer {
            text-align: center;
            padding: 10px;
        }
        </style>
        <div class="footer">
            <p>Resume Customizer Pro | Enhanced with Security & Performance Monitoring</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def check_file_readiness(uploaded_files):
    """Check which files are ready for bulk processing."""
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
    
    return ready_files, missing_data_files


def prepare_bulk_data(uploaded_files, ready_files):
    """Prepare data for bulk processing."""
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
    return files_data


if __name__ == "__main__":
    main()
