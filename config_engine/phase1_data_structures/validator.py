#!/usr/bin/env python3
"""
Phase 1 Topology Data Validator
Defines comprehensive validation framework for topology data structures
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .enums import (
    TopologyType, DeviceType, InterfaceType, InterfaceRole, DeviceRole,
    ValidationStatus, BridgeDomainType, OuterTagImposition
)
from .topology_data import TopologyData
from .device_info import DeviceInfo
from .interface_info import InterfaceInfo
from .path_info import PathInfo, PathSegment
from .bridge_domain_config import BridgeDomainConfig


class TopologyValidator:
    """
    Comprehensive validator for Phase 1 topology data structures.
    
    This class provides validation at multiple levels:
    - Individual component validation
    - Cross-component consistency validation
    - Business rule validation
    - Topology constraint validation
    """
    
    def __init__(self):
        """Initialize the topology validator"""
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
        self.validation_passed: bool = False
    
    def validate_topology(self, topology_data: TopologyData) -> Tuple[bool, List[str], List[str]]:
        """
        Validate complete topology data structure.
        
        Args:
            topology_data: TopologyData instance to validate
            
        Returns:
            Tuple of (passed, errors, warnings)
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        try:
            # Component-level validation
            self._validate_devices(topology_data.devices)
            self._validate_interfaces(topology_data.interfaces)
            self._validate_paths(topology_data.paths)
            self._validate_bridge_domain_config(topology_data.bridge_domain_config)
            
            # Cross-component validation
            self._validate_device_interface_consistency(topology_data)
            self._validate_path_device_consistency(topology_data)
            self._validate_bridge_domain_device_consistency(topology_data)
            
            # Topology constraint validation
            self._validate_topology_constraints(topology_data)
            
            # Business rule validation
            self._validate_business_rules(topology_data)
            
            # Determine overall validation result
            self.validation_passed = len(self.validation_errors) == 0
            
            return self.validation_passed, self.validation_errors, self.validation_warnings
            
        except Exception as e:
            self.validation_errors.append(f"Validation failed with exception: {str(e)}")
            return False, self.validation_errors, self.validation_warnings
    
    def _validate_devices(self, devices: List[DeviceInfo]) -> None:
        """Validate device information"""
        if not devices:
            self.validation_errors.append("No devices found in topology")
            return
        
        device_names = set()
        for device in devices:
            # Check for duplicate device names
            if device.name in device_names:
                self.validation_errors.append(f"Duplicate device name: {device.name}")
            device_names.add(device.name)
            
            # Validate individual device
            self._validate_single_device(device)
    
    def _validate_single_device(self, device: DeviceInfo) -> None:
        """Validate a single device"""
        # Basic validation (already done in __post_init__, but double-check)
        if not device.name:
            self.validation_errors.append(f"Device has empty name")
        
        if device.confidence_score < 0.0 or device.confidence_score > 1.0:
            self.validation_errors.append(f"Device {device.name} has invalid confidence score: {device.confidence_score}")
        
        # Business rule validation
        if device.is_superspine and device.is_source:
            self.validation_errors.append(f"Superspine device {device.name} cannot be a source device")
        
        if device.is_leaf and device.is_transport:
            self.validation_errors.append(f"Leaf device {device.name} cannot be a transport device")
    
    def _validate_interfaces(self, interfaces: List[InterfaceInfo]) -> None:
        """Validate interface information"""
        if not interfaces:
            self.validation_errors.append("No interfaces found in topology")
            return
        
        interface_names = set()
        for interface in interfaces:
            # Check for duplicate interface names per device
            device_interface_key = f"{interface.device_name}:{interface.name}"
            if device_interface_key in interface_names:
                self.validation_errors.append(f"Duplicate interface {interface.name} on device {interface.device_name}")
            interface_names.add(device_interface_key)
            
            # Validate individual interface
            self._validate_single_interface(interface)
    
    def _validate_single_interface(self, interface: InterfaceInfo) -> None:
        """Validate a single interface"""
        # Basic validation
        if not interface.name:
            self.validation_errors.append(f"Interface has empty name on device {interface.device_name}")
        
        if not interface.device_name:
            self.validation_errors.append(f"Interface {interface.name} has no device association")
        
        if interface.confidence_score < 0.0 or interface.confidence_score > 1.0:
            self.validation_errors.append(f"Interface {interface.name} has invalid confidence score: {interface.confidence_score}")
        
        # VLAN validation
        if interface.vlan_id is not None:
            if not (1 <= interface.vlan_id <= 4094):
                self.validation_errors.append(f"Interface {interface.name} has invalid VLAN ID: {interface.vlan_id}")
        
        # Bundle validation
        if interface.bundle_id is not None:
            if not (1 <= interface.bundle_id <= 64):
                self.validation_errors.append(f"Interface {interface.name} has invalid bundle ID: {interface.bundle_id}")
        
        # Subinterface validation
        if interface.is_subinterface:
            if interface.bundle_id is None:
                self.validation_errors.append(f"Subinterface {interface.name} must have bundle ID")
            if interface.vlan_id is None:
                self.validation_warnings.append(f"Subinterface {interface.name} has no VLAN ID configured")
    
    def _validate_paths(self, paths: List[PathInfo]) -> None:
        """Validate path information"""
        if not paths:
            self.validation_errors.append("No paths found in topology")
            return
        
        path_names = set()
        for path in paths:
            # Check for duplicate path names
            if path.path_name in path_names:
                self.validation_errors.append(f"Duplicate path name: {path.path_name}")
            path_names.add(path.path_name)
            
            # Validate individual path
            self._validate_single_path(path)
    
    def _validate_single_path(self, path: PathInfo) -> None:
        """Validate a single path"""
        # Basic validation
        if not path.path_name:
            self.validation_errors.append("Path has empty name")
        
        if not path.segments:
            self.validation_errors.append(f"Path {path.path_name} has no segments")
            return
        
        # Validate path continuity
        self._validate_path_continuity(path)
        
        # Validate path segments
        for i, segment in enumerate(path.segments):
            self._validate_path_segment(segment, path.path_name, i)
    
    def _validate_path_continuity(self, path: PathInfo) -> None:
        """Validate that path segments form a continuous path"""
        segments = path.segments
        
        # First segment should start with source device
        if segments[0].source_device != path.source_device:
            self.validation_errors.append(
                f"Path {path.path_name}: First segment starts with {segments[0].source_device}, "
                f"but path source is {path.source_device}"
            )
        
        # Last segment should end with dest device
        if segments[-1].dest_device != path.dest_device:
            self.validation_errors.append(
                f"Path {path.path_name}: Last segment ends at {segments[-1].dest_device}, "
                f"but path destination is {path.dest_device}"
            )
        
        # Adjacent segments should connect
        for i in range(len(segments) - 1):
            current_segment = segments[i]
            next_segment = segments[i + 1]
            
            if current_segment.dest_device != next_segment.source_device:
                self.validation_errors.append(
                    f"Path {path.path_name}: Segment {i} ends at {current_segment.dest_device}, "
                    f"segment {i+1} starts at {next_segment.source_device}"
                )
    
    def _validate_path_segment(self, segment: PathSegment, path_name: str, segment_index: int) -> None:
        """Validate a single path segment"""
        # Basic validation
        if not segment.source_device:
            self.validation_errors.append(f"Path {path_name} segment {segment_index}: Missing source device")
        
        if not segment.dest_device:
            self.validation_errors.append(f"Path {path_name} segment {segment_index}: Missing destination device")
        
        if not segment.source_interface:
            self.validation_errors.append(f"Path {path_name} segment {segment_index}: Missing source interface")
        
        if not segment.dest_interface:
            self.validation_errors.append(f"Path {path_name} segment {segment_index}: Missing destination interface")
        
        if not segment.segment_type:
            self.validation_errors.append(f"Path {path_name} segment {segment_index}: Missing segment type")
        
        # Bundle validation
        if segment.bundle_id is not None:
            if not (1 <= segment.bundle_id <= 64):
                self.validation_errors.append(f"Path {path_name} segment {segment_index}: Invalid bundle ID {segment.bundle_id}")
    
    def _validate_bridge_domain_config(self, config: BridgeDomainConfig) -> None:
        """Validate bridge domain configuration"""
        # Basic validation
        if not config.service_name:
            self.validation_errors.append("Bridge domain configuration has empty service name")
        
        if not config.source_device:
            self.validation_errors.append("Bridge domain configuration has empty source device")
        
        if not config.source_interface:
            self.validation_errors.append("Bridge domain configuration has empty source interface")
        
        if not config.destinations:
            self.validation_errors.append("Bridge domain configuration has no destinations")
        
        # VLAN validation based on type
        self._validate_bridge_domain_vlans(config)
        
        # Destination validation
        self._validate_bridge_domain_destinations(config)
    
    def _validate_bridge_domain_vlans(self, config: BridgeDomainConfig) -> None:
        """Validate VLAN configuration based on bridge domain type"""
        if config.is_single_vlan:
            if config.vlan_id is None:
                self.validation_errors.append("Single VLAN bridge domain must have VLAN ID")
            elif not (1 <= config.vlan_id <= 4094):
                self.validation_errors.append(f"Single VLAN bridge domain has invalid VLAN ID: {config.vlan_id}")
        
        elif config.is_vlan_range:
            if config.vlan_start is None or config.vlan_end is None:
                self.validation_errors.append("VLAN range bridge domain must have start and end VLAN IDs")
            elif not (1 <= config.vlan_start <= 4094) or not (1 <= config.vlan_end <= 4094):
                self.validation_errors.append(f"VLAN range has invalid values: {config.vlan_start}-{config.vlan_end}")
            elif config.vlan_start >= config.vlan_end:
                self.validation_errors.append(f"VLAN start {config.vlan_start} must be less than VLAN end {config.vlan_end}")
        
        elif config.is_vlan_list:
            if not config.vlan_list:
                self.validation_errors.append("VLAN list bridge domain must have VLAN list")
            else:
                for vlan_id in config.vlan_list:
                    if not (1 <= vlan_id <= 4094):
                        self.validation_errors.append(f"VLAN list contains invalid VLAN ID: {vlan_id}")
        
        elif config.is_qinq:
            if config.outer_vlan is None or config.inner_vlan is None:
                self.validation_errors.append("QinQ bridge domain must have outer and inner VLAN IDs")
            elif not (1 <= config.outer_vlan <= 4094) or not (1 <= config.inner_vlan <= 4094):
                self.validation_errors.append(f"QinQ has invalid VLAN IDs: outer={config.outer_vlan}, inner={config.inner_vlan}")
    
    def _validate_bridge_domain_destinations(self, config: BridgeDomainConfig) -> None:
        """Validate destination configuration"""
        for i, dest in enumerate(config.destinations):
            if not isinstance(dest, dict):
                self.validation_errors.append(f"Destination {i} is not a dictionary")
                continue
            
            if 'device' not in dest:
                self.validation_errors.append(f"Destination {i} missing 'device' key")
            elif not dest['device']:
                self.validation_errors.append(f"Destination {i} has empty device name")
            
            if 'port' not in dest:
                self.validation_errors.append(f"Destination {i} missing 'port' key")
            elif not dest['port']:
                self.validation_errors.append(f"Destination {i} has empty port name")
    
    def _validate_device_interface_consistency(self, topology_data: TopologyData) -> None:
        """Validate consistency between devices and interfaces"""
        device_names = {device.name for device in topology_data.devices}
        
        for interface in topology_data.interfaces:
            if interface.device_name not in device_names:
                self.validation_errors.append(
                    f"Interface {interface.name} references unknown device {interface.device_name}"
                )
    
    def _validate_path_device_consistency(self, topology_data: TopologyData) -> None:
        """Validate consistency between paths and devices"""
        device_names = {device.name for device in topology_data.devices}
        
        for path in topology_data.paths:
            if path.source_device not in device_names:
                self.validation_errors.append(
                    f"Path {path.path_name} references unknown source device {path.source_device}"
                )
            
            if path.dest_device not in device_names:
                self.validation_errors.append(
                    f"Path {path.path_name} references unknown destination device {path.dest_device}"
                )
            
            # Check all devices in path segments
            for segment in path.segments:
                if segment.source_device not in device_names:
                    self.validation_errors.append(
                        f"Path {path.path_name} segment references unknown source device {segment.source_device}"
                    )
                
                if segment.dest_device not in device_names:
                    self.validation_errors.append(
                        f"Path {path.path_name} segment references unknown destination device {segment.dest_device}"
                    )
    
    def _validate_bridge_domain_device_consistency(self, topology_data: TopologyData) -> None:
        """Validate consistency between bridge domain config and devices"""
        device_names = {device.name for device in topology_data.devices}
        config = topology_data.bridge_domain_config
        
        if config.source_device not in device_names:
            self.validation_errors.append(
                f"Bridge domain config references unknown source device {config.source_device}"
            )
        
        for dest in config.destinations:
            if dest['device'] not in device_names:
                self.validation_errors.append(
                    f"Bridge domain config references unknown destination device {dest['device']}"
                )
    
    def _validate_topology_constraints(self, topology_data: TopologyData) -> None:
        """Validate topology-specific constraints"""
        # Check for valid P2P topology
        if topology_data.is_p2p:
            if len(topology_data.paths) != 1:
                self.validation_warnings.append("P2P topology should have exactly one path")
            
            if topology_data.bridge_domain_config.destination_count != 1:
                self.validation_errors.append("P2P topology must have exactly one destination")
        
        # Check for valid P2MP topology
        if topology_data.is_p2mp:
            if topology_data.bridge_domain_config.destination_count < 2:
                self.validation_errors.append("P2MP topology must have at least two destinations")
            
            if len(topology_data.paths) < 2:
                self.validation_warnings.append("P2MP topology should have multiple paths")
        
        # Check device type constraints
        source_devices = topology_data.source_devices
        if len(source_devices) != 1:
            self.validation_errors.append(f"Topology must have exactly one source device, found {len(source_devices)}")
        
        # Check for superspine constraints
        superspine_devices = topology_data.superspine_devices
        for device in superspine_devices:
            if device.is_source:
                self.validation_errors.append(f"Superspine device {device.name} cannot be a source device")
    
    def _validate_business_rules(self, topology_data: TopologyData) -> None:
        """Validate business-specific rules and constraints"""
        # Check VLAN ID consistency
        if topology_data.vlan_id is not None:
            config = topology_data.bridge_domain_config
            
            if config.is_single_vlan and config.vlan_id != topology_data.vlan_id:
                self.validation_errors.append(
                    f"Topology VLAN ID {topology_data.vlan_id} doesn't match bridge domain VLAN ID {config.vlan_id}"
                )
        
        # Check interface configuration consistency
        configured_interfaces = topology_data.configured_interfaces
        if configured_interfaces:
            vlan_ids = {interface.vlan_id for interface in configured_interfaces if interface.vlan_id is not None}
            if len(vlan_ids) > 1:
                self.validation_warnings.append(f"Multiple VLAN IDs found in configured interfaces: {vlan_ids}")
        
        # Check for redundant paths
        redundant_paths = [path for path in topology_data.paths if path.is_redundant]
        if redundant_paths:
            self.validation_warnings.append(f"Found {len(redundant_paths)} redundant paths")
    
    def get_validation_summary(self) -> str:
        """Get human-readable validation summary"""
        if self.validation_passed:
            return f"✅ Validation PASSED - {len(self.validation_warnings)} warnings"
        else:
            return f"❌ Validation FAILED - {len(self.validation_errors)} errors, {len(self.validation_warnings)} warnings"
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report"""
        return {
            'passed': self.validation_passed,
            'error_count': len(self.validation_errors),
            'warning_count': len(self.validation_warnings),
            'errors': self.validation_errors.copy(),
            'warnings': self.validation_warnings.copy(),
            'summary': self.get_validation_summary()
        }

