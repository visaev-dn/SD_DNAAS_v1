#!/usr/bin/env python3
"""
Service Interfaces Package
Exports all service interface classes for easy importing
"""

from .bridge_domain_service import (
    BridgeDomainService,
    BridgeDomainConfig,
    BridgeDomainResult
)

from .topology_service import (
    TopologyService,
    TopologyNode,
    TopologyLink,
    TopologyScanResult
)

from .ssh_service import (
    SSHService,
    SSHConnectionConfig,
    SSHCommandResult,
    SSHConfigPushResult
)

from .discovery_service import (
    DiscoveryService,
    DiscoveryTarget,
    DiscoveryResult,
    DeviceInfo
)

from .user_workflow_service import (
    UserWorkflowService,
    WorkflowStep,
    WorkflowDefinition,
    WorkflowExecutionResult
)

__all__ = [
    # Bridge Domain Service
    'BridgeDomainService',
    'BridgeDomainConfig',
    'BridgeDomainResult',
    
    # Topology Service
    'TopologyService',
    'TopologyNode',
    'TopologyLink',
    'TopologyScanResult',
    
    # SSH Service
    'SSHService',
    'SSHConnectionConfig',
    'SSHCommandResult',
    'SSHConfigPushResult',
    
    # Discovery Service
    'DiscoveryService',
    'DiscoveryTarget',
    'DiscoveryResult',
    'DeviceInfo',
    
    # User Workflow Service
    'UserWorkflowService',
    'WorkflowStep',
    'WorkflowDefinition',
    'WorkflowExecutionResult',
]
