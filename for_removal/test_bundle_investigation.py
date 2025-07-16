#!/usr/bin/env python3
"""
Test script to investigate bundle mappings
"""

import yaml
from pathlib import Path

def investigate_bundles():
    """Investigate bundle mappings to understand the structure"""
    
    # Load bundle mappings
    bundle_file = Path("topology/bundle_mapping_v2.yaml")
    with open(bundle_file, 'r') as f:
        bundle_data = yaml.safe_load(f)
    
    print("=== Bundle Investigation ===")
    
    # Check bundle_connections
    connections = bundle_data.get('bundle_connections', [])
    print(f"Bundle connections: {len(connections)}")
    
    # Check bundles
    bundles = bundle_data.get('bundles', {})
    print(f"Bundle definitions: {len(bundles)}")
    
    # Find bundles for specific devices
    test_devices = ['DNAAS-LEAF-B01', 'DNAAS-SPINE-B08', 'DNAAS-LEAF-B07']
    
    for device in test_devices:
        print(f"\n--- {device} ---")
        device_bundles = []
        
        for bundle_name, bundle_info in bundles.items():
            if bundle_info.get('device') == device:
                members = bundle_info.get('members', [])
                device_bundles.append({
                    'name': bundle_name,
                    'members': members
                })
        
        if device_bundles:
            print(f"Found {len(device_bundles)} bundles:")
            for bundle in device_bundles:
                print(f"  {bundle['name']}: {bundle['members']}")
        else:
            print("No bundles found")
    
    # Test specific interfaces from the test case
    test_interfaces = [
        ('DNAAS-LEAF-B01', 'ge100-0/0/36'),
        ('DNAAS-SPINE-B08', 'ge100-0/0/0'),
        ('DNAAS-SPINE-B08', 'ge100-0/0/24'),
        ('DNAAS-LEAF-B07', 'ge100-0/0/36')
    ]
    
    print(f"\n--- Interface Bundle Lookup Test ---")
    for device, interface in test_interfaces:
        found_bundle = None
        for bundle_name, bundle_info in bundles.items():
            if bundle_info.get('device') == device:
                members = bundle_info.get('members', [])
                if interface in members:
                    found_bundle = bundle_name
                    break
        
        if found_bundle:
            print(f"✅ {device}:{interface} → {found_bundle}")
        else:
            print(f"❌ {device}:{interface} → No bundle found")
    
    # Find interfaces that DO have bundles
    print(f"\n--- Available Interfaces with Bundles ---")
    available_interfaces = []
    for bundle_name, bundle_info in bundles.items():
        device = bundle_info.get('device')
        members = bundle_info.get('members', [])
        for member in members:
            available_interfaces.append((device, member, bundle_name))
    
    # Show some examples
    print(f"Found {len(available_interfaces)} interfaces with bundles")
    print("Sample interfaces:")
    for i, (device, interface, bundle) in enumerate(available_interfaces[:10]):
        print(f"  {device}:{interface} → {bundle}")
    
    # Find good test candidates
    print(f"\n--- Good Test Candidates ---")
    leaf_devices = set()
    spine_devices = set()
    
    for device, interface, bundle in available_interfaces:
        if 'LEAF' in device:
            leaf_devices.add(device)
        elif 'SPINE' in device:
            spine_devices.add(device)
    
    print(f"Leaf devices with bundles: {sorted(leaf_devices)}")
    print(f"Spine devices with bundles: {sorted(spine_devices)}")

if __name__ == "__main__":
    investigate_bundles() 