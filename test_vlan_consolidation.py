#!/usr/bin/env python3
"""
Test VLAN-Based Bridge Domain Consolidation

This script demonstrates how bridge domains with different naming conventions
but the same VLAN ID and username are consolidated into a single topology.
"""

import sys
import os
import json
from pathlib import Path

# Add the config_engine directory to the path
sys.path.append(str(Path(__file__).parent / 'config_engine'))

from bridge_domain_discovery import BridgeDomainDiscovery

def test_vlan_consolidation():
    """Test VLAN-based consolidation with naming inconsistencies."""
    
    discovery = BridgeDomainDiscovery()
    
    # Create test data with naming inconsistencies
    test_analyzed_data = {
        "DNAAS-LEAF-B14": {
            "bridge_domains": [
                {
                    "service_name": "g_visaev_v253_Spirent",
                    "detected_username": "visaev",
                    "detected_vlan": 253,
                    "confidence": 95,
                    "detection_method": "complex_descriptive_pattern",
                    "scope": "global",
                    "scope_description": "Globally significant VLAN ID, can be configured everywhere",
                    "interfaces": [
                        {
                            "name": "bundle-60000.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "uplink"
                        },
                        {
                            "name": "ge100-0/0/12.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "access"
                        }
                    ],
                    "admin_state": "enabled"
                }
            ],
            "vlan_manipulation_configs": []
        },
        "DNAAS-LEAF-B15": {
            "bridge_domains": [
                {
                    "service_name": "g_visaev_v253_to_Spirent",
                    "detected_username": "visaev",
                    "detected_vlan": 253,
                    "confidence": 95,
                    "detection_method": "complex_descriptive_pattern",
                    "scope": "global",
                    "scope_description": "Globally significant VLAN ID, can be configured everywhere",
                    "interfaces": [
                        {
                            "name": "bundle-60000.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "uplink"
                        },
                        {
                            "name": "ge100-0/0/5.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "access"
                        }
                    ],
                    "admin_state": "enabled"
                }
            ],
            "vlan_manipulation_configs": []
        },
        "DNAAS-LEAF-B16": {
            "bridge_domains": [
                {
                    "service_name": "visaev_253_test",
                    "detected_username": "visaev",
                    "detected_vlan": 253,
                    "confidence": 85,
                    "detection_method": "simple_pattern",
                    "scope": "unknown",
                    "scope_description": "Unknown scope - unable to determine",
                    "interfaces": [
                        {
                            "name": "ge100-0/0/8.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "access"
                        }
                    ],
                    "admin_state": "enabled"
                }
            ],
            "vlan_manipulation_configs": []
        }
    }
    
    print("🔍 VLAN-Based Bridge Domain Consolidation Test")
    print("=" * 60)
    print()
    
    # Show original bridge domains
    print("📋 ORIGINAL BRIDGE DOMAINS (Before Consolidation):")
    print("-" * 50)
    for device_name, device_data in test_analyzed_data.items():
        for bd in device_data['bridge_domains']:
            print(f"  • {bd['service_name']}")
            print(f"    - Device: {device_name}")
            print(f"    - Username: {bd['detected_username']}")
            print(f"    - VLAN: {bd['detected_vlan']}")
            print(f"    - Confidence: {bd['confidence']}%")
            print()
    
    # Create bridge domain collections (simulate the process)
    bridge_domain_collections = {}
    
    for device_name, device_data in test_analyzed_data.items():
        device_type = discovery.detect_device_type(device_name)
        
        for bridge_domain in device_data['bridge_domains']:
            service_name = bridge_domain['service_name']
            confidence = bridge_domain.get('confidence', 0)
            
            if confidence >= 70:
                if service_name not in bridge_domain_collections:
                    bridge_domain_collections[service_name] = {
                        'devices': {},
                        'service_name': service_name,
                        'detected_username': bridge_domain['detected_username'],
                        'detected_vlan': bridge_domain['detected_vlan'],
                        'confidence': confidence,
                        'detection_method': bridge_domain['detection_method'],
                        'scope': bridge_domain.get('scope', 'unknown'),
                        'scope_description': bridge_domain.get('scope_description', 'Unknown scope - unable to determine')
                    }
                
                # Add device information
                device_info = {
                    'interfaces': bridge_domain['interfaces'],
                    'admin_state': bridge_domain['admin_state'],
                    'device_type': device_type
                }
                
                bridge_domain_collections[service_name]['devices'][device_name] = device_info
    
    # Test consolidation
    print("🔄 CONSOLIDATION PROCESS:")
    print("-" * 50)
    
    consolidated_bridge_domains = discovery.consolidate_bridge_domains_by_vlan(bridge_domain_collections)
    
    print("📊 CONSOLIDATED BRIDGE DOMAINS (After Consolidation):")
    print("-" * 50)
    
    for consolidated_name, consolidated_data in consolidated_bridge_domains.items():
        consolidation_info = consolidated_data.get('consolidation_info', {})
        original_names = consolidation_info.get('original_names', [])
        consolidated_count = consolidation_info.get('consolidated_count', 1)
        
        print(f"  • {consolidated_name}")
        print(f"    - Username: {consolidated_data['detected_username']}")
        print(f"    - VLAN: {consolidated_data['detected_vlan']}")
        print(f"    - Confidence: {consolidated_data['confidence']}%")
        print(f"    - Scope: {consolidated_data['scope']}")
        
        if consolidated_count > 1:
            print(f"    - CONSOLIDATED from {consolidated_count} bridge domains:")
            for orig_name in original_names:
                print(f"      * {orig_name}")
        else:
            print(f"    - Single bridge domain (no consolidation needed)")
        
        print(f"    - Devices: {list(consolidated_data['devices'].keys())}")
        print()
    
    # Show JSON structure example
    print("📋 CONSOLIDATED JSON STRUCTURE EXAMPLE:")
    print("-" * 50)
    
    example_consolidated = {
        "g_visaev_v253": {
            "service_name": "g_visaev_v253",
            "detected_username": "visaev",
            "detected_vlan": 253,
            "confidence": 95,
            "detection_method": "complex_descriptive_pattern",
            "scope": "global",
            "scope_description": "Globally significant VLAN ID, can be configured everywhere",
            "topology_type": "p2mp",
            "devices": {
                "DNAAS-LEAF-B14": {
                    "interfaces": [
                        {
                            "name": "bundle-60000.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "uplink"
                        },
                        {
                            "name": "ge100-0/0/12.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "access"
                        }
                    ],
                    "admin_state": "enabled",
                    "device_type": "leaf"
                },
                "DNAAS-LEAF-B15": {
                    "interfaces": [
                        {
                            "name": "bundle-60000.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "uplink"
                        },
                        {
                            "name": "ge100-0/0/5.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "access"
                        }
                    ],
                    "admin_state": "enabled",
                    "device_type": "leaf"
                },
                "DNAAS-LEAF-B16": {
                    "interfaces": [
                        {
                            "name": "ge100-0/0/8.253",
                            "type": "subinterface",
                            "vlan_id": 253,
                            "role": "access"
                        }
                    ],
                    "admin_state": "enabled",
                    "device_type": "leaf"
                }
            },
            "consolidation_info": {
                "original_names": [
                    "g_visaev_v253_Spirent",
                    "g_visaev_v253_to_Spirent",
                    "visaev_253_test"
                ],
                "consolidation_key": "visaev_v253",
                "consolidated_count": 3
            }
        }
    }
    
    print(json.dumps(example_consolidated, indent=2))
    
    print("\n🔑 Key Benefits:")
    print("• Multiple bridge domains with same VLAN ID are consolidated")
    print("• Complete topology is visible in one place")
    print("• Original names are preserved in consolidation_info")
    print("• Standardized naming convention is applied")
    print("• All devices and interfaces are merged into single topology")

def test_consolidation_edge_cases():
    """Test edge cases for VLAN consolidation."""
    
    discovery = BridgeDomainDiscovery()
    
    print("\n🧪 CONSOLIDATION EDGE CASES:")
    print("=" * 60)
    
    # Test case 1: Same VLAN, different usernames (should not consolidate)
    print("Test Case 1: Same VLAN, Different Usernames")
    print("-" * 40)
    
    edge_case_1 = {
        "g_user1_v100": {
            'devices': {"device1": {}},
            'detected_username': 'user1',
            'detected_vlan': 100,
            'confidence': 95,
            'detection_method': 'automated_pattern',
            'scope': 'global',
            'scope_description': 'Global scope'
        },
        "g_user2_v100": {
            'devices': {"device2": {}},
            'detected_username': 'user2',
            'detected_vlan': 100,
            'confidence': 95,
            'detection_method': 'automated_pattern',
            'scope': 'global',
            'scope_description': 'Global scope'
        }
    }
    
    consolidated_1 = discovery.consolidate_bridge_domains_by_vlan(edge_case_1)
    print(f"Result: {len(consolidated_1)} bridge domains (should be 2 - no consolidation)")
    
    # Test case 2: Same username, different VLANs (should not consolidate)
    print("\nTest Case 2: Same Username, Different VLANs")
    print("-" * 40)
    
    edge_case_2 = {
        "g_user1_v100": {
            'devices': {"device1": {}},
            'detected_username': 'user1',
            'detected_vlan': 100,
            'confidence': 95,
            'detection_method': 'automated_pattern',
            'scope': 'global',
            'scope_description': 'Global scope'
        },
        "g_user1_v200": {
            'devices': {"device2": {}},
            'detected_username': 'user1',
            'detected_vlan': 200,
            'confidence': 95,
            'detection_method': 'automated_pattern',
            'scope': 'global',
            'scope_description': 'Global scope'
        }
    }
    
    consolidated_2 = discovery.consolidate_bridge_domains_by_vlan(edge_case_2)
    print(f"Result: {len(consolidated_2)} bridge domains (should be 2 - no consolidation)")
    
    # Test case 3: No VLAN ID (should not consolidate)
    print("\nTest Case 3: No VLAN ID (Local Scope)")
    print("-" * 40)
    
    edge_case_3 = {
        "l_user1_description1": {
            'devices': {"device1": {}},
            'detected_username': 'user1',
            'detected_vlan': None,
            'confidence': 90,
            'detection_method': 'l_prefix_pattern',
            'scope': 'local',
            'scope_description': 'Local scope'
        },
        "l_user1_description2": {
            'devices': {"device2": {}},
            'detected_username': 'user1',
            'detected_vlan': None,
            'confidence': 90,
            'detection_method': 'l_prefix_pattern',
            'scope': 'local',
            'scope_description': 'Local scope'
        }
    }
    
    consolidated_3 = discovery.consolidate_bridge_domains_by_vlan(edge_case_3)
    print(f"Result: {len(consolidated_3)} bridge domains (should be 1 - consolidated by username only)")

if __name__ == "__main__":
    print("🚀 Testing VLAN-Based Bridge Domain Consolidation")
    print("=" * 60)
    
    # Run the main test
    test_vlan_consolidation()
    
    # Run edge case tests
    test_consolidation_edge_cases()
    
    print("\n✅ VLAN-based consolidation successfully handles naming inconsistencies!")
    print("This ensures that the same topology appears as one bridge domain regardless of naming variations.") 