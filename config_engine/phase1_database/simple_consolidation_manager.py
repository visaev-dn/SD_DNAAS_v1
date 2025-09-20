#!/usr/bin/env python3
"""
SIMPLE Bridge Domain Consolidation Manager
Implements the core principle: Same VLAN = Same broadcast domain = Consolidate

This is the clean slate approach - simple, effective, and follows the documentation.
"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple
from dataclasses import dataclass

from config_engine.phase1_data_structures.topology_data import TopologyData
from config_engine.phase1_data_structures.enums import ConsolidationDecision


@dataclass
class SimpleConsolidationResult:
    """Simple consolidation result"""
    consolidation_key: str
    bridge_domain_names: List[str]
    decision: ConsolidationDecision
    reason: str


class SimpleConsolidationManager:
    """
    SIMPLE Bridge Domain Consolidation Manager
    
    Core Principle: Same VLAN = Same broadcast domain = Consolidate
    
    Rules:
    1. Same username (owner)
    2. Same VLAN ID (broadcast domain)
    3. That's it!
    
    No complex validation layers, no path validation, no over-engineering.
    Just the network truth: VLAN identity.
    """
    
    def __init__(self):
        self.consolidation_stats = {
            'total_groups': 0,
            'consolidated_groups': 0,
            'rejected_groups': 0
        }
    
    def consolidate_topologies(self, topologies: List[TopologyData]) -> Tuple[List[TopologyData], Dict[str, SimpleConsolidationResult]]:
        """
        Perform simple VLAN-based consolidation
        
        Returns:
            Tuple of (consolidated_topologies, consolidation_results)
        """
        print("🎯 SIMPLE VLAN-BASED CONSOLIDATION")
        print("=" * 50)
        print("Rule: Same username + Same VLAN = Consolidate")
        print("No complex validation - just network truth!")
        print()
        
        # Phase 1: Generate consolidation keys
        consolidation_keys = {}
        parsing_failures = []
        
        for topology in topologies:
            try:
                consolidation_key = self._generate_consolidation_key(topology)
                consolidation_keys[topology.bridge_domain_name] = consolidation_key
                print(f"✅ {topology.bridge_domain_name}: {consolidation_key}")
                    
            except ValueError as e:
                parsing_failures.append({
                    'bridge_domain': topology.bridge_domain_name,
                    'error': str(e)
                })
                print(f"❌ {topology.bridge_domain_name}: {str(e)}")
                continue
        
        # Report parsing failures
        if parsing_failures:
            print(f"\n🚨 PARSING FAILURES: {len(parsing_failures)} bridge domains")
            print("These require discovery system fixes:")
            for failure in parsing_failures[:5]:
                print(f"   ❌ {failure['bridge_domain']}: {failure['error']}")
            if len(parsing_failures) > 5:
                print(f"   ... and {len(parsing_failures) - 5} more failures")
            print()
        
        # Phase 2: Group by consolidation keys
        consolidation_groups = defaultdict(list)
        for topology in topologies:
            if topology.bridge_domain_name in consolidation_keys:
                key = consolidation_keys[topology.bridge_domain_name]
                consolidation_groups[key].append(topology)
        
        # Phase 3: Process each consolidation group
        consolidation_results = {}
        consolidated_topologies = []
        
        for consolidation_key, group_topologies in consolidation_groups.items():
            if len(group_topologies) == 1:
                # No consolidation needed
                consolidated_topologies.append(group_topologies[0])
                print(f"📋 {consolidation_key}: Single bridge domain (no consolidation)")
            else:
                # Multiple bridge domains with same key - consolidate!
                print(f"🎯 {consolidation_key}: {len(group_topologies)} bridge domains → CONSOLIDATE")
                
                # Create consolidation result
                result = SimpleConsolidationResult(
                    consolidation_key=consolidation_key,
                    bridge_domain_names=[t.bridge_domain_name for t in group_topologies],
                    decision=ConsolidationDecision.APPROVE,
                    reason="Same username + same VLAN = same broadcast domain"
                )
                consolidation_results[consolidation_key] = result
                
                # Consolidate the group (keep the first one, merge names)
                consolidated_topology = self._simple_merge(group_topologies)
                consolidated_topologies.append(consolidated_topology)
                self.consolidation_stats['consolidated_groups'] += 1
        
        self.consolidation_stats['total_groups'] = len(consolidation_groups)
        
        # Print summary
        self._print_summary()
        
        return consolidated_topologies, consolidation_results
    
    def _generate_consolidation_key(self, topology: TopologyData) -> str:
        """Generate consolidation key: username_v{vlan_id}"""
        
        # Extract username and VLAN ID
        username = self._extract_username(topology.bridge_domain_name)
        vlan_id = self._extract_primary_vlan(topology.bridge_domain_config)
        
        # Validate critical data
        if not username:
            raise ValueError("Username extraction failed")
        
        if vlan_id is None:
            raise ValueError("VLAN ID extraction failed - DISCOVERY SYSTEM PARSING ISSUE")
        
        # Generate key: username_v{vlan_id}
        return f"{username}_v{vlan_id}"
    
    def _extract_username(self, bridge_domain_name: str) -> str:
        """Extract username from bridge domain name"""
        
        if not bridge_domain_name:
            raise ValueError("Empty bridge domain name")
        
        # Remove scope prefixes (g_, l_, d_)
        name = bridge_domain_name
        if name.startswith(('g_', 'l_', 'd_')):
            name = name[2:]
        
        # Simple patterns for username extraction
        patterns = [
            r'^([a-zA-Z][a-zA-Z0-9]*?)_v\d+',           # username_v123
            r'^([a-zA-Z][a-zA-Z0-9]*?)_v\d+_to_\w+',    # username_v123_to_dest
            r'^([a-zA-Z][a-zA-Z0-9]*?)_v\d+_\w+',       # username_v123_desc
            r'^([a-zA-Z][a-zA-Z0-9]*?)_\d+',             # username_123
            r'^([a-zA-Z][a-zA-Z0-9]*?)_\w+',             # username_desc
            r'^([a-zA-Z][a-zA-Z0-9]*?)$',                # username
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name)
            if match:
                return match.group(1)
        
        raise ValueError(f"Could not extract username from: {bridge_domain_name}")
    
    def _extract_primary_vlan(self, bridge_domain_config) -> int:
        """Extract primary VLAN ID from bridge domain configuration"""
        
        if not bridge_domain_config:
            raise ValueError("No bridge domain configuration")
        
        # Priority order for VLAN extraction
        if hasattr(bridge_domain_config, 'vlan_id') and bridge_domain_config.vlan_id:
            return bridge_domain_config.vlan_id
        
        if hasattr(bridge_domain_config, 'outer_vlan') and bridge_domain_config.outer_vlan:
            return bridge_domain_config.outer_vlan
        
        if hasattr(bridge_domain_config, 'vlan_start') and bridge_domain_config.vlan_start:
            return bridge_domain_config.vlan_start
        
        if hasattr(bridge_domain_config, 'vlan_list') and bridge_domain_config.vlan_list:
            if bridge_domain_config.vlan_list:
                return bridge_domain_config.vlan_list[0]
        
        raise ValueError("No VLAN ID found in bridge domain configuration")
    
    def _simple_merge(self, group_topologies: List[TopologyData]) -> TopologyData:
        """Simple merge: keep first topology, update name to show consolidation"""
        
        if not group_topologies:
            raise ValueError("Empty topology group")
        
        # Keep the first topology
        consolidated = group_topologies[0]
        
        # Update the name to show consolidation
        original_names = [t.bridge_domain_name for t in group_topologies]
        consolidated.bridge_domain_name = f"CONSOLIDATED_{len(original_names)}_BDS"
        
        # Add consolidation metadata
        if hasattr(consolidated, 'consolidation_info'):
            consolidated.consolidation_info = {
                'consolidated_from': original_names,
                'consolidation_date': '2025-08-31',
                'consolidation_reason': 'Same username + same VLAN = same broadcast domain'
            }
        
        return consolidated
    
    def _print_summary(self):
        """Print simple consolidation summary"""
        print("\n" + "=" * 50)
        print("📊 CONSOLIDATION SUMMARY")
        print("=" * 50)
        print(f"Total consolidation groups: {self.consolidation_stats['total_groups']}")
        print(f"Groups consolidated: {self.consolidation_stats['consolidated_groups']}")
        print(f"Groups rejected: {self.consolidation_stats['rejected_groups']}")
        print()
        
        if self.consolidation_stats['consolidated_groups'] > 0:
            print("🎉 SUCCESS: Bridge domains consolidated based on VLAN identity!")
            print("💡 This reflects the true network topology.")
        else:
            print("ℹ️  No consolidation needed or possible.")
            print("💡 Check if discovery system is providing VLAN data correctly.")
    
    def get_consolidation_candidates(self, topologies: List[TopologyData]) -> Dict[str, List[str]]:
        """Get consolidation candidates for display"""
        
        consolidation_keys = {}
        
        for topology in topologies:
            try:
                consolidation_key = self._generate_consolidation_key(topology)
                consolidation_keys[topology.bridge_domain_name] = consolidation_key
            except ValueError:
                continue
        
        # Group by consolidation keys
        candidates = defaultdict(list)
        for bd_name, key in consolidation_keys.items():
            candidates[key].append(bd_name)
        
        # Only return groups with multiple bridge domains
        return {k: v for k, v in candidates.items() if len(v) > 1}
