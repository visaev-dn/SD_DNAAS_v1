#!/usr/bin/env python3
"""
Root Consolidation Manager - Back to the Roots
Implements the documented network engineer approach: Same VLAN = Same broadcast domain = Consolidate

Based on BRIDGE_DOMAIN_CONSOLIDATION_DESIGN.md:
- Simple rule: Same username + same VLAN = consolidate  
- Remove over-engineered validation layers
- Type-specific edge case handling for QinQ, ranges, lists
- Network reality over admin preference
"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

from config_engine.phase1_data_structures.topology_data import TopologyData
from config_engine.phase1_data_structures.enums import (
    BridgeDomainType, BridgeDomainScope, ConsolidationDecision
)

logger = logging.getLogger(__name__)


@dataclass
class RootConsolidationResult:
    """Simple consolidation result - no over-engineering"""
    consolidation_key: str
    decision: ConsolidationDecision
    reason: str
    topologies: List[TopologyData]
    consolidated_topology: Optional[TopologyData] = None


class RootConsolidationManager:
    """
    ROOT Consolidation Manager - Back to Network Engineering Fundamentals
    
    Core Principle from documentation:
    "Same VLAN = Same Broadcast Domain = MUST Consolidate"
    
    Rules (and ONLY these rules):
    1. Same username (owner) 
    2. Same VLAN ID (broadcast domain)
    3. Type-specific edge cases (QinQ outer VLAN, VLAN ranges/lists)
    
    What we DON'T check (over-engineered complexity):
    - Scope differences (GLO vs LOC) - just admin marking
    - Topology patterns (P2P vs P2MP) - same broadcast domain  
    - Device counts - same broadcast domain
    - Complexity levels - same broadcast domain
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total_bridge_domains': 0,
            'consolidation_groups': 0,
            'consolidated_bridge_domains': 0,
            'parsing_failures': 0
        }
    
    def consolidate_topologies(self, topologies: List[TopologyData]) -> Tuple[List[TopologyData], Dict[str, RootConsolidationResult]]:
        """
        Perform root consolidation based on documented network engineer logic
        
        Returns:
            Tuple of (consolidated_topologies, consolidation_results)
        """
        self.logger.info("🎯 ROOT CONSOLIDATION - BACK TO NETWORK ENGINEERING FUNDAMENTALS")
        self.logger.info("=" * 70)
        self.logger.info("Rule: Same username + Same VLAN = Same broadcast domain = Consolidate")
        self.logger.info("No over-engineered validation - just network truth!")
        self.logger.info("")
        
        self.stats['total_bridge_domains'] = len(topologies)
        
        # Phase 1: Generate consolidation keys using VLAN identity
        consolidation_groups = defaultdict(list)
        parsing_failures = []
        
        for topology in topologies:
            try:
                consolidation_key = self._generate_vlan_based_key(topology)
                consolidation_groups[consolidation_key].append(topology)
                self.logger.debug(f"✅ {topology.bridge_domain_name}: {consolidation_key}")
                    
            except ValueError as e:
                parsing_failures.append({
                    'bridge_domain': topology.bridge_domain_name,
                    'error': str(e)
                })
                self.logger.warning(f"❌ {topology.bridge_domain_name}: {str(e)}")
                # Keep as individual topology
                consolidation_groups[f"PARSING_FAILURE_{topology.bridge_domain_name}"] = [topology]
                continue
        
        self.stats['parsing_failures'] = len(parsing_failures)
        self.stats['consolidation_groups'] = len([g for g in consolidation_groups.values() if len(g) > 1])
        
        # Phase 2: Apply consolidation
        consolidated_topologies = []
        consolidation_results = {}
        
        for consolidation_key, group_topologies in consolidation_groups.items():
            if len(group_topologies) == 1:
                # No consolidation needed
                consolidated_topologies.append(group_topologies[0])
            else:
                # Multiple bridge domains with same VLAN identity - consolidate them
                result = self._consolidate_group(consolidation_key, group_topologies)
                consolidation_results[consolidation_key] = result
                
                if result.decision == ConsolidationDecision.APPROVE:
                    consolidated_topologies.append(result.consolidated_topology)
                    self.stats['consolidated_bridge_domains'] += len(group_topologies) - 1
                    self.logger.info(f"✅ CONSOLIDATED: {consolidation_key} ({len(group_topologies)} → 1)")
                else:
                    # Keep separate (shouldn't happen with simple logic, but safety)
                    consolidated_topologies.extend(group_topologies)
                    self.logger.warning(f"❌ REJECTED: {consolidation_key} - {result.reason}")
        
        # Print summary
        self._print_consolidation_summary()
        
        return consolidated_topologies, consolidation_results
    
    def _generate_vlan_based_key(self, topology: TopologyData) -> str:
        """
        Generate consolidation key based on VLAN identity (the ONLY thing that matters)
        
        From documentation: "Same username + same VLAN = consolidate"
        """
        # Extract username from bridge domain name
        username = self._extract_username(topology.bridge_domain_name)
        if not username:
            raise ValueError(f"Cannot extract username from bridge domain name")
        
        # Get VLAN ID from authoritative sources ONLY
        vlan_id = self._get_authoritative_vlan_id(topology)
        if vlan_id is None:
            raise ValueError(f"No authoritative VLAN ID found - missing device configuration data")
        
        # Handle type-specific edge cases
        if hasattr(topology, 'bridge_domain_config') and topology.bridge_domain_config:
            bd_type = topology.bridge_domain_config.bridge_domain_type
            
            # QinQ types: Use outer VLAN as service identifier
            if bd_type in [BridgeDomainType.DOUBLE_TAGGED, BridgeDomainType.QINQ_SINGLE_BD, 
                          BridgeDomainType.QINQ_MULTI_BD, BridgeDomainType.HYBRID]:
                outer_vlan = getattr(topology.bridge_domain_config, 'outer_vlan', None)
                if outer_vlan:
                    return f"{username}_qinq_outer_{outer_vlan}"
            
            # VLAN Range types: Use range as identifier  
            elif bd_type == BridgeDomainType.SINGLE_TAGGED_RANGE:
                vlan_start = getattr(topology.bridge_domain_config, 'vlan_start', None)
                vlan_end = getattr(topology.bridge_domain_config, 'vlan_end', None)
                if vlan_start and vlan_end:
                    return f"{username}_range_{vlan_start}_{vlan_end}"
            
            # VLAN List types: Use sorted list as identifier
            elif bd_type == BridgeDomainType.SINGLE_TAGGED_LIST:
                vlan_list = getattr(topology.bridge_domain_config, 'vlan_list', None)
                if vlan_list:
                    sorted_vlans = sorted(vlan_list)
                    return f"{username}_list_{'_'.join(map(str, sorted_vlans))}"
            
            # Port Mode: Use username only (no VLAN)
            elif bd_type == BridgeDomainType.PORT_MODE:
                return f"{username}_port_mode"
        
        # Default: Single VLAN (Type 4A)
        return f"{username}_vlan_{vlan_id}"
    
    def _extract_username(self, bridge_domain_name: str) -> Optional[str]:
        """
        Extract username from bridge domain name using documented patterns
        
        From documentation: Username extraction is REQUIRED for consolidation
        """
        if not bridge_domain_name:
            return None
        
        clean_name = bridge_domain_name.strip().lower()
        
        # Pattern 1: Standard naming (l_user_v123, g_user_v456)
        user_match = re.search(r'^[gl]_([^_v]+)', clean_name)
        if user_match:
            return user_match.group(1)
        
        # Pattern 2: TATA bridge domains (all same user)
        if 'tata' in clean_name:
            return 'tata'
        
        # Pattern 3: Management networks
        if 'mgmt' in clean_name:
            return 'mgmt'
        
        # Pattern 4: Direct username patterns (visaev_v123, mochiu_v456)
        user_match = re.search(r'^([^_v]+)_v\d+', clean_name)
        if user_match:
            return user_match.group(1)
        
        # Pattern 5: Complex patterns (g_visaev-test_v257)
        user_match = re.search(r'^[gl]_([^_]+)', clean_name)
        if user_match:
            # Handle compound usernames (visaev-test, visaev-jn204)
            username = user_match.group(1)
            # Extract base username (visaev from visaev-test)
            base_match = re.match(r'^([^-]+)', username)
            if base_match:
                return base_match.group(1)
            return username
        
        return None
    
    def _get_authoritative_vlan_id(self, topology: TopologyData) -> Optional[int]:
        """
        Get VLAN ID from authoritative sources ONLY
        
        From documentation: "NEVER rely on interface names for VLAN data"
        Authoritative sources: Device configuration, VLAN manipulation commands
        """
        # Priority 1: Bridge domain configuration VLAN ID
        if hasattr(topology, 'bridge_domain_config') and topology.bridge_domain_config:
            if topology.bridge_domain_config.vlan_id:
                return topology.bridge_domain_config.vlan_id
        
        # Priority 2: Topology-level VLAN ID (from device config)
        if hasattr(topology, 'vlan_id') and topology.vlan_id:
            return topology.vlan_id
        
        # Priority 3: Interface VLAN configuration (authoritative device config)
        if hasattr(topology, 'interfaces') and topology.interfaces:
            for interface in topology.interfaces:
                if hasattr(interface, 'vlan_id') and interface.vlan_id:
                    # Validate it's from device config, not interface name inference
                    if hasattr(interface, 'source_data') and interface.source_data:
                        # Check if VLAN came from actual device configuration
                        if 'vlan_config' in interface.source_data or 'device_config' in interface.source_data:
                            return interface.vlan_id
        
        return None
    
    def _consolidate_group(self, consolidation_key: str, topologies: List[TopologyData]) -> RootConsolidationResult:
        """
        Consolidate a group of topologies with same VLAN identity
        
        From documentation: "Same VLAN = Same broadcast domain = MUST consolidate"
        """
        if len(topologies) < 2:
            return RootConsolidationResult(
                consolidation_key=consolidation_key,
                decision=ConsolidationDecision.REJECT,
                reason="Single topology - no consolidation needed",
                topologies=topologies
            )
        
        # For root consolidation: Same VLAN identity = ALWAYS consolidate
        # No over-engineered validation layers
        
        # Create consolidated topology
        consolidated_topology = self._merge_topologies(topologies, consolidation_key)
        
        return RootConsolidationResult(
            consolidation_key=consolidation_key,
            decision=ConsolidationDecision.APPROVE,
            reason=f"Same VLAN identity - network engineering rule",
            topologies=topologies,
            consolidated_topology=consolidated_topology
        )
    
    def _merge_topologies(self, topologies: List[TopologyData], consolidation_key: str) -> TopologyData:
        """
        Merge multiple topologies into one consolidated topology
        
        Preserves all network information while creating unified view
        """
        if not topologies:
            raise ValueError("Cannot merge empty topology list")
        
        # Use the first topology as base
        base_topology = topologies[0]
        
        # Collect all unique devices, interfaces, and paths
        all_devices = []
        all_interfaces = []
        all_paths = []
        all_bridge_domain_names = []
        
        device_names = set()
        interface_keys = set()
        path_names = set()
        
        for topology in topologies:
            all_bridge_domain_names.append(topology.bridge_domain_name)
            
            # Merge devices (avoid duplicates)
            if hasattr(topology, 'devices') and topology.devices:
                for device in topology.devices:
                    if device.name not in device_names:
                        all_devices.append(device)
                        device_names.add(device.name)
            
            # Merge interfaces (avoid duplicates)
            if hasattr(topology, 'interfaces') and topology.interfaces:
                for interface in topology.interfaces:
                    interface_key = f"{interface.device_name}:{interface.name}"
                    if interface_key not in interface_keys:
                        all_interfaces.append(interface)
                        interface_keys.add(interface_key)
            
            # Merge paths (avoid duplicates)
            if hasattr(topology, 'paths') and topology.paths:
                for path in topology.paths:
                    if path.path_name not in path_names:
                        all_paths.append(path)
                        path_names.add(path.path_name)
        
        # Create consolidated bridge domain name
        consolidated_name = f"CONSOLIDATED_{consolidation_key}_{len(topologies)}BDs"
        
        # Create new consolidated topology
        from datetime import datetime
        
        consolidated_topology = TopologyData(
            bridge_domain_name=consolidated_name,
            topology_type=base_topology.topology_type,
            vlan_id=base_topology.vlan_id,
            devices=all_devices,
            interfaces=all_interfaces,
            paths=all_paths,
            bridge_domain_config=base_topology.bridge_domain_config,  # Use base config
            discovered_at=datetime.now(),
            scan_method="root_consolidation",
            confidence_score=min(t.confidence_score for t in topologies),  # Conservative confidence
            source_data={
                'consolidation_key': consolidation_key,
                'original_bridge_domains': all_bridge_domain_names,
                'consolidation_reason': 'Same VLAN identity - network engineering rule',
                'consolidated_count': len(topologies)
            }
        )
        
        return consolidated_topology
    
    def _print_consolidation_summary(self):
        """Print consolidation summary"""
        self.logger.info("")
        self.logger.info("🎯 ROOT CONSOLIDATION SUMMARY")
        self.logger.info("=" * 50)
        self.logger.info(f"📊 Total Bridge Domains: {self.stats['total_bridge_domains']}")
        self.logger.info(f"🔗 Consolidation Groups: {self.stats['consolidation_groups']}")
        self.logger.info(f"✅ Consolidated Bridge Domains: {self.stats['consolidated_bridge_domains']}")
        self.logger.info(f"❌ Parsing Failures: {self.stats['parsing_failures']}")
        
        if self.stats['consolidation_groups'] > 0:
            reduction_percent = (self.stats['consolidated_bridge_domains'] / self.stats['total_bridge_domains']) * 100
            self.logger.info(f"📈 Reduction: {reduction_percent:.1f}% (network truth revealed)")
        
        self.logger.info("")
        self.logger.info("🎯 Network Engineering Truth: Same VLAN = Same Broadcast Domain")
        self.logger.info("✅ No over-engineered complexity - just network reality!")
