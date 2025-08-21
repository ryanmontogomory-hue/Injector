# 📝 Resume Customizer + Bulk Email Sender

A powerful Streamlit application that helps you customize resumes with tech stacks and send them via email with bulk processing capabilities.

## ✨ Features

- **📄 Resume Customization**: Upload DOCX resumes and add tech-specific bullet points
- **🔍 Smart Preview**: See exactly what will be changed before processing
- **📧 Email Integration**: Send customized resumes directly via email
- **⚡ Bulk Processing**: Process multiple resumes simultaneously with parallel workers
- **🎯 Format Preservation**: Maintains original formatting, fonts, and styles
- **🔒 Secure**: No credentials stored, app-specific password support
- **📊 Performance Metrics**: Real-time progress tracking and throughput statistics

## 🚀 Quick Start

### Option 1: Local Development
```bash
# Clone the repository
git clone <your-repo-url>
cd resume-customizer

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Option 2: Docker
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t resume-customizer .
docker run -p 8501:8501 resume-customizer
```

### Option 3: One-Click Deploy
- **Streamlit Cloud**: [![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
- **Railway**: Deploy directly from GitHub
- **Heroku**: One-click deploy with Heroku button

## 📋 Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`:
  - streamlit>=1.28.0
  - python-docx>=0.8.11
  - mammoth>=1.6.0 (for preview)

## 🔧 Usage

### 1. Upload Resumes
- Upload one or more DOCX files
- Each resume should have clear project sections with "Responsibilities:" headings

### 2. Add Tech Stacks
For each resume, provide tech stacks in this format:
```
Python: • Developed web applications using Django and Flask • Implemented RESTful APIs
JavaScript: • Created interactive UI components with React • Utilized Node.js for backend services
AWS: • Deployed applications using EC2 and S3 • Managed databases with RDS
```

### 3. Configure Email (Optional)
- **Recipient Email**: Where to send the resume
- **Sender Email**: Your email address
- **App Password**: Use app-specific passwords for Gmail/Office365
- **SMTP Server**: Pre-configured options available

### 4. Preview Changes
- Click "🔍 Preview Changes" to see exactly what will be modified
- Review the changes before processing

### 5. Generate & Send
- **Individual**: Process one resume at a time
- **Bulk Mode**: Process 3+ resumes simultaneously for maximum speed

## 🏗️ Architecture

### Core Components
- **Resume Parser**: Finds projects and responsibilities sections
- **Point Distributor**: Distributes tech points across top 3 projects
- **Format Preserver**: Maintains original document formatting
- **Email Manager**: SMTP connection pooling and batch sending
- **Parallel Processor**: Multi-threaded resume processing

### Performance Features
- **Connection Pooling**: Reuses SMTP connections for faster email sending
- **Parallel Processing**: Up to 8x faster with multiple workers
- **Memory Optimization**: Efficient buffer management
- **Real-time Progress**: Live updates during bulk operations

## 📁 Project Structure

```
resume-customizer/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container configuration
├── docker-compose.yml              # Docker Compose setup
├── DEPLOYMENT.md                   # Comprehensive deployment guide
├── README.md                       # This file
├── .streamlit/
│   ├── config.toml                 # Streamlit configuration
│   └── secrets.toml.example        # Secrets template
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── email_analysis.py               # Email functionality analysis
├── email_status_report.md          # Email feature documentation
└── test_email.py                   # Email testing utilities
```

## 🔒 Security

- **No Credential Storage**: Email credentials are never stored
- **App-Specific Passwords**: Supports secure authentication methods
- **Input Validation**: Validates file types and content
- **Error Handling**: Graceful handling of failures

## 🚀 Deployment

### Recommended Platforms

1. **Streamlit Cloud** (Free)
   - Best for: Quick deployment, public projects
   - Setup: Connect GitHub → Deploy
   - URL: Auto-generated

2. **Docker** (Production)
   - Best for: Production environments, custom infrastructure
   - Platforms: AWS, GCP, Azure, DigitalOcean
   - Features: Scalable, consistent environment

3. **Railway** (Modern PaaS)
   - Best for: Modern deployment, generous free tier
   - Setup: Connect GitHub → Auto-deploy
   - Features: Automatic HTTPS, custom domains

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## ⚡ Performance

### Benchmarks
- **Single Resume**: ~2-3 seconds
- **Bulk Processing**: Up to 8x faster with parallel workers
- **Email Sending**: Connection pooling for optimal speed
- **Memory Usage**: Optimized for multiple file processing

### Scaling
- **Concurrent Users**: Supports multiple simultaneous users
- **File Size**: Handles large DOCX files efficiently
- **Batch Size**: Configurable worker count and batch sizes

## 🛠️ Troubleshooting

### Common Issues

1. **Email Not Sending**
   - Use app-specific passwords
   - Check firewall settings
   - Verify SMTP server settings

2. **Resume Not Recognized**
   - Ensure clear "Responsibilities:" sections
   - Check project heading formats
   - Verify DOCX format

3. **Performance Issues**
   - Reduce worker count for lower-spec machines
   - Check memory availability
   - Optimize batch sizes

### Debug Mode

Enable debug output:
```python
import streamlit as st
st.write("Debug info:", st.session_state)
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Deployment Guide](DEPLOYMENT.md)
- 🐛 [Report Issues](https://github.com/yourusername/resume-customizer/issues)
- 💬 [Discussions](https://github.com/yourusername/resume-customizer/discussions)

## 🎯 Use Cases

- **Job Seekers**: Customize resumes for different job applications
- **Recruiters**: Bulk process candidate resumes
- **Career Services**: Help students tailor resumes
- **Freelancers**: Quick resume customization for clients

## 🌟 Key Benefits

- ⏱️ **Time Saving**: Bulk process multiple resumes
- 🎯 **Targeted**: Focus on top 3 projects for impact
- 📧 **Automated**: Direct email sending capabilities
- 🔍 **Preview**: See changes before processing
- 🚀 **Fast**: Parallel processing for speed
- 📱 **User-Friendly**: Intuitive Streamlit interface

---

**Made with ❤️ using Streamlit**

*Perfect for job applications, recruitment agencies, and career services!*
