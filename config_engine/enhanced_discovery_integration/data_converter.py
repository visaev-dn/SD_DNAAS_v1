#!/usr/bin/env python3
"""
Enhanced Data Converter

Handles specific data format conversions from legacy discovery data
to Enhanced Database structures with validation and error handling.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Import Phase 1 data structures
from config_engine.phase1_data_structures import (
    TopologyData, DeviceInfo, InterfaceInfo, PathInfo, 
    PathSegment, BridgeDomainConfig, TopologyType, DeviceType,
    InterfaceType, InterfaceRole, DeviceRole, BridgeDomainType,
    OuterTagImposition, ValidationStatus
)

# Import error handling
from .error_handler import (
    EnhancedDataConversionError, EnhancedValidationError
)


class EnhancedDataConverter:
    """Handles specific data format conversions with validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conversion_stats = {
            'devices_converted': 0,
            'interfaces_converted': 0,
            'paths_converted': 0,
            'bridge_domains_converted': 0,
            'conversion_errors': 0,
            'validation_errors': 0
        }
    
    def convert_device_info(self, legacy_device: Dict) -> DeviceInfo:
        """Convert legacy device data to Enhanced Database DeviceInfo"""
        
        try:
            # Extract device information with fallbacks
            device_name = legacy_device.get('name', 'unknown')
            device_type_str = legacy_device.get('device_type', 'leaf')
            device_role_str = legacy_device.get('device_role', 'source')
            
            # Convert device type
            try:
                device_type = DeviceType(device_type_str.lower())
            except ValueError:
                self.logger.warning(f"Invalid device type '{device_type_str}' for {device_name}, defaulting to LEAF")
                device_type = DeviceType.LEAF
            
            # Convert device role
            try:
                device_role = DeviceRole(device_role_str.lower())
            except ValueError:
                self.logger.warning(f"Invalid device role '{device_role_str}' for {device_name}, defaulting to SOURCE")
                device_role = DeviceRole.SOURCE
            
            # Create DeviceInfo with available data
            device_info = DeviceInfo(
                name=device_name,
                device_type=device_type,
                device_role=device_role,
                management_ip=legacy_device.get('mgmt_ip') or legacy_device.get('management_ip'),
                row=legacy_device.get('row'),
                rack=legacy_device.get('rack'),
                position=legacy_device.get('position'),
                total_interfaces=legacy_device.get('total_interfaces', 0),
                available_interfaces=legacy_device.get('available_interfaces', 0),
                configured_interfaces=legacy_device.get('configured_interfaces', 0),
                confidence_score=legacy_device.get('confidence_score', 0.5),
                validation_status=ValidationStatus.PENDING
            )
            
            self.conversion_stats['devices_converted'] += 1
            self.logger.debug(f"Successfully converted device: {device_name}")
            
            return device_info
            
        except Exception as e:
            self.conversion_stats['conversion_errors'] += 1
            error_msg = f"Failed to convert device {legacy_device.get('name', 'unknown')}: {e}"
            self.logger.error(error_msg)
            raise EnhancedDataConversionError(
                message=error_msg,
                source_format='legacy_device',
                target_format='DeviceInfo',
                context={'legacy_data': legacy_device}
            )
    
    def convert_interface_info(self, legacy_interface: Dict) -> InterfaceInfo:
        """Convert legacy interface data to Enhanced Database InterfaceInfo"""
        
        try:
            # Extract interface information
            interface_name = legacy_interface.get('name', 'unknown')
            device_name = legacy_interface.get('device_name', 'unknown')
            
            # Convert interface type
            interface_type_str = legacy_interface.get('interface_type', 'physical')
            try:
                interface_type = InterfaceType(interface_type_str.lower())
            except ValueError:
                self.logger.warning(f"Invalid interface type '{interface_type_str}' for {interface_name}, defaulting to PHYSICAL")
                interface_type = InterfaceType.PHYSICAL
            
            # Convert interface role
            interface_role_str = legacy_interface.get('interface_role', 'uplink')
            try:
                interface_role = InterfaceRole(interface_role_str.lower())
            except ValueError:
                self.logger.warning(f"Invalid interface role '{interface_role_str}' for {interface_name}, defaulting to UPLINK")
                interface_role = InterfaceRole.UPLINK
            
            # Create InterfaceInfo
            interface_info = InterfaceInfo(
                name=interface_name,
                interface_type=interface_type,
                interface_role=interface_role,
                device_name=device_name,
                vlan_id=legacy_interface.get('vlan_id'),
                bundle_id=legacy_interface.get('bundle_id'),
                subinterface_id=legacy_interface.get('subinterface_id'),
                speed=legacy_interface.get('speed'),
                duplex=legacy_interface.get('duplex'),
                media_type=legacy_interface.get('media_type'),
                description=legacy_interface.get('description'),
                mtu=legacy_interface.get('mtu'),
                l2_service_enabled=legacy_interface.get('l2_service_enabled', False),
                connected_device=legacy_interface.get('connected_device'),
                connected_interface=legacy_interface.get('connected_interface'),
                connection_type=legacy_interface.get('connection_type'),
                confidence_score=legacy_interface.get('confidence_score', 0.5),
                validation_status=ValidationStatus.PENDING
            )
            
            self.conversion_stats['interfaces_converted'] += 1
            self.logger.debug(f"Successfully converted interface: {interface_name}")
            
            return interface_info
            
        except Exception as e:
            self.conversion_stats['conversion_errors'] += 1
            error_msg = f"Failed to convert interface {legacy_interface.get('name', 'unknown')}: {e}"
            self.logger.error(error_msg)
            raise EnhancedDataConversionError(
                message=error_msg,
                source_format='legacy_interface',
                target_format='InterfaceInfo',
                context={'legacy_data': legacy_interface}
            )
    
    def convert_path_info(self, legacy_path: Dict) -> PathInfo:
        """Convert legacy path data to Enhanced Database PathInfo"""
        
        try:
            # Extract path information
            path_name = legacy_path.get('path_name') or legacy_path.get('name', 'unknown')
            source_device = legacy_path.get('source_device', 'unknown')
            dest_device = legacy_path.get('dest_device', 'unknown')
            
            # Convert path type
            path_type_str = legacy_path.get('path_type', 'p2p')
            try:
                path_type = TopologyType(path_type_str.lower())
            except ValueError:
                self.logger.warning(f"Invalid path type '{path_type_str}' for {path_name}, defaulting to P2P")
                path_type = TopologyType.P2P
            
            # Convert segments
            segments = []
            legacy_segments = legacy_path.get('segments', [])
            
            for segment_data in legacy_segments:
                try:
                    segment = PathSegment(
                        source_device=segment_data.get('source_device', 'unknown'),
                        dest_device=segment_data.get('dest_device', 'unknown'),
                        source_interface=segment_data.get('source_interface', 'unknown'),
                        dest_interface=segment_data.get('dest_interface', 'unknown'),
                        segment_type=segment_data.get('segment_type', 'physical'),
                        connection_type=segment_data.get('connection_type', 'direct'),
                        bundle_id=segment_data.get('bundle_id'),
                        confidence_score=segment_data.get('confidence_score', 0.5)
                    )
                    segments.append(segment)
                except Exception as e:
                    self.logger.warning(f"Failed to convert path segment: {e}, skipping")
                    continue
            
            # Create PathInfo
            path_info = PathInfo(
                path_name=path_name,
                path_type=path_type,
                source_device=source_device,
                dest_device=dest_device,
                segments=segments,
                is_active=legacy_path.get('is_active', True),
                is_redundant=legacy_path.get('is_redundant', False),
                confidence_score=legacy_path.get('confidence_score', 0.5),
                validation_status=ValidationStatus.PENDING
            )
            
            self.conversion_stats['paths_converted'] += 1
            self.logger.debug(f"Successfully converted path: {path_name}")
            
            return path_info
            
        except Exception as e:
            self.conversion_stats['conversion_errors'] += 1
            error_msg = f"Failed to convert path {legacy_path.get('path_name', 'unknown')}: {e}"
            self.logger.error(error_msg)
            raise EnhancedDataConversionError(
                message=error_msg,
                source_format='legacy_path',
                target_format='PathInfo',
                context={'legacy_data': legacy_path}
            )
    
    def convert_bridge_domain_config(self, legacy_bd: Dict) -> BridgeDomainConfig:
        """Convert legacy bridge domain to Enhanced Database BridgeDomainConfig"""
        
        try:
            # Extract bridge domain information
            service_name = legacy_bd.get('service_name') or legacy_bd.get('name', 'unknown')
            source_device = legacy_bd.get('source_device', 'unknown')
            source_interface = legacy_bd.get('source_interface', 'unknown')
            
            # Convert bridge domain type
            bd_type_str = legacy_bd.get('bridge_domain_type', 'single_vlan')
            try:
                bridge_domain_type = BridgeDomainType(bd_type_str.lower())
            except ValueError:
                self.logger.warning(f"Invalid bridge domain type '{bd_type_str}' for {service_name}, defaulting to SINGLE_VLAN")
                bridge_domain_type = BridgeDomainType.SINGLE_VLAN
            
            # Convert outer tag imposition
            outer_tag_str = legacy_bd.get('outer_tag_imposition', 'edge')
            try:
                outer_tag_imposition = OuterTagImposition(outer_tag_str.lower())
            except ValueError:
                self.logger.warning(f"Invalid outer tag imposition '{outer_tag_str}' for {service_name}, defaulting to EDGE")
                outer_tag_imposition = OuterTagImposition.EDGE
            
            # Process destinations
            destinations = []
            legacy_destinations = legacy_bd.get('destinations', [])
            
            for dest_data in legacy_destinations:
                if isinstance(dest_data, dict):
                    destinations.append(dest_data)
                elif isinstance(dest_data, str):
                    # Handle string format like "device:port"
                    if ':' in dest_data:
                        device, port = dest_data.split(':', 1)
                        destinations.append({'device': device.strip(), 'port': port.strip()})
                    else:
                        destinations.append({'device': dest_data, 'port': 'unknown'})
            
            # Create BridgeDomainConfig
            bridge_domain_config = BridgeDomainConfig(
                service_name=service_name,
                bridge_domain_type=bridge_domain_type,
                source_device=source_device,
                source_interface=source_interface,
                destinations=destinations,
                vlan_id=legacy_bd.get('vlan_id'),
                vlan_start=legacy_bd.get('vlan_start'),
                vlan_end=legacy_bd.get('vlan_end'),
                vlan_list=legacy_bd.get('vlan_list'),
                outer_vlan=legacy_bd.get('outer_vlan'),
                inner_vlan=legacy_bd.get('inner_vlan'),
                outer_tag_imposition=outer_tag_imposition,
                bundle_id=legacy_bd.get('bundle_id'),
                interface_number=legacy_bd.get('interface_number'),
                is_active=legacy_bd.get('is_active', True),
                is_deployed=legacy_bd.get('is_deployed', False),
                deployment_status=legacy_bd.get('deployment_status', 'pending'),
                created_by=legacy_bd.get('created_by'),
                confidence_score=legacy_bd.get('confidence_score', 0.5),
                validation_status=ValidationStatus.PENDING
            )
            
            self.conversion_stats['bridge_domains_converted'] += 1
            self.logger.debug(f"Successfully converted bridge domain: {service_name}")
            
            return bridge_domain_config
            
        except Exception as e:
            self.conversion_stats['conversion_errors'] += 1
            error_msg = f"Failed to convert bridge domain {legacy_bd.get('service_name', 'unknown')}: {e}"
            self.logger.error(error_msg)
            raise EnhancedDataConversionError(
                message=error_msg,
                source_format='legacy_bridge_domain',
                target_format='BridgeDomainConfig',
                context={'legacy_data': legacy_bd}
            )
    
    def convert_lacp_data(self, lacp_data: Dict) -> List[Dict[str, Any]]:
        """Convert LACP data to Enhanced Database compatible format"""
        
        try:
            converted_data = []
            bundles = lacp_data.get('bundles', [])
            
            for bundle in bundles:
                bundle_name = bundle.get('name', 'unknown')
                members = bundle.get('members', [])
                
                # Create device info for each bundle
                bundle_device = {
                    'name': bundle_name,
                    'device_type': 'bundle',
                    'device_role': 'transport',
                    'total_interfaces': len(members),
                    'configured_interfaces': len(members),
                    'confidence_score': 0.8
                }
                
                # Create interface info for each member
                for member in members:
                    member_interface = {
                        'name': member,
                        'interface_type': 'physical',
                        'interface_role': 'access',
                        'device_name': bundle_name,
                        'bundle_id': bundle.get('bundle_id'),
                        'connection_type': 'bundle',
                        'confidence_score': 0.8
                    }
                    
                    converted_data.append({
                        'type': 'interface',
                        'data': member_interface
                    })
                
                converted_data.append({
                    'type': 'device',
                    'data': bundle_device
                })
            
            self.logger.info(f"Converted {len(bundles)} LACP bundles with {len(converted_data)} total items")
            return converted_data
            
        except Exception as e:
            error_msg = f"Failed to convert LACP data: {e}"
            self.logger.error(error_msg)
            raise EnhancedDataConversionError(
                message=error_msg,
                source_format='lacp_data',
                target_format='enhanced_database',
                context={'lacp_data': lacp_data}
            )
    
    def convert_lldp_data(self, lldp_data: Dict) -> List[Dict[str, Any]]:
        """Convert LLDP data to Enhanced Database compatible format"""
        
        try:
            converted_data = []
            neighbors = lldp_data.get('neighbors', [])
            
            for neighbor in neighbors:
                # Create path segment from LLDP neighbor
                path_segment = {
                    'source_device': lldp_data.get('device_name', 'unknown'),
                    'dest_device': neighbor.get('neighbor_device', 'unknown'),
                    'source_interface': neighbor.get('local_interface', 'unknown'),
                    'dest_interface': neighbor.get('neighbor_interface', 'unknown'),
                    'segment_type': 'physical',
                    'connection_type': 'direct',
                    'confidence_score': 0.9
                }
                
                converted_data.append({
                    'type': 'path_segment',
                    'data': path_segment
                })
            
            self.logger.info(f"Converted {len(neighbors)} LLDP neighbors")
            return converted_data
            
        except Exception as e:
            error_msg = f"Failed to convert LLDP data: {e}"
            self.logger.error(error_msg)
            raise EnhancedDataConversionError(
                message=error_msg,
                source_format='lldp_data',
                target_format='enhanced_database',
                context={'lldp_data': lldp_data}
            )
    
    def convert_bridge_domain_data(self, bd_data: Dict) -> List[Dict[str, Any]]:
        """Convert Bridge Domain data to Enhanced Database compatible format"""
        
        try:
            converted_data = []
            bridge_domains = bd_data.get('bridge_domains', [])
            
            for bd in bridge_domains:
                # Convert bridge domain config
                bd_config = self.convert_bridge_domain_config(bd)
                converted_data.append({
                    'type': 'bridge_domain_config',
                    'data': bd_config
                })
                
                # Add source device if not already present
                source_device = {
                    'name': bd.get('source_device', 'unknown'),
                    'device_type': 'leaf',
                    'device_role': 'source',
                    'confidence_score': 0.8
                }
                
                converted_data.append({
                    'type': 'device',
                    'data': source_device
                })
                
                # Add source interface
                source_interface = {
                    'name': bd.get('source_interface', 'unknown'),
                    'interface_type': 'physical',
                    'interface_role': 'access',
                    'device_name': bd.get('source_device', 'unknown'),
                    'vlan_id': bd.get('vlan_id'),
                    'confidence_score': 0.8
                }
                
                converted_data.append({
                    'type': 'interface',
                    'data': source_interface
                })
            
            self.logger.info(f"Converted {len(bridge_domains)} bridge domains")
            return converted_data
            
        except Exception as e:
            error_msg = f"Failed to convert Bridge Domain data: {e}"
            self.logger.error(error_msg)
            raise EnhancedDataConversionError(
                message=error_msg,
                source_format='bridge_domain_data',
                target_format='enhanced_database',
                context={'bd_data': bd_data}
            )
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics"""
        
        return {
            'devices_converted': self.conversion_stats['devices_converted'],
            'interfaces_converted': self.conversion_stats['interfaces_converted'],
            'paths_converted': self.conversion_stats['paths_converted'],
            'bridge_domains_converted': self.conversion_stats['bridge_domains_converted'],
            'conversion_errors': self.conversion_stats['conversion_errors'],
            'validation_errors': self.conversion_stats['validation_errors'],
            'total_conversions': sum([
                self.conversion_stats['devices_converted'],
                self.conversion_stats['interfaces_converted'],
                self.conversion_stats['paths_converted'],
                self.conversion_stats['bridge_domains_converted']
            ]),
            'success_rate': (
                (sum([
                    self.conversion_stats['devices_converted'],
                    self.conversion_stats['interfaces_converted'],
                    self.conversion_stats['paths_converted'],
                    self.conversion_stats['bridge_domains_converted']
                ]) / max(1, sum([
                    self.conversion_stats['devices_converted'],
                    self.conversion_stats['interfaces_converted'],
                    self.conversion_stats['paths_converted'],
                    self.conversion_stats['bridge_domains_converted']
                ]) + self.conversion_stats['conversion_errors'])) * 100
            )
        }
    
    def reset_statistics(self):
        """Reset conversion statistics"""
        
        for key in self.conversion_stats:
            self.conversion_stats[key] = 0
        
        self.logger.info("Conversion statistics reset")
    
    def validate_converted_data(self, converted_data: Any, data_type: str) -> bool:
        """Validate converted data against Enhanced Database schema"""
        
        try:
            if data_type == 'device':
                if not isinstance(converted_data, DeviceInfo):
                    raise EnhancedValidationError(
                        f"Converted data is not a DeviceInfo instance: {type(converted_data)}",
                        field_name='device_data',
                        validation_rule='instance_type'
                    )
                
                # Validate required fields
                if not converted_data.name:
                    raise EnhancedValidationError(
                        "Device name is required",
                        field_name='name',
                        validation_rule='required'
                    )
                
            elif data_type == 'interface':
                if not isinstance(converted_data, InterfaceInfo):
                    raise EnhancedValidationError(
                        f"Converted data is not an InterfaceInfo instance: {type(converted_data)}",
                        field_name='interface_data',
                        validation_rule='instance_type'
                    )
                
                # Validate required fields
                if not converted_data.name:
                    raise EnhancedValidationError(
                        "Interface name is required",
                        field_name='name',
                        validation_rule='required'
                    )
                
                if not converted_data.device_name:
                    raise EnhancedValidationError(
                        "Device name is required for interface",
                        field_name='device_name',
                        validation_rule='required'
                    )
            
            elif data_type == 'path':
                if not isinstance(converted_data, PathInfo):
                    raise EnhancedValidationError(
                        f"Converted data is not a PathInfo instance: {type(converted_data)}",
                        field_name='path_data',
                        validation_rule='instance_type'
                    )
                
                # Validate required fields
                if not converted_data.path_name:
                    raise EnhancedValidationError(
                        "Path name is required",
                        field_name='path_name',
                        validation_rule='required'
                    )
                
                if not converted_data.segments:
                    raise EnhancedValidationError(
                        "Path must have at least one segment",
                        field_name='segments',
                        validation_rule='required'
                    )
            
            elif data_type == 'bridge_domain':
                if not isinstance(converted_data, BridgeDomainConfig):
                    raise EnhancedValidationError(
                        f"Converted data is not a BridgeDomainConfig instance: {type(converted_data)}",
                        field_name='bridge_domain_data',
                        validation_rule='instance_type'
                    )
                
                # Validate required fields
                if not converted_data.service_name:
                    raise EnhancedValidationError(
                        "Service name is required",
                        field_name='service_name',
                        validation_rule='required'
                    )
                
                if not converted_data.source_device:
                    raise EnhancedValidationError(
                        "Source device is required",
                        field_name='source_device',
                        validation_rule='required'
                    )
                
                if not converted_data.source_interface:
                    raise EnhancedValidationError(
                        "Source interface is required",
                        field_name='source_interface',
                        validation_rule='required'
                    )
            
            return True
            
        except EnhancedValidationError:
            self.conversion_stats['validation_errors'] += 1
            raise
        except Exception as e:
            self.conversion_stats['validation_errors'] += 1
            raise EnhancedValidationError(
                f"Validation failed for {data_type}: {e}",
                field_name='validation',
                validation_rule='general'
            )
