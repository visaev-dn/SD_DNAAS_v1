#!/usr/bin/env python3
"""
Topology Models
Data structures and models for topology representation
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from core.logging import get_logger


class TopologyStatus(Enum):
    """Topology discovery status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class DiscoveryMethod(Enum):
    """Topology discovery methods"""
    SSH = "ssh"
    LLDP = "lldp"
    LACP = "lacp"
    SNMP = "snmp"
    NETCONF = "netconf"
    INVENTORY = "inventory"
    MANUAL = "manual"


@dataclass
class NetworkSegment:
    """Network segment information"""
    name: str
    vlan_id: Optional[int] = None
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    dhcp_enabled: bool = False
    devices: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BundleInterface:
    """Bundle interface information"""
    bundle_name: str
    member_interfaces: List[str]
    bundle_type: str = "lacp"
    min_links: int = 1
    max_links: Optional[int] = None
    status: str = "unknown"
    speed: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VLANInfo:
    """VLAN information"""
    vlan_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"
    interfaces: List[str] = field(default_factory=list)
    bridge_domains: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BridgeDomainInfo:
    """Bridge domain information"""
    name: str
    vlan_id: int
    source_device: str
    source_interface: str
    destination_device: str
    destination_interface: str
    topology_type: str = "p2p"
    status: str = "active"
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PathSegment:
    """Path segment information"""
    source_device: str
    target_device: str
    source_interface: str
    target_interface: str
    link_type: str = "ethernet"
    bandwidth: Optional[str] = None
    latency: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NetworkPath:
    """Complete network path"""
    path_id: str
    source_device: str
    destination_device: str
    segments: List[PathSegment]
    total_hops: int = 0
    total_latency: Optional[float] = None
    path_type: str = "shortest"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TopologyMetrics:
    """Topology performance and health metrics"""
    total_devices: int = 0
    total_interfaces: int = 0
    total_links: int = 0
    active_devices: int = 0
    active_interfaces: int = 0
    active_links: int = 0
    average_device_uptime: Optional[float] = None
    average_interface_utilization: Optional[float] = None
    network_redundancy_score: Optional[float] = None
    last_updated: Optional[str] = None


@dataclass
class DiscoverySession:
    """Topology discovery session information"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    status: TopologyStatus = TopologyStatus.PENDING
    methods_used: List[DiscoveryMethod] = field(default_factory=list)
    devices_scanned: int = 0
    devices_successful: int = 0
    devices_failed: int = 0
    error_messages: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class TopologyGraph:
    """
    Graph representation of network topology.
    
    This class provides graph operations for topology analysis,
    path finding, and network analysis.
    """
    
    def __init__(self):
        """Initialize the topology graph"""
        self.logger = get_logger(__name__)
        self.nodes = {}  # device_name -> device_info
        self.edges = {}  # (source, target) -> edge_info
        self.adjacency_list = {}  # device_name -> [neighbor_devices]
        
    def add_device(self, device_name: str, device_info: Dict[str, Any]) -> None:
        """
        Add a device to the topology graph.
        
        Args:
            device_name: Name of the device
            device_info: Device information dictionary
        """
        self.nodes[device_name] = device_info
        if device_name not in self.adjacency_list:
            self.adjacency_list[device_name] = []
    
    def add_link(self, source: str, target: str, link_info: Dict[str, Any]) -> None:
        """
        Add a link between devices.
        
        Args:
            source: Source device name
            target: Target device name
            link_info: Link information dictionary
        """
        # Add edge
        edge_key = (source, target)
        self.edges[edge_key] = link_info
        
        # Update adjacency list
        if source not in self.adjacency_list:
            self.adjacency_list[source] = []
        if target not in self.adjacency_list:
            self.adjacency_list[target] = []
        
        if target not in self.adjacency_list[source]:
            self.adjacency_list[source].append(target)
        if source not in self.adjacency_list[target]:
            self.adjacency_list[target].append(source)
    
    def remove_device(self, device_name: str) -> None:
        """
        Remove a device and all its links from the graph.
        
        Args:
            device_name: Name of the device to remove
        """
        if device_name in self.nodes:
            del self.nodes[device_name]
        
        if device_name in self.adjacency_list:
            # Remove all edges involving this device
            edges_to_remove = []
            for edge in self.edges:
                if device_name in edge:
                    edges_to_remove.append(edge)
            
            for edge in edges_to_remove:
                del self.edges[edge]
            
            # Remove from adjacency lists
            del self.adjacency_list[device_name]
            for neighbors in self.adjacency_list.values():
                if device_name in neighbors:
                    neighbors.remove(device_name)
    
    def get_neighbors(self, device_name: str) -> List[str]:
        """
        Get list of neighboring devices.
        
        Args:
            device_name: Name of the device
            
        Returns:
            List of neighboring device names
        """
        return self.adjacency_list.get(device_name, [])
    
    def get_device_degree(self, device_name: str) -> int:
        """
        Get the degree (number of connections) of a device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            Number of connections
        """
        return len(self.get_neighbors(device_name))
    
    def find_shortest_path(self, source: str, destination: str) -> List[str]:
        """
        Find shortest path between two devices using BFS.
        
        Args:
            source: Source device name
            destination: Destination device name
            
        Returns:
            List of devices in the shortest path
        """
        if source == destination:
            return [source]
        
        if source not in self.nodes or destination not in self.nodes:
            return []
        
        # BFS implementation
        queue = [(source, [source])]
        visited = {source}
        
        while queue:
            current, path = queue.pop(0)
            
            for neighbor in self.get_neighbors(current):
                if neighbor == destination:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []  # No path found
    
    def get_connected_components(self) -> List[List[str]]:
        """
        Find all connected components in the graph.
        
        Returns:
            List of connected component lists
        """
        visited = set()
        components = []
        
        for device in self.nodes:
            if device not in visited:
                component = self._dfs_component(device, visited)
                components.append(component)
        
        return components
    
    def _dfs_component(self, start_device: str, visited: set) -> List[str]:
        """DFS to find connected component"""
        component = []
        stack = [start_device]
        
        while stack:
            device = stack.pop()
            if device not in visited:
                visited.add(device)
                component.append(device)
                
                for neighbor in self.get_neighbors(device):
                    if neighbor not in visited:
                        stack.append(neighbor)
        
        return component
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the topology graph.
        
        Returns:
            Dictionary containing graph statistics
        """
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)
        
        # Calculate degrees
        degrees = [self.get_device_degree(device) for device in self.nodes]
        avg_degree = sum(degrees) / total_nodes if total_nodes > 0 else 0
        max_degree = max(degrees) if degrees else 0
        min_degree = min(degrees) if degrees else 0
        
        # Find connected components
        components = self.get_connected_components()
        largest_component = max(len(comp) for comp in components) if components else 0
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "average_degree": round(avg_degree, 2),
            "max_degree": max_degree,
            "min_degree": min_degree,
            "connected_components": len(components),
            "largest_component_size": largest_component,
            "graph_density": round(total_edges / (total_nodes * (total_nodes - 1)), 4) if total_nodes > 1 else 0
        }
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export graph to dictionary format.
        
        Returns:
            Dictionary representation of the graph
        """
        return {
            "nodes": self.nodes,
            "edges": {str(k): v for k, v in self.edges.items()},
            "adjacency_list": self.adjacency_list,
            "statistics": self.get_graph_statistics()
        }
    
    def import_from_dict(self, graph_data: Dict[str, Any]) -> None:
        """
        Import graph from dictionary format.
        
        Args:
            graph_data: Dictionary containing graph data
        """
        self.nodes = graph_data.get("nodes", {})
        self.edges = {eval(k): v for k, v in graph_data.get("edges", {}).items()}
        self.adjacency_list = graph_data.get("adjacency_list", {})
        
        self.logger.info(f"Imported graph with {len(self.nodes)} nodes and {len(self.edges)} edges")


class TopologyValidator:
    """
    Validator for topology data consistency and completeness.
    
    This class provides validation methods for ensuring
    topology data is valid and consistent.
    """
    
    def __init__(self):
        """Initialize the topology validator"""
        self.logger = get_logger(__name__)
    
    def validate_topology_data(self, topology_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate topology data for consistency and completeness.
        
        Args:
            topology_data: Topology data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ["nodes", "devices", "interfaces"]
        for field in required_fields:
            if field not in topology_data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # Validate nodes
        nodes_valid, node_errors = self._validate_nodes(topology_data.get("nodes", []))
        if not nodes_valid:
            errors.extend(node_errors)
        
        # Validate devices
        devices_valid, device_errors = self._validate_devices(topology_data.get("devices", {}))
        if not devices_valid:
            errors.extend(device_errors)
        
        # Validate interfaces
        interfaces_valid, interface_errors = self._validate_interfaces(topology_data.get("interfaces", {}))
        if not interfaces_valid:
            errors.extend(interface_errors)
        
        # Validate links
        if "links" in topology_data:
            links_valid, link_errors = self._validate_links(topology_data["links"], topology_data.get("devices", {}))
            if not links_valid:
                errors.extend(link_errors)
        
        return len(errors) == 0, errors
    
    def _validate_nodes(self, nodes: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validate topology nodes"""
        errors = []
        
        for i, node in enumerate(nodes):
            if "id" not in node:
                errors.append(f"Node {i}: Missing required field 'id'")
            if "name" not in node:
                errors.append(f"Node {i}: Missing required field 'name'")
            if "device_type" not in node:
                errors.append(f"Node {i}: Missing required field 'device_type'")
        
        return len(errors) == 0, errors
    
    def _validate_devices(self, devices: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate device information"""
        errors = []
        
        for device_name, device_info in devices.items():
            if not isinstance(device_info, dict):
                errors.append(f"Device {device_name}: Device info must be a dictionary")
                continue
            
            if "name" not in device_info:
                errors.append(f"Device {device_name}: Missing required field 'name'")
            if "device_type" not in device_info:
                errors.append(f"Device {device_name}: Missing required field 'device_type'")
        
        return len(errors) == 0, errors
    
    def _validate_interfaces(self, interfaces: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate interface information"""
        errors = []
        
        for interface_name, interface_info in interfaces.items():
            if not isinstance(interface_info, dict):
                errors.append(f"Interface {interface_name}: Interface info must be a dictionary")
                continue
            
            if "name" not in interface_info:
                errors.append(f"Interface {interface_name}: Missing required field 'name'")
            if "device_name" not in interface_info:
                errors.append(f"Interface {interface_name}: Missing required field 'device_name'")
            if "interface_type" not in interface_info:
                errors.append(f"Interface {interface_name}: Missing required field 'interface_type'")
        
        return len(errors) == 0, errors
    
    def _validate_links(self, links: List[Dict[str, Any]], devices: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate topology links"""
        errors = []
        
        for i, link in enumerate(links):
            if not isinstance(link, dict):
                errors.append(f"Link {i}: Link info must be a dictionary")
                continue
            
            if "source" not in link:
                errors.append(f"Link {i}: Missing required field 'source'")
            if "target" not in link:
                errors.append(f"Link {i}: Missing required field 'target'")
            
            # Check if source and target devices exist
            if "source" in link and "target" in link:
                source = link["source"]
                target = link["target"]
                
                if source not in devices:
                    errors.append(f"Link {i}: Source device '{source}' not found in devices")
                if target not in devices:
                    errors.append(f"Link {i}: Target device '{target}' not found in devices")
        
        return len(errors) == 0, errors
