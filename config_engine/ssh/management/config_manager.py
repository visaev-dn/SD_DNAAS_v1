#!/usr/bin/env python3
"""
SSH Configuration Manager
Handles SSH configuration push, validation, and management operations
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from core.logging import get_logger
from core.exceptions import BusinessLogicError, ValidationError, ConfigurationError
from ..base_ssh_manager import (
    SSHConnectionConfig, SSHConfigPushResult, SSHCommandResult
)
from ..connection.connection_manager import ConnectionManager, SSHConnection
from ..execution.command_executor import CommandExecutor


@dataclass
class ConfigurationFile:
    """Configuration file information"""
    name: str
    path: str
    device_name: str
    config_type: str
    status: str
    created_at: str
    deployed_at: Optional[str] = None
    removed_at: Optional[str] = None
    vlan_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConfigurationValidation:
    """Configuration validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validation_time: str
    validator_version: str


class ConfigurationManager:
    """
    Manages SSH configuration operations including push, validation, and removal.
    """
    
    def __init__(self, config_dir: str = "configs", logs_dir: str = "logs"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
            logs_dir: Directory for operation logs
        """
        self.config_dir = Path(config_dir)
        self.logs_dir = Path(logs_dir)
        self.logger = get_logger(__name__)
        
        # Ensure directories exist
        self._create_directories()
        
        # Initialize components
        self.connection_manager = ConnectionManager()
        self.command_executor = CommandExecutor()
        
        # Configuration tracking
        self.configs: Dict[str, ConfigurationFile] = {}
        self.config_lock = threading.Lock()
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Load existing configurations
        self._load_existing_configs()
        
        self.logger.info(f"Configuration Manager initialized with config_dir: {config_dir}")
    
    def _create_directories(self) -> None:
        """Create the configuration directory structure."""
        directories = [
            self.config_dir,
            self.config_dir / "pending",
            self.config_dir / "deployed",
            self.config_dir / "removed",
            self.config_dir / "deployment_logs",
            self.logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_existing_configs(self) -> None:
        """Load existing configuration files from disk."""
        try:
            # Load from pending directory
            pending_dir = self.config_dir / "pending"
            for config_file in pending_dir.glob("*.yaml"):
                self._load_config_file(config_file, "pending")
            
            # Load from deployed directory
            deployed_dir = self.config_dir / "deployed"
            for config_file in deployed_dir.glob("*.yaml"):
                self._load_config_file(config_file, "deployed")
            
            # Load from removed directory
            removed_dir = self.config_dir / "removed"
            for config_file in removed_dir.glob("*.yaml"):
                self._load_config_file(config_file, "removed")
                
        except Exception as e:
            self.logger.error(f"Error loading existing configs: {e}")
    
    def _load_config_file(self, config_file: Path, status: str) -> None:
        """Load configuration file into memory."""
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            config = ConfigurationFile(
                name=config_data.get("name", config_file.stem),
                path=str(config_file),
                device_name=config_data.get("device_name", "unknown"),
                config_type=config_data.get("config_type", "unknown"),
                status=status,
                created_at=config_data.get("created_at", datetime.now().isoformat()),
                deployed_at=config_data.get("deployed_at"),
                removed_at=config_data.get("removed_at"),
                vlan_id=config_data.get("vlan_id"),
                metadata=config_data.get("metadata", {})
            )
            
            self.configs[config.name] = config
            
        except Exception as e:
            self.logger.error(f"Error loading config file {config_file}: {e}")
    
    def get_available_configs(self) -> List[Dict[str, Any]]:
        """
        Get list of available configurations for deployment.
        
        Returns:
            List of configuration dictionaries
        """
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent.parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get all configurations with 'pending' status
            pending_configs = db_manager.get_configurations_by_status('pending')
            
            configs = []
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
            
            return configs
            
        except Exception as e:
            self.logger.error(f"Error loading available configs from database: {e}")
            return []
    
    def get_deployed_configs(self) -> List[Dict[str, Any]]:
        """
        Get list of currently deployed configurations.
        
        Returns:
            List of configuration dictionaries
        """
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent.parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get all configurations with 'deployed' status
            deployed_db_configs = db_manager.get_configurations_by_status('deployed')
            
            deployed_configs = []
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
            
            return deployed_configs
            
        except Exception as e:
            self.logger.error(f"Error loading deployed configs from database: {e}")
            return []
    
    def get_removed_configs(self) -> List[Dict[str, Any]]:
        """
        Get list of removed configurations.
        
        Returns:
            List of configuration dictionaries
        """
        try:
            # Import database manager
            from database_manager import DatabaseManager
            
            # Initialize database manager with correct path
            db_path = Path(__file__).parent.parent.parent.parent / "instance" / "lab_automation.db"
            db_manager = DatabaseManager(str(db_path))
            
            # Get all configurations with 'removed' status
            removed_db_configs = db_manager.get_configurations_by_status('removed')
            
            removed_configs = []
            for config_record in removed_db_configs:
                config_info = {
                    "name": config_record['service_name'],
                    "path": f"database://{config_record['service_name']}",
                    "deleted_at": config_record['deleted_at'],
                    "vlan_id": config_record.get('vlan_id')
                }
                removed_configs.append(config_info)
            
            return removed_configs
            
        except Exception as e:
            self.logger.error(f"Error loading removed configs from database: {e}")
            return []
    
    def push_configuration(self, device_name: str, config_lines: List[str], 
                          connection_config: SSHConnectionConfig) -> SSHConfigPushResult:
        """
        Push configuration to a device.
        
        Args:
            device_name: Name of the device to push configuration to
            config_lines: List of configuration lines to push
            connection_config: SSH connection configuration
            
        Returns:
            SSHConfigPushResult with push status and details
        """
        try:
            self.logger.info(f"Pushing configuration to {device_name}")
            
            # Validate connection configuration
            is_valid, errors = self.connection_manager.validate_connection_config(connection_config)
            if not is_valid:
                return SSHConfigPushResult(
                    success=False,
                    device_name=device_name,
                    error_message=f"Invalid connection configuration: {'; '.join(errors)}"
                )
            
            # Create or get connection
            connection = self.connection_manager.create_connection(device_name, connection_config)
            if not connection:
                return SSHConfigPushResult(
                    success=False,
                    device_name=device_name,
                    error_message="Failed to establish SSH connection"
                )
            
            # Enter configuration mode
            config_commands = self._get_config_mode_commands(connection_config.device_type)
            if config_commands:
                for cmd in config_commands:
                    result = self.command_executor.execute_command(connection, cmd)
                    if not result.success:
                        return SSHConfigPushResult(
                            success=False,
                            device_name=device_name,
                            error_message=f"Failed to enter config mode: {result.error}"
                        )
            
            # Push configuration lines
            commands_executed = []
            for line in config_lines:
                if line.strip() and not line.strip().startswith('!'):
                    result = self.command_executor.execute_command(connection, line)
                    commands_executed.append(line)
                    
                    if not result.success:
                        return SSHConfigPushResult(
                            success=False,
                            device_name=device_name,
                            error_message=f"Failed to push config line: {line} - {result.error}",
                            commands_executed=commands_executed
                        )
            
            # Exit configuration mode
            exit_commands = self._get_exit_config_commands(connection_config.device_type)
            if exit_commands:
                for cmd in exit_commands:
                    result = self.command_executor.execute_command(connection, cmd)
                    if not result.success:
                        self.logger.warning(f"Failed to exit config mode: {result.error}")
            
            # Validate configuration
            validation_result = self._validate_deployed_config(connection, device_name)
            
            return SSHConfigPushResult(
                success=True,
                device_name=device_name,
                config_changes={"lines_pushed": len(config_lines)},
                commands_executed=commands_executed,
                validation_results=validation_result
            )
            
        except Exception as e:
            self.logger.error(f"Error pushing configuration to {device_name}: {e}")
            return SSHConfigPushResult(
                success=False,
                device_name=device_name,
                error_message=str(e)
            )
    
    def remove_configuration(self, device_name: str, config_lines: List[str], 
                           connection_config: SSHConnectionConfig) -> SSHConfigPushResult:
        """
        Remove configuration from a device.
        
        Args:
            device_name: Name of the device to remove configuration from
            config_lines: List of configuration lines to remove
            connection_config: SSH connection configuration
            
        Returns:
            SSHConfigPushResult with removal status and details
        """
        try:
            self.logger.info(f"Removing configuration from {device_name}")
            
            # Create or get connection
            connection = self.connection_manager.create_connection(device_name, connection_config)
            if not connection:
                return SSHConfigPushResult(
                    success=False,
                    device_name=device_name,
                    error_message="Failed to establish SSH connection"
                )
            
            # Enter configuration mode
            config_commands = self._get_config_mode_commands(connection_config.device_type)
            if config_commands:
                for cmd in config_commands:
                    result = self.command_executor.execute_command(connection, cmd)
                    if not result.success:
                        return SSHConfigPushResult(
                            success=False,
                            device_name=device_name,
                            error_message=f"Failed to enter config mode: {result.error}"
                        )
            
            # Remove configuration lines
            commands_executed = []
            for line in config_lines:
                if line.strip() and not line.strip().startswith('!'):
                    # Convert add commands to remove commands
                    remove_line = self._convert_to_remove_command(line, connection_config.device_type)
                    if remove_line:
                        result = self.command_executor.execute_command(connection, remove_line)
                        commands_executed.append(remove_line)
                        
                        if not result.success:
                            return SSHConfigPushResult(
                                success=False,
                                device_name=device_name,
                                error_message=f"Failed to remove config line: {line} - {result.error}",
                                commands_executed=commands_executed
                            )
            
            # Exit configuration mode
            exit_commands = self._get_exit_config_commands(connection_config.device_type)
            if exit_commands:
                for cmd in exit_commands:
                    result = self.command_executor.execute_command(connection, cmd)
                    if not result.success:
                        self.logger.warning(f"Failed to exit config mode: {result.error}")
            
            return SSHConfigPushResult(
                success=True,
                device_name=device_name,
                config_changes={"lines_removed": len(config_lines)},
                commands_executed=commands_executed
            )
            
        except Exception as e:
            self.logger.error(f"Error removing configuration from {device_name}: {e}")
            return SSHConfigPushResult(
                success=False,
                device_name=device_name,
                error_message=str(e)
            )
    
    def validate_configuration(self, device_name: str, config_lines: List[str], 
                             connection_config: SSHConnectionConfig) -> ConfigurationValidation:
        """
        Validate configuration before deployment.
        
        Args:
            device_name: Name of the device to validate configuration for
            config_lines: List of configuration lines to validate
            connection_config: SSH connection configuration
            
        Returns:
            ConfigurationValidation with validation results
        """
        errors = []
        warnings = []
        
        try:
            # Basic syntax validation
            for i, line in enumerate(config_lines, 1):
                if line.strip() and not line.strip().startswith('!'):
                    # Check for common syntax issues
                    if line.count('{') != line.count('}'):
                        errors.append(f"Line {i}: Mismatched braces in '{line}'")
                    
                    if line.count('(') != line.count(')'):
                        errors.append(f"Line {i}: Mismatched parentheses in '{line}'")
                    
                    # Check for missing semicolons (Cisco)
                    if connection_config.device_type in ["cisco", "arista"]:
                        if not line.strip().endswith(';') and not line.strip().endswith('}'):
                            warnings.append(f"Line {i}: Missing semicolon in '{line}'")
            
            # Device-specific validation
            device_errors = self._validate_device_specific_config(config_lines, connection_config.device_type)
            errors.extend(device_errors)
            
            is_valid = len(errors) == 0
            
            return ConfigurationValidation(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                validation_time=datetime.now().isoformat(),
                validator_version="1.0.0"
            )
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return ConfigurationValidation(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                validation_time=datetime.now().isoformat(),
                validator_version="1.0.0"
            )
    
    def _get_config_mode_commands(self, device_type: str) -> List[str]:
        """Get commands to enter configuration mode for device type."""
        if device_type in ["cisco", "arista"]:
            return ["configure terminal"]
        elif device_type == "juniper":
            return ["configure"]
        else:
            return []
    
    def _get_exit_config_commands(self, device_type: str) -> List[str]:
        """Get commands to exit configuration mode for device type."""
        if device_type in ["cisco", "arista"]:
            return ["end", "write memory"]
        elif device_type == "juniper":
            return ["commit and-quit"]
        else:
            return []
    
    def _convert_to_remove_command(self, line: str, device_type: str) -> Optional[str]:
        """Convert add command to remove command for device type."""
        if device_type in ["cisco", "arista"]:
            if line.strip().startswith('interface '):
                return f"no {line.strip()}"
            elif line.strip().startswith('vlan '):
                return f"no {line.strip()}"
            else:
                return f"no {line.strip()}"
        elif device_type == "juniper":
            # Juniper uses "delete" instead of "no"
            if line.strip().startswith('set '):
                return line.strip().replace('set ', 'delete ', 1)
            else:
                return None
        else:
            return None
    
    def _validate_device_specific_config(self, config_lines: List[str], device_type: str) -> List[str]:
        """Validate configuration for specific device type."""
        errors = []
        
        if device_type in ["cisco", "arista"]:
            # Cisco/Arista specific validation
            for line in config_lines:
                if line.strip() and not line.strip().startswith('!'):
                    # Check for valid interface names
                    if line.strip().startswith('interface '):
                        interface_name = line.strip().split('interface ')[1].split()[0]
                        if not self._is_valid_interface_name(interface_name):
                            errors.append(f"Invalid interface name: {interface_name}")
        
        elif device_type == "juniper":
            # Juniper specific validation
            for line in config_lines:
                if line.strip() and not line.strip().startswith('#'):
                    if line.strip().startswith('set '):
                        # Validate set command format
                        parts = line.strip().split()
                        if len(parts) < 3:
                            errors.append(f"Invalid set command format: {line}")
        
        return errors
    
    def _is_valid_interface_name(self, interface_name: str) -> bool:
        """Check if interface name is valid."""
        import re
        
        # Common interface patterns
        valid_patterns = [
            r'^[a-zA-Z]+[\d/]+$',           # ge1/0/1, fa0/1
            r'^[a-zA-Z]+\d+-\d+/\d+/\d+$', # ge100-0/0/1
            r'^bundle-\d+$',                 # bundle-1
            r'^lo\d+$',                      # lo0
            r'^mgmt\d+$'                     # mgmt0
        ]
        
        return any(re.match(pattern, interface_name) for pattern in valid_patterns)
    
    def _validate_deployed_config(self, connection: SSHConnection, device_name: str) -> Dict[str, Any]:
        """Validate that configuration was deployed successfully."""
        try:
            # Show running config to verify
            if connection.config.device_type in ["cisco", "arista"]:
                result = self.command_executor.execute_template(connection, "show_running_config")
            elif connection.config.device_type == "juniper":
                result = self.command_executor.execute_template(connection, "show_config")
            else:
                result = None
            
            if result and result.success:
                return {
                    "validation_method": "show_running_config",
                    "output_length": len(result.output or ""),
                    "validation_success": True
                }
            else:
                return {
                    "validation_method": "show_running_config",
                    "validation_success": False,
                    "error": result.error if result else "No result"
                }
                
        except Exception as e:
            return {
                "validation_method": "show_running_config",
                "validation_success": False,
                "error": str(e)
            }
    
    def get_manager_info(self) -> Dict[str, Any]:
        """
        Get configuration manager information.
        
        Returns:
            Dictionary containing manager information
        """
        return {
            "config_dir": str(self.config_dir),
            "logs_dir": str(self.logs_dir),
            "total_configs": len(self.configs),
            "pending_configs": len([c for c in self.configs.values() if c.status == "pending"]),
            "deployed_configs": len([c for c in self.configs.values() if c.status == "deployed"]),
            "removed_configs": len([c for c in self.configs.values() if c.status == "removed"]),
            "connection_manager_info": self.connection_manager.get_manager_info(),
            "command_executor_info": self.command_executor.get_executor_info()
        }
    
    def cleanup(self) -> None:
        """Clean up configuration manager resources."""
        try:
            self.connection_manager.cleanup()
            self.executor.shutdown(wait=True)
            self.logger.info("Configuration Manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
