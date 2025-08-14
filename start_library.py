#!/usr/bin/env python3
"""
Library Management System Starter Script
=========================================

This script starts your Flask library management system and displays access information.

Demo Login Credentials:
- Librarian: username='librarian', password='admin123'
- Student: username='student', password='student123'
"""

import subprocess
import sys
import time
import webbrowser
from threading import Timer

def print_header():
    print("=" * 60)
    print("🏛️  LIBRARY MANAGEMENT SYSTEM")
    print("=" * 60)
    print()

def print_access_info():
    print("📋 ACCESS INFORMATION:")
    print("-" * 40)
    print("🌐 Local URL: http://localhost:8080")
    print("🌐 Network URL: http://127.0.0.1:8080")
    print()
    print("👤 DEMO LOGIN CREDENTIALS:")
    print("-" * 40)
    print("📚 Librarian Account:")
    print("   Username: librarian")
    print("   Password: admin123")
    print()
    print("🎓 Student Account:")
    print("   Username: student")
    print("   Password: student123")
    print() 
    print("=" * 60)
    print("✨ The login page will automatically redirect you to the")
    print("   appropriate dashboard based on your account type!")
    print("=" * 60)
    print()

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)
    try:
        webbrowser.open('http://localhost:8080')
        print("🚀 Opening browser to http://localhost:8080")
    except:
        print("⚠️  Could not automatically open browser")

def main():
    print_header()
    print_access_info()
    
    print("🚀 Starting Flask server...")
    print("   Press Ctrl+C to stop the server")
    print()
    
    # Start browser opening in background
    timer = Timer(3.0, open_browser)
    timer.start()
    
    try:
        # Start the Flask app
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n")
        print("👋 Server stopped. Thank you for using the Library Management System!")
    except FileNotFoundError:
        print("❌ Error: app.py not found in current directory")
        print("   Please make sure you're in the correct directory")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()
