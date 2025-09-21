#!/usr/bin/env python3
"""
Production server starter for Render deployment
This file provides an alternative way to start the web terminal
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app
from web_terminal import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    
    print(f"🚀 Starting AI-Powered Web Terminal on port {port}")
    print("✨ Features: Python Commands + Natural English + AI Processing")
    
    # Try gunicorn first, fallback to Flask dev server
    try:
        import gunicorn.app.wsgiapp as wsgi
        sys.argv = ['gunicorn', '--worker-class', 'sync', '-w', '1', 
                   '--bind', f'0.0.0.0:{port}', 'web_terminal:app']
        wsgi.run()
    except ImportError:
        print("⚠️  Gunicorn not found, using Flask development server")
        socketio.run(app, debug=debug, host='0.0.0.0', port=port)
