#!/usr/bin/env python3
"""
Consolidation Engine Component

SINGLE RESPONSIBILITY: Consolidate bridge domains by global identifier

INPUT: Bridge domains with global identifiers
OUTPUT: Consolidated bridge domain groups
DEPENDENCIES: GlobalIdentifierExtractor
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.components.global_identifier_extractor import GlobalIdentifierExtractor, GlobalIdentifierResult, ConsolidationScope
from config_engine.components.bridge_domain_detector import BridgeDomainInstance
from config_engine.components.interface_role_analyzer import InterfaceInfo

logger = logging.getLogger(__name__)

@dataclass
class ConsolidationInfo:
    """Consolidation tracking information"""
    consolidation_type: str
    global_identifier: str
    source_bridge_domains: List[str]
    consolidation_key: str
    consolidated_count: int

@dataclass
class ConsolidatedBridgeDomain:
    """Consolidated bridge domain result"""
    consolidated_name: str
    global_identifier: Optional[str]
    consolidation_scope: ConsolidationScope
    source_bridge_domains: List[BridgeDomainInstance]
    devices: List[str]
    interfaces: List[InterfaceInfo]
    consolidation_info: Optional[ConsolidationInfo] = None
    confidence: float = 1.0

class ConsolidationEngine:
    """
    Consolidation Engine Component
    
    SINGLE RESPONSIBILITY: Consolidate bridge domains by global identifier
    """
    
    def __init__(self):
        self.global_identifier_extractor = GlobalIdentifierExtractor()
    
    def consolidate_bridge_domains(self, bridge_domains: List[BridgeDomainInstance], 
                                 enhanced_interfaces: Dict[str, List[InterfaceInfo]]) -> List[ConsolidatedBridgeDomain]:
        """
        Consolidate bridge domains by global identifier
        
        Args:
            bridge_domains: List of bridge domain instances
            enhanced_interfaces: Dictionary mapping BD names to interface lists
            
        Returns:
            List of consolidated bridge domains
        """
        logger.info(f"🔄 Starting consolidation of {len(bridge_domains)} bridge domains...")
        
        # Step 1: Extract global identifiers for all bridge domains
        bd_with_identifiers = []
        for bd in bridge_domains:
            try:
                global_id_result = self.global_identifier_extractor.extract_global_identifier(bd)
                bd_with_identifiers.append((bd, global_id_result))
            except Exception as e:
                logger.error(f"Failed to extract global identifier for {bd.name}: {e}")
                continue
        
        # Step 2: Group bridge domains by consolidation capability
        global_groups = defaultdict(list)
        local_bds = []
        local_deployment_bds = []
        
        for bd, global_id_result in bd_with_identifiers:
            if global_id_result.consolidation_scope == ConsolidationScope.GLOBAL_DEPLOYMENT:
                # Can be consolidated globally
                consolidation_key = self._create_consolidation_key(bd, global_id_result)
                global_groups[consolidation_key].append((bd, global_id_result))
            elif global_id_result.consolidation_scope == ConsolidationScope.LOCAL_DEPLOYMENT:
                # Global capable but locally deployed
                local_deployment_bds.append((bd, global_id_result))
            else:
                # Local only
                local_bds.append((bd, global_id_result))
        
        # Step 3: Create consolidated bridge domains
        consolidated_results = []
        
        # Process global consolidation groups
        for consolidation_key, bd_group in global_groups.items():
            if len(bd_group) > 1:
                # Multiple BDs with same key - consolidate
                consolidated_bd = self._merge_bridge_domain_group(bd_group, enhanced_interfaces)
                consolidated_results.append(consolidated_bd)
                logger.info(f"✅ Consolidated {len(bd_group)} bridge domains with key: {consolidation_key}")
            else:
                # Single BD with global identifier - keep as is
                bd, global_id_result = bd_group[0]
                consolidated_bd = self._create_single_bd_result(bd, global_id_result, enhanced_interfaces)
                consolidated_results.append(consolidated_bd)
        
        # Process local deployment BDs (global capable but locally deployed)
        for bd, global_id_result in local_deployment_bds:
            consolidated_bd = self._create_single_bd_result(bd, global_id_result, enhanced_interfaces)
            consolidated_results.append(consolidated_bd)
        
        # Process local BDs (no consolidation)
        for bd, global_id_result in local_bds:
            consolidated_bd = self._create_single_bd_result(bd, global_id_result, enhanced_interfaces)
            consolidated_results.append(consolidated_bd)
        
        logger.info(f"🔄 Consolidation complete: {len(consolidated_results)} final bridge domains")
        return consolidated_results
    
    def validate_consolidation_safety(self, bd_group: List[BridgeDomainInstance]) -> bool:
        """
        Validate that consolidation is safe and correct
        
        Args:
            bd_group: List of bridge domains to consolidate
            
        Returns:
            True if consolidation is safe
        """
        if len(bd_group) <= 1:
            return True
        
        # Check that all bridge domains have same global identifier
        global_identifiers = set()
        usernames = set()
        
        for bd in bd_group:
            global_id_result = self.global_identifier_extractor.extract_global_identifier(bd)
            if global_id_result.global_identifier:
                global_identifiers.add(global_id_result.global_identifier)
            
            username = self.global_identifier_extractor.extract_username(bd.name)
            if username:
                usernames.add(username)
        
        # Safety checks
        if len(global_identifiers) > 1:
            logger.error(f"❌ Unsafe consolidation: Multiple global identifiers {global_identifiers}")
            return False
        
        if len(usernames) > 1:
            logger.error(f"❌ Unsafe consolidation: Multiple usernames {usernames}")
            return False
        
        return True
    
    def _create_consolidation_key(self, bridge_domain: BridgeDomainInstance, 
                                global_id_result: GlobalIdentifierResult) -> str:
        """Create consolidation key for grouping"""
        
        username = self.global_identifier_extractor.extract_username(bridge_domain.name)
        global_id = global_id_result.global_identifier
        
        if username and global_id:
            return f"{username}_{global_id}"
        elif global_id:
            return f"unknown_{global_id}"
        else:
            return f"local_{bridge_domain.name}"
    
    def _merge_bridge_domain_group(self, bd_group: List[tuple], 
                                 enhanced_interfaces: Dict[str, List[InterfaceInfo]]) -> ConsolidatedBridgeDomain:
        """Merge multiple bridge domains into one consolidated domain"""
        
        bridge_domains = [bd for bd, _ in bd_group]
        global_id_results = [result for _, result in bd_group]
        
        # Validate consolidation safety
        if not self.validate_consolidation_safety(bridge_domains):
            raise ValueError(f"Unsafe consolidation attempted for bridge domains: {[bd.name for bd in bridge_domains]}")
        
        # Create consolidated name
        first_bd = bridge_domains[0]
        username = self.global_identifier_extractor.extract_username(first_bd.name)
        global_id = global_id_results[0].global_identifier
        
        if username and global_id:
            consolidated_name = f"{username}_v{global_id}_consolidated"
        else:
            consolidated_name = f"consolidated_{first_bd.name}"
        
        # Merge devices and interfaces
        all_devices = set()
        all_interfaces = []
        
        for bd in bridge_domains:
            all_devices.update(bd.devices)
            if bd.name in enhanced_interfaces:
                all_interfaces.extend(enhanced_interfaces[bd.name])
        
        # Create consolidation info
        consolidation_info = ConsolidationInfo(
            consolidation_type="global_consolidation",
            global_identifier=global_id,
            source_bridge_domains=[bd.name for bd in bridge_domains],
            consolidation_key=self._create_consolidation_key(first_bd, global_id_results[0]),
            consolidated_count=len(bridge_domains)
        )
        
        # Create consolidated bridge domain
        consolidated_bd = ConsolidatedBridgeDomain(
            consolidated_name=consolidated_name,
            global_identifier=global_id,
            consolidation_scope=global_id_results[0].consolidation_scope,
            source_bridge_domains=bridge_domains,
            devices=list(all_devices),
            interfaces=all_interfaces,
            consolidation_info=consolidation_info,
            confidence=min(result.confidence for result in global_id_results)
        )
        
        return consolidated_bd
    
    def _create_single_bd_result(self, bridge_domain: BridgeDomainInstance, 
                               global_id_result: GlobalIdentifierResult,
                               enhanced_interfaces: Dict[str, List[InterfaceInfo]]) -> ConsolidatedBridgeDomain:
        """Create consolidated result for single bridge domain (no merging)"""
        
        interfaces = enhanced_interfaces.get(bridge_domain.name, [])
        
        consolidated_bd = ConsolidatedBridgeDomain(
            consolidated_name=bridge_domain.name,
            global_identifier=global_id_result.global_identifier,
            consolidation_scope=global_id_result.consolidation_scope,
            source_bridge_domains=[bridge_domain],
            devices=bridge_domain.devices,
            interfaces=interfaces,
            consolidation_info=None,  # No consolidation needed
            confidence=global_id_result.confidence
        )
        
        return consolidated_bd
