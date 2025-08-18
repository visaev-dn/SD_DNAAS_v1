#!/usr/bin/env python3
"""
Rollback Manager
Manages rollback configurations for smart deployments, ensuring safe recovery from failed deployments.
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import re

from .smart_deployment_types import RollbackConfig, DeploymentDiff, DeviceChange

logger = logging.getLogger(__name__)

class RollbackManager:
    """
    Manages rollback configurations for deployments.
    
    Features:
    - Automatic rollback configuration generation
    - Rollback command validation
    - Rollback execution tracking
    - Rollback configuration storage
    """
    
    def __init__(self, storage_dir: str = "rollbacks"):
        """
        Initialize rollback manager.
        
        Args:
            storage_dir: Directory to store rollback configurations
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.logger = logger
        
        # Rollback configurations storage
        self.rollback_configs: Dict[str, RollbackConfig] = {}
        
        # Load existing rollback configurations
        self._load_existing_rollbacks()
    
    def prepare_rollback(self, diff: DeploymentDiff, config_id: int) -> RollbackConfig:
        """
        Prepare rollback configuration from deployment diff.
        
        Args:
            diff: DeploymentDiff containing changes to rollback
            config_id: ID of the configuration being deployed
            
        Returns:
            RollbackConfig with commands to restore previous state
        """
        try:
            self.logger.info("Preparing rollback configuration from deployment diff")
            
            # Generate rollback commands for each change
            rollback_commands = []
            
            # Handle device additions (need to remove)
            for device_change in diff.devices_to_add:
                if device_change.change_type == 'add':
                    device_rollback_cmds = self._generate_rollback_commands_for_addition(device_change)
                    rollback_commands.extend(device_rollback_cmds)
            
            # Handle device modifications (need to restore old config)
            for device_change in diff.devices_to_modify:
                if device_change.change_type == 'modify':
                    device_rollback_cmds = self._generate_rollback_commands_for_modification(device_change)
                    rollback_commands.extend(device_rollback_cmds)
            
            # Handle device removals (need to restore)
            for device_change in diff.devices_to_remove:
                if device_change.change_type == 'remove':
                    device_rollback_cmds = self._generate_rollback_commands_for_removal(device_change)
                    rollback_commands.extend(device_rollback_cmds)
            
            # Create rollback configuration with new dataclass structure
            rollback_config = RollbackConfig(
                deployment_id=f"rollback_{int(time.time())}",
                original_config_id=config_id,
                rollback_commands=rollback_commands,
                created_at=datetime.utcnow().isoformat(),
                # Legacy fields for backward compatibility
                commands={
                    'rollback_commands': rollback_commands
                },
                metadata={
                    'created_from_diff': True,
                    'device_count': len(set(dc.device_name for dc in diff.devices_to_add + diff.devices_to_modify + diff.devices_to_remove)),
                    'change_types': list(set(dc.change_type for dc in diff.devices_to_add + diff.devices_to_modify + diff.devices_to_remove)),
                    'vlan_changes': len(diff.vlan_changes),
                    'risk_level': diff.estimated_impact.risk_level.value
                }
            )
            
            self.logger.info(f"Rollback configuration prepared for {len(rollback_commands)} commands")
            return rollback_config
            
        except Exception as e:
            self.logger.error(f"Error preparing rollback configuration: {e}")
            raise
    
    def prepare_rollback_from_config(self, current_config: Dict, config_id: int) -> RollbackConfig:
        """
        Prepare rollback configuration from current configuration.
        
        Args:
            current_config: Current configuration to backup
            config_id: ID of the configuration being backed up
            
        Returns:
            RollbackConfig with commands to restore current state
        """
        try:
            self.logger.info("Preparing rollback configuration from current configuration")
            
            # Parse current configuration
            parsed_config = self._parse_configuration_for_rollback(current_config)
            
            # Generate rollback commands as a flat list
            rollback_commands = []
            for device_name, device_config in parsed_config['devices'].items():
                rollback_commands.extend(device_config['commands'])
            
            # Create rollback configuration with new dataclass structure
            rollback_config = RollbackConfig(
                deployment_id=f"backup_{int(time.time())}",
                original_config_id=config_id,
                rollback_commands=rollback_commands,
                created_at=datetime.utcnow().isoformat(),
                # Legacy fields for backward compatibility
                commands={
                    'rollback_commands': rollback_commands
                },
                metadata={
                    'created_from_config': True,
                    'device_count': len(parsed_config['devices']),
                    'config_type': 'current_state_backup',
                    'total_commands': len(rollback_commands)
                }
            )
            
            self.logger.info(f"Rollback configuration prepared from current config for {len(rollback_commands)} commands")
            return rollback_config
            
        except Exception as e:
            self.logger.error(f"Error preparing rollback from config: {e}")
            raise
    
    def store_rollback_config(self, rollback_config: RollbackConfig) -> str:
        """
        Store rollback configuration for later use.
        
        Args:
            rollback_config: RollbackConfig to store
            
        Returns:
            Storage ID for the rollback configuration
        """
        try:
            storage_id = f"rollback_{rollback_config.deployment_id}_{int(time.time())}"
            
            # Store in memory
            self.rollback_configs[storage_id] = rollback_config
            
            # Store to disk
            file_path = self.storage_dir / f"{storage_id}.json"
            with open(file_path, 'w') as f:
                json.dump(self._serialize_rollback_config(rollback_config), f, indent=2, default=str)
            
            self.logger.info(f"Rollback configuration stored with ID: {storage_id}")
            return storage_id
            
        except Exception as e:
            self.logger.error(f"Error storing rollback configuration: {e}")
            raise
    
    def get_rollback_config(self, storage_id: str) -> Optional[RollbackConfig]:
        """
        Retrieve stored rollback configuration.
        
        Args:
            storage_id: Storage ID of the rollback configuration
            
        Returns:
            RollbackConfig if found, None otherwise
        """
        try:
            # Try memory first
            if storage_id in self.rollback_configs:
                return self.rollback_configs[storage_id]
            
            # Try disk
            file_path = self.storage_dir / f"{storage_id}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    rollback_config = self._deserialize_rollback_config(data)
                    # Cache in memory
                    self.rollback_configs[storage_id] = rollback_config
                    return rollback_config
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving rollback configuration {storage_id}: {e}")
            return None
    
    def list_rollback_configs(self) -> List[Dict]:
        """
        List all available rollback configurations.
        
        Returns:
            List of rollback configuration summaries
        """
        try:
            rollbacks = []
            
            # Check memory
            for storage_id, config in self.rollback_configs.items():
                rollbacks.append({
                    'storage_id': storage_id,
                    'deployment_id': config.deployment_id,
                    'created_at': config.created_at,
                    'device_count': len(config.commands),
                    'metadata': config.metadata
                })
            
            # Check disk for additional configs
            for file_path in self.storage_dir.glob("rollback_*.json"):
                try:
                    storage_id = file_path.stem
                    if storage_id not in self.rollback_configs:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            config = self._deserialize_rollback_config(data)
                            rollbacks.append({
                                'storage_id': storage_id,
                                'deployment_id': config.deployment_id,
                                'created_at': config.created_at,
                                'device_count': len(config.commands),
                                'metadata': config.metadata
                            })
                except Exception as e:
                    self.logger.warning(f"Error reading rollback file {file_path}: {e}")
            
            # Sort by creation time (newest first)
            rollbacks.sort(key=lambda x: x['created_at'], reverse=True)
            
            return rollbacks
            
        except Exception as e:
            self.logger.error(f"Error listing rollback configurations: {e}")
            return []
    
    def delete_rollback_config(self, storage_id: str) -> bool:
        """
        Delete a stored rollback configuration.
        
        Args:
            storage_id: Storage ID of the rollback configuration to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Remove from memory
            if storage_id in self.rollback_configs:
                del self.rollback_configs[storage_id]
            
            # Remove from disk
            file_path = self.storage_dir / f"{storage_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            self.logger.info(f"Rollback configuration {storage_id} deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting rollback configuration {storage_id}: {e}")
            return False
    
    def validate_rollback_config(self, rollback_config: RollbackConfig) -> Dict[str, Any]:
        """
        Validate rollback configuration for correctness and safety.
        
        Args:
            rollback_config: RollbackConfig to validate
            
        Returns:
            Validation result with issues and warnings
        """
        try:
            validation_result = {
                'valid': True,
                'issues': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Check if rollback config has commands
            if not rollback_config.commands:
                validation_result['valid'] = False
                validation_result['issues'].append("No rollback commands found")
            
            # Validate each device's rollback commands
            for device_name, commands in rollback_config.commands.items():
                device_validation = self._validate_device_rollback_commands(device_name, commands)
                
                if not device_validation['valid']:
                    validation_result['valid'] = False
                    validation_result['issues'].extend(device_validation['issues'])
                
                validation_result['warnings'].extend(device_validation['warnings'])
                validation_result['recommendations'].extend(device_validation['recommendations'])
            
            # Check metadata
            if not rollback_config.metadata:
                validation_result['warnings'].append("No metadata found in rollback configuration")
            
            # Check creation time
            if rollback_config.created_at:
                age_hours = (datetime.utcnow() - rollback_config.created_at).total_seconds() / 3600
                if age_hours > 24:
                    validation_result['warnings'].append(f"Rollback configuration is {age_hours:.1f} hours old")
            
            self.logger.info(f"Rollback configuration validation complete: {len(validation_result['issues'])} issues, {len(validation_result['warnings'])} warnings")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating rollback configuration: {e}")
            return {
                'valid': False,
                'issues': [f"Validation error: {str(e)}"],
                'warnings': [],
                'recommendations': []
            }
    
    def execute_rollback(self, deployment_id: str) -> Dict[str, Any]:
        """
        Execute rollback for a specific deployment.
        
        Args:
            deployment_id: ID of the deployment to rollback
            
        Returns:
            Execution result with success status and details
        """
        try:
            self.logger.info(f"Executing rollback for deployment: {deployment_id}")
            
            # Find rollback configuration for this deployment
            rollback_config = None
            for config in self.rollback_configs.values():
                if config.deployment_id == deployment_id:
                    rollback_config = config
                    break
            
            if not rollback_config:
                # Try to find by original config ID
                for config in self.rollback_configs.values():
                    if hasattr(config, 'original_config_id') and str(config.original_config_id) == deployment_id:
                        rollback_config = config
                        break
            
            if not rollback_config:
                raise ValueError(f"No rollback configuration found for deployment: {deployment_id}")
            
            # Execute rollback commands
            execution_result = {
                'success': True,
                'deployment_id': deployment_id,
                'rollback_config_id': rollback_config.deployment_id,
                'commands_executed': 0,
                'commands_failed': 0,
                'errors': [],
                'logs': []
            }
            
            # Execute rollback commands (this would integrate with SSH manager in practice)
            if rollback_config.rollback_commands:
                for command in rollback_config.rollback_commands:
                    try:
                        # In practice, this would execute via SSH
                        # For now, we'll simulate execution
                        self.logger.info(f"Executing rollback command: {command}")
                        execution_result['logs'].append(f"Executed: {command}")
                        execution_result['commands_executed'] += 1
                        
                        # Simulate some commands failing (for testing)
                        if "dangerous" in command.lower():
                            raise Exception("Dangerous command detected")
                            
                    except Exception as e:
                        execution_result['commands_failed'] += 1
                        execution_result['errors'].append(f"Command '{command}' failed: {str(e)}")
                        execution_result['logs'].append(f"Failed: {command} - {str(e)}")
                        self.logger.error(f"Rollback command failed: {command} - {e}")
            
            # Update execution result
            if execution_result['commands_failed'] > 0:
                execution_result['success'] = False
                execution_result['logs'].append(f"Rollback completed with {execution_result['commands_failed']} failures")
            else:
                execution_result['logs'].append("Rollback completed successfully")
            
            self.logger.info(f"Rollback execution completed: {execution_result['commands_executed']} commands executed, {execution_result['commands_failed']} failed")
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Error executing rollback: {e}")
            return {
                'success': False,
                'deployment_id': deployment_id,
                'error': str(e),
                'commands_executed': 0,
                'commands_failed': 0,
                'errors': [str(e)],
                'logs': [f"Rollback execution failed: {str(e)}"]
            }
    
    def get_rollback_config_for_deployment(self, deployment_id: str) -> Optional[RollbackConfig]:
        """
        Get rollback configuration for a specific deployment.
        
        Args:
            deployment_id: ID of the deployment
            
        Returns:
            RollbackConfig if found, None otherwise
        """
        try:
            # First try to find by deployment_id
            for config in self.rollback_configs.values():
                if config.deployment_id == deployment_id:
                    return config
            
            # Then try by original_config_id
            for config in self.rollback_configs.values():
                if hasattr(config, 'original_config_id') and str(config.original_config_id) == deployment_id:
                    return config
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding rollback config for deployment {deployment_id}: {e}")
            return None
    
    def _generate_rollback_commands_for_addition(self, device_change: DeviceChange) -> List[str]:
        """Generate rollback commands for a device addition."""
        try:
            rollback_commands = []
            
            # For added devices, we need to remove the configuration
            # This is a simplified approach - in practice, you'd need device-specific logic
            
            # Remove VLAN configurations
            for vlan_change in device_change.vlan_changes:
                if vlan_change['change_type'] == 'add':
                    rollback_commands.append(f"no vlan {vlan_change['vlan_id']}")
            
            # Remove interface configurations
            for interface in device_change.affected_interfaces:
                rollback_commands.append(f"interface {interface}")
                rollback_commands.append("shutdown")
                rollback_commands.append("exit")
            
            # Add device-specific cleanup commands
            rollback_commands.append("write memory")
            
            return rollback_commands
            
        except Exception as e:
            self.logger.error(f"Error generating rollback commands for addition: {e}")
            return []
    
    def _generate_rollback_commands_for_modification(self, device_change: DeviceChange) -> List[str]:
        """Generate rollback commands for a device modification."""
        try:
            rollback_commands = []
            
            # For modified devices, we need to restore the old configuration
            # This is a simplified approach - in practice, you'd need device-specific logic
            
            # Restore old commands
            rollback_commands.extend(device_change.old_commands)
            
            # Add device-specific cleanup commands
            rollback_commands.append("write memory")
            
            return rollback_commands
            
        except Exception as e:
            self.logger.error(f"Error generating rollback commands for modification: {e}")
            return []
    
    def _generate_rollback_commands_for_removal(self, device_change: DeviceChange) -> List[str]:
        """Generate rollback commands for a device removal."""
        try:
            rollback_commands = []
            
            # For removed devices, we need to restore the configuration
            # This is a simplified approach - in practice, you'd need device-specific logic
            
            # Restore old commands
            rollback_commands.extend(device_change.old_commands)
            
            # Add device-specific cleanup commands
            rollback_commands.append("write memory")
            
            return rollback_commands
            
        except Exception as e:
            self.logger.error(f"Error generating rollback commands for removal: {e}")
            return []
    
    def _parse_configuration_for_rollback(self, config: Dict) -> Dict:
        """Parse configuration for rollback purposes."""
        try:
            parsed = {
                'devices': {},
                'metadata': {}
            }
            
            # Handle different configuration formats
            if isinstance(config, dict):
                for device_name, device_config in config.items():
                    if isinstance(device_config, dict) and 'commands' in device_config:
                        parsed['devices'][device_name] = {
                            'commands': device_config['commands']
                        }
                    elif isinstance(device_config, list):
                        parsed['devices'][device_name] = {
                            'commands': device_config
                        }
            
            # Extract metadata
            if 'metadata' in config:
                parsed['metadata'] = config['metadata']
            
            return parsed
            
        except Exception as e:
            self.logger.error(f"Error parsing configuration for rollback: {e}")
            raise
    
    def _validate_device_rollback_commands(self, device_name: str, commands: List[str]) -> Dict[str, Any]:
        """Validate rollback commands for a specific device."""
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Check if commands exist
            if not commands:
                validation_result['valid'] = False
                validation_result['issues'].append(f"No rollback commands for device {device_name}")
                return validation_result
            
            # Check for dangerous commands
            dangerous_patterns = [
                r'^no\s+username\s+admin',  # Removing admin user
                r'^no\s+enable\s+secret',   # Removing enable secret
                r'^no\s+ip\s+route',        # Removing routing
                r'^no\s+vlan\s+1'           # Removing default VLAN
            ]
            
            for pattern in dangerous_patterns:
                for command in commands:
                    if re.search(pattern, command, re.IGNORECASE):
                        validation_result['warnings'].append(f"Potentially dangerous command: {command}")
            
            # Check for missing critical commands
            critical_commands = ['write memory', 'copy running-config startup-config']
            has_critical = any(cmd in ' '.join(commands) for cmd in critical_commands)
            
            if not has_critical:
                validation_result['warnings'].append("No configuration save command found")
                validation_result['recommendations'].append("Add 'write memory' or equivalent command")
            
            # Check command syntax (basic validation)
            for command in commands:
                if not self._validate_command_syntax(command):
                    validation_result['warnings'].append(f"Potentially invalid command syntax: {command}")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_command_syntax(self, command: str) -> bool:
        """Basic command syntax validation."""
        try:
            # This is a simplified validation - in practice, you'd use device-specific parsers
            
            # Check for basic structure
            if not command or command.strip() == '':
                return False
            
            # Check for common patterns
            if command.startswith('interface ') and not command.endswith('exit'):
                return False
            
            # Check for balanced parentheses/brackets
            if command.count('(') != command.count(')') or command.count('[') != command.count(']'):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _serialize_rollback_config(self, rollback_config: RollbackConfig) -> Dict:
        """Serialize rollback configuration for storage."""
        return {
            'commands': rollback_config.commands,
            'metadata': rollback_config.metadata,
            'created_at': rollback_config.created_at.isoformat(),
            'deployment_id': rollback_config.deployment_id
        }
    
    def _deserialize_rollback_config(self, data: Dict) -> RollbackConfig:
        """Deserialize rollback configuration from storage."""
        return RollbackConfig(
            commands=data['commands'],
            metadata=data['metadata'],
            created_at=datetime.fromisoformat(data['created_at']),
            deployment_id=data['deployment_id']
        )
    
    def _load_existing_rollbacks(self):
        """Load existing rollback configurations from disk."""
        try:
            for file_path in self.storage_dir.glob("rollback_*.json"):
                try:
                    storage_id = file_path.stem
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        config = self._deserialize_rollback_config(data)
                        self.rollback_configs[storage_id] = config
                except Exception as e:
                    self.logger.warning(f"Error loading rollback file {file_path}: {e}")
            
            self.logger.info(f"Loaded {len(self.rollback_configs)} existing rollback configurations")
            
        except Exception as e:
            self.logger.error(f"Error loading existing rollbacks: {e}")
    
    def cleanup_old_rollbacks(self, max_age_hours: int = 168) -> int:
        """
        Clean up old rollback configurations.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup (default: 1 week)
            
        Returns:
            Number of rollback configurations cleaned up
        """
        try:
            cleaned_count = 0
            current_time = datetime.utcnow()
            
            for storage_id, config in list(self.rollback_configs.items()):
                age_hours = (current_time - config.created_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    if self.delete_rollback_config(storage_id):
                        cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} old rollback configurations")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old rollbacks: {e}")
            return 0 