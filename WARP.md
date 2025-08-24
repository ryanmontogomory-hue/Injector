# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## 📋 Essential Development Commands

### Quick Start & Development
```bash
# Development setup
pip install -r requirements.txt
streamlit run app.py

# Test streamlit app basics
python test_streamlit_app.py  # Basic functionality tests
```

### Testing & Validation
```bash
# Validate setup and dependencies
python -c "import streamlit; from docx import Document; print('Core dependencies OK')"

# Test bulk processing functionality
python -c "from concurrent.futures import ThreadPoolExecutor; print('Parallel processing OK')"
```

## 🏗️ Architecture Overview

### Core Application Structure
This is a **single-user resume customization tool** built with Streamlit, focused on simplicity and performance:

**Features**: Resume processing, email automation, bulk operations, parallel processing

### Key Architectural Components

#### 1. **Resume Processing Engine**
- **Core Functions**: `find_projects_and_responsibilities()`, `add_points_to_responsibilities()`, `distribute_points()`
- **Purpose**: Intelligent parsing of resume structure and enhancement with tech stack points
- **Features**: Format preservation, bullet point detection, project identification
- **Strategy**: Focus on top 3 projects for maximum impact

#### 2. **Email Automation System**
- **Core Classes**: `SMTPConnectionPool`
- **Purpose**: Reliable email sending with SMTP connection pooling
- **Features**: Connection reuse, batch processing, multiple provider support
- **Providers**: Gmail, Office365, Yahoo with app-specific password support

#### 3. **Parallel Processing Framework**
- **Core Functions**: `process_resumes_bulk()`, `process_single_resume()`, `send_emails_batch()`
- **Purpose**: High-performance batch processing for multiple resumes
- **Features**: ThreadPoolExecutor-based parallelism, progress tracking, error handling
- **Performance**: Up to 8x faster than sequential processing

### Data Flow Architecture

```
File Upload → Tech Stack Input → Resume Processing → Email Sending (Optional) → Download
     ↓              ↓                    ↓                    ↓                  ↓
DOCX Files → Bullet Points → Format Preservation → SMTP Pool → Customized Resume
```

### Processing Pipeline
1. **File Upload**: Multiple DOCX files supported
2. **Tech Stack Parsing**: Extract bullet points from formatted input
3. **Project Detection**: Identify project sections and responsibilities
4. **Point Distribution**: Distribute points across top 3 projects
5. **Format Preservation**: Maintain original document formatting
6. **Email Automation**: Optional bulk email sending with connection pooling
7. **Download**: Individual and bulk download options

### State Management Strategy
- **Streamlit Session State**: File uploads, tech stack inputs, processing results
- **Memory Management**: Cleanup after bulk operations with `cleanup_memory()`
- **Connection Pooling**: SMTP connection reuse for email efficiency

## 🔄 Development Workflow

### Feature Development
1. **Resume parsing** - Understand the document structure parsing logic
2. **Format preservation** - Key to maintaining document integrity
3. **Bulk operations** - Leverage parallel processing for performance
4. **Email integration** - Connection pooling prevents SMTP timeouts

### Testing Strategy
- **Basic Testing**: `test_streamlit_app.py` for UI component testing
- **Integration Testing**: Full app testing locally
- **Manual Testing**: Use the built-in preview and email functions

### Deployment Considerations
- **File Storage**: Temporary files handled in memory
- **Memory Usage**: Built-in cleanup functions for bulk operations
- **Local Setup**: Simple pip install and streamlit run

## 🔧 Configuration & Customization

### Streamlit Configuration (`.streamlit/config.toml`)
- **Upload limits**: 200MB max file size
- **Performance settings**: Compression, CORS enabled
- **Theme**: Professional color scheme

### Key Configuration Points
- **Max Workers**: Configurable parallel processing (2-8 workers)
- **SMTP Servers**: Pre-configured for Gmail, Office365, Yahoo
- **Tech Stack Format**: Specific bullet point format required

## 🚨 Common Development Pitfalls

### File Processing Issues
- **Issue**: Document format not recognized
- **Solution**: Ensure resumes have clear "Responsibilities:" sections in projects
- **Testing**: Use the preview function to verify parsing

### SMTP Connection Problems
- **Issue**: Email sending failures
- **Solution**: Use app-specific passwords, not regular passwords
- **Debugging**: Check SMTP server settings and port numbers

### Memory Management
- **Issue**: High memory usage with large batches
- **Solution**: `cleanup_memory()` function cleans up after bulk operations
- **Pattern**: Called automatically after bulk processing

### Streamlit Button Keys
- **Issue**: Duplicate button key errors
- **Solution**: Use file-specific keys like `f"preview_{file.name}"`
- **Pattern**: Always include unique identifiers in button keys

## 📊 Performance Optimizations

### Current Optimizations
- **Parallel Processing**: ThreadPoolExecutor for bulk resume processing
- **SMTP Connection Pooling**: Reuse connections for batch email sending
- **Memory Cleanup**: Automatic garbage collection after operations
- **File Handling**: Optimized BytesIO handling for concurrent processing

### Performance Monitoring
The app includes built-in performance tracking:
- Processing speed (resumes/second)
- Total processing time
- Email sending statistics
- Speed comparison vs sequential processing

### Scaling Considerations
- **File Size**: Handles large DOCX files efficiently
- **Batch Size**: Configurable worker count (2-8 workers optimal)
- **Memory**: Automatic cleanup prevents memory leaks
- **Concurrent Users**: Single-user design, but efficient resource usage

## 🔐 Security Implementation

### Input Security
- **File Validation**: DOCX format verification
- **Size Limits**: 200MB per file maximum
- **Content Sanitization**: Safe document processing

### Email Security  
- **Credential Handling**: Never store email passwords
- **App Passwords**: Recommend app-specific passwords
- **Connection Security**: SSL/TLS encrypted SMTP connections

### File Security
- **Temporary Files**: Automatic cleanup after processing
- **Path Safety**: Proper file path handling
- **Data Privacy**: No persistent storage of personal data

## 💡 Key Development Tips

### Working with DOCX Processing
- Documents must have clear project sections
- "Responsibilities:" headings are detection keywords
- Format preservation is critical - test with various document styles

### Optimizing Bulk Operations
- Use 3+ files to enable bulk mode
- Monitor memory usage during development
- Test with realistic file sizes and quantities

### Email Integration Best Practices
- Always test with app-specific passwords
- Handle SMTP errors gracefully
- Provide clear user feedback on email status

This simplified architecture focuses on core resume processing functionality while maintaining high performance through parallel processing and efficient resource management.
