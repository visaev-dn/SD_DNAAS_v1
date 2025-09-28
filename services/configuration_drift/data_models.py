#!/usr/bin/env python3
"""
Configuration Drift Data Models

Data structures for configuration drift detection, resolution, and database sync.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class DriftType(Enum):
    """Types of configuration drift"""
    INTERFACE_ALREADY_CONFIGURED = "interface_already_configured"
    BRIDGE_DOMAIN_ALREADY_EXISTS = "bridge_domain_already_exists"
    VLAN_CONFLICT = "vlan_conflict"
    CONFIGURATION_MISMATCH = "configuration_mismatch"
    UNKNOWN_CONFIGURATION = "unknown_configuration"


class SyncAction(Enum):
    """Actions for resolving sync issues"""
    SKIP = "skip"              # Skip conflicting interfaces
    OVERRIDE = "override"      # Force reconfiguration
    SYNCED = "synced"         # Successfully synced database
    ABORT = "abort"           # Abort deployment
    FAILED = "failed"         # Sync operation failed


@dataclass
class DriftEvent:
    """Represents a configuration drift event"""
    drift_type: DriftType
    device_name: str
    interface_name: Optional[str] = None
    expected_config: Dict = field(default_factory=dict)
    actual_config: Dict = field(default_factory=dict)
    detection_source: str = ""  # commit-check, validation, discovery
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    severity: str = "medium"  # low, medium, high, critical
    resolution_options: List[str] = field(default_factory=list)


@dataclass
class InterfaceConfig:
    """Discovered interface configuration"""
    device_name: str
    interface_name: str
    vlan_id: Optional[int] = None
    admin_status: str = "unknown"
    oper_status: str = "unknown"
    interface_type: str = "unknown"
    description: str = ""
    l2_service_enabled: bool = False
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "targeted_discovery"
    raw_output: str = ""
    raw_cli_config: List[str] = field(default_factory=list)  # NEW: Store actual CLI commands


@dataclass
class BridgeDomainDiscoveryResult:
    """Complete bridge domain discovery result for database population"""
    
    # Bridge Domain Core Data
    bridge_domain_name: str
    username: Optional[str] = None              # Extracted from BD name
    vlan_id: Optional[int] = None              # Primary VLAN
    
    # Classification Data
    dnaas_type: Optional[str] = None           # DNAAS_TYPE_4A_SINGLE_TAGGED
    topology_type: Optional[str] = None        # p2mp, p2p
    bridge_domain_scope: str = "unknown"       # global, local
    
    # Interface Data
    interfaces: List[InterfaceConfig] = field(default_factory=list)
    devices: List[str] = field(default_factory=list)
    
    # Configuration Data
    configuration_data: Dict[str, Any] = field(default_factory=dict)
    raw_cli_config: List[str] = field(default_factory=list)
    interface_data: Dict[str, Any] = field(default_factory=dict)
    
    # Discovery Metadata
    discovery_metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    discovery_method: str = "targeted_drift_resolution"
    
    # Validation
    validation_status: str = "valid"
    confidence_score: float = 0.9
    success: bool = True
    error_message: Optional[str] = None


@dataclass
class SyncResolution:
    """Result of sync resolution"""
    action: SyncAction
    message: str
    discovered_configs: List[InterfaceConfig] = field(default_factory=list)
    sync_result: Optional['SyncResult'] = None
    user_choice: str = ""
    resolution_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SyncResult:
    """Result of database sync operation"""
    success: bool
    updated_count: int = 0
    added_count: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)
    total_processed: int = 0
    error_message: str = ""
    sync_duration: float = 0.0


@dataclass
class DeviceConfigSnapshot:
    """Complete device configuration snapshot"""
    device_name: str
    interface_configs: List[InterfaceConfig] = field(default_factory=list)
    bridge_domain_configs: List[Dict] = field(default_factory=list)
    snapshot_time: str = field(default_factory=lambda: datetime.now().isoformat())
    discovery_source: str = "targeted_discovery"
    total_interfaces: int = 0
    configured_interfaces: int = 0


@dataclass
class DriftAnalysis:
    """Analysis of configuration drift patterns"""
    total_drift_events: int = 0
    drift_by_type: Dict[DriftType, int] = field(default_factory=dict)
    drift_by_device: Dict[str, int] = field(default_factory=dict)
    resolution_by_action: Dict[SyncAction, int] = field(default_factory=dict)
    analysis_period: str = ""
    recommendations: List[str] = field(default_factory=list)


# Exception classes
class ConfigurationDriftException(Exception):
    """Base exception for configuration drift operations"""
    pass


class DriftDetectionError(ConfigurationDriftException):
    """Error in drift detection"""
    pass


class TargetedDiscoveryError(ConfigurationDriftException):
    """Error in targeted discovery"""
    pass


class SyncResolutionError(ConfigurationDriftException):
    """Error in sync resolution"""
    pass


class DatabaseSyncError(ConfigurationDriftException):
    """Error in database synchronization"""
    pass


# Convenience functions
def create_drift_event(drift_type: DriftType, device_name: str, 
                      interface_name: str = None, **kwargs) -> DriftEvent:
    """Create drift event with defaults"""
    
    return DriftEvent(
        drift_type=drift_type,
        device_name=device_name,
        interface_name=interface_name,
        **kwargs
    )


def create_interface_config(device_name: str, interface_name: str, 
                           vlan_id: int = None, **kwargs) -> InterfaceConfig:
    """Create interface config with defaults"""
    
    return InterfaceConfig(
        device_name=device_name,
        interface_name=interface_name,
        vlan_id=vlan_id,
        **kwargs
    )


def create_sync_result(success: bool, **kwargs) -> SyncResult:
    """Create sync result with defaults"""
    
    return SyncResult(
        success=success,
        **kwargs
    )
