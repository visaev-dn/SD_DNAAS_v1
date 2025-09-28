#!/usr/bin/env python3
"""
BD Editor Data Models & Core Structures

Comprehensive data models for intelligent BD editor system including
validation results, interface analysis, impact analysis, and error handling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
from enum import Enum


class BDEditingComplexity(Enum):
    """BD editing complexity levels"""
    SIMPLE = "simple"      # Type 4A: Single-Tagged (73.3% of BDs)
    ADVANCED = "advanced"  # Type 2A: QinQ Single BD (21.0% of BDs)
    EXPERT = "expert"      # Type 1: Double-Tagged (3.2% of BDs)
    SPECIALIZED = "specialized"  # Other types (2.5% of BDs)


@dataclass
class ValidationResult:
    """Result of validation operations"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
        
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result"""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


@dataclass
class InterfaceAnalysis:
    """Analysis of BD interfaces for editability"""
    customer_editable: List[Dict] = field(default_factory=list)
    infrastructure_readonly: List[Dict] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate summary statistics"""
        total = len(self.customer_editable) + len(self.infrastructure_readonly)
        self.summary = {
            "total_interfaces": total,
            "customer_count": len(self.customer_editable),
            "infrastructure_count": len(self.infrastructure_readonly),
            "editability_percentage": (len(self.customer_editable) / max(1, total)) * 100
        }


@dataclass
class ImpactAnalysis:
    """Analysis of change impact on network and services"""
    customer_interfaces_affected: int = 0
    affected_devices: Set[str] = field(default_factory=set)
    services_impacted: List[str] = field(default_factory=list)
    estimated_downtime: str = "Unknown"
    warnings: List[str] = field(default_factory=list)
    
    def merge(self, other: 'ImpactAnalysis'):
        """Merge another impact analysis"""
        self.customer_interfaces_affected += other.customer_interfaces_affected
        self.affected_devices.update(other.affected_devices)
        self.services_impacted.extend(other.services_impacted)
        self.warnings.extend(other.warnings)


@dataclass
class PreviewReport:
    """Complete configuration preview report"""
    changes: List[Dict] = field(default_factory=list)
    commands_by_device: Dict[str, List[str]] = field(default_factory=dict)
    affected_devices: Set[str] = field(default_factory=set)
    all_commands: List[str] = field(default_factory=list)
    impact_analysis: Optional[ImpactAnalysis] = None
    validation_result: Optional[ValidationResult] = None
    errors: List[str] = field(default_factory=list)
    
    def add_change_commands(self, change: Dict, commands: List[str]):
        """Add commands for a specific change"""
        device = change.get('interface', {}).get('device', 'unknown')
        if device not in self.commands_by_device:
            self.commands_by_device[device] = []
        self.commands_by_device[device].extend(commands)
        self.all_commands.extend(commands)
        self.affected_devices.add(device)
        
    def add_error(self, change: Dict, error: str):
        """Add error for a specific change"""
        self.errors.append(f"Change {change.get('description', 'unknown')}: {error}")


@dataclass
class HealthReport:
    """BD health check report"""
    is_healthy: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add health check error"""
        self.errors.append(error)
        self.is_healthy = False
        
    def add_warning(self, warning: str):
        """Add health check warning"""
        self.warnings.append(warning)
        
    def add_recommendation(self, recommendation: str):
        """Add health check recommendation"""
        self.recommendations.append(recommendation)
        
    def has_errors(self) -> bool:
        """Check if health report has errors"""
        return len(self.errors) > 0
        
    def merge(self, other: 'HealthReport'):
        """Merge another health report"""
        if not other.is_healthy:
            self.is_healthy = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.recommendations.extend(other.recommendations)


@dataclass
class DeploymentResult:
    """Result of BD deployment operation"""
    success: bool
    affected_devices: List[str] = field(default_factory=list)
    commands_executed: Dict[str, List[str]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    deployment_time: Optional[datetime] = None


@dataclass
class DeviceDeploymentResult:
    """Result of deployment to specific device"""
    device: str
    success: bool
    commands_executed: List[str] = field(default_factory=list)
    output: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class BDTypeProfile:
    """Profile for a specific BD type with editing characteristics"""
    dnaas_type: str
    complexity: BDEditingComplexity
    common_name: str
    description: str
    percentage: float
    interface_config_pattern: str
    editing_tips: List[str]
    validation_rules: List[str]


# Exception Classes
class BDEditorException(Exception):
    """Base exception for BD editor operations"""
    pass


class BDDataRetrievalError(BDEditorException):
    """Error retrieving BD data from database"""
    pass


class IntegrationFailureError(BDEditorException):
    """Error with external system integration"""
    pass


class CriticalIntegrationError(BDEditorException):
    """Critical integration failure that prevents operation"""
    pass


class BDEditorExitException(BDEditorException):
    """User chose to exit BD editor"""
    pass


class ValidationError(BDEditorException):
    """Configuration validation failed"""
    pass


class ConfigurationError(BDEditorException):
    """Error in configuration generation or processing"""
    pass


class DeploymentError(BDEditorException):
    """Error during deployment to network devices"""
    pass


class SessionError(BDEditorException):
    """Error in session management"""
    pass


class PerformanceError(BDEditorException):
    """Performance requirement violation"""
    pass
