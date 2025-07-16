#!/usr/bin/env python3
"""
Test script for building bridge between DNAAS-LEAF-B15 and DNAAS-LEAF-B16
"""

from config_engine.bridge_domain_builder import BridgeDomainBuilder
import yaml
from pathlib import Path

def test_b15_b16_bridge():
    """Test bridge domain builder between DNAAS-LEAF-B15 and DNAAS-LEAF-B16"""
    print("=== Testing Bridge Domain: DNAAS-LEAF-B15 ↔ DNAAS-LEAF-B16 ===")
    
    # Initialize the builder
    builder = BridgeDomainBuilder()
    
    if not builder.topology_data:
        print("❌ No topology data available. Please run topology discovery first.")
        return False
    
    print("✅ Topology data loaded successfully")
    
    # Check bundle mappings for these devices
    bundle_data = builder.bundle_mappings
    bundles = bundle_data.get('bundles', {})
    
    print("\n--- Bundle Analysis ---")
    
    # Check DNAAS-LEAF-B15 bundles
    b15_bundles = []
    for bundle_name, bundle_info in bundles.items():
        if bundle_info.get('device') == 'DNAAS-LEAF-B15':
            members = bundle_info.get('members', [])
            b15_bundles.append((bundle_name, members))
    
    if b15_bundles:
        print("✅ DNAAS-LEAF-B15 bundles found:")
        for bundle_name, members in b15_bundles:
            print(f"  {bundle_name}: {members}")
    else:
        print("❌ DNAAS-LEAF-B15: No bundles defined")
    
    # Check DNAAS-LEAF-B16 bundles
    b16_bundles = []
    for bundle_name, bundle_info in bundles.items():
        if bundle_info.get('device') == 'DNAAS-LEAF-B16':
            members = bundle_info.get('members', [])
            b16_bundles.append((bundle_name, members))
    
    if b16_bundles:
        print("✅ DNAAS-LEAF-B16 bundles found:")
        for bundle_name, members in b16_bundles:
            print(f"  {bundle_name}: {members}")
    else:
        print("❌ DNAAS-LEAF-B16: No bundles defined")
    
    # Check DNAAS-SPINE-B09 bundles
    spine_b09_bundles = []
    for bundle_name, bundle_info in bundles.items():
        if bundle_info.get('device') == 'DNAAS-SPINE-B09':
            members = bundle_info.get('members', [])
            spine_b09_bundles.append((bundle_name, members))
    
    if spine_b09_bundles:
        print("✅ DNAAS-SPINE-B09 bundles found:")
        for bundle_name, members in spine_b09_bundles[:5]:  # Show first 5
            print(f"  {bundle_name}: {members}")
        if len(spine_b09_bundles) > 5:
            print(f"  ... and {len(spine_b09_bundles)-5} more bundles")
    else:
        print("❌ DNAAS-SPINE-B09: No bundles defined")
    
    print("\n--- Path Calculation Test ---")
    
    # Test path calculation
    path = builder.calculate_path('DNAAS-LEAF-B15', 'DNAAS-LEAF-B16')
    
    if path:
        print("✅ Path calculated successfully!")
        print(f"Path: {path['source_leaf']} → {path['source_spine']} → {path['superspine']} → {path['dest_spine']} → {path['destination_leaf']}")
        
        print("Path segments:")
        for segment in path['segments']:
            print(f"  {segment['type']}: {segment['source_device']}:{segment['source_interface']} → {segment['dest_device']}:{segment['dest_interface']}")
        
        # Test bridge domain configuration with available interfaces
        test_cases = [
            {
                'source_port': 'ge100-0/0/1',   # External interface
                'dest_port': 'ge100-0/0/0',     # External interface
                'description': 'External interfaces'
            },
            {
                'source_port': 'ge100-0/0/9',   # External interface
                'dest_port': 'ge100-0/0/10',    # Bundle member for B16
                'description': 'One external, one bundle member'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Bridge Configuration Test {i}: {test_case['description']} ---")
            print(f"Source: DNAAS-LEAF-B15 ({test_case['source_port']})")
            print(f"Destination: DNAAS-LEAF-B16 ({test_case['dest_port']})")
            
            configs = builder.build_bridge_domain_config(
                service_name="test_b15_b16",
                vlan_id=1000,
                source_leaf='DNAAS-LEAF-B15',
                source_port=test_case['source_port'],
                dest_leaf='DNAAS-LEAF-B16',
                dest_port=test_case['dest_port']
            )
            
            if configs:
                print(f"✅ Bridge domain configuration generated for {len(configs)} devices:")
                for device, config in configs.items():
                    print(f"  📋 {device}: {len(config)} configuration lines")
                    if config:
                        print("    Sample config:")
                        for line in config[:3]:
                            print(f"      {line}")
                        if len(config) > 3:
                            print(f"      ... and {len(config)-3} more lines")
            else:
                print("❌ Failed to generate bridge domain configuration")
    else:
        print("❌ Failed to calculate path")
    
    print("\n=== Bridge Domain Test Complete ===")
    return True

if __name__ == "__main__":
    test_b15_b16_bridge() 