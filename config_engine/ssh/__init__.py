#!/usr/bin/env python3
"""
SSH Package
Consolidated SSH management for the Lab Automation Framework
"""

from .base_ssh_manager import (
    BaseSSHManager,
    SSHConnectionConfig,
    SSHCommandResult,
    SSHConfigPushResult,
    SSHConnectionStatus,
    SSHConnectionPool
)

from .connection import (
    ConnectionManager,
    SSHConnection,
    ConnectionMetrics
)

from .execution import (
    CommandExecutor,
    CommandTemplate
)

from .management import (
    ConfigurationManager,
    ConfigurationFile,
    ConfigurationValidation
)

__all__ = [
    # Base SSH manager
    'BaseSSHManager',
    'SSHConnectionConfig',
    'SSHCommandResult',
    'SSHConfigPushResult',
    'SSHConnectionStatus',
    'SSHConnectionPool',
    
    # Connection management
    'ConnectionManager',
    'SSHConnection',
    'ConnectionMetrics',
    
    # Command execution
    'CommandExecutor',
    'CommandTemplate',
    
    # Configuration management
    'ConfigurationManager',
    'ConfigurationFile',
    'ConfigurationValidation'
]

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Consolidated SSH management with connection pooling, command execution, and configuration management"
