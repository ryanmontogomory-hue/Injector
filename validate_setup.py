#!/usr/bin/env python3
"""
Setup validation script for Resume Customizer deployment
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.9+ is required")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'streamlit',
        'docx',  # python-docx imports as 'docx'
        'mammoth',
        'decouple',  # python-decouple imports as 'decouple'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def check_files():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'README.md',
        'DEPLOYMENT.md',
        '.gitignore',
        '.env.example',
        '.streamlit/config.toml',
        '.streamlit/secrets.toml.example',
    ]
    
    missing_files = []
    current_dir = Path('.')
    
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} is missing")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_streamlit_config():
    """Test basic Streamlit functionality"""
    try:
        result = subprocess.run(['streamlit', '--version'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Streamlit is working: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Streamlit test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Streamlit test error: {e}")
        return False

def check_app_syntax():
    """Check if app.py has valid syntax"""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Try to compile the code
        compile(code, 'app.py', 'exec')
        print("✅ app.py syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ app.py syntax error: {e}")
        return False
    except FileNotFoundError:
        print("❌ app.py file not found")
        return False

def check_docker_setup():
    """Check if Docker setup is valid"""
    docker_files = ['Dockerfile', 'docker-compose.yml']
    all_exist = True
    
    for file in docker_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} is missing")
            all_exist = False
    
    # Check if Docker is installed (optional)
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Docker is available: {result.stdout.strip()}")
        else:
            print("⚠️ Docker not found (optional for local development)")
    except:
        print("⚠️ Docker not found (optional for local development)")
    
    return all_exist

def check_git_setup():
    """Check if Git is set up"""
    try:
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Git is available: {result.stdout.strip()}")
            
            # Check if it's a git repository
            if os.path.exists('.git'):
                print("✅ Git repository initialized")
            else:
                print("⚠️ Git repository not initialized (run: git init)")
            return True
        else:
            print("❌ Git not found")
            return False
    except:
        print("❌ Git not found")
        return False

def main():
    """Run all validation checks"""
    print("🔍 Resume Customizer Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Required Files", check_files),
        ("Streamlit Setup", check_streamlit_config),
        ("App Syntax", check_app_syntax),
        ("Docker Setup", check_docker_setup),
        ("Git Setup", check_git_setup),
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            if check_func():
                passed_checks += 1
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 SUMMARY: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("🎉 All checks passed! Your setup is ready for deployment.")
        print("\n🚀 Next Steps:")
        print("1. Test locally: streamlit run app.py")
        print("2. Choose deployment method from DEPLOYMENT.md")
        print("3. Set up version control: git init && git add .")
        return True
    else:
        print("⚠️ Some checks failed. Please address the issues above.")
        print("\n🛠️ Common fixes:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Ensure all files are in place")
        print("- Check Python version compatibility")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
