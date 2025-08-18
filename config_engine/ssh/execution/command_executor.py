#!/usr/bin/env python3
"""
SSH Command Executor
Handles SSH command execution, output parsing, and result management
"""

import time
import re
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import queue

from core.logging import get_logger
from core.exceptions import ValidationError, BusinessLogicError
from ..base_ssh_manager import SSHCommandResult
from ..connection.connection_manager import SSHConnection


@dataclass
class CommandTemplate:
    """Command template for different device types"""
    name: str
    template: str
    device_types: List[str]
    parameters: List[str]
    description: str
    timeout: int = 30
    retry_count: int = 0
    validation_patterns: List[str] = None
    
    def __post_init__(self):
        """Initialize validation patterns if not provided"""
        if self.validation_patterns is None:
            self.validation_patterns = []
    
    def format_command(self, **kwargs) -> str:
        """
        Format command template with parameters.
        
        Args:
            **kwargs: Parameters to substitute in template
            
        Returns:
            Formatted command string
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValidationError(f"Missing required parameter: {e}")
    
    def validate_output(self, output: str) -> Tuple[bool, List[str]]:
        """
        Validate command output against patterns.
        
        Args:
            output: Command output to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if not self.validation_patterns:
            return True, []
        
        errors = []
        for pattern in self.validation_patterns:
            if not re.search(pattern, output, re.IGNORECASE):
                errors.append(f"Output does not match pattern: {pattern}")
        
        return len(errors) == 0, errors


class CommandExecutor:
    """
    Executes SSH commands and manages command results.
    """
    
    def __init__(self):
        """Initialize command executor."""
        self.logger = get_logger(__name__)
        
        # Command templates
        self.command_templates = self._initialize_command_templates()
        
        # Command history
        self.command_history: List[SSHCommandResult] = []
        self.history_lock = threading.Lock()
        
        # Output buffers
        self.output_buffers: Dict[str, queue.Queue] = {}
        self.buffer_lock = threading.Lock()
    
    def _initialize_command_templates(self) -> Dict[str, CommandTemplate]:
        """Initialize built-in command templates."""
        templates = {}
        
        # Basic system commands
        templates["show_version"] = CommandTemplate(
            name="show_version",
            template="show version",
            device_types=["generic", "cisco", "juniper", "arista"],
            parameters=[],
            description="Show device version information",
            timeout=15
        )
        
        templates["show_interfaces"] = CommandTemplate(
            name="show_interfaces",
            template="show interfaces",
            device_types=["generic", "cisco", "juniper", "arista"],
            parameters=[],
            description="Show interface information",
            timeout=20
        )
        
        templates["show_running_config"] = CommandTemplate(
            name="show_running_config",
            template="show running-config",
            device_types=["cisco", "arista"],
            parameters=[],
            description="Show running configuration",
            timeout=60
        )
        
        templates["show_config"] = CommandTemplate(
            name="show_config",
            template="show configuration",
            device_types=["juniper"],
            parameters=[],
            description="Show device configuration",
            timeout=60
        )
        
        templates["ping"] = CommandTemplate(
            name="ping",
            template="ping {destination} count {count}",
            device_types=["generic", "cisco", "juniper", "arista"],
            parameters=["destination", "count"],
            description="Ping destination with specified count",
            timeout=30,
            validation_patterns=[r"ping.*successful", r"ping.*failed"]
        )
        
        return templates
    
    def execute_command(self, connection: SSHConnection, command: str, 
                       timeout: int = 30, wait_for_prompt: bool = True) -> SSHCommandResult:
        """
        Execute a single command on a device.
        
        Args:
            connection: SSH connection to use
            command: Command to execute
            timeout: Command timeout in seconds
            wait_for_prompt: Whether to wait for command prompt
            
        Returns:
            SSHCommandResult with command output and status
        """
        try:
            if not connection.is_connected():
                return SSHCommandResult(
                    success=False,
                    command=command,
                    error="Connection not established",
                    device_name=connection.config.hostname
                )
            
            self.logger.info(f"Executing command: {command}")
            start_time = time.time()
            
            # Clear any existing output
            self._clear_connection_buffer(connection)
            
            # Send command
            if not self._send_command(connection, command):
                return SSHCommandResult(
                    success=False,
                    command=command,
                    error="Failed to send command",
                    device_name=connection.config.hostname
                )
            
            # Wait for output
            output = self._wait_for_output(connection, timeout, wait_for_prompt)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create result
            result = SSHCommandResult(
                success=True,
                command=command,
                output=output,
                execution_time=execution_time,
                device_name=connection.config.hostname
            )
            
            # Add to history
            self._add_to_history(result)
            
            self.logger.info(f"Command executed successfully in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time if 'start_time' in locals() else 0
            
            result = SSHCommandResult(
                success=False,
                command=command,
                error=str(e),
                execution_time=execution_time,
                device_name=connection.config.hostname
            )
            
            self._add_to_history(result)
            self.logger.error(f"Command execution failed: {e}")
            return result
    
    def execute_commands(self, connection: SSHConnection, commands: List[str], 
                        timeout: int = 30, wait_between: float = 1.0) -> List[SSHCommandResult]:
        """
        Execute multiple commands on a device.
        
        Args:
            connection: SSH connection to use
            commands: List of commands to execute
            timeout: Command timeout in seconds
            wait_between: Wait time between commands
            
        Returns:
            List of SSHCommandResult objects
        """
        results = []
        
        for i, command in enumerate(commands):
            self.logger.info(f"Executing command {i+1}/{len(commands)}: {command}")
            
            # Execute command
            result = self.execute_command(connection, command, timeout)
            results.append(result)
            
            # Wait between commands (except for the last one)
            if i < len(commands) - 1 and wait_between > 0:
                time.sleep(wait_between)
            
            # Stop if command failed
            if not result.success:
                self.logger.warning(f"Command failed, stopping execution: {command}")
                break
        
        return results
    
    def execute_template(self, connection: SSHConnection, template_name: str, 
                        **kwargs) -> SSHCommandResult:
        """
        Execute a command using a predefined template.
        
        Args:
            connection: SSH connection to use
            template_name: Name of the command template
            **kwargs: Parameters for the template
            
        Returns:
            SSHCommandResult with command output and status
        """
        if template_name not in self.command_templates:
            return SSHCommandResult(
                success=False,
                command=template_name,
                error=f"Unknown command template: {template_name}",
                device_name=connection.config.hostname
            )
        
        template = self.command_templates[template_name]
        
        try:
            # Format command
            command = template.format_command(**kwargs)
            
            # Execute command
            result = self.execute_command(connection, command, template.timeout)
            
            # Validate output if patterns are defined
            if template.validation_patterns and result.success:
                is_valid, errors = template.validate_output(result.output or "")
                if not is_valid:
                    result.success = False
                    result.error = f"Output validation failed: {'; '.join(errors)}"
            
            return result
            
        except ValidationError as e:
            return SSHCommandResult(
                success=False,
                command=template_name,
                error=str(e),
                device_name=connection.config.hostname
            )
    
    def get_command_templates(self) -> Dict[str, CommandTemplate]:
        """Get all available command templates."""
        return self.command_templates.copy()
    
    def add_command_template(self, template: CommandTemplate) -> None:
        """
        Add a new command template.
        
        Args:
            template: CommandTemplate to add
        """
        self.command_templates[template.name] = template
        self.logger.info(f"Added command template: {template.name}")
    
    def remove_command_template(self, template_name: str) -> bool:
        """
        Remove a command template.
        
        Args:
            template_name: Name of the template to remove
            
        Returns:
            True if template was removed, False if not found
        """
        if template_name in self.command_templates:
            del self.command_templates[template_name]
            self.logger.info(f"Removed command template: {template_name}")
            return True
        return False
    
    def get_command_history(self, device_name: Optional[str] = None, 
                           limit: Optional[int] = None) -> List[SSHCommandResult]:
        """
        Get command execution history.
        
        Args:
            device_name: Filter by device name (optional)
            limit: Maximum number of results to return (optional)
            
        Returns:
            List of SSHCommandResult objects
        """
        with self.history_lock:
            if device_name:
                history = [result for result in self.command_history 
                          if result.device_name == device_name]
            else:
                history = self.command_history.copy()
            
            if limit:
                history = history[-limit:]
            
            return history
    
    def clear_command_history(self) -> None:
        """Clear command execution history."""
        with self.history_lock:
            self.command_history.clear()
            self.logger.info("Command history cleared")
    
    def _send_command(self, connection: SSHConnection, command: str) -> bool:
        """
        Send command to SSH connection.
        
        Args:
            connection: SSH connection to use
            command: Command to send
            
        Returns:
            True if command sent successfully, False otherwise
        """
        try:
            if not connection.shell:
                return False
            
            # Send command with newline
            command_with_newline = f"{command}\n"
            connection.shell.send(command_with_newline)
            
            # Update last activity
            connection.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            return False
    
    def _wait_for_output(self, connection: SSHConnection, timeout: int, 
                         wait_for_prompt: bool) -> str:
        """
        Wait for command output.
        
        Args:
            connection: SSH connection to use
            timeout: Timeout in seconds
            wait_for_prompt: Whether to wait for command prompt
            
        Returns:
            Command output string
        """
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if connection.shell and connection.shell.recv_ready():
                    data = connection.shell.recv(4096).decode('utf-8', errors='ignore')
                    output += data
                    
                    # Update last activity
                    connection.last_activity = datetime.now()
                    
                    # Check if we have a complete response
                    if wait_for_prompt and self._has_prompt(output):
                        break
                
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.debug(f"Error reading output: {e}")
                break
        
        return output.strip()
    
    def _has_prompt(self, output: str) -> bool:
        """
        Check if output contains a command prompt.
        
        Args:
            output: Output string to check
            
        Returns:
            True if prompt is found, False otherwise
        """
        # Common prompt patterns
        prompt_patterns = [
            r'[#>]\s*$',           # Cisco/Arista style
            r'%\s*$',              # Juniper style
            r'\$\s*$',             # Linux/Unix style
            r'admin@.*>\s*$',      # Generic admin prompt
            r'root@.*#\s*$'        # Root prompt
        ]
        
        for pattern in prompt_patterns:
            if re.search(pattern, output, re.MULTILINE):
                return True
        
        return False
    
    def _clear_connection_buffer(self, connection: SSHConnection) -> None:
        """
        Clear any existing output in the connection buffer.
        
        Args:
            connection: SSH connection to clear buffer for
        """
        try:
            if connection.shell and connection.shell.recv_ready():
                connection.shell.recv(65535)
        except Exception as e:
            self.logger.debug(f"Error clearing buffer: {e}")
    
    def _add_to_history(self, result: SSHCommandResult) -> None:
        """
        Add command result to history.
        
        Args:
            result: SSHCommandResult to add
        """
        with self.history_lock:
            self.command_history.append(result)
            
            # Keep only last 1000 results
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-1000:]
    
    def get_executor_info(self) -> Dict[str, Any]:
        """
        Get command executor information.
        
        Returns:
            Dictionary containing executor information
        """
        return {
            "command_templates": len(self.command_templates),
            "command_history_size": len(self.command_history),
            "available_templates": list(self.command_templates.keys()),
            "total_commands_executed": len(self.command_history),
            "successful_commands": len([r for r in self.command_history if r.success]),
            "failed_commands": len([r for r in self.command_history if not r.success])
        }
