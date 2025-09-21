#!/usr/bin/env python3
"""
GUI Python Terminal with AI Integration
A Tkinter-based GUI version of the unified terminal with all features:
- Dual input (Python commands + Natural English)
- AI integration with Gemini API
- Command history and auto-completion
- Visual indicators and professional formatting
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import sys
import subprocess
import shutil
import psutil
import json
import re
import requests
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class GUITerminal:
    """GUI Terminal with all CLI features integrated."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 AI-Powered Python Terminal")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(True, True)
        
        # Set window icon and properties
        self.root.iconbitmap(default='')  # You can add an icon file here
        self.root.attributes('-alpha', 0.95)  # Slight transparency
        
        # Terminal state
        self.current_dir = os.getcwd()
        self.gemini_api_key = "AIzaSyCknv4gzEzQj1ThRx8uEs_w1IqAo4dxC9c"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Supported commands
        self.supported_commands = {
            'dir', 'cd', 'mkdir', 'rmdir', 'del', 'copy', 'move', 'ren', 'type', 'touch',
            'tasklist', 'taskkill', 'cpu', 'mem', 'ipconfig', 'ping', 'netstat', 
            'cls', 'echo', 'help', 'exit', 'quit', 'pwd', 'ls', 'rm', 'mv', 'cp', 'cat', 'ps', 'kill', 'clear', 'history'
        }
        
        # Command history
        self.command_history = []
        self.history_index = -1
        self.current_input = ""
        
        # Auto-completion
        self.completion_options = []
        self.completion_index = -1
        
        self.setup_ui()
        self.load_history()
        
    def setup_ui(self):
        """Setup the modern GUI interface."""
        # Configure modern styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color scheme
        self.colors = {
            'bg_primary': '#0a0a0a',
            'bg_secondary': '#1a1a1a',
            'bg_tertiary': '#2a2a2a',
            'accent_blue': '#00d4ff',
            'accent_green': '#00ff88',
            'accent_purple': '#8b5cf6',
            'accent_orange': '#ff6b35',
            'text_primary': '#ffffff',
            'text_secondary': '#b3b3b3',
            'text_muted': '#666666',
            'border': '#333333',
            'success': '#00ff88',
            'error': '#ff4757',
            'warning': '#ffa502',
            'info': '#3742fa'
        }
        
        # Configure styles
        style.configure('Modern.TFrame', background=self.colors['bg_primary'])
        style.configure('Card.TFrame', background=self.colors['bg_secondary'], relief='flat', borderwidth=1)
        style.configure('Modern.TLabel', background=self.colors['bg_primary'], foreground=self.colors['text_primary'])
        style.configure('Title.TLabel', background=self.colors['bg_primary'], foreground=self.colors['accent_blue'], font=('Segoe UI', 20, 'bold'))
        style.configure('Subtitle.TLabel', background=self.colors['bg_primary'], foreground=self.colors['text_secondary'], font=('Segoe UI', 10))
        
        # Main container with gradient-like effect
        main_frame = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header section with modern design
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_secondary'], height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Title with gradient effect simulation
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        title_frame.pack(expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(title_frame, text="🚀 AI-Powered Python Terminal", 
                              bg=self.colors['bg_secondary'], fg=self.colors['accent_blue'], 
                              font=('Segoe UI', 18, 'bold'))
        title_label.pack(pady=15)
        
        # Subtitle with status
        subtitle_label = tk.Label(title_frame, text="Advanced Command Interface with Natural Language Processing", 
                                 bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'], 
                                 font=('Segoe UI', 10))
        subtitle_label.pack()
        
        # Main content area
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Terminal output area with modern styling
        output_card = tk.Frame(content_frame, bg=self.colors['bg_secondary'], relief='flat', bd=1)
        output_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Output header
        output_header = tk.Frame(output_card, bg=self.colors['bg_tertiary'], height=30)
        output_header.pack(fill=tk.X)
        output_header.pack_propagate(False)
        
        # Terminal title
        terminal_title = tk.Label(output_header, text="💻 Terminal Output", 
                                 bg=self.colors['bg_tertiary'], fg=self.colors['accent_green'], 
                                 font=('Segoe UI', 10, 'bold'))
        terminal_title.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Terminal controls (simulated)
        controls_frame = tk.Frame(output_header, bg=self.colors['bg_tertiary'])
        controls_frame.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Simulated terminal buttons
        for i, color in enumerate([self.colors['error'], self.colors['warning'], self.colors['success']]):
            btn = tk.Label(controls_frame, text="●", bg=color, fg=color, font=('Arial', 8))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Output area with modern styling
        self.output_area = scrolledtext.ScrolledText(
            output_card,
            height=20,
            width=100,
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=('Consolas', 11),
            insertbackground=self.colors['accent_blue'],
            selectbackground=self.colors['accent_blue'],
            selectforeground=self.colors['bg_primary'],
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief='flat',
            bd=0,
            padx=15,
            pady=10
        )
        self.output_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Input section with modern design
        input_card = tk.Frame(content_frame, bg=self.colors['bg_secondary'], relief='flat', bd=1)
        input_card.pack(fill=tk.X, pady=(0, 15))
        
        # Input header
        input_header = tk.Frame(input_card, bg=self.colors['bg_tertiary'], height=25)
        input_header.pack(fill=tk.X)
        input_header.pack_propagate(False)
        
        # Current directory display
        self.dir_label = tk.Label(input_header, text=f"📁 {os.path.basename(self.current_dir)}", 
                                 bg=self.colors['bg_tertiary'], fg=self.colors['accent_purple'], 
                                 font=('Consolas', 10, 'bold'))
        self.dir_label.pack(side=tk.LEFT, padx=10, pady=3)
        
        # Command prompt
        prompt_label = tk.Label(input_header, text="$", 
                               bg=self.colors['bg_tertiary'], fg=self.colors['accent_orange'], 
                               font=('Consolas', 12, 'bold'))
        prompt_label.pack(side=tk.RIGHT, padx=10, pady=3)
        
        # Input entry with modern styling
        self.input_entry = tk.Entry(
            input_card,
            bg=self.colors['bg_primary'],
            fg=self.colors['text_primary'],
            font=('Consolas', 13),
            insertbackground=self.colors['accent_blue'],
            selectbackground=self.colors['accent_blue'],
            selectforeground=self.colors['bg_primary'],
            relief='flat',
            bd=0,
            highlightthickness=2,
            highlightcolor=self.colors['accent_blue'],
            highlightbackground=self.colors['border']
        )
        self.input_entry.pack(fill=tk.X, padx=15, pady=15)
        self.input_entry.bind('<Return>', self.execute_command)
        self.input_entry.bind('<Up>', self.history_up)
        self.input_entry.bind('<Down>', self.history_down)
        self.input_entry.bind('<Tab>', self.auto_complete)
        self.input_entry.bind('<KeyRelease>', self.on_key_release)
        self.input_entry.bind('<FocusIn>', self._on_input_focus_in)
        self.input_entry.bind('<FocusOut>', self._on_input_focus_out)
        
        # Status bar with modern design
        status_card = tk.Frame(content_frame, bg=self.colors['bg_secondary'], relief='flat', bd=1)
        status_card.pack(fill=tk.X)
        
        # Status content
        status_content = tk.Frame(status_card, bg=self.colors['bg_secondary'])
        status_content.pack(fill=tk.X, padx=15, pady=8)
        
        # Status indicators
        status_left = tk.Frame(status_content, bg=self.colors['bg_secondary'])
        status_left.pack(side=tk.LEFT)
        
        # Connection status
        self.connection_status = tk.Label(status_left, text="🟢 Connected", 
                                         bg=self.colors['bg_secondary'], fg=self.colors['success'], 
                                         font=('Segoe UI', 9))
        self.connection_status.pack(side=tk.LEFT, padx=(0, 15))
        
        # AI status
        self.ai_status = tk.Label(status_left, text="🤖 AI Ready", 
                                 bg=self.colors['bg_secondary'], fg=self.colors['accent_blue'], 
                                 font=('Segoe UI', 9))
        self.ai_status.pack(side=tk.LEFT, padx=(0, 15))
        
        # Main status
        self.status_label = tk.Label(status_content, text="Ready | Use ↑↓ for history, Tab for completion", 
                                    bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'], 
                                    font=('Segoe UI', 9))
        self.status_label.pack(side=tk.RIGHT)
        
        # Focus on input
        self.input_entry.focus()
        
        # Welcome message with modern styling
        self.add_output("🚀 AI-Powered Python Terminal v2.0", self.colors['accent_blue'])
        self.add_output("=" * 80, self.colors['accent_green'])
        self.add_output("✨ Features: Python Commands + Natural English + AI Processing", self.colors['text_primary'])
        self.add_output("🎯 Type 'help' for available commands, 'exit' to quit", self.colors['text_secondary'])
        self.add_output("=" * 80, self.colors['accent_green'])
        self.add_output("")
        
        # Start status animation
        self._animate_status()
        
        # Add some visual enhancements
        self._add_visual_effects()
        
    def add_output(self, text, color=None):
        """Add text to the output area with color."""
        if color is None:
            color = self.colors['text_primary']
            
        self.output_area.config(state=tk.NORMAL)
        
        # Configure tag for this color
        tag_name = f"color_{color.replace('#', '')}"
        self.output_area.tag_configure(tag_name, foreground=color)
        
        # Insert text with color
        start_pos = self.output_area.index(tk.END)
        self.output_area.insert(tk.END, text + '\n')
        end_pos = self.output_area.index(tk.END)
        self.output_area.tag_add(tag_name, start_pos, end_pos)
        
        self.output_area.config(state=tk.DISABLED)
        self.output_area.see(tk.END)
        
    def _on_input_focus_in(self, event):
        """Handle input focus in event."""
        self.input_entry.config(highlightbackground=self.colors['accent_blue'])
        
    def _on_input_focus_out(self, event):
        """Handle input focus out event."""
        self.input_entry.config(highlightbackground=self.colors['border'])
        
    def _animate_status(self):
        """Animate status indicators."""
        # Rotate through different status messages
        status_messages = [
            "Ready | Use ↑↓ for history, Tab for completion",
            "AI Processing Available | Natural Language Supported",
            "System Online | All Commands Available",
            "Ready | Use ↑↓ for history, Tab for completion"
        ]
        
        if hasattr(self, '_status_index'):
            self._status_index = (self._status_index + 1) % len(status_messages)
        else:
            self._status_index = 0
            
        self.status_label.config(text=status_messages[self._status_index])
        
        # Schedule next animation
        self.root.after(3000, self._animate_status)
        
    def _add_visual_effects(self):
        """Add visual effects to enhance the GUI."""
        # Add subtle border effects
        self._add_border_effects()
        
        # Add typing animation for welcome message
        self._type_welcome_message()
        
    def _add_border_effects(self):
        """Add subtle border effects to cards."""
        # This creates a subtle glow effect simulation
        pass  # Placeholder for future enhancements
        
    def _type_welcome_message(self):
        """Add a typing effect to the welcome message."""
        welcome_text = "Welcome to the future of terminal interfaces! 🚀"
        self.add_output("", self.colors['accent_green'])
        self.add_output("🎉 " + "=" * 60, self.colors['accent_green'])
        self.add_output("", self.colors['accent_green'])
        
        # Add some fun ASCII art
        ascii_art = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    🚀 AI-Powered Terminal Interface v2.0                    ║
    ║                                                              ║
    ║    ✨ Features:                                              ║
    ║       • Natural Language Processing                          ║
    ║       • Advanced Command Recognition                         ║
    ║       • Modern GUI with Visual Effects                      ║
    ║       • Real-time Status Updates                            ║
    ║                                                              ║
    ║    🎯 Ready to revolutionize your workflow!                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
        """
        
        for line in ascii_art.split('\n'):
            if line.strip():
                self.add_output(line, self.colors['accent_blue'])
            else:
                self.add_output("")
        
        self.add_output("", self.colors['accent_green'])
        self.add_output("🎉 " + "=" * 60, self.colors['accent_green'])
        self.add_output("")
        
    def execute_command(self, event=None):
        """Execute the command entered by the user."""
        command = self.input_entry.get().strip()
        if not command:
            return
            
        # Add to history
        self.add_to_history(command)
        
        # Clear input
        self.input_entry.delete(0, tk.END)
        
        # Show command in output with modern styling
        self.add_output(f"💻 {os.path.basename(self.current_dir)}$ {command}", self.colors['accent_blue'])
        
        # Disable input while processing
        self.input_entry.config(state='disabled')
        self.status_label.config(text="Processing command...")
        
        # Process and execute command in a separate thread for GUI responsiveness
        def run_command():
            try:
                # Check if it's a Python command
                if self._is_python_command(command):
                    result = self._execute_command(command)
                else:
                    # Convert natural language to command
                    converted_command = self._convert_natural_language(command)
                    self.root.after(0, lambda: self.add_output(f"🔄 Converted: '{command}' → '{converted_command}'", self.colors['accent_orange']))
                    result = self._execute_command(converted_command)
                
                # Display result in main thread
                if result:
                    self.root.after(0, lambda: self.add_output(result))
                    
            except Exception as e:
                self.root.after(0, lambda: self.add_output(f"❌ Error: {str(e)}", self.colors['error']))
            
            # Re-enable input and update status
            self.root.after(0, self._command_finished)
        
        # Start command execution in background thread
        thread = threading.Thread(target=run_command, daemon=True)
        thread.start()
        
    def _command_finished(self):
        """Called when command execution is finished."""
        self.input_entry.config(state='normal')
        self.status_label.config(text="Ready | Use ↑↓ for history, Tab for completion")
        self.add_output("")  # Empty line for readability
        self.input_entry.focus()
        
        # Update AI status to show it's processing
        self.ai_status.config(text="🤖 AI Ready", fg=self.colors['accent_blue'])
        
    def _is_python_command(self, input_text: str) -> bool:
        """Check if input is already a valid Python terminal command."""
        parts = input_text.strip().split()
        if not parts:
            return False
        command = parts[0].lower()
        return command in self.supported_commands
        
    def _convert_natural_language(self, natural_input: str) -> str:
        """Convert natural language to Python terminal command using Gemini API."""
        try:
            # Try Gemini API first
            command = self._try_gemini_api(natural_input)
            if command and command != "help":
                return command
        except:
            pass
        
        # Fallback to pattern matching
        return self._fallback_conversion(natural_input)
        
    def _try_gemini_api(self, natural_input: str) -> str:
        """Try to convert using Gemini API."""
        try:
            prompt = f"""
Convert this natural language input to a Python terminal command.
Supported commands: dir, cd, mkdir, rmdir, del, copy, move, ren, type, tasklist, taskkill, cpu, mem, ipconfig, ping, netstat, cls, echo, help, exit

Input: "{natural_input}"

Rules:
- Only return the executable command, no explanations
- Use proper syntax for each command
- For file operations, use current directory if path not specified
- Commands must be safe to execute

Examples:
- "list files in current directory" → "dir"
- "create a folder called test" → "mkdir test"
- "delete the file hello.txt" → "del hello.txt"
- "show all running processes" → "tasklist"
- "check CPU usage" → "cpu"

Return only the command:
"""

            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            headers = {"Content-Type": "application/json"}
            url = f"{self.gemini_url}?key={self.gemini_api_key}"
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    command = content.strip().strip('"').strip("'")
                    return command
                    
        except Exception:
            pass
        
        return None
        
    def _fallback_conversion(self, natural_input: str) -> str:
        """Fallback conversion using flexible pattern matching."""
        input_lower = natural_input.lower().strip()
        
        # More flexible pattern matching - check for any action words first
        action_words = {
            'list': ['list', 'show', 'display', 'see', 'view', 'ls'],
            'create': ['create', 'make', 'new', 'add', 'generate', 'build'],
            'delete': ['delete', 'remove', 'del', 'erase', 'destroy', 'kill'],
            'move': ['move', 'transfer', 'relocate', 'shift'],
            'copy': ['copy', 'duplicate', 'clone', 'backup'],
            'rename': ['rename', 'ren', 'change name', 'rechristen'],
            'read': ['read', 'view', 'show', 'display', 'open', 'cat'],
            'echo': ['echo', 'print', 'say', 'output', 'display'],
            'process': ['process', 'running', 'task', 'programs'],
            'cpu': ['cpu', 'processor', 'processing'],
            'memory': ['memory', 'ram', 'mem'],
            'network': ['network', 'ip', 'configuration', 'config'],
            'ping': ['ping', 'test connection', 'check connection'],
            'clear': ['clear', 'clean', 'wipe'],
            'help': ['help', 'commands', 'what can you do'],
            'exit': ['exit', 'quit', 'close', 'bye', 'goodbye']
        }
        
        # Check for directory listing
        if any(word in input_lower for word in action_words['list']):
            if any(word in input_lower for word in ['file', 'directory', 'folder', 'contents', 'what', 'here']):
                return "dir"
            elif any(word in input_lower for word in ['process', 'running', 'task', 'program']):
                return "tasklist"
            else:
                return "dir"  # Default to listing files
        
        # Check for file/folder creation
        if any(word in input_lower for word in action_words['create']):
            # Extract name from various patterns
            name = self._extract_flexible_name(input_lower, ['file', 'folder', 'directory', 'document'])
            if name:
                # Check if it's a file (has extension) or folder
                if '.' in name and not name.endswith('/'):
                    return f"touch {name}"  # Create empty file
                else:
                    return f"mkdir {name}"
            else:
                return "mkdir new_folder"
        
        # Check for deletion
        if any(word in input_lower for word in action_words['delete']):
            name = self._extract_flexible_name(input_lower, ['file', 'folder', 'directory', 'document'])
            if name:
                return f"del {name}"
            else:
                return "del file.txt"
        
        # Check for moving
        if any(word in input_lower for word in action_words['move']):
            return self._extract_move_command(input_lower)
        
        # Check for copying
        if any(word in input_lower for word in action_words['copy']):
            return self._extract_copy_command(input_lower)
        
        # Check for renaming
        if any(word in input_lower for word in action_words['rename']):
            return self._extract_rename_command(input_lower)
        
        # Check for reading files
        if any(word in input_lower for word in action_words['read']):
            name = self._extract_flexible_name(input_lower, ['file', 'document', 'text'])
            if name:
                return f"type {name}"
            else:
                return "type file.txt"
        
        # Check for echo/print
        if any(word in input_lower for word in action_words['echo']):
            # Extract text to echo
            text = self._extract_echo_text(input_lower)
            if text:
                return f"echo {text}"
            else:
                return "echo Hello World"
        
        # Check for system commands
        if any(word in input_lower for word in action_words['process']):
            return "tasklist"
        elif any(word in input_lower for word in action_words['cpu']):
            return "cpu"
        elif any(word in input_lower for word in action_words['memory']):
            return "mem"
        elif any(word in input_lower for word in action_words['network']):
            return "ipconfig"
        elif any(word in input_lower for word in action_words['ping']):
            return self._extract_ping_command(input_lower)
        elif any(word in input_lower for word in action_words['clear']):
            return "cls"
        elif any(word in input_lower for word in action_words['help']):
            return "help"
        elif any(word in input_lower for word in action_words['exit']):
            return "exit"
        
        # If no clear action found, try to extract a filename and assume creation
        name = self._extract_flexible_name(input_lower, ['file', 'document', 'text', 'txt'])
        if name:
            if '.' in name:
                return f"touch {name}"
            else:
                return f"mkdir {name}"
        
        return "help"
            
    def _extract_flexible_name(self, text: str, object_words: List[str]) -> str:
        """Extract name from natural language with flexible patterns."""
        # Remove common words that might interfere
        text = re.sub(r'\b(the|a|an|this|that|my|your|our|their)\b', '', text)
        
        # Patterns to extract names
        patterns = [
            # "create file called filename.txt"
            r'(?:' + '|'.join(object_words) + r')\s+(?:called|named|with\s+name|as)\s+([a-zA-Z0-9_.-]+)',
            # "create filename.txt"
            r'(?:' + '|'.join(object_words) + r')\s+([a-zA-Z0-9_.-]+)',
            # "filename.txt" (standalone)
            r'\b([a-zA-Z0-9_][a-zA-Z0-9_.-]*)\b',
            # "called filename" or "named filename"
            r'(?:called|named)\s+([a-zA-Z0-9_.-]+)',
            # "with name filename"
            r'with\s+name\s+([a-zA-Z0-9_.-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # Filter out common words that shouldn't be filenames
                if name not in ['file', 'folder', 'directory', 'document', 'text', 'new', 'the', 'a', 'an']:
                    return name
        
        return None
    
    def _extract_echo_text(self, text: str) -> str:
        """Extract text to echo from natural language."""
        # Remove action words
        text = re.sub(r'\b(echo|print|say|output|display)\b', '', text)
        
        # Extract quoted text
        quoted_match = re.search(r'["\']([^"\']+)["\']', text)
        if quoted_match:
            return quoted_match.group(1)
        
        # Extract text after "text" or "message"
        text_match = re.search(r'(?:text|message|content)\s+(.+)', text)
        if text_match:
            return text_match.group(1).strip()
        
        # Extract remaining meaningful words
        words = text.split()
        meaningful_words = [w for w in words if w not in ['the', 'a', 'an', 'this', 'that', 'my', 'your']]
        if meaningful_words:
            return ' '.join(meaningful_words)
        
        return None
    
    def _extract_rename_command(self, text: str) -> str:
        """Extract rename command from natural language."""
        # Patterns for rename
        patterns = [
            r'rename\s+([a-zA-Z0-9_.-]+)\s+(?:to|as)\s+([a-zA-Z0-9_.-]+)',
            r'change\s+([a-zA-Z0-9_.-]+)\s+(?:to|as)\s+([a-zA-Z0-9_.-]+)',
            r'([a-zA-Z0-9_.-]+)\s+(?:to|as)\s+([a-zA-Z0-9_.-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                old_name = match.group(1)
                new_name = match.group(2)
                return f"ren {old_name} {new_name}"
        
        return "ren old_name new_name"
    
    def _matches_patterns(self, text: str, action_words: List[str], object_words: List[str]) -> bool:
        """Check if text matches any combination of action and object words."""
        return (any(word in text for word in action_words) and 
                any(word in text for word in object_words))
                
    def _extract_name(self, text: str, object_words: List[str], name_indicators: List[str]) -> str:
        """Extract name from natural language."""
        patterns = [
            r'(?:' + '|'.join(object_words) + r')\s+(?:' + '|'.join(name_indicators) + r')?\s*(\w+(?:\.\w+)?)',
            r'(?:' + '|'.join(name_indicators) + r')\s+(\w+(?:\.\w+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
        
    def _extract_move_command(self, text: str) -> str:
        """Extract move command from natural language."""
        file_patterns = [r'(\w+\.\w+)', r'file\s+(\w+(?:\.\w+)?)']
        dest_patterns = [r'(?:into|to|in)\s+(\w+)', r'(\w+)\s+(?:folder|directory)']
        
        source = None
        for pattern in file_patterns:
            match = re.search(pattern, text)
            if match:
                source = match.group(1)
                break
                
        dest = None
        for pattern in dest_patterns:
            match = re.search(pattern, text)
            if match:
                dest = match.group(1)
                break
                
        if source and dest:
            return f"move {source} {dest}"
        elif source:
            return f"move {source} destination"
        else:
            return "move file.txt destination"
            
    def _extract_copy_command(self, text: str) -> str:
        """Extract copy command from natural language."""
        file_patterns = [r'(\w+\.\w+)', r'file\s+(\w+(?:\.\w+)?)']
        dest_patterns = [r'(?:to|into)\s+(\w+)', r'(\w+)\s+(?:folder|directory)']
        
        source = None
        for pattern in file_patterns:
            match = re.search(pattern, text)
            if match:
                source = match.group(1)
                break
                
        dest = None
        for pattern in dest_patterns:
            match = re.search(pattern, text)
            if match:
                dest = match.group(1)
                break
                
        if source and dest:
            return f"copy {source} {dest}"
        elif source:
            return f"copy {source} destination"
        else:
            return "copy file.txt destination"
            
    def _extract_ping_command(self, text: str) -> str:
        """Extract ping command from natural language."""
        host_match = re.search(r'(?:ping|test)\s+(\w+(?:\.\w+)*)', text)
        if host_match:
            return f"ping {host_match.group(1)}"
        return "ping google.com"
        
    def _execute_command(self, command: str) -> str:
        """Execute a Python terminal command."""
        parts = command.strip().split()
        if not parts:
            return ""
            
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # File operations
            if cmd in ['dir', 'ls']:
                return self._dir(args)
            elif cmd == 'cd':
                return self._cd(args)
            elif cmd == 'pwd':
                return self._pwd(args)
            elif cmd == 'mkdir':
                return self._mkdir(args)
            elif cmd == 'rmdir':
                return self._rmdir(args)
            elif cmd in ['del', 'rm']:
                return self._del(args)
            elif cmd in ['move', 'mv']:
                return self._move(args)
            elif cmd in ['copy', 'cp']:
                return self._copy(args)
            elif cmd == 'ren':
                return self._ren(args)
            elif cmd in ['type', 'cat']:
                return self._type(args)
            elif cmd == 'echo':
                return self._echo(args)
            elif cmd == 'touch':
                return self._touch(args)
            elif cmd in ['tasklist', 'ps']:
                return self._tasklist(args)
            elif cmd in ['taskkill', 'kill']:
                return self._taskkill(args)
            elif cmd == 'cpu':
                return self._cpu(args)
            elif cmd == 'mem':
                return self._mem(args)
            elif cmd == 'ipconfig':
                return self._ipconfig(args)
            elif cmd == 'ping':
                return self._ping(args)
            elif cmd == 'netstat':
                return self._netstat(args)
            elif cmd in ['cls', 'clear']:
                return self._cls(args)
            elif cmd == 'history':
                return self._history(args)
            elif cmd == 'help':
                return self._help(args)
            elif cmd in ['exit', 'quit']:
                self.root.quit()
                return "Goodbye!"
            else:
                return f"Unknown command: {cmd}"
        except Exception as e:
            return f"Error executing '{cmd}': {str(e)}"
            
    # Command implementations
    def _dir(self, args: List[str]) -> str:
        """List directory contents."""
        try:
            path = args[0] if args else '.'
            path = os.path.abspath(path)
            
            if not os.path.exists(path):
                return f"❌ Error: '{path}' does not exist"
            
            if not os.path.isdir(path):
                return f"❌ Error: '{path}' is not a directory"
            
            items = os.listdir(path)
            items.sort()
            
            result = []
            result.append(f"📁 Directory: {path}")
            result.append("=" * 50)
            
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    result.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    result.append(f"📄 {item} ({size} bytes)")
            
            return '\n'.join(result) if result else "Directory is empty"
            
        except Exception as e:
            return f"❌ Error listing directory: {str(e)}"
            
    def _cd(self, args: List[str]) -> str:
        """Change directory."""
        try:
            if not args:
                new_dir = os.path.expanduser("~")
            else:
                new_dir = args[0]
            
            if new_dir == "..":
                new_dir = os.path.dirname(self.current_dir)
            elif not os.path.isabs(new_dir):
                new_dir = os.path.join(self.current_dir, new_dir)
            
            new_dir = os.path.abspath(new_dir)
            
            if not os.path.exists(new_dir):
                return f"❌ Error: Directory '{new_dir}' does not exist"
            
            if not os.path.isdir(new_dir):
                return f"❌ Error: '{new_dir}' is not a directory"
            
            self.current_dir = new_dir
            os.chdir(new_dir)
            self.dir_label.config(text=f"📁 {os.path.basename(self.current_dir)}")
            return f"✅ Changed to: {new_dir}"
            
        except Exception as e:
            return f"❌ Error changing directory: {str(e)}"
            
    def _pwd(self, args: List[str]) -> str:
        """Print working directory."""
        return f"📁 Current directory: {self.current_dir}"
        
    def _mkdir(self, args: List[str]) -> str:
        """Create directory."""
        if not args:
            return "❌ Error: mkdir requires a directory name"
        
        try:
            for dir_name in args:
                dir_path = os.path.join(self.current_dir, dir_name)
                os.makedirs(dir_path, exist_ok=True)
            return f"✅ Created directory: {', '.join(args)}"
        except Exception as e:
            return f"❌ Error creating directory: {str(e)}"
            
    def _rmdir(self, args: List[str]) -> str:
        """Remove empty directory."""
        if not args:
            return "❌ Error: rmdir requires a directory name"
        
        try:
            for dir_name in args:
                dir_path = os.path.join(self.current_dir, dir_name)
                if not os.path.exists(dir_path):
                    return f"❌ Error: Directory '{dir_name}' does not exist"
                if not os.path.isdir(dir_path):
                    return f"❌ Error: '{dir_name}' is not a directory"
                if os.listdir(dir_path):
                    return f"❌ Error: Directory '{dir_name}' is not empty. Use 'del' to remove directories with content."
                os.rmdir(dir_path)
            return f"✅ Removed directory: {', '.join(args)}"
        except Exception as e:
            return f"❌ Error removing directory: {str(e)}"
            
    def _del(self, args: List[str]) -> str:
        """Delete file or directory (with content)."""
        if not args:
            return "❌ Error: del requires a file or directory name"
        
        try:
            deleted_items = []
            for item_name in args:
                item_path = os.path.join(self.current_dir, item_name)
                if not os.path.exists(item_path):
                    return f"❌ Error: '{item_name}' does not exist"
                
                if os.path.isdir(item_path):
                    # Remove directory with all contents
                    shutil.rmtree(item_path)
                    deleted_items.append(f"📁 {item_name}/")
                else:
                    # Remove file
                    os.remove(item_path)
                    deleted_items.append(f"📄 {item_name}")
            
            return f"✅ Deleted: {', '.join(deleted_items)}"
        except Exception as e:
            return f"❌ Error deleting: {str(e)}"
            
    def _move(self, args: List[str]) -> str:
        """Move file or directory."""
        if len(args) < 2:
            return "❌ Error: move requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.current_dir, dest)
            
            shutil.move(source, dest)
            return f"✅ Moved '{source}' to '{dest}'"
        except Exception as e:
            return f"❌ Error moving: {str(e)}"
            
    def _copy(self, args: List[str]) -> str:
        """Copy file or directory."""
        if len(args) < 2:
            return "❌ Error: copy requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.current_dir, dest)
            
            if not os.path.exists(source):
                return f"❌ Error: Source '{source}' does not exist"
            
            if os.path.isdir(source):
                # For directories, use copytree with dirs_exist_ok for Python 3.8+
                try:
                    shutil.copytree(source, dest, dirs_exist_ok=True)
                except TypeError:
                    # Fallback for older Python versions
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest)
            else:
                # For files, ensure destination directory exists
                dest_dir = os.path.dirname(dest)
                if dest_dir and not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(source, dest)
            
            return f"✅ Copied '{source}' to '{dest}'"
        except Exception as e:
            return f"❌ Error copying: {str(e)}"
            
    def _ren(self, args: List[str]) -> str:
        """Rename file or directory."""
        if len(args) < 2:
            return "❌ Error: ren requires old name and new name"
        
        try:
            old_name = args[0]
            new_name = args[1]
            
            if not os.path.isabs(old_name):
                old_name = os.path.join(self.current_dir, old_name)
            if not os.path.isabs(new_name):
                new_name = os.path.join(self.current_dir, new_name)
            
            os.rename(old_name, new_name)
            return f"✅ Renamed '{old_name}' to '{new_name}'"
        except Exception as e:
            return f"❌ Error renaming: {str(e)}"
            
    def _type(self, args: List[str]) -> str:
        """Display file contents."""
        if not args:
            return "❌ Error: type requires a file name"
        
        try:
            file_path = args[0]
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_dir, file_path)
            
            if not os.path.exists(file_path):
                return f"❌ Error: File '{file_path}' does not exist"
            
            if os.path.isdir(file_path):
                return f"❌ Error: '{file_path}' is a directory, not a file"
            
            # Check file size to prevent reading huge files
            file_size = os.path.getsize(file_path)
            if file_size > 1024 * 1024:  # 1MB limit
                return f"❌ Error: File too large ({file_size // (1024*1024)}MB). Use a text editor for large files."
            
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return f"❌ Error: Could not read file with supported encodings"
            
            return f"📄 Contents of {file_path}:\n{'-' * 40}\n{content}"
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"
            
    def _echo(self, args: List[str]) -> str:
        """Echo text to console."""
        return ' '.join(args)
        
    def _touch(self, args: List[str]) -> str:
        """Create empty file(s)."""
        if not args:
            return "❌ Error: touch requires a file name"
        
        try:
            created_files = []
            for file_name in args:
                file_path = os.path.join(self.current_dir, file_name)
                
                # Create directory if it doesn't exist
                dir_path = os.path.dirname(file_path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                
                # Create empty file
                with open(file_path, 'w', encoding='utf-8') as f:
                    pass
                created_files.append(f"📄 {file_name}")
            
            return f"✅ Created file(s): {', '.join(created_files)}"
        except Exception as e:
            return f"❌ Error creating file: {str(e)}"
        
    def _tasklist(self, args: List[str]) -> str:
        """Show running processes."""
        try:
            result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True, timeout=10)
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "❌ Error: tasklist command timed out"
        except Exception as e:
            return f"❌ Error getting task list: {str(e)}"
            
    def _taskkill(self, args: List[str]) -> str:
        """Kill a process."""
        if not args:
            return "❌ Error: taskkill requires process ID or name"
        
        try:
            result = subprocess.run(['taskkill'] + args, capture_output=True, text=True, shell=True, timeout=10)
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "❌ Error: taskkill command timed out"
        except Exception as e:
            return f"❌ Error killing process: {str(e)}"
            
    def _cpu(self, args: List[str]) -> str:
        """Show CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            return f"🖥️ CPU Usage: {cpu_percent}% (Cores: {cpu_count})"
        except Exception as e:
            return f"❌ Error getting CPU info: {str(e)}"
            
    def _mem(self, args: List[str]) -> str:
        """Show memory usage."""
        try:
            memory = psutil.virtual_memory()
            return f"💾 Memory: {memory.percent}% used ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)"
        except Exception as e:
            return f"❌ Error getting memory info: {str(e)}"
            
    def _ipconfig(self, args: List[str]) -> str:
        """Show network configuration."""
        try:
            result = subprocess.run(['ipconfig'] + args, capture_output=True, text=True, shell=True, timeout=10)
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "❌ Error: ipconfig command timed out"
        except Exception as e:
            return f"❌ Error getting network config: {str(e)}"
            
    def _ping(self, args: List[str]) -> str:
        """Ping a host."""
        if not args:
            return "❌ Error: ping requires a hostname or IP"
        
        try:
            # Limit ping to 4 packets to prevent long waits
            ping_args = args + ['-n', '4'] if os.name == 'nt' else args + ['-c', '4']
            result = subprocess.run(['ping'] + ping_args, capture_output=True, text=True, shell=True, timeout=15)
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "❌ Error: ping command timed out"
        except Exception as e:
            return f"❌ Error pinging: {str(e)}"
            
    def _netstat(self, args: List[str]) -> str:
        """Show network connections."""
        try:
            result = subprocess.run(['netstat'] + args, capture_output=True, text=True, shell=True, timeout=10)
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "❌ Error: netstat command timed out"
        except Exception as e:
            return f"❌ Error getting network stats: {str(e)}"
            
    def _cls(self, args: List[str]) -> str:
        """Clear the screen."""
        self.output_area.config(state=tk.NORMAL)
        self.output_area.delete(1.0, tk.END)
        self.output_area.config(state=tk.DISABLED)
        return ""
        
    def _history(self, args: List[str]) -> str:
        """Show command history."""
        if not self.command_history:
            return "📜 No command history"
        
        result = []
        result.append("📜 Command History:")
        result.append("=" * 50)
        
        # Show last 20 commands
        start_idx = max(0, len(self.command_history) - 20)
        for i, cmd in enumerate(self.command_history[start_idx:], start_idx + 1):
            # Add visual indicators
            if cmd.startswith(('dir', 'ls')):
                result.append(f"{i:4d}  📁 {cmd}")
            elif cmd.startswith(('mkdir', 'rmdir')):
                result.append(f"{i:4d}  📂 {cmd}")
            elif cmd.startswith(('del', 'rm')):
                result.append(f"{i:4d}  🗑️ {cmd}")
            elif cmd.startswith(('copy', 'cp', 'move', 'mv')):
                result.append(f"{i:4d}  📋 {cmd}")
            elif cmd.startswith(('create', 'make', 'delete', 'show')):
                result.append(f"{i:4d}  🗣️ {cmd}")
            else:
                result.append(f"{i:4d}  💻 {cmd}")
        
        if len(self.command_history) > 20:
            result.append(f"\n... and {len(self.command_history) - 20} more commands")
        
        result.append("=" * 50)
        result.append(f"📊 Total commands: {len(self.command_history)}")
        result.append("⌨️ Use ↑↓ arrow keys to navigate history")
        
        return '\n'.join(result)
        
    def _help(self, args: List[str]) -> str:
        """Show help information."""
        return """
🚀 AI-Powered Python Terminal v1.0
Supports both Python commands and flexible natural English

🎯 FEATURES:
  • Command History: Use ↑↓ arrow keys to navigate previous commands
  • Auto-completion: Press Tab to complete commands and file paths
  • AI Commands: Use natural English (e.g., "create a folder called test")
  • Windows Commands: Full support for dir, cd, mkdir, del, copy, move, etc.

📋 AVAILABLE COMMANDS:
  dir [path]             - List directory contents
  cd [path]              - Change directory
  pwd                    - Print working directory
  mkdir <dir>            - Create directory
  rmdir <dir>            - Remove empty directory only
  del <file/dir>         - Delete file or directory (with content)
  copy <source> <dest>   - Copy file or directory
  move <source> <dest>   - Move or rename file or directory
  ren <old> <new>        - Rename file or directory
  type <file>            - Display file contents
  touch <file>           - Create empty file
  echo <text>            - Echo text to console
  tasklist               - Show running processes
  taskkill <pid/name>    - Kill a process
  cpu                    - Show CPU usage
  mem                    - Show memory usage
  ipconfig               - Show network configuration
  ping <host>            - Ping a host
  netstat                - Show network connections
  cls                    - Clear the screen
  history                - Show command history
  help                   - Show this help
  exit/quit              - Exit terminal

🗣️ NATURAL LANGUAGE EXAMPLES:
  "list files in current directory" → dir
  "show me what's here" → dir
  "create a folder called test" → mkdir test
  "make a file called file1.txt" → touch file1.txt
  "create file1.txt" → touch file1.txt
  "delete the file hello.txt" → del hello.txt
  "remove the folder test" → del test
  "show all running processes" → tasklist
  "check CPU usage" → cpu
  "clear the screen" → cls
  "echo hello world" → echo hello world

⌨️ KEYBOARD SHORTCUTS:
  ↑↓ Arrow Keys          - Navigate command history
  Tab                    - Auto-complete commands and files
  Enter                  - Execute command
        """
        
    # History management
    def add_to_history(self, command: str):
        """Add command to history."""
        if command and command not in self.command_history:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            
    def history_up(self, event=None):
        """Navigate up in command history."""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, self.command_history[self.history_index])
        return "break"
        
    def history_down(self, event=None):
        """Navigate down in command history."""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.input_entry.delete(0, tk.END)
        return "break"
        
    # Auto-completion
    def auto_complete(self, event=None):
        """Handle auto-completion."""
        current_text = self.input_entry.get()
        cursor_pos = self.input_entry.index(tk.INSERT)
        
        # Get completion options
        options = self._get_completion_options(current_text)
        
        if options:
            if len(options) == 1:
                # Single match - complete it
                completion = options[0]
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, completion)
            else:
                # Multiple matches - show suggestions
                self._show_completion_suggestions(current_text, options)
        
        return "break"
        
    def _get_completion_options(self, text: str) -> List[str]:
        """Get completion options for the given text."""
        options = []
        
        # Command completion
        for cmd in self.supported_commands:
            if cmd.startswith(text):
                options.append(cmd)
        
        # File/directory completion
        if ' ' in text:
            parts = text.split()
            if len(parts) > 1:
                prefix = ' '.join(parts[:-1]) + ' '
                last_part = parts[-1]
                try:
                    dir_path = os.path.dirname(last_part) or '.'
                    base_name = os.path.basename(last_part)
                    
                    if os.path.exists(dir_path) and os.path.isdir(dir_path):
                        for item in os.listdir(dir_path):
                            if item.startswith(base_name):
                                full_path = os.path.join(dir_path, item)
                                if os.path.isdir(full_path):
                                    options.append(prefix + item + '/')
                                else:
                                    options.append(prefix + item)
                except:
                    pass
        
        return options
        
    def _show_completion_suggestions(self, text: str, options: List[str]):
        """Show completion suggestions."""
        self.add_output(f"💡 Suggestions for '{text}':")
        for i, option in enumerate(options[:10]):
            if option in self.supported_commands:
                desc = self._get_command_description(option)
                self.add_output(f"  {i+1:2d}. {option:<12} - {desc}")
            else:
                if option.endswith('/'):
                    self.add_output(f"  {i+1:2d}. {option:<12} - 📁 Directory")
                else:
                    self.add_output(f"  {i+1:2d}. {option:<12} - 📄 File")
        
        if len(options) > 10:
            self.add_output(f"  ... and {len(options) - 10} more options")
        self.add_output("Press Tab to cycle through options...")
        
    def _get_command_description(self, command: str) -> str:
        """Get description for a command."""
        descriptions = {
            'dir': 'List directory contents',
            'cd': 'Change directory',
            'pwd': 'Print working directory',
            'mkdir': 'Create directory',
            'rmdir': 'Remove empty directory',
            'del': 'Delete file',
            'copy': 'Copy file or directory',
            'move': 'Move or rename file',
            'ren': 'Rename file or directory',
            'type': 'Display file contents',
            'echo': 'Echo text to console',
            'tasklist': 'Show running processes',
            'taskkill': 'Kill a process',
            'cpu': 'Show CPU usage',
            'mem': 'Show memory usage',
            'ipconfig': 'Show network configuration',
            'ping': 'Ping a host',
            'netstat': 'Show network connections',
            'cls': 'Clear the screen',
            'history': 'Show command history',
            'help': 'Show help information',
            'exit': 'Exit terminal',
            'quit': 'Exit terminal'
        }
        return descriptions.get(command, 'Command')
        
    def on_key_release(self, event=None):
        """Handle key release events."""
        # Reset history index when typing
        if event and event.keysym not in ['Up', 'Down']:
            self.history_index = len(self.command_history)
            
    def load_history(self):
        """Load command history from file."""
        try:
            history_file = os.path.expanduser("~/.gui_terminal_history")
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self.command_history.append(line)
        except Exception:
            pass
            
    def save_history(self):
        """Save command history to file."""
        try:
            history_file = os.path.expanduser("~/.gui_terminal_history")
            with open(history_file, 'w', encoding='utf-8') as f:
                for cmd in self.command_history:
                    f.write(cmd + '\n')
        except Exception:
            pass
            
    def run(self):
        """Start the GUI terminal."""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
            
    def on_closing(self):
        """Handle application closing."""
        self.save_history()
        self.root.destroy()


def main():
    """Main entry point."""
    try:
        terminal = GUITerminal()
        terminal.run()
    except Exception as e:
        print(f"Error starting GUI terminal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
