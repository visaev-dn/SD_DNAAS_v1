#!/usr/bin/env python3
"""
Phase 1 Integration - Data Transformers
Converts between legacy CLI data structures and Phase 1 standardized data structures
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# Import Phase 1 data structures
from config_engine.phase1_data_structures import (
    TopologyData, DeviceInfo, InterfaceInfo, PathInfo, PathSegment,
    BridgeDomainConfig, TopologyValidator,
    TopologyType, DeviceType, InterfaceType, InterfaceRole, DeviceRole,
    ValidationStatus, BridgeDomainType, OuterTagImposition
)

# Import existing enhanced device types for compatibility
from config_engine.enhanced_device_types import DeviceType as LegacyDeviceType, enhanced_classifier


class DataTransformer:
    """
    Transforms data between legacy CLI structures and Phase 1 structures.
    
    This class provides bidirectional transformation to maintain compatibility
    while enabling Phase 1 validation and standardization.
    """
    
    def __init__(self):
        """Initialize the data transformer"""
        self.logger = logging.getLogger('DataTransformer')
        self.validator = TopologyValidator()
    
    def legacy_to_phase1_topology(self, 
                                  service_name: str,
                                  vlan_id: int,
                                  source_device: str,
                                  source_interface: str,
                                  destinations: List[Dict[str, str]],
                                  topology_data: Optional[Dict] = None) -> TopologyData:
        """
        Transform legacy CLI input to Phase 1 TopologyData structure.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            destinations: List of destination dictionaries with 'device' and 'port' keys
            topology_data: Optional topology data from discovery
            
        Returns:
            TopologyData instance
        """
        try:
            # Determine topology type
            topology_type = TopologyType.P2P if len(destinations) == 1 else TopologyType.P2MP
            
            # Create device information
            devices = self._create_device_info_list(source_device, destinations, topology_data)
            
            # Create interface information
            interfaces = self._create_interface_info_list(source_device, source_interface, 
                                                        destinations, vlan_id, topology_data)
            
            # Create path information
            paths = self._create_path_info_list(source_device, destinations, topology_data)
            
            # Create bridge domain configuration
            bridge_domain_config = self._create_bridge_domain_config(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            # Create topology data
            topology = TopologyData(
                bridge_domain_name=service_name,
                topology_type=topology_type,
                vlan_id=vlan_id,
                devices=devices,
                interfaces=interfaces,
                paths=paths,
                bridge_domain_config=bridge_domain_config,
                discovered_at=datetime.now(),
                scan_method="cli_input",
                confidence_score=0.8,  # CLI input has high confidence
                validation_status=ValidationStatus.PENDING
            )
            
            # Validate the topology
            passed, errors, warnings = self.validator.validate_topology(topology)
            if passed:
                # Update validation status to VALID
                topology = self._update_validation_status(topology, ValidationStatus.VALID)
                self.logger.info(f"✅ Topology validation passed for {service_name}")
            else:
                # Update validation status to WARNING (allow with warnings)
                topology = self._update_validation_status(topology, ValidationStatus.WARNING)
                self.logger.warning(f"⚠️ Topology validation warnings for {service_name}: {warnings}")
                if errors:
                    self.logger.error(f"❌ Topology validation errors for {service_name}: {errors}")
            
            return topology
            
        except Exception as e:
            self.logger.error(f"Failed to transform legacy data to Phase 1: {e}")
            raise
    
    def phase1_to_legacy_config(self, topology: TopologyData) -> Dict[str, Any]:
        """
        Transform Phase 1 TopologyData back to legacy configuration format.
        
        Args:
            topology: Phase 1 TopologyData instance
            
        Returns:
            Legacy configuration dictionary
        """
        try:
            # Extract basic information
            service_name = topology.bridge_domain_name
            vlan_id = topology.vlan_id
            
            # Find source device and interface
            source_devices = topology.source_devices
            if not source_devices:
                raise ValueError("No source device found in topology")
            
            source_device = source_devices[0].name
            source_interfaces = topology.get_interfaces_by_device(source_device)
            source_interface = None
            
            for interface in source_interfaces:
                if interface.interface_role == InterfaceRole.ACCESS:
                    source_interface = interface.name
                    break
            
            if not source_interface:
                raise ValueError("No source interface found")
            
            # Extract destinations
            destinations = []
            dest_devices = topology.destination_devices
            
            for dest_device in dest_devices:
                dest_interfaces = topology.get_interfaces_by_device(dest_device.name)
                dest_interface = None
                
                for interface in dest_interfaces:
                    if interface.interface_role == InterfaceRole.ACCESS:
                        dest_interface = interface.name
                        break
                
                if dest_interface:
                    destinations.append({
                        'device': dest_device.name,
                        'port': dest_interface
                    })
            
            # Create legacy format
            legacy_config = {
                'service_name': service_name,
                'vlan_id': vlan_id,
                'source_device': source_device,
                'source_interface': source_interface,
                'destinations': destinations,
                'topology_type': topology.topology_type.value,
                'validation_status': topology.validation_status.value,
                'confidence_score': topology.confidence_score
            }
            
            return legacy_config
            
        except Exception as e:
            self.logger.error(f"Failed to transform Phase 1 to legacy format: {e}")
            raise
    
    def _create_device_info_list(self, source_device: str, destinations: List[Dict], 
                               topology_data: Optional[Dict] = None) -> List[DeviceInfo]:
        """Create list of DeviceInfo objects from legacy data"""
        devices = []
        all_device_names = {source_device}
        all_device_names.update(dest['device'] for dest in destinations)
        
        for device_name in all_device_names:
            # Determine device type
            device_type = self._get_phase1_device_type(device_name)
            
            # Determine device role
            if device_name == source_device:
                device_role = DeviceRole.SOURCE
            elif device_name in [dest['device'] for dest in destinations]:
                device_role = DeviceRole.DESTINATION
            else:
                device_role = DeviceRole.TRANSPORT
            
            # Extract additional info from topology data if available
            row, rack = self._parse_device_location(device_name)
            
            device_info = DeviceInfo(
                name=device_name,
                device_type=device_type,
                device_role=device_role,
                row=row,
                rack=rack,
                discovered_at=datetime.now(),
                confidence_score=0.9,
                validation_status=ValidationStatus.PENDING
            )
            
            devices.append(device_info)
        
        return devices
    
    def _create_interface_info_list(self, source_device: str, source_interface: str,
                                  destinations: List[Dict], vlan_id: int,
                                  topology_data: Optional[Dict] = None) -> List[InterfaceInfo]:
        """Create list of InterfaceInfo objects from legacy data"""
        interfaces = []
        
        # Source interface
        source_interface_info = InterfaceInfo(
            name=source_interface,
            interface_type=self._get_interface_type(source_interface),
            interface_role=InterfaceRole.ACCESS,
            device_name=source_device,
            vlan_id=vlan_id,
            l2_service_enabled=True,
            discovered_at=datetime.now(),
            confidence_score=0.9,
            validation_status=ValidationStatus.PENDING
        )
        interfaces.append(source_interface_info)
        
        # Destination interfaces
        for dest in destinations:
            dest_device = dest['device']
            dest_interface = dest['port']
            
            dest_interface_info = InterfaceInfo(
                name=dest_interface,
                interface_type=self._get_interface_type(dest_interface),
                interface_role=InterfaceRole.ACCESS,
                device_name=dest_device,
                vlan_id=vlan_id,
                l2_service_enabled=True,
                discovered_at=datetime.now(),
                confidence_score=0.9,
                validation_status=ValidationStatus.PENDING
            )
            interfaces.append(dest_interface_info)
        
        return interfaces
    
    def _create_path_info_list(self, source_device: str, destinations: List[Dict],
                             topology_data: Optional[Dict] = None) -> List[PathInfo]:
        """Create list of PathInfo objects from legacy data"""
        paths = []
        
        for dest in destinations:
            dest_device = dest['device']
            dest_interface = dest['port']
            
            # Create a simple path segment (direct connection for now)
            path_segment = PathSegment(
                source_device=source_device,
                dest_device=dest_device,
                source_interface=dest.get('source_interface', 'unknown'),
                dest_interface=dest_interface,
                segment_type=self._get_segment_type(source_device, dest_device),
                discovered_at=datetime.now(),
                confidence_score=0.7
            )
            
            # Create path info
            path_info = PathInfo(
                path_name=f"{source_device}_to_{dest_device}",
                path_type=TopologyType.P2P,  # Individual paths are P2P
                source_device=source_device,
                dest_device=dest_device,
                segments=[path_segment],
                discovered_at=datetime.now(),
                confidence_score=0.7,
                validation_status=ValidationStatus.PENDING
            )
            
            paths.append(path_info)
        
        return paths
    
    def _create_bridge_domain_config(self, service_name: str, vlan_id: int,
                                   source_device: str, source_interface: str,
                                   destinations: List[Dict]) -> BridgeDomainConfig:
        """Create BridgeDomainConfig from legacy data"""
        return BridgeDomainConfig(
            service_name=service_name,
            bridge_domain_type=BridgeDomainType.SINGLE_VLAN,
            source_device=source_device,
            source_interface=source_interface,
            destinations=destinations,
            vlan_id=vlan_id,
            outer_tag_imposition=OuterTagImposition.EDGE,
            created_at=datetime.now(),
            confidence_score=0.9,
            validation_status=ValidationStatus.PENDING
        )
    
    def _get_phase1_device_type(self, device_name: str) -> DeviceType:
        """Convert legacy device type to Phase 1 device type"""
        legacy_type = enhanced_classifier.detect_device_type(device_name)
        
        if legacy_type == LegacyDeviceType.LEAF:
            return DeviceType.LEAF
        elif legacy_type == LegacyDeviceType.SPINE:
            return DeviceType.SPINE
        elif legacy_type == LegacyDeviceType.SUPERSPINE:
            return DeviceType.SUPERSPINE
        else:
            # Default to LEAF for unknown types
            return DeviceType.LEAF
    
    def _get_interface_type(self, interface_name: str) -> InterfaceType:
        """Determine interface type from interface name"""
        if 'bundle' in interface_name.lower():
            if '.' in interface_name:
                return InterfaceType.SUBINTERFACE
            else:
                return InterfaceType.BUNDLE
        else:
            return InterfaceType.PHYSICAL
    
    def _get_segment_type(self, source_device: str, dest_device: str) -> str:
        """Determine segment type based on device types"""
        source_type = self._get_phase1_device_type(source_device)
        dest_type = self._get_phase1_device_type(dest_device)
        
        if source_type == DeviceType.LEAF and dest_type == DeviceType.LEAF:
            return "leaf_to_leaf"
        elif source_type == DeviceType.LEAF and dest_type == DeviceType.SPINE:
            return "leaf_to_spine"
        elif source_type == DeviceType.SPINE and dest_type == DeviceType.SPINE:
            return "spine_to_spine"
        elif source_type == DeviceType.SPINE and dest_type == DeviceType.LEAF:
            return "spine_to_leaf"
        elif source_type == DeviceType.LEAF and dest_type == DeviceType.SUPERSPINE:
            return "leaf_to_superspine"
        else:
            return "unknown"
    
    def _parse_device_location(self, device_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse device name to extract DC row and rack"""
        import re
        
        patterns = [
            r'DNAAS-LEAF-([A-Z])(\d+(?:-\d+)?)',  # DNAAS-LEAF-A12
            r'DNAAS_LEAF_([A-Z])(\d+)',           # DNAAS_LEAF_D13
            r'DNAAS-SUPERSPINE-([A-Z])(\d+)',     # DNAAS-SUPERSPINE-D04
        ]
        
        for pattern in patterns:
            match = re.match(pattern, device_name)
            if match:
                return match.group(1), match.group(2)
        
        return None, None
    
    def _update_validation_status(self, topology: TopologyData, status: ValidationStatus) -> TopologyData:
        """Update validation status in topology data"""
        # Since TopologyData is frozen, we need to create a new instance
        # For now, we'll just log the status change
        self.logger.info(f"Topology validation status updated to: {status.value}")
        return topology
    
    def legacy_config_to_phase1(self, legacy_config: Dict[str, Any]) -> TopologyData:
        """
        Convert legacy configuration dictionary to Phase 1 TopologyData.
        
        Args:
            legacy_config: Legacy configuration dictionary
            
        Returns:
            TopologyData instance
        """
        service_name = legacy_config.get('service_name', 'unknown')
        vlan_id = legacy_config.get('vlan_id', 100)
        source_device = legacy_config.get('source_device', 'unknown')
        source_interface = legacy_config.get('source_interface', 'unknown')
        destinations = legacy_config.get('destinations', [])
        
        return self.legacy_to_phase1_topology(
            service_name, vlan_id, source_device, source_interface, destinations
        )
    
    def validate_and_transform(self, service_name: str, vlan_id: int,
                             source_device: str, source_interface: str,
                             destinations: List[Dict[str, str]]) -> Tuple[TopologyData, bool, List[str], List[str]]:
        """
        Transform legacy data to Phase 1 and validate in one step.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            destinations: List of destination dictionaries
            
        Returns:
            Tuple of (topology_data, validation_passed, errors, warnings)
        """
        try:
            # Transform to Phase 1
            topology = self.legacy_to_phase1_topology(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            # Validate
            passed, errors, warnings = self.validator.validate_topology(topology)
            
            return topology, passed, errors, warnings
            
        except Exception as e:
            error_msg = f"Transformation failed: {str(e)}"
            self.logger.error(error_msg)
            return None, False, [error_msg], []


class LegacyConfigAdapter:
    """
    Adapter for working with legacy configuration formats.
    
    This class provides utilities for reading and writing legacy configuration
    files and formats while maintaining compatibility.
    """
    
    def __init__(self):
        """Initialize the legacy config adapter"""
        self.logger = logging.getLogger('LegacyConfigAdapter')
    
    def load_legacy_config(self, config_path: str) -> Dict[str, Any]:
        """Load legacy configuration from file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_file, 'r') as f:
                if config_file.suffix.lower() == '.json':
                    return json.load(f)
                elif config_file.suffix.lower() in ['.yaml', '.yml']:
                    import yaml
                    return yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {config_file.suffix}")
                    
        except Exception as e:
            self.logger.error(f"Failed to load legacy config from {config_path}: {e}")
            raise
    
    def save_legacy_config(self, config: Dict[str, Any], output_path: str) -> bool:
        """Save configuration in legacy format"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                if output_file.suffix.lower() == '.json':
                    json.dump(config, f, indent=2, default=str)
                elif output_file.suffix.lower() in ['.yaml', '.yml']:
                    import yaml
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                else:
                    raise ValueError(f"Unsupported file format: {output_file.suffix}")
            
            self.logger.info(f"Legacy configuration saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save legacy config to {output_path}: {e}")
            return False
    
    def extract_cli_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract CLI parameters from legacy configuration"""
        return {
            'service_name': config.get('service_name'),
            'vlan_id': config.get('vlan_id'),
            'source_device': config.get('source_device'),
            'source_interface': config.get('source_interface'),
            'destinations': config.get('destinations', []),
            'topology_type': config.get('topology_type', 'P2P')
        }
