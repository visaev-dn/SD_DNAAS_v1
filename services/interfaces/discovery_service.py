#!/usr/bin/env python3
"""
Discovery Service Interface
Abstract base class defining the contract for network discovery operations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class DiscoveryTarget:
    """Target for network discovery"""
    ip_address: str
    device_type: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    scan_protocols: List[str] = None  # ["snmp", "ssh", "http", etc.]


@dataclass
class DiscoveryResult:
    """Result of discovery operations"""
    success: bool
    discovered_devices: Optional[List[Dict[str, Any]]] = None
    topology_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    discovery_timestamp: Optional[str] = None


@dataclass
class DeviceInfo:
    """Information about a discovered device"""
    hostname: str
    ip_address: str
    device_type: str
    model: Optional[str] = None
    os_version: Optional[str] = None
    interfaces: List[str] = None
    status: str = "discovered"


class DiscoveryService(ABC):
    """
    Abstract base class for discovery services.
    
    This interface defines the contract that all discovery services
    must implement, ensuring consistency across different implementations.
    """
    
    @abstractmethod
    def discover_network(self, targets: List[DiscoveryTarget]) -> DiscoveryResult:
        """
        Discover devices in the network.
        
        Args:
            targets: List of DiscoveryTarget objects to scan
            
        Returns:
            DiscoveryResult with discovered devices and topology
        """
        pass
    
    @abstractmethod
    def discover_device(self, target: DiscoveryTarget) -> Optional[DeviceInfo]:
        """
        Discover a single device.
        
        Args:
            target: DiscoveryTarget to scan
            
        Returns:
            DeviceInfo if discovery successful, None otherwise
        """
        pass
    
    @abstractmethod
    def scan_lacp_connections(self) -> List[Dict[str, Any]]:
        """
        Scan for LACP connections in the network.
        
        Returns:
            List of LACP connection information
        """
        pass
    
    @abstractmethod
    def scan_lldp_neighbors(self) -> List[Dict[str, Any]]:
        """
        Scan for LLDP neighbor information.
        
        Returns:
            List of LLDP neighbor information
        """
        pass
    
    @abstractmethod
    def populate_from_inventory(self, inventory_path: str) -> bool:
        """
        Populate device information from inventory file.
        
        Args:
            inventory_path: Path to inventory file
            
        Returns:
            True if population successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_discovery_status(self) -> Dict[str, Any]:
        """
        Get current status of discovery operations.
        
        Returns:
            Dictionary containing discovery status information
        """
        pass
    
    @abstractmethod
    def validate_discovery_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate discovered data for consistency.
        
        Args:
            data: Discovery data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        pass
    
    @abstractmethod
    def export_discovery_results(self, format_type: str = "json") -> str:
        """
        Export discovery results in specified format.
        
        Args:
            format_type: Export format ("json", "yaml", "csv", etc.)
            
        Returns:
            String representation of exported results
        """
        pass
    
    @abstractmethod
    def get_discovery_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about discovery operations.
        
        Returns:
            Dictionary containing discovery statistics
        """
        pass
    
    @abstractmethod
    def clear_discovery_cache(self) -> bool:
        """
        Clear cached discovery data.
        
        Returns:
            True if cache cleared successfully, False otherwise
        """
        pass
