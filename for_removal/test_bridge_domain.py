#!/usr/bin/env python3
"""
Test script for bridge domain builder with devices that have spine connections
"""

from config_engine.bridge_domain_builder import BridgeDomainBuilder
import json

def test_bridge_domain():
    print("Testing Bridge Domain Builder with devices that have spine connections...")
    
    # Initialize the builder
    builder = BridgeDomainBuilder()
    
    # Debug: Check what topology data is loaded
    print(f"Topology data keys: {list(builder.topology_data.keys())}")
    
    devices = builder.topology_data.get('devices', {})
    print(f"Number of devices: {len(devices)}")
    
    # Check specific devices
    test_devices = ["DNAAS-LEAF-B15", "DNAAS-LEAF-B10"]
    for device in test_devices:
        if device in devices:
            device_info = devices[device]
            print(f"\n{device}:")
            print(f"  Type: {device_info.get('type')}")
            print(f"  Connected spines: {device_info.get('connected_spines', [])}")
        else:
            print(f"\n{device}: Not found in topology data")
    
    # Test with devices that have spine connections
    source_leaf = "DNAAS-LEAF-B15"  # Has connections to DNAAS-SPINE-B09
    dest_leaf = "DNAAS-LEAF-B10"    # Has connections to DNAAS-SPINE-B09
    
    print(f"\nTesting path calculation: {source_leaf} → {dest_leaf}")
    
    # Calculate path
    path = builder.calculate_path(source_leaf, dest_leaf)
    
    if path:
        print("✅ Path calculation successful!")
        print(f"Path: {path['source_leaf']} → {path['source_spine']} → {path['superspine']} → {path['dest_spine']} → {path['destination_leaf']}")
        
        # Test building configuration
        print("\nTesting bridge domain configuration build...")
        configs = builder.build_bridge_domain_config(
            "test_service", 100,
            source_leaf, "ge100-0/0/10",
            dest_leaf, "ge100-0/0/20"
        )
        
        if configs:
            print("✅ Bridge domain configuration built successfully!")
            print(f"Devices configured: {list(configs.keys())}")
        else:
            print("❌ Failed to build bridge domain configuration")
    else:
        print("❌ Path calculation failed")

if __name__ == "__main__":
    test_bridge_domain() 