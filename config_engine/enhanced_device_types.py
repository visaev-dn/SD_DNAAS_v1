#!/usr/bin/env python3
"""
Enhanced Device Type and Interface Type Classification
Implements the enhanced device type and interface type classification system
for supporting Superspine devices as destinations.
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

class DeviceType(Enum):
    """Enhanced device type classification."""
    LEAF = "leaf"           # Can be source or destination, has ACs
    SPINE = "spine"         # Transport only, no ACs
    SUPERSPINE = "superspine"  # Can be destination only, has ACs for bridge domains
    UNKNOWN = "unknown"

class InterfaceType(Enum):
    """Interface type classification."""
    ACCESS = "access"           # Access interfaces (leaf and superspine)
    TRANSPORT_10GE = "transport_10ge"    # 10GE transport interfaces
    TRANSPORT_100GE = "transport_100ge"  # 100GE transport interfaces
    UNKNOWN = "unknown"

class EnhancedDeviceClassifier:
    """
    Enhanced device and interface classifier with Superspine support.
    
    Implements the enhanced device type and interface type classification
    system for supporting Superspine devices as destinations.
    """
    
    def __init__(self):
        """Initialize the enhanced device classifier."""
        # Interface patterns for validation - based on actual topology data
        self.interface_patterns = {
            InterfaceType.ACCESS: [
                # Access interfaces can be any speed - usage depends on context
                r'^ge\d+-\d+/\d+/\d+$',  # Any GE interface (ge10, ge100, etc.)
            ],
            InterfaceType.TRANSPORT_10GE: [
                r'^ge10-\d+/\d+/\d+$',   # ge10-0/0/X (10GE transport)
            ],
            InterfaceType.TRANSPORT_100GE: [
                r'^ge100-\d+/\d+/\d+$',  # ge100-0/0/X, ge100-4/0/X, ge100-5/0/X (100GE transport)
            ]
        }
        
        # Bundle patterns (valid for all device types)
        self.bundle_patterns = [
            r'^bundle-\d+$',  # bundle-X
        ]
    
    def detect_device_type(self, device_name: str, device_info: Optional[Dict] = None) -> DeviceType:
        """
        Enhanced device type detection with Superspine support.
        
        Args:
            device_name: Name of the device
            device_info: Optional device information dictionary
            
        Returns:
            DeviceType enum value
        """
        device_name_lower = device_name.lower()
        
        # Enhanced Superspine detection
        if "superspine" in device_name_lower or "ss" in device_name_lower:
            return DeviceType.SUPERSPINE
        elif "spine" in device_name_lower:
            return DeviceType.SPINE
        elif "leaf" in device_name_lower:
            return DeviceType.LEAF
        else:
            return DeviceType.UNKNOWN
    
    def _is_valid_leaf_interface(self, interface: str) -> bool:
        """
        Validate interfaces for leaf devices.
        
        Args:
            interface: Interface name to validate
            
        Returns:
            True if valid leaf interface, False otherwise
        """
        # Leaf devices support: Any GE interface (AC or transport), bundles
        patterns = (
            self.interface_patterns[InterfaceType.ACCESS] +
            self.interface_patterns[InterfaceType.TRANSPORT_10GE] +
            self.interface_patterns[InterfaceType.TRANSPORT_100GE] +
            self.bundle_patterns
        )
        
        return any(re.match(pattern, interface) for pattern in patterns)
    
    def _is_valid_transport_interface(self, interface: str) -> bool:
        """
        Validate transport interfaces (10GE, 100GE, bundles).
        
        Args:
            interface: Interface name to validate
            
        Returns:
            True if valid transport interface, False otherwise
        """
        # Transport devices support: 10GE, 100GE, bundles only
        patterns = (
            self.interface_patterns[InterfaceType.TRANSPORT_10GE] +
            self.interface_patterns[InterfaceType.TRANSPORT_100GE] +
            self.bundle_patterns
        )
        
        return any(re.match(pattern, interface) for pattern in patterns)
    
    def _is_valid_superspine_interface(self, interface: str) -> bool:
        """
        Validate interfaces for superspine devices.
        
        Args:
            interface: Interface name to validate
            
        Returns:
            True if valid superspine interface, False otherwise
        """
        # Superspine devices support: Any GE interface (AC or transport), bundles
        # Note: Specific interface availability depends on topology (reserved for spines)
        patterns = (
            self.interface_patterns[InterfaceType.ACCESS] +
            self.interface_patterns[InterfaceType.TRANSPORT_10GE] +
            self.interface_patterns[InterfaceType.TRANSPORT_100GE] +
            self.bundle_patterns
        )
        
        return any(re.match(pattern, interface) for pattern in patterns)
    
    def validate_interface_for_device(self, interface: str, device_type: DeviceType) -> bool:
        """
        Validate interface compatibility with device type.
        
        Args:
            interface: Interface name to validate
            device_type: Device type to validate against
            
        Returns:
            True if interface is valid for device type, False otherwise
        """
        if device_type == DeviceType.LEAF:
            return self._is_valid_leaf_interface(interface)
        elif device_type == DeviceType.SPINE:
            # Spines only support transport interfaces (no AC interfaces)
            return self._is_valid_transport_interface(interface)
        elif device_type == DeviceType.SUPERSPINE:
            # Superspines support any GE interface (AC or transport), bundles
            # Note: Specific availability depends on topology (reserved for spines)
            return self._is_valid_superspine_interface(interface)
        return False
    
    def parse_10ge_interface(self, interface: str) -> Optional[Dict]:
        """
        Parse 10GE interface (ge10-0/0/X).
        
        Args:
            interface: Interface name to parse
            
        Returns:
            Dictionary with interface details or None if invalid
        """
        pattern = r'^ge10-(\d+)/(\d+)/(\d+)$'
        match = re.match(pattern, interface)
        if match:
            return {
                'interface_type': InterfaceType.TRANSPORT_10GE,
                'slot': int(match.group(1)),
                'module': int(match.group(2)),
                'port': int(match.group(3))
            }
        return None
    
    def parse_100ge_interface(self, interface: str) -> Optional[Dict]:
        """
        Parse 100GE interface (ge100-0/0/X).
        
        Args:
            interface: Interface name to parse
            
        Returns:
            Dictionary with interface details or None if invalid
        """
        pattern = r'^ge100-(\d+)/(\d+)/(\d+)$'
        match = re.match(pattern, interface)
        if match:
            return {
                'interface_type': InterfaceType.TRANSPORT_100GE,
                'slot': int(match.group(1)),
                'module': int(match.group(2)),
                'port': int(match.group(3))
            }
        return None
    
    def validate_topology_constraints(self, source_type: DeviceType, dest_type: DeviceType) -> bool:
        """
        Validate topology constraints for Superspine support.
        
        Args:
            source_type: Source device type
            dest_type: Destination device type
            
        Returns:
            True if topology is valid, False otherwise
        """
        # Constraint: Superspine only as destination
        if source_type == DeviceType.SUPERSPINE:
            return False
        
        # Constraint: No Superspine → Superspine
        if source_type == DeviceType.SUPERSPINE and dest_type == DeviceType.SUPERSPINE:
            return False
        
        return True
    
    def get_interface_type(self, interface: str) -> InterfaceType:
        """
        Determine interface type from interface name.
        
        Args:
            interface: Interface name
            
        Returns:
            InterfaceType enum value
        """
        # Check 10GE transport
        if self.parse_10ge_interface(interface):
            return InterfaceType.TRANSPORT_10GE
        
        # Check 100GE transport
        if self.parse_100ge_interface(interface):
            return InterfaceType.TRANSPORT_100GE
        
        # Check access interfaces (ge1-0/0/X)
        if re.match(r'^ge\d+-\d+/\d+/\d+$', interface):
            return InterfaceType.ACCESS
        
        # Check bundles
        if re.match(r'^bundle-\d+$', interface):
            return InterfaceType.TRANSPORT_100GE  # Bundles are typically high-speed
        
        return InterfaceType.UNKNOWN
    
    def get_device_type_icon(self, device_type: DeviceType) -> str:
        """
        Get icon for device type display.
        
        Args:
            device_type: Device type
            
        Returns:
            Icon string for display
        """
        icons = {
            DeviceType.LEAF: "🌿",
            DeviceType.SPINE: "🌲",
            DeviceType.SUPERSPINE: "🌐",
            DeviceType.UNKNOWN: "❓"
        }
        return icons.get(device_type, "❓")
    
    def get_interface_type_description(self, interface_type: InterfaceType) -> str:
        """
        Get human-readable description for interface type.
        
        Args:
            interface_type: Interface type
            
        Returns:
            Description string
        """
        descriptions = {
            InterfaceType.ACCESS: "Access Interface",
            InterfaceType.TRANSPORT_10GE: "10GE Transport Interface",
            InterfaceType.TRANSPORT_100GE: "100GE Transport Interface",
            InterfaceType.UNKNOWN: "Unknown Interface Type"
        }
        return descriptions.get(interface_type, "Unknown Interface Type")

# Global instance for easy access
enhanced_classifier = EnhancedDeviceClassifier() 