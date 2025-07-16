#!/usr/bin/env python3

import paramiko
import time
import logging
from typing import Optional, List, Union
import sys

class DNOSSSH:
    """A class to handle SSH connections to DNOS devices with proper timing and debugging."""
    
    def __init__(self, hostname: str, username: str, password: str, port: int = 22, debug: bool = False):
        """
        Initialize the DNOS SSH connection.
        
        Args:
            hostname: The hostname or IP address of the DNOS device
            username: SSH username
            password: SSH password
            port: SSH port (default: 22)
            debug: Enable debug logging (default: False)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.ssh = None
        self.shell = None
        
        # Configure logging
        self.logger = logging.getLogger(f'DNOSSSH_{hostname}')
        if debug:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
    
    def connect(self) -> bool:
        """
        Establish SSH connection to the DNOS device.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.logger.info(f"Connecting to {self.hostname}...")
            self.ssh.connect(
                self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False
            )
            
            self.shell = self.ssh.invoke_shell()
            time.sleep(2)  # Wait for shell to be ready
            
            # Clear any initial output
            self._clear_buffer()
            
            self.logger.info("Successfully connected to device")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {str(e)}")
            return False
    
    def disconnect(self):
        """Close the SSH connection."""
        if self.ssh:
            self.ssh.close()
            self.logger.info("Connection closed")
    
    def _clear_buffer(self):
        """Clear the shell buffer."""
        if self.shell.recv_ready():
            self.shell.recv(65535)
    
    def _read_channel(self) -> str:
        """
        Read available data from the SSH channel.
        
        Returns:
            str: Available data from the channel, empty string if no data
        """
        if not self.shell:
            return ""
        
        if self.shell.recv_ready():
            try:
                data = self.shell.recv(4096).decode('utf-8', errors='ignore')
                return data
            except Exception as e:
                self.logger.debug(f"Error reading channel: {e}")
                return ""
        return ""
    
    def _wait_for_prompt(self, timeout: int = 30) -> bool:
        """
        Wait for the command prompt to appear.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if prompt is found, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.shell.recv_ready():
                output = self.shell.recv(65535).decode('utf-8')
                if '>' in output or '#' in output:
                    return True
            time.sleep(0.1)
        return False
    
    def send_command(self, command: str, wait_time: float = 1.0) -> str:
        """
        Send a command and wait for the response.
        
        Args:
            command: Command to send
            wait_time: Time to wait after sending command
            
        Returns:
            str: Command output
        """
        if not self.shell:
            raise Exception("Not connected to device")
        
        self.logger.debug(f"Sending command: {command}")
        self.shell.send(command + '\n')
        time.sleep(wait_time)
        
        output = ""
        if self.shell.recv_ready():
            output = self.shell.recv(65535).decode('utf-8')
            self.logger.debug(f"Received output: {output}")
        
        return output
    
    def send_command_with_full_output(self, command: str, timeout: int = 120) -> str:
        """
        Send a command and collect all output until prompt returns.
        
        Args:
            command: Command to send
            timeout: Maximum time to wait for complete output
            
        Returns:
            str: Complete command output
        """
        if not self.shell:
            raise Exception("Not connected to device")
        
        self.logger.debug(f"Sending command with full output: {command}")
        self.shell.send(command + '\n')
        
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            chunk = self._read_channel()
            if chunk:
                output += chunk
                # Check if we've reached the prompt (device-specific)
                if '#' in chunk or '>' in chunk:
                    # Give a little more time for any final output
                    time.sleep(0.5)
                    final_chunk = self._read_channel()
                    if final_chunk:
                        output += final_chunk
                    break
            time.sleep(0.1)
        
        self.logger.debug(f"Received {len(output)} characters of output")
        return output
    
    def collect_xml_config(self, timeout: int = 180) -> str:
        """
        Collect complete XML configuration from the device.
        Reads until the </config> tag is found or timeout is reached.
        
        Args:
            timeout: Maximum time to wait for complete XML
            
        Returns:
            str: Complete XML configuration
        """
        if not self.shell:
            raise Exception("Not connected to device")
        
        command = 'show config | display-xml | no-more'
        self.logger.info(f"Collecting XML config from {self.hostname}")
        self.shell.send(command + '\n')
        
        output = ""
        start_time = time.time()
        closing_tag = '</config>'
        
        while time.time() - start_time < timeout:
            chunk = self._read_channel()
            if chunk:
                output += chunk
                if closing_tag in output:
                    self.logger.info("Found closing </config> tag, XML collection complete.")
                    break
            time.sleep(0.1)
        else:
            self.logger.warning("Timeout reached before </config> tag was found.")
        
        self.logger.debug(f"Total XML output length: {len(output)}")
        return output
    
    def configure(self, commands: Union[str, List[str]], commit: bool = True) -> bool:
        """
        Enter configuration mode and apply commands.
        
        Args:
            commands: Single command string or list of commands
            commit: Whether to commit the configuration (default: True)
            
        Returns:
            bool: True if configuration was successful
        """
        def read_all_output(shell, wait=0.5, max_reads=10):
            output = ""
            for _ in range(max_reads):
                time.sleep(wait)
                while self.shell.recv_ready():
                    output += self.shell.recv(65535).decode('utf-8')
            return output
        try:
            # Enter configuration mode
            output = self.send_command('configure')
            self.logger.debug(f"Output after 'configure': {output}")
            print(f"Output after 'configure':\n{output}")
            time.sleep(1)
            
            # Convert single command to list
            if isinstance(commands, str):
                commands = [commands]
            
            # Send each command
            for cmd in commands:
                output = self.send_command(cmd)
                self.logger.debug(f"Output after '{cmd}': {output}")
                print(f"Output after '{cmd}':\n{output}")
                time.sleep(0.5)
            
            # Commit if requested
            commit_success = False
            if commit:
                commit_output = self.send_command('commit and-exit')
                commit_output += read_all_output(self.shell, wait=0.5, max_reads=10)
                self.logger.debug(f"Output after 'commit and-exit': {commit_output}")
                print(f"Output after 'commit and-exit':\n{commit_output}")
                if 'error' not in commit_output.lower() and ('commit' in commit_output.lower() or 'completed' in commit_output.lower() or 'exit' in commit_output.lower()):
                    commit_success = True
                else:
                    # Try commit then exit separately
                    print("Trying separate 'commit' and 'exit'...")
                    commit_output = self.send_command('commit')
                    commit_output += read_all_output(self.shell, wait=0.5, max_reads=10)
                    self.logger.debug(f"Output after 'commit': {commit_output}")
                    print(f"Output after 'commit':\n{commit_output}")
                    exit_output = self.send_command('exit')
                    exit_output += read_all_output(self.shell, wait=0.5, max_reads=10)
                    self.logger.debug(f"Output after 'exit': {exit_output}")
                    print(f"Output after 'exit':\n{exit_output}")
                    if 'error' not in commit_output.lower() and ('commit' in commit_output.lower() or 'completed' in commit_output.lower() or 'exit' in exit_output.lower()):
                        commit_success = True
            else:
                exit_output = self.send_command('exit')
                exit_output += read_all_output(self.shell, wait=0.5, max_reads=10)
                self.logger.debug(f"Output after 'exit': {exit_output}")
                print(f"Output after 'exit':\n{exit_output}")
                time.sleep(1)
                commit_success = True
            
            return commit_success
            
        except Exception as e:
            self.logger.error(f"Configuration failed: {str(e)}")
            print(f"Configuration failed: {str(e)}")
            return False
    
    def get_configuration(self) -> Optional[str]:
        """
        Get the current device configuration.
        
        Returns:
            Optional[str]: Device configuration or None if failed
        """
        try:
            output = self.send_command('show configuration | display set')
            return output
        except Exception as e:
            self.logger.error(f"Failed to get configuration: {str(e)}")
            return None

# Example usage:
if __name__ == "__main__":
    # Example of how to use the class
    device = DNOSSSH(
        hostname="192.168.1.1",
        username="admin",
        password="password",
        debug=True
    )
    
    if device.connect():
        try:
            # Example configuration
            config_commands = [
                "set system host-name test-router",
                "set interfaces ge-0/0/0 description 'Test Interface'"
            ]
            
            if device.configure(config_commands):
                print("Configuration applied successfully")
            
            # Get current configuration
            current_config = device.get_configuration()
            if current_config:
                print("Current configuration:", current_config)
                
        finally:
            device.disconnect() 