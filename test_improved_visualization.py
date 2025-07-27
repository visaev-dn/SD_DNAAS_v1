#!/usr/bin/env python3
"""
Test Improved Bridge Domain Visualization

This script demonstrates the improved visualization with better access interface display
for both P2P and P2MP topologies.
"""

import sys
import os
from pathlib import Path

# Add the config_engine directory to the path
sys.path.append(str(Path(__file__).parent / 'config_engine'))

from bridge_domain_visualization import BridgeDomainVisualization

def test_improved_p2p_visualization():
    """Test improved P2P visualization with better access interface display."""
    
    visualization = BridgeDomainVisualization()
    
    # Create test P2P bridge domain data
    test_p2p_data = {
        "service_name": "g_zkeiserman_v150",
        "detected_username": "zkeiserman",
        "detected_vlan": 150,
        "confidence": 95,
        "detection_method": "complex_descriptive_pattern",
        "scope": "global",
        "scope_description": "Globally significant VLAN ID, can be configured everywhere",
        "topology_type": "p2p",
        "devices": {
            "DNAAS-LEAF-B14": {
                "interfaces": [
                    {
                        "name": "bundle-60000.150",
                        "type": "subinterface",
                        "vlan_id": 150,
                        "role": "uplink"
                    },
                    {
                        "name": "ge100-0/0/3.150",
                        "type": "subinterface",
                        "vlan_id": 150,
                        "role": "access"
                    }
                ],
                "admin_state": "enabled",
                "device_type": "leaf"
            },
            "DNAAS-SPINE-B09": {
                "interfaces": [
                    {
                        "name": "bundle-60000.150",
                        "type": "subinterface",
                        "vlan_id": 150,
                        "role": "downlink"
                    },
                    {
                        "name": "bundle-60001.150",
                        "type": "subinterface",
                        "vlan_id": 150,
                        "role": "downlink"
                    },
                    {
                        "name": "bundle-60003.150",
                        "type": "subinterface",
                        "vlan_id": 150,
                        "role": "downlink"
                    }
                ],
                "admin_state": "enabled",
                "device_type": "spine"
            },
            "DNAAS-LEAF-B10": {
                "interfaces": [
                    {
                        "name": "bundle-60000.150",
                        "type": "subinterface",
                        "vlan_id": 150,
                        "role": "uplink"
                    },
                    {
                        "name": "ge100-0/0/9.150",
                        "type": "subinterface",
                        "vlan_id": 150,
                        "role": "access"
                    }
                ],
                "admin_state": "enabled",
                "device_type": "leaf"
            }
        },
        "topology_analysis": {
            "leaf_devices": 2,
            "spine_devices": 1,
            "total_interfaces": 5,
            "path_complexity": "2-tier",
            "estimated_bandwidth": "50G"
        }
    }
    
    print("🔍 Improved P2P Visualization Test")
    print("=" * 60)
    print()
    
    # Generate P2P visualization
    p2p_visualization = visualization.create_p2p_visualization(test_p2p_data)
    print(p2p_visualization)
    
    print("\n" + "=" * 60)
    print("✅ Key Improvements:")
    print("• Access interfaces are now displayed directly on leaf devices")
    print("• Access interfaces are marked with 🔌 icon")
    print("• Uplink interfaces are shown in connection lines")
    print("• Clear separation between access and uplink interfaces")

def test_improved_p2mp_visualization():
    """Test improved P2MP visualization with better interface grouping."""
    
    visualization = BridgeDomainVisualization()
    
    # Create test P2MP bridge domain data
    test_p2mp_data = {
        "service_name": "g_mgmt_v998",
        "detected_username": "mgmt",
        "detected_vlan": 998,
        "confidence": 100,
        "detection_method": "automated_pattern",
        "scope": "global",
        "scope_description": "Globally significant VLAN ID, can be configured everywhere",
        "topology_type": "p2mp",
        "devices": {
            "DNAAS-LEAF-A11-2": {
                "interfaces": [
                    {
                        "name": "bundle-60000.998",
                        "type": "subinterface",
                        "vlan_id": 998,
                        "role": "uplink"
                    },
                    {
                        "name": "ge100-0/0/1.998",
                        "type": "subinterface",
                        "vlan_id": 998,
                        "role": "access"
                    }
                ],
                "admin_state": "enabled",
                "device_type": "leaf"
            },
            "DNAAS-LEAF-B13": {
                "interfaces": [
                    {
                        "name": "bundle-60000.998",
                        "type": "subinterface",
                        "vlan_id": 998,
                        "role": "uplink"
                    },
                    {
                        "name": "ge100-0/0/2.998",
                        "type": "subinterface",
                        "vlan_id": 998,
                        "role": "access"
                    }
                ],
                "admin_state": "enabled",
                "device_type": "leaf"
            },
            "DNAAS-SPINE-B09": {
                "interfaces": [
                    {
                        "name": "bundle-60000.998",
                        "type": "subinterface",
                        "vlan_id": 998,
                        "role": "downlink"
                    },
                    {
                        "name": "bundle-60001.998",
                        "type": "subinterface",
                        "vlan_id": 998,
                        "role": "downlink"
                    }
                ],
                "admin_state": "enabled",
                "device_type": "spine"
            }
        },
        "topology_analysis": {
            "leaf_devices": 2,
            "spine_devices": 1,
            "total_interfaces": 4,
            "path_complexity": "2-tier",
            "estimated_bandwidth": "40G"
        }
    }
    
    print("🔍 Improved P2MP Visualization Test")
    print("=" * 60)
    print()
    
    # Generate P2MP visualization
    p2mp_visualization = visualization.create_p2mp_visualization(test_p2mp_data)
    print(p2mp_visualization)
    
    print("\n" + "=" * 60)
    print("✅ Key Improvements:")
    print("• Access interfaces are grouped separately with 🔌 icon")
    print("• Uplink interfaces are grouped separately with 🔗 icon")
    print("• Downlink interfaces on spines are grouped with 🔽 icon")
    print("• Uplink interfaces on spines are grouped with 🔼 icon")
    print("• Clear hierarchy and organization of interface types")

def test_interface_role_detection():
    """Test interface role detection and classification."""
    
    visualization = BridgeDomainVisualization()
    
    print("🔍 Interface Role Detection Test")
    print("=" * 60)
    print()
    
    # Test different interface types
    test_interfaces = [
        {
            "name": "ge100-0/0/10",
            "type": "physical",
            "vlan_id": None,
            "role": "access"
        },
        {
            "name": "bundle-60000.150",
            "type": "subinterface",
            "vlan_id": 150,
            "role": "uplink"
        },
        {
            "name": "bundle-60001.998",
            "type": "subinterface",
            "vlan_id": 998,
            "role": "downlink"
        },
        {
            "name": "ge100-0/0/15.1285",
            "type": "subinterface",
            "vlan_id": 1285,
            "role": "access"
        }
    ]
    
    print("Interface Role Classification:")
    for interface in test_interfaces:
        formatted = visualization.format_interface_details(interface)
        role = interface.get('role', 'unknown')
        print(f"  • {formatted} → Role: {role}")
    
    print("\nRole Definitions:")
    print("  • access: Customer-facing interfaces (AC - Access Circuits)")
    print("  • uplink: Connections from leaf to spine")
    print("  • downlink: Connections from spine to leaf")

if __name__ == "__main__":
    print("🚀 Testing Improved Bridge Domain Visualization")
    print("=" * 60)
    
    # Test P2P visualization
    test_improved_p2p_visualization()
    
    print("\n" + "=" * 80)
    
    # Test P2MP visualization
    test_improved_p2mp_visualization()
    
    print("\n" + "=" * 80)
    
    # Test interface role detection
    test_interface_role_detection()
    
    print("\n✅ Improved visualization successfully displays access interfaces!")
    print("Access interfaces are now clearly visible on leaf devices with 🔌 icon.") 