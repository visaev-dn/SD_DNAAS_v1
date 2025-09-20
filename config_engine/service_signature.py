#!/usr/bin/env python3
"""
Service Signature Generator
Production-ready VLAN-based service identification for deduplication

This module implements the definitive service signature logic:
- VLAN ID (outer tag) as primary identifier for L2 overlay services
- Username for port-mode and local scope differentiation
- Classification-based handling for missing VLAN data
- Fail-fast approach for unclassifiable topologies
"""

import re
import logging
from typing import Optional, List, Set
from dataclasses import dataclass

from config_engine.phase1_data_structures.topology_data import TopologyData
from config_engine.phase1_data_structures.enums import BridgeDomainType, BridgeDomainScope

logger = logging.getLogger(__name__)


@dataclass
class ServiceSignatureResult:
    """Result of service signature generation"""
    signature: str
    classification: str
    confidence: float
    warning: Optional[str] = None


class ServiceSignatureGenerator:
    """
    Production-ready service signature generator based on network engineering fundamentals
    
    Core Principles:
    1. VLAN ID (outer tag) = Primary service identifier
    2. Username = Differentiation for port-mode and local scope
    3. Classification-based handling = Proper service type detection
    4. Fail-fast = Force discovery fixes for unclassifiable services
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.review_queue = []  # Topologies requiring manual review
    
    def generate_signature(self, topology_data: TopologyData) -> ServiceSignatureResult:
        """
        Generate service signature for topology data
        
        Args:
            topology_data: TopologyData object to generate signature for
            
        Returns:
            ServiceSignatureResult with signature and metadata
            
        Raises:
            ValueError: When topology cannot be classified or lacks required data
        """
        try:
            # Step 1: Classify bridge domain type
            bd_type = self._classify_bridge_domain_type(topology_data)
            
            # Step 2: Generate signature based on type
            if bd_type == BridgeDomainType.PORT_MODE:
                return self._generate_port_mode_signature(topology_data)
            
            elif bd_type in [BridgeDomainType.SINGLE_TAGGED, BridgeDomainType.QINQ, 
                           BridgeDomainType.DOUBLE_TAGGED]:
                return self._generate_vlan_based_signature(topology_data, bd_type)
            
            elif bd_type in [BridgeDomainType.VLAN_LIST, BridgeDomainType.VLAN_RANGE]:
                return self._generate_multi_vlan_signature(topology_data, bd_type)
            
            else:
                # Unclassifiable topology - fail for review
                self._queue_for_review(topology_data, f"Unclassifiable bridge domain type: {bd_type}")
                raise ValueError(f"Cannot generate signature for unclassifiable topology: {topology_data.bridge_domain_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to generate signature for {topology_data.bridge_domain_name}: {e}")
            raise
    
    def _generate_port_mode_signature(self, topology_data: TopologyData) -> ServiceSignatureResult:
        """Generate signature for port-mode services (username only)"""
        username = self._extract_username(topology_data.bridge_domain_name)
        
        if not username or username == "unknown":
            self._queue_for_review(topology_data, "Cannot extract username for port-mode service")
            raise ValueError(f"Port-mode service requires valid username: {topology_data.bridge_domain_name}")
        
        signature = f"portmode_{username}"
        
        return ServiceSignatureResult(
            signature=signature,
            classification="port_mode",
            confidence=0.95,
            warning=None
        )
    
    def _generate_vlan_based_signature(self, topology_data: TopologyData, bd_type: BridgeDomainType) -> ServiceSignatureResult:
        """Generate signature for VLAN-based services"""
        
        # Extract authoritative VLAN ID
        vlan_id = self._extract_authoritative_vlan_id(topology_data, bd_type)
        
        if vlan_id is None:
            self._queue_for_review(topology_data, f"Missing VLAN configuration for {bd_type.value} service")
            raise ValueError(f"Cannot generate signature: Missing VLAN data for {topology_data.bridge_domain_name}")
        
        # Determine scope
        scope = self._detect_scope(topology_data.bridge_domain_name)
        
        if scope == BridgeDomainScope.LOCAL:
            # Local scope: Username required for differentiation
            username = self._extract_username(topology_data.bridge_domain_name)
            if not username or username == "unknown":
                self._queue_for_review(topology_data, "Cannot extract username for local scope service")
                raise ValueError(f"Local scope service requires valid username: {topology_data.bridge_domain_name}")
            
            signature = f"local_{username}_vlan_{vlan_id}"
            classification = f"local_{bd_type.value}"
        else:
            # Global scope: VLAN ID is globally unique
            signature = f"global_vlan_{vlan_id}"
            classification = f"global_{bd_type.value}"
        
        return ServiceSignatureResult(
            signature=signature,
            classification=classification,
            confidence=0.98,
            warning=None
        )
    
    def _generate_multi_vlan_signature(self, topology_data: TopologyData, bd_type: BridgeDomainType) -> ServiceSignatureResult:
        """Generate signature for multi-VLAN services (VLAN list/range)"""
        
        vlan_list = self._extract_vlan_list_or_range(topology_data)
        
        if not vlan_list:
            self._queue_for_review(topology_data, f"Missing VLAN list/range for {bd_type.value} service")
            raise ValueError(f"Cannot extract VLAN list/range for {topology_data.bridge_domain_name}")
        
        # Create deterministic VLAN signature
        sorted_vlans = sorted(vlan_list)
        vlan_signature = "_".join(map(str, sorted_vlans))
        
        # Multi-VLAN services are typically global scope
        signature = f"global_vlans_{vlan_signature}"
        
        return ServiceSignatureResult(
            signature=signature,
            classification=f"global_{bd_type.value}",
            confidence=0.90,
            warning=f"Multi-VLAN service with {len(vlan_list)} VLANs" if len(vlan_list) > 10 else None
        )
    
    def _extract_authoritative_vlan_id(self, topology_data: TopologyData, bd_type: BridgeDomainType) -> Optional[int]:
        """
        Extract VLAN ID from authoritative sources only
        
        Priority order:
        1. QinQ outer tag (for QinQ services)
        2. Bridge domain config VLAN ID
        3. Interface VLAN configuration (not subinterface names!)
        
        NEVER infer from bridge domain names or subinterface names!
        """
        
        # Priority 1: QinQ outer tag (network service identifier)
        if bd_type in [BridgeDomainType.QINQ, BridgeDomainType.DOUBLE_TAGGED]:
            if topology_data.bridge_domain_config.outer_vlan:
                outer_vlan = topology_data.bridge_domain_config.outer_vlan
                if 1 <= outer_vlan <= 4094:
                    return outer_vlan
        
        # Priority 2: Regular VLAN ID from bridge domain config
        if topology_data.vlan_id and 1 <= topology_data.vlan_id <= 4094:
            return topology_data.vlan_id
        
        if topology_data.bridge_domain_config.vlan_id and 1 <= topology_data.bridge_domain_config.vlan_id <= 4094:
            return topology_data.bridge_domain_config.vlan_id
        
        # Priority 3: Interface VLAN configuration (actual config, not subinterface names!)
        for interface in topology_data.interfaces:
            if interface.vlan_id and 1 <= interface.vlan_id <= 4094:
                # Only use if it's from actual VLAN configuration, not subinterface name parsing
                if hasattr(interface, 'source_data') and interface.source_data.get('vlan_from_config', False):
                    return interface.vlan_id
        
        # NEVER infer from names (per documentation)
        return None
    
    def _extract_vlan_list_or_range(self, topology_data: TopologyData) -> Optional[List[int]]:
        """Extract VLAN list or range from topology data"""
        
        vlan_list = []
        
        # Check bridge domain config for VLAN lists
        if hasattr(topology_data.bridge_domain_config, 'vlan_list') and topology_data.bridge_domain_config.vlan_list:
            vlan_list.extend(topology_data.bridge_domain_config.vlan_list)
        
        # Check interface configurations for VLAN ranges
        for interface in topology_data.interfaces:
            if hasattr(interface, 'vlan_range') and interface.vlan_range:
                start, end = interface.vlan_range
                vlan_list.extend(range(start, end + 1))
        
        # Remove duplicates and validate
        unique_vlans = list(set(vlan_list))
        valid_vlans = [v for v in unique_vlans if 1 <= v <= 4094]
        
        return valid_vlans if valid_vlans else None
    
    def _extract_username(self, bridge_domain_name: str) -> str:
        """
        Extract username from bridge domain name following classification rules
        
        Never infer VLAN IDs from names - only extract administrative username
        """
        if not bridge_domain_name:
            return "unknown"
        
        # Remove scope prefix (g_, l_)
        clean_name = re.sub(r'^[gl]_', '', bridge_domain_name.lower())
        
        # Extract username patterns
        patterns = [
            r'^([a-zA-Z][a-zA-Z0-9_]*?)_v\d+',     # user_v123_anything
            r'^([a-zA-Z][a-zA-Z0-9_]*?)_test',     # user_test_anything
            r'^([a-zA-Z][a-zA-Z0-9_]*?)_[^_]+_v\d+', # user_project_v123
            r'^([a-zA-Z][a-zA-Z0-9_]*?)_',         # user_anything
            r'^([a-zA-Z][a-zA-Z0-9_]*)$'           # just_user
        ]
        
        for pattern in patterns:
            match = re.match(pattern, clean_name)
            if match:
                username = match.group(1)
                # Validate username format
                if len(username) >= 2 and username.isalnum():
                    return username.lower()
        
        return "unknown"
    
    def _detect_scope(self, bridge_domain_name: str) -> BridgeDomainScope:
        """Detect bridge domain scope from naming convention"""
        if bridge_domain_name.startswith('l_'):
            return BridgeDomainScope.LOCAL
        elif bridge_domain_name.startswith('g_'):
            return BridgeDomainScope.GLOBAL
        else:
            return BridgeDomainScope.UNSPECIFIED
    
    def _classify_bridge_domain_type(self, topology_data: TopologyData) -> BridgeDomainType:
        """
        Classify bridge domain type based on configuration data
        
        Returns the detected BridgeDomainType or raises ValueError for unclassifiable
        """
        
        # Use existing bridge domain type if available and valid
        if topology_data.bridge_domain_config.bridge_domain_type:
            return topology_data.bridge_domain_config.bridge_domain_type
        
        # Classify based on configuration patterns
        has_outer_vlan = topology_data.bridge_domain_config.outer_vlan is not None
        has_inner_vlan = topology_data.bridge_domain_config.inner_vlan is not None
        has_vlan_id = topology_data.vlan_id is not None or topology_data.bridge_domain_config.vlan_id is not None
        
        if has_outer_vlan and has_inner_vlan:
            return BridgeDomainType.QINQ
        elif has_outer_vlan:
            return BridgeDomainType.DOUBLE_TAGGED
        elif has_vlan_id:
            return BridgeDomainType.SINGLE_TAGGED
        else:
            # Check for port-mode indicators
            interface_types = [i.interface_type for i in topology_data.interfaces]
            if all(itype.value == 'PHYSICAL' for itype in interface_types):
                return BridgeDomainType.PORT_MODE
            
            # Unclassifiable
            raise ValueError(f"Cannot classify bridge domain type for {topology_data.bridge_domain_name}")
    
    def _queue_for_review(self, topology_data: TopologyData, reason: str):
        """Queue topology for manual review"""
        review_item = {
            'bridge_domain_name': topology_data.bridge_domain_name,
            'reason': reason,
            'topology_id': getattr(topology_data, 'topology_id', None),
            'discovered_at': topology_data.discovered_at,
            'vlan_id': topology_data.vlan_id,
            'device_count': len(topology_data.devices),
            'interface_count': len(topology_data.interfaces)
        }
        
        self.review_queue.append(review_item)
        self.logger.warning(f"Queued for review: {topology_data.bridge_domain_name} - {reason}")
    
    def get_review_queue(self) -> List[dict]:
        """Get topologies queued for manual review"""
        return self.review_queue.copy()
    
    def clear_review_queue(self):
        """Clear the review queue"""
        self.review_queue.clear()


# Convenience functions for direct usage
def generate_service_signature(topology_data: TopologyData) -> ServiceSignatureResult:
    """Generate service signature for topology data"""
    generator = ServiceSignatureGenerator()
    return generator.generate_signature(topology_data)


def extract_username_from_bridge_domain_name(bridge_domain_name: str) -> str:
    """Extract username from bridge domain name"""
    generator = ServiceSignatureGenerator()
    return generator._extract_username(bridge_domain_name)
