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
        """Get list of available configurations for deployment (pending configs) from database."""
        configs = []
        
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get all configurations with 'pending' status
            pending_configs = db_manager.get_configurations_by_status('pending')
            
            for config_record in pending_configs:
                config_info = {
                    "name": config_record['service_name'],
                    "path": f"database://{config_record['service_name']}",
                    "type": config_record.get('config_type', 'bridge_domain'),
                    "status": config_record['status'],
                    "created": config_record['created_at'],
                    "vlan_id": config_record.get('vlan_id')
                }
                configs.append(config_info)
            
        except Exception as e:
            print(f"Error loading available configs from database: {e}")
        
        return configs
    
    def get_deployed_configs(self) -> List[Dict]:
        """Get list of currently deployed configurations from database."""
        deployed_configs = []
        
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get all configurations with 'deployed' status
            deployed_db_configs = db_manager.get_configurations_by_status('deployed')
            
            for config_record in deployed_db_configs:
                config_info = {
                    "name": config_record['service_name'],
                    "path": f"database://{config_record['service_name']}",
                    "type": config_record.get('config_type', 'bridge_domain'),
                    "status": config_record['status'],
                    "deployed_at": config_record['deployed_at'],
                    "vlan_id": config_record.get('vlan_id')
                }
                deployed_configs.append(config_info)
            
        except Exception as e:
            print(f"Error loading deployed configs from database: {e}")
        
        return deployed_configs
    
    def get_removed_configs(self) -> List[Dict]:
        """Get list of removed configurations that can be restored from database."""
        removed_configs = []
        
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get all configurations with 'deleted' status
            deleted_db_configs = db_manager.get_configurations_by_status('deleted')
            
            for config_record in deleted_db_configs:
                config_info = {
                    "name": config_record['service_name'],
                    "path": f"database://{config_record['service_name']}",
                    "type": config_record.get('config_type', 'bridge_domain'),
                    "status": config_record['status'],
                    "deleted_at": config_record.get('deployed_at'),  # Using deployed_at as deleted_at
                    "vlan_id": config_record.get('vlan_id')
                }
                removed_configs.append(config_info)
            
        except Exception as e:
            print(f"Error loading removed configs from database: {e}")
        
        return removed_configs
    
    def restore_config(self, config_name: str) -> Tuple[bool, List[str]]:
        """
        Restore a removed configuration to pending for redeployment from database.
        
        Args:
            config_name: Name of the configuration to restore
            
        Returns:
            Tuple of (success, errors)
        """
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get the configuration from database
            config_record = db_manager.get_configuration_by_service_name(config_name)
            
            if not config_record:
                return False, [f"Configuration {config_name} not found in database"]
            
            if config_record['status'] != 'deleted':
                return False, [f"Configuration {config_name} is not in 'deleted' status (current: {config_record['status']})"]
            
            # Check if there's already a pending configuration with the same name
            pending_configs = db_manager.get_configurations_by_status('pending')
            for pending_config in pending_configs:
                if pending_config['service_name'] == config_name:
                    return False, [f"Configuration {config_name} already exists in pending status"]
            
            # Check if there's already a deployed configuration with the same name
            deployed_configs = db_manager.get_configurations_by_status('deployed')
            for deployed_config in deployed_configs:
                if deployed_config['service_name'] == config_name:
                    return False, [f"Configuration {config_name} already exists in deployed status"]
            
            # Update the configuration status to 'pending'
            try:
                import sqlite3
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE configurations 
                    SET status = 'pending', deployed_at = NULL, deployed_by = NULL
                    WHERE service_name = ?
                """, (config_name,))
                
                conn.commit()
                conn.close()
                
                print(f"✅ Configuration {config_name} restored to pending")
                print(f"📁 Configuration status updated in database")
                return True, []
                
            except Exception as e:
                return False, [f"Failed to restore {config_name}: {e}"]
                
        except Exception as e:
            error_msg = f"Failed to restore {config_name}: {e}"
            return False, [error_msg]
    
    def load_config(self, config_name: str) -> Optional[Dict]:
        """Load a configuration from the database by service name."""
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get configuration from database
            config_record = db_manager.get_configuration_by_service_name(config_name)
            
            if not config_record:
                print(f"Configuration {config_name} not found in database")
                return None
            
            # Parse the config_data JSON string
            if config_record.get('config_data'):
                try:
                    config_data = json.loads(config_record['config_data'])
                    return config_data
                except json.JSONDecodeError as e:
                    print(f"Error parsing config data for {config_name}: {e}")
                    return None
            else:
                print(f"No config data found for {config_name}")
                return None
                
        except Exception as e:
            print(f"Error loading config {config_name} from database: {e}")
            return None
    
    def validate_config(self, config_name: str) -> Tuple[bool, List[str]]:
        """Validate a configuration before deployment."""
        errors = []
        
        # Load config
        config = self.load_config(config_name)
        if not config:
            errors.append(f"Configuration {config_name} not found in database")
            return False, errors
        
        # Basic structure validation
        if not isinstance(config, dict):
            errors.append("Configuration must be a dictionary")
            return False, errors
        
        # Check for required devices (exclude _metadata)
        actual_devices = {k: v for k, v in config.items() if k != '_metadata'}
        if not actual_devices:
            errors.append("Configuration is empty (no actual devices)")
            return False, errors
        
        # Validate each device configuration
        for device_name, device_config in actual_devices.items():
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
            errors.append(f"Configuration {config_name} not found in database")
            return False, errors, device_commands
        
        # Convert YAML config to CLI commands for each device (exclude _metadata)
        for device_name, device_config in config.items():
            # Skip _metadata - it's not a real device
            if device_name == '_metadata':
                continue
                
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
        
        # Load config from database
        config = self.load_config(config_name)
        if not config:
            errors.append(f"Configuration {config_name} not found in database")
            return False, errors, device_commands
        
        # Convert database config to deletion CLI commands for each device (exclude _metadata)
        for device_name, device_config in config.items():
            # Skip _metadata - it's not a real device
            if device_name == '_metadata':
                continue
                
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
                cli_commands.append(f"no interfaces {interface}")
            
            # Remove bridge domain instances
            for instance in sorted(bridge_domain_instances):
                cli_commands.append(f"no network-services bridge-domain instance {instance}")
            
            # End with commit
            cli_commands.append("commit")
            
            device_commands[device_name] = cli_commands
        
        return True, errors, device_commands

    def _load_device_info(self, device_name: str) -> Optional[dict]:
        """Load SSH connection info for a device from devices.yaml."""
        devices_file = Path(__file__).parent.parent / "devices.yaml"
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
        
        # Handle consolidated superspine names (e.g., DNAAS-SUPERSPINE-D04 -> DNAAS-SuperSpine-D04-NCC0)
        if not device_data and 'SUPERSPINE' in device_name.upper():
            # Try to find NCC variants
            base_name = device_name.replace('SUPERSPINE', 'SuperSpine')
            for variant in ['-NCC0', '-NCC1']:
                variant_name = base_name + variant
                if variant_name in devices_data:
                    device_data = devices_data[variant_name]
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
            
            # Check for "already exists" patterns in the output
            # For DriveNets devices, we need to look for multiple patterns
            already_exists_patterns = [
                "no configuration changes were made",
                "no changes to commit",
                "configuration already exists",
                "already configured",
                "no modifications"
            ]
            
            already_exists = any(pattern.lower() in output.lower() for pattern in already_exists_patterns)
            
            # Additional check: if this is a commit check stage and it passes without errors,
            # but we don't see "already exists" patterns, assume it doesn't exist
            if stage == "check" and not already_exists:
                # For commit check, if it passes without "already exists" patterns, 
                # the configuration likely doesn't exist yet
                already_exists = False
                log_f.write(f"🔍 Commit check passed - configuration does not appear to exist yet\n")
            
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
            log_f.write(f"Complete SSH output for {device_info['hostname']}\n")
            
            # NEW APPROACH: For DriveNets devices, we need to be smarter about detecting "already exists"
            # Instead of looking for specific text patterns, we'll use a different strategy
            
            if stage == "check":
                # For commit check stage:
                # 1) If errors are present, treat as failure upstream
                # 2) If no errors: ONLY mark 'already_exists' when explicit 'no changes' verbiage is present
                
                # Look for error patterns first
                error_patterns = [
                    'Error:', 'ERROR:', 'Invalid', 'INVALID', 'Failed', 'FAILED',
                    'not found', 'NOT FOUND', 'does not exist', 'DOES NOT EXIST',
                    'syntax error', 'SYNTAX ERROR', 'command not found', 'COMMAND NOT FOUND',
                    'permission denied', 'PERMISSION DENIED', 'access denied', 'ACCESS DENIED'
                ]
                
                has_errors = any(pattern.lower() in output.lower() for pattern in error_patterns)
                
                if has_errors:
                    already_exists = False
                    log_f.write(f"❌ Commit-check detected errors (treat as not-existing)\n")
                else:
                    # Explicit 'no change' patterns only
                    explicit_no_change_patterns = [
                        'no configuration changes were made',
                        'no configuration changes',
                        'no changes to commit',
                        'nothing to commit',
                        'configuration already exists'
                    ]
                    already_exists = any(pat in output.lower() for pat in explicit_no_change_patterns)
                    if already_exists:
                        log_f.write(f"✅ Commit-check indicates no changes needed (already exists)\n")
                    else:
                        # Passed commit-check without explicit 'no change' text → treat as new/changed
                        already_exists = False
                        log_f.write(f"✅ Commit-check passed (new or changed configuration detected)\n")
            else:
                # For commit stage, we don't check for 'already exists' patterns; only success/failure matters
                already_exists = False
                log_f.write(f"🔍 Commit stage - not checking for 'already exists' patterns\n")
            
            if already_exists:
                log_f.write(f"✅ Configuration already exists on device\n")
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
                        # For commit-check stage, passing successfully means the configuration is valid
                        # but doesn't necessarily mean it already exists
                        if stage == "check":
                            log_f.write(f"✅ Commit check passed successfully - configuration is valid\n")
                            # Return already_exists=False since we can't determine if it exists from commit check
                            return True, False, None
                        else:
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
            # Handle None log_f by creating a dummy log file
            if log_f is None:
                class DummyLogFile:
                    def write(self, text):
                        pass  # Silently ignore log writes
                log_f = DummyLogFile()
            
            log_f.write(f"🔄 Starting {stage.upper()} on {device} ({device_info['hostname']})...\n")
            ok, already_exists, error_message = self._ssh_push_commands_two_stage(device_info, cli_commands, log_f, stage)
            
            # Debug logging to see what's being returned
            log_f.write(f"🔍 DEBUG: _ssh_push_commands_two_stage returned: ok={ok}, already_exists={already_exists}, error_message={error_message}\n")
            
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
            # Handle None log_f by creating a dummy log file
            if log_f is None:
                class DummyLogFile:
                    def write(self, text):
                        pass  # Silently ignore log writes
                log_f = DummyLogFile()
            
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
            # Handle None log_f by creating a dummy log file
            if log_f is None:
                class DummyLogFile:
                    def write(self, text):
                        pass  # Silently ignore log writes
                log_f = DummyLogFile()
            
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
            # Handle None log_f by creating a dummy log file
            if log_f is None:
                class DummyLogFile:
                    def write(self, text):
                        pass  # Silently ignore log writes
                log_f = DummyLogFile()
            
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
            
            # Check for "Unknown word" error - this indicates the configuration doesn't exist
            if "ERROR: Unknown word:" in output and service_name in output:
                config_exists = False
                print(f"   ❌ Not found (Unknown word error indicates no configuration)")
                log_f.write(f"Configuration check: ❌ Not found (Unknown word error indicates no configuration)\n")
            
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
            # Handle None log_f by creating a dummy log file
            if log_f is None:
                class DummyLogFile:
                    def write(self, text):
                        pass  # Silently ignore log writes
                log_f = DummyLogFile()
            
            print(f"🔍 Verifying deletion on {device_info['hostname']} for configuration '{service_name}'...")
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
            
            # Check if configuration still exists (should be False for successful deletion)
            config_still_exists = service_name in output
            
            # Check for "Unknown word" error - this indicates the configuration was successfully deleted
            if "ERROR: Unknown word:" in output and service_name in output:
                config_still_exists = False
                print(f"   ✅ Successfully deleted (Unknown word error indicates deletion)")
                log_f.write(f"Deletion check: ✅ Successfully deleted (Unknown word error indicates deletion)\n")
            else:
                print(f"   {'❌ Still exists' if config_still_exists else '✅ Successfully deleted'}")
                log_f.write(f"Deletion check: {'❌ Still exists' if config_still_exists else '✅ Successfully deleted'}\n")
            
            log_f.write(f"Command output: {output}\n")
            
            # Additional check for bridge domain format
            if not config_still_exists and "Bridge-Domain:" in output:
                # Check if the service name appears after "Bridge-Domain:"
                bridge_domain_line = [line for line in output.split('\n') if line.strip().startswith('Bridge-Domain:')]
                if bridge_domain_line and service_name in bridge_domain_line[0]:
                    config_still_exists = True
                    print(f"   ❌ Still exists (in Bridge-Domain format)")
                    log_f.write(f"Still exists in Bridge-Domain format: {bridge_domain_line[0]}\n")
            
            if not config_still_exists:
                print(f"   ✅ Deletion verification successful for {device_info['hostname']}")
                log_f.write(f"✅ Deletion verification successful for {device_info['hostname']}\n")
            else:
                print(f"   ❌ Deletion verification failed for {device_info['hostname']}")
                log_f.write(f"❌ Deletion verification failed for {device_info['hostname']}\n")
            
            return not config_still_exists
            
        except Exception as e:
            print(f"   ❌ SSH Error: {e}")
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
            return False, ["Configuration not found in database"]
        
        if dry_run:
            actual_devices = [device for device in config.keys() if device != '_metadata']
            print(f"🔍 DRY RUN: Would deploy {config_name} to {len(actual_devices)} devices")
            for device, commands in config.items():
                if device != '_metadata':
                    print(f"   📱 {device}: {len(commands)} commands")
            return True, []
        
        # Log deployment start
        deployment_log_file = self.logs_dir / f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        with open(deployment_log_file, 'w') as log_f:
            log_f.write(f"=== Two-Stage Deployment Log for {config_name} ===\n")
            log_f.write(f"Deployment started: {datetime.now().isoformat()}\n")
            # Filter out _metadata key - only process actual devices
            actual_devices = [device for device in config.keys() if device != '_metadata']
            log_f.write(f"Devices: {', '.join(actual_devices)}\n\n")
            
            # Prepare CLI commands for each device
            _, _, device_commands = self.preview_cli_commands(config_name)
            
            # Extract service name for verification from the actual configuration
            service_name = None
            for device_config in config.values():
                for command in device_config:
                    if "network-services bridge-domain instance" in command:
                        parts = command.split()
                        if len(parts) >= 4:
                            service_name = parts[3]  # Extract the actual service name
                            break
                if service_name:
                    break
            
            if not service_name:
                # Fallback to the old method if service name not found in config
                service_name = config_name.replace('bridge_domain_', '')
            
            # Stage 1: Commit-check on all devices in parallel
            log_f.write("=== STAGE 1: Commit-Check (Validation) ===\n")
            print(f"🔄 Stage 1: Validating configuration on {len(actual_devices)} devices...")
            print(f"   📋 Running commit-check in parallel...")
            
            check_results = {}
            check_errors = []
            configs_already_exist = []
            
            # Execute commit-check on all devices in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(actual_devices)) as executor:
                futures = {}
                for device in actual_devices:
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
                    print(f"   📊 Progress: {completed_count}/{len(actual_devices)} devices completed")
            
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
            print(f"\n🔄 Stage 2: Committing configuration on {len(actual_devices)} devices...")
            print(f"   📋 Running commit in parallel...")
            
            commit_results = {}
            commit_errors = []
            
            # Execute commit on all devices in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(actual_devices)) as executor:
                futures = {}
                for device in actual_devices:
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
                    print(f"   📊 Progress: {completed_count}/{len(actual_devices)} devices completed")
            
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
            print(f"\n🔍 Stage 3: Verifying deployment on {len(actual_devices)} devices...")
            print(f"   📋 Running verification in parallel...")
            
            verification_errors = []
            
            # Verify deployment on all devices in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(actual_devices)) as executor:
                futures = {}
                for device in actual_devices:
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
                    print(f"   📊 Progress: {completed_count}/{len(actual_devices)} devices completed")
            
            if verification_errors:
                print(f"\n❌ Verification failed.")
                print(f"📋 Verification errors:")
                for err in verification_errors:
                    print(f"   • {err}")
                print(f"📁 Deployment log saved to: {deployment_log_file}")
                return False, verification_errors
            
            # Update database status to deployed if all stages succeeded
            try:
                # Import database manager
                from database_manager import DatabaseManager
                
                # Initialize database manager with correct path
                db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
                db_manager = DatabaseManager(str(db_path))
                
                # Update configuration status to 'deployed'
                import sqlite3
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE configurations 
                    SET status = 'deployed', deployed_at = ?, deployed_by = ?
                    WHERE service_name = ?
                """, (datetime.utcnow().isoformat(), 1, config_name))  # Using user_id = 1 for CLI operations
                
                conn.commit()
                conn.close()
                
                log_f.write("✅ Configuration deployment completed successfully\n")
                log_f.write(f"Configuration status updated to 'deployed' in database\n")
                
                # Provide user feedback
                if configs_already_exist:
                    print(f"✅ Configuration {config_name} deployed successfully!")
                    print(f"ℹ️  Some configurations already existed on devices: {', '.join(configs_already_exist)}")
                else:
                    print(f"✅ Configuration {config_name} deployed successfully!")
                
                print(f"📁 Configuration status updated to 'deployed' in database")
                print(f"📁 Deployment log saved to: {deployment_log_file}")
                return True, []
            except Exception as e:
                error_msg = f"Failed to deploy {config_name}: {e}"
                errors.append(error_msg)
                log_f.write(f"❌ {error_msg}\n")
                return False, errors
    
    def remove_config(self, config_name: str, dry_run: bool = False, progress_callback=None) -> Tuple[bool, List[str]]:
        """Remove a deployed configuration using parallel execution with optional progress tracking."""
        # Load config from database
        config = self.load_config(config_name)
        if not config:
            return False, [f"Configuration {config_name} not found in database"]
        
        if dry_run:
            actual_devices = [device for device in config.keys() if device != '_metadata']
            print(f"🔍 DRY RUN: Would remove {config_name} from {len(actual_devices)} devices")
            return True, []
        
        # Log removal start
        if progress_callback:
            progress_callback("🗑️ Starting configuration removal...")
        
        deletion_log_file = self.logs_dir / f"{config_name}_deletion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        with open(deletion_log_file, 'w') as log_f:
            log_f.write(f"=== Parallel Deletion Log for {config_name} ===\n")
            log_f.write(f"Deletion started: {datetime.now().isoformat()}\n")
            # Filter out _metadata key - only process actual devices
            actual_devices = [device for device in config.keys() if device != '_metadata']
            log_f.write(f"Devices: {', '.join(actual_devices)}\n\n")
            
            # Prepare deletion CLI commands for each device
            _, _, device_commands = self.preview_deletion_commands(config_name)
            
            # Extract service name for verification
            service_name = config_name.replace('bridge_domain_', '')
            
            # Execute deletion on all devices in parallel
            log_f.write("=== Parallel Deletion ===\n")
            if progress_callback:
                progress_callback(f"🔄 Removing configuration from {len(actual_devices)} devices...")
            print(f"🔄 Removing configuration from {len(actual_devices)} devices...")
            print(f"   📋 Running deletion in parallel...")
            
            deletion_errors = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(actual_devices)) as executor:
                futures = {}
                for device in actual_devices:
                    device_info = self._load_device_info(device)
                    if not device_info:
                        msg = f"Missing SSH info for {device}"
                        log_f.write(f"❌ {msg}\n")
                        deletion_errors.append(msg)
                        if progress_callback:
                            progress_callback(f"❌ {msg}")
                        continue
                    
                    cli_commands = device_commands.get(device, [])
                    if not cli_commands:
                        msg = f"No deletion commands generated for {device}"
                        log_f.write(f"❌ {msg}\n")
                        deletion_errors.append(msg)
                        if progress_callback:
                            progress_callback(f"❌ {msg}")
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
                            error_msg = f"Failed to remove from {device_name}: {error_message}"
                            deletion_errors.append(error_msg)
                            if progress_callback:
                                progress_callback(f"❌ {error_msg}")
                        else:
                            error_msg = f"Failed to remove from {device_name}"
                            deletion_errors.append(error_msg)
                            if progress_callback:
                                progress_callback(f"❌ {error_msg}")
                    else:
                        log_f.write(f"✅ Removed config from {device_name}\n")
                        if progress_callback:
                            progress_callback(f"✅ {device_name}: Configuration removed successfully")
                    
                    # Show progress
                    print(f"   📊 Progress: {completed_count}/{len(actual_devices)} devices completed")
                    if progress_callback:
                        progress_callback(f"📊 Progress: {completed_count}/{len(actual_devices)} devices completed")
            
            if deletion_errors:
                if progress_callback:
                    progress_callback("❌ Removal failed")
                print(f"\n❌ Deletion failed. Config remains in deployed.")
                print(f"📋 Deletion errors:")
                for err in deletion_errors:
                    print(f"   • {err}")
                print(f"📁 Deletion log saved to: {deletion_log_file}")
                return False, deletion_errors
            
            # Verify deletion on all devices in parallel
            log_f.write("\n=== Verification ===\n")
            if progress_callback:
                progress_callback("🔍 Verifying deletion...")
            print(f"\n🔍 Verifying deletion on {len(actual_devices)} devices...")
            print(f"   📋 Running verification in parallel...")
            
            verification_errors = []
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(actual_devices)) as executor:
                futures = {}
                for device in actual_devices:
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
                        error_msg = f"Deletion verification failed for {device_name}"
                        verification_errors.append(error_msg)
                        if progress_callback:
                            progress_callback(f"❌ {error_msg}")
                    else:
                        if progress_callback:
                            progress_callback(f"✅ {device_name}: Removal verified")
                    
                    # Show progress
                    print(f"   📊 Progress: {completed_count}/{len(actual_devices)} devices completed")
                    if progress_callback:
                        progress_callback(f"📊 Verification Progress: {completed_count}/{len(actual_devices)} devices completed")
            
            if verification_errors:
                if progress_callback:
                    progress_callback("❌ Deletion verification failed")
                print(f"\n❌ Deletion verification failed.")
                print(f"📋 Verification errors:")
                for err in verification_errors:
                    print(f"   • {err}")
                print(f"📁 Deletion log saved to: {deletion_log_file}")
                return False, verification_errors
            
            # Update database status to removed if all stages succeeded
            try:
                # Import database manager
                from database_manager import DatabaseManager
                
                # Initialize database manager with correct path
                db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
                db_manager = DatabaseManager(str(db_path))
                
                # Update configuration status to 'removed'
                import sqlite3
                conn = sqlite3.connect(db_manager.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE configurations 
                    SET status = 'deleted', deployed_at = NULL, deployed_by = NULL
                    WHERE service_name = ?
                """, (config_name,))
                
                conn.commit()
                conn.close()
                
                log_f.write("✅ Configuration status updated to 'deleted' in database\n")
                if progress_callback:
                    progress_callback("✅ Database status updated to 'deleted'")
                print(f"✅ Configuration {config_name} deleted successfully")
                print(f"📁 Configuration status updated to 'deleted' in database")
                print(f"📁 Deletion log saved to: {deletion_log_file}")
                return True, []
            except Exception as e:
                error_msg = f"Failed to remove {config_name}: {e}"
                deletion_errors.append(error_msg)
                log_f.write(f"❌ {error_msg}\n")
                if progress_callback:
                    progress_callback(f"❌ {error_msg}")
                return False, deletion_errors
    
    def get_config_details(self, config_name: str) -> Optional[Dict]:
        """Get detailed information about a configuration from the database."""
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get configuration from database
            config_record = db_manager.get_configuration_by_service_name(config_name)
            
            if not config_record:
                return None
            
            # Parse the config_data JSON string
            config_data = None
            if config_record.get('config_data'):
                try:
                    config_data = json.loads(config_record['config_data'])
                except json.JSONDecodeError as e:
                    print(f"Error parsing config data for {config_name}: {e}")
                    return None
            
            if not config_data:
                return None
            
            # Filter out _metadata from devices
            actual_devices = {k: v for k, v in config_data.items() if k != '_metadata'}
            
            details = {
                "name": config_name,
                "devices": list(actual_devices.keys()),
                "device_count": len(actual_devices),
                "vlan_id": self._extract_vlan_id(config_data),
                "status": config_record.get('status', 'unknown'),
                "created_at": config_record.get('created_at'),
                "deployed_at": config_record.get('deployed_at'),
                "deployed_by": config_record.get('deployed_by')
            }
            
            return details
                
        except Exception as e:
            print(f"Error getting config details for {config_name}: {e}")
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