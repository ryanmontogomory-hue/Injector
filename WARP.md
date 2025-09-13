# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Development Commands

### Running the Application
```bash
# Primary command to run the Resume Customizer
streamlit run app.py

# For development with debug mode
streamlit run app.py --server.runOnSave=true
```

### Testing
```bash
# Run all tests
python -m pytest tests_new/

# Run specific test categories
python -m pytest tests_new/unit/          # Unit tests
python -m pytest tests_new/integration/   # Integration tests
python -m pytest tests_new/performance/   # Performance tests

# Run comprehensive test suite
python test_comprehensive.py

# Test security features (Phase 1)
python test_security_phase1.py

# Test the reorganized structure
python test_reorganized_structure.py

# Test Celery integration
python test_celery_end_to_end.py
```

### Database Operations
```bash
# Setup database (PostgreSQL)
python scripts/setup_database.py

# Initialize database with environment setup
python scripts/setup_database.py --setup-env

# Run database migrations
python scripts/setup_database.py --migrate

# Test database connection
python scripts/setup_database.py --test
```

### Background Processing (Celery)
```bash
# Start Celery worker (Windows)
scripts/run_worker.bat

# Start Celery with specific configuration
scripts/start_celery.bat

# For Python-based worker startup
python scripts/start_celery_worker.py
```

### Performance and Monitoring
```bash
# Run performance benchmarks
python tests_new/performance/performance_benchmark.py

# Check application health
python -c "from infrastructure.monitoring.performance_monitor import health_check; print(health_check())"
```

## Architecture Overview

### High-Level Structure
The application follows a clean architecture pattern with clear separation of concerns:

- **`resume_customizer/`** - Core business logic for resume processing
- **`infrastructure/`** - Cross-cutting concerns (logging, monitoring, security, async processing)
- **`ui/`** - Streamlit user interface components
- **`database/`** - PostgreSQL data models and migrations
- **`enhancements/`** - Advanced features and optimizations

### Key Architectural Patterns

#### Modular Resume Processing Pipeline
The resume customization follows a pipeline pattern:
1. **Parse** input text using restricted format parser (only 3 supported formats)
2. **Detect** project sections in uploaded DOCX files
3. **Distribute** tech stack points across top 3 projects
4. **Format** bullets consistently (auto-detects dash/bullet style)
5. **Generate** customized resume with preserved formatting

#### Multi-User Enterprise Architecture
- **Database-backed** with PostgreSQL for scalability (50+ concurrent users)
- **Connection pooling** (20-connection pool) for optimal performance
- **Async processing** with Celery for background tasks
- **Rate limiting** with subscription-based quotas
- **Caching layers** with TTL for performance optimization

#### Security-First Design (Phase 1 Complete)
- **AES-256 password encryption** for email credentials
- **CSRF protection** for all forms
- **Input sanitization** preventing XSS and path traversal
- **Rate limiting** across all critical operations
- **Session security** with automatic timeouts

### Input Format Restrictions
The parser **strictly enforces only 3 supported formats**:

1. **Format 1**: `Tech Stack` + tabbed bullets (`•\tpoint`)
2. **Format 2**: `Tech Stack:` + tabbed bullets (`•\tpoint`)
3. **Format 3**: `Tech Stack` + regular bullets (`• point`)

**Important**: Mixed formats are allowed in same input, but any other format variations are rejected with detailed error messages.

### Bullet Consistency System
- **Emergency patch active** - `bullet_consistency_patch.py` ensures consistent output
- **Auto-detection** of existing resume bullet style (dash `-` or bullet `•`)
- **Smart conversion** matches detected style throughout document
- **Format preservation** maintains fonts, spacing, colors, and indentation

### Database Architecture
- **PostgreSQL** with comprehensive models in `database/models.py`
- **UUID primary keys** for scalability and security
- **JSONB fields** for flexible tech stack storage with GIN indexing
- **Optimistic locking** with version fields
- **Migration system** from JSON to PostgreSQL with `database/migrate_from_json.py`

### Performance Optimizations
- **Parallel processing** up to 8x faster with worker pools
- **SMTP connection pooling** for email efficiency
- **Memory optimization** with cleanup thresholds
- **Circuit breakers** for fault tolerance
- **Distributed caching** with Redis support

## Important Development Guidelines

### Import Patterns
Due to the reorganized structure, use proper import paths:

```python
# Resume functionality
from resume_customizer import parse_input_text, get_resume_manager
from resume_customizer.parsers.restricted_text_parser import RestrictedFormatError

# Infrastructure components
from infrastructure.utilities.logger import get_logger
from infrastructure.security.enhancements import InputSanitizer
from infrastructure.monitoring.performance_monitor import performance_decorator

# UI components
from ui.secure_components import get_secure_ui_components
```

### Configuration Management
- **Environment-based configuration** in `config.py` with `.env` support
- **Validation system** with detailed feedback via `validate_config()`
- **Template generation** for environment setup
- **Production/development** environment detection

### Error Handling Strategy
- **Enhanced error recovery** in `enhancements/enhanced_error_recovery.py`
- **Structured logging** with context and performance metrics
- **Graceful degradation** when optional components fail
- **Comprehensive error messages** with actionable guidance

### Testing Strategy
- **Unit tests** in `tests_new/unit/` for individual components
- **Integration tests** in `tests_new/integration/` for end-to-end workflows
- **Performance tests** for load and stress testing
- **Security validation** with dedicated test suite

### Background Processing
- **Celery integration** for heavy operations (bulk processing, email sending)
- **Task monitoring** and progress tracking
- **Fallback mechanisms** when async processing unavailable
- **Redis backend** for task queuing and results

## Key Files and Their Roles

### Core Application Files
- `app.py` - Main Streamlit entry point with progressive loading and error handling
- `config.py` - Comprehensive configuration management with environment variable support
- `requirements.txt` - Python dependencies including security, database, and async processing libraries

### Resume Processing Core
- `resume_customizer/parsers/restricted_text_parser.py` - Strict 3-format parser with detailed validation
- `resume_customizer/processors/document_processor.py` - DOCX manipulation preserving formatting
- `resume_customizer/detectors/project_detector.py` - Intelligent project section detection
- `resume_customizer/formatters/bullet_formatter.py` - Bullet consistency formatting

### Infrastructure Components
- `infrastructure/security/enhancements.py` - Phase 1 security implementation (encryption, sanitization, CSRF)
- `infrastructure/monitoring/performance_monitor.py` - Performance tracking and health checks
- `infrastructure/async_processing/tasks.py` - Celery task definitions for background processing
- `infrastructure/utilities/structured_logger.py` - Advanced logging with context and performance metrics

### Database Layer
- `database/models.py` - PostgreSQL models with UUID keys, JSONB fields, and optimizations
- `database/migrate_from_json.py` - Migration utility from JSON to PostgreSQL
- `scripts/setup_database.py` - Database initialization and migration script

### UI Components
- `ui/secure_components.py` - Security-enhanced UI components with CSRF protection
- `ui/bulk_processor.py` - Bulk processing interface with progress tracking
- `ui/resume_tab_handler.py` - Individual resume processing interface

## Common Issues and Solutions

### Format Parser Errors
When users get format validation errors, guide them to use only the 3 supported formats with clear examples from the error messages.

### Performance Issues
For bulk processing slowdowns, check:
1. Worker pool configuration in `config.py`
2. Memory cleanup thresholds
3. Database connection pool status

### Security Validation Failures
Phase 1 security may fail if:
1. Required crypto dependencies missing
2. CSRF tokens expired (refresh page)
3. Rate limits exceeded (wait or check limits)

### Database Connection Issues
Use `scripts/setup_database.py --test` to diagnose PostgreSQL connectivity and pool status.

### Import Errors After Reorganization
The project was recently reorganized. If imports fail, check the new module structure and update import paths accordingly.
