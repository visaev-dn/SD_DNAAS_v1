#!/usr/bin/env python3
"""
Base SSH Manager
Abstract base class for all SSH management operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.logging import get_logger
from core.exceptions import BusinessLogicError, ValidationError, ConnectionError


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
    device_type: str = "generic"
    connection_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate connection configuration"""
        errors = []
        if not self.hostname:
            errors.append("Hostname is required")
        if not self.username:
            errors.append("Username is required")
        if not self.password and not self.private_key_path:
            errors.append("Either password or private key path is required")
        if self.port < 1 or self.port > 65535:
            errors.append("Port must be between 1 and 65535")
        if self.timeout < 1:
            errors.append("Timeout must be positive")
        if self.retry_attempts < 0:
            errors.append("Retry attempts must be non-negative")
        
        if errors:
            raise ValidationError("; ".join(errors))


@dataclass
class SSHCommandResult:
    """Result of SSH command execution"""
    success: bool
    command: str
    output: Optional[str] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: Optional[float] = None
    device_name: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SSHConfigPushResult:
    """Result of configuration push operations"""
    success: bool
    device_name: str
    config_changes: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    push_timestamp: Optional[str] = None
    commands_executed: List[str] = field(default_factory=list)
    validation_results: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.push_timestamp is None:
            self.push_timestamp = datetime.now().isoformat()


@dataclass
class SSHConnectionStatus:
    """Status of SSH connection"""
    connected: bool
    device_name: str
    connection_time: Optional[str] = None
    last_activity: Optional[str] = None
    connection_quality: Optional[str] = None
    error_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SSHConnectionPool:
    """Pool of SSH connections"""
    max_connections: int = 10
    active_connections: Dict[str, SSHConnectionStatus] = field(default_factory=dict)
    connection_queue: List[str] = field(default_factory=list)
    pool_lock: threading.Lock = field(default_factory=threading.Lock)


class BaseSSHManager(ABC):
    """
    Abstract base class for all SSH management operations.
    
    This class provides common functionality and enforces the interface
    that all SSH managers must implement.
    """
    
    def __init__(self, config_dir: str = "configs", logs_dir: str = "logs"):
        """
        Initialize the base SSH manager.
        
        Args:
            config_dir: Directory containing configuration files
            logs_dir: Directory for SSH operation logs
        """
        self.config_dir = Path(config_dir)
        self.logs_dir = Path(logs_dir)
        self.logger = get_logger(__name__)
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection pool
        self.connection_pool = SSHConnectionPool()
        self.connection_lock = threading.Lock()
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        self.logger.info(f"Base SSH Manager initialized with config_dir: {config_dir}")
    
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
    def disconnect(self, device_name: str) -> bool:
        """
        Close SSH connection to a specific device.
        
        Args:
            device_name: Name of the device to disconnect from
            
        Returns:
            True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def execute_command(self, device_name: str, command: str) -> SSHCommandResult:
        """
        Execute a command on a connected device.
        
        Args:
            device_name: Name of the device to execute command on
            command: Command string to execute
            
        Returns:
            SSHCommandResult with command output and status
        """
        pass
    
    @abstractmethod
    def execute_commands(self, device_name: str, commands: List[str]) -> List[SSHCommandResult]:
        """
        Execute multiple commands on a connected device.
        
        Args:
            device_name: Name of the device to execute commands on
            commands: List of command strings to execute
            
        Returns:
            List of SSHCommandResult objects
        """
        pass
    
    @abstractmethod
    def push_configuration(self, device_name: str, config_lines: List[str]) -> SSHConfigPushResult:
        """
        Push configuration to a device.
        
        Args:
            device_name: Name of the device to push configuration to
            config_lines: List of configuration lines to push
            
        Returns:
            SSHConfigPushResult with push status and details
        """
        pass
    
    def get_connection_status(self, device_name: str) -> Optional[SSHConnectionStatus]:
        """
        Get connection status for a specific device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            SSHConnectionStatus object or None if not connected
        """
        with self.connection_lock:
            return self.connection_pool.active_connections.get(device_name)
    
    def get_all_connection_statuses(self) -> Dict[str, SSHConnectionStatus]:
        """
        Get status of all active connections.
        
        Returns:
            Dictionary mapping device names to connection statuses
        """
        with self.connection_lock:
            return self.connection_pool.active_connections.copy()
    
    def is_connected(self, device_name: str) -> bool:
        """
        Check if a device is currently connected.
        
        Args:
            device_name: Name of the device
            
        Returns:
            True if connected, False otherwise
        """
        status = self.get_connection_status(device_name)
        return status.connected if status else False
    
    def get_connection_count(self) -> int:
        """
        Get the current number of active connections.
        
        Returns:
            Number of active connections
        """
        with self.connection_lock:
            return len(self.connection_pool.active_connections)
    
    def get_available_connections(self) -> int:
        """
        Get the number of available connection slots.
        
        Returns:
            Number of available connection slots
        """
        return self.connection_pool.max_connections - self.get_connection_count()
    
    def execute_concurrent_commands(self, device_commands: Dict[str, List[str]]) -> Dict[str, List[SSHCommandResult]]:
        """
        Execute commands on multiple devices concurrently.
        
        Args:
            device_commands: Dictionary mapping device names to command lists
            
        Returns:
            Dictionary mapping device names to command results
        """
        results = {}
        
        # Submit all tasks to thread pool
        future_to_device = {}
        for device_name, commands in device_commands.items():
            if self.is_connected(device_name):
                future = self.executor.submit(self.execute_commands, device_name, commands)
                future_to_device[future] = device_name
        
        # Collect results as they complete
        for future in as_completed(future_to_device):
            device_name = future_to_device[future]
            try:
                results[device_name] = future.result()
            except Exception as e:
                self.logger.error(f"Error executing commands on {device_name}: {e}")
                results[device_name] = [SSHCommandResult(
                    success=False,
                    command="",
                    error=str(e),
                    device_name=device_name
                )]
        
        return results
    
    def validate_connection_config(self, config: SSHConnectionConfig) -> Tuple[bool, List[str]]:
        """
        Validate SSH connection configuration.
        
        Args:
            config: SSHConnectionConfig to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Test basic validation
            config.__post_init__()
        except ValidationError as e:
            errors.append(str(e))
        
        # Additional validation
        if config.hostname and not self._is_valid_hostname(config.hostname):
            errors.append("Invalid hostname format")
        
        if config.private_key_path and not Path(config.private_key_path).exists():
            errors.append("Private key file does not exist")
        
        return len(errors) == 0, errors
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """
        Validate hostname format.
        
        Args:
            hostname: Hostname to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        
        # Basic hostname validation
        if not hostname or len(hostname) > 253:
            return False
        
        # Check for valid characters
        valid_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        return bool(re.match(valid_pattern, hostname))
    
    def get_manager_info(self) -> Dict[str, Any]:
        """
        Get information about this SSH manager.
        
        Returns:
            Dictionary containing manager information
        """
        return {
            "manager_type": self.__class__.__name__,
            "config_dir": str(self.config_dir),
            "logs_dir": str(self.logs_dir),
            "active_connections": self.get_connection_count(),
            "max_connections": self.connection_pool.max_connections,
            "available_connections": self.get_available_connections(),
            "capabilities": self.get_capabilities(),
            "supported_device_types": self.get_supported_device_types()
        }
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of manager capabilities.
        
        Returns:
            List of capability strings
        """
        pass
    
    @abstractmethod
    def get_supported_device_types(self) -> List[str]:
        """
        Get list of supported device types.
        
        Returns:
            List of supported device type strings
        """
        pass
    
    def cleanup(self) -> None:
        """Clean up resources and close all connections."""
        try:
            # Close all active connections
            device_names = list(self.get_all_connection_statuses().keys())
            for device_name in device_names:
                self.disconnect(device_name)
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            self.logger.info("SSH Manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
