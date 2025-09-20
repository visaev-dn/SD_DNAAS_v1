#!/usr/bin/env python3
"""
Database Populator Component

SINGLE RESPONSIBILITY: Populate database with discovered topology

INPUT: Consolidated bridge domains with paths
OUTPUT: Database persistence results
DEPENDENCIES: None (pure persistence)
"""

import os
import sys
import logging
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.phase1_data_structures.topology_data import TopologyData
from config_engine.phase1_data_structures.device_info import DeviceInfo
from config_engine.phase1_data_structures.interface_info import InterfaceInfo as DBInterfaceInfo
from config_engine.phase1_data_structures.bridge_domain_config import BridgeDomainConfig
from config_engine.phase1_data_structures.enums import TopologyType, DeviceRole, BridgeDomainType
from config_engine.components.consolidation_engine import ConsolidatedBridgeDomain
from config_engine.components.interface_role_analyzer import InterfaceInfo

logger = logging.getLogger(__name__)

@dataclass
class SaveResult:
    """Database save result"""
    success: bool
    topology_data_id: Optional[int]
    devices_saved: int
    interfaces_saved: int
    paths_saved: int
    errors: List[str]
    warnings: List[str]

class DatabasePopulator:
    """
    Database Populator Component
    
    SINGLE RESPONSIBILITY: Populate database with discovered topology
    """
    
    def __init__(self):
        # Import database manager
        from config_engine.phase1_database.manager import Phase1DatabaseManager
        self.db_manager = Phase1DatabaseManager()
    
    def save_bridge_domains(self, consolidated_bridge_domains: List[ConsolidatedBridgeDomain]) -> List[SaveResult]:
        """
        Save consolidated bridge domains to database
        
        Args:
            consolidated_bridge_domains: List of consolidated bridge domains
            
        Returns:
            List of SaveResult objects with save status
        """
        logger.info(f"💾 Saving {len(consolidated_bridge_domains)} bridge domains to database...")
        
        save_results = []
        
        for bd in consolidated_bridge_domains:
            try:
                # Convert to TopologyData object
                topology_data = self._convert_to_topology_data(bd)
                
                # Validate before saving
                validation_errors = self._validate_topology_data(topology_data)
                if validation_errors:
                    logger.error(f"❌ Validation failed for {bd.consolidated_name}: {validation_errors}")
                    save_results.append(SaveResult(
                        success=False,
                        topology_data_id=None,
                        devices_saved=0,
                        interfaces_saved=0,
                        paths_saved=0,
                        errors=validation_errors,
                        warnings=[]
                    ))
                    continue
                
                # Save to database
                topology_id = self.db_manager.upsert_topology_data(topology_data)
                
                save_result = SaveResult(
                    success=True,
                    topology_data_id=topology_id,
                    devices_saved=len(topology_data.devices),
                    interfaces_saved=len(topology_data.interfaces),
                    paths_saved=len(topology_data.paths),
                    errors=[],
                    warnings=[]
                )
                
                save_results.append(save_result)
                logger.debug(f"✅ Saved {bd.consolidated_name} to database (ID: {topology_id})")
                
            except Exception as e:
                logger.error(f"❌ Failed to save {bd.consolidated_name}: {e}")
                save_results.append(SaveResult(
                    success=False,
                    topology_data_id=None,
                    devices_saved=0,
                    interfaces_saved=0,
                    paths_saved=0,
                    errors=[str(e)],
                    warnings=[]
                ))
        
        # Log summary
        successful_saves = sum(1 for result in save_results if result.success)
        logger.info(f"💾 Database save complete: {successful_saves}/{len(save_results)} successful")
        
        return save_results
    
    def prevent_interface_duplication(self, interfaces: List[InterfaceInfo]) -> List[InterfaceInfo]:
        """
        Ensure no interface duplication during save
        
        Args:
            interfaces: List of interfaces to deduplicate
            
        Returns:
            List of unique interfaces
        """
        seen_interfaces: Set[str] = set()
        unique_interfaces = []
        
        for interface in interfaces:
            interface_key = f"{interface.device_name}:{interface.name}"
            
            if interface_key not in seen_interfaces:
                unique_interfaces.append(interface)
                seen_interfaces.add(interface_key)
            else:
                logger.debug(f"Skipping duplicate interface: {interface_key}")
        
        logger.debug(f"Deduplicated interfaces: {len(interfaces)} → {len(unique_interfaces)}")
        return unique_interfaces
    
    def _convert_to_topology_data(self, consolidated_bd: ConsolidatedBridgeDomain) -> TopologyData:
        """Convert consolidated bridge domain to TopologyData object"""
        
        # Create DeviceInfo objects
        devices = []
        for i, device_name in enumerate(consolidated_bd.devices):
            device_role = DeviceRole.SOURCE if i == 0 else DeviceRole.DESTINATION
            
            device_info = DeviceInfo(
                name=device_name,
                device_type=self._detect_device_type(device_name),
                device_role=device_role,
                confidence_score=0.9
            )
            devices.append(device_info)
        
        # Convert and deduplicate interfaces
        unique_interfaces = self.prevent_interface_duplication(consolidated_bd.interfaces)
        
        # Create database InterfaceInfo objects
        db_interfaces = []
        for interface in unique_interfaces:
            db_interface = DBInterfaceInfo(
                name=interface.name,
                device_name=interface.device_name,
                interface_type=interface.interface_type,
                interface_role=interface.interface_role,
                vlan_id=interface.vlan_id,
                confidence_score=interface.role_confidence,
                description=f"Role: {interface.interface_role.value}, Method: {interface.role_assignment_method}"
            )
            db_interfaces.append(db_interface)
        
        # Create BridgeDomainConfig
        primary_vlan = self._extract_primary_vlan(consolidated_bd)
        
        bridge_domain_config = BridgeDomainConfig(
            service_name=consolidated_bd.consolidated_name,
            bridge_domain_type=self._determine_bridge_domain_type(consolidated_bd),
            source_device=devices[0].name if devices else None,
            source_interface=db_interfaces[0].name if db_interfaces else None,
            destinations=[],  # Will be populated from devices
            vlan_id=primary_vlan
        )
        
        # Determine topology type
        topology_type = TopologyType.P2MP if len(devices) > 1 else TopologyType.P2P
        
        # Create TopologyData object
        topology_data = TopologyData(
            bridge_domain_name=consolidated_bd.consolidated_name,
            topology_type=topology_type,
            vlan_id=primary_vlan,
            devices=devices,
            interfaces=db_interfaces,
            paths=[],  # Paths will be generated separately if needed
            bridge_domain_config=bridge_domain_config,
            discovered_at=datetime.now(),
            scan_method='enhanced_discovery_refactored',
            confidence_score=consolidated_bd.confidence
        )
        
        return topology_data
    
    def _validate_topology_data(self, topology_data: TopologyData) -> List[str]:
        """Validate topology data before database save"""
        
        validation_errors = []
        
        # Check for required fields
        if not topology_data.bridge_domain_name:
            validation_errors.append("Missing bridge domain name")
        
        if not topology_data.devices:
            validation_errors.append("No devices in topology")
        
        if not topology_data.interfaces:
            validation_errors.append("No interfaces in topology")
        
        # Check for interface-device ownership consistency
        device_names = {device.name for device in topology_data.devices}
        for interface in topology_data.interfaces:
            if interface.device_name not in device_names:
                validation_errors.append(f"Interface {interface.name} assigned to unknown device {interface.device_name}")
        
        # Check for duplicate interfaces
        interface_keys = []
        for interface in topology_data.interfaces:
            interface_key = f"{interface.device_name}:{interface.name}"
            if interface_key in interface_keys:
                validation_errors.append(f"Duplicate interface detected: {interface_key}")
            interface_keys.append(interface_key)
        
        return validation_errors
    
    def _detect_device_type(self, device_name: str):
        """Detect device type from name (simple pattern matching)"""
        from config_engine.components.device_type_classifier import DeviceTypeClassifier
        classifier = DeviceTypeClassifier()
        classification = classifier.classify_device_type(device_name)
        return classification.device_type
    
    def _extract_primary_vlan(self, consolidated_bd: ConsolidatedBridgeDomain) -> Optional[int]:
        """Extract primary VLAN ID from consolidated bridge domain"""
        
        # Use global identifier if it's a VLAN ID
        if consolidated_bd.global_identifier and consolidated_bd.global_identifier.isdigit():
            return int(consolidated_bd.global_identifier)
        
        # Look through interfaces for VLAN ID
        for interface in consolidated_bd.interfaces:
            if interface.vlan_id:
                return interface.vlan_id
        
        return None
    
    def _determine_bridge_domain_type(self, consolidated_bd: ConsolidatedBridgeDomain) -> BridgeDomainType:
        """Determine bridge domain type from consolidated data"""
        
        # Use the type from the first source bridge domain
        if consolidated_bd.source_bridge_domains:
            return consolidated_bd.source_bridge_domains[0].dnaas_type
        
        # Default fallback
        return BridgeDomainType.SINGLE_TAGGED
