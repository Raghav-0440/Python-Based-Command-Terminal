#!/usr/bin/env python3
"""
Simple launcher for the Web Terminal
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'flask', 'flask_socketio', 'psutil', 'requests', 'pathlib2', 
        'python_socketio', 'eventlet'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Installing missing packages...")
        
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'web_requirements.txt'])
            print("✅ All packages installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages. Please run:")
            print("   pip install -r web_requirements.txt")
            return False
    
    return True

def open_browser():
    """Open browser after a short delay."""
    time.sleep(2)
    webbrowser.open('http://localhost:5000')

def main():
    """Main launcher function."""
    print("🚀 AI-Powered Web Terminal Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        input("Press Enter to exit...")
        return
    
    print("\n🌐 Starting Web Terminal Server...")
    print("🎯 Features:")
    print("   • Python Commands + Natural English")
    print("   • AI Integration with Gemini API")
    print("   • Real-time Web Interface")
    print("   • Session-based Command History")
    print("\n🌐 Opening browser in 2 seconds...")
    print("   URL: http://localhost:5000")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the web server
    try:
        from web_terminal import app, socketio
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Web Terminal stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
