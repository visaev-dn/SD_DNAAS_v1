#!/usr/bin/env python3
"""
P2MP Configuration Generator
Generates bridge domain configurations for Point-to-Multipoint topology
"""

import logging
from typing import Dict, List
from .bridge_domain_builder import BridgeDomainBuilder


class P2MPConfigGenerator:
    """Generate P2MP bridge domain configurations"""
    
    def __init__(self, builder: BridgeDomainBuilder):
        """
        Initialize P2MP configuration generator
        
        Args:
            builder: Bridge domain builder instance
        """
        self.builder = builder
        self.logger = logging.getLogger('P2MPConfigGenerator')
    
    def generate_p2mp_config(self, service_name: str, vlan_id: int,
                           source_leaf: str, source_port: str,
                           destinations: List[Dict],
                           path_calculation: Dict) -> Dict:
        """
        Generate P2MP bridge domain configuration
        """
        self.logger.info(f"Generating P2MP config for {service_name} (VLAN {vlan_id})")
        self.logger.info(f"Source: {source_leaf}, Destinations: {len(destinations)}")
        configs = {}
        
        # Source leaf config - need to include spine bundle interface
        source_config = self._generate_source_config(service_name, vlan_id, source_leaf, source_port)
        
        # Add spine bundle interface for source leaf (only once per unique bundle)
        added_bundles = set()  # Track bundles already added to avoid duplicates
        for dest_name, path_info in path_calculation['destinations'].items():
            for seg in path_info['segments']:
                if seg['type'] == 'leaf_to_spine' and seg['source_device'] == source_leaf:
                    spine_iface = seg['source_interface']
                    bundle = self.builder.get_bundle_for_interface(source_leaf, spine_iface)
                    if bundle and bundle not in added_bundles:
                        source_config.append(f"network-services bridge-domain instance {service_name} interface {bundle}.{vlan_id}")
                        source_config.append(f"interfaces {bundle}.{vlan_id} l2-service enabled")
                        source_config.append(f"interfaces {bundle}.{vlan_id} vlan-id {vlan_id}")
                        added_bundles.add(bundle)
        
        configs[source_leaf] = source_config
        
        # Destination configs
        for dest_info in destinations:
            dest_leaf = dest_info['leaf']
            dest_port = dest_info['port']
            if dest_leaf in path_calculation['destinations']:
                path_info = path_calculation['destinations'][dest_leaf]
                dest_config = self._generate_destination_config(service_name, vlan_id, dest_leaf, dest_port, path_info)
                configs[dest_leaf] = dest_config
            else:
                self.logger.warning(f"No path found for destination {dest_leaf}")
        
        # Spine configs: for each spine, configure all bundles/interfaces used in any segment
        for spine, dev_ifaces in path_calculation.get('spine_interfaces', {}).items():
            spine_config = []
            for dev, iface in dev_ifaces:
                if dev == spine:
                    bundle = self.builder.get_bundle_for_interface(spine, iface)
                    if bundle:
                        spine_config.append(f"network-services bridge-domain instance {service_name} interface {bundle}.{vlan_id}")
                        spine_config.append(f"interfaces {bundle}.{vlan_id} l2-service enabled")
                        spine_config.append(f"interfaces {bundle}.{vlan_id} vlan-id {vlan_id}")
            if spine_config:
                configs[spine] = sorted(set(spine_config), key=lambda x: (x.count('interface'), x))
        
        self.logger.info(f"Generated configurations for {len(configs)} devices")
        return configs

    def _generate_destination_config(self, service_name: str, vlan_id: int,
                                   dest_leaf: str, dest_port: str,
                                   path_info: Dict) -> List[str]:
        config = []
        # Find the real spine interface for this destination
        for seg in path_info['segments']:
            if seg['type'] == 'spine_to_leaf':
                spine_iface = seg['dest_interface']
                spine = seg['source_device']
                bundle = self.builder.get_bundle_for_interface(dest_leaf, spine_iface)
                if bundle:
                    config.append(f"network-services bridge-domain instance {service_name} interface {bundle}.{vlan_id}")
                    config.append(f"interfaces {bundle}.{vlan_id} l2-service enabled")
                    config.append(f"interfaces {bundle}.{vlan_id} vlan-id {vlan_id}")
        # User port
        config.append(f"network-services bridge-domain instance {service_name} interface {dest_port}.{vlan_id}")
        config.append(f"interfaces {dest_port}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {dest_port}.{vlan_id} vlan-id {vlan_id}")
        return config

    def _generate_source_config(self, service_name: str, vlan_id: int,
                              source_leaf: str, source_port: str) -> List[str]:
        config = []
        # For P2MP, we need to find the spine interface for the source leaf
        # We'll get this from the path calculation data
        # For now, we'll configure both user port and a placeholder spine bundle
        # The actual spine bundle will be configured when we have the path data
        
        # User port (always needed)
        config.append(f"network-services bridge-domain instance {service_name} interface {source_port}.{vlan_id}")
        config.append(f"interfaces {source_port}.{vlan_id} l2-service enabled")
        config.append(f"interfaces {source_port}.{vlan_id} vlan-id {vlan_id}")
        
        return config
    
    def generate_distributed_config(self, service_name: str, vlan_id: int,
                                 source_leaf: str, source_port: str,
                                 destination_paths: Dict) -> Dict:
        """
        Generate configuration for destinations on different spines
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_leaf: Source leaf device name
            source_port: Source port interface
            destination_paths: Dictionary of destination path information
            
        Returns:
            Configuration for all devices
        """
        # This is similar to generate_p2mp_config but without shared spine optimization
        # For now, use the same logic as generate_p2mp_config
        destinations = [{'leaf': dest, 'port': f'ge100-0/0/{i+20}'} 
                       for i, dest in enumerate(destination_paths.keys())]
        
        return self.generate_p2mp_config(service_name, vlan_id, source_leaf, source_port, destinations, destination_paths)
    
    def generate_hybrid_config(self, service_name: str, vlan_id: int,
                             source_leaf: str, source_port: str,
                             path_groups: Dict) -> Dict:
        """
        Generate configuration for mixed 2-tier and 3-tier paths
        
        Args:
            service_name: Service identifier
            vlan_id: VLAN ID
            source_leaf: Source leaf device name
            source_port: Source port interface
            path_groups: Dictionary with path group information
            
        Returns:
            Configuration for all devices
        """
        # For now, use the same logic as generate_p2mp_config
        # Future enhancement: handle 3-tier paths differently
        destinations = []
        for group_name, group_info in path_groups.items():
            for dest in group_info.get('destinations', []):
                destinations.append({'leaf': dest, 'port': f'ge100-0/0/{len(destinations)+20}'})
        
        # Create a simplified path calculation structure
        path_calculation = {
            'destinations': {},
            'spine_utilization': {},
            'optimization_metrics': {}
        }
        
        for dest_info in destinations:
            dest_name = dest_info['leaf']
            # Create a simple path info structure
            path_calculation['destinations'][dest_name] = {
                'spine': f'DNAAS-SPINE-{len(path_calculation["destinations"])+1}',
                'path_type': '2-tier'
            }
        
        return self.generate_p2mp_config(service_name, vlan_id, source_leaf, source_port, destinations, path_calculation) 