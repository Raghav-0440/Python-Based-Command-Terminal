#!/usr/bin/env python3
"""
Unified Python Terminal with Flexible Natural Language Processing
Supports both Python syntax commands and flexible natural English input
"""

import os
import sys
import subprocess
import shutil
import psutil
import readline
import json
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class UnifiedTerminal:
    """Unified terminal that processes both Python commands and flexible natural English."""
    
    def __init__(self):
        self.current_dir = os.getcwd()
        self.history_file = os.path.expanduser("~/.unified_terminal_history")
        self.gemini_api_key = "AIzaSyCknv4gzEzQj1ThRx8uEs_w1IqAo4dxC9c"
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        # Supported commands
        self.supported_commands = {
            'dir', 'cd', 'mkdir', 'rmdir', 'del', 'copy', 'move', 'ren', 'type', 
            'tasklist', 'taskkill', 'cpu', 'mem', 'ipconfig', 'ping', 'netstat', 
            'cls', 'echo', 'help', 'exit', 'quit', 'pwd', 'ls', 'rm', 'mv', 'cp', 'cat', 'touch', 'ps', 'kill', 'clear', 'history'
        }
        
        self._load_history()
        self._setup_autocomplete()
    
    def _load_history(self):
        """Load command history from file with enhanced features."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Load last 1000 commands to avoid memory issues
                    for line in lines[-1000:]:
                        line = line.strip()
                        if line and line not in [readline.get_history_item(i) for i in range(1, readline.get_current_history_length() + 1)]:
                            readline.add_history(line)
        except Exception:
            pass
    
    def _save_history(self, command: str):
        """Save command to history file with enhanced features."""
        try:
            # Don't save empty commands or duplicates
            if not command.strip() or command.strip() == readline.get_history_item(readline.get_current_history_length()):
                return
            
            # Add to readline history
            readline.add_history(command)
            
            # Save to file with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.history_file, 'a', encoding='utf-8') as f:
                f.write(f"{command}\n")
        except Exception:
            pass
    
    def _setup_autocomplete(self):
        """Setup simple and reliable tab completion."""
        def completer(text, state):
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
            
            # Remove duplicates
            unique_options = list(dict.fromkeys(options))
            
            # Show suggestions on first tab press
            if state == 0 and len(unique_options) > 1:
                print(f"\n💡 Suggestions for '{text}':")
                for i, option in enumerate(unique_options[:10]):
                    if option in self.supported_commands:
                        desc = self._get_command_description(option)
                        print(f"  {i+1:2d}. {option:<12} - {desc}")
                    else:
                        if option.endswith('/'):
                            print(f"  {i+1:2d}. {option:<12} - 📁 Directory")
                        else:
                            print(f"  {i+1:2d}. {option:<12} - 📄 File")
                
                if len(unique_options) > 10:
                    print(f"  ... and {len(unique_options) - 10} more options")
                print("Press Tab to cycle through options...")
            
            # Return the option for the current state
            if state < len(unique_options):
                return unique_options[state]
            return None
        
        # Simple readline configuration
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set show-all-if-ambiguous on")
        readline.parse_and_bind("set completion-query-items 0")
        
        # Enable history navigation with arrow keys
        readline.parse_and_bind("\\C-p: history-search-backward")
        readline.parse_and_bind("\\C-n: history-search-forward")
    
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
    
    def _is_python_command(self, input_text: str) -> bool:
        """Check if input is already a valid Python terminal command."""
        parts = input_text.strip().split()
        if not parts:
            return False
        
        command = parts[0].lower()
        return command in self.supported_commands
    
    def _convert_natural_language(self, natural_input: str) -> str:
        """Convert natural language to Python terminal command using flexible processing."""
        try:
            # First try Gemini API
            command = self._try_gemini_api(natural_input)
            if command and command != "help":
                return command
        except:
            pass
        
        # Fallback to flexible pattern matching
        return self._flexible_conversion(natural_input)
    
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
- "delete the folder test" → "rmdir test"
- "delete the file hello.txt" → "del hello.txt"
- "copy file.txt to backup" → "copy file.txt backup"
- "move file1.txt to test folder" → "move file1.txt test"
- "rename old.txt to new.txt" → "ren old.txt new.txt"
- "show contents of file.txt" → "type file.txt"
- "show all running processes" → "tasklist"
- "kill process with id 1234" → "taskkill /pid 1234"
- "check CPU usage" → "cpu"
- "check memory usage" → "mem"
- "show network configuration" → "ipconfig"
- "ping google.com" → "ping google.com"
- "show network connections" → "netstat"
- "clear the screen" → "cls"
- "echo hello world" → "echo hello world"

Return only the command:
"""

            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
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
    
    def _flexible_conversion(self, natural_input: str) -> str:
        """Flexible natural language conversion using multiple patterns."""
        input_lower = natural_input.lower()
        
        # File operations patterns
        if self._matches_patterns(input_lower, ['list', 'show', 'display', 'see'], ['file', 'directory', 'folder', 'content']):
            return "dir"
        
        elif self._matches_patterns(input_lower, ['create', 'make', 'new', 'add'], ['folder', 'directory']):
            folder_name = self._extract_name(input_lower, ['folder', 'directory'], ['called', 'named'])
            return f"mkdir {folder_name}" if folder_name else "mkdir new_folder"
        
        elif self._matches_patterns(input_lower, ['create', 'make', 'new', 'add'], ['file']):
            file_name = self._extract_name(input_lower, ['file'], ['named', 'called'])
            return f"echo. > {file_name}" if file_name else "echo. > new_file.txt"
        
        elif self._matches_patterns(input_lower, ['delete', 'remove', 'erase', 'trash'], ['folder', 'directory']):
            item_name = self._extract_name(input_lower, ['folder', 'directory'], ['named', 'called'])
            return f"rmdir {item_name}" if item_name else "rmdir folder"
        
        elif self._matches_patterns(input_lower, ['delete', 'remove', 'erase', 'trash'], ['file']):
            item_name = self._extract_name(input_lower, ['file'], ['named', 'called'])
            return f"del {item_name}" if item_name else "del file.txt"
        
        elif self._matches_patterns(input_lower, ['move', 'transfer', 'relocate'], ['file', 'folder']):
            return self._extract_move_command(input_lower)
        
        elif self._matches_patterns(input_lower, ['copy', 'duplicate'], ['file', 'folder']):
            return self._extract_copy_command(input_lower)
        
        elif self._matches_patterns(input_lower, ['rename', 'change name'], ['file', 'folder']):
            return self._extract_rename_command(input_lower)
        
        elif self._matches_patterns(input_lower, ['show', 'display', 'read'], ['content', 'contents'], ['file']):
            file_name = self._extract_name(input_lower, ['file'], ['named', 'called'])
            return f"type {file_name}" if file_name else "type file.txt"
        
        # System operations
        elif self._matches_patterns(input_lower, ['process', 'running', 'task', 'program']):
            return "tasklist"
        
        elif self._matches_patterns(input_lower, ['kill', 'terminate', 'stop'], ['process', 'task', 'program']):
            return self._extract_kill_command(input_lower)
        
        elif self._matches_patterns(input_lower, ['cpu', 'processor', 'processor usage']):
            return "cpu"
        
        elif self._matches_patterns(input_lower, ['memory', 'ram', 'memory usage']):
            return "mem"
        
        elif self._matches_patterns(input_lower, ['current', 'working'], ['directory', 'folder', 'path']):
            return "cd"
        
        elif self._matches_patterns(input_lower, ['change', 'go', 'navigate'], ['directory', 'folder']):
            dir_name = self._extract_name(input_lower, ['directory', 'folder'], ['to', 'into'])
            return f"cd {dir_name}" if dir_name else "cd"
        
        # Network operations
        elif self._matches_patterns(input_lower, ['network', 'ip', 'configuration', 'config']):
            return "ipconfig"
        
        elif self._matches_patterns(input_lower, ['ping', 'test connection']):
            return self._extract_ping_command(input_lower)
        
        elif self._matches_patterns(input_lower, ['network', 'connection', 'port']):
            return "netstat"
        
        # Utility operations
        elif self._matches_patterns(input_lower, ['clear', 'clean'], ['screen', 'console']):
            return "cls"
        
        elif self._matches_patterns(input_lower, ['echo', 'print', 'say']):
            return self._extract_echo_command(input_lower)
        
        elif self._matches_patterns(input_lower, ['help', 'commands', 'what can i do']):
            return "help"
        
        elif self._matches_patterns(input_lower, ['exit', 'quit', 'close', 'stop']):
            return "exit"
        
        else:
            return "help"
    
    def _matches_patterns(self, text: str, action_words: List[str], object_words: List[str]) -> bool:
        """Check if text matches any combination of action and object words."""
        return (any(word in text for word in action_words) and 
                any(word in text for word in object_words))
    
    def _extract_name(self, text: str, object_words: List[str], name_indicators: List[str]) -> str:
        """Extract name from natural language."""
        # Try different patterns
        patterns = [
            r'(?:' + '|'.join(object_words) + r')\s+(?:' + '|'.join(name_indicators) + r')?\s*(\w+(?:\.\w+)?)',
            r'(?:' + '|'.join(name_indicators) + r')\s+(\w+(?:\.\w+)?)',
            r'(\w+(?:\.\w+)?)\s+(?:' + '|'.join(object_words) + r')',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_move_command(self, text: str) -> str:
        """Extract move command from natural language."""
        # Extract source file
        file_patterns = [
            r'(\w+\.\w+)',
            r'file\s+(\w+(?:\.\w+)?)',
        ]
        
        source = None
        for pattern in file_patterns:
            match = re.search(pattern, text)
            if match:
                source = match.group(1)
                break
        
        # Extract destination
        dest_patterns = [
            r'(?:into|to|in)\s+(\w+)',
            r'(\w+)\s+(?:folder|directory)',
        ]
        
        dest = None
        for pattern in dest_patterns:
            match = re.search(pattern, text)
            if match:
                dest = match.group(1)
                break
        
        if source and dest:
            return f"mv {source} {dest}"
        elif source:
            return f"mv {source} destination"
        else:
            return "mv file.txt destination"
    
    def _extract_copy_command(self, text: str) -> str:
        """Extract copy command from natural language."""
        # Similar to move but with copy command
        file_patterns = [
            r'(\w+\.\w+)',
            r'file\s+(\w+(?:\.\w+)?)',
        ]
        
        source = None
        for pattern in file_patterns:
            match = re.search(pattern, text)
            if match:
                source = match.group(1)
                break
        
        dest_patterns = [
            r'(?:to|into)\s+(\w+)',
            r'(\w+)\s+(?:folder|directory)',
        ]
        
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
    
    def _extract_rename_command(self, text: str) -> str:
        """Extract rename command from natural language."""
        # Extract old and new names
        patterns = [
            r'(\w+(?:\.\w+)?)\s+(?:to|as)\s+(\w+(?:\.\w+)?)',
            r'rename\s+(\w+(?:\.\w+)?)\s+(?:to|as)\s+(\w+(?:\.\w+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                old_name = match.group(1)
                new_name = match.group(2)
                return f"ren {old_name} {new_name}"
        
        return "ren old.txt new.txt"
    
    def _extract_kill_command(self, text: str) -> str:
        """Extract kill command from natural language."""
        # Extract process ID or name
        pid_match = re.search(r'(?:id|pid)\s+(\d+)', text)
        if pid_match:
            return f"taskkill /pid {pid_match.group(1)}"
        
        name_match = re.search(r'(?:process|task)\s+(\w+)', text)
        if name_match:
            return f"taskkill /im {name_match.group(1)}"
        
        return "taskkill /pid 1234"
    
    def _extract_ping_command(self, text: str) -> str:
        """Extract ping command from natural language."""
        # Extract hostname or IP
        host_match = re.search(r'(?:ping|test)\s+(\w+(?:\.\w+)*)', text)
        if host_match:
            return f"ping {host_match.group(1)}"
        
        return "ping google.com"
    
    def _extract_echo_command(self, text: str) -> str:
        """Extract echo command from natural language."""
        # Extract text to echo
        text_match = re.search(r'(?:echo|print|say)\s+(.+)', text)
        if text_match:
            return f"echo {text_match.group(1)}"
        
        return "echo hello"
    
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
            elif cmd == 'touch':
                return self._touch(args)
            elif cmd == 'echo':
                return self._echo(args)
            
            # System operations
            elif cmd in ['tasklist', 'ps']:
                return self._tasklist(args)
            elif cmd in ['taskkill', 'kill']:
                return self._taskkill(args)
            elif cmd == 'cpu':
                return self._cpu(args)
            elif cmd == 'mem':
                return self._mem(args)
            
            # Network operations
            elif cmd == 'ipconfig':
                return self._ipconfig(args)
            elif cmd == 'ping':
                return self._ping(args)
            elif cmd == 'netstat':
                return self._netstat(args)
            
            # Utility operations
            elif cmd in ['cls', 'clear']:
                return self._cls(args)
            elif cmd == 'history':
                return self._history(args)
            elif cmd == 'help':
                return self._help(args)
            elif cmd in ['exit', 'quit']:
                return "exit"
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
                return f"Error: '{path}' does not exist"
            
            if not os.path.isdir(path):
                return f"Error: '{path}' is not a directory"
            
            items = os.listdir(path)
            items.sort()
            
            result = []
            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    result.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    result.append(f"📄 {item} ({size} bytes)")
            
            return '\n'.join(result) if result else "Directory is empty"
            
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
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
                return f"Error: Directory '{new_dir}' does not exist"
            
            if not os.path.isdir(new_dir):
                return f"Error: '{new_dir}' is not a directory"
            
            self.current_dir = new_dir
            os.chdir(new_dir)
            return f"Changed to: {new_dir}"
            
        except Exception as e:
            return f"Error changing directory: {str(e)}"
    
    def _pwd(self, args: List[str]) -> str:
        """Print working directory."""
        return self.current_dir
    
    def _mkdir(self, args: List[str]) -> str:
        """Create directory."""
        if not args:
            return "Error: mkdir requires a directory name"
        
        try:
            for dir_name in args:
                dir_path = os.path.join(self.current_dir, dir_name)
                os.makedirs(dir_path, exist_ok=True)
            return f"Created directory: {', '.join(args)}"
        except Exception as e:
            return f"Error creating directory: {str(e)}"
    
    def _rm(self, args: List[str]) -> str:
        """Remove file or directory."""
        if not args:
            return "Error: rm requires a file or directory name"
        
        try:
            for item in args:
                item_path = os.path.join(self.current_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            return f"Removed: {', '.join(args)}"
        except Exception as e:
            return f"Error removing: {str(e)}"
    
    def _mv(self, args: List[str]) -> str:
        """Move or rename file or directory."""
        if len(args) < 2:
            return "Error: mv requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.current_dir, dest)
            
            shutil.move(source, dest)
            return f"Moved '{source}' to '{dest}'"
        except Exception as e:
            return f"Error moving: {str(e)}"
    
    def _cp(self, args: List[str]) -> str:
        """Copy file or directory."""
        if len(args) < 2:
            return "Error: cp requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.current_dir, dest)
            
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            
            return f"Copied '{source}' to '{dest}'"
        except Exception as e:
            return f"Error copying: {str(e)}"
    
    def _touch(self, args: List[str]) -> str:
        """Create a new file."""
        if not args:
            return "Error: touch requires a file name"
        
        try:
            for file_name in args:
                file_path = os.path.join(self.current_dir, file_name)
                with open(file_path, 'w') as f:
                    pass  # Create empty file
            return f"Created file: {', '.join(args)}"
        except Exception as e:
            return f"Error creating file: {str(e)}"
    
    def _cat(self, args: List[str]) -> str:
        """Display file contents."""
        if not args:
            return "Error: cat requires a file name"
        
        try:
            file_path = args[0]
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_dir, file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _echo(self, args: List[str]) -> str:
        """Echo text to console."""
        return ' '.join(args)
    
    def _cpu(self, args: List[str]) -> str:
        """Show CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            return f"CPU Usage: {cpu_percent}% (Cores: {cpu_count})"
        except Exception as e:
            return f"Error getting CPU info: {str(e)}"
    
    def _mem(self, args: List[str]) -> str:
        """Show memory usage."""
        try:
            memory = psutil.virtual_memory()
            return f"Memory: {memory.percent}% used ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)"
        except Exception as e:
            return f"Error getting memory info: {str(e)}"
    
    def _ps(self, args: List[str]) -> str:
        """Show running processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            result = ["PID     Name                    CPU%    Memory%"]
            result.append("-" * 50)
            
            for proc in processes[:20]:
                pid = str(proc['pid']).ljust(7)
                name = (proc['name'] or 'N/A')[:20].ljust(20)
                cpu = f"{proc['cpu_percent'] or 0:.1f}".ljust(6)
                memory = f"{proc['memory_percent'] or 0:.1f}"
                result.append(f"{pid} {name} {cpu} {memory}")
            
            return '\n'.join(result)
        except Exception as e:
            return f"Error getting processes: {str(e)}"
    
    def _kill(self, args: List[str]) -> str:
        """Kill a process by PID."""
        if not args:
            return "Error: kill requires a process ID"
        
        try:
            pid = int(args[0])
            proc = psutil.Process(pid)
            proc.terminate()
            return f"Terminated process {pid}"
        except (ValueError, psutil.NoSuchProcess) as e:
            return f"Error killing process: {str(e)}"
    
    def _clear(self, args: List[str]) -> str:
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        return ""
    
    def _history(self, args: List[str]) -> str:
        """Show command history with enhanced display."""
        try:
            # Handle clear history command
            if args and args[0].lower() == 'clear':
                return self._clear_history()
            
            history_length = readline.get_current_history_length()
            if history_length == 0:
                return "No command history"
            
            result = []
            result.append("📜 Command History:")
            result.append("=" * 60)
            
            # Show last 20 commands with better formatting
            start_idx = max(0, history_length - 20)
            for i in range(start_idx, history_length):
                cmd = readline.get_history_item(i + 1)
                if cmd:
                    # Add visual indicators for different command types
                    if cmd.startswith(('dir', 'ls')):
                        result.append(f"{i + 1:4d}  📁 {cmd}")
                    elif cmd.startswith(('mkdir', 'rmdir')):
                        result.append(f"{i + 1:4d}  📂 {cmd}")
                    elif cmd.startswith(('del', 'rm')):
                        result.append(f"{i + 1:4d}  🗑️ {cmd}")
                    elif cmd.startswith(('copy', 'cp', 'move', 'mv')):
                        result.append(f"{i + 1:4d}  📋 {cmd}")
                    elif cmd.startswith(('create', 'make', 'delete', 'show')):
                        result.append(f"{i + 1:4d}  🗣️ {cmd}")
                    else:
                        result.append(f"{i + 1:4d}  💻 {cmd}")
            
            if history_length > 20:
                result.append(f"\n... and {history_length - 20} more commands")
            
            result.append("=" * 60)
            result.append(f"📊 Total commands: {history_length}")
            result.append("⌨️  Use ↑↓ arrow keys to navigate history")
            result.append("💡 Type 'history clear' to clear history")
            
            return '\n'.join(result)
        except Exception as e:
            return f"Error accessing history: {str(e)}"
    
    def _clear_history(self) -> str:
        """Clear command history."""
        try:
            # Clear readline history
            readline.clear_history()
            
            # Clear history file
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            
            return "✅ Command history cleared successfully!"
        except Exception as e:
            return f"Error clearing history: {str(e)}"
    
    def _rmdir(self, args: List[str]) -> str:
        """Remove empty directory."""
        if not args:
            return "Error: rmdir requires a directory name"
        
        try:
            for dir_name in args:
                dir_path = os.path.join(self.current_dir, dir_name)
                os.rmdir(dir_path)
            return f"Removed directory: {', '.join(args)}"
        except Exception as e:
            return f"Error removing directory: {str(e)}"
    
    def _del(self, args: List[str]) -> str:
        """Delete file."""
        if not args:
            return "Error: del requires a file name"
        
        try:
            for file_name in args:
                file_path = os.path.join(self.current_dir, file_name)
                os.remove(file_path)
            return f"Deleted file: {', '.join(args)}"
        except Exception as e:
            return f"Error deleting file: {str(e)}"
    
    def _move(self, args: List[str]) -> str:
        """Move file or directory."""
        if len(args) < 2:
            return "Error: move requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.current_dir, dest)
            
            shutil.move(source, dest)
            return f"Moved '{source}' to '{dest}'"
        except Exception as e:
            return f"Error moving: {str(e)}"
    
    def _copy(self, args: List[str]) -> str:
        """Copy file or directory."""
        if len(args) < 2:
            return "Error: copy requires source and destination"
        
        try:
            source = args[0]
            dest = args[1]
            
            if not os.path.isabs(source):
                source = os.path.join(self.current_dir, source)
            if not os.path.isabs(dest):
                dest = os.path.join(self.current_dir, dest)
            
            if os.path.isdir(source):
                shutil.copytree(source, dest)
            else:
                shutil.copy2(source, dest)
            
            return f"Copied '{source}' to '{dest}'"
        except Exception as e:
            return f"Error copying: {str(e)}"
    
    def _ren(self, args: List[str]) -> str:
        """Rename file or directory."""
        if len(args) < 2:
            return "Error: ren requires old name and new name"
        
        try:
            old_name = args[0]
            new_name = args[1]
            
            if not os.path.isabs(old_name):
                old_name = os.path.join(self.current_dir, old_name)
            if not os.path.isabs(new_name):
                new_name = os.path.join(self.current_dir, new_name)
            
            os.rename(old_name, new_name)
            return f"Renamed '{old_name}' to '{new_name}'"
        except Exception as e:
            return f"Error renaming: {str(e)}"
    
    def _type(self, args: List[str]) -> str:
        """Display file contents."""
        if not args:
            return "Error: type requires a file name"
        
        try:
            file_path = args[0]
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.current_dir, file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _tasklist(self, args: List[str]) -> str:
        """Show running processes."""
        try:
            result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error getting task list: {str(e)}"
    
    def _taskkill(self, args: List[str]) -> str:
        """Kill a process."""
        if not args:
            return "Error: taskkill requires process ID or name"
        
        try:
            result = subprocess.run(['taskkill'] + args, capture_output=True, text=True, shell=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error killing process: {str(e)}"
    
    def _ipconfig(self, args: List[str]) -> str:
        """Show network configuration."""
        try:
            result = subprocess.run(['ipconfig'] + args, capture_output=True, text=True, shell=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error getting network config: {str(e)}"
    
    def _ping(self, args: List[str]) -> str:
        """Ping a host."""
        if not args:
            return "Error: ping requires a hostname or IP"
        
        try:
            result = subprocess.run(['ping'] + args, capture_output=True, text=True, shell=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error pinging: {str(e)}"
    
    def _netstat(self, args: List[str]) -> str:
        """Show network connections."""
        try:
            result = subprocess.run(['netstat'] + args, capture_output=True, text=True, shell=True)
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Error getting network stats: {str(e)}"
    
    def _cls(self, args: List[str]) -> str:
        """Clear the screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        return ""
    
    def _help(self, args: List[str]) -> str:
        """Show help information."""
        return """
Unified Python Terminal v1.0
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
  rmdir <dir>            - Remove empty directory
  del <file>             - Delete file
  copy <source> <dest>   - Copy file or directory
  move <source> <dest>   - Move or rename file or directory
  ren <old> <new>        - Rename file or directory
  type <file>            - Display file contents
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
  "create a folder called test" → mkdir test
  "delete the folder test" → rmdir test
  "delete the file hello.txt" → del hello.txt
  "copy file.txt to backup" → copy file.txt backup
  "move file1.txt to test folder" → move file1.txt test
  "rename old.txt to new.txt" → ren old.txt new.txt
  "show contents of file.txt" → type file.txt
  "show all running processes" → tasklist
  "kill process with id 1234" → taskkill /pid 1234
  "check CPU usage" → cpu
  "check memory usage" → mem
  "show network configuration" → ipconfig
  "ping google.com" → ping google.com
  "show network connections" → netstat
  "clear the screen" → cls
  "echo hello world" → echo hello world

⌨️ KEYBOARD SHORTCUTS:
  ↑↓ Arrow Keys          - Navigate command history
  Tab                    - Auto-complete commands and files
  Ctrl+C                 - Interrupt current operation
  Ctrl+D                 - Exit terminal
        """
    
    def process_input(self, user_input: str) -> str:
        """Process user input and return executable command."""
        if not user_input.strip():
            return ""
        
        # Check if it's already a Python command
        if self._is_python_command(user_input):
            return user_input
        
        # Convert natural language to command
        command = self._convert_natural_language(user_input)
        
        # Debug: print the converted command
        print(f"Converted: '{user_input}' → '{command}'")
        
        return command
    
    def run(self):
        """Main terminal loop with enhanced history and auto-completion."""
        print("Unified Python Terminal v1.0")
        print("Supports both Python commands and flexible natural English")
        print("Features: Command History (↑↓), Auto-completion (Tab), AI Commands")
        print("Type 'help' for available commands, 'exit' to quit")
        print("-" * 70)
        
        while True:
            try:
                # Update current directory
                self.current_dir = os.getcwd()
                
                # Get user input with enhanced prompt
                prompt = f"unified:{os.path.basename(self.current_dir)}$ "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Save to history (both original input and converted command)
                self._save_history(user_input)
                
                # Process input and get command
                command = self.process_input(user_input)
                
                # Handle exit command
                if command == "exit":
                    print("Goodbye!")
                    break
                
                # Execute command
                result = self._execute_command(command)
                
                # Display result
                if result:
                    print(result)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' to close the terminal")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {str(e)}")


def main():
    """Main entry point."""
    terminal = UnifiedTerminal()
    terminal.run()


if __name__ == "__main__":
    main()