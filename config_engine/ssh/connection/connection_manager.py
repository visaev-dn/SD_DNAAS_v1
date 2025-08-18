#!/usr/bin/env python3
"""
SSH Connection Manager
Handles SSH connection establishment, pooling, and management
"""

import paramiko
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import socket

from core.logging import get_logger
from core.exceptions import ConnectionError, ValidationError
from ..base_ssh_manager import (
    BaseSSHManager, SSHConnectionConfig, SSHConnectionStatus, SSHConnectionPool
)


@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    connection_time: float
    response_time: float
    throughput: float
    error_rate: float
    last_measured: datetime


class SSHConnection:
    """Individual SSH connection wrapper"""
    
    def __init__(self, config: SSHConnectionConfig):
        """
        Initialize SSH connection.
        
        Args:
            config: SSH connection configuration
        """
        self.config = config
        self.ssh_client = None
        self.shell = None
        self.connected_at = None
        self.last_activity = None
        self.error_count = 0
        self.metrics = None
        self.logger = get_logger(f"SSHConnection_{config.hostname}")
        
        # Connection state
        self._lock = threading.Lock()
        self._is_connected = False
    
    def connect(self) -> bool:
        """
        Establish SSH connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self._lock:
                if self._is_connected:
                    self.logger.warning("Already connected")
                    return True
                
                self.logger.info(f"Connecting to {self.config.hostname}:{self.config.port}")
                start_time = time.time()
                
                # Create SSH client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Connection parameters
                connect_kwargs = {
                    'hostname': self.config.hostname,
                    'port': self.config.port,
                    'username': self.config.username,
                    'timeout': self.config.timeout,
                    'look_for_keys': False,
                    'allow_agent': False
                }
                
                # Add authentication
                if self.config.password:
                    connect_kwargs['password'] = self.config.password
                elif self.config.private_key_path:
                    connect_kwargs['key_filename'] = self.config.private_key_path
                
                # Establish connection
                self.ssh_client.connect(**connect_kwargs)
                
                # Get shell
                self.shell = self.ssh_client.invoke_shell()
                time.sleep(2)  # Wait for shell to be ready
                
                # Clear initial buffer
                self._clear_buffer()
                
                # Update state
                self._is_connected = True
                self.connected_at = datetime.now()
                self.last_activity = datetime.now()
                
                # Measure connection time
                connection_time = time.time() - start_time
                self.metrics = ConnectionMetrics(
                    connection_time=connection_time,
                    response_time=0.0,
                    throughput=0.0,
                    error_rate=0.0,
                    last_measured=datetime.now()
                )
                
                self.logger.info(f"Successfully connected in {connection_time:.2f}s")
                return True
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Connection failed: {e}")
            self._cleanup()
            return False
    
    def disconnect(self) -> bool:
        """
        Close SSH connection.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        try:
            with self._lock:
                if not self._is_connected:
                    return True
                
                self.logger.info("Disconnecting...")
                
                if self.shell:
                    self.shell.close()
                    self.shell = None
                
                if self.ssh_client:
                    self.ssh_client.close()
                    self.ssh_client = None
                
                self._is_connected = False
                self.logger.info("Disconnected successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connection is active."""
        with self._lock:
            return self._is_connected and self.ssh_client and self.shell
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        with self._lock:
            if not self._is_connected:
                return {}
            
            return {
                "hostname": self.config.hostname,
                "username": self.config.username,
                "port": self.config.port,
                "device_type": self.config.device_type,
                "connected_at": self.connected_at.isoformat() if self.connected_at else None,
                "last_activity": self.last_activity.isoformat() if self.last_activity else None,
                "error_count": self.error_count,
                "metrics": self.metrics.__dict__ if self.metrics else None
            }
    
    def _clear_buffer(self) -> None:
        """Clear the shell buffer."""
        if self.shell and self.shell.recv_ready():
            try:
                self.shell.recv(65535)
            except Exception as e:
                self.logger.debug(f"Error clearing buffer: {e}")
    
    def _cleanup(self) -> None:
        """Clean up connection resources."""
        try:
            if self.shell:
                self.shell.close()
                self.shell = None
            
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
                
        except Exception as e:
            self.logger.debug(f"Error during cleanup: {e}")
        
        self._is_connected = False


class ConnectionManager:
    """
    Manages SSH connections with pooling and lifecycle management.
    """
    
    def __init__(self, max_connections: int = 10, connection_timeout: int = 300):
        """
        Initialize connection manager.
        
        Args:
            max_connections: Maximum number of concurrent connections
            connection_timeout: Connection timeout in seconds
        """
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.logger = get_logger(__name__)
        
        # Connection storage
        self.connections: Dict[str, SSHConnection] = {}
        self.connection_lock = threading.Lock()
        
        # Connection pool metrics
        self.total_connections = 0
        self.failed_connections = 0
        self.connection_errors = []
        
        # Health check thread
        self.health_check_thread = None
        self.health_check_interval = 60  # seconds
        self._stop_health_check = threading.Event()
        
        # Start health check
        self._start_health_check()
    
    def get_connection(self, device_name: str) -> Optional[SSHConnection]:
        """
        Get existing connection for a device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            SSHConnection object or None if not found
        """
        with self.connection_lock:
            return self.connections.get(device_name)
    
    def create_connection(self, device_name: str, config: SSHConnectionConfig) -> Optional[SSHConnection]:
        """
        Create a new SSH connection.
        
        Args:
            device_name: Name of the device
            config: SSH connection configuration
            
        Returns:
            SSHConnection object or None if creation failed
        """
        try:
            # Check if connection already exists
            existing = self.get_connection(device_name)
            if existing and existing.is_connected():
                self.logger.info(f"Connection to {device_name} already exists")
                return existing
            
            # Check connection limit
            if len(self.connections) >= self.max_connections:
                self.logger.warning(f"Connection limit reached ({self.max_connections})")
                return None
            
            # Create new connection
            self.logger.info(f"Creating connection to {device_name}")
            connection = SSHConnection(config)
            
            # Attempt to connect
            if connection.connect():
                with self.connection_lock:
                    self.connections[device_name] = connection
                    self.total_connections += 1
                
                self.logger.info(f"Successfully created connection to {device_name}")
                return connection
            else:
                self.failed_connections += 1
                self.connection_errors.append({
                    "device": device_name,
                    "error": "Connection failed",
                    "timestamp": datetime.now().isoformat()
                })
                return None
                
        except Exception as e:
            self.failed_connections += 1
            self.connection_errors.append({
                "device": device_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self.logger.error(f"Error creating connection to {device_name}: {e}")
            return None
    
    def close_connection(self, device_name: str) -> bool:
        """
        Close connection to a specific device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            True if connection closed successfully, False otherwise
        """
        try:
            with self.connection_lock:
                connection = self.connections.pop(device_name, None)
            
            if connection:
                success = connection.disconnect()
                if success:
                    self.logger.info(f"Closed connection to {device_name}")
                return success
            else:
                self.logger.warning(f"No connection found for {device_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error closing connection to {device_name}: {e}")
            return False
    
    def close_all_connections(self) -> None:
        """Close all active connections."""
        self.logger.info("Closing all connections...")
        
        device_names = list(self.connections.keys())
        for device_name in device_names:
            self.close_connection(device_name)
        
        self.logger.info("All connections closed")
    
    def get_connection_status(self, device_name: str) -> Optional[SSHConnectionStatus]:
        """
        Get connection status for a device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            SSHConnectionStatus object or None if not found
        """
        connection = self.get_connection(device_name)
        if not connection:
            return None
        
        info = connection.get_connection_info()
        return SSHConnectionStatus(
            connected=connection.is_connected(),
            device_name=device_name,
            connection_time=info.get("connected_at"),
            last_activity=info.get("last_activity"),
            connection_quality=self._assess_connection_quality(connection),
            error_count=info.get("error_count", 0)
        )
    
    def get_all_connection_statuses(self) -> Dict[str, SSHConnectionStatus]:
        """
        Get status of all connections.
        
        Returns:
            Dictionary mapping device names to connection statuses
        """
        statuses = {}
        for device_name in self.connections.keys():
            status = self.get_connection_status(device_name)
            if status:
                statuses[device_name] = status
        return statuses
    
    def get_connection_count(self) -> int:
        """Get current number of active connections."""
        with self.connection_lock:
            return len(self.connections)
    
    def get_available_connections(self) -> int:
        """Get number of available connection slots."""
        return self.max_connections - self.get_connection_count()
    
    def validate_connection_config(self, config: 'SSHConnectionConfig') -> Tuple[bool, List[str]]:
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
    
    def _assess_connection_quality(self, connection: SSHConnection) -> str:
        """
        Assess the quality of a connection.
        
        Args:
            connection: SSHConnection object
            
        Returns:
            Quality assessment string
        """
        if not connection.metrics:
            return "unknown"
        
        metrics = connection.metrics
        
        # Simple quality assessment based on metrics
        if metrics.error_rate > 0.1:  # > 10% error rate
            return "poor"
        elif metrics.response_time > 5.0:  # > 5s response time
            return "fair"
        elif metrics.response_time > 2.0:  # > 2s response time
            return "good"
        else:
            return "excellent"
    
    def _start_health_check(self) -> None:
        """Start the health check thread."""
        def health_check_worker():
            while not self._stop_health_check.wait(self.health_check_interval):
                self._perform_health_check()
        
        self.health_check_thread = threading.Thread(target=health_check_worker, daemon=True)
        self.health_check_thread.start()
        self.logger.info("Health check thread started")
    
    def _perform_health_check(self) -> None:
        """Perform health check on all connections."""
        try:
            self.logger.debug("Performing health check...")
            
            # Check for stale connections
            current_time = datetime.now()
            stale_connections = []
            
            for device_name, connection in self.connections.items():
                if not connection.is_connected():
                    stale_connections.append(device_name)
                    continue
                
                # Check connection timeout
                if (connection.last_activity and 
                    current_time - connection.last_activity > timedelta(seconds=self.connection_timeout)):
                    self.logger.warning(f"Connection to {device_name} timed out")
                    stale_connections.append(device_name)
            
            # Remove stale connections
            for device_name in stale_connections:
                self.logger.info(f"Removing stale connection to {device_name}")
                self.close_connection(device_name)
                
        except Exception as e:
            self.logger.error(f"Error during health check: {e}")
    
    def stop_health_check(self) -> None:
        """Stop the health check thread."""
        self._stop_health_check.set()
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        self.logger.info("Health check thread stopped")
    
    def get_manager_info(self) -> Dict[str, Any]:
        """
        Get connection manager information.
        
        Returns:
            Dictionary containing manager information
        """
        return {
            "max_connections": self.max_connections,
            "active_connections": self.get_connection_count(),
            "available_connections": self.get_available_connections(),
            "total_connections": self.total_connections,
            "failed_connections": self.failed_connections,
            "connection_errors": self.connection_errors[-10:],  # Last 10 errors
            "health_check_active": not self._stop_health_check.is_set()
        }
    
    def cleanup(self) -> None:
        """Clean up connection manager resources."""
        try:
            self.stop_health_check()
            self.close_all_connections()
            self.logger.info("Connection manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
