#!/usr/bin/env python3
"""
Unified Bridge Domain Builder
Handles both P2P and P2MP scenarios with any device type combinations.
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from enum import Enum

from .enhanced_device_types import DeviceType, enhanced_classifier
from .device_name_normalizer import normalizer
from .bridge_domain_builder import BridgeDomainBuilder


class ConfigurationType(Enum):
    """Configuration type enumeration"""
    P2P = "P2P"
    P2MP = "P2MP"


class UnifiedBridgeDomainBuilder:
    """
    Unified bridge domain builder that handles both P2P and P2MP scenarios.
    
    Supports:
    - P2P: Leaf → Leaf, Leaf → Superspine
    - P2MP: Leaf → Multiple Leaves, Leaf → Multiple Superspines, Leaf → Mixed
    - Automatic path calculation for all scenarios
    - Unified configuration generation
    """
    
    def __init__(self, topology_dir: str = "topology"):
        """
        Initialize unified bridge domain builder.
        
        Args:
            topology_dir: Directory containing topology files
        """
        self.topology_dir = Path(topology_dir)
        self.logger = logging.getLogger('UnifiedBridgeDomainBuilder')
        
        # Initialize the original bridge domain builder for base functionality
        self.original_builder = BridgeDomainBuilder(topology_dir)
        
        # Initialize device name normalizer
        self.normalizer = normalizer
        
        # Load topology data
        self.topology_data = self.original_builder.topology_data
        self.bundle_mappings = self.original_builder.bundle_mappings
        
        # Build device connection map
        self.device_connections = self._build_connection_map()
    
    def _build_connection_map(self) -> Dict:
        """Build comprehensive device connection map from topology data"""
        devices = self.topology_data.get('devices', {})
        device_connections = {}
        
        for device_name, device_info in devices.items():
            device_connections[device_name] = []
            
            # Add spine connections
            for spine_conn in device_info.get('connected_spines', []):
                if isinstance(spine_conn, dict):
                    spine_name = spine_conn['name']
                    device_connections[device_name].append({
                        'device': spine_name,
                        'local_interface': spine_conn['local_interface'],
                        'remote_interface': spine_conn['remote_interface'],
                        'connection_type': 'spine'
                    })
                    
                    # Add reverse connection for spine
                    if spine_name not in device_connections:
                        device_connections[spine_name] = []
                    device_connections[spine_name].append({
                        'device': device_name,
                        'local_interface': spine_conn['remote_interface'],
                        'remote_interface': spine_conn['local_interface'],
                        'connection_type': 'leaf'
                    })
            
            # Add superspine connections
            for superspine_conn in device_info.get('connected_superspines', []):
                if isinstance(superspine_conn, dict):
                    superspine_name = superspine_conn['name']
                    device_connections[device_name].append({
                        'device': superspine_name,
                        'local_interface': superspine_conn['local_interface'],
                        'remote_interface': superspine_conn['remote_interface'],
                        'connection_type': 'superspine'
                    })
                    
                    # Add reverse connection for superspine
                    if superspine_name not in device_connections:
                        device_connections[superspine_name] = []
                    device_connections[superspine_name].append({
                        'device': device_name,
                        'local_interface': superspine_conn['remote_interface'],
                        'remote_interface': superspine_conn['local_interface'],
                        'connection_type': 'spine'
                    })
        
        return device_connections
    
    def get_device_type(self, device_name: str) -> DeviceType:
        """Get device type for a device"""
        return enhanced_classifier.detect_device_type(device_name)
    
    def get_available_sources(self) -> List[Dict]:
        """Get available source devices (leaves only)"""
        available_leaves = self.original_builder.get_available_leaves()
        devices = []
        
        for leaf_name in available_leaves:
            devices.append({
                'name': leaf_name,
                'device_type': DeviceType.LEAF
            })
        
        return devices
    
    def get_available_destinations(self, source_device: str) -> List[Dict]:
        """Get available destination devices (leaves + superspines)"""
        devices = []
        
        # Get available leaves (excluding source)
        available_leaves = self.original_builder.get_available_leaves()
        for leaf_name in available_leaves:
            if leaf_name != source_device:
                devices.append({
                    'name': leaf_name,
                    'device_type': DeviceType.LEAF
                })
        
        # Get available superspines
        if self.topology_data:
            superspine_devices = self.topology_data.get('superspine_devices', [])
            for superspine_name in superspine_devices:
                devices.append({
                    'name': superspine_name,
                    'device_type': DeviceType.SUPERSPINE
                })
        
        return devices
    
    def build_bridge_domain_config(self, service_name: str, vlan_id: int,
                                 source_device: str, source_interface: str,
                                 destinations: List[Dict]) -> Dict:
        """
        Build bridge domain configuration for any scenario.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            destinations: List of destination dictionaries with 'device' and 'port' keys
            
        Returns:
            Bridge domain configuration dictionary
        """
        # Determine configuration type based on destination count
        if len(destinations) == 1:
            return self._build_p2p_config(service_name, vlan_id, source_device, source_interface, destinations[0])
        else:
            return self._build_p2mp_config(service_name, vlan_id, source_device, source_interface, destinations)
    
    def _build_p2p_config(self, service_name: str, vlan_id: int,
                          source_device: str, source_interface: str,
                          destination: Dict) -> Dict:
        """Build P2P bridge domain configuration"""
        dest_device = destination['device']
        dest_interface = destination['port']
        
        source_type = self.get_device_type(source_device)
        dest_type = self.get_device_type(dest_device)
        
        # Validate topology constraints
        if not self._validate_p2p_topology(source_type, dest_type):
            raise ValueError(f"Invalid P2P topology: {source_type.value} → {dest_type.value}")
        
        # Use original builder for leaf-to-leaf
        if dest_type == DeviceType.LEAF:
            return self.original_builder.build_bridge_domain_config(
                service_name, vlan_id,
                source_device, source_interface,
                dest_device, dest_interface
            )
        
        # Handle leaf-to-superspine
        elif dest_type == DeviceType.SUPERSPINE:
            return self._build_leaf_to_superspine_p2p_config(
                service_name, vlan_id,
                source_device, source_interface,
                dest_device, dest_interface
            )
        
        else:
            raise ValueError(f"Unsupported destination device type: {dest_type}")
    
    def _build_p2mp_config(self, service_name: str, vlan_id: int,
                           source_device: str, source_interface: str,
                           destinations: List[Dict]) -> Dict:
        """Build P2MP bridge domain configuration"""
        # Analyze destination types
        leaf_destinations = []
        superspine_destinations = []
        
        for dest in destinations:
            dest_device = dest['device']
            dest_type = self.get_device_type(dest_device)
            
            if dest_type == DeviceType.LEAF:
                leaf_destinations.append(dest)
            elif dest_type == DeviceType.SUPERSPINE:
                superspine_destinations.append(dest)
            else:
                raise ValueError(f"Unsupported destination device type: {dest_type}")
        
        # Handle different P2MP scenarios
        if leaf_destinations and superspine_destinations:
            # Mixed destinations - build separate configs
            return self._build_mixed_p2mp_config(
                service_name, vlan_id,
                source_device, source_interface,
                leaf_destinations, superspine_destinations
            )
        elif leaf_destinations:
            # All leaf destinations - use P2MP builder
            return self._build_leaf_p2mp_config(
                service_name, vlan_id,
                source_device, source_interface,
                leaf_destinations
            )
        elif superspine_destinations:
            # All superspine destinations - build individual P2P configs
            return self._build_superspine_p2mp_config(
                service_name, vlan_id,
                source_device, source_interface,
                superspine_destinations
            )
        else:
            raise ValueError("No valid destinations provided")
    
    def _build_leaf_to_superspine_p2p_config(self, service_name: str, vlan_id: int,
                                            source_leaf: str, source_interface: str,
                                            dest_superspine: str, dest_interface: str) -> Dict:
        """Build P2P configuration for leaf-to-superspine"""
        # Find spine connected to source leaf
        source_spine = None
        source_leaf_conn = None
        
        for conn in self.device_connections.get(source_leaf, []):
            if conn['connection_type'] == 'spine':
                spine_name = conn['device']
                # Check if this spine connects to the superspine
                for spine_conn in self.device_connections.get(spine_name, []):
                    if (spine_conn['connection_type'] == 'superspine' and 
                        spine_conn['device'].replace('-NCC0', '').replace('-NCC1', '') == 
                        dest_superspine.replace('-NCC0', '').replace('-NCC1', '')):
                        source_spine = spine_name
                        source_leaf_conn = conn
                        break
                if source_spine:
                    break
        
        if not source_spine:
            raise ValueError(f"Could not find spine connecting {source_leaf} to {dest_superspine}")
        
        # Find spine-to-superspine connection
        spine_superspine_conn = None
        for conn in self.device_connections.get(source_spine, []):
            if (conn['connection_type'] == 'superspine' and 
                conn['device'].replace('-NCC0', '').replace('-NCC1', '') == 
                dest_superspine.replace('-NCC0', '').replace('-NCC1', '')):
                spine_superspine_conn = conn
                break
        
        if not spine_superspine_conn:
            raise ValueError(f"Could not find superspine connection for {source_spine}")
        
        # Build configurations
        configs = {}
        
        # Source Leaf Configuration
        source_leaf_config = self._build_leaf_config(
            service_name, vlan_id, source_leaf,
            source_interface, source_leaf_conn['local_interface'],
            is_source=True
        )
        configs[source_leaf] = source_leaf_config
        
        # Spine Configuration
        spine_config = self.original_builder._build_spine_config(
            service_name, vlan_id, source_spine,
            source_leaf_conn['remote_interface'], spine_superspine_conn['local_interface']
        )
        configs[source_spine] = spine_config
        
        # Superspine Configuration
        superspine_config = self._build_superspine_config(
            service_name, vlan_id, dest_superspine,
            spine_superspine_conn['remote_interface'], dest_interface
        )
        configs[dest_superspine] = superspine_config
        
        # Add metadata
        configs['_metadata'] = {
            'service_name': service_name,
            'vlan_id': vlan_id,
            'topology_type': 'P2P',
            'source_device': source_leaf,
            'dest_device': dest_superspine,
            'source_device_type': 'leaf',
            'dest_device_type': 'superspine',
            'path': [source_leaf, source_spine, dest_superspine]
        }
        
        return configs
    
    def _build_leaf_p2mp_config(self, service_name: str, vlan_id: int,
                                source_device: str, source_interface: str,
                                destinations: List[Dict]) -> Dict:
        """Build P2MP configuration for leaf destinations"""
        # Use P2MP builder for leaf-to-leaf P2MP
        try:
            from .p2mp_bridge_domain_builder import P2MPBridgeDomainBuilder
            p2mp_builder = P2MPBridgeDomainBuilder(str(self.topology_dir))
            
            # Convert destinations to P2MP format
            p2mp_destinations = []
            for dest in destinations:
                p2mp_destinations.append({
                    'leaf': dest['device'],
                    'port': dest['port']
                })
            
            return p2mp_builder.build_p2mp_bridge_domain_config(
                service_name, vlan_id,
                source_device, source_interface,
                p2mp_destinations
            )
            
        except ImportError:
            raise ValueError("P2MP bridge domain builder not available")
    
    def _build_superspine_p2mp_config(self, service_name: str, vlan_id: int,
                                     source_device: str, source_interface: str,
                                     destinations: List[Dict]) -> Dict:
        """Build P2MP configuration for superspine destinations (individual P2P configs)"""
        all_configs = {}
        successful_configs = 0
        
        for dest in destinations:
            dest_device = dest['device']
            dest_interface = dest['port']
            
            try:
                # Build individual P2P config for each superspine
                config = self._build_leaf_to_superspine_p2p_config(
                    service_name, vlan_id,
                    source_device, source_interface,
                    dest_device, dest_interface
                )
                
                # Merge configs (excluding metadata)
                for device, device_config in config.items():
                    if device != '_metadata':
                        if device not in all_configs:
                            all_configs[device] = []
                        all_configs[device].extend(device_config)
                
                successful_configs += 1
                
            except Exception as e:
                self.logger.error(f"Failed to build config for {dest_device}: {e}")
        
        # Add unified metadata
        all_configs['_metadata'] = {
            'service_name': service_name,
            'vlan_id': vlan_id,
            'topology_type': 'P2MP',
            'source_device': source_device,
            'dest_devices': [dest['device'] for dest in destinations],
            'source_device_type': 'leaf',
            'dest_device_types': ['superspine'] * len(destinations),
            'successful_configs': successful_configs,
            'total_destinations': len(destinations)
        }
        
        return all_configs
    
    def _build_mixed_p2mp_config(self, service_name: str, vlan_id: int,
                                 source_device: str, source_interface: str,
                                 leaf_destinations: List[Dict],
                                 superspine_destinations: List[Dict]) -> Dict:
        """Build P2MP configuration for mixed leaf and superspine destinations"""
        all_configs = {}
        
        # Build P2MP config for leaf destinations
        if leaf_destinations:
            leaf_config = self._build_leaf_p2mp_config(
                service_name, vlan_id,
                source_device, source_interface,
                leaf_destinations
            )
            
            # Merge leaf configs
            for device, device_config in leaf_config.items():
                if device != '_metadata':
                    if device not in all_configs:
                        all_configs[device] = []
                    all_configs[device].extend(device_config)
        
        # Build individual P2P configs for superspine destinations
        successful_superspine_configs = 0
        for dest in superspine_destinations:
            dest_device = dest['device']
            dest_interface = dest['port']
            
            try:
                config = self._build_leaf_to_superspine_p2p_config(
                    service_name, vlan_id,
                    source_device, source_interface,
                    dest_device, dest_interface
                )
                
                # Merge configs with deduplication
                for device, device_config in config.items():
                    if device != '_metadata':
                        if device not in all_configs:
                            all_configs[device] = []
                        
                        # Deduplicate configurations for this device
                        existing_configs = set(all_configs[device])
                        new_configs = []
                        
                        for config_line in device_config:
                            if config_line not in existing_configs:
                                new_configs.append(config_line)
                                existing_configs.add(config_line)
                        
                        all_configs[device].extend(new_configs)
                
                successful_superspine_configs += 1
                
            except Exception as e:
                self.logger.error(f"Failed to build config for {dest_device}: {e}")
        
        # Add unified metadata
        all_configs['_metadata'] = {
            'service_name': service_name,
            'vlan_id': vlan_id,
            'topology_type': 'P2MP_MIXED',
            'source_device': source_device,
            'leaf_destinations': [dest['device'] for dest in leaf_destinations],
            'superspine_destinations': [dest['device'] for dest in superspine_destinations],
            'source_device_type': 'leaf',
            'successful_leaf_configs': len(leaf_destinations),
            'successful_superspine_configs': successful_superspine_configs,
            'total_destinations': len(leaf_destinations) + len(superspine_destinations)
        }
        
        return all_configs
    
    def _build_leaf_config(self, service_name: str, vlan_id: int,
                          device: str, user_port: str, spine_interface: str,
                          is_source: bool) -> List[str]:
        """Build leaf configuration"""
        config = []
        
        # Get bundle for spine interface
        spine_bundle = self.original_builder.get_bundle_for_interface(device, spine_interface)
        if not spine_bundle:
            raise ValueError(f"No bundle found for spine interface {spine_interface} on {device}")
        
        # Use bundle interface for spine connection
        config.append(f"network-services bridge-domain instance {service_name} interface {spine_bundle}.{vlan_id}")
        config.append(f"interfaces {spine_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {spine_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        # User port
        config.append(f"network-services bridge-domain instance {service_name} interface {user_port}.{vlan_id}")
        config.append(f"interfaces {user_port}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {user_port}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def _build_superspine_config(self, service_name: str, vlan_id: int,
                                device: str, in_interface: str, out_interface: str) -> List[str]:
        """Build superspine configuration"""
        config = []
        
        # Try to get bundle for in_interface (from spine)
        in_bundle = self._get_bundle_for_superspine_interface(device, in_interface)
        if in_bundle:
            config.append(f"network-services bridge-domain instance {service_name} interface {in_bundle}.{vlan_id}")
            config.append(f"interfaces {in_bundle}.{vlan_id} l2-service enabled")
            config.append(f"interfaces {in_bundle}.{vlan_id} vlan-id {vlan_id}")
        else:
            # Use direct interface
            config.append(f"network-services bridge-domain instance {service_name} interface {in_interface}.{vlan_id}")
            config.append(f"interfaces {in_interface}.{vlan_id} l2-service enabled")
            config.append(f"interfaces {in_interface}.{vlan_id} vlan-id {vlan_id}")
        
        # Try to get bundle for out_interface (user port)
        out_bundle = self._get_bundle_for_superspine_interface(device, out_interface)
        if out_bundle:
            config.append(f"network-services bridge-domain instance {service_name} interface {out_bundle}.{vlan_id}")
            config.append(f"interfaces {out_bundle}.{vlan_id} l2-service enabled")
            config.append(f"interfaces {out_bundle}.{vlan_id} vlan-id {vlan_id}")
        else:
            # Use direct interface
            config.append(f"network-services bridge-domain instance {service_name} interface {out_interface}.{vlan_id}")
            config.append(f"interfaces {out_interface}.{vlan_id} l2-service enabled")
            config.append(f"interfaces {out_interface}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def _validate_p2p_topology(self, source_type: DeviceType, dest_type: DeviceType) -> bool:
        """Validate P2P topology constraints"""
        # Only leaf → leaf and leaf → superspine are supported
        if source_type == DeviceType.LEAF:
            return dest_type in [DeviceType.LEAF, DeviceType.SUPERSPINE]
        return False
    
    def get_available_interfaces(self, device_name: str) -> List[str]:
        """Get available interfaces for a device"""
        device_type = self.get_device_type(device_name)
        
        if device_type == DeviceType.LEAF:
            # Generate common leaf interfaces
            interfaces = []
            for i in range(1, 49):
                interfaces.append(f"ge100-0/0/{i}")
            return interfaces
        elif device_type == DeviceType.SUPERSPINE:
            # Get available superspine interfaces (not connected to spines)
            return self._get_available_superspine_interfaces(device_name)
        else:
            # For other device types, generate a basic list
            interfaces = []
            for i in range(1, 25):
                interfaces.append(f"ge10-0/0/{i}")
                interfaces.append(f"ge100-0/0/{i}")
            return interfaces
    
    def _get_available_superspine_interfaces(self, superspine_device: str) -> List[str]:
        """Get available interfaces for a superspine device"""
        devices = self.topology_data.get('devices', {})
        
        # Handle NCC variants
        normalized_device = superspine_device.replace('-NCC0', '').replace('-NCC1', '')
        actual_device = None
        
        # Find the actual device name in topology
        for device_name in devices.keys():
            if device_name.replace('-NCC0', '').replace('-NCC1', '') == normalized_device:
                actual_device = device_name
                break
        
        if not actual_device:
            return []
        
        device_info = devices.get(actual_device, {})
        all_interfaces = set(device_info.get('interfaces', []))
        connected_interfaces = set()
        
        # Find interfaces connected to spines
        for conn in device_info.get('connected_spines', []):
            if isinstance(conn, dict):
                connected_interfaces.add(conn['local_interface'])
        
        # Return available interfaces (not connected to spines)
        available_interfaces = all_interfaces - connected_interfaces
        return sorted(list(available_interfaces))
    
    def save_configuration(self, configs: Dict, output_file: str = "unified_bridge_domain_config.yaml"):
        """Save configuration to file"""
        try:
            # Ensure the directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                yaml.dump(configs, f, default_flow_style=False, indent=2)
            self.logger.info(f"Configuration saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def get_configuration_summary(self, configs: Dict) -> str:
        """Get configuration summary"""
        metadata = configs.get('_metadata', {})
        
        summary = f"""
📋 Unified Configuration Summary
──────────────────────────────
Service Name: {metadata.get('service_name', 'N/A')}
VLAN ID: {metadata.get('vlan_id', 'N/A')}
Topology Type: {metadata.get('topology_type', 'N/A')}
Source Device: {metadata.get('source_device', 'N/A')}
"""
        
        if metadata.get('topology_type') == 'P2P':
            summary += f"Destination Device: {metadata.get('dest_device', 'N/A')}\n"
            summary += f"Path: {' → '.join(metadata.get('path', []))}\n"
        elif metadata.get('topology_type') == 'P2MP':
            summary += f"Total Destinations: {metadata.get('total_destinations', 'N/A')}\n"
            if 'leaf_destinations' in metadata:
                summary += f"Leaf Destinations: {len(metadata['leaf_destinations'])}\n"
            if 'superspine_destinations' in metadata:
                summary += f"Superspine Destinations: {len(metadata['superspine_destinations'])}\n"
        
        device_count = len([k for k in configs.keys() if k != '_metadata'])
        summary += f"Devices Configured: {device_count}\n"
        
        return summary 

    def _find_actual_device_name_for_bundle(self, consolidated_device: str) -> Optional[str]:
        """Find the actual device name in bundle mappings for a consolidated device name"""
        bundles = self.bundle_mappings.get('bundles', {})
        
        # Try to find a bundle that matches the consolidated device name
        for bundle_key, bundle_info in bundles.items():
            if isinstance(bundle_info, dict) and 'device' in bundle_info:
                bundle_device = bundle_info['device']
                # Check if this bundle device matches our consolidated device
                # Remove NCC suffixes and normalize case
                normalized_bundle_device = bundle_device.replace('-NCC0', '').replace('-NCC1', '')
                normalized_consolidated = consolidated_device.replace('SUPERSPINE', 'SuperSpine')
                
                if normalized_bundle_device == normalized_consolidated:
                    return bundle_device
        
        return None
    
    def _get_bundle_for_superspine_interface(self, device: str, interface: str) -> Optional[str]:
        """Get bundle for superspine interface with proper device name handling"""
        # First try with the original device name
        bundle = self.original_builder.get_bundle_for_interface(device, interface)
        if bundle:
            return bundle
        
        # If not found, try to find the actual device name in bundle mappings
        actual_device = self._find_actual_device_name_for_bundle(device)
        if actual_device:
            bundle = self.original_builder.get_bundle_for_interface(actual_device, interface)
            if bundle:
                return bundle
        
        return None 