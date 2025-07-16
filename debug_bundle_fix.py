#!/usr/bin/env python3
"""
Debug Bundle-Based Spine Connection Fix
Traces through the bundle-based fix logic to understand why it's not working for B06 devices.
"""

import sys
import os
import yaml
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.device_name_normalizer import normalizer

def debug_bundle_fix():
    """Debug the bundle-based spine connection fix logic."""
    print("=" * 80)
    print("🔍 DEBUGGING BUNDLE-BASED SPINE CONNECTION FIX")
    print("=" * 80)
    
    # Load bundle mappings
    bundle_file = "topology/bundle_mapping_v2.yaml"
    print(f"📁 Loading bundle mappings from: {bundle_file}")
    
    try:
        with open(bundle_file, 'r') as f:
            bundle_data = yaml.safe_load(f)
        print(f"✅ Loaded bundle mappings successfully")
        print(f"Type of bundle_data: {type(bundle_data)}")
        # Print a sample of the data
        if isinstance(bundle_data, dict):
            sample_keys = list(bundle_data.keys())[:5]
            print(f"Sample keys: {sample_keys}")
            for k in sample_keys:
                print(f"  {k}: {str(bundle_data[k])[:200]}")
        elif isinstance(bundle_data, list):
            print(f"Sample (first 3 items): {bundle_data[:3]}")
        else:
            print(f"Sample: {str(bundle_data)[:500]}")
    except Exception as e:
        print(f"❌ Failed to load bundle mappings: {e}")
        return
    
    # Extract bundle connections using canonical keys
    bundle_connections = {}
    bundles = bundle_data.get('bundles', {})
    print(f"📊 Processing {len(bundles)} bundle entries using canonical keys...")
    
    for bundle_name, bundle_info in bundles.items():
        if isinstance(bundle_info, dict) and 'device' in bundle_info and 'connections' in bundle_info:
            device_name = bundle_info['device']
            connections = bundle_info['connections']
            
            # Use canonical key for device lookup
            device_key = normalizer.canonical_key(device_name)
            if device_key not in bundle_connections:
                bundle_connections[device_key] = []
            
            for conn in connections:
                if isinstance(conn, dict) and 'remote_device' in conn:
                    bundle_connections[device_key].append(conn['remote_device'])
    
    print(f"📊 Found bundle connections for {len(bundle_connections)} devices (by canonical key)")
    
    # Debug: Show some examples
    print(f"\n🔍 Sample bundle connections (by canonical key):")
    count = 0
    for device_key, remotes in bundle_connections.items():
        if count < 5:  # Show first 5
            print(f"  • {device_key}: {remotes}")
            count += 1
        else:
            break
    
    # Test B06 devices specifically with canonical keys
    b06_devices = [
        "DNAAS-LEAF-B06-1",
        "DNAAS-LEAF-B06-2 (NCPL)",
        "DNAAS-LEAF-B06-2-(NCPL)",
        "DNAAS-LEAF-B06-2-NCP1"
    ]
    
    print("\n🔍 TESTING B06 DEVICES WITH CANONICAL KEYS:")
    for device in b06_devices:
        print(f"\n📋 Device: {device}")
        device_key = normalizer.canonical_key(device)
        print(f"  🔑 Canonical key: {device_key}")
        
        # Check if device exists in bundle connections
        if device_key in bundle_connections:
            print(f"  ✅ Found in bundle connections")
            print(f"  📡 Remote devices: {bundle_connections[device_key]}")
            
            # Check for spine connections
            spine_connections = []
            for remote in bundle_connections[device_key]:
                if 'SPINE' in remote:
                    normalized_spine = normalizer.normalize_device_name(remote)
                    spine_connections.append(normalized_spine)
                    print(f"    • {remote} -> {normalized_spine}")
            
            print(f"  🏗️  Spine connections: {spine_connections}")
        else:
            print(f"  ❌ NOT found in bundle connections")
    
    # Test the actual bundle-based fix logic with canonical keys
    print("\n🔧 TESTING BUNDLE-BASED FIX LOGIC WITH CANONICAL KEYS:")
    
    # Simulate the bundle-based fix logic
    devices_to_test = ["DNAAS-LEAF-B06-1", "DNAAS-LEAF-B06-2-NCP1"]
    
    for device_name in devices_to_test:
        print(f"\n📋 Testing device: {device_name}")
        device_key = normalizer.canonical_key(device_name)
        print(f"  🔑 Canonical key: {device_key}")
        
        if device_key in bundle_connections:
            print(f"  ✅ Found in bundle connections")
            
            all_bundle_spines = set()
            for remote_device in bundle_connections[device_key]:
                print(f"    📡 Remote: {remote_device}")
                if 'SPINE' in remote_device:
                    normalized_spine = normalizer.normalize_device_name(remote_device)
                    all_bundle_spines.add(normalized_spine)
                    print(f"      🏗️  Spine: {remote_device} -> {normalized_spine}")
            
            print(f"  🎯 Final spine connections: {list(all_bundle_spines)}")
        else:
            print(f"  ❌ No bundle connections found for canonical key {device_key}")

if __name__ == "__main__":
    debug_bundle_fix() 