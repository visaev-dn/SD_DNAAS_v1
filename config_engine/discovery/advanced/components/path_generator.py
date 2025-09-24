#!/usr/bin/env python3
"""
Path Generator Component

SINGLE RESPONSIBILITY: Generate network topology paths

INPUT: Bridge domains with interface roles and neighbor info
OUTPUT: Network topology paths
DEPENDENCIES: InterfaceRoleAnalyzer, LLDPAnalyzer
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.phase1_data_structures.enums import DeviceType, InterfaceRole
from config_engine.phase1_data_structures.path_info import PathInfo, PathSegment
from .consolidation_engine import ConsolidatedBridgeDomain
from .interface_role_analyzer import InterfaceInfo
from .lldp_analyzer import NeighborInfo

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Path validation result"""
    is_valid: bool
    validation_errors: List[str]
    validation_warnings: List[str]

class PathGenerator:
    """
    Path Generator Component
    
    SINGLE RESPONSIBILITY: Generate network topology paths
    """
    
    def __init__(self):
        pass
    
    def generate_paths_for_bridge_domain(self, bridge_domain: ConsolidatedBridgeDomain) -> List[PathInfo]:
        """
        Generate topology paths for bridge domain
        
        Args:
            bridge_domain: Consolidated bridge domain with interfaces and neighbor info
            
        Returns:
            List of PathInfo objects representing network topology
        """
        logger.debug(f"🛤️ Generating paths for {bridge_domain.consolidated_name}")
        
        # Handle single-device bridge domains (no self-loops)
        if len(bridge_domain.devices) == 1:
            logger.debug(f"Single-device bridge domain {bridge_domain.consolidated_name} - no paths generated")
            return []  # No paths for single-device BDs (fixes self-loop issue)
        
        # Generate paths for multi-device bridge domains
        paths = []
        
        # Group interfaces by device
        device_interfaces = defaultdict(list)
        for interface in bridge_domain.interfaces:
            device_interfaces[interface.device_name].append(interface)
        
        # Create paths between devices
        device_list = list(bridge_domain.devices)
        
        for i, source_device in enumerate(device_list):
            for j, dest_device in enumerate(device_list):
                if i != j:  # Don't create self-loops
                    path = self._create_path_between_devices(
                        source_device, dest_device, 
                        device_interfaces[source_device],
                        device_interfaces[dest_device]
                    )
                    if path:
                        paths.append(path)
        
        logger.debug(f"🛤️ Generated {len(paths)} paths for {bridge_domain.consolidated_name}")
        return paths
    
    def validate_path_connectivity(self, paths: List[PathInfo]) -> ValidationResult:
        """
        Validate that paths are logically consistent
        
        Args:
            paths: List of paths to validate
            
        Returns:
            ValidationResult with validation status and issues
        """
        validation_errors = []
        validation_warnings = []
        
        for path in paths:
            # Check for self-loops
            if path.source_device == path.dest_device:
                validation_errors.append(f"Self-loop detected: {path.source_device}")
            
            # Check for empty segments
            if not path.segments:
                validation_warnings.append(f"Empty path segments: {path.path_name}")
            
            # Check segment consistency
            for segment in path.segments:
                if segment.source_device == segment.dest_device:
                    validation_errors.append(f"Self-loop segment: {segment.source_device}")
        
        is_valid = len(validation_errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings
        )
    
    def _create_path_between_devices(self, source_device: str, dest_device: str,
                                   source_interfaces: List[InterfaceInfo],
                                   dest_interfaces: List[InterfaceInfo]) -> Optional[PathInfo]:
        """Create path between two devices using their interfaces"""
        
        # Find best interface pair for path creation
        source_interface = self._find_best_interface_for_path(source_interfaces, "source")
        dest_interface = self._find_best_interface_for_path(dest_interfaces, "destination")
        
        if not source_interface or not dest_interface:
            logger.debug(f"Cannot create path {source_device} → {dest_device}: missing interfaces")
            return None
        
        # Create path segment
        segment = PathSegment(
            source_device=source_device,
            dest_device=dest_device,
            source_interface=source_interface.name,
            dest_interface=dest_interface.name,
            segment_type="bridge_domain_link"
        )
        
        # Create path info
        path = PathInfo(
            path_name=f"{source_device}_to_{dest_device}",
            source_device=source_device,
            dest_device=dest_device,
            segments=[segment]
        )
        
        return path
    
    def _find_best_interface_for_path(self, interfaces: List[InterfaceInfo], direction: str) -> Optional[InterfaceInfo]:
        """Find the best interface for path creation"""
        
        if not interfaces:
            return None
        
        # Prefer uplink interfaces for source, downlink for destination
        if direction == "source":
            # Look for uplink interfaces first
            uplink_interfaces = [iface for iface in interfaces if iface.interface_role == InterfaceRole.UPLINK]
            if uplink_interfaces:
                return uplink_interfaces[0]
        elif direction == "destination":
            # Look for downlink interfaces first
            downlink_interfaces = [iface for iface in interfaces if iface.interface_role == InterfaceRole.DOWNLINK]
            if downlink_interfaces:
                return downlink_interfaces[0]
        
        # Fallback to first available interface
        return interfaces[0]
    
    def build_path_from_interface(self, device_name: str, interface: InterfaceInfo, 
                                neighbor_maps: Dict[str, Dict[str, NeighborInfo]]) -> Optional[PathInfo]:
        """
        Build path from interface using LLDP neighbor information
        
        Args:
            device_name: Source device name
            interface: Interface to start path from
            neighbor_maps: LLDP neighbor maps
            
        Returns:
            PathInfo if path can be built, None otherwise
        """
        # Get LLDP neighbor information
        neighbor_map = neighbor_maps.get(device_name, {})
        neighbor_info = neighbor_map.get(interface.name)
        
        if not neighbor_info or not neighbor_info.neighbor_device:
            logger.debug(f"No neighbor info for {device_name}:{interface.name}")
            return None
        
        # Create simple path segment
        segment = PathSegment(
            source_device=device_name,
            dest_device=neighbor_info.neighbor_device,
            source_interface=interface.name,
            dest_interface=neighbor_info.neighbor_interface,
            segment_type="lldp_link"
        )
        
        # Create path info
        path = PathInfo(
            path_name=f"{device_name}_to_{neighbor_info.neighbor_device}",
            source_device=device_name,
            dest_device=neighbor_info.neighbor_device,
            segments=[segment]
        )
        
        return path
