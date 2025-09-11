#!/usr/bin/env python3
"""
Redis Management Script
Provides easy commands to manage Redis server for your resume processing app.
"""

import subprocess
import sys
import time
import os

def run_command(command, shell=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_redis_status():
    """Check if Redis service is running."""
    success, stdout, stderr = run_command('powershell "Get-Service -Name Redis | Select-Object Status"')
    if success and "Running" in stdout:
        return True, "Redis service is running"
    else:
        return False, "Redis service is not running"

def start_redis():
    """Start Redis service."""
    print("🚀 Starting Redis service...")
    success, stdout, stderr = run_command('powershell "Start-Service -Name Redis"')
    if success:
        print("✅ Redis service started successfully!")
        return True
    else:
        print(f"❌ Failed to start Redis service: {stderr}")
        return False

def stop_redis():
    """Stop Redis service."""
    print("🛑 Stopping Redis service...")
    success, stdout, stderr = run_command('powershell "Stop-Service -Name Redis"')
    if success:
        print("✅ Redis service stopped successfully!")
        return True
    else:
        print(f"❌ Failed to stop Redis service: {stderr}")
        return False

def restart_redis():
    """Restart Redis service."""
    print("🔄 Restarting Redis service...")
    stop_redis()
    time.sleep(2)
    return start_redis()

def test_redis_connection():
    """Test Redis connection with ping."""
    print("🔍 Testing Redis connection...")
    success, stdout, stderr = run_command('C:\\redis\\redis-cli.exe ping')
    if success and "PONG" in stdout:
        print("✅ Redis connection successful!")
        print("📡 Redis server is responding on localhost:6379")
        return True
    else:
        print("❌ Redis connection failed!")
        print(f"Error: {stderr}")
        return False

def show_redis_info():
    """Show Redis server information."""
    print("ℹ️  Redis Server Information:")
    success, stdout, stderr = run_command('C:\\redis\\redis-cli.exe info server')
    if success:
        for line in stdout.split('\n'):
            if line.startswith('redis_version:') or line.startswith('tcp_port:') or line.startswith('uptime_in_seconds:'):
                print(f"  {line}")
    
    # Show service status
    is_running, status_msg = check_redis_status()
    print(f"  Service Status: {'🟢 Running' if is_running else '🔴 Stopped'}")

def show_celery_status():
    """Show Celery configuration status."""
    print("\n📋 Celery Configuration Status:")
    try:
        from celeryconfig import CELERY_BROKER_URL, CELERY_RESULT_BACKEND
        print(f"  Broker: {CELERY_BROKER_URL}")
        print(f"  Backend: {CELERY_RESULT_BACKEND}")
        
        if 'redis' in CELERY_BROKER_URL.lower():
            print("  ✅ Using Redis broker (high performance)")
        else:
            print("  ⚠️  Using filesystem broker (fallback)")
            
    except Exception as e:
        print(f"  ❌ Error loading Celery config: {e}")

def main():
    """Main menu for Redis management."""
    print("🔴 Redis Management Tool")
    print("=" * 40)
    
    while True:
        print("\nChoose an option:")
        print("1. Check Redis status")
        print("2. Start Redis service")
        print("3. Stop Redis service")
        print("4. Restart Redis service")
        print("5. Test Redis connection")
        print("6. Show Redis info")
        print("7. Show Celery status")
        print("8. Exit")
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == '1':
            is_running, msg = check_redis_status()
            print(f"{'✅' if is_running else '❌'} {msg}")
            
        elif choice == '2':
            start_redis()
            
        elif choice == '3':
            stop_redis()
            
        elif choice == '4':
            restart_redis()
            
        elif choice == '5':
            test_redis_connection()
            
        elif choice == '6':
            show_redis_info()
            
        elif choice == '7':
            show_celery_status()
            
        elif choice == '8':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
