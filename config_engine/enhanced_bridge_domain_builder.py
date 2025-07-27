#!/usr/bin/env python3
"""
Enhanced Bridge Domain Builder with Superspine Support
Extends the original BridgeDomainBuilder to support superspine destinations.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .enhanced_device_types import (
    DeviceType, InterfaceType, enhanced_classifier
)
from .device_name_normalizer import normalizer
from .bridge_domain_builder import BridgeDomainBuilder

class EnhancedBridgeDomainBuilder:
    """
    Enhanced bridge domain builder that extends the original BridgeDomainBuilder.
    
    Adds support for:
    - Superspine devices as destinations only
    - No AC interfaces on Superspine (transport only)
    - No Superspine → Superspine topologies
    - P2P and P2MP topologies ending at Superspine
    """
    
    def __init__(self, topology_dir: str = "topology"):
        """
        Initialize enhanced bridge domain builder.
        
        Args:
            topology_dir: Directory containing topology files
        """
        self.topology_dir = Path(topology_dir)
        self.logger = logging.getLogger('EnhancedBridgeDomainBuilder')
        
        # Initialize the original bridge domain builder
        self.original_builder = BridgeDomainBuilder(topology_dir)
        
        # Initialize device name normalizer
        self.normalizer = normalizer
        
        # Load topology data
        self.topology_data = self.original_builder.topology_data
        self.bundle_mappings = self.original_builder.bundle_mappings
    
    def get_device_type(self, device_name: str) -> DeviceType:
        """
        Get device type for a device.
        
        Args:
            device_name: Device name
            
        Returns:
            DeviceType enum value
        """
        return enhanced_classifier.detect_device_type(device_name)
    
    def get_available_sources(self) -> List[Dict]:
        """
        Get available source devices (leafs only).
        
        Returns:
            List of device info dictionaries
        """
        available_leaves = self.original_builder.get_available_leaves()
        devices = []
        
        for leaf_name in available_leaves:
            devices.append({
                'name': leaf_name,
                'device_type': DeviceType.LEAF
            })
        
        return devices
    
    def get_available_destinations(self, source_device: str) -> List[Dict]:
        """
        Get available destination devices (leafs + superspines).
        
        Args:
            source_device: Source device name
            
        Returns:
            List of device info dictionaries
        """
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
        topology_data = self.original_builder.topology_data
        if topology_data:
            superspine_devices = topology_data.get('superspine_devices', [])
            for superspine_name in superspine_devices:
                devices.append({
                    'name': superspine_name,
                    'device_type': DeviceType.SUPERSPINE
                })
        
        return devices
    
    def validate_interface_for_device(self, interface: str, device_name: str) -> bool:
        """
        Validate interface for device type.
        
        Args:
            interface: Interface name
            device_name: Device name
            
        Returns:
            True if valid, False otherwise
        """
        device_type = self.get_device_type(device_name)
        return enhanced_classifier.validate_interface_for_device(interface, device_type)
    
    def validate_path_topology(self, source_device: str, dest_device: str) -> bool:
        """
        Validate topology constraints.
        
        Args:
            source_device: Source device name
            dest_device: Destination device name
            
        Returns:
            True if valid topology, False otherwise
        """
        source_type = self.get_device_type(source_device)
        dest_type = self.get_device_type(dest_device)
        
        return enhanced_classifier.validate_topology_constraints(source_type, dest_type)
    
    def calculate_path_to_superspine(self, source_leaf: str, dest_superspine: str) -> List[str]:
        """
        Calculate path from leaf to superspine through spine.
        
        Args:
            source_leaf: Source leaf device name
            dest_superspine: Destination superspine device name
            
        Returns:
            List of devices in the path: [source_leaf, spine, dest_superspine]
        """
        if not self.topology_data:
            raise ValueError("No topology data available")
        
        devices = self.topology_data.get('devices', {})
        
        # Find spine connected to source leaf
        source_spine = None
        source_leaf_conn = None
        
        leaf_info = devices.get(source_leaf, {})
        for spine_conn in leaf_info.get('connected_spines', []):
            if isinstance(spine_conn, dict):
                spine_name = spine_conn['name']
                # Check if this spine connects to the superspine
                spine_info = devices.get(spine_name, {})
                for superspine_conn in spine_info.get('connected_superspines', []):
                    if isinstance(superspine_conn, dict):
                        # Check both the full name and the normalized name
                        superspine_name = superspine_conn['name']
                        normalized_name = superspine_name.replace('-NCC0', '').replace('-NCC1', '')
                        if superspine_name == dest_superspine or normalized_name == dest_superspine:
                            source_spine = spine_name
                            source_leaf_conn = spine_conn
                            break
                if source_spine:
                    break
        
        if not source_spine:
            raise ValueError(f"Could not find spine connecting {source_leaf} to {dest_superspine}")
        
        return [source_leaf, source_spine, dest_superspine]
    
    def detect_topology_type(self, source_device: str, dest_device: str) -> str:
        """
        Detect topology type.
        
        Args:
            source_device: Source device name
            dest_device: Destination device name
            
        Returns:
            Topology type: 'P2P' or 'P2MP'
        """
        dest_type = self.get_device_type(dest_device)
        
        if dest_type == DeviceType.SUPERSPINE:
            # Leaf → Superspine: Always P2P
            return 'P2P'
        elif dest_type == DeviceType.LEAF:
            # Leaf → Leaf: Use original logic
            return 'P2P'  # Simplified for now
        
        return 'UNKNOWN'
    
    def build_bridge_domain_config(self, service_name: str, vlan_id: int,
                                 source_device: str, source_interface: str,
                                 dest_device: str, dest_interface: str) -> Dict:
        """
        Build bridge domain configuration using original builder logic.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_device: Source device name
            source_interface: Source interface name
            dest_device: Destination device name
            dest_interface: Destination interface name
            
        Returns:
            Bridge domain configuration dictionary
        """
        source_type = self.get_device_type(source_device)
        dest_type = self.get_device_type(dest_device)
        
        # Validate topology constraints
        if not self.validate_path_topology(source_device, dest_device):
            raise ValueError(f"Invalid topology: {source_type.value} → {dest_type.value}")
        
        # Use original builder for leaf-to-leaf
        if dest_type == DeviceType.LEAF:
            return self.original_builder.build_bridge_domain_config(
                service_name, vlan_id,
                source_device, source_interface,
                dest_device, dest_interface
            )
        
        # Handle leaf-to-superspine
        elif dest_type == DeviceType.SUPERSPINE:
            return self._build_leaf_to_superspine_config(
                service_name, vlan_id,
                source_device, source_interface,
                dest_device, dest_interface
            )
        
        else:
            raise ValueError(f"Unsupported destination device type: {dest_type}")
    
    def _build_leaf_to_superspine_config(self, service_name: str, vlan_id: int,
                                        source_leaf: str, source_interface: str,
                                        dest_superspine: str, dest_interface: str) -> Dict:
        """
        Build bridge domain configuration for leaf-to-superspine path using original builder's approach.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_leaf: Source leaf device name
            source_interface: Source interface name
            dest_superspine: Destination superspine device name
            dest_interface: Destination interface name
            
        Returns:
            Bridge domain configuration dictionary
        """
        # Use the original builder's path calculation logic
        # For leaf-to-superspine, we need to create a 3-tier path: Leaf → Spine → Superspine
        
        # Get topology data
        devices = self.topology_data.get('devices', {})
        
        # Find spine connected to source leaf
        source_leaf_info = devices.get(source_leaf, {})
        source_spine = None
        source_leaf_conn = None
        
        for spine_conn in source_leaf_info.get('connected_spines', []):
            if isinstance(spine_conn, dict):
                spine_name = spine_conn['name']
                # Check if this spine connects to the superspine
                spine_info = devices.get(spine_name, {})
                spine_superspines = spine_info.get('connected_superspines', [])
                
                for superspine_conn in spine_superspines:
                    if isinstance(superspine_conn, dict):
                        # Treat NCC0 and NCC1 as the same chassis
                        superspine_name = superspine_conn['name']
                        normalized_superspine = superspine_name.replace('-NCC0', '').replace('-NCC1', '')
                        normalized_dest = dest_superspine.replace('-NCC0', '').replace('-NCC1', '')
                        
                        if normalized_superspine == normalized_dest:
                            source_spine = spine_name
                            source_leaf_conn = spine_conn
                            break
                if source_spine:
                    break
        
        if not source_spine:
            raise ValueError(f"Could not find spine connecting {source_leaf} to {dest_superspine}")
        
        # Find spine-to-superspine connection
        spine_info = devices.get(source_spine, {})
        spine_superspine_conn = None
        for superspine_conn in spine_info.get('connected_superspines', []):
            if isinstance(superspine_conn, dict):
                # Treat NCC0 and NCC1 as the same chassis
                superspine_name = superspine_conn['name']
                normalized_superspine = superspine_name.replace('-NCC0', '').replace('-NCC1', '')
                normalized_dest = dest_superspine.replace('-NCC0', '').replace('-NCC1', '')
                
                if normalized_superspine == normalized_dest:
                    spine_superspine_conn = superspine_conn
                    break
        
        if not spine_superspine_conn:
            raise ValueError(f"Could not find superspine connection for {source_spine}")
        
        # Create path segments like the original builder
        segments = [
            {
                'type': 'leaf_to_spine',
                'source_device': source_leaf,
                'dest_device': source_spine,
                'source_interface': source_leaf_conn['local_interface'],
                'dest_interface': source_leaf_conn['remote_interface']
            },
            {
                'type': 'spine_to_superspine',
                'source_device': source_spine,
                'dest_device': dest_superspine,
                'source_interface': spine_superspine_conn['local_interface'],
                'dest_interface': spine_superspine_conn['remote_interface']
            }
        ]
        
        # Build configurations using original builder's methods
        configs = {}
        
        # Source Leaf Configuration
        leaf_segment = next(seg for seg in segments if seg['type'] == 'leaf_to_spine')
        source_leaf_config = self._build_leaf_config_hybrid(
            service_name, vlan_id, source_leaf,
            source_interface, leaf_segment['source_interface'],  # Use leaf interface, not spine interface
            is_source=True
        )
        configs[source_leaf] = source_leaf_config
        
        # Spine Configuration
        spine_segment = next(seg for seg in segments if seg['type'] == 'spine_to_superspine')
        spine_config = self.original_builder._build_spine_config(
            service_name, vlan_id, source_spine,
            leaf_segment['dest_interface'], spine_segment['source_interface']
        )
        configs[source_spine] = spine_config
        
        # Superspine Configuration
        # Validate that the destination interface is available
        if not self.validate_superspine_interface(dest_superspine, dest_interface):
            available_interfaces = self.get_available_superspine_interfaces(dest_superspine)
            raise ValueError(
                f"Interface {dest_interface} is not available on {dest_superspine}. "
                f"Available interfaces: {available_interfaces[:10]}{'...' if len(available_interfaces) > 10 else ''}"
            )
        
        # Get the actual device name from the topology connection for bundle lookup
        actual_superspine_device = spine_superspine_conn['name']
        
        superspine_config = self._build_superspine_config_hybrid(
            service_name, vlan_id, dest_superspine,
            spine_segment['dest_interface'], dest_interface, actual_superspine_device  # Pass actual device for bundle lookup
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
    
    def _build_leaf_config_hybrid(self, service_name: str, vlan_id: int,
                                 device: str, user_port: str, spine_interface: str,
                                 is_source: bool) -> List[str]:
        """
        Build leaf configuration that handles both bundle and direct interfaces.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            device: Device name
            user_port: User-specified port
            spine_interface: Interface to spine
            is_source: True if source leaf, False if destination
            
        Returns:
            List of configuration commands
        """
        config = []
        
        # Try to get bundle for spine interface
        spine_bundle = self.original_builder.get_bundle_for_interface(device, spine_interface)
        
        if not spine_bundle:
            raise ValueError(f"No bundle found for spine interface {spine_interface} on {device}. "
                           f"Uplink interfaces must use bundles, not physical interfaces.")
        
        # Use bundle interface for spine connection
        config.append(f"network-services bridge-domain instance {service_name} interface {spine_bundle}.{vlan_id}")
        config.append(f"interfaces {spine_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {spine_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        # User port (always use direct interface)
        config.append(f"network-services bridge-domain instance {service_name} interface {user_port}.{vlan_id}")
        config.append(f"interfaces {user_port}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {user_port}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def _build_superspine_config_hybrid(self, service_name: str, vlan_id: int,
                                       device: str, in_interface: str, out_interface: str, 
                                       actual_device: str = None) -> List[str]:
        """
        Build superspine configuration that handles both bundle and direct interfaces.
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            device: Device name for configuration
            in_interface: Interface from spine (superspine interface)
            out_interface: User-specified AC interface
            actual_device: Actual device name for bundle lookup (if different from device)
            
        Returns:
            List of configuration commands
        """
        config = []
        
        # Use actual_device for bundle lookup if provided, otherwise use device
        bundle_lookup_device = actual_device if actual_device else device
        
        # Try to get bundle for in_interface (from spine) - this should be a bundle
        in_bundle = self.original_builder.get_bundle_for_interface(bundle_lookup_device, in_interface)
        if not in_bundle:
            raise ValueError(f"No bundle found for spine interface {in_interface} on {bundle_lookup_device}. "
                           f"Downlink interfaces must use bundles, not physical interfaces.")
        
        # Use bundle interface for spine connection
        config.append(f"network-services bridge-domain instance {service_name} interface {in_bundle}.{vlan_id}")
        config.append(f"interfaces {in_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {in_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        # For out_interface (user AC port), try to get bundle but allow fallback to physical
        out_bundle = self.original_builder.get_bundle_for_interface(device, out_interface)
        if out_bundle:
            # Use bundle if available for user port
            config.append(f"network-services bridge-domain instance {service_name} interface {out_bundle}.{vlan_id}")
            config.append(f"interfaces {out_bundle}.{vlan_id} l2-service enabled")
            config.append(f"interfaces {out_bundle}.{vlan_id} vlan-id {vlan_id}")
        else:
            # Use direct interface for user port (AC interface)
            config.append(f"network-services bridge-domain instance {service_name} interface {out_interface}.{vlan_id}")
            config.append(f"interfaces {out_interface}.{vlan_id} l2-service enabled")
            config.append(f"interfaces {out_interface}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def _build_superspine_direct_config(self, service_name: str, vlan_id: int,
                                       device: str, in_interface: str, out_interface: str) -> List[str]:
        """
        Build configuration for a superspine device using direct interfaces (no bundles).
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            device: Device name
            in_interface: Interface from spine
            out_interface: Interface to destination
            
        Returns:
            List of configuration commands
        """
        config = []
        
        # Bridge domain instance with both interfaces
        config.append(f"network-services bridge-domain instance {service_name} interface {in_interface}.{vlan_id}")
        config.append(f"interfaces {in_interface}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {in_interface}.{vlan_id} vlan-id {vlan_id}")
        
        config.append(f"network-services bridge-domain instance {service_name} interface {out_interface}.{vlan_id}")
        config.append(f"interfaces {out_interface}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {out_interface}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def save_configuration(self, configs: Dict, output_file: str = "enhanced_bridge_domain_config.yaml"):
        """
        Save configuration to file.
        
        Args:
            configs: Configuration dictionary
            output_file: Output file name
        """
        try:
            with open(output_file, 'w') as f:
                yaml.dump(configs, f, default_flow_style=False, indent=2)
            self.logger.info(f"Configuration saved to {output_file}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def get_configuration_summary(self, configs: Dict) -> str:
        """
        Get configuration summary.
        
        Args:
            configs: Configuration dictionary
            
        Returns:
            Summary string
        """
        metadata = configs.get('_metadata', {})
        
        summary = f"""
📋 Configuration Summary
───────────────────────
Service Name: {metadata.get('service_name', 'N/A')}
VLAN ID: {metadata.get('vlan_id', 'N/A')}
Topology Type: {metadata.get('topology_type', 'N/A')}
Source Device: {metadata.get('source_device', 'N/A')} ({metadata.get('source_device_type', 'N/A')})
Destination Device: {metadata.get('dest_device', 'N/A')} ({metadata.get('dest_device_type', 'N/A')})
Path: {' → '.join(metadata.get('path', []))}
Devices Configured: {len([k for k in configs.keys() if k != '_metadata'])}
"""
        return summary
    
    def visualize_paths(self, path_calculation: Dict) -> str:
        """
        Visualize paths for the configuration.
        
        Args:
            path_calculation: Path calculation dictionary
            
        Returns:
            Visualization string
        """
        if not path_calculation:
            return "No path information available"
        
        visualization = "\n🌳 Path Visualization:\n"
        path = path_calculation.get('path', [])
        
        for i, device in enumerate(path):
            device_type = self.get_device_type(device)
            icon = enhanced_classifier.get_device_type_icon(device_type)
            
            if i == 0:
                visualization += f"  {icon} {device} (Source)\n"
            elif i == len(path) - 1:
                visualization += f"  {icon} {device} (Destination)\n"
            else:
                visualization += f"  {icon} {device} (Intermediate)\n"
            
            if i < len(path) - 1:
                visualization += "  ↓\n"
        
        return visualization 

    def get_available_superspine_interfaces(self, superspine_device: str) -> List[str]:
        """
        Get available interfaces for a superspine device (not connected to spines).
        
        Args:
            superspine_device: Superspine device name
            
        Returns:
            List of available interface names
        """
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
    
    def validate_superspine_interface(self, superspine_device: str, interface: str) -> bool:
        """
        Validate if an interface is available on a superspine device.
        
        Args:
            superspine_device: Superspine device name
            interface: Interface name to validate
            
        Returns:
            True if interface is available, False otherwise
        """
        available_interfaces = self.get_available_superspine_interfaces(superspine_device)
        return interface in available_interfaces 