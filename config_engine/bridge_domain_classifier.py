#!/usr/bin/env python3
"""
Bridge Domain Classifier

Systematic classification of bridge domains based on VLAN configuration patterns
following DNAAS documentation types 1-5.
"""

import logging
from typing import Dict, List, Optional, Tuple

# Import existing enum from phase1_data_structures
from config_engine.phase1_data_structures.enums import BridgeDomainType

logger = logging.getLogger(__name__)

class BridgeDomainClassifier:
    """
    Systematic bridge domain classifier based on VLAN configuration patterns.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def classify_bridge_domain(self, bd_name: str, interfaces: List[Dict]) -> Tuple[BridgeDomainType, int, Dict]:
        """
        Classify bridge domain based on interface VLAN configurations.
        
        Args:
            bd_name: Bridge domain name
            interfaces: List of interface configurations
            
        Returns:
            Tuple of (BridgeDomainType, confidence_score, analysis_details)
        """
        
        if not interfaces:
            return BridgeDomainType.SINGLE_VLAN, 10, {"error": "No interfaces found"}
        
        # Analyze VLAN configuration patterns
        analysis = self._analyze_vlan_patterns(interfaces)
        
        # Apply classification rules
        bd_type, confidence = self._apply_classification_rules(analysis)
        
        # Get QinQ subtype information if applicable
        if bd_type == BridgeDomainType.QINQ:
            analysis['qinq_subtype'] = self._determine_qinq_subtype(analysis)
        
        self.logger.debug(f"Classified {bd_name} as {bd_type} with {confidence}% confidence")
        
        return bd_type, confidence, analysis
    
    def _analyze_vlan_patterns(self, interfaces: List[Dict]) -> Dict:
        """Analyze VLAN configuration patterns across all interfaces."""
        
        analysis = {
            # Physical interface analysis
            'physical_interfaces': 0,
            'subinterfaces': 0,
            'interfaces_with_vlans': 0,
            'interfaces_without_vlans': 0,
            
            # VLAN configuration analysis
            'single_vlan_configs': [],
            'vlan_ranges': [],
            'vlan_lists': [],
            'full_ranges_1_4094': 0,
            
            # QinQ indicators
            'vlan_manipulation_count': 0,
            'push_outer_tag_count': 0,
            'pop_operations_count': 0,
            'outer_inner_tag_pairs': [],
            
            # Interface details
            'interface_details': [],
            
            # Unique VLAN tracking
            'unique_vlan_ids': []
        }
        
        for iface in interfaces:
            iface_analysis = self._analyze_interface(iface)
            analysis['interface_details'].append(iface_analysis)
            
            # Aggregate statistics
            if iface_analysis['is_physical']:
                analysis['physical_interfaces'] += 1
            else:
                analysis['subinterfaces'] += 1
            
            if iface_analysis['has_vlan_config']:
                analysis['interfaces_with_vlans'] += 1
            else:
                analysis['interfaces_without_vlans'] += 1
            
            # VLAN configuration aggregation
            if iface_analysis['vlan_id']:
                analysis['single_vlan_configs'].append(iface_analysis['vlan_id'])
                if iface_analysis['vlan_id'] not in analysis['unique_vlan_ids']:
                    analysis['unique_vlan_ids'].append(iface_analysis['vlan_id'])
            
            if iface_analysis['outer_vlan']:
                if iface_analysis['outer_vlan'] not in analysis['unique_vlan_ids']:
                    analysis['unique_vlan_ids'].append(iface_analysis['outer_vlan'])
            
            if iface_analysis['inner_vlan']:
                if iface_analysis['inner_vlan'] not in analysis['unique_vlan_ids']:
                    analysis['unique_vlan_ids'].append(iface_analysis['inner_vlan'])
            
            if iface_analysis['vlan_range']:
                analysis['vlan_ranges'].append(iface_analysis['vlan_range'])
                if iface_analysis['vlan_range'] == '1-4094':
                    analysis['full_ranges_1_4094'] += 1
            
            if iface_analysis['vlan_list']:
                analysis['vlan_lists'].append(iface_analysis['vlan_list'])
            
            # QinQ indicators
            if iface_analysis['has_vlan_manipulation']:
                analysis['vlan_manipulation_count'] += 1
                
                if iface_analysis['has_push_outer']:
                    analysis['push_outer_tag_count'] += 1
                
                if iface_analysis['has_pop']:
                    analysis['pop_operations_count'] += 1
            
            # Only add to outer_inner_tag_pairs if BOTH outer AND inner VLANs are valid integers
            outer_vlan = iface_analysis['outer_vlan']
            inner_vlan = iface_analysis['inner_vlan']
            
            if (outer_vlan is not None and inner_vlan is not None and 
                isinstance(outer_vlan, int) and isinstance(inner_vlan, int) and
                1 <= outer_vlan <= 4094 and 1 <= inner_vlan <= 4094 and
                outer_vlan != inner_vlan):  # Must be different for true QinQ
                analysis['outer_inner_tag_pairs'].append({
                    'outer': outer_vlan,
                    'inner': inner_vlan,
                    'interface': iface['name']
                })
        
        return analysis
    
    def _analyze_interface(self, iface: Dict) -> Dict:
        """Analyze a single interface's VLAN configuration."""
        
        analysis = {
            'interface_name': iface.get('name', 'unknown'),
            'is_physical': iface.get('type') == 'physical',
            'is_subinterface': '.' in iface.get('name', ''),
            
            # VLAN configuration
            'vlan_id': iface.get('vlan_id'),
            'vlan_range': iface.get('vlan_range'),
            'vlan_list': iface.get('vlan_list'),
            'outer_vlan': iface.get('outer_vlan'),
            'inner_vlan': iface.get('inner_vlan'),
            
            # VLAN manipulation
            'vlan_manipulation': iface.get('vlan_manipulation'),
            'has_vlan_manipulation': bool(iface.get('vlan_manipulation')),
            'has_push_outer': False,
            'has_pop': False,
            
            # L2 service
            'l2_service_enabled': iface.get('l2_service', False),
            
            # Configuration presence
            'has_vlan_config': False
        }
        
        # Analyze VLAN manipulation details
        vlan_manip = iface.get('vlan_manipulation')
        if vlan_manip:
            vlan_manip_str = str(vlan_manip).lower()
            analysis['has_push_outer'] = 'push outer-tag' in vlan_manip_str
            analysis['has_pop'] = 'pop' in vlan_manip_str
        
        # Determine if interface has any VLAN configuration
        analysis['has_vlan_config'] = any([
            analysis['vlan_id'],
            analysis['vlan_range'], 
            analysis['vlan_list'],
            analysis['outer_vlan'],
            analysis['inner_vlan'],
            analysis['has_vlan_manipulation']
        ])
        
        return analysis
    
    def _determine_qinq_subtype(self, analysis: Dict) -> Dict:
        """
        Determine QinQ subtype based on DNAAS documentation types.
        
        Returns detailed QinQ classification information.
        """
        subtype_info = {
            'dnaas_type': None,
            'imposition_location': None,
            'traffic_distribution': None,
            'confidence': 0
        }
        
        # Type 2A: Q-in-Q Single BD (all traffic to single bridge domain)
        if analysis['full_ranges_1_4094'] > 0:
            subtype_info.update({
                'dnaas_type': '2A',
                'traffic_distribution': 'single_bd',
                'confidence': 90
            })
            self.logger.debug("QinQ Subtype: Type 2A (Single BD, full range)")
        
        # Type 2B: Q-in-Q Multi BD (traffic split by inner VLAN)
        elif (len(analysis['vlan_ranges']) > 0 and 
              analysis['full_ranges_1_4094'] == 0):
            subtype_info.update({
                'dnaas_type': '2B', 
                'traffic_distribution': 'multi_bd',
                'confidence': 85
            })
            self.logger.debug("QinQ Subtype: Type 2B (Multi BD, specific ranges)")
        
        # Type 1: Double-Tagged with Edge Imposition
        elif len(analysis['outer_inner_tag_pairs']) > 0:
            subtype_info.update({
                'dnaas_type': '1',
                'imposition_location': 'edge',
                'traffic_distribution': 'paired',
                'confidence': 85
            })
            self.logger.debug("QinQ Subtype: Type 1 (Double-tagged, edge imposition)")
        
        # Determine imposition location for Type 2A/2B
        if subtype_info['dnaas_type'] in ['2A', '2B']:
            if (analysis['push_outer_tag_count'] > 0 and 
                analysis['pop_operations_count'] > 0):
                subtype_info['imposition_location'] = 'leaf'
                self.logger.debug("QinQ Imposition: LEAF (push/pop operations detected)")
            else:
                subtype_info['imposition_location'] = 'edge'  # Default assumption
        
        return subtype_info
    
    def _determine_specific_qinq_type(self, analysis: Dict) -> Tuple[BridgeDomainType, int]:
        """
        Determine specific DNAAS QinQ type (1, 2A, 2B, 3) based on LEAF configuration patterns
        """
        
        # Type 1: Static Double-Tag (outer/inner tags WITHOUT any manipulation)
        if (len(analysis['outer_inner_tag_pairs']) > 0 and 
            analysis['vlan_manipulation_count'] == 0 and
            analysis['push_outer_tag_count'] == 0 and
            analysis['pop_operations_count'] == 0):
            self.logger.debug("QinQ Type 1: Static double-tag configuration (no LEAF manipulation)")
            return BridgeDomainType.DOUBLE_TAGGED, 95
        
        # Type 2A: LEAF Full Range QinQ (1-4094 + manipulation)
        elif (analysis['full_ranges_1_4094'] > 0 and 
              analysis['vlan_manipulation_count'] > 0):
            self.logger.debug("QinQ Type 2A: LEAF full range manipulation (1-4094)")
            return BridgeDomainType.QINQ_SINGLE_BD, 95
        
        # Type 2B: LEAF Specific Range QinQ (specific ranges + manipulation)
        elif (len(analysis['vlan_ranges']) > 0 and 
              analysis['vlan_manipulation_count'] > 0 and
              analysis['full_ranges_1_4094'] == 0):
            self.logger.debug("QinQ Type 2B: LEAF specific range manipulation")
            return BridgeDomainType.QINQ_MULTI_BD, 90
        
        # Type 3: Hybrid (mixed patterns within same bridge domain)
        elif self._detect_hybrid_pattern(analysis):
            self.logger.debug("QinQ Type 3: Hybrid pattern detected")
            return BridgeDomainType.HYBRID, 75
        
        # Fallback to Type 1 (should rarely happen)
        else:
            self.logger.debug("QinQ detected but pattern unclear - using Type 1 as fallback")
            return BridgeDomainType.DOUBLE_TAGGED, 60
    
    def _detect_hybrid_pattern(self, analysis: Dict) -> bool:
        """
        Detect Type 3 Hybrid pattern: mixed interface configurations within same bridge domain
        """
        
        # Check if we have both manipulation and non-manipulation interfaces
        has_manipulation_interfaces = analysis['vlan_manipulation_count'] > 0
        has_static_double_tag = len(analysis['outer_inner_tag_pairs']) > 0
        has_simple_single_tag = len(analysis['single_vlan_configs']) > 0
        
        # Hybrid pattern: combination of different interface types in same BD
        is_hybrid = (
            # Mix of manipulation + static double-tag
            (has_manipulation_interfaces and has_static_double_tag) or
            # Mix of manipulation + simple single-tag + static double-tag
            (has_manipulation_interfaces and has_simple_single_tag and has_static_double_tag)
        )
        
        if is_hybrid:
            self.logger.debug(f"Hybrid pattern detected: manipulation={has_manipulation_interfaces}, "
                            f"static_double={has_static_double_tag}, simple_single={has_simple_single_tag}")
        
        return is_hybrid
    
    def _detect_port_mode(self, analysis: Dict) -> bool:
        """
        Detect Type 5 Port-Mode: physical interfaces without VLAN configuration
        """
        
        # Check if all interfaces are physical (no subinterface suffix like .100)
        all_physical = all(
            '.' not in iface_detail.get('interface_name', '')
            for iface_detail in analysis['interface_details']
        )
        
        # Check if no VLAN configuration exists
        no_vlan_config = (
            len(analysis['single_vlan_configs']) == 0 and
            len(analysis['vlan_ranges']) == 0 and
            len(analysis['vlan_lists']) == 0 and
            len(analysis['outer_inner_tag_pairs']) == 0 and
            analysis['vlan_manipulation_count'] == 0
        )
        
        # Check if l2-service is enabled (from interface details)
        has_l2_service = any(
            iface_detail.get('l2_service_enabled', False)
            for iface_detail in analysis['interface_details']
        )
        
        is_port_mode = all_physical and no_vlan_config and has_l2_service
        
        if is_port_mode:
            self.logger.debug("Port-Mode detected: physical interfaces, no VLAN config, l2-service enabled")
        elif not all_physical:
            self.logger.debug(f"Not Port-Mode: not all physical interfaces")
        elif not no_vlan_config:
            self.logger.debug(f"Not Port-Mode: has VLAN configuration")
        elif not has_l2_service:
            self.logger.debug(f"Not Port-Mode: no l2-service enabled")
        
        return is_port_mode
    
    def _detect_empty_bridge_domain(self, analysis: Dict) -> bool:
        """
        Detect empty bridge domains: bridge domains with no interfaces assigned
        """
        
        # Check if there are no interface details
        no_interfaces = len(analysis['interface_details']) == 0
        
        # Check if all interfaces have no VLAN configuration
        no_vlan_config = (
            len(analysis['single_vlan_configs']) == 0 and
            len(analysis['vlan_ranges']) == 0 and
            len(analysis['vlan_lists']) == 0 and
            len(analysis['outer_inner_tag_pairs']) == 0 and
            analysis['vlan_manipulation_count'] == 0
        )
        
        is_empty = no_interfaces or (len(analysis['interface_details']) > 0 and no_vlan_config)
        
        if is_empty:
            self.logger.debug("Empty bridge domain detected: no interfaces or no VLAN configuration")
        
        return is_empty
    
    def _apply_classification_rules(self, analysis: Dict) -> Tuple[BridgeDomainType, int]:
        """Apply classification rules based on official DNAAS types 1-5."""
        
        # Rule 0: Empty Bridge Domain (check first)
        if self._detect_empty_bridge_domain(analysis):
            return BridgeDomainType.EMPTY_BRIDGE_DOMAIN, 10
        
        # Rule 1: Type 5 - Port-Mode (highest confidence, check first)
        if self._detect_port_mode(analysis):
            return BridgeDomainType.PORT_MODE, 95
        
        # Rule 2: Q-in-Q Detection (All DNAAS Types 1, 2A, 2B, 3)
        
        # Check for legitimate QinQ indicators
        has_legitimate_qinq = False
        qinq_confidence = 0
        
        # CONSERVATIVE QinQ Detection - Require definitive evidence
        
        # 1.1: DEFINITIVE: VLAN manipulation (push/pop operations) + QinQ evidence
        # FIXED: Don't require multiple VLANs - Type 2B QinQ can have single outer VLAN with ranges
        if (analysis['push_outer_tag_count'] > 0 and 
            analysis['pop_operations_count'] > 0 and
            (len(analysis['outer_inner_tag_pairs']) > 0 or    # Has actual double tags, OR
             len(analysis['vlan_ranges']) > 0 or              # Has VLAN ranges (Type 2A/2B pattern), OR
             analysis['full_ranges_1_4094'] > 0)):            # Has full range (Type 2A pattern)
            has_legitimate_qinq = True
            qinq_confidence = 95
            self.logger.debug("QinQ detected: VLAN manipulation with push/pop operations + QinQ evidence (ranges/tags)")
        
        # 1.2: DEFINITIVE: Outer/inner tag pairs with different values (don't require multiple VLANs)
        elif len(analysis['outer_inner_tag_pairs']) > 0:
            # All pairs in outer_inner_tag_pairs are already validated as having outer != inner
            # during the analysis phase, so we can trust them directly
            if analysis['outer_inner_tag_pairs']:
                has_legitimate_qinq = True
                qinq_confidence = 90
                self.logger.debug(f"QinQ detected: {len(analysis['outer_inner_tag_pairs'])} valid outer/inner pairs (outer≠inner)")
            else:
                # All pairs have outer=inner, this is likely single VLAN misclassified
                self.logger.debug("Rejected QinQ: all outer/inner pairs have same values (outer=inner)")
        
        # 1.3: DEFINITIVE: VLAN ranges with manipulation AND multiple VLANs (Type 2A/2B patterns)
        elif (analysis['vlan_manipulation_count'] > 0 and 
              len(analysis['vlan_ranges']) > 0 and
              len(analysis['unique_vlan_ids']) > 1):
            has_legitimate_qinq = True
            qinq_confidence = 85
            self.logger.debug("QinQ detected: VLAN ranges with manipulation and multiple VLANs")
        
        # 1.4: CONSERVATIVE: Full range 1-4094 only if combined with other indicators
        elif (analysis['full_ranges_1_4094'] > 0 and 
              (analysis['vlan_manipulation_count'] > 0 or len(analysis['unique_vlan_ids']) > 1)):
            has_legitimate_qinq = True  
            qinq_confidence = 80
            self.logger.debug("QinQ detected: Full VLAN range (1-4094) with additional QinQ indicators")
        
        if has_legitimate_qinq:
            # Determine specific QinQ type based on DNAAS classification
            qinq_type, qinq_confidence = self._determine_specific_qinq_type(analysis)
            return qinq_type, qinq_confidence
        
        # Rule 6: Type 4B - VLAN Range (single-tagged with range)
        if len(analysis['vlan_ranges']) > 0 and analysis['vlan_manipulation_count'] == 0:
            return BridgeDomainType.SINGLE_TAGGED_RANGE, 85
        
        # Rule 7: Type 4B - VLAN List (single-tagged with list)
        if len(analysis['vlan_lists']) > 0 and analysis['vlan_manipulation_count'] == 0:
            return BridgeDomainType.SINGLE_TAGGED_LIST, 85
        
        # Rule 8: Type 4A - Single VLAN Detection
        if len(analysis['single_vlan_configs']) > 0:
            unique_vlans = set(analysis['single_vlan_configs'])
            if len(unique_vlans) == 1:
                return BridgeDomainType.SINGLE_TAGGED, 90
            else:
                # Multiple different VLANs - still Type 4A but lower confidence
                return BridgeDomainType.SINGLE_TAGGED, 70
        
        # Rule 9: Default Type 4A (Very low confidence)
        return BridgeDomainType.SINGLE_TAGGED, 30
    
    def get_classification_explanation(self, bd_type: BridgeDomainType, analysis: Dict) -> str:
        """Generate human-readable explanation of classification."""
        
        explanations = {
            BridgeDomainType.QINQ: "Q-in-Q configuration with VLAN manipulation or outer/inner tags",
            BridgeDomainType.VLAN_RANGE: "VLAN range configuration without manipulation",
            BridgeDomainType.VLAN_LIST: "VLAN list configuration without manipulation", 
            BridgeDomainType.SINGLE_VLAN: "Single VLAN configuration"
        }
        
        base_explanation = explanations.get(bd_type, "Unknown classification")
        
        # Add specific details
        details = []
        if analysis['vlan_manipulation_count'] > 0:
            details.append(f"{analysis['vlan_manipulation_count']} interfaces with VLAN manipulation")
        
        if analysis['full_ranges_1_4094'] > 0:
            details.append(f"{analysis['full_ranges_1_4094']} interfaces with full VLAN range (1-4094)")
        
        if len(analysis['outer_inner_tag_pairs']) > 0:
            details.append(f"{len(analysis['outer_inner_tag_pairs'])} outer/inner tag pairs")
        
        if details:
            return f"{base_explanation} ({', '.join(details)})"
        else:
            return base_explanation

if __name__ == "__main__":
    # Test the classifier
    classifier = BridgeDomainClassifier()
    
    # Test cases based on real configuration patterns
    test_cases = [
        {
            'name': 'test_qinq_single_bd',
            'interfaces': [
                {
                    'name': 'bundle-445.100',
                    'type': 'subinterface',
                    'vlan_range': '1-4094',
                    'vlan_manipulation': {
                        'ingress': 'push outer-tag 445',
                        'egress': 'pop outer-tag'
                    }
                }
            ]
        },
        {
            'name': 'test_single_vlan',
            'interfaces': [
                {
                    'name': 'ge100-0/0/1.100',
                    'type': 'subinterface', 
                    'vlan_id': 100
                }
            ]
        },
        {
            'name': 'test_port_mode',
            'interfaces': [
                {
                    'name': 'ge100-0/0/1',
                    'type': 'physical',
                    'l2_service': True
                }
            ]
        }
    ]
    
    print("Bridge Domain Classifier Test")
    print("=" * 50)
    
    for test_case in test_cases:
        bd_type, confidence, analysis = classifier.classify_bridge_domain(
            test_case['name'], 
            test_case['interfaces']
        )
        
        explanation = classifier.get_classification_explanation(bd_type, analysis)
        
        print(f"\nTest Case: {test_case['name']}")
        print(f"  Classification: {bd_type}")
        print(f"  Confidence: {confidence}%")
        print(f"  Explanation: {explanation}")
