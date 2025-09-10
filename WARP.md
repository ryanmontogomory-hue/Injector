# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview
Resume Customizer is a Streamlit-based web application that automatically injects technology-specific bullet points into resumes based on user input. It supports bulk processing, email automation, Google Drive integration, and distributed task processing with Celery.

## Common Development Commands

### Local Development
```bash
# Start the main application
streamlit run app.py

# Install dependencies
pip install -r requirements.txt

# Install Google Drive dependencies (optional)
pip install -r requirements-gdrive.txt

# Run tests
pytest

# Verify environment setup
python verify_env.py
```

### Distributed Processing Setup
```bash
# Start Redis (required for Celery)
docker run -p 6379:6379 redis

# Start Celery worker
celery -A celeryconfig.celery_app worker --loglevel=info

# Start Celery worker with multiple processes
celery -A celeryconfig.celery_app worker --loglevel=info -c 4

# Monitor resource usage
python resource_monitor.py
```

### Testing & Validation
```bash
# Run specific test modules
pytest tests/

# Verify bullet point formatting
python verify_bullet_formatting.py

# Test email functionality
python test_email.py
```

## Architecture Overview

### Core Components
The application follows a modular architecture with clear separation of concerns:

1. **Main Application Layer** (`app.py`)
   - Streamlit UI orchestration
   - Tab management and routing
   - Session state management
   - Health checks and cleanup

2. **Processing Pipeline**
   - `text_parser.py` - Parses tech stack input in multiple formats
   - `resume_processor.py` - Orchestrates entire processing workflow
   - `document_processor.py` - Handles Word document manipulation
   - `email_handler.py` - Manages SMTP connections and email sending

3. **Specialized Processors** (`processors/` directory)
   - `DocumentProcessor` - Main document processing coordinator
   - `PointDistributor` - Round-robin distribution of points across projects
   - `project_detector.py` - Detects projects and responsibility sections

4. **Format Handlers** (`formatters/` directory)
   - `BulletFormatter` - Preserves original bullet point formatting
   - `base_formatters.py` - Base formatting utilities

5. **UI Components** (`ui/` directory)
   - Modular UI components for different tabs
   - `BulkProcessor` - High-performance parallel processing
   - `ResumeTabHandler` - Individual resume processing
   - `RequirementsManager` - Job requirements management

### Key Design Patterns

#### Processing Pipeline
The application uses a pipeline pattern for document processing:
1. **Parse** tech stacks from user input (supports multiple formats)
2. **Detect** projects in uploaded Word documents
3. **Distribute** points across top 3 projects using round-robin
4. **Inject** points while preserving original formatting
5. **Email** (optional) processed documents

#### Caching Strategy
- LRU caching in `text_parser.py` for parsed tech stacks
- Document loading cache in `DocumentProcessor` 
- Result caching in `ResumeProcessor` to avoid reprocessing identical inputs

#### Async Processing
- Celery integration for distributed task processing (`tasks.py`, `celeryconfig.py`)
- Thread pools for parallel document processing
- SMTP connection pooling for efficient email sending

#### Format Preservation
The app maintains original Word document formatting through:
- Style preservation in `BulletFormatter`
- Run-level formatting copying
- Paragraph formatting inheritance

### Data Flow

```
User Input → Text Parser → Resume Processor → Document Processor
    ↓              ↓              ↓                  ↓
Tech Points → Point Distributor → Project Detector → Document
    ↓              ↓              ↓                  ↓
Distribution → Bullet Formatter → Email Handler → Final Output
```

## Important Configuration

### Environment Variables
- `CELERY_BROKER_URL` - Redis URL for Celery (default: redis://localhost:6379/0)
- `CELERY_RESULT_BACKEND` - Redis backend for results

### Configuration Files
- `config.py` - Main application configuration including SMTP servers, UI settings, performance limits
- `celeryconfig.py` - Celery task configuration with timeouts and serialization
- `pytest.ini` - Test configuration

## Technology Stack Requirements

### Core Dependencies
- **Streamlit** - Web UI framework
- **python-docx** - Word document manipulation  
- **Celery + Redis** - Distributed task processing
- **psutil** - System resource monitoring

### Document Processing
- **mammoth** - Document preview generation
- **python-pptx** - PowerPoint support
- **PyPDF2** - PDF processing capabilities

### Email & Communication
- **yagmail** - Simplified email sending
- SMTP servers: Gmail, Office365, Yahoo supported

## Performance Considerations

### Scalability Features
- Supports 50+ concurrent users with connection pooling
- Bulk processing with configurable worker pools (max 8 workers)
- Memory optimization with automatic cleanup after processing
- SMTP connection reuse for faster email sending

### Resource Monitoring
- Real-time CPU and memory tracking
- Celery queue length monitoring
- Automatic alerts for high resource usage
- Background resource monitoring via `resource_monitor.py`

## Common Patterns & Conventions

### Error Handling
- Centralized error messages in `config.py`
- Graceful degradation for missing dependencies
- Comprehensive logging via `logger.py`
- Audit logging for security events via `audit_logger.py`

### Session State Management
- File upload state preservation across tabs
- Resume input caching for better UX
- User session tracking with UUIDs

### Testing Strategy
- Unit tests focus on core parsing and configuration modules
- Integration tests for document processing pipeline
- Manual validation scripts for formatting preservation

## File Structure Context

### Key Directories
- `/ui/` - Modular UI components for different application tabs
- `/processors/` - Core document processing logic
- `/formatters/` - Document formatting preservation
- `/detectors/` - Project and content detection algorithms

### Configuration Files
- `requirements*.txt` - Dependency management (base + Google Drive)
- `Dockerfile` - Container deployment configuration
- `.streamlit/config.toml` - Streamlit-specific settings

## Special Features

### Google Drive Integration
- OAuth-based authentication via `client_secrets.json`
- File picker UI in `ui/gdrive_picker.py`
- Token persistence via `token_gdrive.pkl`

### Multi-Format Input Support
The text parser supports both legacy and modern input formats:
- Legacy: `TechName: • point1 • point2`
- Modern: Block format with tech names followed by bullet points

### Bulk Processing Optimizations
- Parallel document processing with ThreadPoolExecutor
- SMTP connection pooling and reuse
- Real-time progress tracking
- Memory cleanup between batches

## Development Guidelines

### When Adding New Features
1. Follow the modular architecture - add new processors to `/processors/`
2. Update configuration in `config.py` for new settings
3. Add corresponding UI components in `/ui/` directory
4. Implement proper error handling with messages in `config.py`
5. Add logging calls for debugging and monitoring

### Performance Best Practices
- Use LRU caching for repeated operations
- Implement lazy loading for heavy resources
- Clean up document resources after processing
- Monitor memory usage in bulk operations

### Testing New Changes
- Run `python verify_env.py` to check dependencies
- Use `python verify_bullet_formatting.py` for formatting preservation
- Test with sample documents of various formats
- Verify Celery integration with `celery -A celeryconfig.celery_app worker`
