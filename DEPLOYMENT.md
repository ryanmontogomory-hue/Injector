# 🚀 Resume Customizer Deployment Guide

This guide provides multiple deployment options for your Resume Customizer Streamlit application.

## 📋 Prerequisites

- Python 3.9 or higher
- Git (for version control)
- A GitHub account (for most deployment methods)

## 🌟 Deployment Options

### 1. 🔵 Streamlit Cloud (Recommended - FREE)

**Pros**: Free, easy setup, automatic deployments, built for Streamlit
**Cons**: Public repository required (unless you have Streamlit Cloud Pro)

#### Steps:

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/resume-customizer.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Configuration** (Optional):
   - Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Add any configuration in Streamlit Cloud dashboard

#### URL Format:
Your app will be available at: `https://yourusername-resume-customizer-app-xxxxxx.streamlit.app`

---

### 2. ☁️ Heroku (Simple PaaS)

**Pros**: Easy deployment, good for small apps
**Cons**: Requires credit card, limited free tier

#### Setup:

1. **Install Heroku CLI**:
   - Download from [heroku.com](https://devcenter.heroku.com/articles/heroku-cli)

2. **Create Procfile**:
   ```bash
   echo "web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile
   ```

3. **Deploy**:
   ```bash
   heroku login
   heroku create your-resume-customizer-app
   git push heroku main
   ```

#### URL Format:
`https://your-resume-customizer-app.herokuapp.com`

---

### 3. 🔥 Railway (Modern Alternative to Heroku)

**Pros**: Simple, modern, generous free tier
**Cons**: Newer platform

#### Steps:

1. **Visit [railway.app](https://railway.app)**
2. **Connect GitHub account**
3. **Create new project from GitHub repo**
4. **Set custom start command**:
   ```
   streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

---

### 4. 💻 Local Development Deployment

#### Option A: Virtual Environment (Recommended)

1. **Create virtual environment**:
   ```bash
   python -m venv resume_customizer_env
   
   # Windows
   resume_customizer_env\Scripts\activate
   
   # macOS/Linux
   source resume_customizer_env/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

#### Option B: Direct Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

### 5. 🌐 Self-Hosted on VPS

**For Advanced Users**

1. **Setup VPS** (Ubuntu/CentOS)
2. **Install dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3-pip nginx
   pip3 install -r requirements.txt
   ```

3. **Create systemd service**:
   ```bash
   sudo nano /etc/systemd/system/resume-customizer.service
   ```

4. **Configure reverse proxy with Nginx**
5. **Set up SSL with Let's Encrypt**

---

## 🔧 Configuration Tips

### Environment Variables

Create `.env` file from template:
```bash
cp .env.example .env
# Edit .env with your values
```

### Security Considerations

1. **Email Credentials**: Never hardcode in the app
2. **HTTPS**: Always use HTTPS in production
3. **File Upload Limits**: Configure appropriate limits
4. **Rate Limiting**: Consider implementing for production

### Performance Optimization

1. **Memory Limits**: Configure for your deployment platform
2. **Worker Processes**: Adjust based on traffic
3. **File Cleanup**: Implement cleanup for temporary files

---

## 🎯 Quick Start Commands

### Streamlit Cloud (Fastest):
```bash
git init && git add . && git commit -m "Deploy" && git push
# Then deploy via Streamlit Cloud UI
```

### Docker (Production):
```bash
docker-compose up -d
```

### Local Development:
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🆘 Troubleshooting

### Common Issues:

1. **Dependencies not found**: Check `requirements.txt`
2. **Port issues**: Ensure port 8501 is available
3. **Memory issues**: Large file uploads may need more memory
4. **SMTP errors**: Check email configuration and firewall

### Debug Mode:

Add to your app:
```python
import streamlit as st
st.write("Debug info:", st.secrets if hasattr(st, 'secrets') else "No secrets")
```

### Check Logs:

- **Streamlit Cloud**: Check app logs in dashboard
- **Docker**: `docker logs container-name`
- **Heroku**: `heroku logs --tail`
- **Local**: Terminal output

---

## 📈 Scaling Considerations

### For High Traffic:

1. **Load Balancing**: Use multiple instances
2. **Database**: Consider adding Redis for session storage
3. **CDN**: Use CloudFlare for static assets
4. **Monitoring**: Implement health checks

### Cost Optimization:

1. **Streamlit Cloud**: Free for public repos
2. **Railway**: Generous free tier
3. **Docker on VPS**: Most cost-effective for high traffic
4. **Cloud Functions**: Consider for serverless approach

---

## 🎉 Success!

Once deployed, your Resume Customizer will be accessible at your chosen URL. Users can:

- Upload multiple resumes
- Customize with tech stacks
- Preview changes
- Send via email
- Download customized resumes
- Use bulk processing for multiple files

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify all configuration files
3. Test locally first
4. Check platform-specific documentation

Happy deploying! 🚀
