#!/usr/bin/env python3
"""
Network Models
Data structures and models for network-level information
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import ipaddress

from core.logging import get_logger


class NetworkProtocol(Enum):
    """Network protocols"""
    ETHERNET = "ethernet"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    VLAN = "vlan"
    LACP = "lacp"
    LLDP = "lldp"
    OSPF = "ospf"
    BGP = "bgp"
    ISIS = "isis"


class NetworkStatus(Enum):
    """Network status values"""
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    TESTING = "testing"
    DORMANT = "dormant"
    NOT_PRESENT = "not_present"
    LOWER_LAYER_DOWN = "lower_layer_down"


@dataclass
class IPAddress:
    """IP address information"""
    address: str
    version: int  # 4 or 6
    prefix_length: Optional[int] = None
    interface: Optional[str] = None
    status: NetworkStatus = NetworkStatus.UP
    is_primary: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate IP address after initialization"""
        try:
            ip = ipaddress.ip_address(self.address)
            if self.version != ip.version:
                raise ValueError(f"IP version mismatch: expected {self.version}, got {ip.version}")
        except ValueError as e:
            raise ValueError(f"Invalid IP address {self.address}: {e}")
    
    @property
    def network(self) -> Optional[str]:
        """Get network address if prefix length is specified"""
        if self.prefix_length is not None:
            try:
                network = ipaddress.ip_network(f"{self.address}/{self.prefix_length}", strict=False)
                return str(network.network_address)
            except ValueError:
                return None
        return None
    
    @property
    def is_private(self) -> bool:
        """Check if IP address is private"""
        try:
            ip = ipaddress.ip_address(self.address)
            return ip.is_private
        except ValueError:
            return False
    
    @property
    def is_loopback(self) -> bool:
        """Check if IP address is loopback"""
        try:
            ip = ipaddress.ip_address(self.address)
            return ip.is_loopback
        except ValueError:
            return False


@dataclass
class Subnet:
    """Subnet information"""
    network: str
    prefix_length: int
    gateway: Optional[str] = None
    dhcp_server: Optional[str] = None
    dns_servers: List[str] = field(default_factory=list)
    vlan_id: Optional[int] = None
    description: Optional[str] = None
    status: NetworkStatus = NetworkStatus.UP
    devices: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate subnet after initialization"""
        try:
            network = ipaddress.ip_network(f"{self.network}/{self.prefix_length}", strict=False)
            self.network = str(network.network_address)
        except ValueError as e:
            raise ValueError(f"Invalid subnet {self.network}/{self.prefix_length}: {e}")
    
    @property
    def network_address(self) -> str:
        """Get network address"""
        return self.network
    
    @property
    def broadcast_address(self) -> str:
        """Get broadcast address"""
        try:
            network = ipaddress.ip_network(f"{self.network}/{self.prefix_length}", strict=False)
            return str(network.broadcast_address)
        except ValueError:
            return ""
    
    @property
    def num_addresses(self) -> int:
        """Get number of addresses in subnet"""
        try:
            network = ipaddress.ip_network(f"{self.network}/{self.prefix_length}", strict=False)
            return network.num_addresses
        except ValueError:
            return 0
    
    @property
    def usable_addresses(self) -> int:
        """Get number of usable addresses in subnet"""
        return max(0, self.num_addresses - 2)  # Subtract network and broadcast


@dataclass
class RoutingTable:
    """Routing table information"""
    device_name: str
    routes: List[Dict[str, Any]] = field(default_factory=list)
    protocol: Optional[NetworkProtocol] = None
    last_updated: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def add_route(self, destination: str, next_hop: str, interface: str, 
                  protocol: str = "static", metric: Optional[int] = None) -> None:
        """Add a route to the routing table"""
        route = {
            "destination": destination,
            "next_hop": next_hop,
            "interface": interface,
            "protocol": protocol,
            "metric": metric,
            "added_at": datetime.now().isoformat()
        }
        self.routes.append(route)
    
    def get_route(self, destination: str) -> Optional[Dict[str, Any]]:
        """Get route for specific destination"""
        for route in self.routes:
            if route["destination"] == destination:
                return route
        return None
    
    def remove_route(self, destination: str) -> bool:
        """Remove route for specific destination"""
        for i, route in enumerate(self.routes):
            if route["destination"] == destination:
                del self.routes[i]
                return True
        return False


@dataclass
class NetworkInterface:
    """Network interface information"""
    name: str
    device_name: str
    interface_type: str
    status: NetworkStatus = NetworkStatus.UNKNOWN
    speed: Optional[str] = None
    duplex: Optional[str] = None
    mtu: Optional[int] = None
    ip_addresses: List[IPAddress] = field(default_factory=list)
    vlan_id: Optional[int] = None
    bundle: Optional[str] = None
    description: Optional[str] = None
    last_seen: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def add_ip_address(self, ip_address: IPAddress) -> None:
        """Add IP address to interface"""
        self.ip_addresses.append(ip_address)
    
    def remove_ip_address(self, address: str) -> bool:
        """Remove IP address from interface"""
        for i, ip_addr in enumerate(self.ip_addresses):
            if ip_addr.address == address:
                del self.ip_addresses[i]
                return True
        return False
    
    def get_primary_ip(self) -> Optional[IPAddress]:
        """Get primary IP address"""
        for ip_addr in self.ip_addresses:
            if ip_addr.is_primary:
                return ip_addr
        return self.ip_addresses[0] if self.ip_addresses else None
    
    def is_up(self) -> bool:
        """Check if interface is up"""
        return self.status == NetworkStatus.UP


@dataclass
class NetworkDevice:
    """Network device information"""
    name: str
    device_type: str
    ip_addresses: List[IPAddress] = field(default_factory=list)
    interfaces: List[NetworkInterface] = field(default_factory=list)
    routing_tables: List[RoutingTable] = field(default_factory=list)
    status: NetworkStatus = NetworkStatus.UNKNOWN
    uptime: Optional[float] = None
    last_seen: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def add_interface(self, interface: NetworkInterface) -> None:
        """Add interface to device"""
        self.interfaces.append(interface)
    
    def get_interface(self, interface_name: str) -> Optional[NetworkInterface]:
        """Get interface by name"""
        for interface in self.interfaces:
            if interface.name == interface_name:
                return interface
        return None
    
    def get_interfaces_by_status(self, status: NetworkStatus) -> List[NetworkInterface]:
        """Get interfaces by status"""
        return [interface for interface in self.interfaces if interface.status == status]
    
    def get_routing_table(self, protocol: Optional[NetworkProtocol] = None) -> Optional[RoutingTable]:
        """Get routing table for specific protocol"""
        for table in self.routing_tables:
            if protocol is None or table.protocol == protocol:
                return table
        return None


@dataclass
class NetworkTopology:
    """Complete network topology information"""
    devices: Dict[str, NetworkDevice] = field(default_factory=dict)
    subnets: Dict[str, Subnet] = field(default_factory=dict)
    vlans: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    bundles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_updated: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def add_device(self, device: NetworkDevice) -> None:
        """Add device to topology"""
        self.devices[device.name] = device
    
    def remove_device(self, device_name: str) -> None:
        """Remove device from topology"""
        if device_name in self.devices:
            del self.devices[device_name]
    
    def get_device(self, device_name: str) -> Optional[NetworkDevice]:
        """Get device by name"""
        return self.devices.get(device_name)
    
    def add_subnet(self, subnet: Subnet) -> None:
        """Add subnet to topology"""
        key = f"{subnet.network}/{subnet.prefix_length}"
        self.subnets[key] = subnet
    
    def get_subnet(self, network: str, prefix_length: int) -> Optional[Subnet]:
        """Get subnet by network and prefix length"""
        key = f"{network}/{prefix_length}"
        return self.subnets.get(key)
    
    def get_devices_in_subnet(self, network: str, prefix_length: int) -> List[str]:
        """Get devices in specific subnet"""
        subnet = self.get_subnet(network, prefix_length)
        if subnet:
            return subnet.devices
        return []
    
    def get_topology_statistics(self) -> Dict[str, Any]:
        """Get statistics about the network topology"""
        total_devices = len(self.devices)
        total_interfaces = sum(len(device.interfaces) for device in self.devices.values())
        total_subnets = len(self.subnets)
        total_vlans = len(self.vlans)
        total_bundles = len(self.bundles)
        
        # Count devices by status
        device_status_counts = {}
        for device in self.devices.values():
            status = device.status.value
            device_status_counts[status] = device_status_counts.get(status, 0) + 1
        
        # Count interfaces by status
        interface_status_counts = {}
        for device in self.devices.values():
            for interface in device.interfaces:
                status = interface.status.value
                interface_status_counts[status] = interface_status_counts.get(status, 0) + 1
        
        return {
            "total_devices": total_devices,
            "total_interfaces": total_interfaces,
            "total_subnets": total_subnets,
            "total_vlans": total_vlans,
            "total_bundles": total_bundles,
            "device_status_counts": device_status_counts,
            "interface_status_counts": interface_status_counts,
            "last_updated": self.last_updated
        }


class NetworkAnalyzer:
    """
    Network analysis and validation utilities.
    
    This class provides methods for analyzing network configurations,
    validating network settings, and performing network calculations.
    """
    
    def __init__(self):
        """Initialize the network analyzer"""
        self.logger = get_logger(__name__)
    
    def validate_ip_address(self, address: str) -> bool:
        """
        Validate IP address format.
        
        Args:
            address: IP address string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ipaddress.ip_address(address)
            return True
        except ValueError:
            return False
    
    def validate_subnet(self, network: str, prefix_length: int) -> bool:
        """
        Validate subnet configuration.
        
        Args:
            network: Network address
            prefix_length: Subnet prefix length
            
        Returns:
            True if valid, False otherwise
        """
        try:
            ipaddress.ip_network(f"{network}/{prefix_length}", strict=False)
            return True
        except ValueError:
            return False
    
    def is_ip_in_subnet(self, ip_address: str, network: str, prefix_length: int) -> bool:
        """
        Check if IP address is in specified subnet.
        
        Args:
            ip_address: IP address to check
            network: Network address
            prefix_length: Subnet prefix length
            
        Returns:
            True if IP is in subnet, False otherwise
        """
        try:
            ip = ipaddress.ip_address(ip_address)
            network_obj = ipaddress.ip_network(f"{network}/{prefix_length}", strict=False)
            return ip in network_obj
        except ValueError:
            return False
    
    def calculate_subnet_info(self, network: str, prefix_length: int) -> Dict[str, Any]:
        """
        Calculate subnet information.
        
        Args:
            network: Network address
            prefix_length: Subnet prefix length
            
        Returns:
            Dictionary containing subnet information
        """
        try:
            network_obj = ipaddress.ip_network(f"{network}/{prefix_length}", strict=False)
            
            return {
                "network_address": str(network_obj.network_address),
                "broadcast_address": str(network_obj.broadcast_address),
                "first_usable": str(network_obj.network_address + 1),
                "last_usable": str(network_obj.broadcast_address - 1),
                "total_addresses": network_obj.num_addresses,
                "usable_addresses": network_obj.num_addresses - 2,
                "subnet_mask": str(network_obj.netmask),
                "wildcard_mask": str(network_obj.hostmask)
            }
        except ValueError as e:
            self.logger.error(f"Failed to calculate subnet info: {e}")
            return {}
    
    def find_overlapping_subnets(self, subnets: List[Subnet]) -> List[List[Subnet]]:
        """
        Find overlapping subnets in a list.
        
        Args:
            subnets: List of subnets to check
            
        Returns:
            List of overlapping subnet groups
        """
        overlapping_groups = []
        checked = set()
        
        for i, subnet1 in enumerate(subnets):
            if i in checked:
                continue
                
            overlapping = [subnet1]
            checked.add(i)
            
            for j, subnet2 in enumerate(subnets[i+1:], i+1):
                if j in checked:
                    continue
                    
                try:
                    net1 = ipaddress.ip_network(f"{subnet1.network}/{subnet1.prefix_length}", strict=False)
                    net2 = ipaddress.ip_network(f"{subnet2.network}/{subnet2.prefix_length}", strict=False)
                    
                    if net1.overlaps(net2):
                        overlapping.append(subnet2)
                        checked.add(j)
                except ValueError:
                    continue
            
            if len(overlapping) > 1:
                overlapping_groups.append(overlapping)
        
        return overlapping_groups
    
    def suggest_subnet_allocation(self, network: str, prefix_length: int, 
                                required_sizes: List[int]) -> List[Subnet]:
        """
        Suggest subnet allocation for given requirements.
        
        Args:
            network: Base network address
            prefix_length: Base network prefix length
            required_sizes: List of required subnet sizes
            
        Returns:
            List of suggested subnets
        """
        try:
            base_network = ipaddress.ip_network(f"{network}/{prefix_length}", strict=False)
            suggestions = []
            
            # Sort required sizes in descending order for efficient allocation
            sorted_sizes = sorted(required_sizes, reverse=True)
            
            current_network = base_network
            for size in sorted_sizes:
                # Find appropriate prefix length for required size
                required_prefix = 32 - (size - 1).bit_length()
                
                if required_prefix < prefix_length:
                    self.logger.warning(f"Cannot allocate subnet of size {size} in base network {network}/{prefix_length}")
                    continue
                
                # Create subnet
                subnet = ipaddress.ip_network(f"{current_network.network_address}/{required_prefix}", strict=False)
                
                # Create Subnet object
                subnet_obj = Subnet(
                    network=str(subnet.network_address),
                    prefix_length=required_prefix,
                    description=f"Allocated for size {size}"
                )
                suggestions.append(subnet_obj)
                
                # Move to next available network
                current_network = list(current_network.subnets(new_prefix=required_prefix))[1]
            
            return suggestions
            
        except ValueError as e:
            self.logger.error(f"Failed to suggest subnet allocation: {e}")
            return []
