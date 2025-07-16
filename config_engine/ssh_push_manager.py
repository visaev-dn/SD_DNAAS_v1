#!/usr/bin/env python3
"""
SSH Configuration Push Manager
Handles configuration deployment, validation, and removal via SSH.
"""
import os
import yaml
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import subprocess
import sys
import paramiko
import time
import concurrent.futures
import threading

class SSHPushManager:
    def __init__(self):
        self.base_dir = Path("configs")
        self.pending_dir = self.base_dir / "pending"
        self.deployed_dir = self.base_dir / "deployed"
        self.removed_dir = self.base_dir / "removed"
        self.logs_dir = self.base_dir / "deployment_logs"
        
        # Create directory structure
        self._create_directories()
    
    def _create_directories(self):
        """Create the configuration directory structure."""
        directories = [
            self.base_dir,
            self.pending_dir,
            self.deployed_dir,
            self.removed_dir,
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_available_configs(self) -> List[Dict]:
        """Get list of available configurations for deployment (pending configs)."""
        configs = []
        
        # Check pending directory for configurations ready to deploy
        for config_file in self.pending_dir.glob("*.yaml"):
            config_info = {
                "name": config_file.stem,
                "path": str(config_file),
                "type": "bridge_domain",
                "status": "pending",
                "created": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            }
            configs.append(config_info)
        
        return configs
    
    def get_deployed_configs(self) -> List[Dict]:
        """Get list of currently deployed configurations."""
        deployed_configs = []
        
        for config_file in self.deployed_dir.glob("*.yaml"):
            config_info = {
                "name": config_file.stem,
                "path": str(config_file),
                "type": "bridge_domain",
                "status": "deployed",
                "deployed_at": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            }
            deployed_configs.append(config_info)
        
        return deployed_configs
    
    def get_removed_configs(self) -> List[Dict]:
        """Get list of removed configurations that can be restored."""
        removed_configs = []
        
        for config_file in self.removed_dir.glob("*.yaml"):
            config_info = {
                "name": config_file.stem,
                "path": str(config_file),
                "type": "bridge_domain",
                "status": "removed",
                "removed_at": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            }
            removed_configs.append(config_info)
        
        return removed_configs
    
    def restore_config(self, config_name: str) -> Tuple[bool, List[str]]:
        """
        Restore a removed configuration to pending for redeployment.
        
        Args:
            config_name: Name of the configuration to restore
            
        Returns:
            Tuple of (success, errors)
        """
        # Check if config exists in removed directory
        removed_config_path = self.removed_dir / f"{config_name}.yaml"
        if not removed_config_path.exists():
            return False, [f"Configuration {config_name} not found in removed directory"]
        
        # Check if config already exists in pending directory
        pending_config_path = self.pending_dir / f"{config_name}.yaml"
        if pending_config_path.exists():
            return False, [f"Configuration {config_name} already exists in pending directory"]
        
        # Check if config already exists in deployed directory
        deployed_config_path = self.deployed_dir / f"{config_name}.yaml"
        if deployed_config_path.exists():
            return False, [f"Configuration {config_name} already exists in deployed directory"]
        
        try:
            # Move config from removed to pending
            shutil.move(str(removed_config_path), str(pending_config_path))
            print(f"✅ Configuration {config_name} restored to pending")
            print(f"📁 Configuration moved from removed to pending")
            return True, []
        except Exception as e:
            error_msg = f"Failed to restore {config_name}: {e}"
            return False, [error_msg]
    
    def load_config(self, config_name: str) -> Optional[Dict]:
        """Load a configuration file from pending directory."""
        config_path = self.pending_dir / f"{config_name}.yaml"
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config {config_name}: {e}")
            return None
    
    def validate_config(self, config_name: str) -> Tuple[bool, List[str]]:
        """Validate a configuration before deployment."""
        errors = []
        
        # Load config
        config = self.load_config(config_name)
        if not config:
            errors.append(f"Configuration {config_name} not found in pending directory")
            return False, errors
        
        # Basic structure validation
        if not isinstance(config, dict):
            errors.append("Configuration must be a dictionary")
            return False, errors
        
        # Check for required devices
        if not config:
            errors.append("Configuration is empty")
            return False, errors
        
        # Validate each device configuration
        for device_name, device_config in config.items():
            if not isinstance(device_config, list):
                errors.append(f"Device {device_name}: configuration must be a list")
                continue
            
            # Check for required commands
            required_patterns = [
                "network-services bridge-domain instance",
                "interfaces",
                "l2-service enabled",
                "vlan-id"
            ]
            
            config_text = "\n".join(device_config)
            for pattern in required_patterns:
                if pattern not in config_text:
                    errors.append(f"Device {device_name}: missing required pattern '{pattern}'")
        
        return len(errors) == 0, errors

    def preview_cli_commands(self, config_name: str) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """
        Preview CLI commands that would be deployed for a configuration.
        
        Args:
            config_name: Name of the configuration to preview
            
        Returns:
            Tuple of (success, errors, device_commands)
        """
        errors = []
        device_commands = {}
        
        # Load config
        config = self.load_config(config_name)
        if not config:
            errors.append(f"Configuration {config_name} not found in pending directory")
            return False, errors, device_commands
        
        # Convert YAML config to CLI commands for each device
        for device_name, device_config in config.items():
            cli_commands = []
            
            # Start with configure terminal
            cli_commands.append("conf")
            
            # Add all configuration commands with ^ separators
            for command in device_config:
                cli_commands.append(f"{command} ^")
            
            # End with commit
            cli_commands.append("commit")
            
            device_commands[device_name] = cli_commands
        
        return True, errors, device_commands

    def preview_deletion_commands(self, config_name: str) -> Tuple[bool, List[str], Dict[str, List[str]]]:
        """
        Preview CLI deletion commands that would remove a configuration.
        
        Args:
            config_name: Name of the configuration to preview deletion for
            
        Returns:
            Tuple of (success, errors, device_commands)
        """
        errors = []
        device_commands = {}
        
        # Load config from deployed directory
        config_path = self.deployed_dir / f"{config_name}.yaml"
        if not config_path.exists():
            errors.append(f"Configuration {config_name} not found in deployed directory")
            return False, errors, device_commands
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"Error loading config {config_name}: {e}")
            return False, errors, device_commands
        
        # Convert YAML config to deletion CLI commands for each device
        for device_name, device_config in config.items():
            cli_commands = []
            
            # Start with configure terminal
            cli_commands.append("conf")
            
            # Extract unique interfaces and bridge domain instances for deletion
            interfaces_to_remove = set()
            bridge_domain_instances = set()
            
            for command in device_config:
                if "network-services bridge-domain instance" in command:
                    # Extract bridge domain instance name
                    parts = command.split()
                    if len(parts) >= 4:
                        instance_name = parts[3]  # g_visaev_v123
                        bridge_domain_instances.add(instance_name)
                elif "interfaces" in command and "l2-service" in command:
                    # Extract interface name
                    parts = command.split()
                    if len(parts) >= 2:
                        interface_name = parts[1]  # bundle-60000.123
                        interfaces_to_remove.add(interface_name)
            
            # Add deletion commands in reverse order (remove interfaces first, then bridge domain)
            # Remove interfaces
            for interface in sorted(interfaces_to_remove):
                cli_commands.append(f"no interfaces {interface} ^")
            
            # Remove bridge domain instances
            for instance in sorted(bridge_domain_instances):
                cli_commands.append(f"no network-services bridge-domain instance {instance} ^")
            
            # End with commit
            cli_commands.append("commit")
            
            device_commands[device_name] = cli_commands
        
        return True, errors, device_commands

    def _load_device_info(self, device_name: str) -> Optional[dict]:
        """Load SSH connection info for a device from devices.yaml."""
        devices_file = Path("devices.yaml")
        if not devices_file.exists():
            return None
        with open(devices_file, 'r') as f:
            devices_data = yaml.safe_load(f)
        defaults = devices_data.get('defaults', {})
        
        # Try exact match first
        device_data = devices_data.get(device_name, {})
        
        # If not found, try case-insensitive lookup
        if not device_data:
            for key in devices_data.keys():
                if key.lower() == device_name.lower():
                    device_data = devices_data[key]
                    break
        
        info = {
            'hostname': device_data.get('mgmt_ip'),
            'username': device_data.get('username', defaults.get('username')),
            'password': device_data.get('password', defaults.get('password')),
            'port': device_data.get('ssh_port', defaults.get('ssh_port', 22)),
        }
        if not info['hostname'] or not info['username'] or not info['password']:
            return None
        return info

    def _ssh_push_commands(self, device_info: dict, cli_commands: list, log_f) -> Tuple[bool, bool, Optional[str]]:
        """
        Push CLI commands to a device via SSH. 
        Returns (success, already_exists, error_message) tuple.
        """
        try:
            log_f.write(f"Connecting to {device_info['hostname']} as {device_info['username']}...\n")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=device_info['hostname'],
                port=device_info['port'],
                username=device_info['username'],
                password=device_info['password'],
                look_for_keys=False,
                allow_agent=False,
                timeout=15  # Increased timeout for connection
            )
            shell = ssh.invoke_shell()
            shell.settimeout(10)  # Set timeout for shell operations
            output = ''
            
            # Wait for initial prompt with timeout
            time.sleep(1)
            try:
                initial_output = shell.recv(4096).decode(errors='ignore')
                output += initial_output
                log_f.write(f"Initial connection output: {initial_output}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting initial output: {e}\n")
            
            # Send each command and collect output with timeout
            for cmd in cli_commands:
                log_f.write(f"Sending command: {cmd}\n")
                shell.send(cmd + '\n')
                
                # Wait longer for commit command, but with timeout
                if 'commit' in cmd.lower():
                    time.sleep(5)  # Wait longer for commit to complete
                else:
                    time.sleep(2)  # Wait for command to process
                
                # Try to receive output with timeout
                try:
                    chunk = shell.recv(4096).decode(errors='ignore')
                    output += chunk
                    log_f.write(f"Command response: {chunk}\n")
                except Exception as e:
                    log_f.write(f"Warning: Timeout or error receiving response: {e}\n")
                    # Continue anyway, might have partial output
            
            # Get final prompt state with timeout
            time.sleep(1)
            try:
                final_chunk = shell.recv(4096).decode(errors='ignore')
                output += final_chunk
                log_f.write(f"Final output: {final_chunk}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting final output: {e}\n")
            
            ssh.close()
            log_f.write(f"Complete SSH output for {device_info['hostname']}:\n{output}\n")
            
            # Check for "no configuration changes" message - this means config already exists
            already_exists = "no configuration changes were made" in output.lower()
            if already_exists:
                log_f.write(f"✅ Configuration already exists on device (no changes needed)\n")
                return True, True, None
            
            # Check for error patterns in the output and extract specific error messages
            error_patterns = [
                'Error:', 'ERROR:', 'Invalid', 'INVALID', 'Failed', 'FAILED',
                'not found', 'NOT FOUND', 'does not exist', 'DOES NOT EXIST',
                'syntax error', 'SYNTAX ERROR', 'command not found', 'COMMAND NOT FOUND',
                'permission denied', 'PERMISSION DENIED', 'access denied', 'ACCESS DENIED'
            ]
            
            # Look for specific error messages in the output
            error_message = None
            for pattern in error_patterns:
                if pattern.lower() in output.lower():
                    log_f.write(f"❌ Error pattern '{pattern}' found in output\n")
                    
                    # Extract the specific error message
                    lines = output.split('\n')
                    for line in lines:
                        if pattern.lower() in line.lower():
                            error_message = line.strip()
                            log_f.write(f"📋 Specific error: {error_message}\n")
                            break
                    
                    return False, False, error_message
            
            # Check for successful commit (if commit command was sent)
            if 'commit' in ' '.join(cli_commands).lower():
                # For DriveNets devices, successful commit can return to normal prompt OR stay in config mode
                # Both are valid success cases
                if 'commit' in output.lower():
                    # Check if commit succeeded (look for "Commit succeeded" message)
                    if 'commit succeeded' in output.lower():
                        log_f.write(f"✅ Commit appears successful (commit succeeded message found)\n")
                        return True, False, None
                    else:
                        log_f.write(f"❌ Commit command not found in output\n")
                        return False, False, "Commit command failed or not found in output"
                else:
                    log_f.write(f"❌ Commit command not found in output\n")
                    return False, False, "Commit command not found in output"
            
            log_f.write(f"✅ No error patterns found, deployment appears successful\n")
            return True, False, None
            
        except Exception as e:
            log_f.write(f"❌ SSH error for {device_info['hostname']}: {e}\n")
            return False, False, f"SSH connection error: {e}"

    def _ssh_push_commands_two_stage(self, device_info: dict, cli_commands: list, log_f, stage: str = "check") -> Tuple[bool, bool, Optional[str]]:
        """
        Push CLI commands to a device via SSH using two-stage approach.
        Stage can be "check" (commit-check) or "commit" (actual commit).
        Returns (success, already_exists, error_message) tuple.
        """
        try:
            log_f.write(f"Connecting to {device_info['hostname']} as {device_info['username']}...\n")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=device_info['hostname'],
                port=device_info['port'],
                username=device_info['username'],
                password=device_info['password'],
                look_for_keys=False,
                allow_agent=False,
                timeout=15
            )
            shell = ssh.invoke_shell()
            shell.settimeout(10)
            output = ''
            
            # Wait for initial prompt
            time.sleep(1)
            try:
                initial_output = shell.recv(4096).decode(errors='ignore')
                output += initial_output
                log_f.write(f"Initial connection output: {initial_output}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting initial output: {e}\n")
            
            # Modify commands based on stage
            if stage == "check":
                # Replace "commit" with "commit check" for validation stage
                modified_commands = []
                for cmd in cli_commands:
                    if cmd.lower() == "commit":
                        modified_commands.append("commit check")
                    else:
                        modified_commands.append(cmd)
                cli_commands = modified_commands
                log_f.write(f"Stage: CHECK - Using commit check for validation\n")
            else:
                log_f.write(f"Stage: COMMIT - Using actual commit\n")
            
            # Send each command and collect output
            for cmd in cli_commands:
                log_f.write(f"Sending command: {cmd}\n")
                shell.send(cmd + '\n')
                
                # Wait longer for commit/commit-check commands
                if 'commit' in cmd.lower():
                    time.sleep(5)
                else:
                    time.sleep(2)
                
                try:
                    chunk = shell.recv(4096).decode(errors='ignore')
                    output += chunk
                    log_f.write(f"Command response: {chunk}\n")
                except Exception as e:
                    log_f.write(f"Warning: Timeout or error receiving response: {e}\n")
            
            # Get final output
            time.sleep(1)
            try:
                final_chunk = shell.recv(4096).decode(errors='ignore')
                output += final_chunk
                log_f.write(f"Final output: {final_chunk}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting final output: {e}\n")
            
            ssh.close()
            log_f.write(f"Complete SSH output for {device_info['hostname']}:\n{output}\n")
            
            # Check for "no configuration changes" message
            already_exists = "no configuration changes were made" in output.lower()
            if already_exists:
                log_f.write(f"✅ Configuration already exists on device (no changes needed)\n")
                return True, True, None
            
            # Check for error patterns
            error_patterns = [
                'Error:', 'ERROR:', 'Invalid', 'INVALID', 'Failed', 'FAILED',
                'not found', 'NOT FOUND', 'does not exist', 'DOES NOT EXIST',
                'syntax error', 'SYNTAX ERROR', 'command not found', 'COMMAND NOT FOUND',
                'permission denied', 'PERMISSION DENIED', 'access denied', 'ACCESS DENIED'
            ]
            
            error_message = None
            for pattern in error_patterns:
                if pattern.lower() in output.lower():
                    log_f.write(f"❌ Error pattern '{pattern}' found in output\n")
                    
                    # Extract specific error message
                    lines = output.split('\n')
                    for line in lines:
                        if pattern.lower() in line.lower():
                            error_message = line.strip()
                            log_f.write(f"📋 Specific error: {error_message}\n")
                            break
                    
                    return False, False, error_message
            
            # Check for successful commit/commit-check
            if 'commit' in ' '.join(cli_commands).lower():
                if 'commit' in output.lower():
                    # Check for various success messages
                    success_indicators = [
                        'commit succeeded',
                        'commit check succeeded', 
                        'commit check passed successfully',
                        'commit check passed'
                    ]
                    
                    success_found = any(indicator in output.lower() for indicator in success_indicators)
                    
                    if success_found:
                        log_f.write(f"✅ {stage.upper()} appears successful\n")
                        return True, False, None
                    else:
                        log_f.write(f"❌ {stage.upper()} command not found in output\n")
                        return False, False, f"{stage.upper()} command failed or not found in output"
                else:
                    log_f.write(f"❌ {stage.upper()} command not found in output\n")
                    return False, False, f"{stage.upper()} command not found in output"
            
            log_f.write(f"✅ No error patterns found, {stage} appears successful\n")
            return True, False, None
            
        except Exception as e:
            log_f.write(f"❌ SSH error for {device_info['hostname']}: {e}\n")
            return False, False, f"SSH connection error: {e}"

    def _execute_on_device_parallel(self, device: str, device_info: dict, cli_commands: list, log_f, stage: str = "check") -> Tuple[str, bool, bool, Optional[str]]:
        """
        Execute commands on a single device (for parallel execution).
        Returns (device_name, success, already_exists, error_message).
        """
        try:
            log_f.write(f"🔄 Starting {stage.upper()} on {device} ({device_info['hostname']})...\n")
            ok, already_exists, error_message = self._ssh_push_commands_two_stage(device_info, cli_commands, log_f, stage)
            
            # Real-time progress feedback
            if ok:
                if already_exists:
                    print(f"   ✅ {device}: Configuration already exists")
                else:
                    print(f"   ✅ {device}: {stage.upper()} completed successfully")
            else:
                if error_message:
                    print(f"   ❌ {device}: {stage.upper()} failed - {error_message}")
                else:
                    print(f"   ❌ {device}: {stage.upper()} failed")
            
            return device, ok, already_exists, error_message
        except Exception as e:
            log_f.write(f"❌ Exception on {device}: {e}\n")
            print(f"   ❌ {device}: Exception - {e}")
            return device, False, False, f"Exception: {e}"

    def _verify_config_deployment_parallel(self, device: str, device_info: dict, service_name: str, log_f) -> Tuple[str, bool]:
        """
        Verify configuration deployment on a single device (for parallel execution).
        Returns (device_name, success).
        """
        try:
            log_f.write(f"🔍 Verifying {device} ({device_info['hostname']}) for configuration '{service_name}'...\n")
            success = self._verify_config_deployment(device_info, service_name, log_f)
            
            # Real-time progress feedback
            if success:
                print(f"   ✅ {device}: Configuration verified successfully")
            else:
                print(f"   ❌ {device}: Configuration verification failed")
            
            return device, success
        except Exception as e:
            log_f.write(f"❌ Verification exception on {device}: {e}\n")
            print(f"   ❌ {device}: Verification exception - {e}")
            return device, False

    def _verify_deletion_parallel(self, device: str, device_info: dict, service_name: str, log_f) -> Tuple[str, bool]:
        """
        Verify configuration deletion on a single device (for parallel execution).
        Returns (device_name, success).
        """
        try:
            log_f.write(f"🔍 Verifying deletion on {device} ({device_info['hostname']})...\n")
            success = self._verify_deletion(device_info, service_name, log_f)
            
            # Real-time progress feedback
            if success:
                print(f"   ✅ {device}: Deletion verified successfully")
            else:
                print(f"   ❌ {device}: Deletion verification failed")
            
            return device, success
        except Exception as e:
            log_f.write(f"❌ Deletion verification exception on {device}: {e}\n")
            print(f"   ❌ {device}: Deletion verification exception - {e}")
            return device, False

    def _verify_config_deployment(self, device_info: dict, service_name: str, log_f) -> bool:
        """Verify that the configuration was actually applied to the device."""
        try:
            print(f"🔍 Verifying {device_info['hostname']} for configuration '{service_name}'...")
            log_f.write(f"Verifying configuration on {device_info['hostname']}...\n")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=device_info['hostname'],
                port=device_info['port'],
                username=device_info['username'],
                password=device_info['password'],
                look_for_keys=False,
                allow_agent=False,
                timeout=15  # Increased timeout
            )
            
            # Use interactive shell like our deployment
            shell = ssh.invoke_shell()
            shell.settimeout(10)
            output = ''
            
            # Wait for initial prompt
            time.sleep(1)
            try:
                initial_output = shell.recv(4096).decode(errors='ignore')
                output += initial_output
                log_f.write(f"Initial connection output: {initial_output}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting initial output: {e}\n")
            
            # Check for specific configuration using the correct command
            command = f"show network-services bridge-domain {service_name}"
            print(f"   📋 Running: {command}")
            log_f.write(f"Running command: {command}\n")
            
            shell.send(command + '\n')
            time.sleep(2)
            
            try:
                response = shell.recv(4096).decode(errors='ignore')
                output += response
                log_f.write(f"Command response: {response}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting response: {e}\n")
            
            ssh.close()
            
            # Check if configuration exists
            config_exists = service_name in output
            print(f"   {'✅ Found' if config_exists else '❌ Not found'}")
            log_f.write(f"Configuration check: {'✅ Found' if config_exists else '❌ Not found'}\n")
            log_f.write(f"Command output: {output}\n")
            
            # Additional check for bridge domain format
            if not config_exists and "Bridge-Domain:" in output:
                # Check if the service name appears after "Bridge-Domain:"
                bridge_domain_line = [line for line in output.split('\n') if line.strip().startswith('Bridge-Domain:')]
                if bridge_domain_line and service_name in bridge_domain_line[0]:
                    config_exists = True
                    print(f"   ✅ Found (in Bridge-Domain format)")
                    log_f.write(f"Found in Bridge-Domain format: {bridge_domain_line[0]}\n")
            
            if config_exists:
                print(f"   ✅ Configuration verification successful for {device_info['hostname']}")
                log_f.write(f"✅ Configuration verification successful for {device_info['hostname']}\n")
            else:
                print(f"   ❌ Configuration verification failed for {device_info['hostname']}")
                log_f.write(f"❌ Configuration verification failed for {device_info['hostname']}\n")
            
            return config_exists
            
        except Exception as e:
            print(f"   ❌ SSH Error: {e}")
            log_f.write(f"❌ Verification error for {device_info['hostname']}: {e}\n")
            return False

    def _verify_deletion(self, device_info: dict, service_name: str, log_f) -> bool:
        """Verify that the configuration was actually removed from the device."""
        try:
            log_f.write(f"Verifying deletion on {device_info['hostname']}...\n")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=device_info['hostname'],
                port=device_info['port'],
                username=device_info['username'],
                password=device_info['password'],
                look_for_keys=False,
                allow_agent=False,
                timeout=15  # Increased timeout
            )
            
            # Use interactive shell like our deployment
            shell = ssh.invoke_shell()
            shell.settimeout(10)
            output = ''
            
            # Wait for initial prompt
            time.sleep(1)
            try:
                initial_output = shell.recv(4096).decode(errors='ignore')
                output += initial_output
                log_f.write(f"Initial connection output: {initial_output}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting initial output: {e}\n")
            
            # Check if bridge domain instance still exists (should NOT exist)
            command = f"show network-services bridge-domain {service_name}"
            log_f.write(f"Running command: {command}\n")
            shell.send(command + '\n')
            time.sleep(2)
            
            try:
                response = shell.recv(4096).decode(errors='ignore')
                output += response
                log_f.write(f"Command response: {response}\n")
            except Exception as e:
                log_f.write(f"Warning: Timeout getting response: {e}\n")
            
            ssh.close()
            
            # Check for successful deletion indicators
            # "ERROR: Unknown word" means the bridge domain doesn't exist (success!)
            # "Invalid command" also means it doesn't exist
            deletion_success_indicators = [
                "ERROR: Unknown word",
                "Invalid command",
                "not found",
                "does not exist"
            ]
            
            for indicator in deletion_success_indicators:
                if indicator.lower() in output.lower():
                    log_f.write(f"✅ Deletion verification successful - bridge domain no longer exists\n")
                    return True
            
            # If we see the service name in the output, it still exists (failure)
            if service_name in output:
                log_f.write(f"❌ Bridge domain instance {service_name} still exists on device\n")
                return False
            
            # If we get here, assume deletion was successful
            log_f.write(f"✅ Deletion verification successful for {device_info['hostname']}\n")
            return True
            
        except Exception as e:
            log_f.write(f"❌ Deletion verification error for {device_info['hostname']}: {e}\n")
            return False

    def deploy_config(self, config_name: str, dry_run: bool = False) -> Tuple[bool, List[str]]:
        """Deploy a configuration to devices using two-stage approach. Move to deployed if successful."""
        errors = []
        
        # Validate config first
        is_valid, validation_errors = self.validate_config(config_name)
        if not is_valid:
            return False, validation_errors
        
        # Load config
        config = self.load_config(config_name)
        if not config:
            return False, ["Configuration not found in pending directory"]
        
        if dry_run:
            print(f"🔍 DRY RUN: Would deploy {config_name} to {len(config)} devices")
            for device, commands in config.items():
                print(f"   📱 {device}: {len(commands)} commands")
            return True, []
        
        # Log deployment start
        deployment_log_file = self.logs_dir / f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        with open(deployment_log_file, 'w') as log_f:
            log_f.write(f"=== Two-Stage Deployment Log for {config_name} ===\n")
            log_f.write(f"Deployment started: {datetime.now().isoformat()}\n")
            log_f.write(f"Devices: {', '.join(config.keys())}\n\n")
            
            # Prepare CLI commands for each device
            _, _, device_commands = self.preview_cli_commands(config_name)
            
            # Extract service name for verification
            service_name = config_name.replace('bridge_domain_', '')
            
            # Stage 1: Commit-check on all devices in parallel
            log_f.write("=== STAGE 1: Commit-Check (Validation) ===\n")
            print(f"🔄 Stage 1: Validating configuration on {len(config)} devices...")
            print(f"   📋 Running commit-check in parallel...")
            
            check_results = {}
            check_errors = []
            configs_already_exist = []
            
            # Execute commit-check on all devices in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(config)) as executor:
                futures = {}
                for device in config.keys():
                    device_info = self._load_device_info(device)
                    if not device_info:
                        msg = f"Missing SSH info for {device}"
                        log_f.write(f"❌ {msg}\n")
                        check_errors.append(msg)
                        continue
                    
                    cli_commands = device_commands.get(device, [])
                    if not cli_commands:
                        msg = f"No CLI commands generated for {device}"
                        log_f.write(f"❌ {msg}\n")
                        check_errors.append(msg)
                        continue
                    
                    # Submit task for parallel execution
                    future = executor.submit(
                        self._execute_on_device_parallel,
                        device, device_info, cli_commands, log_f, "check"
                    )
                    futures[future] = device
                
                # Collect results as they complete
                completed_count = 0
                for future in concurrent.futures.as_completed(futures):
                    device_name, success, already_exists, error_message = future.result()
                    check_results[device_name] = (success, already_exists, error_message)
                    completed_count += 1
                    
                    if not success:
                        if error_message:
                            check_errors.append(f"Failed to validate on {device_name}: {error_message}")
                        else:
                            check_errors.append(f"Failed to validate on {device_name}")
                    elif already_exists:
                        configs_already_exist.append(device_name)
                    
                    # Show progress
                    print(f"   📊 Progress: {completed_count}/{len(config)} devices completed")
            
            # Check if any validation failed
            if check_errors:
                print(f"\n❌ Validation failed. Deployment aborted.")
                print(f"📋 Validation errors:")
                for err in check_errors:
                    print(f"   • {err}")
                print(f"📁 Deployment log saved to: {deployment_log_file}")
                return False, check_errors
            
            # Stage 2: Commit on all devices in parallel (only if all checks passed)
            log_f.write("\n=== STAGE 2: Commit (Actual Deployment) ===\n")
            print(f"\n🔄 Stage 2: Committing configuration on {len(config)} devices...")
            print(f"   📋 Running commit in parallel...")
            
            commit_results = {}
            commit_errors = []
            
            # Execute commit on all devices in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(config)) as executor:
                futures = {}
                for device in config.keys():
                    device_info = self._load_device_info(device)
                    cli_commands = device_commands.get(device, [])
                    
                    # Submit task for parallel execution
                    future = executor.submit(
                        self._execute_on_device_parallel,
                        device, device_info, cli_commands, log_f, "commit"
                    )
                    futures[future] = device
                
                # Collect results as they complete
                completed_count = 0
                for future in concurrent.futures.as_completed(futures):
                    device_name, success, already_exists, error_message = future.result()
                    commit_results[device_name] = (success, already_exists, error_message)
                    completed_count += 1
                    
                    if not success:
                        if error_message:
                            commit_errors.append(f"Failed to commit on {device_name}: {error_message}")
                        else:
                            commit_errors.append(f"Failed to commit on {device_name}")
                    
                    # Show progress
                    print(f"   📊 Progress: {completed_count}/{len(config)} devices completed")
            
            # Check if any commit failed
            if commit_errors:
                print(f"\n❌ Commit failed. Deployment failed.")
                print(f"📋 Commit errors:")
                for err in commit_errors:
                    print(f"   • {err}")
                print(f"📁 Deployment log saved to: {deployment_log_file}")
                return False, commit_errors
            
            # Stage 3: Verify deployment on all devices
            log_f.write("\n=== STAGE 3: Verification ===\n")
            print(f"\n🔍 Stage 3: Verifying deployment on {len(config)} devices...")
            print(f"   📋 Running verification in parallel...")
            
            verification_errors = []
            
            # Verify deployment on all devices in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(config)) as executor:
                futures = {}
                for device in config.keys():
                    device_info = self._load_device_info(device)
                    
                    # Submit verification task
                    future = executor.submit(
                        self._verify_config_deployment_parallel,
                        device, device_info, service_name, log_f
                    )
                    futures[future] = device
                
                # Collect verification results as they complete
                completed_count = 0
                for future in concurrent.futures.as_completed(futures):
                    device_name, success = future.result()
                    completed_count += 1
                    
                    if not success:
                        verification_errors.append(f"Configuration verification failed for {device_name}")
                    
                    # Show progress
                    print(f"   📊 Progress: {completed_count}/{len(config)} devices completed")
            
            if verification_errors:
                print(f"\n❌ Verification failed.")
                print(f"📋 Verification errors:")
                for err in verification_errors:
                    print(f"   • {err}")
                print(f"📁 Deployment log saved to: {deployment_log_file}")
                return False, verification_errors
            
            # Move to deployed if all stages succeeded
            source_path = self.pending_dir / f"{config_name}.yaml"
            dest_path = self.deployed_dir / f"{config_name}.yaml"
            try:
                shutil.move(str(source_path), str(dest_path))
                log_f.write("✅ Configuration deployment completed successfully\n")
                log_f.write(f"Configuration moved from pending to deployed: {dest_path}\n")
                
                # Provide user feedback
                if configs_already_exist:
                    print(f"✅ Configuration {config_name} deployed successfully!")
                    print(f"ℹ️  Some configurations already existed on devices: {', '.join(configs_already_exist)}")
                else:
                    print(f"✅ Configuration {config_name} deployed successfully!")
                
                print(f"📁 Configuration moved from pending to deployed")
                print(f"📁 Deployment log saved to: {deployment_log_file}")
                return True, []
            except Exception as e:
                error_msg = f"Failed to deploy {config_name}: {e}"
                errors.append(error_msg)
                log_f.write(f"❌ {error_msg}\n")
                return False, errors
    
    def remove_config(self, config_name: str, dry_run: bool = False) -> Tuple[bool, List[str]]:
        """Remove a deployed configuration using parallel execution."""
        # Load config from deployed directory
        config_path = self.deployed_dir / f"{config_name}.yaml"
        if not config_path.exists():
            return False, [f"Configuration {config_name} is not deployed"]
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            return False, [f"Error loading config {config_name}: {e}"]
        
        if dry_run:
            print(f"🔍 DRY RUN: Would remove {config_name} from {len(config)} devices")
            return True, []
        
        # Log deletion start
        deletion_log_file = self.logs_dir / f"{config_name}_deletion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        with open(deletion_log_file, 'w') as log_f:
            log_f.write(f"=== Parallel Deletion Log for {config_name} ===\n")
            log_f.write(f"Deletion started: {datetime.now().isoformat()}\n")
            log_f.write(f"Devices: {', '.join(config.keys())}\n\n")
            
            # Prepare deletion CLI commands for each device
            _, _, device_commands = self.preview_deletion_commands(config_name)
            
            # Extract service name for verification
            service_name = config_name.replace('bridge_domain_', '')
            
            # Execute deletion on all devices in parallel
            log_f.write("=== Parallel Deletion ===\n")
            print(f"🔄 Removing configuration from {len(config)} devices...")
            print(f"   📋 Running deletion in parallel...")
            
            deletion_errors = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(config)) as executor:
                futures = {}
                for device in config.keys():
                    device_info = self._load_device_info(device)
                    if not device_info:
                        msg = f"Missing SSH info for {device}"
                        log_f.write(f"❌ {msg}\n")
                        deletion_errors.append(msg)
                        continue
                    
                    cli_commands = device_commands.get(device, [])
                    if not cli_commands:
                        msg = f"No deletion commands generated for {device}"
                        log_f.write(f"❌ {msg}\n")
                        deletion_errors.append(msg)
                        continue
                    
                    # Submit deletion task for parallel execution
                    future = executor.submit(
                        self._execute_on_device_parallel,
                        device, device_info, cli_commands, log_f, "commit"
                    )
                    futures[future] = device
                
                # Collect deletion results as they complete
                completed_count = 0
                for future in concurrent.futures.as_completed(futures):
                    device_name, success, _, error_message = future.result()
                    completed_count += 1
                    
                    if not success:
                        if error_message:
                            deletion_errors.append(f"Failed to remove from {device_name}: {error_message}")
                        else:
                            deletion_errors.append(f"Failed to remove from {device_name}")
                    else:
                        log_f.write(f"✅ Removed config from {device_name}\n")
                    
                    # Show progress
                    print(f"   📊 Progress: {completed_count}/{len(config)} devices completed")
            
            if deletion_errors:
                print(f"\n❌ Deletion failed. Config remains in deployed.")
                print(f"📋 Deletion errors:")
                for err in deletion_errors:
                    print(f"   • {err}")
                print(f"📁 Deletion log saved to: {deletion_log_file}")
                return False, deletion_errors
            
            # Verify deletion on all devices in parallel
            log_f.write("\n=== Verification ===\n")
            print(f"\n🔍 Verifying deletion on {len(config)} devices...")
            print(f"   📋 Running verification in parallel...")
            
            verification_errors = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(config)) as executor:
                futures = {}
                for device in config.keys():
                    device_info = self._load_device_info(device)
                    
                    # Submit verification task
                    future = executor.submit(
                        self._verify_deletion_parallel,
                        device, device_info, service_name, log_f
                    )
                    futures[future] = device
                
                # Collect verification results as they complete
                completed_count = 0
                for future in concurrent.futures.as_completed(futures):
                    device_name, success = future.result()
                    completed_count += 1
                    
                    if not success:
                        verification_errors.append(f"Deletion verification failed for {device_name}")
                    
                    # Show progress
                    print(f"   📊 Progress: {completed_count}/{len(config)} devices completed")
            
            if verification_errors:
                print(f"\n❌ Deletion verification failed.")
                print(f"📋 Verification errors:")
                for err in verification_errors:
                    print(f"   • {err}")
                print(f"📁 Deletion log saved to: {deletion_log_file}")
                return False, verification_errors
            
            # Move the config file to the removed directory
            try:
                dest_path = self.removed_dir / f"{config_name}.yaml"
                shutil.move(str(config_path), str(dest_path))
                log_f.write("✅ Configuration moved to removed directory\n")
                log_f.write(f"Configuration file moved: {dest_path}\n")
                print(f"✅ Configuration {config_name} removed successfully")
                print(f"📁 Configuration file moved to removed")
                print(f"📁 Deletion log saved to: {deletion_log_file}")
                return True, []
            except Exception as e:
                error_msg = f"Failed to move {config_name} to removed: {e}"
                deletion_errors.append(error_msg)
                log_f.write(f"❌ {error_msg}\n")
                return False, deletion_errors
    
    def get_config_details(self, config_name: str) -> Optional[Dict]:
        """Get detailed information about a configuration."""
        # Check if config is in pending directory
        config = self.load_config(config_name)
        if config:
            details = {
                "name": config_name,
                "devices": list(config.keys()),
                "device_count": len(config),
                "vlan_id": self._extract_vlan_id(config),
                "status": "pending"
            }
            return details
        
        # Check if config is in deployed directory
        deployed_config_path = self.deployed_dir / f"{config_name}.yaml"
        if deployed_config_path.exists():
            try:
                with open(deployed_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                details = {
                    "name": config_name,
                    "devices": list(config.keys()),
                    "device_count": len(config),
                    "vlan_id": self._extract_vlan_id(config),
                    "status": "deployed",
                    "deployed_at": datetime.fromtimestamp(deployed_config_path.stat().st_mtime).isoformat()
                }
                
                return details
            except Exception as e:
                print(f"Error loading deployed config {config_name}: {e}")
        
        # Check if config is in removed directory
        removed_config_path = self.removed_dir / f"{config_name}.yaml"
        if removed_config_path.exists():
            try:
                with open(removed_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                details = {
                    "name": config_name,
                    "devices": list(config.keys()),
                    "device_count": len(config),
                    "vlan_id": self._extract_vlan_id(config),
                    "status": "removed",
                    "removed_at": datetime.fromtimestamp(removed_config_path.stat().st_mtime).isoformat()
                }
                
                return details
            except Exception as e:
                print(f"Error loading removed config {config_name}: {e}")
        
        return None
    
    def _extract_vlan_id(self, config: Dict) -> Optional[str]:
        """Extract VLAN ID from configuration."""
        for device_config in config.values():
            for command in device_config:
                if "vlan-id" in command:
                    # Extract VLAN ID from command like "vlan-id 253"
                    parts = command.split()
                    for i, part in enumerate(parts):
                        if part == "vlan-id" and i + 1 < len(parts):
                            return parts[i + 1]
        return None 