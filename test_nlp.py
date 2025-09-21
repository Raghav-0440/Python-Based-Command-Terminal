#!/usr/bin/env python3
"""
Test script for natural language processing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from smart_terminal import SmartTerminal

def test_nlp():
    terminal = SmartTerminal()
    
    test_cases = [
        "create a file named hello",
        "delete the file named hello", 
        "create a folder called test",
        "list files",
        "show me all running processes",
        "check CPU usage"
    ]
    
    print("Testing Natural Language Processing:")
    print("=" * 50)
    
    for test_input in test_cases:
        command = terminal.process_input(test_input)
        print(f"Input: '{test_input}'")
        print(f"Command: '{command}'")
        print("-" * 30)

if __name__ == "__main__":
    test_nlp()
