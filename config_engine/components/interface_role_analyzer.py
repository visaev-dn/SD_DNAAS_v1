#!/usr/bin/env python3
"""
Interface Role Analyzer Component

SINGLE RESPONSIBILITY: Determine interface roles using multiple data sources

INPUT: Interface info, LLDP data, device types
OUTPUT: Interface role assignments
DEPENDENCIES: DeviceTypeClassifier, LLDPAnalyzer
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.phase1_data_structures.enums import DeviceType, InterfaceRole, InterfaceType
from config_engine.components.device_type_classifier import DeviceClassification
from config_engine.components.lldp_analyzer import NeighborInfo, LLDPDataMissingError, InvalidTopologyError

logger = logging.getLogger(__name__)

@dataclass
class InterfaceInfo:
    """Enhanced interface information with role assignment"""
    name: str
    device_name: str
    interface_type: InterfaceType
    interface_role: InterfaceRole
    vlan_id: Optional[int] = None
    neighbor_info: Optional[NeighborInfo] = None
    role_confidence: float = 1.0
    role_assignment_method: str = "unknown"

class InterfaceRoleAnalyzer:
    """
    Interface Role Analyzer Component
    
    SINGLE RESPONSIBILITY: Determine interface roles using multiple data sources
    """
    
    def __init__(self):
        pass
    
    def determine_interface_role(self, interface_name: str, device_type: DeviceType, 
                               neighbor_info: Optional[NeighborInfo] = None) -> Tuple[InterfaceRole, float, str]:
        """
        Determine interface role using LLDP and pattern analysis
        
        Args:
            interface_name: Name of the interface
            device_type: Type of the source device
            neighbor_info: LLDP neighbor information (optional)
            
        Returns:
            Tuple of (interface_role, confidence, assignment_method)
        """
        logger.debug(f"🔍 Determining role for {interface_name} on {device_type.value}")
        
        # Bundle interfaces: Use legacy pattern-based logic (reliable)
        if 'bundle-' in interface_name.lower():
            return self._determine_bundle_interface_role_legacy(interface_name, device_type)
        
        # Physical interfaces: Use LLDP neighbor analysis if available
        if neighbor_info:
            return self._determine_physical_interface_role_lldp(interface_name, device_type, neighbor_info)
        else:
            # No LLDP data - use pattern-based fallback
            return self._determine_physical_interface_role_pattern(interface_name, device_type)
    
    def assign_roles_for_bridge_domain(self, bridge_domain_name: str, interfaces: List[str], 
                                     device_types: Dict[str, DeviceClassification],
                                     neighbor_maps: Dict[str, Dict[str, NeighborInfo]]) -> List[InterfaceInfo]:
        """
        Assign roles for all interfaces in a bridge domain
        
        Args:
            bridge_domain_name: Name of the bridge domain
            interfaces: List of interface names
            device_types: Device type classifications
            neighbor_maps: LLDP neighbor maps for all devices
            
        Returns:
            List of InterfaceInfo objects with assigned roles
        """
        logger.info(f"🎯 Assigning interface roles for {bridge_domain_name}...")
        
        enhanced_interfaces = []
        
        for interface_name in interfaces:
            try:
                # Extract device name from interface (assuming format device_name:interface_name)
                if ':' in interface_name:
                    device_name, actual_interface = interface_name.split(':', 1)
                else:
                    # Try to infer device from neighbor maps
                    device_name = self._find_device_for_interface(interface_name, neighbor_maps)
                    actual_interface = interface_name
                
                if not device_name or device_name not in device_types:
                    logger.warning(f"⚠️ Cannot determine device for interface {interface_name}")
                    continue
                
                device_type = device_types[device_name].device_type
                neighbor_info = neighbor_maps.get(device_name, {}).get(actual_interface)
                
                # Determine interface role
                interface_role, confidence, method = self.determine_interface_role(
                    actual_interface, device_type, neighbor_info
                )
                
                # Determine interface type
                interface_type = self._determine_interface_type(actual_interface)
                
                # Create enhanced interface info
                enhanced_interface = InterfaceInfo(
                    name=actual_interface,
                    device_name=device_name,
                    interface_type=interface_type,
                    interface_role=interface_role,
                    neighbor_info=neighbor_info,
                    role_confidence=confidence,
                    role_assignment_method=method
                )
                
                enhanced_interfaces.append(enhanced_interface)
                logger.debug(f"✅ Assigned role {interface_role.value} to {actual_interface}")
                
            except Exception as e:
                logger.error(f"❌ Failed to assign role for interface {interface_name}: {e}")
                continue
        
        logger.info(f"🎯 Interface role assignment complete: {len(enhanced_interfaces)} interfaces processed")
        return enhanced_interfaces
    
    def _determine_bundle_interface_role_legacy(self, interface_name: str, device_type: DeviceType) -> Tuple[InterfaceRole, float, str]:
        """
        Determine bundle interface role using legacy pattern-based logic
        
        This is reliable because bundle interfaces have predictable roles based on device type
        """
        if device_type == DeviceType.LEAF:
            return InterfaceRole.UPLINK, 0.95, "legacy_pattern_bundle_leaf"
        elif device_type == DeviceType.SPINE:
            return InterfaceRole.DOWNLINK, 0.95, "legacy_pattern_bundle_spine"
        elif device_type == DeviceType.SUPERSPINE:
            return InterfaceRole.DOWNLINK, 0.95, "legacy_pattern_bundle_superspine"
        else:
            return InterfaceRole.ACCESS, 0.7, "legacy_pattern_bundle_unknown"
    
    def _determine_physical_interface_role_lldp(self, interface_name: str, device_type: DeviceType, 
                                              neighbor_info: NeighborInfo) -> Tuple[InterfaceRole, float, str]:
        """
        Determine physical interface role using LLDP neighbor analysis
        """
        # Check for corrupted LLDP data
        if neighbor_info.neighbor_device == '|':
            raise LLDPDataMissingError(f"Corrupted LLDP data for {interface_name}")
        
        neighbor_device_type = neighbor_info.neighbor_device_type
        
        if not neighbor_device_type:
            # Unknown neighbor device type - default to access
            return InterfaceRole.ACCESS, 0.6, "lldp_unknown_neighbor"
        
        # Role assignment matrix based on device types
        if device_type == DeviceType.LEAF:
            if neighbor_device_type == DeviceType.SPINE:
                return InterfaceRole.UPLINK, 1.0, "lldp_leaf_to_spine"
            elif neighbor_device_type == DeviceType.SUPERSPINE:
                return InterfaceRole.UPLINK, 1.0, "lldp_leaf_to_superspine"
            elif neighbor_device_type == DeviceType.LEAF:
                raise InvalidTopologyError(f"LEAF → LEAF connection detected: {device_type.value} → {neighbor_info.neighbor_device}")
            else:
                return InterfaceRole.ACCESS, 0.8, "lldp_leaf_to_unknown"
        
        elif device_type == DeviceType.SPINE:
            if neighbor_device_type == DeviceType.LEAF:
                return InterfaceRole.DOWNLINK, 1.0, "lldp_spine_to_leaf"
            elif neighbor_device_type == DeviceType.SPINE:
                return InterfaceRole.TRANSPORT, 1.0, "lldp_spine_to_spine"
            elif neighbor_device_type == DeviceType.SUPERSPINE:
                return InterfaceRole.UPLINK, 1.0, "lldp_spine_to_superspine"
            else:
                return InterfaceRole.ACCESS, 0.8, "lldp_spine_to_unknown"
        
        elif device_type == DeviceType.SUPERSPINE:
            if neighbor_device_type == DeviceType.SPINE:
                return InterfaceRole.DOWNLINK, 1.0, "lldp_superspine_to_spine"
            elif neighbor_device_type == DeviceType.SUPERSPINE:
                return InterfaceRole.TRANSPORT, 1.0, "lldp_superspine_to_superspine"
            elif neighbor_device_type == DeviceType.LEAF:
                return InterfaceRole.DOWNLINK, 1.0, "lldp_superspine_to_leaf"
            else:
                return InterfaceRole.ACCESS, 0.8, "lldp_superspine_to_unknown"
        
        # Default fallback
        return InterfaceRole.ACCESS, 0.5, "lldp_unknown_device_type"
    
    def _determine_physical_interface_role_pattern(self, interface_name: str, device_type: DeviceType) -> Tuple[InterfaceRole, float, str]:
        """
        Determine physical interface role using pattern-based logic (fallback)
        """
        # Physical interfaces are typically access (customer-facing)
        if 'ge' in interface_name.lower() or 'et' in interface_name.lower():
            return InterfaceRole.ACCESS, 0.8, "pattern_physical_access"
        
        # Default based on device type
        if device_type == DeviceType.LEAF:
            return InterfaceRole.ACCESS, 0.7, "pattern_leaf_default"
        else:
            return InterfaceRole.UPLINK, 0.7, "pattern_non_leaf_default"
    
    def _determine_interface_type(self, interface_name: str) -> InterfaceType:
        """Determine interface type from interface name"""
        
        if 'bundle-' in interface_name.lower():
            return InterfaceType.BUNDLE
        elif '.' in interface_name:
            return InterfaceType.SUBINTERFACE
        else:
            return InterfaceType.PHYSICAL
    
    def _find_device_for_interface(self, interface_name: str, neighbor_maps: Dict[str, Dict[str, NeighborInfo]]) -> Optional[str]:
        """Find which device owns an interface by searching neighbor maps"""
        
        for device_name, neighbor_map in neighbor_maps.items():
            if interface_name in neighbor_map:
                return device_name
        
        return None
