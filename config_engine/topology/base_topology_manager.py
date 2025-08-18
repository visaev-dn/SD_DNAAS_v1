#!/usr/bin/env python3
"""
Base Topology Manager
Abstract base class for all topology management operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.logging import get_logger
from core.exceptions import BusinessLogicError, ValidationError


@dataclass
class DeviceInfo:
    """Device information structure"""
    name: str
    device_type: str
    ip_address: Optional[str] = None
    status: str = "unknown"
    capabilities: List[str] = None
    interfaces: List[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class InterfaceInfo:
    """Interface information structure"""
    name: str
    device_name: str
    interface_type: str
    status: str = "unknown"
    speed: Optional[str] = None
    vlan: Optional[int] = None
    bundle: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TopologyNode:
    """Topology node structure"""
    id: str
    name: str
    device_type: str
    position: Optional[Dict[str, float]] = None
    properties: Optional[Dict[str, Any]] = None


@dataclass
class TopologyLink:
    """Topology link structure"""
    source: str
    target: str
    source_interface: str
    target_interface: str
    link_type: str = "ethernet"
    properties: Optional[Dict[str, Any]] = None


@dataclass
class TopologyData:
    """Complete topology data structure"""
    nodes: List[TopologyNode]
    links: List[TopologyLink]
    devices: Dict[str, DeviceInfo]
    interfaces: Dict[str, InterfaceInfo]
    metadata: Optional[Dict[str, Any]] = None
    discovered_at: Optional[str] = None


@dataclass
class DiscoveryConfig:
    """Configuration for topology discovery"""
    scan_ssh: bool = True
    scan_lldp: bool = True
    scan_lacp: bool = True
    scan_vlans: bool = True
    scan_bundles: bool = True
    timeout_seconds: int = 30
    max_concurrent_scans: int = 10
    include_inactive: bool = False


@dataclass
class DiscoveryResult:
    """Result of topology discovery operation"""
    success: bool
    topology_data: Optional[TopologyData] = None
    error_message: Optional[str] = None
    devices_discovered: int = 0
    interfaces_discovered: int = 0
    links_discovered: int = 0
    metadata: Optional[Dict[str, Any]] = None


class BaseTopologyManager(ABC):
    """
    Abstract base class for all topology management operations.
    
    This class provides common functionality and enforces the interface
    that all topology managers must implement.
    """
    
    def __init__(self, topology_dir: str = "topology", config_dir: str = "configs"):
        """
        Initialize the base topology manager.
        
        Args:
            topology_dir: Directory containing topology files
            config_dir: Directory containing device configurations
        """
        self.topology_dir = Path(topology_dir)
        self.config_dir = Path(config_dir)
        self.logger = get_logger(__name__)
        
        # Ensure directories exist
        self.topology_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize data structures
        self.topology_data = TopologyData(
            nodes=[],
            links=[],
            devices={},
            interfaces={},
            metadata={},
            discovered_at=None
        )
        
        self.logger.info(f"Base Topology Manager initialized with topology_dir: {topology_dir}")
    
    @abstractmethod
    def discover_topology(self, config: DiscoveryConfig) -> DiscoveryResult:
        """
        Discover network topology.
        
        Args:
            config: Discovery configuration
            
        Returns:
            DiscoveryResult with topology data
        """
        pass
    
    @abstractmethod
    def scan_device(self, device_name: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan a single device for topology information.
        
        Args:
            device_name: Name of the device to scan
            device_info: Device information dictionary
            
        Returns:
            Dictionary containing device topology data
        """
        pass
    
    @abstractmethod
    def get_topology_tree(self, root_device: Optional[str] = None) -> Dict[str, Any]:
        """
        Get topology in tree format.
        
        Args:
            root_device: Optional root device for tree structure
            
        Returns:
            Dictionary containing topology tree
        """
        pass
    
    @abstractmethod
    def get_device_status(self, device_name: str) -> Dict[str, Any]:
        """
        Get current status of a device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            Dictionary containing device status
        """
        pass
    
    @abstractmethod
    def get_device_interfaces(self, device_name: str) -> List[InterfaceInfo]:
        """
        Get interfaces for a specific device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            List of interface information
        """
        pass
    
    def validate_topology(self, topology_data: TopologyData) -> Tuple[bool, List[str]]:
        """
        Validate topology data for consistency and completeness.
        
        Args:
            topology_data: Topology data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for required fields
        if not topology_data.nodes:
            errors.append("Topology must contain at least one node")
        
        if not topology_data.devices:
            errors.append("Topology must contain device information")
        
        # Validate device consistency
        for node in topology_data.nodes:
            if node.id not in topology_data.devices:
                errors.append(f"Node {node.id} missing from devices dictionary")
        
        # Validate interface consistency
        for device_name, device_info in topology_data.devices.items():
            if device_info.interfaces:
                for interface_name in device_info.interfaces:
                    if interface_name not in topology_data.interfaces:
                        errors.append(f"Interface {interface_name} missing from interfaces dictionary")
        
        # Validate link consistency
        for link in topology_data.links:
            if link.source not in topology_data.devices:
                errors.append(f"Link source {link.source} not found in devices")
            if link.target not in topology_data.devices:
                errors.append(f"Link target {link.target} not found in devices")
        
        return len(errors) == 0, errors
    
    def export_topology(self, format_type: str = "json", file_path: Optional[str] = None) -> str:
        """
        Export topology data in specified format.
        
        Args:
            format_type: Export format (json, yaml, etc.)
            file_path: Optional file path for export
            
        Returns:
            String representation of exported topology
        """
        try:
            if format_type.lower() == "json":
                return self._export_json(file_path)
            elif format_type.lower() == "yaml":
                return self._export_yaml(file_path)
            else:
                raise BusinessLogicError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to export topology: {e}")
            raise BusinessLogicError(f"Export failed: {e}")
    
    def _export_json(self, file_path: Optional[str] = None) -> str:
        """Export topology to JSON format"""
        import json
        
        # Convert topology data to dictionary
        export_data = {
            "nodes": [node.__dict__ for node in self.topology_data.nodes],
            "links": [link.__dict__ for link in self.topology_data.links],
            "devices": {name: device.__dict__ for name, device in self.topology_data.devices.items()},
            "interfaces": {name: interface.__dict__ for name, interface in self.topology_data.interfaces.items()},
            "metadata": self.topology_data.metadata,
            "discovered_at": self.topology_data.discovered_at or datetime.now().isoformat()
        }
        
        json_str = json.dumps(export_data, indent=2)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_str)
            self.logger.info(f"Topology exported to: {file_path}")
        
        return json_str
    
    def _export_yaml(self, file_path: Optional[str] = None) -> str:
        """Export topology to YAML format"""
        try:
            import yaml
        except ImportError:
            raise BusinessLogicError("PyYAML not installed. Install with: pip install pyyaml")
        
        # Convert topology data to dictionary
        export_data = {
            "nodes": [node.__dict__ for node in self.topology_data.nodes],
            "links": [link.__dict__ for link in self.topology_data.links],
            "devices": {name: device.__dict__ for name, device in self.topology_data.devices.items()},
            "interfaces": {name: interface.__dict__ for name, interface in self.topology_data.interfaces.items()},
            "metadata": self.topology_data.metadata,
            "discovered_at": self.topology_data.discovered_at or datetime.now().isoformat()
        }
        
        yaml_str = yaml.dump(export_data, default_flow_style=False, indent=2)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(yaml_str)
            self.logger.info(f"Topology exported to: {file_path}")
        
        return yaml_str
    
    def get_topology_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current topology.
        
        Returns:
            Dictionary containing topology statistics
        """
        return {
            "total_nodes": len(self.topology_data.nodes),
            "total_links": len(self.topology_data.links),
            "total_devices": len(self.topology_data.devices),
            "total_interfaces": len(self.topology_data.interfaces),
            "device_types": self._count_device_types(),
            "interface_types": self._count_interface_types(),
            "discovered_at": self.topology_data.discovered_at,
            "topology_size_kb": self._calculate_topology_size()
        }
    
    def _count_device_types(self) -> Dict[str, int]:
        """Count devices by type"""
        device_counts = {}
        for device in self.topology_data.devices.values():
            device_type = device.device_type
            device_counts[device_type] = device_counts.get(device_type, 0) + 1
        return device_counts
    
    def _count_interface_types(self) -> Dict[str, int]:
        """Count interfaces by type"""
        interface_counts = {}
        for interface in self.topology_data.interfaces.values():
            interface_type = interface.interface_type
            interface_counts[interface_type] = interface_counts.get(interface_type, 0) + 1
        return interface_counts
    
    def _calculate_topology_size(self) -> float:
        """Calculate approximate topology size in KB"""
        import sys
        
        # Get size of topology data in memory
        size_bytes = sys.getsizeof(self.topology_data)
        
        # Convert to KB
        return round(size_bytes / 1024, 2)
    
    def find_path(self, source: str, destination: str) -> List[str]:
        """
        Find path between two devices.
        
        Args:
            source: Source device name
            destination: Destination device name
            
        Returns:
            List of devices in the path
        """
        try:
            # Simple path finding implementation
            # This would be enhanced with proper graph algorithms
            if source == destination:
                return [source]
            
            # Check if direct link exists
            for link in self.topology_data.links:
                if (link.source == source and link.target == destination) or \
                   (link.source == destination and link.target == source):
                    return [source, destination]
            
            # For now, return simple path through spine
            # This would be enhanced with proper routing algorithms
            return [source, "spine1", destination]
            
        except Exception as e:
            self.logger.error(f"Path finding failed: {e}")
            return []
    
    def clear_topology(self) -> None:
        """Clear all topology data"""
        self.topology_data = TopologyData(
            nodes=[],
            links=[],
            devices={},
            interfaces={},
            metadata={},
            discovered_at=None
        )
        self.logger.info("Topology data cleared")
    
    def get_manager_info(self) -> Dict[str, Any]:
        """
        Get information about this topology manager.
        
        Returns:
            Dictionary containing manager information
        """
        return {
            "manager_type": self.__class__.__name__,
            "topology_dir": str(self.topology_dir),
            "config_dir": str(self.config_dir),
            "capabilities": self.get_capabilities(),
            "supported_formats": self.get_supported_formats()
        }
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of manager capabilities.
        
        Returns:
            List of capability strings
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported export formats.
        
        Returns:
            List of supported format strings
        """
        pass
