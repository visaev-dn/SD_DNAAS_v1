#!/usr/bin/env python3
"""
Universal SSH Deployment Framework

A unified, reliable SSH deployment framework that abstracts all SSH complexity
and provides consistent, proven deployment capabilities for all use cases.

Extracted from proven working systems:
- Interface Discovery SSH (6000+ interfaces discovered)
- BD-Builder Deployment (production-tested)
- DNOSSSH Core (DRIVENETS CLI expertise)
- SSH Push Menu (user experience patterns)
"""

from typing import Dict

# Core framework components
from .data_models import (
    ExecutionMode,
    ExecutionResult,
    DeploymentPlan,
    DeploymentResult,
    UniversalSSHException
)

from .device_manager import (
    UniversalDeviceManager,
    DeviceInfo,
    DeviceConnection
)

from .command_executor import (
    UniversalCommandExecutor,
    CommandResult
)

from .deployment_orchestrator import (
    UniversalDeploymentOrchestrator,
    deploy_with_universal_framework
)

__version__ = "1.0.0"
__author__ = "Lab Automation Framework"

# Framework status
def check_framework_health() -> Dict[str, bool]:
    """Check health of universal SSH framework components"""
    
    health_status = {}
    
    # Check DNOSSSH availability
    try:
        from utils.dnos_ssh import DNOSSSH
        health_status['dnosssh_core'] = True
    except ImportError:
        health_status['dnosssh_core'] = False
    
    # Check devices.yaml availability
    try:
        import os
        health_status['devices_yaml'] = os.path.exists('devices.yaml')
    except Exception:
        health_status['devices_yaml'] = False
    
    # Check interface discovery patterns
    try:
        from services.interface_discovery import SimpleInterfaceDiscovery
        health_status['interface_discovery_patterns'] = True
    except ImportError:
        health_status['interface_discovery_patterns'] = False
    
    return health_status

__all__ = [
    # Data models
    'ExecutionMode',
    'ExecutionResult',
    'DeploymentPlan',
    'DeploymentResult',
    'UniversalSSHException',
    'DeviceInfo',
    'DeviceConnection',
    'CommandResult',
    
    # Core components
    'UniversalDeviceManager',
    'UniversalCommandExecutor',
    'UniversalDeploymentOrchestrator',
    
    # Convenience functions
    'deploy_with_universal_framework',
    'check_framework_health'
]

# Framework health check
FRAMEWORK_HEALTH = check_framework_health()
FRAMEWORK_READY = all(FRAMEWORK_HEALTH.values())
