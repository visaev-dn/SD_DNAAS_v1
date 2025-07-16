#!/usr/bin/env python3
"""
Bridge Domain Configuration Builder
Builds bridge domain configurations across spine-leaf topology
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .device_name_normalizer import normalizer

class BridgeDomainBuilder:
    """Builds bridge domain configurations for spine-leaf topology"""
    
    def __init__(self, topology_dir: str = "topology"):
        """
        Initialize bridge domain builder
        
        Args:
            topology_dir: Directory containing topology files
        """
        self.topology_dir = Path(topology_dir)
        self.logger = logging.getLogger('BridgeDomainBuilder')
        
        # Initialize device name normalizer
        self.normalizer = normalizer
        
        # Load topology data
        self.topology_data = self._load_topology_data()
        self.bundle_mappings = self._load_bundle_mappings()
        
        # Apply normalization to topology data if needed
        self._normalize_topology_data()
    
    def _normalize_topology_data(self):
        """Apply device name normalization to topology data."""
        if not self.topology_data:
            return
        
        # Check if we should use enhanced topology
        enhanced_topology_file = self.topology_dir / "enhanced_topology.json"
        if enhanced_topology_file.exists():
            self.logger.info("Using enhanced topology with normalization")
            with open(enhanced_topology_file, 'r') as f:
                self.topology_data = json.load(f)
        else:
            self.logger.info("Applying normalization to existing topology data")
            self._apply_normalization_to_topology()
    
    def _apply_normalization_to_topology(self):
        """Apply normalization to existing topology data."""
        if not self.topology_data:
            return
        
        devices = self.topology_data.get('devices', {})
        normalized_devices = {}
        
        for device_name, device_info in devices.items():
            normalized_name = self.normalizer.normalize_device_name(device_name)
            normalized_devices[normalized_name] = device_info
            
            # Update device name in device info
            device_info['name'] = normalized_name
            
            # Normalize connected spines
            if 'connected_spines' in device_info:
                normalized_spines = []
                for spine_conn in device_info['connected_spines']:
                    if isinstance(spine_conn, dict):
                        # Handle new format with connection details
                        spine_name = spine_conn.get('name', '')
                        normalized_spine_name = self.normalizer.normalize_device_name(spine_name)
                        spine_conn['name'] = normalized_spine_name
                        normalized_spines.append(spine_conn)
                    else:
                        # Handle old format with just spine names
                        normalized_spine = self.normalizer.normalize_device_name(spine_conn)
                        normalized_spines.append(normalized_spine)
                device_info['connected_spines'] = normalized_spines
        
        self.topology_data['devices'] = normalized_devices
        
        # Normalize device lists
        for key in ['available_leaves', 'unavailable_leaves', 'superspine_devices', 'spine_devices']:
            if key in self.topology_data:
                normalized_list = []
                for device in self.topology_data[key]:
                    normalized_device = self.normalizer.normalize_device_name(device)
                    normalized_list.append(normalized_device)
                self.topology_data[key] = normalized_list
    
    def _load_topology_data(self) -> Dict:
        """Load topology data from JSON file"""
        try:
            # Try V2 topology first
            topology_file = self.topology_dir / "complete_topology_v2.json"
            if topology_file.exists():
                with open(topology_file, 'r') as f:
                    return json.load(f)
            
            # Fallback to old topology format
            topology_file = self.topology_dir / "complete_topology.json"
            if topology_file.exists():
                with open(topology_file, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Topology file not found: {topology_file}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load topology data: {e}")
            return {}
    
    def _load_bundle_mappings(self) -> Dict:
        """Load bundle interface mappings"""
        try:
            # Try V2 bundle mapping first
            bundle_file = self.topology_dir / "bundle_mapping_v2.yaml"
            if bundle_file.exists():
                with open(bundle_file, 'r') as f:
                    return yaml.safe_load(f)
            
            # Fallback to old bundle mapping format
            bundle_file = self.topology_dir / "bundle_interface_mapping.yaml"
            if bundle_file.exists():
                with open(bundle_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                self.logger.warning(f"Bundle mapping file not found: {bundle_file}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load bundle mappings: {e}")
            return {}
    
    def calculate_path(self, source_leaf: str, dest_leaf: str) -> Optional[Dict]:
        """
        Calculate the path from source leaf to destination leaf through the three-tier or two-tier architecture
        """
        if not self.topology_data:
            self.logger.error("No topology data available")
            return None
        
        # Normalize device names for path calculation
        normalized_source_leaf = self.normalizer.normalize_device_name(source_leaf)
        normalized_dest_leaf = self.normalizer.normalize_device_name(dest_leaf)
        self.logger.info(f"[PATH] Normalized device names: {source_leaf} -> {normalized_source_leaf}, {dest_leaf} -> {normalized_dest_leaf}")
        
        # Load the new topology format
        devices = self.topology_data.get('devices', {})
        
        # Classify devices by type
        superspine_devices = []
        spine_devices = []
        leaf_devices = []
        for device_name, device_info in devices.items():
            device_type = device_info.get('type', 'unknown')
            if device_type == 'superspine':
                superspine_devices.append(device_name)
            elif device_type == 'spine':
                spine_devices.append(device_name)
            elif device_type == 'leaf':
                leaf_devices.append(device_name)
        self.logger.info(f"[PATH] Found {len(superspine_devices)} superspine, {len(spine_devices)} spine, {len(leaf_devices)} leaf devices")
        
        # Build device connection map from connected_spines data
        device_connections = {}
        for device_name, device_info in devices.items():
            connected_spines = device_info.get('connected_spines', [])
            if connected_spines:
                device_connections[device_name] = []
                for spine_conn in connected_spines:
                    if isinstance(spine_conn, dict):
                        spine_name = spine_conn['name']
                        device_connections[device_name].append({
                            'device': spine_name,
                            'local_interface': spine_conn['local_interface'],
                            'remote_interface': spine_conn['remote_interface']
                        })
                        # Also add reverse connection for spine
                        if spine_name not in device_connections:
                            device_connections[spine_name] = []
                        device_connections[spine_name].append({
                            'device': device_name,
                            'local_interface': spine_conn['remote_interface'],
                            'remote_interface': spine_conn['local_interface']
                        })
                    else:
                        spine_name = spine_conn
                        device_connections[device_name].append({
                            'device': spine_name,
                            'local_interface': 'unknown',
                            'remote_interface': 'unknown'
                        })
                        if spine_name not in device_connections:
                            device_connections[spine_name] = []
                        device_connections[spine_name].append({
                            'device': device_name,
                            'local_interface': 'unknown',
                            'remote_interface': 'unknown'
                        })
        # Log all connections for each device
        for dev, conns in device_connections.items():
            self.logger.info(f"[CONNECTIONS] {dev}: {conns}")
        
        # Step 1: Find all spines connected to each leaf
        source_leaf_spines = set(conn['device'] for conn in device_connections.get(normalized_source_leaf, []) if conn['device'] in spine_devices)
        dest_leaf_spines = set(conn['device'] for conn in device_connections.get(normalized_dest_leaf, []) if conn['device'] in spine_devices)
        
        # Step 2: Check for shared spine (2-tier path)
        shared_spines = source_leaf_spines & dest_leaf_spines
        if shared_spines:
            shared_spine = list(shared_spines)[0]
            self.logger.info(f"[PATH] Found shared spine {shared_spine} for 2-tier path")
            source_leaf_conn = next(conn for conn in device_connections.get(normalized_source_leaf, []) if conn['device'] == shared_spine)
            dest_leaf_conn = next(conn for conn in device_connections.get(normalized_dest_leaf, []) if conn['device'] == shared_spine)
            self.logger.info(f"[PATH] 2-tier segments:")
            self.logger.info(f"  leaf_to_spine: {normalized_source_leaf} {source_leaf_conn['local_interface']} -> {shared_spine} {source_leaf_conn['remote_interface']}")
            self.logger.info(f"  spine_to_leaf: {shared_spine} {dest_leaf_conn['remote_interface']} -> {normalized_dest_leaf} {dest_leaf_conn['local_interface']}")
            path = {
                'source_leaf': normalized_source_leaf,
                'destination_leaf': normalized_dest_leaf,
                'source_spine': shared_spine,
                'superspine': None,
                'dest_spine': shared_spine,
                'segments': [
                    {
                        'type': 'leaf_to_spine',
                        'source_device': normalized_source_leaf,
                        'dest_device': shared_spine,
                        'source_interface': source_leaf_conn['local_interface'],
                        'dest_interface': source_leaf_conn['remote_interface']
                    },
                    {
                        'type': 'spine_to_leaf',
                        'source_device': shared_spine,
                        'dest_device': normalized_dest_leaf,
                        'source_interface': dest_leaf_conn['remote_interface'],
                        'dest_interface': dest_leaf_conn['local_interface']
                    }
                ]
            }
            return path
        # Step 3: 3-tier path (existing logic)
        source_spine = None
        source_leaf_conn = None
        for conn in device_connections.get(normalized_source_leaf, []):
            if conn['device'] in spine_devices:
                source_spine = conn['device']
                source_leaf_conn = conn
                break
        if not source_spine:
            self.logger.error(f"[PATH] Could not find spine connection for source leaf {normalized_source_leaf}")
            return None
        dest_spine = None
        dest_leaf_conn = None
        for conn in device_connections.get(normalized_dest_leaf, []):
            if conn['device'] in spine_devices:
                dest_spine = conn['device']
                dest_leaf_conn = conn
                break
        if not dest_spine:
            self.logger.error(f"[PATH] Could not find spine connection for destination leaf {normalized_dest_leaf}")
            return None
        superspine = None
        source_spine_to_superspine = None
        dest_spine_to_superspine = None
        source_spine_info = devices.get(source_spine, {})
        dest_spine_info = devices.get(dest_spine, {})
        source_spine_superspines = source_spine_info.get('connected_superspines', [])
        dest_spine_superspines = dest_spine_info.get('connected_superspines', [])
        source_superspine_names = {conn['name'] for conn in source_spine_superspines}
        dest_superspine_names = {conn['name'] for conn in dest_spine_superspines}
        common_superspines = source_superspine_names & dest_superspine_names
        if common_superspines:
            superspine = list(common_superspines)[0]
            source_spine_to_superspine = next(conn for conn in source_spine_superspines if conn['name'] == superspine)
            dest_spine_to_superspine = next(conn for conn in dest_spine_superspines if conn['name'] == superspine)
            self.logger.info(f"[PATH] Found common superspine {superspine} using connected_superspines data")
        else:
            for superspine_name in superspine_devices:
                superspine_conns = device_connections.get(superspine_name, [])
                source_spine_conn = None
                dest_spine_conn = None
                for conn in superspine_conns:
                    if conn['device'] == source_spine:
                        source_spine_conn = conn
                    elif conn['device'] == dest_spine:
                        dest_spine_conn = conn
                if source_spine_conn and dest_spine_conn:
                    superspine = superspine_name
                    source_spine_to_superspine = source_spine_conn
                    dest_spine_to_superspine = dest_spine_conn
                    self.logger.info(f"[PATH] Found common superspine {superspine} using fallback method")
                    break
        if not superspine:
            self.logger.error(f"[PATH] Could not find common super spine for {source_spine} and {dest_spine}")
            self.logger.error(f"[PATH] Source spine superspines: {[conn['name'] for conn in source_spine_superspines]}")
            self.logger.error(f"[PATH] Dest spine superspines: {[conn['name'] for conn in dest_spine_superspines]}")
            return None
        path = {
            'source_leaf': normalized_source_leaf,
            'destination_leaf': normalized_dest_leaf,
            'source_spine': source_spine,
            'superspine': superspine,
            'dest_spine': dest_spine,
            'segments': []
        }
        # Segment 1: Source Leaf → Source Spine
        path['segments'].append({
            'type': 'leaf_to_spine',
            'source_device': normalized_source_leaf,
            'dest_device': source_spine,
            'source_interface': source_leaf_conn['local_interface'],
            'dest_interface': source_leaf_conn['remote_interface']
        })
        # Segment 2: Source Spine → Super Spine
        if isinstance(source_spine_to_superspine, dict) and 'local_interface' in source_spine_to_superspine:
            path['segments'].append({
                'type': 'spine_to_superspine',
                'source_device': source_spine,
                'dest_device': superspine,
                'source_interface': source_spine_to_superspine['local_interface'],
                'dest_interface': source_spine_to_superspine['remote_interface']
            })
        else:
            path['segments'].append({
                'type': 'spine_to_superspine',
                'source_device': source_spine,
                'dest_device': superspine,
                'source_interface': source_spine_to_superspine['remote_interface'],
                'dest_interface': source_spine_to_superspine['local_interface']
            })
        # Segment 3: Super Spine → Destination Spine
        if isinstance(dest_spine_to_superspine, dict) and 'local_interface' in dest_spine_to_superspine:
            path['segments'].append({
                'type': 'superspine_to_spine',
                'source_device': superspine,
                'dest_device': dest_spine,
                'source_interface': dest_spine_to_superspine['remote_interface'],
                'dest_interface': dest_spine_to_superspine['local_interface']
            })
        else:
            path['segments'].append({
                'type': 'superspine_to_spine',
                'source_device': superspine,
                'dest_device': dest_spine,
                'source_interface': dest_spine_to_superspine['local_interface'],
                'dest_interface': dest_spine_to_superspine['remote_interface']
            })
        # Segment 4: Destination Spine → Destination Leaf
        path['segments'].append({
            'type': 'spine_to_leaf',
            'source_device': dest_spine,
            'dest_device': normalized_dest_leaf,
            'source_interface': dest_leaf_conn['remote_interface'],
            'dest_interface': dest_leaf_conn['local_interface']
        })
        self.logger.info(f"[PATH] 3-tier segments:")
        for seg in path['segments']:
            self.logger.info(f"  {seg['type']}: {seg['source_device']} {seg['source_interface']} -> {seg['dest_device']} {seg['dest_interface']}")
        self.logger.info(f"[PATH] Calculated path: {normalized_source_leaf} → {source_spine} → {superspine} → {dest_spine} → {normalized_dest_leaf}")
        return path
    
    def get_bundle_for_interface(self, device: str, interface: str) -> Optional[str]:
        """
        Get bundle name for a physical interface
        """
        bundles = self.bundle_mappings.get('bundles', {})
        for bundle_key, bundle_info in bundles.items():
            if bundle_info.get('device') == device:
                members = bundle_info.get('members', [])
                if interface in members:
                    self.logger.info(f"[BUNDLE] Bundle lookup: {device} {interface} -> {bundle_info.get('name')}")
                    return bundle_info.get('name')
        device_variations = [
            device,
            device.upper(),
            device.lower(),
            device.replace('_', '-'),
            device.replace('-', '_'),
            device.replace('SUPERSPINE', 'SuperSpine'),
            device.replace('SuperSpine', 'SUPERSPINE'),
            device.replace('SPINE', 'Spine'),
            device.replace('Spine', 'SPINE'),
            device.replace('LEAF', 'Leaf'),
            device.replace('Leaf', 'LEAF'),
        ]
        for device_variant in device_variations:
            for bundle_key, bundle_info in bundles.items():
                if bundle_info.get('device') == device_variant:
                    members = bundle_info.get('members', [])
                    if interface in members:
                        self.logger.info(f"[BUNDLE] Bundle lookup: {device_variant} {interface} -> {bundle_info.get('name')}")
                        return bundle_info.get('name')
        device_mappings = self.bundle_mappings.get(device, {})
        if interface in device_mappings:
            self.logger.info(f"[BUNDLE] Bundle lookup: {device} {interface} -> {device_mappings[interface]}")
            return device_mappings[interface]
        for device_variant in device_variations:
            device_mappings = self.bundle_mappings.get(device_variant, {})
            if interface in device_mappings:
                self.logger.info(f"[BUNDLE] Bundle lookup: {device_variant} {interface} -> {device_mappings[interface]}")
                return device_mappings[interface]
        self.logger.warning(f"[BUNDLE] Bundle lookup: {device} {interface} -> NOT FOUND")
        return None
    
    def _find_bundle_for_device(self, device_name: str, interface_name: str) -> Optional[Dict]:
        """Find bundle information for a device and interface using canonical keys."""
        if not hasattr(self, 'bundle_mappings') or not self.bundle_mappings:
            return None
        bundles = self.bundle_mappings.get('bundles', {})
        if not bundles:
            return None
        device_key = self.normalizer.canonical_key(device_name)
        for bundle_name, bundle_info in bundles.items():
            if isinstance(bundle_info, dict) and 'device' in bundle_info:
                bundle_device = bundle_info['device']
                bundle_device_key = self.normalizer.canonical_key(bundle_device)
                if bundle_device_key == device_key:
                    members = bundle_info.get('members', [])
                    if interface_name in members:
                        self.logger.info(f"[BUNDLE] Bundle lookup: {device_name} {interface_name} using device variant {bundle_device} -> {bundle_info.get('name')}")
                        return bundle_info
            if '_bundle-' in bundle_name:
                bundle_device_from_name = bundle_name.split('_bundle-')[0]
                device_variations = [
                    device_name,
                    device_name.replace('-', '_'),
                    device_name.replace('_', '-'),
                    device_name.replace('SPINE-', 'SPINE_'),
                    device_name.replace('SPINE_', 'SPINE-'),
                ]
                if 'SPINE' in device_name and 'D14' in device_name:
                    device_variations.extend([
                        device_name.replace('SPINE-', 'SPINE-NCP1-'),
                        device_name.replace('SPINE-', 'SPINE-NCPL-'),
                        device_name.replace('SPINE-', 'SPINE-NCP-'),
                    ])
                
                # Also try SuperSpine vs SUPERSPINE variations
                if 'SUPERSPINE' in device_name:
                    device_variations.extend([
                        device_name.replace('SUPERSPINE', 'SuperSpine'),  # DNAAS-SuperSpine-D04
                        device_name.replace('SuperSpine', 'SUPERSPINE'),   # DNAAS-SUPERSPINE-D04
                    ])
                
                # Check if any variation matches the bundle device name
                for variation in device_variations:
                    if bundle_device_from_name == variation:
                        # Check if interface is in bundle members
                        members = bundle_info.get('members', [])
                        if interface_name in members:
                            self.logger.info(f"[BUNDLE] Bundle lookup: {device_name} {interface_name} using bundle name variation {bundle_device_from_name} -> {bundle_info.get('name')}")
                            return bundle_info
        self.logger.warning(f"[BUNDLE] Bundle lookup: {device_name} {interface_name} -> NOT FOUND")
        return None
    
    def get_available_leaves(self) -> List[str]:
        """
        Get list of leaves that are available for bridge domain calculations
        (excludes leaves connected to failed spines)
        
        Returns:
            List of available leaf device names
        """
        if not self.topology_data:
            return []
        
        # Check if we have available_leaves in the topology data
        available_leaves = self.topology_data.get('available_leaves', [])
        if available_leaves:
            self.logger.info(f"Found {len(available_leaves)} available leaves for bridge domain calculations")
            return available_leaves
        
        # Fallback: get all successful leaf devices
        devices = self.topology_data.get('devices', {})
        leaf_devices = []
        
        for device_name, device_info in devices.items():
            if device_info.get('type') == 'leaf':
                leaf_devices.append(device_name)
        
        self.logger.info(f"Using all {len(leaf_devices)} leaf devices (no availability filtering)")
        return leaf_devices
    
    def get_unavailable_leaves(self) -> Dict[str, Dict]:
        """
        Get information about leaves that are unavailable for bridge domain calculations
        
        Returns:
            Dictionary mapping leaf names to reasons for unavailability
        """
        if not self.topology_data:
            return {}
        
        unavailable_reasons = self.topology_data.get('unavailable_reasons', {})
        
        # Also check for leaves that might not be in the topology but are in device status
        # This handles cases where leaves exist in device status but not in topology
        device_status_file = Path("topology/device_status.json")
        if device_status_file.exists():
            try:
                with open(device_status_file, 'r') as f:
                    device_status = json.load(f)
                
                # Find leaves that are in device status but not in topology
                topology_devices = set(self.topology_data.get('devices', {}).keys())
                status_devices = set(device_status.get('devices', {}).keys())
                
                # Find leaf devices in status that are not in topology
                missing_leaves = []
                for device_name, device_info in device_status.get('devices', {}).items():
                    if 'LEAF' in device_name.upper() and device_name not in topology_devices:
                        # Try to find a matching device with different naming
                        device_variations = [
                            device_name,
                            device_name.replace('_', '-'),
                            device_name.replace('-', '_'),
                            device_name.upper(),
                            device_name.lower(),
                        ]
                        
                        found_in_topology = False
                        for variant in device_variations:
                            if variant in topology_devices:
                                found_in_topology = True
                                break
                        
                        if not found_in_topology:
                            missing_leaves.append(device_name)
                
                # Add missing leaves to unavailable reasons
                for leaf in missing_leaves:
                    if leaf not in unavailable_reasons:
                        unavailable_reasons[leaf] = {
                            'reason': 'not_in_topology',
                            'description': 'Device not found in topology data'
                        }
                        
            except Exception as e:
                self.logger.warning(f"Error reading device status file: {e}")
        
        return unavailable_reasons
    
    def build_bridge_domain_config(self, service_name: str, vlan_id: int, 
                                 source_leaf: str, source_port: str,
                                 dest_leaf: str, dest_port: str) -> Dict:
        """
        Build bridge domain configuration for all devices in the path (2-tier or 3-tier)
        
        Args:
            service_name: Service identifier (e.g., 'g_visaev_v253')
            vlan_id: VLAN ID
            source_leaf: Source leaf device name
            source_port: Source port interface
            dest_leaf: Destination leaf device name
            dest_port: Destination port interface
            
        Returns:
            Configuration for all devices in the path
        """
        self.logger.info(f"Building bridge domain config for {service_name} (VLAN {vlan_id})")
        self.logger.info(f"Path: {source_leaf}:{source_port} -> {dest_leaf}:{dest_port}")
        
        # Calculate path through architecture
        path = self.calculate_path(source_leaf, dest_leaf)
        if not path:
            return {}
        
        # Determine if this is a 2-tier or 3-tier path
        is_2_tier = path.get('superspine') is None
        
        if is_2_tier:
            self.logger.info(f"2-tier path: {source_leaf} → {path['source_spine']} → {dest_leaf}")
        else:
            self.logger.info(f"3-tier path: {source_leaf} → {path['source_spine']} → {path['superspine']} → {path['dest_spine']} → {dest_leaf}")
        
        # Build configurations for each device in the path
        configs = {}
        
        # Source Leaf Configuration
        source_leaf_segment = next(seg for seg in path['segments'] if seg['type'] == 'leaf_to_spine')
        source_leaf_config = self._build_leaf_config(
            service_name, vlan_id, source_leaf,
            source_port, source_leaf_segment['source_interface'],
            is_source=True
        )
        configs[source_leaf] = source_leaf_config
        
        # Spine Configuration
        if is_2_tier:
            # 2-tier: Single spine configuration
            dest_leaf_segment = next(seg for seg in path['segments'] if seg['type'] == 'spine_to_leaf')
            spine_config = self._build_spine_config(
                service_name, vlan_id, path['source_spine'],
                source_leaf_segment['dest_interface'], dest_leaf_segment['source_interface']
            )
            configs[path['source_spine']] = spine_config
        else:
            # 3-tier: Source spine configuration
            source_spine_segment = next(seg for seg in path['segments'] if seg['type'] == 'spine_to_superspine')
            source_spine_config = self._build_spine_config(
                service_name, vlan_id, path['source_spine'],
                source_leaf_segment['dest_interface'], source_spine_segment['source_interface']
            )
            configs[path['source_spine']] = source_spine_config
            
            # Super Spine Configuration
            superspine_segment_in = next(seg for seg in path['segments'] if seg['type'] == 'spine_to_superspine')
            superspine_segment_out = next(seg for seg in path['segments'] if seg['type'] == 'superspine_to_spine')
            superspine_config = self._build_superspine_config(
                service_name, vlan_id, path['superspine'],
                superspine_segment_in['dest_interface'], superspine_segment_out['source_interface']
            )
            configs[path['superspine']] = superspine_config
            
            # Destination Spine Configuration
            dest_spine_segment = next(seg for seg in path['segments'] if seg['type'] == 'spine_to_leaf')
            dest_spine_config = self._build_spine_config(
                service_name, vlan_id, path['dest_spine'],
                superspine_segment_out['dest_interface'], dest_spine_segment['source_interface']
            )
            configs[path['dest_spine']] = dest_spine_config
        
        # Destination Leaf Configuration
        dest_leaf_segment = next(seg for seg in path['segments'] if seg['type'] == 'spine_to_leaf')
        dest_leaf_config = self._build_leaf_config(
            service_name, vlan_id, dest_leaf,
            dest_port, dest_leaf_segment['dest_interface'],
            is_source=False
        )
        configs[dest_leaf] = dest_leaf_config
        
        self.logger.info(f"Generated configurations for {len(configs)} devices")
        return configs
    
    def _build_leaf_config(self, service_name: str, vlan_id: int, 
                          device: str, user_port: str, spine_interface: str,
                          is_source: bool) -> List[str]:
        """
        Build configuration for a leaf device
        
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
        
        # Get bundle for spine interface
        spine_bundle = self.get_bundle_for_interface(device, spine_interface)
        if not spine_bundle:
            self.logger.warning(f"No bundle found for {device}:{spine_interface}")
            return []
        
        # Bridge domain instance
        config.append(f"network-services bridge-domain instance {service_name} interface {spine_bundle}.{vlan_id}")
        config.append(f"interfaces {spine_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {spine_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        # User port
        config.append(f"network-services bridge-domain instance {service_name} interface {user_port}.{vlan_id}")
        config.append(f"interfaces {user_port}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {user_port}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def _build_spine_config(self, service_name: str, vlan_id: int,
                           device: str, source_interface: str, dest_interface: str) -> List[str]:
        """
        Build configuration for a spine device
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            device: Device name
            source_interface: Interface to source leaf
            dest_interface: Interface to destination leaf
            
        Returns:
            List of configuration commands
        """
        config = []
        
        # Get bundles for both interfaces
        source_bundle = self.get_bundle_for_interface(device, source_interface)
        dest_bundle = self.get_bundle_for_interface(device, dest_interface)
        
        if not source_bundle or not dest_bundle:
            self.logger.warning(f"Missing bundle mappings for {device}: {source_interface} or {dest_interface}")
            return []
        
        # Bridge domain instance with both interfaces
        config.append(f"network-services bridge-domain instance {service_name} interface {source_bundle}.{vlan_id}")
        config.append(f"interfaces {source_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {source_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        config.append(f"network-services bridge-domain instance {service_name} interface {dest_bundle}.{vlan_id}")
        config.append(f"interfaces {dest_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {dest_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def _build_superspine_config(self, service_name: str, vlan_id: int,
                                device: str, in_interface: str, out_interface: str) -> List[str]:
        """
        Build configuration for a super spine device
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            device: Device name
            in_interface: Interface to incoming spine
            out_interface: Interface to outgoing spine
            
        Returns:
            List of configuration commands
        """
        config = []
        
        # Get bundles for both interfaces
        in_bundle = self.get_bundle_for_interface(device, in_interface)
        out_bundle = self.get_bundle_for_interface(device, out_interface)
        
        if not in_bundle or not out_bundle:
            self.logger.warning(f"Missing bundle mappings for {device}: {in_interface} or {out_interface}")
            return []
        
        # Bridge domain instance with both interfaces
        config.append(f"network-services bridge-domain instance {service_name} interface {in_bundle}.{vlan_id}")
        config.append(f"interfaces {in_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {in_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        config.append(f"network-services bridge-domain instance {service_name} interface {out_bundle}.{vlan_id}")
        config.append(f"interfaces {out_bundle}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {out_bundle}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def save_configuration(self, configs: Dict, output_file: str = "bridge_domain_config.yaml"):
        """
        Save configuration to YAML file in configs/pending/ directory
        
        Args:
            configs: Device configurations
            output_file: Output file path (will be saved in configs/pending/)
        """
        try:
            # Create configs/pending directory if it doesn't exist
            pending_dir = Path("configs/pending")
            pending_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file in the configs/pending directory
            output_path = pending_dir / output_file
            with open(output_path, 'w') as f:
                yaml.dump(configs, f, default_flow_style=False, indent=2)
            self.logger.info(f"Configuration saved to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build bridge domain configurations')
    parser.add_argument('--service-name', required=True, help='Service identifier')
    parser.add_argument('--vlan-id', type=int, required=True, help='VLAN ID')
    parser.add_argument('--source-leaf', required=True, help='Source leaf device')
    parser.add_argument('--source-port', required=True, help='Source port interface')
    parser.add_argument('--dest-leaf', required=True, help='Destination leaf device')
    parser.add_argument('--dest-port', required=True, help='Destination port interface')
    parser.add_argument('--output', default='bridge_domain_config.yaml', help='Output file')
    
    args = parser.parse_args()
    
    # Build configuration
    builder = BridgeDomainBuilder()
    configs = builder.build_bridge_domain_config(
        args.service_name, args.vlan_id,
        args.source_leaf, args.source_port,
        args.dest_leaf, args.dest_port
    )
    
    if configs:
        builder.save_configuration(configs, args.output)
        print(f"✅ Bridge domain configuration built successfully")
        print(f"📁 Configuration saved to: {args.output}")
        
        # Show configuration summary
        print(f"\n📋 Configuration Summary:")
        for device, config in configs.items():
            print(f"  {device}: {len(config)} commands")
    else:
        print("❌ Failed to build bridge domain configuration")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 