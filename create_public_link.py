#!/usr/bin/env python3
from pyngrok import ngrok
import time
import subprocess
import sys

def create_public_link():
    print("🚀 Setting up public access to your Library Website...")
    print("=" * 50)
    
    try:
        # Kill any existing ngrok processes
        ngrok.kill()
        
        # Create a tunnel to port 8080 where your Flask app is running
        public_tunnel = ngrok.connect(8081)
        public_url = public_tunnel.public_url
        
        print(f"✅ SUCCESS! Your library website is now publicly accessible at:")
        print(f"🌐 {public_url}")
        print("=" * 50)
        print("\n📋 Demo Login Credentials:")
        print("👨‍🎓 Student Login:")
        print("   Username: student")
        print("   Password: student123")
        print("\n👩‍🏫 Librarian Login:")
        print("   Username: librarian") 
        print("   Password: admin123")
        print("\n" + "=" * 50)
        print("⚠️  Note: This link will stay active as long as this script is running.")
        print("💡 Share this link with others to access your library website!")
        print("🔄 The link will automatically update if your Flask app restarts.")
        print("\n⏹️  Press Ctrl+C to stop the public tunnel")
        
        # Keep the tunnel alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down public tunnel...")
            ngrok.kill()
            print("✅ Public tunnel closed successfully!")
            
    except Exception as e:
        print(f"❌ Error creating public tunnel: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure your Flask app is running on port 8080")
        print("2. Check if ngrok is installed properly")
        print("3. Ensure no firewall is blocking the connection")

if __name__ == "__main__":
    create_public_link()
