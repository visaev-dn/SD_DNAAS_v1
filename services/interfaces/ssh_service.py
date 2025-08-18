#!/usr/bin/env python3
"""
SSH Service Interface
Abstract base class defining the contract for SSH operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class SSHConnectionConfig:
    """Configuration for SSH connections"""
    hostname: str
    username: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    port: int = 22
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class SSHCommandResult:
    """Result of SSH command execution"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None


@dataclass
class SSHConfigPushResult:
    """Result of configuration push operations"""
    success: bool
    device_name: str
    config_changes: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    push_timestamp: Optional[str] = None


class SSHService(ABC):
    """
    Abstract base class for SSH services.
    
    This interface defines the contract that all SSH services
    must implement, ensuring consistency across different implementations.
    """
    
    @abstractmethod
    def connect(self, config: SSHConnectionConfig) -> bool:
        """
        Establish SSH connection to a device.
        
        Args:
            config: SSHConnectionConfig containing connection parameters
            
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close SSH connection.
        """
        pass
    
    @abstractmethod
    def execute_command(self, command: str) -> SSHCommandResult:
        """
        Execute a command on the connected device.
        
        Args:
            command: Command string to execute
            
        Returns:
            SSHCommandResult with command output and status
        """
        pass
    
    @abstractmethod
    def execute_commands(self, commands: List[str]) -> List[SSHCommandResult]:
        """
        Execute multiple commands on the connected device.
        
        Args:
            commands: List of command strings to execute
            
        Returns:
            List of SSHCommandResult objects
        """
        pass
    
    @abstractmethod
    def push_configuration(self, config_lines: List[str]) -> SSHConfigPushResult:
        """
        Push configuration lines to the device.
        
        Args:
            config_lines: List of configuration lines to apply
            
        Returns:
            SSHConfigPushResult indicating success/failure
        """
        pass
    
    @abstractmethod
    def get_configuration(self) -> Optional[str]:
        """
        Retrieve current device configuration.
        
        Returns:
            Device configuration as string, or None if failed
        """
        pass
    
    @abstractmethod
    def backup_configuration(self, backup_name: str) -> bool:
        """
        Backup current device configuration.
        
        Args:
            backup_name: Name for the backup file
            
        Returns:
            True if backup successful, False otherwise
        """
        pass
    
    @abstractmethod
    def restore_configuration(self, backup_name: str) -> bool:
        """
        Restore device configuration from backup.
        
        Args:
            backup_name: Name of the backup to restore
            
        Returns:
            True if restore successful, False otherwise
        """
        pass
    
    @abstractmethod
    def test_connectivity(self, config: SSHConnectionConfig) -> bool:
        """
        Test if SSH connection can be established.
        
        Args:
            config: SSHConnectionConfig to test
            
        Returns:
            True if connection test successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get current connection status information.
        
        Returns:
            Dictionary containing connection status details
        """
        pass
