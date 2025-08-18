#!/usr/bin/env python3
"""
Topology Service Interface
Abstract base class defining the contract for topology operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class TopologyNode:
    """Represents a node in the network topology"""
    device_name: str
    device_type: str
    interfaces: List[str]
    status: str = "unknown"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TopologyLink:
    """Represents a link between two nodes"""
    source_device: str
    source_interface: str
    destination_device: str
    destination_interface: str
    link_type: str = "ethernet"
    status: str = "unknown"


@dataclass
class TopologyScanResult:
    """Result of topology scanning operations"""
    success: bool
    nodes: Optional[List[TopologyNode]] = None
    links: Optional[List[TopologyLink]] = None
    error_message: Optional[str] = None
    scan_timestamp: Optional[str] = None


class TopologyService(ABC):
    """
    Abstract base class for topology services.
    
    This interface defines the contract that all topology services
    must implement, ensuring consistency across different implementations.
    """
    
    @abstractmethod
    def scan_topology(self) -> TopologyScanResult:
        """
        Scan the network to discover current topology.
        
        Returns:
            TopologyScanResult with discovered nodes and links
        """
        pass
    
    @abstractmethod
    def get_topology_tree(self, format_type: str = "ascii") -> str:
        """
        Generate a topology tree representation.
        
        Args:
            format_type: Type of tree format ("ascii", "minimized", etc.)
            
        Returns:
            String representation of the topology tree
        """
        pass
    
    @abstractmethod
    def get_device_status(self, device_name: str) -> Dict[str, Any]:
        """
        Get current status of a specific device.
        
        Args:
            device_name: Name of the device to check
            
        Returns:
            Dictionary containing device status information
        """
        pass
    
    @abstractmethod
    def get_device_interfaces(self, device_name: str) -> List[Dict[str, Any]]:
        """
        Get interface information for a specific device.
        
        Args:
            device_name: Name of the device
            
        Returns:
            List of interface information dictionaries
        """
        pass
    
    @abstractmethod
    def validate_topology(self) -> Tuple[bool, List[str]]:
        """
        Validate the current topology for consistency.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def export_topology(self, format_type: str = "json") -> str:
        """
        Export topology data in specified format.
        
        Args:
            format_type: Export format ("json", "yaml", "csv", etc.)
            
        Returns:
            String representation of exported topology
        """
        pass
    
    @abstractmethod
    def get_topology_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the current topology.
        
        Returns:
            Dictionary containing topology statistics
        """
        pass
    
    @abstractmethod
    def find_path(self, source: str, destination: str) -> Optional[List[str]]:
        """
        Find a path between two devices.
        
        Args:
            source: Source device name
            destination: Destination device name
            
        Returns:
            List of devices in the path, or None if no path found
        """
        pass
