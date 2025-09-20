#!/usr/bin/env python3
"""
Simplified Network Engineer Bridge Domain Consolidation Manager
Implements VLAN-based consolidation logic that reflects network reality
"""

import re
import json
import uuid
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime

from config_engine.phase1_data_structures.topology_data import TopologyData
from config_engine.phase1_data_structures.enums import (
    BridgeDomainType, BridgeDomainScope, TopologyType, ComplexityLevel, 
    ValidationStatus, ConsolidationDecision
)
from config_engine.path_validation import validate_path_continuity, ValidationResult


@dataclass
class ConsolidationDecisionResult:
    """Result of consolidation decision"""
    decision: ConsolidationDecision
    consolidation_key: str
    bridge_domain_names: List[str]
    confidence: float
    approval_reasons: List[str]
    rejection_reasons: List[str]
    warnings: List[str]
    debug_info: Dict[str, Any]
    safety_score: float = 0.95  # High safety for simplified VLAN-based logic
    validation_results: List = field(default_factory=list)  # Simplified consolidation doesn't use complex validation


class BridgeDomainConsolidationManager:
    """
    Simplified Network Engineer Bridge Domain Consolidation Manager
    
    Implements the new VLAN-based consolidation logic:
    - Same VLAN = Same broadcast domain = Consolidate
    - Scope differences don't matter (just admin marking)
    - Topology patterns don't matter (same broadcast domain)
    - Only VLAN identity matters for broadcast domain membership
    """
    
    def __init__(self, debug_enabled: bool = True):
        self.debug_enabled = debug_enabled
        self.consolidation_stats = {
            'total_groups': 0,
            'consolidated_groups': 0,
            'rejected_groups': 0,
            'review_required_groups': 0
        }
    
    def consolidate_topologies(self, topologies: List[TopologyData]) -> Tuple[List[TopologyData], Dict[str, ConsolidationDecisionResult]]:
        """
        Perform simplified VLAN-based consolidation
        
        Returns:
            Tuple of (consolidated_topologies, consolidation_decisions)
        """
        print("🎯 SIMPLIFIED NETWORK ENGINEER CONSOLIDATION")
        print("=" * 60)
        print("Rule: Same VLAN = Same broadcast domain = Consolidate")
        print("Scope differences don't matter (just admin marking)")
        print("Topology patterns don't matter (same broadcast domain)")
        print()
        
        # Phase 1: Generate consolidation keys
        consolidation_keys = {}
        parsing_failures = []
        
        for topology in topologies:
            try:
                consolidation_key = self._generate_consolidation_key(topology)
                consolidation_keys[topology.bridge_domain_name] = consolidation_key
                
                if self.debug_enabled:
                    print(f"✅ {topology.bridge_domain_name}: {consolidation_key}")
                    
            except ValueError as e:
                # Parsing failure - log for investigation
                parsing_failures.append({
                    'bridge_domain': topology.bridge_domain_name,
                    'error': str(e)
                })
                
                if self.debug_enabled:
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
        consolidation_decisions = {}
        consolidated_topologies = []
        
        for consolidation_key, group_topologies in consolidation_groups.items():
            if len(group_topologies) == 1:
                # No consolidation needed
                consolidated_topologies.append(group_topologies[0])
            else:
                # Multiple bridge domains with same key - validate consolidation
                decision_result = self._validate_consolidation_group(consolidation_key, group_topologies)
                consolidation_decisions[consolidation_key] = decision_result
                
                if self.debug_enabled:
                    self._print_consolidation_decision(decision_result)
                
                # Apply consolidation decision
                if decision_result.decision == ConsolidationDecision.APPROVE:
                    # Consolidate the group
                    consolidated_topology = self._merge_topologies(group_topologies, decision_result)
                    consolidated_topologies.append(consolidated_topology)
                    self.consolidation_stats['consolidated_groups'] += 1
                else:
                    # Keep separate
                    consolidated_topologies.extend(group_topologies)
                    if decision_result.decision == ConsolidationDecision.REJECT:
                        self.consolidation_stats['rejected_groups'] += 1
                    elif decision_result.decision == ConsolidationDecision.REVIEW_REQUIRED:
                        self.consolidation_stats['review_required_groups'] += 1
        
        self.consolidation_stats['total_groups'] = len(consolidation_groups)
        
        # Print consolidation summary
        self._print_consolidation_summary()
        
        return consolidated_topologies, consolidation_decisions
    
    def _generate_consolidation_key(self, topology: TopologyData) -> str:
        """Generate consolidation key based on VLAN identity"""
        
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
    
    def _extract_username(self, bridge_domain_name: str) -> Optional[str]:
        """Extract username from bridge domain name"""
        
        if not bridge_domain_name:
            return None
        
        # Remove scope prefixes (g_, l_, d_)
        name = bridge_domain_name
        if name.startswith(('g_', 'l_', 'd_')):
            name = name[2:]
        
        # Enhanced patterns for username extraction
        patterns = [
            r'^([a-zA-Z][a-zA-Z0-9]*?)_v\d+',           # username_v123
            r'^([a-zA-Z][a-zA-Z0-9]*?)_v\d+_',          # username_v123_something
            r'^([a-zA-Z][a-zA-Z0-9]*?)_.*?_v\d+',       # username_something_v123
            r'^([a-zA-Z][a-zA-Z0-9]*?)(?:_|$)',         # username_ or username at end
            # Edge case patterns
            r'^_([a-zA-Z][a-zA-Z0-9]*?)_v\d+',          # _username_v123 (double underscore)
            r'^([a-zA-Z][a-zA-Z0-9]*?)__v\d+',          # username__v123 (double underscore)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                username = match.group(1).lower()
                # Filter out common non-username prefixes
                if username not in ['mgmt', 'test', 'temp', 'bundle', 'vlan', 'bd']:
                    return username
        
        # Special handling for legacy names
        if name.startswith('bd-') or name.startswith('vlan'):
            return name.lower()
        
        # Handle M_ prefix legacy naming
        if bridge_domain_name.startswith('M_'):
            m_match = re.search(r'^M_([a-zA-Z][a-zA-Z0-9]*?)_\d+', bridge_domain_name)
            if m_match:
                return m_match.group(1).lower()
        
        return None
    
    def _extract_primary_vlan(self, bridge_domain_config) -> Optional[int]:
        """Extract primary VLAN ID from bridge domain configuration"""
        
        if not bridge_domain_config:
            return None
        
        # Strategy 1: For QinQ types, prioritize outer VLAN as service identifier
        if (hasattr(bridge_domain_config, 'bridge_domain_type') and 
            bridge_domain_config.bridge_domain_type and
            'qinq' in bridge_domain_config.bridge_domain_type.value.lower()):
            
            # For QinQ, outer VLAN is the service identifier
            if hasattr(bridge_domain_config, 'outer_vlan') and bridge_domain_config.outer_vlan:
                return bridge_domain_config.outer_vlan
        
        # Strategy 2: Direct VLAN ID
        if hasattr(bridge_domain_config, 'vlan_id') and bridge_domain_config.vlan_id:
            vlan_id = bridge_domain_config.vlan_id
            
            # For QinQ types, validate it's not an inner VLAN
            if (hasattr(bridge_domain_config, 'bridge_domain_type') and 
                bridge_domain_config.bridge_domain_type and
                'qinq' in bridge_domain_config.bridge_domain_type.value.lower()):
                # For QinQ, if vlan_id is in typical inner VLAN range (200-500), it's probably wrong
                if 200 <= vlan_id <= 500:
                    # Skip this - likely an inner VLAN, not service VLAN
                    pass
                else:
                    return vlan_id
            else:
                # For non-QinQ, use vlan_id directly
                return vlan_id
        
        # Strategy 3: Outer VLAN for any type (fallback)
        if hasattr(bridge_domain_config, 'outer_vlan') and bridge_domain_config.outer_vlan:
            return bridge_domain_config.outer_vlan
        
        # Strategy 4: First VLAN in range
        if (hasattr(bridge_domain_config, 'vlan_range_start') and 
            bridge_domain_config.vlan_range_start):
            return bridge_domain_config.vlan_range_start
        
        # Strategy 5: First VLAN in list
        if (hasattr(bridge_domain_config, 'vlan_list') and 
            bridge_domain_config.vlan_list and len(bridge_domain_config.vlan_list) > 0):
            return min(bridge_domain_config.vlan_list)
        
        return None
    
    def _validate_consolidation_group(self, consolidation_key: str, group_topologies: List[TopologyData]) -> ConsolidationDecisionResult:
        """Validate consolidation group using simplified VLAN-based rules"""
        
        if len(group_topologies) < 2:
            return ConsolidationDecisionResult(
                decision=ConsolidationDecision.REJECT,
                consolidation_key=consolidation_key,
                bridge_domain_names=[t.bridge_domain_name for t in group_topologies],
                confidence=0.0,
                approval_reasons=[],
                rejection_reasons=["Insufficient data for validation"],
                warnings=[],
                debug_info={"error": "Group too small"}
            )
        
        # Extract key information for validation
        bridge_domain_names = [t.bridge_domain_name for t in group_topologies]
        bridge_domain_configs = [t.bridge_domain_config for t in group_topologies if t.bridge_domain_config]
        
        # Rule 1: Same username (already validated by consolidation key)
        # Rule 2: Same VLAN ID (already validated by consolidation key)
        
        # Rule 3: Validate path continuity for all topologies in group
        path_validation_result = self._validate_group_paths(group_topologies)
        if not path_validation_result['can_consolidate']:
            return ConsolidationDecisionResult(
                decision=ConsolidationDecision.REJECT,
                consolidation_key=consolidation_key,
                bridge_domain_names=bridge_domain_names,
                confidence=0.0,
                approval_reasons=[],
                rejection_reasons=path_validation_result['rejection_reasons'],
                warnings=[],
                debug_info=path_validation_result
            )
        
        # Rule 4: Handle edge cases by bridge domain type
        validation_result = self._validate_type_specific_consolidation(bridge_domain_configs)
        
        if validation_result['can_consolidate']:
            return ConsolidationDecisionResult(
                decision=ConsolidationDecision.APPROVE,
                consolidation_key=consolidation_key,
                bridge_domain_names=bridge_domain_names,
                confidence=0.95,
                approval_reasons=[
                    "Same username and VLAN ID",
                    "Type-specific validation passed",
                    "Same broadcast domain confirmed"
                ],
                rejection_reasons=[],
                warnings=validation_result.get('warnings', []),
                debug_info=validation_result
            )
        else:
            return ConsolidationDecisionResult(
                decision=ConsolidationDecision.REJECT,
                consolidation_key=consolidation_key,
                bridge_domain_names=bridge_domain_names,
                confidence=0.0,
                approval_reasons=[],
                rejection_reasons=validation_result.get('rejection_reasons', ["Type-specific validation failed"]),
                warnings=[],
                debug_info=validation_result
            )
    
    def _validate_type_specific_consolidation(self, bridge_domain_configs: List) -> Dict[str, Any]:
        """Validate consolidation based on bridge domain type"""
        
        if not bridge_domain_configs:
            return {
                'can_consolidate': False,
                'rejection_reasons': ["No bridge domain configuration found"]
            }
        
        # Get bridge domain types
        bd_types = []
        for config in bridge_domain_configs:
            if hasattr(config, 'bridge_domain_type') and config.bridge_domain_type:
                bd_types.append(config.bridge_domain_type)
        
        if not bd_types:
            return {
                'can_consolidate': False,
                'rejection_reasons': ["No bridge domain types found"]
            }
        
        # Check if all bridge domains have the same type
        if len(set(bd_types)) > 1:
            return {
                'can_consolidate': False,
                'rejection_reasons': [f"Different bridge domain types: {[t.value for t in bd_types]}"]
            }
        
        bd_type = bd_types[0]
        
        # Type-specific validation
        if bd_type in [BridgeDomainType.DOUBLE_TAGGED, BridgeDomainType.QINQ_SINGLE_BD, 
                       BridgeDomainType.QINQ_MULTI_BD, BridgeDomainType.HYBRID]:
            # QinQ types: Validate outer VLAN consistency
            return self._validate_qinq_consolidation(bridge_domain_configs)
        
        elif bd_type == BridgeDomainType.SINGLE_TAGGED_RANGE:
            # VLAN ranges: Must be identical
            return self._validate_vlan_range_consolidation(bridge_domain_configs)
        
        elif bd_type == BridgeDomainType.SINGLE_TAGGED_LIST:
            # VLAN lists: Must be identical
            return self._validate_vlan_list_consolidation(bridge_domain_configs)
        
        elif bd_type == BridgeDomainType.PORT_MODE:
            # Port-mode: Same username + untagged pattern
            return {'can_consolidate': True, 'warnings': []}
        
        elif bd_type == BridgeDomainType.SINGLE_TAGGED:
            # Single VLAN: Simple case
            return {'can_consolidate': True, 'warnings': []}
        
        else:
            return {
                'can_consolidate': False,
                'rejection_reasons': [f"Unknown bridge domain type: {bd_type.value}"]
            }
    
    def _validate_group_paths(self, group_topologies: List[TopologyData]) -> Dict[str, Any]:
        """Validate that all topologies in a consolidation group have valid paths"""
        
        invalid_paths = []
        path_validation_results = []
        
        for topology in group_topologies:
            # Validate each path in the topology
            for path in topology.paths:
                if path.segments:
                    validation_result = validate_path_continuity(path.segments)
                    path_validation_results.append({
                        'topology': topology.bridge_domain_name,
                        'path': path,
                        'validation_result': validation_result
                    })
                    
                    if not validation_result.is_valid:
                        invalid_paths.append({
                            'topology': topology.bridge_domain_name,
                            'errors': validation_result.get_error_summary()
                        })
        
        if invalid_paths:
            return {
                'can_consolidate': False,
                'rejection_reasons': [
                    f"Path validation failed for {len(invalid_paths)} topologies",
                    "Cannot consolidate topologies with invalid network paths"
                ],
                'invalid_paths': invalid_paths,
                'path_validation_results': path_validation_results
            }
        
        return {
            'can_consolidate': True,
            'warnings': [],
            'path_validation_results': path_validation_results
        }
    
    def _validate_type_specific_consolidation(self, bridge_domain_configs: List) -> Dict[str, Any]:
        """Validate consolidation based on bridge domain type"""
        
        if not bridge_domain_configs:
            return {
                'can_consolidate': False,
                'rejection_reasons': ["No bridge domain configuration found"]
            }
        
        # Get bridge domain types
        bd_types = []
        for config in bridge_domain_configs:
            if hasattr(config, 'bridge_domain_type') and config.bridge_domain_type:
                bd_types.append(config.bridge_domain_type)
        
        if not bd_types:
            return {
                'can_consolidate': False,
                'rejection_reasons': ["No bridge domain types found"]
            }
        
        # Check if all bridge domains have the same type
        if len(set(bd_types)) > 1:
            return {
                'can_consolidate': False,
                'rejection_reasons': [f"Different bridge domain types: {[t.value for t in bd_types]}"]
            }
        
        bd_type = bd_types[0]
        
        # Type-specific validation
        if bd_type in [BridgeDomainType.DOUBLE_TAGGED, BridgeDomainType.QINQ_SINGLE_BD, 
                       BridgeDomainType.QINQ_MULTI_BD, BridgeDomainType.HYBRID]:
            # QinQ types: Validate outer VLAN consistency
            return self._validate_qinq_consolidation(bridge_domain_configs)
        
        elif bd_type == BridgeDomainType.SINGLE_TAGGED_RANGE:
            # VLAN ranges: Must be identical
            return self._validate_vlan_range_consolidation(bridge_domain_configs)
        
        elif bd_type == BridgeDomainType.SINGLE_TAGGED_LIST:
            # VLAN lists: Must be identical
            return self._validate_vlan_list_consolidation(bridge_domain_configs)
        
        elif bd_type == BridgeDomainType.PORT_MODE:
            # Port-mode: Same username + untagged pattern
            return {'can_consolidate': True, 'warnings': []}
        
        elif bd_type == BridgeDomainType.SINGLE_TAGGED:
            # Single VLAN: Simple case
            return {'can_consolidate': True, 'warnings': []}
        
        else:
            return {
                'can_consolidate': False,
                'rejection_reasons': [f"Unknown bridge domain type: {bd_type.value}"]
            }
    
    def _validate_qinq_consolidation(self, bridge_domain_configs: List) -> Dict[str, Any]:
        """Validate QinQ consolidation: Same outer VLAN = Same QinQ service"""
        
        outer_vlans = []
        for config in bridge_domain_configs:
            if hasattr(config, 'outer_vlan') and config.outer_vlan:
                outer_vlans.append(config.outer_vlan)
        
        if not outer_vlans:
            return {
                'can_consolidate': False,
                'rejection_reasons': ["QinQ bridge domains missing outer VLAN data"]
            }
        
        if len(set(outer_vlans)) > 1:
            return {
                'can_consolidate': False,
                'rejection_reasons': [f"Different outer VLANs: {outer_vlans}"]
            }
        
        return {
            'can_consolidate': True,
            'warnings': [],
            'outer_vlan': outer_vlans[0]
        }
    
    def _validate_vlan_range_consolidation(self, bridge_domain_configs: List) -> Dict[str, Any]:
        """Validate VLAN range consolidation: Must be identical"""
        
        ranges = []
        for config in bridge_domain_configs:
            if (hasattr(config, 'vlan_range_start') and config.vlan_range_start and
                hasattr(config, 'vlan_range_end') and config.vlan_range_end):
                ranges.append((config.vlan_range_start, config.vlan_range_end))
        
        if not ranges:
            return {
                'can_consolidate': False,
                'rejection_reasons': ["VLAN range bridge domains missing range data"]
            }
        
        if len(set(ranges)) > 1:
            return {
                'can_consolidate': False,
                'rejection_reasons': [f"Different VLAN ranges: {ranges}"]
            }
        
        return {
            'can_consolidate': True,
            'warnings': [],
            'vlan_range': ranges[0]
        }
    
    def _validate_vlan_list_consolidation(self, bridge_domain_configs: List) -> Dict[str, Any]:
        """Validate VLAN list consolidation: Must be identical"""
        
        lists = []
        for config in bridge_domain_configs:
            if hasattr(config, 'vlan_list') and config.vlan_list:
                lists.append(tuple(sorted(config.vlan_list)))
        
        if not lists:
            return {
                'can_consolidate': False,
                'rejection_reasons': ["VLAN list bridge domains missing list data"]
            }
        
        if len(set(lists)) > 1:
            return {
                'can_consolidate': False,
                'rejection_reasons': [f"Different VLAN lists: {lists}"]
            }
        
        return {
            'can_consolidate': True,
            'warnings': [],
            'vlan_list': lists[0]
        }
    
    def _merge_topologies(self, group_topologies: List[TopologyData], 
                         decision_result: ConsolidationDecisionResult) -> TopologyData:
        """Merge topologies based on consolidation decision"""
        
        # Select best topology as base
        base_topology = self._select_best_topology(group_topologies)
        
        # For now, return the base topology
        # In a full implementation, we would merge devices, interfaces, and paths
        return base_topology
    
    def _select_best_topology(self, topologies: List[TopologyData]) -> TopologyData:
        """Select the best topology from a group as the base for consolidation"""
        
        best_topology = topologies[0]
        best_score = 0
        
        for topology in topologies:
            score = 0
            
            # Device count (weight: 10)
            score += len(topology.devices) * 10
            
            # Interface count (weight: 1)
            score += len(topology.interfaces)
            
            # Name length (weight: -1, shorter is better)
            score -= len(topology.bridge_domain_name)
            
            # Global scope preference (weight: 100)
            scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
            if scope == BridgeDomainScope.GLOBAL:
                score += 100
            
            if score > best_score:
                best_score = score
                best_topology = topology
        
        return best_topology
    
    def get_consolidation_candidates(self, topologies: List[TopologyData]) -> Dict[str, List[str]]:
        """Identify consolidation candidates using simplified VLAN-based logic"""
        
        # Generate consolidation keys
        consolidation_keys = {}
        for topology in topologies:
            try:
                consolidation_key = self._generate_consolidation_key(topology)
                consolidation_keys[topology.bridge_domain_name] = consolidation_key
            except Exception:
                continue
        
        # Group by consolidation key
        groups = defaultdict(list)
        for topology in topologies:
            bd_name = topology.bridge_domain_name
            if bd_name in consolidation_keys:
                key = consolidation_keys[bd_name]
                groups[key].append(topology)
        
        # Return only groups with multiple topologies
        candidates = {}
        for consolidation_key, group_topologies in groups.items():
            if len(group_topologies) > 1:
                candidates[consolidation_key] = [t.bridge_domain_name for t in group_topologies]
        
        return candidates
    
    def _print_consolidation_decision(self, decision_result: ConsolidationDecisionResult):
        """Print consolidation decision in a user-friendly format"""
        
        status = "✅ APPROVED" if decision_result.decision == ConsolidationDecision.APPROVE else "❌ REJECTED"
        
        print(f"\n{status}: {decision_result.consolidation_key}")
        print(f"   Bridge Domains: {', '.join(decision_result.bridge_domain_names)}")
        print(f"   Confidence: {decision_result.confidence:.2f}")
        
        if decision_result.approval_reasons:
            print("   ✅ Reasons:")
            for reason in decision_result.approval_reasons:
                print(f"      • {reason}")
        
        if decision_result.rejection_reasons:
            print("   ❌ Reasons:")
            for reason in decision_result.rejection_reasons:
                print(f"      • {reason}")
        
        if decision_result.warnings:
            print("   ⚠️  Warnings:")
            for warning in decision_result.warnings:
                print(f"      • {warning}")
        
        print()
    
    def _print_consolidation_summary(self):
        """Print consolidation summary statistics"""
        
        print("📊 CONSOLIDATION SUMMARY")
        print("=" * 40)
        print(f"Total Groups Analyzed: {self.consolidation_stats['total_groups']}")
        print(f"✅ Consolidated Groups: {self.consolidation_stats['consolidated_groups']}")
        print(f"❌ Rejected Groups: {self.consolidation_stats['rejected_groups']}")
        print(f"⚠️  Review Required: {self.consolidation_stats['review_required_groups']}")
        
        if self.consolidation_stats['total_groups'] > 0:
            success_rate = (self.consolidation_stats['consolidated_groups'] / self.consolidation_stats['total_groups'] * 100)
            print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        print()
