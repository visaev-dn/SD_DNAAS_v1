#!/usr/bin/env python3
"""
Global Identifier Extractor Component

SINGLE RESPONSIBILITY: Extract global identifiers for consolidation

INPUT: Classified bridge domains
OUTPUT: Global identifiers and scope classifications
DEPENDENCIES: None (pure extraction logic)
"""

import os
import sys
import re
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.phase1_data_structures.enums import BridgeDomainType

logger = logging.getLogger(__name__)

class ConsolidationScope(Enum):
    """Consolidation scope enumeration"""
    LOCAL = "local"                    # Local only - no cross-device consolidation
    LOCAL_DEPLOYMENT = "local_deployment"  # Global capable but locally deployed
    GLOBAL_DEPLOYMENT = "global_deployment"  # Global capable and globally deployed

@dataclass
class GlobalIdentifierResult:
    """Global identifier extraction result"""
    bridge_domain_name: str
    global_identifier: Optional[str]
    consolidation_scope: ConsolidationScope
    can_consolidate_globally: bool
    extraction_method: str
    confidence: float

class GlobalIdentifierExtractor:
    """
    Global Identifier Extractor Component
    
    SINGLE RESPONSIBILITY: Extract global identifiers for consolidation
    """
    
    def __init__(self):
        # QinQ types that use outer VLAN as global identifier
        self.QINQ_TYPES = [
            BridgeDomainType.DOUBLE_TAGGED,
            BridgeDomainType.QINQ_SINGLE_BD,
            BridgeDomainType.QINQ_MULTI_BD,
            BridgeDomainType.HYBRID
        ]
        
        # Single-tagged types that use VLAN ID as global identifier
        self.SINGLE_TAGGED_TYPES = [
            BridgeDomainType.SINGLE_TAGGED
        ]
        
        # Range/List types that may or may not have global identifiers
        self.RANGE_LIST_TYPES = [
            BridgeDomainType.SINGLE_TAGGED_RANGE,
            BridgeDomainType.SINGLE_TAGGED_LIST
        ]
    
    def extract_global_identifier(self, bridge_domain) -> GlobalIdentifierResult:
        """
        Extract global identifier based on DNAAS type
        
        Args:
            bridge_domain: Bridge domain instance with DNAAS type and VLAN config
            
        Returns:
            GlobalIdentifierResult with identifier and scope information
        """
        logger.debug(f"🔍 Extracting global identifier for {bridge_domain.name}")
        
        bd_type = bridge_domain.dnaas_type
        vlan_config = bridge_domain.vlan_config
        device_count = len(bridge_domain.devices)
        
        # QinQ Types (1, 2A, 2B, 3) - Use outer VLAN as global identifier
        if bd_type in self.QINQ_TYPES:
            if vlan_config.outer_vlan:
                global_id = str(vlan_config.outer_vlan)
                scope = self._determine_scope(global_id, device_count)
                
                return GlobalIdentifierResult(
                    bridge_domain_name=bridge_domain.name,
                    global_identifier=global_id,
                    consolidation_scope=scope,
                    can_consolidate_globally=(scope == ConsolidationScope.GLOBAL_DEPLOYMENT),
                    extraction_method="qinq_outer_vlan",
                    confidence=0.95
                )
            else:
                logger.warning(f"⚠️ QinQ bridge domain {bridge_domain.name} missing outer VLAN")
                return self._create_local_result(bridge_domain.name, "qinq_missing_outer_vlan")
        
        # Single-Tagged Type 4A - Use VLAN ID as global identifier
        elif bd_type in self.SINGLE_TAGGED_TYPES:
            if vlan_config.vlan_id:
                global_id = str(vlan_config.vlan_id)
                scope = self._determine_scope(global_id, device_count)
                
                return GlobalIdentifierResult(
                    bridge_domain_name=bridge_domain.name,
                    global_identifier=global_id,
                    consolidation_scope=scope,
                    can_consolidate_globally=(scope == ConsolidationScope.GLOBAL_DEPLOYMENT),
                    extraction_method="single_tagged_vlan_id",
                    confidence=0.90
                )
            else:
                logger.warning(f"⚠️ Single-tagged bridge domain {bridge_domain.name} missing VLAN ID")
                return self._create_local_result(bridge_domain.name, "single_tagged_missing_vlan")
        
        # Range/List Types (4B) - Use outer VLAN if QinQ, otherwise local
        elif bd_type in self.RANGE_LIST_TYPES:
            if vlan_config.outer_vlan:
                # QinQ with range/list - use outer VLAN
                global_id = str(vlan_config.outer_vlan)
                scope = self._determine_scope(global_id, device_count)
                
                return GlobalIdentifierResult(
                    bridge_domain_name=bridge_domain.name,
                    global_identifier=global_id,
                    consolidation_scope=scope,
                    can_consolidate_globally=(scope == ConsolidationScope.GLOBAL_DEPLOYMENT),
                    extraction_method="range_list_qinq_outer_vlan",
                    confidence=0.85
                )
            else:
                # Local range/list - no global identifier
                return self._create_local_result(bridge_domain.name, "range_list_local_only")
        
        # Port-Mode (Type 5) - No global identifier (local only)
        elif bd_type == BridgeDomainType.PORT_MODE:
            return self._create_local_result(bridge_domain.name, "port_mode_local_only")
        
        # Default: no global identifier
        else:
            return self._create_local_result(bridge_domain.name, "unknown_type_default")
    
    def determine_consolidation_scope(self, bridge_domain) -> ConsolidationScope:
        """
        Determine if bridge domain can be consolidated globally
        
        Args:
            bridge_domain: Bridge domain instance
            
        Returns:
            ConsolidationScope indicating consolidation capability
        """
        result = self.extract_global_identifier(bridge_domain)
        return result.consolidation_scope
    
    def _determine_scope(self, global_identifier: str, device_count: int) -> ConsolidationScope:
        """Determine consolidation scope based on global identifier and device deployment"""
        
        # Has global identifier but single device = Local deployment
        if device_count == 1:
            return ConsolidationScope.LOCAL_DEPLOYMENT
        
        # Has global identifier and multiple devices = Global deployment
        elif device_count > 1:
            return ConsolidationScope.GLOBAL_DEPLOYMENT
        
        # Default to local
        else:
            return ConsolidationScope.LOCAL
    
    def _create_local_result(self, bridge_domain_name: str, method: str) -> GlobalIdentifierResult:
        """Create a local-only result (no global identifier)"""
        
        return GlobalIdentifierResult(
            bridge_domain_name=bridge_domain_name,
            global_identifier=None,
            consolidation_scope=ConsolidationScope.LOCAL,
            can_consolidate_globally=False,
            extraction_method=method,
            confidence=0.95
        )
    
    def extract_username(self, bridge_domain_name: str) -> Optional[str]:
        """
        Extract username from bridge domain name
        
        Args:
            bridge_domain_name: Bridge domain name
            
        Returns:
            Extracted username or None
        """
        # Common patterns for username extraction
        patterns = [
            r'[lg]_([^_]+)_v\d+',  # g_username_v123 or l_username_v123
            r'([^_]+)_v\d+',       # username_v123
            r'([^_]+)_.*'          # username_anything
        ]
        
        for pattern in patterns:
            match = re.match(pattern, bridge_domain_name.lower())
            if match:
                username = match.group(1)
                logger.debug(f"Extracted username '{username}' from {bridge_domain_name}")
                return username
        
        logger.debug(f"No username pattern matched for {bridge_domain_name}")
        return None
