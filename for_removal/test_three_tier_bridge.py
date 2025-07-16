#!/usr/bin/env python3
"""
Test script to verify three-tier bridge domain builder functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.bridge_domain_builder import BridgeDomainBuilder

def test_three_tier_bridge_builder():
    """Test the bridge domain builder with three-tier architecture."""
    print("=== Testing Three-Tier Bridge Domain Builder ===")
    
    # Initialize the builder
    builder = BridgeDomainBuilder()
    
    if not builder.topology_data:
        print("❌ No topology data available. Please run topology discovery first.")
        return False
    
    print("✅ Topology data loaded successfully")
    
    # Test path calculation between remote leaf devices
    test_cases = [
        {
            'source_leaf': 'DNAAS-LEAF-A12',
            'dest_leaf': 'DNAAS-LEAF-C12-A',
            'description': 'Remote leaf devices through different spines'
        },
        {
            'source_leaf': 'DNAAS-LEAF-B01',
            'dest_leaf': 'DNAAS-LEAF-B07',
            'description': 'Leaf devices connected to same spine (standalone)'
        },
        {
            'source_leaf': 'DNAAS-LEAF-F14',
            'dest_leaf': 'DNAAS-LEAF-A15',
            'description': 'Remote leaf devices through super spine'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        print(f"Source: {test_case['source_leaf']}")
        print(f"Destination: {test_case['dest_leaf']}")
        
        # Calculate path
        path = builder.calculate_path(test_case['source_leaf'], test_case['dest_leaf'])
        
        if path:
            print("✅ Path calculated successfully!")
            print(f"Path: {path['source_leaf']} → {path['source_spine']} → {path['superspine']} → {path['dest_spine']} → {path['destination_leaf']}")
            
            print("Path segments:")
            for segment in path['segments']:
                print(f"  {segment['type']}: {segment['source_device']}:{segment['source_interface']} → {segment['dest_device']}:{segment['dest_interface']}")
            
            # Test bridge domain configuration
            configs = builder.build_bridge_domain_config(
                service_name="test_service",
                vlan_id=1000,
                source_leaf=test_case['source_leaf'],
                source_port="ge100-0/0/1",
                dest_leaf=test_case['dest_leaf'],
                dest_port="ge100-0/0/2"
            )
            
            if configs:
                print(f"✅ Bridge domain configuration generated for {len(configs)} devices:")
                for device, config in configs.items():
                    print(f"  📋 {device}: {len(config)} configuration lines")
            else:
                print("❌ Failed to generate bridge domain configuration")
        else:
            print("❌ Failed to calculate path")
    
    print("\n=== Three-Tier Bridge Domain Builder Test Complete ===")
    return True

if __name__ == "__main__":
    test_three_tier_bridge_builder() 