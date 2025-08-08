#!/usr/bin/env python3
"""
Topology Mapper

This module maps discovered topology data into the format expected by
the existing bridge domain builders, enabling seamless integration.
"""

import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

class TopologyMapper:
    """
    Topology Mapper
    
    Maps discovered topology data into builder-compatible format.
    """
    
    def __init__(self):
        self.device_mappings = {}
        self.interface_mappings = {}
        self.vlan_mappings = {}
    
    def map_to_builder_format(self, topology_data: Dict, path_data: Dict, 
                             bridge_domain_name: str) -> Optional[Dict]:
        """
        Map discovered topology to builder configuration format.
        
        Args:
            topology_data: Topology data from scanner
            path_data: Path data from scanner
            bridge_domain_name: Name of the bridge domain
            
        Returns:
            Builder-compatible configuration dictionary
        """
        try:
            logger.info("=== MAPPING TOPOLOGY TO BUILDER FORMAT ===")
            logger.info(f"Bridge domain: {bridge_domain_name}")
            logger.info(f"Topology data keys: {list(topology_data.keys())}")
            logger.info(f"Path data keys: {list(path_data.keys())}")
            
            # Store path_data as instance variable for use in mapping methods
            self.path_data = path_data
            
            # Extract nodes and edges from topology
            nodes = topology_data.get('nodes', [])
            edges = topology_data.get('edges', [])
            device_mappings = topology_data.get('device_mappings', {})
            
            logger.info(f"Found {len(nodes)} nodes and {len(edges)} edges")
            
            # Step 1: Map devices
            devices = self._map_devices(nodes, device_mappings)
            logger.info(f"Mapped {len(devices)} devices")
            
            # Step 2: Map interfaces
            interfaces = self._map_interfaces(nodes, edges)
            logger.info(f"Mapped {len(interfaces)} interfaces")
            
            # Step 3: Map VLANs
            vlans = self._map_vlans(nodes, path_data)
            logger.info(f"Mapped {len(vlans)} VLANs")
            
            # Step 4: Determine topology type
            topology_type = self._determine_topology_type(nodes, edges, path_data)
            logger.info(f"Determined topology type: {topology_type}")
            
            # Step 5: Create builder configuration
            builder_config = {
                'bridge_domain_name': bridge_domain_name,
                'topology_type': topology_type,
                'devices': devices,
                'interfaces': interfaces,
                'vlans': vlans,
                'paths': path_data,
                'metadata': {
                    'original_topology_data': topology_data,
                    'mapped_at': self._get_timestamp(),
                    'source': 'reverse_engineered'
                }
            }
            
            logger.info(f"Created builder config with keys: {list(builder_config.keys())}")
            return builder_config
            
        except Exception as e:
            logger.error(f"Failed to map topology to builder format: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _map_devices(self, nodes: List[Dict], device_mappings: Dict) -> Dict[str, Dict]:
        """Map device nodes to builder device format."""
        devices = {}
        
        # Extract devices from nodes
        for node in nodes:
            if node.get('type') == 'device':
                device_data = node.get('data', {})
                device_name = device_data.get('name', 'unknown')
                
                # Map to builder device format
                devices[device_name] = {
                    'name': device_name,
                    'device_type': device_data.get('device_type', 'unknown'),
                    'status': device_data.get('status', 'active'),
                    'interfaces_count': device_data.get('interfaces_count', 0),
                    'vlans_count': device_data.get('vlans_count', 0),
                    'bridge_domains_count': device_data.get('bridge_domains_count', 0)
                }
        
        # Also extract devices from path data if we have insufficient devices
        if len(devices) < 2:
            logger.info(f"Only {len(devices)} devices found in nodes, extracting from path data")
            
            # Extract from device paths
            device_paths = self.path_data.get('device_paths', {})
            for path_key, path in device_paths.items():
                for device_name in path:
                    if device_name not in devices:
                        devices[device_name] = {
                            'name': device_name,
                            'device_type': 'unknown',
                            'status': 'active',
                            'interfaces_count': 0,
                            'vlans_count': 0,
                            'bridge_domains_count': 0
                        }
            
            # Extract from VLAN paths
            vlan_paths = self.path_data.get('vlan_paths', {})
            for path_key, path in vlan_paths.items():
                for item in path:
                    if not item.startswith('vlan_') and not item.startswith('bundle-') and not item.startswith('ge'):
                        # This looks like a device name
                        if item not in devices:
                            devices[item] = {
                                'name': item,
                                'device_type': 'unknown',
                                'status': 'active',
                                'interfaces_count': 0,
                                'vlans_count': 0,
                                'bridge_domains_count': 0
                            }
        
        logger.info(f"Mapped devices: {list(devices.keys())}")
        return devices
    
    def _map_interfaces(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Dict]:
        """Map interface nodes to builder interface format."""
        interfaces = {}
        
        # Extract interfaces from nodes
        for node in nodes:
            if node.get('type') == 'interface':
                interface_data = node.get('data', {})
                interface_name = interface_data.get('name', 'unknown')
                device_name = interface_data.get('device_name', 'unknown')
                
                # Create unique interface key
                interface_key = f"{device_name}_{interface_name}"
                
                # Map to builder interface format
                interfaces[interface_key] = {
                    'name': interface_name,
                    'device_name': device_name,
                    'interface_type': interface_data.get('interface_type', 'unknown'),
                    'vlan_id': interface_data.get('vlan_id', 0),
                    'status': interface_data.get('status', 'unknown'),
                    'is_subinterface': interface_data.get('is_subinterface', False)
                }
        
        # Also extract interfaces from path data if we have insufficient interfaces
        if len(interfaces) < 2:
            logger.info(f"Only {len(interfaces)} interfaces found in nodes, extracting from path data")
            
            # Extract from VLAN paths
            vlan_paths = self.path_data.get('vlan_paths', {})
            for path_key, path in vlan_paths.items():
                logger.info(f"Processing VLAN path: {path_key}")
                logger.info(f"Path items: {path}")
                
                # Find all interfaces in the path
                interface_positions = []
                for i, item in enumerate(path):
                    if item.startswith('bundle-') or item.startswith('ge'):
                        interface_positions.append(i)
                
                logger.info(f"Found interface positions: {interface_positions}")
                
                # Extract interfaces with their device names
                for pos in interface_positions:
                    interface_name = path[pos]
                    
                    # Find the device name (look backwards from interface position)
                    device_name = None
                    for i in range(pos - 1, -1, -1):
                        item = path[i]
                        if not item.startswith('vlan_') and not item.startswith('bundle-') and not item.startswith('ge'):
                            device_name = item
                            break
                    
                    # If we didn't find a device name looking backwards, look forwards
                    if not device_name:
                        for i in range(pos + 1, len(path)):
                            item = path[i]
                            if not item.startswith('vlan_') and not item.startswith('bundle-') and not item.startswith('ge'):
                                device_name = item
                                break
                    
                    logger.info(f"Found interface: {interface_name} for device: {device_name}")
                    
                    if device_name:
                        interface_key = f"{device_name}_{interface_name}"
                        if interface_key not in interfaces:
                            # Extract VLAN ID from path key
                            vlan_id = 0
                            if '_' in path_key:
                                parts = path_key.split('_')
                                if len(parts) >= 2 and parts[0] == 'vlan':
                                    try:
                                        vlan_id = int(parts[1])
                                    except ValueError:
                                        pass
                            
                            interfaces[interface_key] = {
                                'name': interface_name,
                                'device_name': device_name,
                                'interface_type': 'bundle' if interface_name.startswith('bundle-') else 'gigabit',
                                'vlan_id': vlan_id,
                                'status': 'active',
                                'is_subinterface': '.' in interface_name
                            }
                            logger.info(f"Added interface: {interface_key}")
                        else:
                            logger.info(f"Interface already exists: {interface_key}")
                            # Try to find a different device for this interface
                            # Look for other devices in the path that don't have this interface yet
                            device_paths = self.path_data.get('device_paths', {})
                            for path_key, device_path in device_paths.items():
                                for other_device in device_path:
                                    if other_device != device_name:
                                        alt_interface_key = f"{other_device}_{interface_name}"
                                        if alt_interface_key not in interfaces:
                                            # Extract VLAN ID from path key
                                            vlan_id = 0
                                            if '_' in path_key:
                                                parts = path_key.split('_')
                                                if len(parts) >= 2 and parts[0] == 'vlan':
                                                    try:
                                                        vlan_id = int(parts[1])
                                                    except ValueError:
                                                        pass
                                            
                                            interfaces[alt_interface_key] = {
                                                'name': interface_name,
                                                'device_name': other_device,
                                                'interface_type': 'bundle' if interface_name.startswith('bundle-') else 'gigabit',
                                                'vlan_id': vlan_id,
                                                'status': 'active',
                                                'is_subinterface': '.' in interface_name
                                            }
                                            logger.info(f"Added alternative interface: {alt_interface_key}")
                                            break
                                break
                    else:
                        logger.warning(f"Could not find device name for interface: {interface_name}")
        
        logger.info(f"Mapped {len(interfaces)} interfaces")
        return interfaces
    
    def _map_vlans(self, nodes: List[Dict], path_data: Dict) -> Dict[str, Dict]:
        """Map VLAN nodes to builder VLAN format."""
        vlans = {}
        
        # Extract VLANs from nodes
        for node in nodes:
            if node.get('type') == 'vlan':
                vlan_data = node.get('data', {})
                vlan_id = vlan_data.get('vlan_id', 0)
                
                if vlan_id > 0:
                    vlans[f"vlan_{vlan_id}"] = {
                        'vlan_id': vlan_id,
                        'name': f'VLAN{vlan_id}',
                        'status': vlan_data.get('status', 'active'),
                        'interfaces': vlan_data.get('interfaces', [])
                    }
        
        # Also extract VLANs from path data
        vlan_paths = path_data.get('vlan_paths', {})
        for path_key, path in vlan_paths.items():
            # Extract VLAN ID from path key (format: vlan_251_...)
            if '_' in path_key:
                parts = path_key.split('_')
                if len(parts) >= 2 and parts[0] == 'vlan':
                    try:
                        vlan_id = int(parts[1])
                        if vlan_id not in [v['vlan_id'] for v in vlans.values()]:
                            vlans[f"vlan_{vlan_id}"] = {
                                'vlan_id': vlan_id,
                                'name': f'VLAN{vlan_id}',
                                'status': 'active',
                                'interfaces': []
                            }
                    except ValueError:
                        continue
        
        logger.info(f"Mapped {len(vlans)} VLANs")
        return vlans
    
    def _determine_topology_type(self, nodes: List[Dict], edges: List[Dict], 
                                path_data: Dict) -> str:
        """Determine topology type (P2P, P2MP, mixed, etc.)."""
        try:
            # Count device nodes
            device_nodes = [n for n in nodes if n.get('type') == 'device']
            device_count = len(device_nodes)
            
            # Count VLAN paths
            vlan_paths = path_data.get('vlan_paths', {})
            vlan_path_count = len(vlan_paths)
            
            # Count device paths
            device_paths = path_data.get('device_paths', {})
            device_path_count = len(device_paths)
            
            logger.info(f"Topology analysis: {device_count} devices, {vlan_path_count} VLAN paths, {device_path_count} device paths")
            
            # Simple heuristics for topology type
            if device_count == 2:
                return 'p2p'  # Point-to-point
            elif device_count > 2 and vlan_path_count > device_path_count:
                return 'p2mp'  # Point-to-multipoint
            elif device_count > 2:
                return 'mixed'  # Mixed topology
            else:
                return 'unknown'
                
        except Exception as e:
            logger.error(f"Failed to determine topology type: {e}")
            return 'unknown'
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_device_interfaces(self, device_name: str, interfaces: Dict[str, Dict]) -> List[Dict]:
        """Get all interfaces for a specific device."""
        device_interfaces = []
        
        for interface_key, interface_data in interfaces.items():
            if interface_data.get('device_name') == device_name:
                device_interfaces.append(interface_data)
        
        return device_interfaces
    
    def get_vlan_interfaces(self, vlan_id: int, interfaces: Dict[str, Dict]) -> List[Dict]:
        """Get all interfaces for a specific VLAN."""
        vlan_interfaces = []
        
        for interface_key, interface_data in interfaces.items():
            if interface_data.get('vlan_id') == vlan_id:
                vlan_interfaces.append(interface_data)
        
        return vlan_interfaces
    
    def validate_mapping(self, builder_config: Dict) -> bool:
        """Validate that the mapping is complete and correct."""
        try:
            required_keys = ['bridge_domain_name', 'topology_type', 'devices', 'interfaces', 'vlans']
            
            for key in required_keys:
                if key not in builder_config:
                    logger.error(f"Missing required key: {key}")
                    return False
            
            # Check that we have at least one device
            if not builder_config['devices']:
                logger.error("No devices mapped")
                return False
            
            # Check that we have at least one interface
            if not builder_config['interfaces']:
                logger.error("No interfaces mapped")
                return False
            
            logger.info("Mapping validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Mapping validation failed: {e}")
            return False

# Example usage
def main():
    """Example usage of the topology mapper."""
    mapper = TopologyMapper()
    
    # Example topology data
    topology_data = {
        'nodes': [
            {
                'type': 'device',
                'data': {
                    'name': 'DNAAS-LEAF-B10',
                    'device_type': 'leaf',
                    'status': 'active',
                    'interfaces_count': 2,
                    'vlans_count': 1,
                    'bridge_domains_count': 1
                }
            },
            {
                'type': 'interface',
                'data': {
                    'name': 'bundle-60000.251',
                    'device_name': 'DNAAS-LEAF-B10',
                    'interface_type': 'bundle',
                    'vlan_id': 251,
                    'status': 'active',
                    'is_subinterface': True
                }
            }
        ],
        'edges': [],
        'device_mappings': {'DNAAS-LEAF-B10': 'device_DNAAS-LEAF-B10'}
    }
    
    path_data = {
        'device_paths': {
            'DNAAS-LEAF-B10_to_DNAAS-LEAF-B14': ['DNAAS-LEAF-B10', 'DNAAS-LEAF-B14']
        },
        'vlan_paths': {
            'vlan_251_DNAAS-LEAF-B10_bundle-60000.251_to_DNAAS-LEAF-B14_bundle-60000.251': [
                'DNAAS-LEAF-B10', 'bundle-60000.251', 'vlan_251', 'bundle-60000.251', 'DNAAS-LEAF-B14'
            ]
        }
    }
    
    # Map topology to builder format
    builder_config = mapper.map_to_builder_format(topology_data, path_data, 'test_bridge_domain')
    
    if builder_config:
        print("Successfully mapped topology to builder format")
        print(f"Topology type: {builder_config['topology_type']}")
        print(f"Devices: {list(builder_config['devices'].keys())}")
        print(f"Interfaces: {len(builder_config['interfaces'])}")
        print(f"VLANs: {len(builder_config['vlans'])}")
    else:
        print("Failed to map topology")

if __name__ == "__main__":
    main() 