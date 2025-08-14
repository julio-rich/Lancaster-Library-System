#!/usr/bin/env python3
"""
Quick Launch Script for Library Management System
================================================

This script starts the Flask server and displays access information.
"""

import sys
import os

def main():
    print("\n" + "="*60)
    print("🏛️  LIBRARY MANAGEMENT SYSTEM")
    print("="*60)
    print()
    print("🌐 Access URLs:")
    print("   • http://localhost:8081")
    print("   • http://127.0.0.1:8081")
    print()
    print("👤 Demo Login Credentials:")
    print("   📚 Librarian: librarian / admin123")
    print("   🎓 Student: student / student123")
    print()
    print("✨ The login redirects automatically to the correct dashboard!")
    print("="*60)
    print()
    print("🚀 Starting server... (Press Ctrl+C to stop)")
    print()
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thank you!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
