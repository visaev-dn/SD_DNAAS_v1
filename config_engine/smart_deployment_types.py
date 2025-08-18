#!/usr/bin/env python3
"""
Smart Deployment Types
Shared dataclasses and enums for the smart deployment system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

class DeploymentStrategy(Enum):
    """Deployment strategy enumeration"""
    CONSERVATIVE = "conservative"  # Sequential, validated steps
    AGGRESSIVE = "aggressive"      # Parallel deployment

class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class DeviceChange:
    """Represents a change to a device configuration"""
    device_name: str
    change_type: str  # 'add', 'modify', 'remove'
    old_commands: List[str]
    new_commands: List[str]
    affected_interfaces: List[str]
    vlan_changes: List[Dict]

@dataclass
class VlanChange:
    """Represents a VLAN configuration change"""
    vlan_id: int
    change_type: str  # 'add', 'modify', 'remove'
    affected_devices: List[str]
    old_config: Dict
    new_config: Dict

@dataclass
class ImpactAssessment:
    """Assessment of deployment impact"""
    affected_device_count: int
    estimated_duration: int  # seconds
    risk_level: RiskLevel
    potential_conflicts: List[str]
    rollback_complexity: str

@dataclass
class DeploymentDiff:
    """Complete diff between current and new configurations"""
    devices_to_add: List[DeviceChange]
    devices_to_modify: List[DeviceChange]
    devices_to_remove: List[DeviceChange]
    unchanged_devices: List[str]
    vlan_changes: List[VlanChange]
    estimated_impact: ImpactAssessment

@dataclass
class ExecutionGroup:
    """Group of operations to execute together"""
    group_id: str
    operations: List[Dict]
    dependencies: List[str]
    estimated_duration: int
    can_parallel: bool

@dataclass
class RollbackConfig:
    """Rollback configuration for deployment"""
    deployment_id: str
    original_config_id: int
    rollback_commands: List[str]
    created_at: str  # ISO format string
    commands: Optional[Dict[str, List[str]]] = None  # device -> commands (legacy)
    metadata: Optional[Dict] = None  # legacy

@dataclass
class ValidationStep:
    """Validation step definition"""
    step_id: str
    name: str
    description: str
    validation_type: str  # 'pre', 'during', 'post'
    required: bool

@dataclass
class DeploymentPlan:
    """Complete deployment plan"""
    deployment_id: str
    strategy: DeploymentStrategy
    execution_groups: List[ExecutionGroup]
    rollback_config: RollbackConfig
    estimated_duration: int
    risk_level: RiskLevel
    validation_steps: List[ValidationStep]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'deployment_id': self.deployment_id,
            'strategy': self.strategy.value,
            'estimated_duration': self.estimated_duration,
            'risk_level': self.risk_level.value,
            'validation_steps': [
                {
                    'step_id': step.step_id,
                    'name': step.name,
                    'description': step.description,
                    'validation_type': step.validation_type,
                    'required': step.required
                } for step in self.validation_steps
            ],
            'execution_groups': [
                {
                    'group_id': group.group_id,
                    'operations': group.operations,
                    'dependencies': group.dependencies,
                    'estimated_duration': group.estimated_duration,
                    'can_parallel': group.can_parallel
                } for group in self.execution_groups
            ]
        }

@dataclass
class DeploymentResult:
    """Result of deployment execution"""
    success: bool
    deployed_devices: List[str]
    failed_devices: List[str]
    logs: List[str]
    errors: List[str]
    duration: int
    rollback_available: bool
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    devices_processed: Optional[int] = None
    validation_results: Optional[List['ValidationResult']] = None

@dataclass
class ValidationResult:
    """Result of deployment validation"""
    valid: bool
    issues: List[str]
    warnings: List[str]
    recommendations: List[str] 