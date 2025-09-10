import streamlit as st
from io import BytesIO
import base64
import hashlib
from performance_monitor import performance_decorator
from validators import TextValidator
from logger import get_logger

logger = get_logger()

class ResumeTabHandler:
    """Handles individual resume tab functionality."""
    
    def __init__(self, resume_manager):
        self.resume_manager = resume_manager

    def render_tab(self, file):
        """Render the tab content for a single resume file."""
        from config import get_default_email_subject, get_default_email_body, get_smtp_servers
        
        # Create unique identifier for this file instance
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        unique_key = f"{file.name}_{file_hash}"
        
        # Defensive: check for resume_inputs existence
        if 'resume_inputs' not in st.session_state:
            st.session_state['resume_inputs'] = {}
        if unique_key not in st.session_state.resume_inputs:
            st.session_state.resume_inputs[unique_key] = {}
        file_data = st.session_state.resume_inputs[unique_key]
        
        # Tech stack input
        st.markdown("#### 📝 Tech Stack & Points")
        st.info("Format: 'TechName: • point1 • point2' or use the block format below")
        
        # Text input for tech stacks
        text_input = st.text_area(
            "Paste your tech stack data here:",
            value=file_data.get('text', ''),
            height=150,
            help="Example: Python: • Developed web applications • Implemented APIs\nJavaScript: • Created UI components • Used React",
            key=f"tech_stack_{unique_key}"
        )
        file_data['text'] = text_input
        
        # Manual points input (optional)
        with st.expander("🔧 Manual Points Override (Optional)", expanded=False):
            manual_text = st.text_area(
                "Manual points (overrides parsed points):",
                value=file_data.get('manual_text', ''),
                height=100,
                help="Enter specific points to add, one per line",
                key=f"manual_points_{unique_key}"
            )
            file_data['manual_text'] = manual_text
        
        # Email configuration
        st.markdown("#### 📧 Email Configuration (Optional)")
        col1, col2 = st.columns(2)
        
        with col1:
            recipient_email = st.text_input(
                "Recipient Email:",
                value=file_data.get('recipient_email', ''),
                help="Email address to send the customized resume to",
                key=f"recipient_email_{unique_key}"
            )
            file_data['recipient_email'] = recipient_email
            
            sender_email = st.text_input(
                "Sender Email:",
                value=file_data.get('sender_email', ''),
                help="Your email address",
                key=f"sender_email_{unique_key}"
            )
            file_data['sender_email'] = sender_email
            
            sender_password = st.text_input(
                "App Password:",
                value=file_data.get('sender_password', ''),
                type="password",
                help="App-specific password for your email account",
                key=f"sender_password_{unique_key}"
            )
            file_data['sender_password'] = sender_password
        
        with col2:
            smtp_server = st.selectbox(
                "SMTP Server:",
                options=get_smtp_servers(),
                index=0,
                help="Select your email provider's SMTP server",
                key=f"smtp_server_{unique_key}"
            )
            file_data['smtp_server'] = smtp_server
            
            smtp_port = st.number_input(
                "SMTP Port:",
                value=file_data.get('smtp_port', 465),
                min_value=1,
                max_value=65535,
                help="SMTP port (usually 465 for SSL or 587 for TLS)",
                key=f"smtp_port_{unique_key}"
            )
            file_data['smtp_port'] = smtp_port
            
            email_subject = st.text_input(
                "Email Subject:",
                value=file_data.get('email_subject', get_default_email_subject()),
                help="Subject line for the email",
                key=f"email_subject_{unique_key}"
            )
            file_data['email_subject'] = email_subject
        
        email_body = st.text_area(
            "Email Body:",
            value=file_data.get('email_body', get_default_email_body()),
            height=100,
            help="Email body text",
            key=f"email_body_{unique_key}"
        )
        file_data['email_body'] = email_body
        
        # Action buttons
        st.markdown("#### 🚀 Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            # Throttle preview button: disable for 1s after click
            preview_key = f"preview_{unique_key}"
            if 'preview_cooldown' not in st.session_state:
                st.session_state['preview_cooldown'] = {}
            cooldown = st.session_state['preview_cooldown'].get(preview_key, 0)
            import time as _time
            now = _time.time()
            if now > cooldown:
                if st.button("🔍 Preview Changes", key=preview_key):
                    st.session_state['preview_cooldown'][preview_key] = now + 1.0  # 1 second cooldown
                    self.handle_preview(file, text_input, manual_text)
            else:
                st.button("🔍 Preview Changes (Wait)", key=preview_key+"_wait", disabled=True)
        
        with col2:
            async_mode = st.checkbox("Process in background (Celery)", key=f"async_mode_{unique_key}")
            if st.button("✅ Generate & Send", key=f"generate_{unique_key}"):
                # Prepare file data for processing
                file_data_for_processing = {
                    'filename': file.name,
                    'file': file,
                    'text': text_input,
                    'manual_text': manual_text,
                    'recipient_email': recipient_email,
                    'sender_email': sender_email,
                    'sender_password': sender_password,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'email_subject': email_subject,
                    'email_body': email_body
                }
                if async_mode:
                    task = self.resume_manager.process_single_resume_async(file_data_for_processing)
                    st.success(f"🎫 Submitted to background queue. Task ID: {task.id}")
                    if st.button("🔄 Check Status", key=f"check_status_{unique_key}"):
                        status = self.resume_manager.get_async_result(task.id)
                        st.info(f"Task {task.id} status: {status['state']}")
                        if status['result']:
                            result = status['result']
                            if result.get('success'):
                                st.success(f"✅ Resume processed with {result['points_added']} points added!")
                                # Download link
                                b64 = base64.b64encode(result['buffer']).decode()
                                link = f'<a href="data:application/octet-stream;base64,{b64}" download="{file.name}">📥 Download</a>'
                                st.markdown(link, unsafe_allow_html=True)
                            else:
                                st.error(f"❌ {result.get('error','Unknown error')}")
                else:
                    self.handle_generation(file, file_data_for_processing)

    @performance_decorator("preview_generation")
    def handle_preview(self, file, user_input, manual_text=""):
        """Handle preview generation for a single file."""
        if not user_input.strip() and not manual_text:
            st.warning(f"⚠️ Please enter tech stack data for {file.name} before previewing.")
            return

        from validators import get_rate_limiter
        user_id = st.session_state.get('user_id', 'anonymous')
        rate_limiter = get_rate_limiter()
        if rate_limiter.is_rate_limited(user_id, 'preview', max_requests=10, time_window=60):
            st.error("⚠️ Too many preview requests. Please wait a moment before trying again.")
            return

        st.markdown("---")
        st.markdown(f"### 👀 Preview of Changes for {file.name}")
        
        with st.expander(f"📄 Preview for {file.name}", expanded=True):
            try:
                result = self.resume_manager.generate_preview(file, user_input, manual_text)
                if not result['success']:
                    st.error(f"❌ {result['error']}")
                    if 'errors' in result and result['errors']:
                        for err in result['errors']:
                            st.error(f"❌ {err}")
                    return

                st.success(f"✅ Preview generated with {result['points_added']} points added!")
                st.info(f"Tech stacks highlighted: {', '.join(result['tech_stacks_used'])}")
                st.info(f"📂 Number of projects in resume: {result['projects_count']}")

                st.markdown("### 📊 Points Distribution by Project")
                for project, mapping in result['project_points_mapping'].items():
                    with st.expander(f"Project: {project}"):
                        for tech, points in mapping.items():
                            st.markdown(f"**{tech}**")
                            for p in points:
                                st.markdown(f"- {p}")
                            st.markdown("")

                # Display document preview
                try:
                    import mammoth
                    buffer = BytesIO()
                    result['preview_doc'].save(buffer)
                    buffer.seek(0)
                    html = mammoth.convert_to_html(buffer).value
                    st.markdown("### 📝 Your Updated Resume (Word Format):", unsafe_allow_html=True)
                    st.markdown(html, unsafe_allow_html=True)
                except ImportError:
                    st.markdown("### 📝 Your Updated Resume Content:")
                    st.info("Install 'mammoth' for better Word format display: pip install mammoth")
                    st.text_area("Updated Resume Content", value=result['preview_content'], height=600)

                st.success("✅ Preview completed! Review changes above.")
            except Exception as e:
                st.error(f"❌ Error generating preview: {e}")

    @performance_decorator("resume_generation")
    def handle_generation(self, file, file_data):
        """Handle resume generation and email sending with async/caching integration."""
        from validators import get_rate_limiter
        user_id = st.session_state.get('user_id', 'anonymous')
        rate_limiter = get_rate_limiter()
        if rate_limiter.is_rate_limited(user_id, 'generation', max_requests=20, time_window=300):
            st.error("⚠️ Too many generation requests. Please wait before trying again.")
            return

        st.markdown("---")
        st.markdown(f"### ✅ Generating Customized Resume: {file.name}")
        logger.log_user_action("resume_generation", file_name=file.name)

        status_placeholder = st.empty()
        def progress_callback(msg):
            status_placeholder.info(msg)

        with st.spinner(f"Processing {file.name}…"):
            result = self.resume_manager.process_single_resume(file_data, progress_callback=progress_callback)
            if not result['success']:
                st.error(f"❌ {result['error']}")
                return

            st.success(f"✅ Resume processed with {result['points_added']} points added!")
            email_data = result['email_data']
            valid = self.resume_manager.validate_email_config(email_data)['valid']

            if valid:
                try:
                    email_res = self.resume_manager.send_single_email(
                        email_data['smtp_server'], email_data['smtp_port'],
                        email_data['sender'], email_data['password'],
                        email_data['recipient'], email_data['subject'],
                        email_data['body'], result['buffer'], file.name
                    )
                    if email_res['success']:
                        st.success(f"📤 Email sent to {email_data['recipient']}")
                    else:
                        st.error(f"❌ Email failed: {email_res['error']}")
                except Exception as e:
                    st.error(f"❌ Email sending failed: {e}")
            else:
                missing = self.resume_manager.validate_email_config(email_data)['missing_fields']
        # Show audit log if available
        if hasattr(self.resume_manager, '_audit_log'):
            with st.expander("🔍 Audit Log", expanded=False):
                for entry in self.resume_manager._audit_log[-5:]:
                    st.code(str(entry))
                st.warning(f"⚠️ Email skipped—Missing: {', '.join(missing)}")

            b64 = base64.b64encode(result['buffer']).decode()
            link = f'<a href="data:application/octet-stream;base64,{b64}" download="{file.name}">📥 Download</a>'
            st.markdown(link, unsafe_allow_html=True)
            st.success(f"🎉 {file.name} processed successfully!")