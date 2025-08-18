#!/usr/bin/env python3
"""
Device Types and Classification
Consolidated device type definitions and classification logic
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from core.logging import get_logger


class DeviceType(Enum):
    """Device type classification."""
    LEAF = "leaf"           # Can be source or destination, has ACs
    SPINE = "spine"         # Transport only, no ACs
    SUPERSPINE = "superspine"  # Can be destination only, has ACs for bridge domains
    ACCESS = "access"       # Access layer devices
    CORE = "core"           # Core network devices
    EDGE = "edge"           # Edge network devices
    UNKNOWN = "unknown"


class InterfaceType(Enum):
    """Interface type classification."""
    ACCESS = "access"           # Access interfaces (leaf and superspine)
    TRANSPORT_10GE = "transport_10ge"    # 10GE transport interfaces
    TRANSPORT_100GE = "transport_100ge"  # 100GE transport interfaces
    TRANSPORT_400GE = "transport_400ge"  # 400GE transport interfaces
    BUNDLE = "bundle"           # Bundle interfaces
    LOOPBACK = "loopback"       # Loopback interfaces
    MANAGEMENT = "management"   # Management interfaces
    UNKNOWN = "unknown"


@dataclass
class DeviceCapabilities:
    """Device capabilities structure"""
    can_be_source: bool = False
    can_be_destination: bool = False
    supports_access_interfaces: bool = False
    supports_transport_interfaces: bool = False
    supports_bundles: bool = False
    supports_vlans: bool = False
    supports_bridge_domains: bool = False
    max_interfaces: Optional[int] = None
    max_vlans: Optional[int] = None


class DeviceClassifier:
    """
    Device and interface classifier with comprehensive support.
    
    Implements device type and interface type classification
    system for all device types in the network.
    """
    
    def __init__(self):
        """Initialize the device classifier."""
        self.logger = get_logger(__name__)
        
        # Interface patterns for validation
        self.interface_patterns = {
            InterfaceType.ACCESS: [
                r'^ge\d+-\d+/\d+/\d+$',      # Any GE interface (ge10, ge100, etc.)
                r'^xe\d+-\d+/\d+/\d+$',      # Any XE interface
                r'^et\d+-\d+/\d+/\d+$',      # Any ET interface
            ],
            InterfaceType.TRANSPORT_10GE: [
                r'^ge10-\d+/\d+/\d+$',       # ge10-0/0/X (10GE transport)
            ],
            InterfaceType.TRANSPORT_100GE: [
                r'^ge100-\d+/\d+/\d+$',      # ge100-0/0/X, ge100-4/0/X, ge100-5/0/X (100GE transport)
                r'^xe100-\d+/\d+/\d+$',      # xe100 interfaces (100GE)
            ],
            InterfaceType.TRANSPORT_400GE: [
                r'^et400-\d+/\d+/\d+$',      # et400 interfaces (400GE)
            ],
            InterfaceType.BUNDLE: [
                r'^bundle-\d+$',              # bundle-X
            ],
            InterfaceType.LOOPBACK: [
                r'^lo\d+$',                   # lo0, lo1, etc.
            ],
            InterfaceType.MANAGEMENT: [
                r'^mgmt\d+$',                 # mgmt0, mgmt1, etc.
            ]
        }
        
        # Device type patterns
        self.device_patterns = {
            DeviceType.LEAF: [
                r'leaf\d+',                   # leaf1, leaf2, etc.
                r'access\d+',                 # access1, access2, etc.
                r'^l\d+$',                    # l1, l2, etc.
            ],
            DeviceType.SPINE: [
                r'spine\d+',                  # spine1, spine2, etc.
                r'^s\d+$',                    # s1, s2, etc.
            ],
            DeviceType.SUPERSPINE: [
                r'superspine\d+',             # superspine1, superspine2, etc.
                r'ss\d+',                     # ss1, ss2, etc.
                r'^ss\d+$',                   # ss1, ss2, etc.
            ],
            DeviceType.ACCESS: [
                r'access\d+',                 # access1, access2, etc.
                r'edge\d+',                   # edge1, edge2, etc.
            ],
            DeviceType.CORE: [
                r'core\d+',                   # core1, core2, etc.
                r'backbone\d+',               # backbone1, backbone2, etc.
            ]
        }
        
        # Device capabilities mapping
        self.device_capabilities = {
            DeviceType.LEAF: DeviceCapabilities(
                can_be_source=True,
                can_be_destination=True,
                supports_access_interfaces=True,
                supports_transport_interfaces=True,
                supports_bundles=True,
                supports_vlans=True,
                supports_bridge_domains=True,
                max_interfaces=48,
                max_vlans=4094
            ),
            DeviceType.SPINE: DeviceCapabilities(
                can_be_source=False,
                can_be_destination=False,
                supports_access_interfaces=False,
                supports_transport_interfaces=True,
                supports_bundles=True,
                supports_vlans=False,
                supports_bridge_domains=False,
                max_interfaces=32,
                max_vlans=0
            ),
            DeviceType.SUPERSPINE: DeviceCapabilities(
                can_be_source=False,
                can_be_destination=True,
                supports_access_interfaces=True,
                supports_transport_interfaces=True,
                supports_bundles=True,
                supports_vlans=True,
                supports_bridge_domains=True,
                max_interfaces=64,
                max_vlans=4094
            ),
            DeviceType.ACCESS: DeviceCapabilities(
                can_be_source=True,
                can_be_destination=True,
                supports_access_interfaces=True,
                supports_transport_interfaces=False,
                supports_bundles=False,
                supports_vlans=True,
                supports_bridge_domains=True,
                max_interfaces=24,
                max_vlans=1024
            ),
            DeviceType.CORE: DeviceCapabilities(
                can_be_source=False,
                can_be_destination=False,
                supports_access_interfaces=False,
                supports_transport_interfaces=True,
                supports_bundles=True,
                supports_vlans=False,
                supports_bridge_domains=False,
                max_interfaces=48,
                max_vlans=0
            )
        }
    
    def detect_device_type(self, device_name: str, device_info: Optional[Dict[str, Any]] = None) -> DeviceType:
        """
        Detect device type based on name and optional device information.
        
        Args:
            device_name: Name of the device
            device_info: Optional device information dictionary
            
        Returns:
            DeviceType enum value
        """
        try:
            device_name_lower = device_name.lower()
            
            # Check device patterns
            for device_type, patterns in self.device_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, device_name_lower):
                        self.logger.debug(f"Device {device_name} classified as {device_type.value}")
                        return device_type
            
            # Fallback to unknown if no pattern matches
            self.logger.warning(f"Could not classify device {device_name}, defaulting to UNKNOWN")
            return DeviceType.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Device type detection failed for {device_name}: {e}")
            return DeviceType.UNKNOWN
    
    def classify_interface(self, interface_name: str, device_type: Optional[DeviceType] = None) -> InterfaceType:
        """
        Classify interface based on name and optional device type.
        
        Args:
            interface_name: Name of the interface
            device_type: Optional device type for context
            
        Returns:
            InterfaceType enum value
        """
        try:
            # Check interface patterns
            for interface_type, patterns in self.interface_patterns.items():
                for pattern in patterns:
                    if re.match(pattern, interface_name):
                        self.logger.debug(f"Interface {interface_name} classified as {interface_type.value}")
                        return interface_type
            
            # Fallback to unknown if no pattern matches
            self.logger.warning(f"Could not classify interface {interface_name}, defaulting to UNKNOWN")
            return InterfaceType.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Interface classification failed for {interface_name}: {e}")
            return InterfaceType.UNKNOWN
    
    def get_device_capabilities(self, device_type: DeviceType) -> DeviceCapabilities:
        """
        Get capabilities for a specific device type.
        
        Args:
            device_type: Device type to get capabilities for
            
        Returns:
            DeviceCapabilities object
        """
        return self.device_capabilities.get(device_type, DeviceCapabilities())
    
    def validate_device_interface_compatibility(self, device_type: DeviceType, interface_type: InterfaceType) -> bool:
        """
        Validate if an interface type is compatible with a device type.
        
        Args:
            device_type: Type of the device
            interface_type: Type of the interface
            
        Returns:
            True if compatible, False otherwise
        """
        try:
            capabilities = self.get_device_capabilities(device_type)
            
            if interface_type == InterfaceType.ACCESS:
                return capabilities.supports_access_interfaces
            elif interface_type in [InterfaceType.TRANSPORT_10GE, InterfaceType.TRANSPORT_100GE, InterfaceType.TRANSPORT_400GE]:
                return capabilities.supports_transport_interfaces
            elif interface_type == InterfaceType.BUNDLE:
                return capabilities.supports_bundles
            elif interface_type in [InterfaceType.LOOPBACK, InterfaceType.MANAGEMENT]:
                return True  # All devices support these
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Interface compatibility validation failed: {e}")
            return False
    
    def can_device_be_source(self, device_type: DeviceType) -> bool:
        """Check if device type can be a source for bridge domains"""
        capabilities = self.get_device_capabilities(device_type)
        return capabilities.can_be_source
    
    def can_device_be_destination(self, device_type: DeviceType) -> bool:
        """Check if device type can be a destination for bridge domains"""
        capabilities = self.get_device_capabilities(device_type)
        return capabilities.can_be_destination
    
    def supports_bridge_domains(self, device_type: DeviceType) -> bool:
        """Check if device type supports bridge domains"""
        capabilities = self.get_device_capabilities(device_type)
        return capabilities.supports_bridge_domains
    
    def get_interface_speed(self, interface_name: str) -> Optional[str]:
        """
        Extract interface speed from interface name.
        
        Args:
            interface_name: Name of the interface
            
        Returns:
            Speed string or None if not found
        """
        try:
            # Extract speed from interface patterns
            if re.match(r'^ge10-\d+/\d+/\d+$', interface_name):
                return "10GE"
            elif re.match(r'^ge100-\d+/\d+/\d+$', interface_name):
                return "100GE"
            elif re.match(r'^et400-\d+/\d+/\d+$', interface_name):
                return "400GE"
            elif re.match(r'^ge\d+-\d+/\d+/\d+$', interface_name):
                return "1GE"
            elif re.match(r'^xe\d+-\d+/\d+/\d+$', interface_name):
                return "10GE"
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to extract interface speed from {interface_name}: {e}")
            return None
    
    def get_interface_bundle(self, interface_name: str) -> Optional[str]:
        """
        Extract bundle information from interface name.
        
        Args:
            interface_name: Name of the interface
            
        Returns:
            Bundle name or None if not found
        """
        try:
            # Check if interface is part of a bundle
            bundle_match = re.search(r'bundle-(\d+)', interface_name)
            if bundle_match:
                return f"bundle-{bundle_match.group(1)}"
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract bundle from {interface_name}: {e}")
            return None
    
    def get_all_device_types(self) -> List[DeviceType]:
        """Get list of all supported device types"""
        return list(DeviceType)
    
    def get_all_interface_types(self) -> List[InterfaceType]:
        """Get list of all supported interface types"""
        return list(InterfaceType)
    
    def get_device_type_description(self, device_type: DeviceType) -> str:
        """Get human-readable description of device type"""
        descriptions = {
            DeviceType.LEAF: "Leaf switch - Access layer device with AC interfaces",
            DeviceType.SPINE: "Spine switch - Transport layer device, no AC interfaces",
            DeviceType.SUPERSPINE: "Superspine switch - High-capacity transport with AC support",
            DeviceType.ACCESS: "Access switch - Edge device with AC interfaces",
            DeviceType.CORE: "Core switch - Backbone transport device",
            DeviceType.EDGE: "Edge switch - Network boundary device",
            DeviceType.UNKNOWN: "Unknown device type"
        }
        return descriptions.get(device_type, "Unknown device type")
    
    def get_interface_type_description(self, interface_type: InterfaceType) -> str:
        """Get human-readable description of interface type"""
        descriptions = {
            InterfaceType.ACCESS: "Access interface - End device connection",
            InterfaceType.TRANSPORT_10GE: "10GE transport interface - High-speed transport",
            InterfaceType.TRANSPORT_100GE: "100GE transport interface - High-capacity transport",
            InterfaceType.TRANSPORT_400GE: "400GE transport interface - Ultra-high capacity transport",
            InterfaceType.BUNDLE: "Bundle interface - Link aggregation group",
            InterfaceType.LOOPBACK: "Loopback interface - Virtual interface",
            InterfaceType.MANAGEMENT: "Management interface - Device management",
            InterfaceType.UNKNOWN: "Unknown interface type"
        }
        return descriptions.get(interface_type, "Unknown interface type")


# Global classifier instance
_device_classifier: Optional[DeviceClassifier] = None


def get_device_classifier() -> DeviceClassifier:
    """Get global device classifier instance"""
    global _device_classifier
    if _device_classifier is None:
        _device_classifier = DeviceClassifier()
    return _device_classifier


def detect_device_type(device_name: str, device_info: Optional[Dict[str, Any]] = None) -> DeviceType:
    """Convenience function to detect device type"""
    return get_device_classifier().detect_device_type(device_name, device_info)


def classify_interface(interface_name: str, device_type: Optional[DeviceType] = None) -> InterfaceType:
    """Convenience function to classify interface"""
    return get_device_classifier().classify_interface(interface_name, device_type)
