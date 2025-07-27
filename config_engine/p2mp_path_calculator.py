#!/usr/bin/env python3
"""
P2MP Path Calculator
Calculates optimal paths for Point-to-Multipoint bridge domain configurations
"""

import logging
from typing import Dict, List, Optional, Tuple
from .device_name_normalizer import normalizer


class P2MPPathCalculator:
    """Calculate optimal paths for P2MP bridge domain topology"""
    
    def __init__(self, topology_data: Dict):
        """
        Initialize P2MP path calculator
        
        Args:
            topology_data: Topology data from bridge domain builder
        """
        self.topology_data = topology_data
        self.device_connections = self._build_connection_map()
        self.logger = logging.getLogger('P2MPPathCalculator')
        
        # Initialize device name normalizer
        self.normalizer = normalizer
    
    def _build_connection_map(self) -> Dict:
        """Build device connection map from topology data"""
        devices = self.topology_data.get('devices', {})
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
                        # Add reverse connection for spine
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
        
        return device_connections
    
    def analyze_source_capabilities(self, source_leaf: str) -> Dict:
        """
        Analyze source leaf connectivity
        
        Returns:
            {
                'connected_spines': [spine1, spine2, ...],
                'available_paths': [path1, path2, ...],
                'path_types': {'2-tier': [path1, path2], '3-tier': [path3, path4]}
            }
        """
        normalized_source = self.normalizer.normalize_device_name(source_leaf)
        
        # Get connected spines
        connected_spines = []
        available_paths = []
        path_types = {'2-tier': [], '3-tier': []}
        
        if normalized_source in self.device_connections:
            for conn in self.device_connections[normalized_source]:
                spine = conn['device']
                connected_spines.append(spine)
                
                # Determine if this is a 2-tier or 3-tier path
                # For now, assume 2-tier if spine is directly connected
                path_info = {
                    'spine': spine,
                    'type': '2-tier',
                    'source_interface': conn['local_interface'],
                    'spine_interface': conn['remote_interface']
                }
                available_paths.append(path_info)
                path_types['2-tier'].append(path_info)
        
        return {
            'connected_spines': connected_spines,
            'available_paths': available_paths,
            'path_types': path_types
        }
    
    def calculate_single_path(self, source_leaf: str, dest_leaf: str) -> Optional[Dict]:
        """
        Calculate single path from source to destination
        Returns:
            Path information or None if no path found
        """
        normalized_source = self.normalizer.normalize_device_name(source_leaf)
        normalized_dest = self.normalizer.normalize_device_name(dest_leaf)
        
        # Find shared spine (2-tier path)
        source_spines = set()
        dest_spines = set()
        
        if normalized_source in self.device_connections:
            source_spines = {conn['device'] for conn in self.device_connections[normalized_source]}
        if normalized_dest in self.device_connections:
            dest_spines = {conn['device'] for conn in self.device_connections[normalized_dest]}
        shared_spines = source_spines & dest_spines
        if shared_spines:
            shared_spine = list(shared_spines)[0]
            # Get connection details (real interfaces)
            source_conn = next(conn for conn in self.device_connections[normalized_source] if conn['device'] == shared_spine)
            dest_conn = next(conn for conn in self.device_connections[normalized_dest] if conn['device'] == shared_spine)
            return {
                'source_leaf': normalized_source,
                'destination_leaf': normalized_dest,
                'spine': shared_spine,
                'path_type': '2-tier',
                'segments': [
                    {
                        'type': 'leaf_to_spine',
                        'source_device': normalized_source,
                        'dest_device': shared_spine,
                        'source_interface': source_conn['local_interface'],
                        'dest_interface': source_conn['remote_interface']
                    },
                    {
                        'type': 'spine_to_leaf',
                        'source_device': shared_spine,
                        'dest_device': normalized_dest,
                        'source_interface': dest_conn['remote_interface'],
                        'dest_interface': dest_conn['local_interface']
                    }
                ]
            }
        self.logger.warning(f"No 2-tier path found between {source_leaf} and {dest_leaf}")
        return None

    def calculate_p2mp_paths(self, source_leaf: str, destinations: List[str]) -> Dict:
        """
        Calculate optimal paths for P2MP topology
        Automatically determines path type:
        - 2-tier for destinations on same spine as source
        - 3-tier for destinations on different spines
        
        Returns:
            {
                'source_leaf': source_leaf,
                'destinations': {
                    'dest_leaf1': { 'path': path_object, ... }, ...
                },
                'spine_interfaces': {
                    'spine1': set((device, interface)), ...
                },
                ...
            }
        """
        self.logger.info(f"Calculating P2MP paths for {source_leaf} to {len(destinations)} destinations")
        individual_paths = {}
        failed_destinations = []
        spine_interfaces = {}  # spine: set((device, interface))
        
        # Get source leaf's connected spines
        normalized_source = self.normalizer.normalize_device_name(source_leaf)
        source_spines = set()
        if normalized_source in self.device_connections:
            source_spines = {conn['device'] for conn in self.device_connections[normalized_source]}
        
        for dest in destinations:
            path = self._calculate_optimal_path_for_destination(source_leaf, dest, source_spines)
            if path:
                individual_paths[dest] = path
                # For each segment, record spine interfaces
                for seg in path['segments']:
                    if seg['type'] == 'leaf_to_spine':
                        spine = seg['dest_device']
                        if spine not in spine_interfaces:
                            spine_interfaces[spine] = set()
                        spine_interfaces[spine].add((seg['source_device'], seg['source_interface']))
                        spine_interfaces[spine].add((seg['dest_device'], seg['dest_interface']))
                    elif seg['type'] == 'spine_to_leaf':
                        spine = seg['source_device']
                        if spine not in spine_interfaces:
                            spine_interfaces[spine] = set()
                        spine_interfaces[spine].add((seg['source_device'], seg['source_interface']))
                        spine_interfaces[spine].add((seg['dest_device'], seg['dest_interface']))
                    elif seg['type'] == 'spine_to_superspine':
                        spine = seg['source_device']
                        superspine = seg['dest_device']
                        if spine not in spine_interfaces:
                            spine_interfaces[spine] = set()
                        if superspine not in spine_interfaces:
                            spine_interfaces[superspine] = set()
                        spine_interfaces[spine].add((seg['source_device'], seg['source_interface']))
                        spine_interfaces[spine].add((seg['dest_device'], seg['dest_interface']))
                        spine_interfaces[superspine].add((seg['source_device'], seg['source_interface']))
                        spine_interfaces[superspine].add((seg['dest_device'], seg['dest_interface']))
                    elif seg['type'] == 'superspine_to_spine':
                        superspine = seg['source_device']
                        spine = seg['dest_device']
                        if superspine not in spine_interfaces:
                            spine_interfaces[superspine] = set()
                        if spine not in spine_interfaces:
                            spine_interfaces[spine] = set()
                        spine_interfaces[superspine].add((seg['source_device'], seg['source_interface']))
                        spine_interfaces[superspine].add((seg['dest_device'], seg['dest_interface']))
                        spine_interfaces[spine].add((seg['source_device'], seg['source_interface']))
                        spine_interfaces[spine].add((seg['dest_device'], seg['dest_interface']))
            else:
                failed_destinations.append(dest)
        
        if failed_destinations:
            self.logger.warning(f"Failed to calculate paths for: {failed_destinations}")
        
        # Calculate spine utilization
        spine_utilization = {spine: {'destinations': 0} for spine in spine_interfaces}
        for dest, path_info in individual_paths.items():
            spine = path_info.get('spine') or path_info.get('source_spine')
            if spine in spine_utilization:
                spine_utilization[spine]['destinations'] += 1
        
        total_spines_used = len(spine_utilization)
        path_efficiency = len(individual_paths) / len(destinations) if destinations else 0
        
        return {
            'source_leaf': source_leaf,
            'destinations': individual_paths,
            'spine_interfaces': {k: list(v) for k, v in spine_interfaces.items()},
            'spine_utilization': spine_utilization,
            'optimization_metrics': {
                'total_spines_used': total_spines_used,
                'path_efficiency': path_efficiency,
                'failed_destinations': failed_destinations
            }
        }

    def _calculate_optimal_path_for_destination(self, source_leaf: str, dest_leaf: str, source_spines: set) -> Optional[Dict]:
        """
        Calculate optimal path for a single destination
        Automatically chooses 2-tier or 3-tier based on spine connectivity
        """
        normalized_source = self.normalizer.normalize_device_name(source_leaf)
        normalized_dest = self.normalizer.normalize_device_name(dest_leaf)
        
        # Get destination's connected spines
        dest_spines = set()
        if normalized_dest in self.device_connections:
            dest_spines = {conn['device'] for conn in self.device_connections[normalized_dest]}
        
        # Check for shared spine (2-tier path)
        shared_spines = source_spines & dest_spines
        if shared_spines:
            # Use 2-tier path
            shared_spine = list(shared_spines)[0]
            source_conn = next(conn for conn in self.device_connections[normalized_source] if conn['device'] == shared_spine)
            dest_conn = next(conn for conn in self.device_connections[normalized_dest] if conn['device'] == shared_spine)
            
            self.logger.info(f"Using 2-tier path for {dest_leaf} via {shared_spine}")
            
            return {
                'source_leaf': normalized_source,
                'destination_leaf': normalized_dest,
                'spine': shared_spine,
                'path_type': '2-tier',
                'segments': [
                    {
                        'type': 'leaf_to_spine',
                        'source_device': normalized_source,
                        'dest_device': shared_spine,
                        'source_interface': source_conn['local_interface'],
                        'dest_interface': source_conn['remote_interface']
                    },
                    {
                        'type': 'spine_to_leaf',
                        'source_device': shared_spine,
                        'dest_device': normalized_dest,
                        'source_interface': dest_conn['remote_interface'],
                        'dest_interface': dest_conn['local_interface']
                    }
                ]
            }
        
        # No shared spine, try 3-tier path
        self.logger.info(f"No shared spine for {dest_leaf}, attempting 3-tier path")
        return self._calculate_3tier_path(normalized_source, normalized_dest)

    def _calculate_3tier_path(self, source_leaf: str, dest_leaf: str) -> Optional[Dict]:
        """
        Calculate 3-tier path via superspine
        """
        # Find spines connected to source and destination
        source_spine = None
        source_conn = None
        for conn in self.device_connections.get(source_leaf, []):
            if conn['device'].startswith('DNAAS-SPINE'):
                source_spine = conn['device']
                source_conn = conn
                break
        
        dest_spine = None
        dest_conn = None
        for conn in self.device_connections.get(dest_leaf, []):
            if conn['device'].startswith('DNAAS-SPINE'):
                dest_spine = conn['device']
                dest_conn = conn
                break
        
        if not source_spine or not dest_spine:
            self.logger.warning(f"Could not find spine connections for 3-tier path")
            return None
        
        # Find common superspine
        source_spine_superspines = set()
        dest_spine_superspines = set()
        
        # Get superspines connected to source spine
        if source_spine in self.device_connections:
            for conn in self.device_connections[source_spine]:
                if conn['device'].startswith('DNAAS-SUPERSPINE'):
                    source_spine_superspines.add(conn['device'])
        
        # Get superspines connected to dest spine
        if dest_spine in self.device_connections:
            for conn in self.device_connections[dest_spine]:
                if conn['device'].startswith('DNAAS-SUPERSPINE'):
                    dest_spine_superspines.add(conn['device'])
        
        # Find common superspine
        common_superspines = source_spine_superspines & dest_spine_superspines
        if not common_superspines:
            self.logger.warning(f"No common superspine found for 3-tier path")
            return None
        
        superspine = list(common_superspines)[0]
        
        # Get connection details
        source_spine_to_superspine = next(conn for conn in self.device_connections[source_spine] if conn['device'] == superspine)
        dest_spine_to_superspine = next(conn for conn in self.device_connections[dest_spine] if conn['device'] == superspine)
        
        self.logger.info(f"Using 3-tier path via {superspine}")
        
        return {
            'source_leaf': source_leaf,
            'destination_leaf': dest_leaf,
            'source_spine': source_spine,
            'superspine': superspine,
            'dest_spine': dest_spine,
            'path_type': '3-tier',
            'segments': [
                {
                    'type': 'leaf_to_spine',
                    'source_device': source_leaf,
                    'dest_device': source_spine,
                    'source_interface': source_conn['local_interface'],
                    'dest_interface': source_conn['remote_interface']
                },
                {
                    'type': 'spine_to_superspine',
                    'source_device': source_spine,
                    'dest_device': superspine,
                    'source_interface': source_spine_to_superspine['local_interface'],
                    'dest_interface': source_spine_to_superspine['remote_interface']
                },
                {
                    'type': 'superspine_to_spine',
                    'source_device': superspine,
                    'dest_device': dest_spine,
                    'source_interface': dest_spine_to_superspine['remote_interface'],
                    'dest_interface': dest_spine_to_superspine['local_interface']
                },
                {
                    'type': 'spine_to_leaf',
                    'source_device': dest_spine,
                    'dest_device': dest_leaf,
                    'source_interface': dest_conn['remote_interface'],
                    'dest_interface': dest_conn['local_interface']
                }
            ]
        }
    
    def _optimize_shared_spine(self, source: str, individual_paths: Dict) -> Dict:
        """
        Optimize for minimum spine usage by grouping destinations
        
        Args:
            source: Source leaf device name
            individual_paths: Dictionary of individual path calculations
            
        Returns:
            Optimized paths with shared spine grouping
        """
        # Group destinations by spine
        spine_groups = {}
        for dest, path_info in individual_paths.items():
            spine = path_info['spine']
            if spine not in spine_groups:
                spine_groups[spine] = []
            spine_groups[spine].append(dest)
        
        self.logger.info(f"Shared spine optimization: {len(spine_groups)} spines for {len(individual_paths)} destinations")
        
        # Return optimized paths (same as individual paths for now)
        # Future enhancement: further optimize by finding better spine assignments
        return individual_paths
    
    def _optimize_hybrid(self, source: str, individual_paths: Dict) -> Dict:
        """
        Optimize using mix of 2-tier and 3-tier paths
        
        Args:
            source: Source leaf device name
            individual_paths: Dictionary of individual path calculations
            
        Returns:
            Optimized paths with hybrid strategy
        """
        # For now, return individual paths
        # Future enhancement: implement 3-tier path calculation and optimization
        self.logger.info(f"Hybrid optimization: using {len(individual_paths)} paths")
        return individual_paths
    
    def validate_path_feasibility(self, path: Dict) -> Tuple[bool, List[str]]:
        """
        Validate if a calculated path is feasible
        
        Args:
            path: Path information dictionary
            
        Returns:
            (is_feasible, error_messages)
        """
        errors = []
        
        # Check if all devices exist in topology
        devices = self.topology_data.get('devices', {})
        
        if path['source_leaf'] not in devices:
            errors.append(f"Source leaf {path['source_leaf']} not found in topology")
        
        if path['destination_leaf'] not in devices:
            errors.append(f"Destination leaf {path['destination_leaf']} not found in topology")
        
        if path['spine'] not in devices:
            errors.append(f"Spine {path['spine']} not found in topology")
        
        # Check connectivity
        if path['source_leaf'] not in self.device_connections:
            errors.append(f"Source leaf {path['source_leaf']} has no connections")
        
        if path['destination_leaf'] not in self.device_connections:
            errors.append(f"Destination leaf {path['destination_leaf']} has no connections")
        
        return len(errors) == 0, errors 