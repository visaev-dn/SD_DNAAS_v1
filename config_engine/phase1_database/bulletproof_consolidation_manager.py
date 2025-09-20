"""
Bulletproof Bridge Domain Consolidation Manager

This module implements a safe consolidation strategy that prevents accidental
merging of different bridge domain types by using comprehensive classification
matching.
"""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from config_engine.phase1_data_structures.topology_data import TopologyData
from config_engine.phase1_data_structures.enums import BridgeDomainScope, BridgeDomainType

logger = logging.getLogger(__name__)

@dataclass
class BridgeDomainSignature:
    """Complete signature for safe bridge domain identification"""
    username: str
    vlan_id: Optional[int]
    bridge_domain_type: BridgeDomainType
    outer_vlan: Optional[int]
    inner_vlan: Optional[int]
    scope: BridgeDomainScope
    device_count: int
    interface_count: int
    
    def to_consolidation_key(self) -> str:
        """Generate safe consolidation key"""
        parts = [
            f"user:{self.username}",
            f"vlan:{self.vlan_id}" if self.vlan_id else "vlan:none",
            f"type:{self.bridge_domain_type.value}",
            f"outer:{self.outer_vlan}" if self.outer_vlan else "outer:none", 
            f"inner:{self.inner_vlan}" if self.inner_vlan else "inner:none",
            f"scope:{self.scope.value}",
            f"dev_range:{self._get_device_range()}",
        ]
        return "|".join(parts)
    
    def _get_device_range(self) -> str:
        """Categorize device count for safer grouping"""
        if self.device_count == 1:
            return "single"
        elif self.device_count <= 3:
            return "small"
        elif self.device_count <= 10:
            return "medium"
        else:
            return "large"
    
    def is_safe_to_merge_with(self, other: 'BridgeDomainSignature') -> bool:
        """Check if two signatures can be safely merged"""
        
        # Must have same username and VLAN
        if self.username != other.username or self.vlan_id != other.vlan_id:
            return False
        
        # Must have same bridge domain type
        if self.bridge_domain_type != other.bridge_domain_type:
            return False
        
        # For QinQ types, must have same outer/inner VLANs
        if self._is_qinq_type():
            if (self.outer_vlan != other.outer_vlan or 
                self.inner_vlan != other.inner_vlan):
                return False
        
        # Must have same scope
        if self.scope != other.scope:
            return False
        
        # Device count should be similar (prevent merging P2P with P2MP)
        if abs(self.device_count - other.device_count) > 2:
            return False
        
        return True
    
    def _is_qinq_type(self) -> bool:
        """Check if this is a QinQ bridge domain type"""
        qinq_types = {
            BridgeDomainType.DOUBLE_TAGGED,
            BridgeDomainType.QINQ_SINGLE_BD, 
            BridgeDomainType.QINQ_MULTI_BD,
            BridgeDomainType.HYBRID
        }
        return self.bridge_domain_type in qinq_types

class BulletproofConsolidationManager:
    """Safe consolidation manager with comprehensive validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_safe_consolidation_candidates(self, topologies: List[TopologyData]) -> Dict[str, List[TopologyData]]:
        """Get consolidation candidates using bulletproof logic"""
        
        self.logger.info(f"Analyzing {len(topologies)} topologies for safe consolidation")
        
        # Create signatures for all topologies
        signatures = {}
        signature_groups = defaultdict(list)
        
        for topology in topologies:
            try:
                signature = self._create_signature(topology)
                signatures[topology.bridge_domain_name] = signature
                
                # Group by base key (username + vlan + type)
                base_key = f"{signature.username}_v{signature.vlan_id}_{signature.bridge_domain_type.value}"
                signature_groups[base_key].append((topology, signature))
                
            except Exception as e:
                self.logger.warning(f"Failed to create signature for {topology.bridge_domain_name}: {e}")
                continue
        
        # Find safe consolidation groups
        safe_groups = {}
        
        for base_key, topology_signature_pairs in signature_groups.items():
            if len(topology_signature_pairs) < 2:
                continue  # No duplicates
            
            # Group by exact signature match
            exact_groups = defaultdict(list)
            for topology, signature in topology_signature_pairs:
                exact_key = signature.to_consolidation_key()
                exact_groups[exact_key].append(topology)
            
            # Only include groups with multiple entries
            for exact_key, group_topologies in exact_groups.items():
                if len(group_topologies) > 1:
                    # Verify all signatures are safe to merge
                    group_signatures = [signatures[t.bridge_domain_name] for t in group_topologies]
                    if self._verify_safe_group(group_signatures):
                        safe_groups[exact_key] = group_topologies
                        self.logger.info(f"Safe consolidation group: {exact_key} ({len(group_topologies)} BDs)")
                    else:
                        self.logger.warning(f"Unsafe group rejected: {exact_key}")
        
        return safe_groups
    
    def _create_signature(self, topology: TopologyData) -> BridgeDomainSignature:
        """Create comprehensive signature for a topology"""
        
        # Extract username
        username = self._extract_username(topology.bridge_domain_name)
        if not username:
            raise ValueError(f"Cannot extract username from {topology.bridge_domain_name}")
        
        # Extract configuration details
        vlan_id = None
        outer_vlan = None
        inner_vlan = None
        bridge_domain_type = BridgeDomainType.SINGLE_VLAN  # default
        
        if topology.bridge_domain_config:
            vlan_id = getattr(topology.bridge_domain_config, 'vlan_id', None)
            outer_vlan = getattr(topology.bridge_domain_config, 'outer_vlan', None)
            inner_vlan = getattr(topology.bridge_domain_config, 'inner_vlan', None)
            bridge_domain_type = topology.bridge_domain_config.bridge_domain_type
        
        # Detect scope
        scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
        
        # Count devices and interfaces
        device_count = len(topology.devices)
        interface_count = len(topology.interfaces)
        
        return BridgeDomainSignature(
            username=username,
            vlan_id=vlan_id,
            bridge_domain_type=bridge_domain_type,
            outer_vlan=outer_vlan,
            inner_vlan=inner_vlan,
            scope=scope,
            device_count=device_count,
            interface_count=interface_count
        )
    
    def _extract_username(self, bridge_domain_name: str) -> Optional[str]:
        """Extract username from bridge domain name"""
        
        # Remove scope prefixes
        name = bridge_domain_name
        if name.startswith(('g_', 'l_', 'd_')):
            name = name[2:]
        
        # Common patterns for username extraction
        patterns = [
            r'^([a-zA-Z][a-zA-Z0-9_-]*?)_v\d+',  # username_v123
            r'^([a-zA-Z][a-zA-Z0-9_-]*?)_v\d+_',  # username_v123_something
            r'^([a-zA-Z][a-zA-Z0-9_-]*?)(?:_|$)',  # username_ or username at end
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name)
            if match:
                username = match.group(1)
                # Filter out common non-username prefixes
                if username.lower() not in ['mgmt', 'test', 'temp', 'bundle', 'vlan', 'bd']:
                    return username.lower()
        
        return None
    
    def _verify_safe_group(self, signatures: List[BridgeDomainSignature]) -> bool:
        """Verify that all signatures in a group are safe to merge"""
        
        if len(signatures) < 2:
            return False
        
        # Check all pairs
        for i in range(len(signatures)):
            for j in range(i + 1, len(signatures)):
                if not signatures[i].is_safe_to_merge_with(signatures[j]):
                    return False
        
        return True
    
    def analyze_consolidation_safety(self, topologies: List[TopologyData]) -> Dict[str, any]:
        """Analyze the safety of current consolidation candidates"""
        
        # Get current (unsafe) candidates
        from .consolidation_manager import BridgeDomainConsolidationManager
        unsafe_manager = BridgeDomainConsolidationManager()
        unsafe_candidates = unsafe_manager.get_consolidation_candidates(topologies)
        
        # Get safe candidates
        safe_candidates = self.get_safe_consolidation_candidates(topologies)
        
        # Analyze differences
        analysis = {
            'total_topologies': len(topologies),
            'unsafe_groups': len(unsafe_candidates),
            'safe_groups': len(safe_candidates),
            'rejected_groups': len(unsafe_candidates) - len(safe_candidates),
            'unsafe_consolidations': sum(len(group) for group in unsafe_candidates.values()),
            'safe_consolidations': sum(len(group) for group in safe_candidates.values()),
            'potentially_dangerous': {},
            'safe_examples': {},
            'rejected_examples': {}
        }
        
        # Find dangerous consolidations
        for key, unsafe_group in unsafe_candidates.items():
            if key not in [sg.split('|')[0] for sg in safe_candidates.keys()]:
                # This group was rejected - analyze why
                if len(unsafe_group) > 1:
                    signatures = []
                    for topology in unsafe_group:
                        try:
                            sig = self._create_signature(topology)
                            signatures.append(sig)
                        except:
                            continue
                    
                    if len(signatures) > 1:
                        # Check why it's unsafe
                        reasons = []
                        for i in range(len(signatures)):
                            for j in range(i + 1, len(signatures)):
                                if not signatures[i].is_safe_to_merge_with(signatures[j]):
                                    reasons.append(self._get_merge_rejection_reason(signatures[i], signatures[j]))
                        
                        analysis['potentially_dangerous'][key] = {
                            'bridge_domains': [t.bridge_domain_name for t in unsafe_group],
                            'rejection_reasons': list(set(reasons))
                        }
        
        return analysis
    
    def _get_merge_rejection_reason(self, sig1: BridgeDomainSignature, sig2: BridgeDomainSignature) -> str:
        """Get human-readable reason why two signatures cannot be merged"""
        
        if sig1.bridge_domain_type != sig2.bridge_domain_type:
            return f"Different types: {sig1.bridge_domain_type.value} vs {sig2.bridge_domain_type.value}"
        
        if sig1.scope != sig2.scope:
            return f"Different scopes: {sig1.scope.value} vs {sig2.scope.value}"
        
        if sig1._is_qinq_type() and (sig1.outer_vlan != sig2.outer_vlan or sig1.inner_vlan != sig2.inner_vlan):
            return f"Different QinQ config: {sig1.outer_vlan}.{sig1.inner_vlan} vs {sig2.outer_vlan}.{sig2.inner_vlan}"
        
        if abs(sig1.device_count - sig2.device_count) > 2:
            return f"Different topology sizes: {sig1.device_count} vs {sig2.device_count} devices"
        
        return "Unknown safety issue"

