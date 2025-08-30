#!/usr/bin/env python3
"""
Phase 1 Data Serializer
Handles serialization and deserialization of Phase 1 data structures
"""

import json
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path

# Import Phase 1 data structures
from config_engine.phase1_data_structures import (
    TopologyData, DeviceInfo, InterfaceInfo, PathInfo, PathSegment,
    BridgeDomainConfig, TopologyType, DeviceType, InterfaceType, 
    InterfaceRole, DeviceRole, ValidationStatus, BridgeDomainType, OuterTagImposition
)

logger = logging.getLogger(__name__)


class Phase1DataSerializer:
    """
    Phase 1 Data Serializer for handling data format conversions.
    
    This serializer provides:
    1. JSON serialization/deserialization
    2. YAML serialization/deserialization
    3. Legacy format compatibility
    4. Data validation during serialization
    """
    
    def __init__(self):
        """Initialize Phase 1 data serializer"""
        self.logger = logger
        
        # Custom JSON encoder for datetime objects
        self.json_encoder = self._create_json_encoder()
        
        self.logger.info("🚀 Phase 1 Data Serializer initialized")
    
    def _create_json_encoder(self):
        """Create custom JSON encoder for datetime objects"""
        class DateTimeEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return super().default(obj)
        
        return DateTimeEncoder
    
    def serialize_topology(self, topology_data: TopologyData, format: str = 'json') -> Optional[str]:
        """
        Serialize Phase 1 topology data to specified format.
        
        Args:
            topology_data: Phase 1 TopologyData object
            format: Output format ('json', 'yaml')
            
        Returns:
            Serialized data as string, None if failed
        """
        try:
            # Convert to dictionary first
            data_dict = topology_data.to_dict()
            
            if format.lower() == 'json':
                return json.dumps(data_dict, indent=2, cls=self.json_encoder)
            elif format.lower() == 'yaml':
                return yaml.dump(data_dict, default_flow_style=False, indent=2)
            else:
                self.logger.error(f"❌ Unsupported serialization format: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Serialization failed: {e}")
            return None
    
    def deserialize_topology(self, data: str, format: str = 'json') -> Optional[TopologyData]:
        """
        Deserialize data to Phase 1 TopologyData object.
        
        Args:
            data: Serialized data string
            format: Input format ('json', 'yaml')
            
        Returns:
            TopologyData object if successful, None otherwise
        """
        try:
            if format.lower() == 'json':
                data_dict = json.loads(data)
            elif format.lower() == 'yaml':
                data_dict = yaml.safe_load(data)
            else:
                self.logger.error(f"❌ Unsupported deserialization format: {format}")
                return None
            
            # Convert dictionary to TopologyData object
            return TopologyData.from_dict(data_dict)
            
        except Exception as e:
            self.logger.error(f"❌ Deserialization failed: {e}")
            return None
    
    def serialize_to_legacy_format(self, topology_data: TopologyData) -> Dict[str, Any]:
        """
        Serialize Phase 1 topology data to legacy format for compatibility.
        
        Args:
            topology_data: Phase 1 TopologyData object
            
        Returns:
            Legacy format dictionary
        """
        try:
            # Extract basic information
            legacy_config = {
                'service_name': topology_data.bridge_domain_name,
                'vlan_id': topology_data.vlan_id,
                'topology_type': topology_data.topology_type.value,
                'source_device': topology_data.source_devices[0].name if topology_data.source_devices else 'unknown',
                'source_interface': 'unknown',  # Will be filled from interfaces
                'destinations': [],
                'devices': {},
                'interfaces': {},
                'paths': {},
                'metadata': {
                    'phase1_version': '1.0.0',
                    'validation_status': topology_data.validation_status.value,
                    'confidence_score': topology_data.confidence_score,
                    'discovered_at': topology_data.discovered_at.isoformat() if topology_data.discovered_at else None,
                    'scan_method': topology_data.scan_method
                }
            }
            
            # Extract source interface
            source_devices = topology_data.source_devices
            if source_devices:
                source_device = source_devices[0]
                source_interfaces = topology_data.get_interfaces_by_device(source_device.name)
                for interface in source_interfaces:
                    if interface.interface_role == InterfaceRole.ACCESS:
                        legacy_config['source_interface'] = interface.name
                        break
            
            # Extract destinations
            dest_devices = topology_data.destination_devices
            for dest_device in dest_devices:
                dest_interfaces = topology_data.get_interfaces_by_device(dest_device.name)
                dest_interface = 'unknown'
                for interface in dest_interfaces:
                    if interface.interface_role == InterfaceRole.ACCESS:
                        dest_interface = interface.name
                        break
                
                legacy_config['destinations'].append({
                    'device': dest_device.name,
                    'port': dest_interface
                })
            
            # Extract device information
            for device in topology_data.devices:
                legacy_config['devices'][device.name] = {
                    'device_type': device.device_type.value,
                    'device_role': device.device_role.value,
                    'row': device.row,
                    'rack': device.rack,
                    'model': getattr(device, 'model', None),
                    'serial_number': getattr(device, 'serial_number', None),
                    'confidence_score': device.confidence_score,
                    'validation_status': device.validation_status.value
                }
            
            # Extract interface information
            for interface in topology_data.interfaces:
                legacy_config['interfaces'][interface.name] = {
                    'device_name': interface.device_name,
                    'interface_type': interface.interface_type.value,
                    'interface_role': interface.interface_role.value,
                    'vlan_id': interface.vlan_id,
                    'l2_service_enabled': interface.l2_service_enabled,
                    'outer_tag_imposition': getattr(interface, 'outer_tag_imposition', None),
                    'confidence_score': interface.confidence_score,
                    'validation_status': interface.validation_status.value
                }
            
            # Extract path information
            for path in topology_data.paths:
                legacy_config['paths'][path.path_name] = {
                    'path_type': path.path_type.value,
                    'source_device': path.source_device,
                    'dest_device': path.dest_device,
                    'segments': [segment.to_dict() for segment in path.segments],
                    'confidence_score': path.confidence_score,
                    'validation_status': path.validation_status.value
                }
            
            return legacy_config
            
        except Exception as e:
            self.logger.error(f"❌ Legacy serialization failed: {e}")
            return {}
    
    def deserialize_from_legacy_format(self, legacy_config: Dict[str, Any]) -> Optional[TopologyData]:
        """
        Deserialize legacy format data to Phase 1 TopologyData object.
        
        Args:
            legacy_config: Legacy configuration dictionary
            
        Returns:
            TopologyData object if successful, None otherwise
        """
        try:
            # Extract basic information
            service_name = legacy_config.get('service_name', 'unknown')
            vlan_id = legacy_config.get('vlan_id')
            topology_type = legacy_config.get('topology_type', 'p2p')
            source_device = legacy_config.get('source_device', 'unknown')
            source_interface = legacy_config.get('source_interface', 'unknown')
            destinations = legacy_config.get('destinations', [])
            
            # Create devices
            devices = []
            devices_data = legacy_config.get('devices', {})
            
            for device_name, device_info in devices_data.items():
                device = DeviceInfo(
                    name=device_name,
                    device_type=DeviceType(device_info.get('device_type', 'leaf')),
                    device_role=DeviceRole(device_info.get('device_role', 'source')),
                    row=device_info.get('row'),
                    rack=device_info.get('rack'),
                    model=device_info.get('model'),
                    serial_number=device_info.get('serial_number'),
                    discovered_at=datetime.now(),
                    confidence_score=device_info.get('confidence_score', 0.0),
                    validation_status=ValidationStatus(device_info.get('validation_status', 'pending'))
                )
                devices.append(device)
            
            # Create interfaces
            interfaces = []
            interfaces_data = legacy_config.get('interfaces', {})
            
            for interface_name, interface_info in interfaces_data.items():
                interface = InterfaceInfo(
                    name=interface_name,
                    interface_type=InterfaceType(interface_info.get('interface_type', 'physical')),
                    interface_role=InterfaceRole(interface_info.get('interface_role', 'access')),
                    device_name=interface_info.get('device_name', 'unknown'),
                    vlan_id=interface_info.get('vlan_id'),
                    l2_service_enabled=interface_info.get('l2_service_enabled', False),
                    outer_tag_imposition=OuterTagImposition(interface_info.get('outer_tag_imposition')) if interface_info.get('outer_tag_imposition') else None,
                    discovered_at=datetime.now(),
                    confidence_score=interface_info.get('confidence_score', 0.0),
                    validation_status=ValidationStatus(interface_info.get('validation_status', 'pending'))
                )
                interfaces.append(interface)
            
            # Create paths
            paths = []
            paths_data = legacy_config.get('paths', {})
            
            for path_name, path_info in paths_data.items():
                # Create path segments
                segments = []
                for segment_data in path_info.get('segments', []):
                    segment = PathSegment(
                        source_device=segment_data.get('source_device', 'unknown'),
                        dest_device=segment_data.get('dest_device', 'unknown'),
                        source_interface=segment_data.get('source_interface', 'unknown'),
                        dest_interface=segment_data.get('dest_interface', 'unknown'),
                        segment_type=segment_data.get('segment_type', 'unknown'),
                        connection_type=segment_data.get('connection_type', 'direct'),
                        discovered_at=datetime.now(),
                        confidence_score=segment_data.get('confidence_score', 0.0)
                    )
                    segments.append(segment)
                
                path = PathInfo(
                    path_name=path_name,
                    path_type=TopologyType(path_info.get('path_type', 'p2p')),
                    source_device=path_info.get('source_device', 'unknown'),
                    dest_device=path_info.get('dest_device', 'unknown'),
                    segments=segments,
                    discovered_at=datetime.now(),
                    confidence_score=path_info.get('confidence_score', 0.0),
                    validation_status=ValidationStatus(path_info.get('validation_status', 'pending'))
                )
                paths.append(path)
            
            # Create bridge domain configuration
            bridge_domain_config = BridgeDomainConfig(
                service_name=service_name,
                bridge_domain_type=BridgeDomainType.SINGLE_VLAN,
                source_device=source_device,
                source_interface=source_interface,
                destinations=destinations,
                vlan_id=vlan_id,
                outer_tag_imposition=OuterTagImposition.EDGE,
                created_at=datetime.now(),
                confidence_score=0.8,
                validation_status=ValidationStatus.PENDING
            )
            
            # Create topology data
            topology_data = TopologyData(
                bridge_domain_name=service_name,
                topology_type=TopologyType(topology_type),
                vlan_id=vlan_id,
                devices=devices,
                interfaces=interfaces,
                paths=paths,
                bridge_domain_config=bridge_domain_config,
                discovered_at=datetime.now(),
                scan_method='legacy_import',
                confidence_score=0.7,
                validation_status=ValidationStatus.PENDING
            )
            
            return topology_data
            
        except Exception as e:
            self.logger.error(f"❌ Legacy deserialization failed: {e}")
            return None
    
    def export_to_file(self, topology_data: TopologyData, file_path: str, format: str = 'json') -> bool:
        """
        Export Phase 1 topology data to file.
        
        Args:
            topology_data: Phase 1 TopologyData object
            file_path: Output file path
            format: Output format ('json', 'yaml')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Serialize data
            serialized_data = self.serialize_topology(topology_data, format)
            if not serialized_data:
                return False
            
            # Write to file
            with open(output_path, 'w') as f:
                f.write(serialized_data)
            
            self.logger.info(f"✅ Topology data exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Export to file failed: {e}")
            return False
    
    def import_from_file(self, file_path: str, format: str = 'auto') -> Optional[TopologyData]:
        """
        Import Phase 1 topology data from file.
        
        Args:
            file_path: Input file path
            format: Input format ('json', 'yaml', 'auto')
            
        Returns:
            TopologyData object if successful, None otherwise
        """
        try:
            input_path = Path(file_path)
            if not input_path.exists():
                self.logger.error(f"❌ File not found: {file_path}")
                return None
            
            # Auto-detect format if not specified
            if format == 'auto':
                if input_path.suffix.lower() == '.json':
                    format = 'json'
                elif input_path.suffix.lower() in ['.yaml', '.yml']:
                    format = 'yaml'
                else:
                    # Try to detect by reading first few characters
                    with open(input_path, 'r') as f:
                        first_chars = f.read(10).strip()
                        if first_chars.startswith('{'):
                            format = 'json'
                        elif first_chars.startswith('-') or first_chars.startswith('#'):
                            format = 'yaml'
                        else:
                            self.logger.error(f"❌ Could not auto-detect format for {file_path}")
                            return None
            
            # Read file content
            with open(input_path, 'r') as f:
                content = f.read()
            
            # Deserialize data
            topology_data = self.deserialize_topology(content, format)
            
            if topology_data:
                self.logger.info(f"✅ Topology data imported from {file_path}")
            else:
                self.logger.error(f"❌ Failed to deserialize data from {file_path}")
            
            return topology_data
            
        except Exception as e:
            self.logger.error(f"❌ Import from file failed: {e}")
            return None
    
    def validate_serialized_data(self, data: str, format: str = 'json') -> Tuple[bool, List[str], List[str]]:
        """
        Validate serialized data without deserializing.
        
        Args:
            data: Serialized data string
            format: Data format ('json', 'yaml')
            
        Returns:
            Tuple of (valid, errors, warnings)
        """
        try:
            # Parse data
            if format.lower() == 'json':
                data_dict = json.loads(data)
            elif format.lower() == 'yaml':
                data_dict = yaml.safe_load(data)
            else:
                return False, [f"Unsupported format: {format}"], []
            
            # Basic validation
            errors = []
            warnings = []
            
            # Check required fields
            required_fields = ['bridge_domain_name', 'topology_type', 'devices', 'interfaces', 'paths']
            for field in required_fields:
                if field not in data_dict:
                    errors.append(f"Missing required field: {field}")
            
            # Check data types
            if 'devices' in data_dict and not isinstance(data_dict['devices'], list):
                errors.append("Devices field must be a list")
            
            if 'interfaces' in data_dict and not isinstance(data_dict['interfaces'], list):
                errors.append("Interfaces field must be a list")
            
            if 'paths' in data_dict and not isinstance(data_dict['paths'], list):
                errors.append("Paths field must be a list")
            
            # Check for potential issues
            if 'devices' in data_dict and len(data_dict['devices']) == 0:
                warnings.append("No devices defined")
            
            if 'interfaces' in data_dict and len(data_dict['interfaces']) == 0:
                warnings.append("No interfaces defined")
            
            if 'paths' in data_dict and len(data_dict['paths']) == 0:
                warnings.append("No paths defined")
            
            # Check confidence score
            if 'confidence_score' in data_dict:
                score = data_dict['confidence_score']
                if not isinstance(score, (int, float)) or score < 0 or score > 1:
                    errors.append("Confidence score must be between 0 and 1")
                elif score < 0.5:
                    warnings.append("Low confidence score detected")
            
            valid = len(errors) == 0
            return valid, errors, warnings
            
        except Exception as e:
            return False, [f"Validation failed: {str(e)}"], []
    
    def convert_format(self, data: str, from_format: str, to_format: str) -> Optional[str]:
        """
        Convert data between different formats.
        
        Args:
            data: Input data string
            from_format: Input format ('json', 'yaml')
            to_format: Output format ('json', 'yaml')
            
        Returns:
            Converted data string, None if failed
        """
        try:
            # Deserialize from source format
            topology_data = self.deserialize_topology(data, from_format)
            if not topology_data:
                return None
            
            # Serialize to target format
            return self.serialize_topology(topology_data, to_format)
            
        except Exception as e:
            self.logger.error(f"❌ Format conversion failed: {e}")
            return None
    
    def get_serialization_info(self, topology_data: TopologyData) -> Dict[str, Any]:
        """
        Get information about serialization capabilities and data size.
        
        Args:
            topology_data: Phase 1 TopologyData object
            
        Returns:
            Serialization information dictionary
        """
        try:
            # Get JSON serialization
            json_data = self.serialize_topology(topology_data, 'json')
            json_size = len(json_data) if json_data else 0
            
            # Get YAML serialization
            yaml_data = self.serialize_topology(topology_data, 'yaml')
            yaml_size = len(yaml_data) if yaml_data else 0
            
            # Get legacy format
            legacy_data = self.serialize_to_legacy_format(topology_data)
            legacy_size = len(json.dumps(legacy_data, cls=self.json_encoder)) if legacy_data else 0
            
            return {
                'json_size_bytes': json_size,
                'yaml_size_bytes': yaml_size,
                'legacy_size_bytes': legacy_size,
                'compression_ratio': yaml_size / json_size if json_size > 0 else 0,
                'formats_supported': ['json', 'yaml', 'legacy'],
                'serialization_success': {
                    'json': json_data is not None,
                    'yaml': yaml_data is not None,
                    'legacy': legacy_data is not None
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get serialization info: {e}")
            return {}
