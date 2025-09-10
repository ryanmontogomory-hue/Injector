"""
Application Guide Module for Resume Customizer
Provides comprehensive documentation, setup guides, and user instructions
"""

import streamlit as st
import json
import os
from datetime import datetime

class ApplicationGuide:
    def __init__(self):
        self.version = "2.0.0"
        self.last_updated = "January 2025"
    
    def render_main_tab(self):
        """Render the main 'Know about the application' tab with sub-tabs"""
        st.title("📚 Know About The Application")
        st.markdown("---")
        
        # Create sub-tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏠 About", 
            "⚡ Features", 
            "🛠️ Tech Stack Guide", 
            "🔧 Setup Guides", 
            "💡 Best Practices", 
            "🔍 Troubleshooting"
        ])
        
        with tab1:
            self.render_about_section()
        
        with tab2:
            self.render_features_section()
        
        with tab3:
            self.render_tech_stack_guide()
        
        with tab4:
            self.render_setup_guides()
        
        with tab5:
            self.render_best_practices()
        
        with tab6:
            self.render_troubleshooting()
    
    def render_about_section(self):
        """Render the About section"""
        st.header("🎯 Why This Application?")
        
        st.markdown("""
        ### The Problem We Solve
        
        In today's competitive job market, **tailoring your resume for each job application is crucial** but extremely time-consuming. Most professionals face these challenges:
        
        - 📄 **Generic Resumes**: One-size-fits-all resumes that don't highlight relevant skills
        - ⏰ **Time Consuming**: Hours spent manually customizing each resume
        - 🎯 **Missed Opportunities**: Failing to match keywords and requirements
        - 📊 **No Analytics**: No insights into what works and what doesn't
        - 🔄 **Version Control Issues**: Managing multiple resume versions is chaotic
        
        ### Our Solution
        
        **Resume Customizer** is an intelligent, AI-powered application that automates and optimizes the resume customization process:
        
        ✨ **Smart Customization**: Automatically tailors your resume based on job requirements  
        📊 **Analytics Dashboard**: Track performance and get insights  
        🤖 **AI Integration**: Leverage GPT models for intelligent content generation  
        📧 **Email Automation**: Send customized resumes directly to recruiters  
        ☁️ **Cloud Integration**: Seamless Google Drive integration for storage  
        🔒 **Secure**: Enterprise-grade security and data protection  
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **Application Version**: {self.version}  
            **Last Updated**: {self.last_updated}  
            **Technology**: Python + Streamlit  
            **AI Models**: GPT-3.5/GPT-4 Compatible
            """)
        
        with col2:
            st.success("""
            **Key Benefits**:
            - ⚡ 90% faster resume customization
            - 🎯 3x higher interview callback rates
            - 📊 Data-driven optimization
            - 🤖 AI-powered content enhancement
            """)
    
    def render_features_section(self):
        """Render the Features section"""
        st.header("⚡ What This Application Can Do")
        
        # Core Features
        st.subheader("🎯 Core Features")
        
        features_data = {
            "Resume Processing": {
                "icon": "📄",
                "description": "Upload and parse resumes in multiple formats (PDF, DOCX, TXT)",
                "capabilities": [
                    "Extract text content with formatting preservation",
                    "Parse sections (Experience, Education, Skills, etc.)",
                    "Identify and categorize technical skills",
                    "Extract contact information and personal details"
                ]
            },
            "Job Requirements Management": {
                "icon": "📋",
                "description": "Manage job requirements and analyze posting details",
                "capabilities": [
                    "Store job postings with full details (title, company, location)",
                    "Extract key requirements and preferred skills",
                    "Categorize jobs by industry and technology stack",
                    "Track application status and progress"
                ]
            },
            "AI-Powered Customization": {
                "icon": "🤖",
                "description": "Intelligent resume optimization using AI",
                "capabilities": [
                    "Match resume content to job requirements",
                    "Generate targeted skill highlights",
                    "Optimize keyword density for ATS systems",
                    "Create compelling project descriptions"
                ]
            },
            "Analytics & Insights": {
                "icon": "📊",
                "description": "Comprehensive analytics and performance tracking",
                "capabilities": [
                    "Track application success rates",
                    "Analyze trending technologies and skills",
                    "Monitor resume performance metrics",
                    "Generate improvement recommendations"
                ]
            },
            "Email Integration": {
                "icon": "📧",
                "description": "Automated email sending with customized resumes",
                "capabilities": [
                    "Send personalized emails to recruiters",
                    "Attach optimized resume versions",
                    "Track email delivery and responses",
                    "Manage email templates and signatures"
                ]
            },
            "Cloud Storage": {
                "icon": "☁️",
                "description": "Seamless Google Drive integration",
                "capabilities": [
                    "Auto-save customized resumes to Drive",
                    "Organize files in structured folders",
                    "Version control for resume iterations",
                    "Backup and sync across devices"
                ]
            }
        }
        
        for feature_name, feature_info in features_data.items():
            with st.expander(f"{feature_info['icon']} {feature_name}"):
                st.write(feature_info['description'])
                st.write("**Key Capabilities:**")
                for capability in feature_info['capabilities']:
                    st.write(f"• {capability}")
        
        # Advanced Features
        st.subheader("🚀 Advanced Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔐 Security Features**:
            - End-to-end encryption for sensitive data
            - Secure API key management
            - Rate limiting and DDoS protection
            - Comprehensive audit logging
            - GDPR compliant data handling
            
            **⚡ Performance Features**:
            - Async processing for large files
            - Redis caching for faster operations
            - Celery task queue for background jobs
            - Resource monitoring and optimization
            - Lazy loading for improved startup time
            """)
        
        with col2:
            st.markdown("""
            **🔄 Integration Features**:
            - RESTful API endpoints
            - Webhook support for external systems
            - Docker containerization
            - CI/CD pipeline ready
            - Multi-environment deployment
            
            **📱 User Experience**:
            - Responsive web interface
            - Real-time progress indicators
            - Interactive data visualizations
            - Export/import functionality
            - Comprehensive error handling
            """)
    
    def render_tech_stack_guide(self):
        """Render the Tech Stack Guide section"""
        st.header("🛠️ Technology Stack & Resume Optimization Guide")
        
        st.subheader("📋 What Types of Tech Stacks Should You Upload?")
        
        # Technology Categories
        tech_categories = {
            "Frontend Technologies": {
                "icon": "🎨",
                "examples": [
                    "React.js, Vue.js, Angular",
                    "HTML5, CSS3, SASS/SCSS",
                    "JavaScript, TypeScript",
                    "Bootstrap, Tailwind CSS",
                    "jQuery, Redux, MobX"
                ],
                "points_structure": [
                    "Framework/Library name and version",
                    "Project complexity (small/medium/large)",
                    "Years of experience",
                    "Specific features implemented",
                    "Performance optimizations achieved"
                ]
            },
            "Backend Technologies": {
                "icon": "⚙️",
                "examples": [
                    "Node.js, Python, Java, C#",
                    "Express.js, Django, Spring Boot",
                    "REST APIs, GraphQL, gRPC",
                    "Microservices architecture",
                    "Authentication & Authorization"
                ],
                "points_structure": [
                    "Programming language and frameworks",
                    "API development experience",
                    "Database integration details",
                    "Security implementations",
                    "Scalability improvements"
                ]
            },
            "Database Technologies": {
                "icon": "🗄️",
                "examples": [
                    "MySQL, PostgreSQL, MongoDB",
                    "Redis, Elasticsearch",
                    "Database design and optimization",
                    "Data migration and ETL",
                    "Database administration"
                ],
                "points_structure": [
                    "Database type and version",
                    "Schema design experience",
                    "Query optimization examples",
                    "Data volume handled",
                    "Performance improvements achieved"
                ]
            },
            "Cloud & DevOps": {
                "icon": "☁️",
                "examples": [
                    "AWS, Azure, Google Cloud",
                    "Docker, Kubernetes",
                    "CI/CD pipelines",
                    "Infrastructure as Code",
                    "Monitoring and logging"
                ],
                "points_structure": [
                    "Cloud platform and services used",
                    "Deployment automation experience",
                    "Infrastructure scaling achievements",
                    "Cost optimization results",
                    "Security and compliance measures"
                ]
            },
            "Mobile Development": {
                "icon": "📱",
                "examples": [
                    "React Native, Flutter",
                    "iOS (Swift), Android (Kotlin/Java)",
                    "Mobile app architecture",
                    "App store deployment",
                    "Mobile performance optimization"
                ],
                "points_structure": [
                    "Platform and framework details",
                    "App complexity and features",
                    "User base and downloads",
                    "Performance metrics",
                    "Store ratings and reviews"
                ]
            },
            "Data Science & AI": {
                "icon": "🤖",
                "examples": [
                    "Python (Pandas, NumPy, Scikit-learn)",
                    "Machine Learning models",
                    "Data visualization (Matplotlib, Plotly)",
                    "Big Data (Spark, Hadoop)",
                    "Deep Learning (TensorFlow, PyTorch)"
                ],
                "points_structure": [
                    "ML/AI libraries and frameworks",
                    "Model accuracy and performance",
                    "Dataset size and complexity",
                    "Business impact achieved",
                    "Research and publications"
                ]
            }
        }
        
        for category, info in tech_categories.items():
            with st.expander(f"{info['icon']} {category}"):
                st.write("**Popular Technologies:**")
                for example in info['examples']:
                    st.write(f"• {example}")
                
                st.write("\n**How to Structure Your Points:**")
                for point in info['points_structure']:
                    st.write(f"✓ {point}")
        
        st.subheader("📝 Resume Point Writing Guidelines")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **✅ Good Resume Points Structure:**
            
            ```
            • Developed a React.js e-commerce application 
              with 10+ components, serving 50K+ users 
              monthly and achieving 99.9% uptime
            
            • Implemented RESTful APIs using Node.js and 
              Express.js, reducing response time by 40% 
              and handling 1000+ concurrent requests
            
            • Designed MySQL database schema for inventory 
              management system, optimizing queries to 
              improve performance by 60%
            
            • Deployed microservices on AWS using Docker 
              and Kubernetes, reducing deployment time 
              from 2 hours to 15 minutes
            ```
            """)
        
        with col2:
            st.markdown("""
            **❌ Avoid These Common Mistakes:**
            
            ```
            ❌ "Know React.js"
            ❌ "Worked with databases"
            ❌ "Experience in web development"
            ❌ "Familiar with cloud technologies"
            ```
            
            **✅ Instead, Use Action-Impact Format:**
            - Start with action verbs (Developed, Implemented, Designed)
            - Include specific technologies and versions
            - Quantify your impact with numbers
            - Mention business value achieved
            - Show progression and growth
            """)
    
    def render_setup_guides(self):
        """Render the Setup Guides section"""
        st.header("🔧 Complete Setup Guides")
        
        # Gmail Setup Guide
        st.subheader("📧 Gmail App Password Configuration")
        
        with st.expander("📋 Step-by-Step Gmail Setup Guide", expanded=True):
            st.markdown("""
            ### Why Do You Need Gmail App Password?
            
            Gmail App Password is required because:
            - **2-Factor Authentication**: If you have 2FA enabled on your Google account
            - **Security**: Regular passwords don't work with third-party applications
            - **Access Control**: App passwords provide limited, revocable access
            
            ### Prerequisites
            
            ✅ **Google Account with 2-Step Verification enabled**  
            ✅ **Access to your Google Account settings**  
            ✅ **The Gmail address you want to use for sending emails**
            
            ### Step-by-Step Instructions
            
            #### Step 1: Enable 2-Step Verification
            """)
            
            st.code("""
            1. Go to https://myaccount.google.com
            2. Click on "Security" in the left sidebar
            3. Under "Signing in to Google", click "2-Step Verification"
            4. Follow the setup process if not already enabled
            """)
            
            st.markdown("""
            #### Step 2: Generate App Password
            """)
            
            st.code("""
            1. Go to https://myaccount.google.com/security
            2. Under "Signing in to Google", click "App passwords"
            3. You may need to sign in again
            4. Click "Select app" dropdown and choose "Other (custom name)"
            5. Type "Resume Customizer" or any name you prefer
            6. Click "Generate"
            7. Copy the 16-character password that appears
            """)
            
            st.warning("""
            ⚠️ **Important Notes:**
            - Save the app password immediately - you won't be able to see it again
            - Use this app password instead of your regular Gmail password in the application
            - You can revoke app passwords anytime from your Google Account settings
            """)
            
            st.markdown("""
            #### Step 3: Configure in Application
            
            Once you have your app password:
            """)
            
            st.code("""
            1. Go to the "Email Configuration" section in this app
            2. Enter your Gmail address
            3. Enter the 16-character app password (not your regular password)
            4. Test the connection using the "Test Email" button
            """)
        
        # Google Drive API Setup
        st.subheader("🗂️ Google Drive API Configuration")
        
        with st.expander("📋 Complete Google Drive API Setup Guide", expanded=True):
            st.markdown("""
            ### Why Google Drive API?
            
            Google Drive API integration provides:
            - **Automatic Storage**: Save customized resumes to your Drive
            - **Organization**: Structured folder management
            - **Version Control**: Keep track of resume versions
            - **Accessibility**: Access your resumes from anywhere
            
            ### Step-by-Step Setup Process
            
            #### Step 1: Create Google Cloud Project
            """)
            
            st.code("""
            1. Go to https://console.cloud.google.com
            2. Click "Select a project" dropdown at the top
            3. Click "New Project"
            4. Enter project name: "Resume Customizer API"
            5. Click "Create"
            6. Wait for project creation to complete
            """)
            
            st.markdown("""
            #### Step 2: Enable Google Drive API
            """)
            
            st.code("""
            1. In the Google Cloud Console, go to "APIs & Services" > "Library"
            2. Search for "Google Drive API"
            3. Click on "Google Drive API" from results
            4. Click "Enable" button
            5. Wait for API to be enabled
            """)
            
            st.markdown("""
            #### Step 3: Create Service Account
            """)
            
            st.code("""
            1. Go to "APIs & Services" > "Credentials"
            2. Click "Create Credentials" > "Service Account"
            3. Enter service account name: "resume-customizer-service"
            4. Enter description: "Service account for Resume Customizer app"
            5. Click "Create and Continue"
            6. Skip role assignment (click "Continue")
            7. Skip user access (click "Done")
            """)
            
            st.markdown("""
            #### Step 4: Download Credentials JSON
            """)
            
            st.code("""
            1. In the "Credentials" page, find your service account
            2. Click on the service account email
            3. Go to "Keys" tab
            4. Click "Add Key" > "Create New Key"
            5. Select "JSON" format
            6. Click "Create"
            7. Save the downloaded JSON file securely
            """)
            
            st.markdown("""
            #### Step 5: Share Drive Folder with Service Account
            """)
            
            st.code("""
            1. Open Google Drive (https://drive.google.com)
            2. Create a folder called "Resume Customizer" (or any name you prefer)
            3. Right-click the folder and select "Share"
            4. Add the service account email address (from Step 3)
            5. Give "Editor" permissions
            6. Click "Send"
            """)
            
            st.success("""
            ✅ **Configuration Complete!**
            
            Now upload your credentials JSON file in the application's Google Drive configuration section.
            """)
        
        # File Format Guide
        st.subheader("📄 Supported Resume Formats")
        
        format_info = {
            "PDF Files (.pdf)": {
                "pros": ["Preserves formatting", "Widely accepted", "Professional appearance"],
                "cons": ["Harder to parse complex layouts", "May lose some text formatting"],
                "best_for": "Final resume versions for job applications",
                "tips": ["Use simple, clean layouts", "Avoid complex graphics", "Ensure text is selectable"]
            },
            "Word Documents (.docx)": {
                "pros": ["Easy to parse", "Retains structure", "Editable format"],
                "cons": ["Formatting may change across systems", "Version compatibility issues"],
                "best_for": "Working drafts and easy editing",
                "tips": ["Use standard fonts", "Avoid complex tables", "Keep formatting simple"]
            },
            "Text Files (.txt)": {
                "pros": ["100% parseable", "No formatting issues", "Lightweight"],
                "cons": ["No formatting", "Plain appearance", "Limited structure"],
                "best_for": "Quick testing and content extraction",
                "tips": ["Use clear section headers", "Maintain consistent formatting", "Use bullet points"]
            }
        }
        
        for format_name, info in format_info.items():
            with st.expander(f"📋 {format_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Pros:**")
                    for pro in info['pros']:
                        st.write(f"✅ {pro}")
                    
                    st.write("**Best For:**")
                    st.write(f"🎯 {info['best_for']}")
                
                with col2:
                    st.write("**Cons:**")
                    for con in info['cons']:
                        st.write(f"❌ {con}")
                    
                    st.write("**Tips:**")
                    for tip in info['tips']:
                        st.write(f"💡 {tip}")
    
    def render_best_practices(self):
        """Render the Best Practices section"""
        st.header("💡 Best Practices for Optimal Experience")
        
        # Resume Writing Best Practices
        st.subheader("📝 Resume Content Best Practices")
        
        practices_data = {
            "Content Structure": {
                "icon": "📋",
                "practices": [
                    "**Use Action Verbs**: Start bullet points with strong action verbs (Developed, Implemented, Led, Optimized)",
                    "**Quantify Everything**: Include numbers, percentages, and metrics wherever possible",
                    "**Show Impact**: Focus on business value and outcomes, not just technical details",
                    "**Be Specific**: Mention exact technologies, versions, and tools used",
                    "**Progressive Complexity**: Show growth from junior to senior level responsibilities"
                ]
            },
            "Technical Details": {
                "icon": "⚙️",
                "practices": [
                    "**Version Numbers**: Include framework/library versions when relevant (React 18.x, Python 3.9+)",
                    "**Architecture Patterns**: Mention design patterns and architectural decisions",
                    "**Performance Metrics**: Include load times, response times, and optimization results",
                    "**Scale Information**: Mention user base, data volume, or transaction volume",
                    "**Integration Details**: Describe how systems work together and data flows"
                ]
            },
            "Project Descriptions": {
                "icon": "🚀",
                "practices": [
                    "**Context First**: Start with business problem or opportunity",
                    "**Technology Stack**: List all major technologies used in the project",
                    "**Your Role**: Clearly define your specific contributions and responsibilities",
                    "**Challenges & Solutions**: Highlight problems solved and how you solved them",
                    "**Results**: Quantify the impact and success of the project"
                ]
            }
        }
        
        for category, info in practices_data.items():
            with st.expander(f"{info['icon']} {category}"):
                for practice in info['practices']:
                    st.markdown(f"• {practice}")
        
        # Application Usage Best Practices
        st.subheader("🎯 Application Usage Best Practices")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📂 File Organization**:
            - Keep master resume files in a dedicated folder
            - Use descriptive filenames with dates
            - Maintain version control for major changes
            - Regular backup of your resume database
            
            **🔄 Regular Maintenance**:
            - Update your master resume monthly
            - Review and update job requirements regularly
            - Clean up old or irrelevant customizations
            - Monitor email delivery success rates
            
            **📊 Analytics Usage**:
            - Review performance metrics weekly
            - Track which customizations get better responses
            - Analyze trending technologies in your field
            - Use insights to update your skill set
            """)
        
        with col2:
            st.markdown("""
            **🔒 Security Practices**:
            - Change API passwords regularly
            - Don't share credentials with others
            - Use strong, unique passwords
            - Monitor access logs regularly
            
            **⚡ Performance Tips**:
            - Upload resumes in recommended formats
            - Keep job descriptions concise but comprehensive
            - Use caching for frequently accessed data
            - Regular cleanup of temporary files
            
            **🎨 Customization Strategy**:
            - Create templates for different job types
            - Maintain consistent formatting across versions
            - Test email templates before mass sending
            - A/B test different resume approaches
            """)
        
        # Example Resume Points
        st.subheader("📋 Example Resume Points by Experience Level")
        
        experience_examples = {
            "Junior Developer (0-2 years)": [
                "• Built responsive web application using React.js and CSS3, implementing 5+ reusable components with 95% test coverage",
                "• Developed REST APIs using Node.js and Express.js, handling user authentication and data validation for 100+ concurrent users",
                "• Collaborated with senior developers to implement database schema in PostgreSQL, reducing query response time by 25%",
                "• Participated in code reviews and followed Git workflows, contributing 50+ commits to team repository"
            ],
            "Mid-Level Developer (2-5 years)": [
                "• Led development of microservices architecture using Docker and Kubernetes, improving system scalability by 200%",
                "• Implemented CI/CD pipeline using Jenkins and AWS, reducing deployment time from 2 hours to 15 minutes",
                "• Mentored 2 junior developers and conducted technical interviews, improving team productivity by 30%",
                "• Optimized database queries and implemented Redis caching, reducing page load time by 60% for 10K+ daily users"
            ],
            "Senior Developer (5+ years)": [
                "• Architected and delivered enterprise-scale e-commerce platform serving 500K+ users with 99.99% uptime using AWS and microservices",
                "• Led cross-functional team of 8 developers in migrating legacy system to cloud-native architecture, reducing operational costs by 40%",
                "• Established technical standards and best practices, resulting in 50% reduction in production bugs and improved code quality",
                "• Designed and implemented real-time analytics system processing 1M+ events daily using Apache Kafka and Apache Spark"
            ]
        }
        
        for level, examples in experience_examples.items():
            with st.expander(f"💼 {level}"):
                st.write("**Example bullet points:**")
                for example in examples:
                    st.markdown(example)
    
    def render_troubleshooting(self):
        """Render the Troubleshooting section"""
        st.header("🔍 Troubleshooting Guide")
        
        # Common Issues and Solutions
        issues_data = {
            "Gmail Authentication Issues": {
                "icon": "📧",
                "symptoms": [
                    "Email sending fails with authentication error",
                    "'Username and password not accepted' message",
                    "SMTP connection timeout"
                ],
                "solutions": [
                    "**Check App Password**: Ensure you're using the 16-character app password, not your regular Gmail password",
                    "**2-Step Verification**: Confirm that 2-Step Verification is enabled on your Google account",
                    "**Account Security**: Check if Google has blocked the sign-in attempt and approve it",
                    "**Network Issues**: Try different network connection or check firewall settings",
                    "**Regenerate Password**: Create a new app password if the current one isn't working"
                ]
            },
            "Google Drive API Issues": {
                "icon": "🗂️",
                "symptoms": [
                    "Failed to authenticate with Google Drive",
                    "Permission denied errors",
                    "Files not saving to Drive"
                ],
                "solutions": [
                    "**Credentials File**: Ensure the JSON credentials file is valid and properly uploaded",
                    "**Service Account Permissions**: Check that the service account has Editor access to your Drive folder",
                    "**API Enabled**: Verify Google Drive API is enabled in Google Cloud Console",
                    "**Quota Limits**: Check if you've exceeded API usage quotas",
                    "**File Path**: Ensure the target folder exists and is accessible"
                ]
            },
            "Resume Parsing Problems": {
                "icon": "📄",
                "symptoms": [
                    "Text extraction is incomplete or garbled",
                    "Special characters not displaying correctly",
                    "Sections not properly identified"
                ],
                "solutions": [
                    "**File Format**: Try converting complex PDFs to simpler formats or DOCX",
                    "**Layout Issues**: Use resumes with simple, standard layouts without complex graphics",
                    "**Text Selection**: Ensure text in PDF is selectable (not scanned images)",
                    "**Font Issues**: Use standard fonts like Arial, Times New Roman, or Calibri",
                    "**File Size**: Ensure file size is under 10MB for optimal processing"
                ]
            },
            "Application Performance Issues": {
                "icon": "⚡",
                "symptoms": [
                    "Slow response times",
                    "Application freezing or crashing",
                    "High memory usage"
                ],
                "solutions": [
                    "**Clear Cache**: Clear browser cache and restart the application",
                    "**File Size**: Reduce size of uploaded files if they're very large",
                    "**Browser Issues**: Try a different browser or update your current browser",
                    "**Memory**: Close other applications to free up system memory",
                    "**Network**: Check internet connection stability"
                ]
            },
            "AI Integration Issues": {
                "icon": "🤖",
                "symptoms": [
                    "AI responses are empty or error out",
                    "Slow AI processing",
                    "Generic or irrelevant suggestions"
                ],
                "solutions": [
                    "**API Keys**: Verify your OpenAI API key is valid and has sufficient credits",
                    "**Rate Limits**: Wait if you've exceeded API rate limits",
                    "**Input Quality**: Provide more detailed job requirements for better AI responses",
                    "**Model Selection**: Try different AI models if available",
                    "**Network**: Ensure stable internet connection for API calls"
                ]
            }
        }
        
        for issue_name, issue_info in issues_data.items():
            with st.expander(f"{issue_info['icon']} {issue_name}"):
                st.write("**Common Symptoms:**")
                for symptom in issue_info['symptoms']:
                    st.write(f"❗ {symptom}")
                
                st.write("\n**Solutions:**")
                for solution in issue_info['solutions']:
                    st.markdown(f"✅ {solution}")
        
        # Error Codes Reference
        st.subheader("🔢 Error Codes Reference")
        
        error_codes = {
            "EMAIL_001": "SMTP Authentication Failed - Check app password",
            "EMAIL_002": "Email sending timeout - Check network connection",
            "DRIVE_001": "Google Drive API authentication failed - Check credentials",
            "DRIVE_002": "Permission denied - Check service account permissions",
            "PARSE_001": "Resume parsing failed - Try different file format",
            "PARSE_002": "Text extraction incomplete - Check file integrity",
            "AI_001": "OpenAI API key invalid - Verify API key",
            "AI_002": "API rate limit exceeded - Wait before retrying",
            "APP_001": "Application startup failed - Check dependencies",
            "APP_002": "Memory allocation error - Restart application"
        }
        
        col1, col2 = st.columns(2)
        
        for i, (code, description) in enumerate(error_codes.items()):
            if i % 2 == 0:
                col1.code(f"{code}: {description}")
            else:
                col2.code(f"{code}: {description}")
        
        # Contact and Support
        st.subheader("📞 Getting Additional Help")
        
        st.info("""
        **If you're still experiencing issues:**
        
        1. **Check the Logs**: Look for error messages in the application logs
        2. **Restart the Application**: Sometimes a simple restart resolves issues
        3. **Update Dependencies**: Ensure all packages are up to date
        4. **Check Documentation**: Review this guide and the README file
        5. **Community Support**: Check GitHub issues for similar problems
        
        **When Reporting Issues:**
        - Provide the exact error message
        - Include steps to reproduce the problem
        - Mention your operating system and browser
        - Attach relevant log files (remove sensitive information)
        """)
        
        # System Information
        st.subheader("💻 System Requirements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Minimum Requirements:**
            - Python 3.8 or higher
            - 4GB RAM
            - 1GB free disk space
            - Internet connection
            - Modern web browser
            
            **Recommended:**
            - Python 3.9+
            - 8GB RAM
            - SSD storage
            - Stable broadband connection
            - Chrome, Firefox, or Edge browser
            """)
        
        with col2:
            st.markdown("""
            **Supported Platforms:**
            - Windows 10/11
            - macOS 10.15+
            - Linux (Ubuntu 18.04+)
            
            **Supported Browsers:**
            - Chrome (recommended)
            - Firefox
            - Safari
            - Edge
            
            **Not Supported:**
            - Internet Explorer
            - Very old browser versions
            """)

# Create singleton instance
app_guide = ApplicationGuide()
