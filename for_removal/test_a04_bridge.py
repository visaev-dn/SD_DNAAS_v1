#!/usr/bin/env python3
"""
Test script for building bridge with DNAAS-LEAF-A04 to verify DNAAS-SPINE-A08 detection
"""

from config_engine.bridge_domain_builder import BridgeDomainBuilder
import yaml
from pathlib import Path

def test_a04_bridge():
    """Test bridge domain builder with DNAAS-LEAF-A04 to verify DNAAS-SPINE-A08 detection"""
    print("=== Testing Bridge Domain: DNAAS-LEAF-A04 (with DNAAS-SPINE-A08) ===")
    
    # Initialize the builder
    builder = BridgeDomainBuilder()
    
    if not builder.topology_data:
        print("❌ No topology data available. Please run topology discovery first.")
        return False
    
    print("✅ Topology data loaded successfully")
    
    # Check if DNAAS-SPINE-A08 is classified as a spine
    spine_devices = builder.topology_data.get('spine_devices', [])
    if 'DNAAS-SPINE-A08' in spine_devices:
        print("✅ DNAAS-SPINE-A08 is classified as a spine device")
    else:
        print("❌ DNAAS-SPINE-A08 is NOT classified as a spine device")
        print(f"Available spine devices: {spine_devices}")
        return False
    
    # Check DNAAS-LEAF-A04's connected spines
    a04_device = builder.topology_data.get('devices', {}).get('DNAAS-LEAF-A04', {})
    connected_spines = a04_device.get('connected_spines', [])
    print(f"DNAAS-LEAF-A04 connected spines: {connected_spines}")
    
    # Test bridge domain building
    print("\n--- Testing Bridge Domain Builder ---")
    
    # Test case: DNAAS-LEAF-A04 to DNAAS-LEAF-A01 (both connect to DNAAS-SPINE-A08)
    source_leaf = "DNAAS-LEAF-A04"
    dest_leaf = "DNAAS-LEAF-A01"
    source_port = "ge100-0/0/1"  # External port
    dest_port = "ge100-0/0/2"     # External port
    
    print(f"Testing: {source_leaf}:{source_port} → {dest_leaf}:{dest_port}")
    
    try:
        # Build bridge domain configuration
        config = builder.build_bridge_domain_config(
            service_name="test_a04_a01",
            vlan_id=1001,
            source_leaf=source_leaf,
            source_port=source_port,
            dest_leaf=dest_leaf,
            dest_port=dest_port
        )
        
        if config:
            print("✅ Bridge domain configuration generated successfully!")
            for device, device_config in config.items():
                print(f"  📋 {device}: {len(device_config)} configuration lines")
                if device_config:
                    print(f"    Sample config: {device_config[0]}")
        else:
            print("❌ Failed to generate bridge domain configuration")
            
    except Exception as e:
        print(f"❌ Error building bridge domain: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_a04_bridge() 