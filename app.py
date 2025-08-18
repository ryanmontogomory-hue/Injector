import streamlit as st
from docx import Document
from io import BytesIO
import re
import base64
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="Resume Customizer", layout="wide")
st.title("📝 Bulk Resume Customizer + Email Sender")

uploaded_files = st.file_uploader("Upload one or more .docx resumes", type="docx", accept_multiple_files=True)

resume_inputs = {}

if uploaded_files:
    st.markdown("### 🔽 Paste Tech Stack + Points for Each Resume")
    for file in uploaded_files:
        with st.expander(f"➕ {file.name}"):
            user_input = st.text_area(f"Paste tech stacks and bullet points for {file.name}", height=300)
            email_to = st.text_input(f"Recipient email for {file.name}")
            sender_email = st.text_input(f"Sender email for {file.name}")
            sender_password = st.text_input(f"Sender email password for {file.name}", type="password")

            resume_inputs[file.name] = {
                "file": file,
                "text": user_input,
                "recipient_email": email_to,
                "sender_email": sender_email,
                "sender_password": sender_password
            }

    if st.button("🔧 Generate & Send Customized Resumes"):
        st.markdown("---")
        st.markdown("### ✅ Customized Resumes")

        for filename, data in resume_inputs.items():
            file = data['file']
            raw_text = data['text']
            recipient_email = data['recipient_email']
            sender_email = data['sender_email']
            sender_password = data['sender_password']

            # Step 1: Parse the tech stacks and their bullet points
            techstack_pattern = r"(?P<stack>[A-Za-z0-9_+#\- ]+):\s*(?P<points>(?:- .+\n?)+)"
            matches = re.finditer(techstack_pattern, raw_text)

            selected_points = []
            for match in matches:
                stack = match.group("stack").strip()
                points_block = match.group("points").strip()
                points = re.findall(r"- (.+)", points_block)
                selected_points.extend(points[:2])  # Take first 2 points per stack

            # Step 2: Group selected points into project blocks
            grouped_projects = []
            for i in range(0, len(selected_points), 6):
                block = selected_points[i:i+6]
                if block:
                    grouped_projects.append(block)

            # Step 3: Load and modify the resume
            doc = Document(file)
            projects_heading_found = False
            for para in doc.paragraphs:
                if para.text.strip().lower() == "projects":
                    projects_heading_found = True
                    insert_index = doc.paragraphs.index(para) + 1
                    break

            if not projects_heading_found:
                st.error(f"❌ 'Projects' section not found in {filename}. Please ensure the heading exists.")
                continue

            for project in grouped_projects:
                doc.paragraphs.insert(insert_index, doc.add_paragraph(""))
                doc.paragraphs.insert(insert_index, doc.add_paragraph("• " + "\n• ".join(project)))
                insert_index += len(project) + 2

            # Step 4: Save modified doc to buffer
            output_buffer = BytesIO()
            doc.save(output_buffer)
            output_buffer.seek(0)

            # Step 5: Email the customized resume
            if recipient_email and sender_email and sender_password:
                try:
                    msg = EmailMessage()
                    msg['Subject'] = 'Customized Resume'
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg.set_content('Hi, please find the customized resume attached.')

                    output_buffer.seek(0)
                    msg.add_attachment(output_buffer.read(), maintype='application', subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', filename=f"updated_{filename}")

                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                        smtp.login(sender_email, sender_password)
                        smtp.send_message(msg)
                    st.success(f"📤 Email sent successfully for {filename} to {recipient_email}")
                except Exception as e:
                    st.error(f"❌ Failed to send email for {filename}: {e}")

            # Step 6: Provide download link
            b64 = base64.b64encode(output_buffer.read()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="updated_{filename}">📥 Download updated {filename}</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.markdown("---")