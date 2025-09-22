#!/usr/bin/env python3
"""
Web-based Python Terminal with AI Integration
A Flask web application version of the terminal with all features:
- Dual input (Python commands + Natural English)
- AI integration with Gemini API
- Real-time command execution
- Modern web interface with WebSocket support
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import sys
import subprocess
import shutil
import psutil
import json
import re
import requests
import threading
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=20,
    ping_interval=5,
)

class WebTerminal:
    """Web Terminal with all CLI features integrated."""
    
    def __init__(self):
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY', "AIzaSyCknv4gzEzQj1ThRx8uEs_w1IqAo4dxC9c")
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Supported commands
        self.supported_commands = {
            'dir', 'cd', 'mkdir', 'rmdir', 'del', 'copy', 'move', 'ren', 'type', 'touch',
            'tasklist', 'taskkill', 'cpu', 'mem', 'ipconfig', 'ping', 'netstat', 
            'cls', 'echo', 'help', 'exit', 'quit', 'pwd', 'ls', 'rm', 'mv', 'cp', 'cat', 'ps', 'kill', 'clear', 'history'
        }
        
        # User sessions
        self.user_sessions = {}
        
    def create_user_session(self, session_id):
        """Create a new user session."""
        self.user_sessions[session_id] = {
            'current_dir': os.getcwd(),
            'command_history': [],
            'history_index': -1
        }
        return self.user_sessions[session_id]
        
    def get_user_session(self, session_id):
        """Get user session or create new one."""
        if session_id not in self.user_sessions:
            return self.create_user_session(session_id)
        return self.user_sessions[session_id]
        
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
Supported commands: dir, cd, mkdir, rmdir, del, copy, move, ren, type, touch, tasklist, taskkill, cpu, mem, ipconfig, ping, netstat, cls, echo, help, exit

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
    
    def _get_completion_options(self, text: str, cursor_pos: int, current_dir: str) -> List[str]:
        """Get completion options for the given text."""
        options = []
        
        # Command completion
        commands = [
            'dir', 'cd', 'mkdir', 'rmdir', 'del', 'copy', 'move', 'ren', 'type', 'touch',
            'tasklist', 'taskkill', 'cpu', 'mem', 'ipconfig', 'ping', 'netstat',
            'cls', 'echo', 'help', 'exit', 'quit', 'pwd', 'ls', 'rm', 'mv', 'cp', 'cat', 'ps', 'kill', 'clear', 'history'
        ]
        
        # Find the current word being typed
        words = text[:cursor_pos].split()
        current_word = words[-1] if words else ''
        
        if len(words) <= 1:
            # First word - command completion
            for cmd in commands:
                if cmd.startswith(current_word.lower()):
                    options.append(cmd)
        else:
            # File/directory completion
            try:
                if os.path.exists(current_dir) and os.path.isdir(current_dir):
                    for item in os.listdir(current_dir):
                        if item.startswith(current_word):
                            item_path = os.path.join(current_dir, item)
                            if os.path.isdir(item_path):
                                options.append(item + '/')
                            else:
                                options.append(item)
            except Exception:
                pass
        
        # Sort options
        options.sort()
        return options[:20]  # Limit to 20 options
    
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
        dest_patterns = [r'(?:to|into|in)\s+(\w+)', r'(\w+)\s+(?:folder|directory)']
        
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
        
    def _execute_command(self, command: str, session_id: str) -> str:
        """Execute a Python terminal command."""
        user_session = self.get_user_session(session_id)
        current_dir = user_session['current_dir']
        
        parts = command.strip().split()
        if not parts:
            return ""
            
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            # File operations
            if cmd in ['dir', 'ls']:
                return self._dir(args, current_dir)
            elif cmd == 'cd':
                result = self._cd(args, current_dir, session_id)
                return result
            elif cmd == 'pwd':
                return self._pwd(args, current_dir)
            elif cmd == 'mkdir':
                return self._mkdir(args, current_dir)
            elif cmd == 'rmdir':
                return self._rmdir(args, current_dir)
            elif cmd in ['del', 'rm']:
                return self._del(args, current_dir)
            elif cmd in ['move', 'mv']:
                return self._move(args, current_dir)
            elif cmd in ['copy', 'cp']:
                return self._copy(args, current_dir)
            elif cmd == 'ren':
                return self._ren(args, current_dir)
            elif cmd in ['type', 'cat']:
                return self._type(args, current_dir)
            elif cmd == 'echo':
                return self._echo(args)
            elif cmd == 'touch':
                return self._touch(args, current_dir)
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
                return "CLS"  # Special command for web interface
            elif cmd == 'history':
                return self._history(args, user_session)
            elif cmd == 'help':
                return self._help(args)
            elif cmd in ['exit', 'quit']:
                return "EXIT"  # Special command for web interface
            else:
                return f"Unknown command: {cmd}"
        except Exception as e:
            return f"Error executing '{cmd}': {str(e)}"
    
    # Command implementations (same as GUI version but with current_dir parameter)
    def _dir(self, args: List[str], current_dir: str) -> str:
        """List directory contents."""
        try:
            path = args[0] if args else current_dir
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
            
    def _cd(self, args: List[str], current_dir: str, session_id: str) -> str:
        """Change directory."""
        try:
            user_session = self.get_user_session(session_id)
            
            if not args:
                new_dir = os.path.expanduser("~")
            else:
                new_dir = args[0]
            
            if new_dir == "..":
                new_dir = os.path.dirname(current_dir)
            elif not os.path.isabs(new_dir):
                new_dir = os.path.join(current_dir, new_dir)
            
            new_dir = os.path.abspath(new_dir)
            
            if not os.path.exists(new_dir):
                return f"❌ Error: Directory '{new_dir}' does not exist"
            
            if not os.path.isdir(new_dir):
                return f"❌ Error: '{new_dir}' is not a directory"
            
            user_session['current_dir'] = new_dir
            return f"✅ Changed to: {new_dir}"
            
        except Exception as e:
            return f"❌ Error changing directory: {str(e)}"
            
    def _pwd(self, args: List[str], current_dir: str) -> str:
        """Print working directory."""
        return f"📁 Current directory: {current_dir}"
        
    def _mkdir(self, args: List[str], current_dir: str) -> str:
        """Create directory."""
        if not args:
            return "❌ Error: mkdir requires a directory name"
        
        try:
            for dir_name in args:
                dir_path = os.path.join(current_dir, dir_name)
                os.makedirs(dir_path, exist_ok=True)
            return f"✅ Created directory: {', '.join(args)}"
        except Exception as e:
            return f"❌ Error creating directory: {str(e)}"
            
    def _rmdir(self, args: List[str], current_dir: str) -> str:
        """Remove empty directory."""
        if not args:
            return "❌ Error: rmdir requires a directory name"
        
        try:
            for dir_name in args:
                dir_path = os.path.join(current_dir, dir_name)
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
            
    def _del(self, args: List[str], current_dir: str) -> str:
        """Delete file or directory (with content)."""
        if not args:
            return "❌ Error: del requires a file or directory name"
        
        try:
            deleted_items = []
            for item_name in args:
                item_path = os.path.join(current_dir, item_name)
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
            
    def _move(self, args: List[str], current_dir: str) -> str:
        """Move file or directory."""
        if len(args) < 2:
            return "❌ Error: move requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(current_dir, dest)
            
            shutil.move(source, dest)
            return f"✅ Moved '{source}' to '{dest}'"
        except Exception as e:
            return f"❌ Error moving: {str(e)}"
            
    def _copy(self, args: List[str], current_dir: str) -> str:
        """Copy file or directory."""
        if len(args) < 2:
            return "❌ Error: copy requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(current_dir, dest)
            
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
            
    def _ren(self, args: List[str], current_dir: str) -> str:
        """Rename file or directory."""
        if len(args) < 2:
            return "❌ Error: ren requires old name and new name"
        
        try:
            old_name = args[0]
            new_name = args[1]
            
            if not os.path.isabs(old_name):
                old_name = os.path.join(current_dir, old_name)
            if not os.path.isabs(new_name):
                new_name = os.path.join(current_dir, new_name)
            
            os.rename(old_name, new_name)
            return f"✅ Renamed '{old_name}' to '{new_name}'"
        except Exception as e:
            return f"❌ Error renaming: {str(e)}"
            
    def _type(self, args: List[str], current_dir: str) -> str:
        """Display file contents."""
        if not args:
            return "❌ Error: type requires a file name"
        
        try:
            file_path = args[0]
            if not os.path.isabs(file_path):
                file_path = os.path.join(current_dir, file_path)
            
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
        
    def _touch(self, args: List[str], current_dir: str) -> str:
        """Create empty file(s)."""
        if not args:
            return "❌ Error: touch requires a file name"
        
        try:
            created_files = []
            for file_name in args:
                file_path = os.path.join(current_dir, file_name)
                
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
            
    def _history(self, args: List[str], user_session: Dict) -> str:
        """Show command history."""
        command_history = user_session.get('command_history', [])
        if not command_history:
            return "📜 No command history"
        
        result = []
        result.append("📜 Command History:")
        result.append("=" * 50)
        
        # Show last 20 commands
        start_idx = max(0, len(command_history) - 20)
        for i, cmd in enumerate(command_history[start_idx:], start_idx + 1):
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
        
        if len(command_history) > 20:
            result.append(f"\n... and {len(command_history) - 20} more commands")
        
        result.append("=" * 50)
        result.append(f"📊 Total commands: {len(command_history)}")
        result.append("⌨️ Use ↑↓ arrow keys to navigate history")
        
        return '\n'.join(result)
        
    def _help(self, args: List[str]) -> str:
        """Show help information."""
        return """
🚀 AI-Powered Python Terminal v2.0 (Web Version)
Supports both Python commands and flexible natural English

🎯 FEATURES:
  • Command History: Commands are saved in your session
  • AI Commands: Use natural English (e.g., "create a folder called test")
  • Windows Commands: Full support for dir, cd, mkdir, del, copy, move, etc.
  • Web Interface: Access from any browser, anywhere

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

🌐 WEB FEATURES:
  • Real-time command execution
  • Session-based command history
  • Responsive design for all devices
  • Modern web interface
        """

# Global terminal instance
terminal = WebTerminal()

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    session_id = str(uuid.uuid4())
    session['session_id'] = session_id
    terminal.create_user_session(session_id)
    join_room(session_id)
    
    # Send welcome message
    emit('output', {
        'text': '🚀 AI-Powered Python Terminal v2.0 (Web Version)',
        'type': 'welcome'
    })
    emit('output', {
        'text': '=' * 80,
        'type': 'separator'
    })
    emit('output', {
        'text': '✨ Features: Python Commands + Natural English + AI Processing',
        'type': 'info'
    })
    emit('output', {
        'text': '🌐 Web Interface: Access from any browser, anywhere',
        'type': 'info'
    })
    emit('output', {
        'text': '🎯 Type "help" for available commands, "exit" to quit',
        'type': 'info'
    })
    emit('output', {
        'text': '=' * 80,
        'type': 'separator'
    })
    emit('output', {
        'text': '',
        'type': 'empty'
    })
    
    # Send current directory
    user_session = terminal.get_user_session(session_id)
    emit('directory_update', {
        'directory': os.path.basename(user_session['current_dir'])
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    if 'session_id' in session:
        leave_room(session['session_id'])

@socketio.on('get_completion')
def handle_completion(data):
    """Handle auto-completion requests."""
    session_id = session.get('session_id')
    if not session_id:
        return
    
    user_session = terminal.get_user_session(session_id)
    current_dir = user_session['current_dir']
    
    text = data.get('text', '')
    cursor_pos = data.get('cursor_pos', 0)
    
    # Get completion options
    options = terminal._get_completion_options(text, cursor_pos, current_dir)
    
    emit('completion_options', {
        'options': options
    })

@socketio.on('command')
def handle_command(data):
    """Handle command execution."""
    session_id = session.get('session_id')
    if not session_id:
        emit('output', {
            'text': '❌ Error: No active session',
            'type': 'error'
        })
        return
    
    command = data.get('command', '').strip()
    if not command:
        return
    
    user_session = terminal.get_user_session(session_id)
    
    # Add to history
    user_session['command_history'].append(command)
    
    # Show command in output
    emit('output', {
        'text': f"💻 {os.path.basename(user_session['current_dir'])}$ {command}",
        'type': 'command'
    })
    
    # Process and execute command
    try:
        # Check if it's a Python command
        if terminal._is_python_command(command):
            result = terminal._execute_command(command, session_id)
        else:
            # Convert natural language to command
            converted_command = terminal._convert_natural_language(command)
            emit('output', {
                'text': f"🔄 Converted: '{command}' → '{converted_command}'",
                'type': 'conversion'
            })
            result = terminal._execute_command(converted_command, session_id)
        
        # Handle special commands
        if result == "CLS":
            emit('clear_screen')
        elif result == "EXIT":
            emit('output', {
                'text': '👋 Goodbye! Thanks for using the AI-Powered Terminal!',
                'type': 'goodbye'
            })
        else:
            # Display result
            if result:
                emit('output', {
                    'text': result,
                    'type': 'result'
                })
                
    except Exception as e:
        emit('output', {
            'text': f"❌ Error: {str(e)}",
            'type': 'error'
        })
    
    # Update directory display
    user_session = terminal.get_user_session(session_id)
    emit('directory_update', {
        'directory': os.path.basename(user_session['current_dir'])
    })
    
    emit('output', {
        'text': '',
        'type': 'empty'
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print("🚀 Starting AI-Powered Web Terminal...")
    print(f"🌐 Open your browser and go to: http://localhost:{port}")
    print("✨ Features: Python Commands + Natural English + AI Processing")
    
    socketio.run(app, debug=debug, host='0.0.0.0', port=port)
