# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **Resume Customizer** application built with Streamlit that automates the process of customizing multiple resumes and sending them via email. The application:

1. Accepts multiple .docx resume files as input
2. Allows users to specify tech stacks and bullet points for each resume
3. Automatically inserts selected bullet points into the "Projects" section of each resume
4. Sends customized resumes via email to specified recipients
5. Provides download links for the modified resumes

## Architecture

### Core Components

- **`app.py`**: Single-file Streamlit application containing all functionality
  - File upload handling for multiple .docx files
  - Text parsing using regex to extract tech stacks and bullet points
  - Document manipulation using `python-docx` library
  - Email sending via SMTP (Gmail)
  - Base64 encoding for file downloads

### Key Dependencies

- `streamlit`: Web UI framework
- `python-docx`: Word document manipulation
- `smtplib`: Built-in email sending
- `re`: Built-in regex for text parsing
- `base64`: Built-in encoding for downloads
- `io.BytesIO`: Built-in memory buffer handling

### Data Flow

1. **Input Phase**: Users upload .docx files and provide tech stack information
2. **Parsing Phase**: Regex extracts tech stacks and bullet points from user input
3. **Selection Phase**: Algorithm selects first 2 points per tech stack, groups into blocks of 6
4. **Document Modification**: Finds "Projects" heading and inserts bullet points
5. **Output Phase**: Saves to memory buffer, emails attachment, provides download

## Development Commands

### Running the Application
```powershell
# Install dependencies (no requirements.txt exists, install manually)
pip install streamlit python-docx

# Run the Streamlit application
streamlit run app.py
```

### Development Workflow
```powershell
# Check application health
streamlit run app.py --server.headless true --server.port 8501

# For development with auto-reload
streamlit run app.py --server.runOnSave true
```

## Critical Implementation Details

### Text Parsing Logic
The application uses a specific regex pattern to parse tech stack input:
```regex
(?P<stack>[A-Za-z0-9_+#\- ]+):\s*(?P<points>(?:- .+\n?)+)
```
This expects input format:
```
TechStack1:
- Point 1
- Point 2
TechStack2:
- Point 3
- Point 4
```

### Document Modification Strategy
- **Requirement**: All resume files MUST contain a "Projects" heading (case-insensitive)
- **Insertion Point**: Content is inserted immediately after the "Projects" heading
- **Grouping**: Bullet points are grouped into blocks of 6 and inserted as separate paragraphs

### Email Configuration
- **SMTP Server**: Hardcoded to Gmail (`smtp.gmail.com:465`)
- **Security**: Uses SSL connection
- **Authentication**: Requires sender email and password (app-specific password recommended)

## Common Issues and Solutions

### Resume Processing Failures
- **Missing "Projects" section**: Application will show error and skip the file
- **Document corruption**: Ensure .docx files are valid Word documents

### Email Delivery Issues
- **Gmail authentication**: Users need app-specific passwords for Gmail accounts
- **SMTP restrictions**: Currently only supports Gmail; other providers require code changes

### Text Parsing Problems
- **Format sensitivity**: Input must exactly match expected format with colons and hyphens
- **Character encoding**: Application handles standard text characters

## File Structure Notes

This is a minimal single-file application with:
- No requirements.txt (dependencies must be installed manually)
- No configuration files
- No test files
- Git repository present but minimal commit history
- Single Python file contains all logic

## Security Considerations

- Email passwords are handled in Streamlit text inputs (not permanently stored)
- No input validation on email addresses
- Document processing happens in memory (no temporary file storage)
- Base64 encoding used for secure file downloads
