#!/usr/bin/env python3
"""
Universal SSH Framework Data Models

Common data structures and enums for the universal SSH deployment framework.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ExecutionMode(Enum):
    """SSH command execution modes"""
    COMMIT_CHECK = "commit_check"  # Test configuration without committing (BD-Builder pattern)
    COMMIT = "commit"              # Execute and commit configuration (BD-Builder pattern)
    QUERY = "query"                # Query device for information (Interface Discovery pattern)
    DRY_RUN = "dry_run"           # Validate commands without execution
    IMMEDIATE = "immediate"        # Execute immediately without config mode


@dataclass
class DeviceInfo:
    """Device information from devices.yaml"""
    name: str
    mgmt_ip: str
    username: str
    password: str
    device_type: str = "unknown"
    ssh_port: int = 22
    status: str = "active"
    location: str = ""
    role: str = ""


@dataclass
class CommandResult:
    """Result of single command execution"""
    command: str
    success: bool
    output: str = ""
    error_message: str = ""
    execution_time: float = 0.0


@dataclass
class ExecutionResult:
    """Result of command execution on a device"""
    device_name: str
    success: bool
    execution_mode: ExecutionMode
    commands_executed: List[str] = field(default_factory=list)
    command_results: List[CommandResult] = field(default_factory=list)
    total_execution_time: float = 0.0
    output: str = ""
    error_message: str = ""
    connection_successful: bool = False
    configuration_applied: bool = False
    commit_check_passed: bool = False


@dataclass
class DeploymentPlan:
    """Deployment plan for universal framework"""
    deployment_id: str
    device_commands: Dict[str, List[str]] = field(default_factory=dict)
    execution_mode: ExecutionMode = ExecutionMode.COMMIT
    parallel_execution: bool = True
    validation_required: bool = True
    rollback_plan: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentResult:
    """Result of deployment operation"""
    deployment_id: str
    success: bool
    execution_results: Dict[str, ExecutionResult] = field(default_factory=dict)
    affected_devices: List[str] = field(default_factory=list)
    total_execution_time: float = 0.0
    commit_check_results: Dict[str, bool] = field(default_factory=dict)
    validation_results: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    deployment_time: Optional[datetime] = None


@dataclass
class DeviceConnection:
    """Managed device connection"""
    device_name: str
    device_info: DeviceInfo
    ssh_client: Any  # DNOSSSH instance
    connected: bool = False
    connection_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None


# Exception classes
class UniversalSSHException(Exception):
    """Base exception for universal SSH framework"""
    pass


class DeviceConnectionError(UniversalSSHException):
    """Error connecting to device"""
    pass


class CommandExecutionError(UniversalSSHException):
    """Error executing command"""
    pass


class DeploymentError(UniversalSSHException):
    """Error in deployment operation"""
    pass


class ValidationError(UniversalSSHException):
    """Error in validation"""
    pass


# Convenience functions
def create_deployment_plan(device_commands: Dict[str, List[str]], 
                          execution_mode: ExecutionMode = ExecutionMode.COMMIT) -> DeploymentPlan:
    """Create deployment plan from device commands"""
    
    import uuid
    
    return DeploymentPlan(
        deployment_id=str(uuid.uuid4())[:8],
        device_commands=device_commands,
        execution_mode=execution_mode,
        deployment_time=datetime.now()
    )


def create_execution_result(device_name: str, mode: ExecutionMode, 
                           success: bool = False) -> ExecutionResult:
    """Create execution result"""
    
    return ExecutionResult(
        device_name=device_name,
        success=success,
        execution_mode=mode
    )
