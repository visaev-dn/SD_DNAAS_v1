#!/usr/bin/env python3
"""
LLDP Analyzer Component

SINGLE RESPONSIBILITY: Load and analyze LLDP neighbor data

INPUT: LLDP YAML files
OUTPUT: Neighbor mappings and connectivity information
DEPENDENCIES: None (pure data analysis)
"""

import os
import sys
import yaml
import glob
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.phase1_data_structures.enums import DeviceType

logger = logging.getLogger(__name__)

# Custom exceptions
class LLDPDataMissingError(Exception):
    """Raised when LLDP data is missing for interface role assignment"""
    pass

class InvalidTopologyError(Exception):
    """Raised when invalid topology connections are detected (e.g., LEAF → LEAF)"""
    pass

@dataclass
class NeighborInfo:
    """LLDP neighbor information"""
    local_interface: str
    neighbor_device: str
    neighbor_interface: str
    neighbor_ip: str
    neighbor_device_type: Optional[DeviceType] = None

@dataclass
class ValidationResult:
    """LLDP validation result"""
    device_name: str
    total_interfaces: int
    validated_interfaces: int
    missing_interfaces: List[str]
    invalid_connections: List[str]
    coverage_percentage: float

class LLDPAnalyzer:
    """
    LLDP Analyzer Component
    
    SINGLE RESPONSIBILITY: Load and analyze LLDP neighbor data
    """
    
    def __init__(self):
        self.parsed_data_dir = Path('topology/configs/parsed_data')
        self._lldp_cache = {}
    
    def load_lldp_data(self, device_name: str) -> Dict[str, NeighborInfo]:
        """
        Load LLDP neighbor information from parsed data files
        
        Args:
            device_name: Name of the device to load LLDP data for
            
        Returns:
            Dictionary mapping interface names to neighbor information
            
        Raises:
            LLDPDataMissingError: If LLDP data file is not found or empty
        """
        # Check cache first
        if device_name in self._lldp_cache:
            return self._lldp_cache[device_name]
        
        try:
            # Find the LLDP parsed file for this device
            lldp_pattern = f"{self.parsed_data_dir}/{device_name}_lldp_parsed_*.yaml"
            lldp_files = glob.glob(lldp_pattern)
            
            if not lldp_files:
                raise LLDPDataMissingError(f"No LLDP data file found for device {device_name}")
            
            # Use the most recent file if multiple exist
            lldp_file = max(lldp_files, key=os.path.getctime)
            
            with open(lldp_file, 'r') as f:
                lldp_data = yaml.safe_load(f)
            
            if not lldp_data or 'neighbors' not in lldp_data:
                raise LLDPDataMissingError(f"Empty or invalid LLDP data for device {device_name}")
            
            # Convert neighbors list to interface-based dictionary
            interface_lldp_map = {}
            for neighbor in lldp_data['neighbors']:
                local_interface = neighbor.get('local_interface', '')
                if local_interface:
                    neighbor_info = NeighborInfo(
                        local_interface=local_interface,
                        neighbor_device=neighbor.get('neighbor_device', ''),
                        neighbor_interface=neighbor.get('neighbor_interface', ''),
                        neighbor_ip=neighbor.get('neighbor_ip', ''),
                        neighbor_device_type=self._detect_neighbor_device_type(neighbor.get('neighbor_device', ''))
                    )
                    interface_lldp_map[local_interface] = neighbor_info
            
            # Cache the result
            self._lldp_cache[device_name] = interface_lldp_map
            
            logger.debug(f"Loaded LLDP data for {device_name}: {len(interface_lldp_map)} interfaces")
            return interface_lldp_map
            
        except Exception as e:
            logger.error(f"Failed to load LLDP data for {device_name}: {e}")
            raise LLDPDataMissingError(f"Could not load LLDP data for {device_name}: {e}")
    
    def load_all_lldp_data(self, device_names: List[str]) -> Dict[str, Dict[str, NeighborInfo]]:
        """
        Load LLDP data for all devices
        
        Args:
            device_names: List of device names
            
        Returns:
            Dictionary mapping device names to their LLDP neighbor maps
        """
        logger.info(f"📡 Loading LLDP data for {len(device_names)} devices...")
        
        all_lldp_data = {}
        missing_devices = []
        
        for device_name in device_names:
            try:
                lldp_data = self.load_lldp_data(device_name)
                all_lldp_data[device_name] = lldp_data
            except LLDPDataMissingError as e:
                logger.warning(f"⚠️ Missing LLDP data for {device_name}: {e}")
                missing_devices.append(device_name)
                all_lldp_data[device_name] = {}
        
        if missing_devices:
            logger.warning(f"⚠️ LLDP data missing for {len(missing_devices)} devices: {missing_devices}")
        
        logger.info(f"📡 LLDP data loading complete: {len(all_lldp_data)} devices processed")
        return all_lldp_data
    
    def validate_lldp_completeness(self, device_name: str, interfaces: List[str]) -> ValidationResult:
        """
        Validate that LLDP data exists for all interfaces
        
        Args:
            device_name: Device name
            interfaces: List of interface names to validate
            
        Returns:
            ValidationResult with completeness information
        """
        try:
            lldp_data = self.load_lldp_data(device_name)
        except LLDPDataMissingError:
            return ValidationResult(
                device_name=device_name,
                total_interfaces=len(interfaces),
                validated_interfaces=0,
                missing_interfaces=interfaces,
                invalid_connections=[],
                coverage_percentage=0.0
            )
        
        missing_interfaces = []
        invalid_connections = []
        validated_count = 0
        
        for interface_name in interfaces:
            if interface_name in lldp_data:
                neighbor_info = lldp_data[interface_name]
                
                # Check for corrupted LLDP data
                if neighbor_info.neighbor_device == '|':
                    invalid_connections.append(f"{interface_name}: corrupted neighbor data")
                else:
                    validated_count += 1
            else:
                missing_interfaces.append(interface_name)
        
        coverage_percentage = (validated_count / len(interfaces)) * 100 if interfaces else 0
        
        return ValidationResult(
            device_name=device_name,
            total_interfaces=len(interfaces),
            validated_interfaces=validated_count,
            missing_interfaces=missing_interfaces,
            invalid_connections=invalid_connections,
            coverage_percentage=coverage_percentage
        )
    
    def detect_invalid_connections(self, neighbor_map: Dict[str, NeighborInfo]) -> List[str]:
        """
        Detect invalid topology connections (e.g., LEAF → LEAF)
        
        Args:
            neighbor_map: Dictionary of interface to neighbor mappings
            
        Returns:
            List of invalid connection descriptions
        """
        invalid_connections = []
        
        for interface_name, neighbor_info in neighbor_map.items():
            # Check for LEAF → LEAF connections (invalid in lab topology)
            if (neighbor_info.neighbor_device_type == DeviceType.LEAF and 
                self._is_leaf_device(neighbor_info.neighbor_device)):
                
                invalid_connections.append(
                    f"LEAF → LEAF connection: {interface_name} → {neighbor_info.neighbor_device}"
                )
        
        return invalid_connections
    
    def get_neighbor_info(self, device_name: str, interface_name: str) -> Optional[NeighborInfo]:
        """
        Get neighbor information for specific interface
        
        Args:
            device_name: Device name
            interface_name: Interface name
            
        Returns:
            NeighborInfo if available, None otherwise
        """
        try:
            lldp_data = self.load_lldp_data(device_name)
            return lldp_data.get(interface_name)
        except LLDPDataMissingError:
            return None
    
    def _detect_neighbor_device_type(self, neighbor_device: str) -> Optional[DeviceType]:
        """Detect device type of neighbor device"""
        
        if not neighbor_device or neighbor_device == '|':
            return None
        
        neighbor_lower = neighbor_device.lower()
        
        if 'leaf' in neighbor_lower:
            return DeviceType.LEAF
        elif 'superspine' in neighbor_lower:
            return DeviceType.SUPERSPINE
        elif 'spine' in neighbor_lower:
            return DeviceType.SPINE
        
        return None
    
    def _is_leaf_device(self, device_name: str) -> bool:
        """Check if device is a LEAF device"""
        return 'LEAF' in device_name.upper()
    
    def alert_admin_missing_lldp(self, validation_results: List[ValidationResult]) -> None:
        """
        Alert admin about missing LLDP data
        
        Args:
            validation_results: List of validation results with missing data
        """
        missing_devices = [result for result in validation_results if result.missing_interfaces]
        
        if not missing_devices:
            return
        
        alert_message = f"""
🚨 LLDP DATA MISSING - ADMIN ACTION REQUIRED

The following interfaces are missing LLDP data and will be SKIPPED:

"""
        for result in missing_devices:
            alert_message += f"Device: {result.device_name} (Coverage: {result.coverage_percentage:.1f}%)\n"
            for interface in result.missing_interfaces:
                alert_message += f"  - {interface}\n"
        
        alert_message += """
ACTION REQUIRED:
1. Check LLDP configuration on affected devices
2. Verify LLDP is enabled on interfaces
3. Re-run discovery after fixing LLDP issues

NO FALLBACK LOGIC - All interfaces must have LLDP data for proper role assignment.
"""
        
        logger.critical(alert_message)
        # Could also send email/notification to admin
