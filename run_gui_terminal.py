#!/usr/bin/env python3
"""
GUI Terminal Launcher
Simple launcher script for the GUI terminal application
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_terminal import main
    main()
except ImportError as e:
    print(f"Error importing GUI terminal: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting GUI terminal: {e}")
    sys.exit(1)
