#!/usr/bin/env python3
"""
Test L-Prefix Pattern Handling

This script demonstrates the enhanced service name analyzer with L-prefix pattern support.
It shows how L-prefix patterns are handled with local scope and proper VLAN ID extraction.
"""

import sys
import os
from pathlib import Path

# Add the config_engine directory to the path
sys.path.append(str(Path(__file__).parent / 'config_engine'))

from service_name_analyzer import ServiceNameAnalyzer

def test_l_prefix_patterns():
    """Test L-prefix pattern handling with the provided examples."""
    
    analyzer = ServiceNameAnalyzer()
    
    # Test cases from the user's examples
    test_cases = [
        {
            'name': 'l_gshafir_ISIS_R51_to_IXIA02',
            'expected_username': 'gshafir',
            'expected_vlan': None,
            'expected_scope': 'local',
            'description': 'L-prefix without VLAN - local scope'
        },
        {
            'name': 'l_cchiriac_v1285_sysp65-kmv94_mxvmx5',
            'expected_username': 'cchiriac',
            'expected_vlan': 1285,
            'expected_scope': 'local',
            'description': 'L-prefix with VLAN - local scope'
        },
        # Additional test cases
        {
            'name': 'l_user_v123',
            'expected_username': 'user',
            'expected_vlan': 123,
            'expected_scope': 'local',
            'description': 'L-prefix simple VLAN - local scope'
        },
        {
            'name': 'l_test_description_only',
            'expected_username': 'test',
            'expected_vlan': None,
            'expected_scope': 'local',
            'description': 'L-prefix description only - local scope'
        }
    ]
    
    print("🔍 L-Prefix Pattern Analysis Test")
    print("=" * 60)
    print()
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['description']}")
        print(f"Input: {test_case['name']}")
        
        # Analyze the service name
        result = analyzer.extract_service_info(test_case['name'])
        
        # Check results
        username_match = result['username'] == test_case['expected_username']
        vlan_match = result['vlan_id'] == test_case['expected_vlan']
        scope_match = result['scope'] == test_case['expected_scope']
        
        print(f"  ✅ Username: {result['username']} (expected: {test_case['expected_username']})")
        print(f"  ✅ VLAN ID: {result['vlan_id']} (expected: {test_case['expected_vlan']})")
        print(f"  ✅ Scope: {result['scope']} (expected: {test_case['expected_scope']})")
        print(f"  ✅ Confidence: {result['confidence']}%")
        print(f"  ✅ Method: {result['method']}")
        print(f"  ✅ Description: {result['description']}")
        print(f"  ✅ Scope Description: {analyzer.get_scope_description(result['scope'])}")
        
        if username_match and vlan_match and scope_match:
            print("  🎉 PASS")
        else:
            print("  ❌ FAIL")
            all_passed = False
        
        print()
    
    # Test scope distribution
    print("📊 Scope Distribution Analysis")
    print("-" * 40)
    
    test_names = [
        'l_gshafir_ISIS_R51_to_IXIA02',
        'l_cchiriac_v1285_sysp65-kmv94_mxvmx5',
        'g_visaev_v253',  # Global scope for comparison
        'M_kazakov_1360',  # Manual scope for comparison
        'unknown_pattern_123'  # Unknown scope for comparison
    ]
    
    stats = analyzer.get_pattern_statistics(test_names)
    print(f"Total names: {stats['total_names']}")
    print(f"Scope distribution: {stats['scope_distribution']}")
    print(f"Pattern matches: {stats['pattern_matches']}")
    print(f"Confidence distribution: {stats['confidence_distribution']}")
    
    # Test suggestions
    print("\n💡 Improvement Suggestions")
    print("-" * 40)
    suggestions = analyzer.suggest_improvements(test_names)
    print(f"High confidence percentage: {suggestions['high_confidence_percentage']:.1f}%")
    print(f"Scope analysis: {suggestions['scope_analysis']}")
    print(f"Issues found: {suggestions['issues_found']}")
    print(f"Recommendations: {suggestions['recommendations']}")
    
    print()
    print("=" * 60)
    if all_passed:
        print("🎉 All L-prefix pattern tests PASSED!")
    else:
        print("❌ Some tests FAILED!")
    
    return all_passed

def test_json_structure_example():
    """Show how the JSON structure would look with L-prefix patterns."""
    
    print("\n📋 JSON Structure Example with L-Prefix Patterns")
    print("=" * 60)
    
    example_json = {
        "bridge_domains": {
            "l_gshafir_ISIS_R51_to_IXIA02": {
                "service_name": "l_gshafir_ISIS_R51_to_IXIA02",
                "detected_username": "gshafir",
                "detected_vlan": None,
                "confidence": 90,
                "detection_method": "l_prefix_pattern",
                "scope": "local",
                "scope_description": "Local scope - configured locally on a leaf and bridge local AC interfaces",
                "topology_type": "p2p",
                "devices": {
                    "DNAAS-LEAF-A11-2": {
                        "interfaces": [
                            {
                                "name": "ge100-0/0/10",
                                "type": "physical",
                                "vlan_id": None,
                                "role": "access"
                            }
                        ],
                        "admin_state": "enabled",
                        "device_type": "leaf"
                    }
                },
                "topology_analysis": {
                    "leaf_devices": 1,
                    "spine_devices": 0,
                    "total_interfaces": 1,
                    "path_complexity": "local",
                    "estimated_bandwidth": "10G"
                }
            },
            "l_cchiriac_v1285_sysp65-kmv94_mxvmx5": {
                "service_name": "l_cchiriac_v1285_sysp65-kmv94_mxvmx5",
                "detected_username": "cchiriac",
                "detected_vlan": 1285,
                "confidence": 90,
                "detection_method": "l_prefix_vlan_pattern",
                "scope": "local",
                "scope_description": "Local scope - configured locally on a leaf and bridge local AC interfaces",
                "topology_type": "p2p",
                "devices": {
                    "DNAAS-LEAF-B13": {
                        "interfaces": [
                            {
                                "name": "ge100-0/0/15.1285",
                                "type": "subinterface",
                                "vlan_id": 1285,
                                "role": "access"
                            }
                        ],
                        "admin_state": "enabled",
                        "device_type": "leaf"
                    }
                },
                "topology_analysis": {
                    "leaf_devices": 1,
                    "spine_devices": 0,
                    "total_interfaces": 1,
                    "path_complexity": "local",
                    "estimated_bandwidth": "10G"
                }
            }
        },
        "topology_summary": {
            "scope_distribution": {
                "global": 350,
                "local": 82,
                "manual": 0,
                "unknown": 0
            }
        }
    }
    
    import json
    print(json.dumps(example_json, indent=2))
    
    print("\n🔑 Key Features:")
    print("• L-prefix patterns are marked with 'scope': 'local'")
    print("• VLAN ID can be null for pure local patterns")
    print("• Scope description explains the local configuration purpose")
    print("• Topology type is typically 'p2p' for local configurations")
    print("• Path complexity is 'local' for single-device configurations")

if __name__ == "__main__":
    print("🚀 Testing L-Prefix Pattern Handling")
    print("=" * 60)
    
    # Run the tests
    success = test_l_prefix_patterns()
    
    # Show JSON structure example
    test_json_structure_example()
    
    if success:
        print("\n✅ All tests completed successfully!")
        print("L-prefix patterns are now properly handled with local scope.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.") 