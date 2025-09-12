# 🎯 Resume Customizer - Reorganized Architecture

A powerful Streamlit application for customizing resumes with strict format validation and bullet consistency.

## 🏗️ **New Project Structure**

```
resume-customizer/
├── 📁 resume_customizer/          # 🆕 CORE RESUME LOGIC
│   ├── parsers/                   # Text parsing (3 supported formats only)
│   ├── processors/                # Document processing & manipulation  
│   ├── detectors/                 # Project section detection
│   ├── formatters/                # Bullet formatting & consistency
│   └── email/                     # Email functionality
│
├── 📁 infrastructure/             # 🆕 SYSTEM INFRASTRUCTURE  
│   ├── config/                    # Configuration management
│   ├── monitoring/                # Performance & health monitoring
│   ├── security/                  # Security & validation
│   ├── async_processing/          # Celery background tasks
│   └── utilities/                 # Logging, memory, retry logic
│
├── 📁 ui/                         # User interface components
├── 📁 tests_new/                  # 🆕 ORGANIZED TESTS
│   ├── unit/                      # Unit tests  
│   ├── integration/               # Integration tests
│   └── performance/               # Performance tests
│
├── 📁 docs_organized/             # 🆕 CONSOLIDATED DOCS
└── 📁 scripts/                    # Utility scripts
```

## ✨ **Key Features**

### 🎯 **Restricted Format Parser**
- **Only 3 supported input formats** (strictly enforced)
- **Format 1**: `Tech Stack` + tabbed bullets (`•\tpoint`)
- **Format 2**: `Tech Stack:` + tabbed bullets (`•\tpoint`) 
- **Format 3**: `Tech Stack` + regular bullets (`• point`)
- **Mixed formats allowed** in same input

### 🔧 **Bullet Consistency**
- **Smart output conversion** matches existing resume format
- **Emergency patch active** for guaranteed consistency
- **Auto-detection** of dash (`-`) or bullet (`•`) markers

### 🏗️ **Clean Architecture** 
- **Modular design** with clear separation of concerns
- **Resume logic** isolated in `resume_customizer/`
- **Infrastructure** separated in `infrastructure/`
- **Organized testing** by type and purpose

## 🚀 **Quick Start**

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run Application
```bash
streamlit run app.py
```

### Run Tests
```bash
# Unit tests
python -m pytest tests_new/unit/

# Integration tests  
python -m pytest tests_new/integration/

# Test reorganized structure
python test_reorganized_structure.py
```

## 📝 **Supported Input Formats**

### ✅ **Format 1: Tech Stack + Tabbed Bullets**
```
Java
•	Developed Spring Boot applications
•	Implemented REST APIs
•	Built microservices architecture
```

### ✅ **Format 2: Tech Stack with Colon + Tabbed Bullets**
```
Python:
•	Created data processing pipelines  
•	Implemented machine learning models
•	Built automated testing frameworks
```

### ✅ **Format 3: Tech Stack + Regular Bullets**
```
AWS
• Deployed containerized applications
• Managed cloud infrastructure  
• Implemented serverless architectures
```

### ❌ **Rejected Formats**
- Single-line formats: `Java: • point1 • point2`
- Mixed bullet types in same section
- Missing bullet markers
- Any other format variations

## 🔧 **Architecture Benefits**

### **Before Reorganization**
- Resume logic scattered across `core/`, `processors/`, `formatters/`
- Tests mixed in root directory
- No clear module boundaries
- Difficult to maintain and extend

### **After Reorganization**  
- **Clear separation**: Resume logic vs infrastructure
- **Organized tests**: Unit, integration, performance
- **Modular imports**: Clean dependency hierarchy
- **Better maintainability**: Logical grouping of related files

## 📊 **Import Examples**

### **Main Components**
```python
# Resume functionality
from resume_customizer import parse_input_text_restricted, get_resume_manager

# Infrastructure  
from infrastructure import get_logger, get_performance_monitor

# Security & validation
from infrastructure.security import InputSanitizer, get_file_validator
```

### **Specific Modules**
```python
# Restricted parser (3 formats only)
from resume_customizer.parsers.restricted_text_parser import RestrictedFormatError

# Document processing
from resume_customizer.processors.document_processor import get_document_processor

# Monitoring
from infrastructure.monitoring.performance_monitor import performance_decorator
```

## 🛡️ **Error Handling**

### **Format Validation**
```python
try:
    points, stacks = parse_input_text_restricted(user_input)
except RestrictedFormatError as e:
    # Shows detailed error with format examples
    print(f"Invalid format: {e}")
```

### **Detailed Error Messages**
- **Format examples** shown on validation failure
- **Clear guidance** on supported formats
- **Helpful suggestions** for fixing input

## 📈 **Performance & Monitoring**

- **Circuit breakers** for fault tolerance
- **Distributed caching** for performance
- **Memory optimization** for large documents
- **Structured logging** for debugging
- **Performance metrics** collection

## 🔐 **Security Features**

- **Input sanitization** for all user inputs
- **File validation** for uploaded documents
- **Rate limiting** for API endpoints
- **Secure password handling** for email functionality

## 📚 **Documentation**

- **Comprehensive guides** in `docs_organized/`
- **API documentation** for all modules
- **Integration examples** and best practices
- **Deployment guides** for production

## 🧪 **Testing Strategy**

- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end workflow testing  
- **Performance tests**: Load and stress testing
- **Format validation tests**: All 3 supported formats

## 🎯 **Future Enhancements**

- Enhanced format detection algorithms
- Additional output format support
- Advanced bullet formatting options
- Integration with more document formats

---

## 📞 **Support**

For issues, questions, or contributions:
- **GitHub Issues**: [Report bugs or request features](https://github.com/12shivam219/Injector/issues)
- **Documentation**: Check `docs_organized/` for detailed guides
- **Tests**: Run `test_reorganized_structure.py` for structure validation

**Built with ❤️ for better resume customization and cleaner code architecture!**