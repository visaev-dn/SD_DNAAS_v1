#!/usr/bin/env python3
"""
Simplified Bridge Domain Discovery - Data Structures
==================================================

Standardized data structures for the 3-step simplified workflow.
These structures ensure consistent data flow and prevent the logic flaws
identified in the architectural analysis.

Architecture: 3-Step Simplified Workflow (ADR-001)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import uuid

# Import existing enums to maintain compatibility
from config_engine.phase1_data_structures.enums import (
    BridgeDomainType, 
    DeviceType, 
    ValidationStatus,
    BridgeDomainScope
)


# =============================================================================
# STEP 1: DATA LOADING & VALIDATION STRUCTURES
# =============================================================================

@dataclass
class RawBridgeDomain:
    """
    Raw bridge domain data from network discovery.
    Used in Step 1: Data Loading & Validation
    """
    name: str
    devices: List[str]
    interfaces: List[Dict[str, Any]]
    raw_config: Dict[str, Any]
    source_files: List[str] = field(default_factory=list)
    discovery_timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.name:
            raise ValueError("Bridge domain name is required")
        if not self.devices:
            raise ValueError("At least one device is required")
        if not self.interfaces:
            raise ValueError("At least one interface is required")


@dataclass
class ValidationResult:
    """
    Result of data quality validation.
    Used in Step 1: Data Loading & Validation
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    data_quality_score: float = 1.0  # 0.0 to 1.0
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)
        if self.data_quality_score > 0.8:
            self.data_quality_score = 0.8  # Reduce quality score for warnings


@dataclass 
class LoadedData:
    """
    Complete loaded data from Step 1.
    Contains all data needed for Step 2 processing.
    """
    bridge_domains: List[RawBridgeDomain]
    device_types: Dict[str, DeviceType]
    lldp_data: Dict[str, Dict[str, Any]]
    validation_results: Dict[str, ValidationResult]
    load_timestamp: datetime = field(default_factory=datetime.now)
    total_devices: int = 0
    total_interfaces: int = 0
    
    def __post_init__(self):
        """Calculate statistics"""
        all_devices = set()
        total_interfaces = 0
        
        for bd in self.bridge_domains:
            all_devices.update(bd.devices)
            total_interfaces += len(bd.interfaces)
        
        self.total_devices = len(all_devices)
        self.total_interfaces = total_interfaces


# =============================================================================
# STEP 2: BD-PROC PIPELINE STRUCTURES  
# =============================================================================

@dataclass
class VLANConfiguration:
    """
    Standardized VLAN configuration extracted from interface data.
    Used throughout BD-PROC pipeline.
    """
    vlan_id: Optional[int] = None
    outer_vlan: Optional[int] = None
    inner_vlan: Optional[int] = None
    vlan_range_start: Optional[int] = None
    vlan_range_end: Optional[int] = None
    vlan_list: List[int] = field(default_factory=list)
    vlan_manipulation: Optional[str] = None
    
    def has_single_vlan(self) -> bool:
        """Check if this is a single VLAN configuration"""
        return (self.vlan_id is not None and 
                self.outer_vlan is None and 
                self.inner_vlan is None and
                not self.vlan_list and
                self.vlan_range_start is None)
    
    def has_qinq_tags(self) -> bool:
        """Check if this has QinQ outer/inner tags"""
        return (self.outer_vlan is not None and 
                self.inner_vlan is not None and
                self.outer_vlan != self.inner_vlan)
    
    def has_vlan_manipulation(self) -> bool:
        """Check if this has VLAN manipulation (push/pop)"""
        return (self.vlan_manipulation is not None and
                ('push' in self.vlan_manipulation.lower() or 
                 'pop' in self.vlan_manipulation.lower()))


@dataclass
class InterfaceInfo:
    """
    Complete interface information after BD-PROC processing.
    Used in Step 2: BD-PROC Pipeline
    """
    name: str
    device_name: str
    vlan_config: VLANConfiguration
    interface_type: str = "unknown"  # physical, bundle, subinterface
    interface_role: str = "unknown"  # access, uplink, downlink, transport
    neighbor_device: Optional[str] = None
    raw_config: List[str] = field(default_factory=list)  # Raw CLI configuration commands
    neighbor_interface: Optional[str] = None
    admin_state: str = "unknown"
    role_assignment_method: str = "unknown"  # pattern, lldp, manual
    confidence: float = 1.0
    
    def is_physical_interface(self) -> bool:
        """Check if this is a physical interface"""
        return '.' not in self.name and not self.name.lower().startswith('bundle')
    
    def is_bundle_interface(self) -> bool:
        """Check if this is a bundle interface"""
        return self.name.lower().startswith('bundle')
    
    def is_subinterface(self) -> bool:
        """Check if this is a subinterface"""
        return '.' in self.name


@dataclass
class ProcessedBridgeDomain:
    """
    Complete bridge domain after BD-PROC pipeline processing.
    Used as output from Step 2: BD-PROC Pipeline
    """
    # Original data
    name: str
    devices: List[str]
    interfaces: List[InterfaceInfo]
    
    # BD-PROC results
    bridge_domain_type: BridgeDomainType
    global_identifier: Optional[Union[int, str]] = None
    username: Optional[str] = None
    bridge_domain_scope: BridgeDomainScope = BridgeDomainScope.UNSPECIFIED
    consolidation_key: Optional[str] = None
    can_consolidate: bool = False
    
    # Device and interface analysis
    device_types: Dict[str, DeviceType] = field(default_factory=dict)
    interface_roles: Dict[str, str] = field(default_factory=dict)
    
    # Processing metadata
    processing_timestamp: datetime = field(default_factory=datetime.now)
    processing_phase: str = "complete"
    confidence_score: float = 1.0
    validation_status: ValidationStatus = ValidationStatus.VALID
    processing_errors: List[str] = field(default_factory=list)
    processing_warnings: List[str] = field(default_factory=list)
    
    # Unique identifier
    bd_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def add_processing_error(self, error: str):
        """Add processing error"""
        self.processing_errors.append(error)
        self.validation_status = ValidationStatus.INVALID
        if self.confidence_score > 0.5:
            self.confidence_score = 0.5
    
    def add_processing_warning(self, warning: str):
        """Add processing warning"""
        self.processing_warnings.append(warning)
        self.validation_status = ValidationStatus.WARNING
        if self.confidence_score > 0.8:
            self.confidence_score = 0.8


# =============================================================================
# STEP 3: CONSOLIDATION & PERSISTENCE STRUCTURES
# =============================================================================

@dataclass
class ConsolidationGroup:
    """
    Group of bridge domains that can be consolidated together.
    Used in Step 3: Consolidation & Persistence
    """
    consolidation_key: str
    bridge_domains: List[ProcessedBridgeDomain]
    consolidation_method: str = "global_identifier"  # global_identifier, username, manual
    conflicts: List[str] = field(default_factory=list)
    can_merge_safely: bool = True
    
    def add_conflict(self, conflict: str):
        """Add consolidation conflict"""
        self.conflicts.append(conflict)
        self.can_merge_safely = False


@dataclass
class ConsolidatedBridgeDomain:
    """
    Final consolidated bridge domain result.
    Used as output from Step 3: Consolidation & Persistence
    """
    # Consolidated identity
    consolidated_name: str
    consolidation_key: str
    global_identifier: Optional[Union[int, str]]
    username: Optional[str]
    
    # Consolidated data
    all_devices: List[str]
    all_interfaces: List[InterfaceInfo]
    bridge_domain_type: BridgeDomainType
    bridge_domain_scope: BridgeDomainScope
    
    # Source bridge domains
    source_bridge_domains: List[str]  # Names of original BDs
    source_count: int = 0
    
    # Topology and paths
    topology_paths: List[Dict[str, Any]] = field(default_factory=list)
    network_topology: Dict[str, Any] = field(default_factory=dict)
    
    # Consolidation metadata
    consolidation_timestamp: datetime = field(default_factory=datetime.now)
    consolidation_method: str = "global_identifier"
    consolidation_confidence: float = 1.0
    consolidation_conflicts: List[str] = field(default_factory=list)
    
    # Final validation
    validation_status: ValidationStatus = ValidationStatus.VALID
    final_errors: List[str] = field(default_factory=list)
    final_warnings: List[str] = field(default_factory=list)
    
    # Unique identifier
    consolidated_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.source_count = len(self.source_bridge_domains)
        
        # Validate consolidation
        if not self.all_devices:
            self.final_errors.append("No devices in consolidated bridge domain")
            self.validation_status = ValidationStatus.INVALID
        
        if not self.all_interfaces:
            self.final_errors.append("No interfaces in consolidated bridge domain")
            self.validation_status = ValidationStatus.INVALID


@dataclass
class DiscoveryResults:
    """
    Complete discovery results from the 3-step workflow.
    Final output structure containing all results and statistics.
    """
    # Results
    consolidated_bridge_domains: List[ConsolidatedBridgeDomain]
    individual_bridge_domains: List[ProcessedBridgeDomain]  # BDs that couldn't be consolidated
    
    # Statistics
    total_bridge_domains_discovered: int = 0
    total_bridge_domains_processed: int = 0
    total_bridge_domains_consolidated: int = 0
    total_devices: int = 0
    total_interfaces: int = 0
    
    # Performance metrics
    discovery_start_time: datetime = field(default_factory=datetime.now)
    discovery_end_time: Optional[datetime] = None
    total_processing_time: Optional[float] = None
    
    # Quality metrics
    success_rate: float = 0.0
    classification_accuracy: float = 0.0
    consolidation_rate: float = 0.0
    
    # Error summary
    total_errors: int = 0
    total_warnings: int = 0
    error_summary: Dict[str, int] = field(default_factory=dict)
    
    # Session info
    discovery_session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def finalize_results(self):
        """Calculate final statistics and metrics"""
        self.discovery_end_time = datetime.now()
        if self.discovery_start_time:
            self.total_processing_time = (
                self.discovery_end_time - self.discovery_start_time
            ).total_seconds()
        
        # Calculate success rate
        total_attempted = self.total_bridge_domains_discovered
        total_successful = self.total_bridge_domains_processed
        if total_attempted > 0:
            self.success_rate = total_successful / total_attempted
        
        # Calculate consolidation rate
        total_final = len(self.consolidated_bridge_domains) + len(self.individual_bridge_domains)
        if self.total_bridge_domains_processed > 0:
            self.consolidation_rate = len(self.consolidated_bridge_domains) / self.total_bridge_domains_processed
        
        # Count errors and warnings
        for cbd in self.consolidated_bridge_domains:
            self.total_errors += len(cbd.final_errors)
            self.total_warnings += len(cbd.final_warnings)
        
        for ibd in self.individual_bridge_domains:
            self.total_errors += len(ibd.processing_errors)
            self.total_warnings += len(ibd.processing_warnings)


# =============================================================================
# ERROR HANDLING STRUCTURES
# =============================================================================

class DiscoveryError(Exception):
    """Base exception for all discovery errors"""
    pass

class DataQualityError(DiscoveryError):
    """Data validation and quality issues"""
    pass

class ClassificationError(DiscoveryError):
    """Bridge domain classification failures"""
    pass

class ConsolidationError(DiscoveryError):
    """Bridge domain consolidation failures"""
    pass

class WorkflowError(DiscoveryError):
    """Workflow and orchestration failures"""
    pass


# =============================================================================
# DATA VALIDATION HELPERS
# =============================================================================

def validate_data_flow_step1_to_step2(loaded_data: LoadedData) -> ValidationResult:
    """Validate data flow from Step 1 to Step 2"""
    result = ValidationResult(is_valid=True)
    
    if not loaded_data.bridge_domains:
        result.add_error("No bridge domains loaded for Step 2 processing")
    
    if not loaded_data.device_types:
        result.add_warning("No device types loaded - will use fallback classification")
    
    if not loaded_data.lldp_data:
        result.add_warning("No LLDP data loaded - will use pattern-based interface roles")
    
    # Validate each bridge domain has required data
    for bd in loaded_data.bridge_domains:
        if not bd.interfaces:
            result.add_error(f"Bridge domain {bd.name} has no interfaces")
        
        if not bd.devices:
            result.add_error(f"Bridge domain {bd.name} has no devices")
    
    return result


def validate_data_flow_step2_to_step3(processed_bds: List[ProcessedBridgeDomain]) -> ValidationResult:
    """Validate data flow from Step 2 to Step 3"""
    result = ValidationResult(is_valid=True)
    
    if not processed_bds:
        result.add_error("No processed bridge domains for Step 3 consolidation")
        return result
    
    # Check that required processing was completed
    for bd in processed_bds:
        if bd.bridge_domain_type == BridgeDomainType.SINGLE_VLAN:  # Default/error value
            result.add_warning(f"Bridge domain {bd.name} has default classification")
        
        if not bd.interfaces:
            result.add_error(f"Processed bridge domain {bd.name} has no interfaces")
        
        if bd.validation_status == ValidationStatus.INVALID:
            result.add_error(f"Bridge domain {bd.name} failed validation")
    
    return result


# =============================================================================
# GUIDED RAILS: DATA STRUCTURE CONTRACTS
# =============================================================================

def enforce_data_structure_contracts():
    """
    Enforce data structure contracts to prevent logic flaws.
    This function validates that our data structures follow the guided rails.
    """
    
    # Contract 1: Step 1 output must match Step 2 input
    step1_output_fields = set(LoadedData.__dataclass_fields__.keys())
    required_step2_input = {"bridge_domains", "device_types", "lldp_data"}
    
    if not required_step2_input.issubset(step1_output_fields):
        missing = required_step2_input - step1_output_fields
        raise WorkflowError(f"Step 1 output missing required fields for Step 2: {missing}")
    
    # Contract 2: Step 2 output must match Step 3 input
    step2_output = ProcessedBridgeDomain
    required_step3_fields = {"bridge_domain_type", "global_identifier", "consolidation_key"}
    step2_fields = set(step2_output.__dataclass_fields__.keys())
    
    if not required_step3_fields.issubset(step2_fields):
        missing = required_step3_fields - step2_fields
        raise WorkflowError(f"Step 2 output missing required fields for Step 3: {missing}")
    
    print("✅ All data structure contracts validated successfully")


if __name__ == "__main__":
    # Run contract validation
    enforce_data_structure_contracts()
    print("🎯 Data structures ready for 3-step simplified workflow")
