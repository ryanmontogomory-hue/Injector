# Resume Customizer - Professional Resume Enhancement Platform

## Overview

This is a comprehensive Resume Customizer application built with Streamlit that provides intelligent resume enhancement and email automation capabilities. The application supports multiple input formats, implements advanced bullet formatting consistency, and includes enterprise-grade features like PostgreSQL integration, async processing with Celery, security enhancements, and performance optimizations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses **Streamlit** as the primary web framework with a tabbed interface design:
- **Multi-tab UI** for different functionalities (resume processing, requirements management, application guide)
- **Progressive loading** for large file lists to prevent UI blocking
- **Responsive design** with modern visual hierarchy and enhanced UX components
- **Real-time progress tracking** with ETA calculations and status updates
- **Security-enhanced forms** with CSRF protection and input sanitization

### Backend Architecture
The system follows a **modular monolithic architecture** with clear separation of concerns:

#### Core Module Structure:
- **`resume_customizer/`** - Main resume processing logic with parsers, processors, detectors, and formatters
- **`infrastructure/`** - System infrastructure including utilities, monitoring, security, and async processing
- **`ui/`** - User interface components and handlers
- **`database/`** - PostgreSQL integration with models, migrations, and connection management
- **`enhancements/`** - Advanced features like analytics, error recovery, and batch processing

#### Key Architectural Decisions:
1. **Restricted Format Parser**: Only supports 3 specific input formats for consistency
2. **Bullet Consistency Engine**: Automatically detects existing bullet markers and maintains formatting consistency
3. **Dual Storage Backend**: Supports both JSON file storage and PostgreSQL with automatic fallback
4. **Circuit Breaker Pattern**: Implements resilience against cascading failures for database, SMTP, and file processing
5. **Memory-Optimized Processing**: Includes automatic garbage collection and memory pressure handling

### Data Storage Solutions
The application implements a **dual-backend storage approach**:

#### PostgreSQL Database (Primary):
- **High-performance connection pooling** (20 base + 30 overflow connections)
- **Advanced indexing** with GIN, B-tree, and composite indexes
- **ACID transactions** with optimistic locking for concurrent access
- **Materialized views** for lightning-fast queries
- **Full-text search capabilities** and audit logging

#### JSON File Storage (Fallback):
- File-based storage for development and lightweight deployments
- Automatic migration utilities to PostgreSQL
- Backward compatibility maintenance

### Authentication and Authorization
The system implements **Phase 1 Security Features**:
- **Password Encryption**: AES-256 encryption for email passwords with secure memory storage
- **Input Sanitization**: XSS protection and dangerous character removal
- **Rate Limiting**: Configurable limits for email sending, file uploads, and processing
- **CSRF Protection**: Form protection with automatic token rotation
- **Session Security**: 30-minute timeout with secure session management

### External Dependencies
The architecture includes **distributed processing capabilities**:
- **Celery Task Queue**: Async resume processing with Redis broker
- **Multi-level Caching**: L1 (local memory) and L2 (Redis) with automatic failover
- **Background Workers**: Scalable worker processes for high-concurrency workloads

## External Dependencies

### Core Framework and UI
- **Streamlit** (≥1.28.0) - Main web application framework
- **Python-docx** (≥0.8.11) - Word document processing
- **Mammoth** (≥1.6.0) - Document conversion and processing

### Database and Storage
- **PostgreSQL** with connection pooling via psycopg2-binary and psycopg[pool]
- **SQLAlchemy** (≥2.0.0) - ORM and database abstraction
- **Alembic** (≥1.12.0) - Database migrations
- **Redis** (≥4.0) - Caching and message broker

### Distributed Processing
- **Celery** (≥5.3) - Distributed task queue for async processing
- **Redis** - Message broker and distributed cache backend

### Security and Encryption
- **Cryptography** (≥41.0.0) - Password encryption and security features
- **Python-jose** (≥3.3.0) - CSRF token generation and validation
- **Passlib** (≥1.7.4) - Password hashing utilities

### Performance and Monitoring
- **psutil** - System resource monitoring
- **structlog** (≥23.0.0) - Structured logging for better observability
- **concurrent-log-handler** - Thread-safe logging

### Email Communication
- **yagmail** - Email sending with SMTP integration
- **python-dateutil** and **pytz** - Date/timezone handling for email scheduling

### Development and Testing
- **python-dotenv** - Environment variable management
- **tqdm** and **colorama** - Progress bars and colored terminal output
- **pytest** - Testing framework (implied from project structure)

The application is designed to gracefully handle missing optional dependencies and provides fallback mechanisms for core functionality.