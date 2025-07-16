#!/usr/bin/env python3
"""
Test script to verify the spine-to-superspine connection fix.
This script tests the enhanced topology discovery with spine-to-superspine extraction
and verifies that path calculations work correctly.
"""

import os
import sys
import json
import yaml
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.enhanced_topology_discovery import enhanced_discovery
from config_engine.bridge_domain_builder import BridgeDomainBuilder

def test_spine_superspine_extraction():
    """Test the spine-to-superspine connection extraction."""
    print("=" * 80)
    print("🔧 TESTING SPINE-TO-SUPERSPINE CONNECTION EXTRACTION")
    print("=" * 80)
    
    # Run enhanced topology discovery
    print("📊 Running enhanced topology discovery...")
    topology_data = enhanced_discovery.discover_topology_with_normalization()
    
    if not topology_data:
        print("❌ Failed to discover topology")
        return False
    
    print(f"✅ Topology discovery completed successfully")
    print(f"📊 Found {len(topology_data.get('devices', {}))} devices")
    
    # Check for spine-to-superspine connections
    devices = topology_data.get('devices', {})
    spine_devices = []
    superspine_devices = []
    
    for device_name, device_info in devices.items():
        if device_info.get('type') == 'spine':
            spine_devices.append(device_name)
        elif device_info.get('type') == 'superspine':
            superspine_devices.append(device_name)
    
    print(f"🏗️  Found {len(spine_devices)} spine devices: {spine_devices}")
    print(f"🏗️  Found {len(superspine_devices)} superspine devices: {superspine_devices}")
    
    # Check spine-to-superspine connections
    spine_with_superspines = []
    for spine_name in spine_devices:
        spine_info = devices.get(spine_name, {})
        connected_superspines = spine_info.get('connected_superspines', [])
        if connected_superspines:
            spine_with_superspines.append(spine_name)
            print(f"✅ {spine_name} -> {[conn['name'] for conn in connected_superspines]}")
        else:
            print(f"❌ {spine_name} -> No superspine connections")
    
    print(f"📊 {len(spine_with_superspines)}/{len(spine_devices)} spines have superspine connections")
    
    # Check superspine-to-spine connections
    superspine_with_spines = []
    for superspine_name in superspine_devices:
        superspine_info = devices.get(superspine_name, {})
        connected_spines = superspine_info.get('connected_spines', [])
        if connected_spines:
            superspine_with_spines.append(superspine_name)
            print(f"✅ {superspine_name} -> {[conn['name'] for conn in connected_spines]}")
        else:
            print(f"❌ {superspine_name} -> No spine connections")
    
    print(f"📊 {len(superspine_with_spines)}/{len(superspine_devices)} superspines have spine connections")
    
    return len(spine_with_superspines) > 0 and len(superspine_with_spines) > 0

def test_path_calculation():
    """Test path calculation with the new spine-to-superspine connections."""
    print("\n" + "=" * 80)
    print("🔧 TESTING PATH CALCULATION WITH SPINE-TO-SUPERSPINE CONNECTIONS")
    print("=" * 80)
    
    # Initialize bridge domain builder
    builder = BridgeDomainBuilder()
    
    # Test specific problematic case: DNAAS-LEAF-B16 -> DNAAS-LEAF-B07
    source_leaf = "DNAAS-LEAF-B16"
    dest_leaf = "DNAAS-LEAF-B07"
    
    print(f"🧪 Testing path calculation: {source_leaf} -> {dest_leaf}")
    
    # Calculate path
    path = builder.calculate_path(source_leaf, dest_leaf)
    
    if path:
        print(f"✅ Path calculation successful!")
        print(f"📊 Path type: {'3-tier' if path.get('superspine') else '2-tier'}")
        print(f"🏗️  Path: {path.get('source_leaf')} -> {path.get('source_spine')} -> {path.get('superspine', 'N/A')} -> {path.get('dest_spine')} -> {path.get('destination_leaf')}")
        print(f"🔗 Segments: {len(path.get('segments', []))}")
        
        for i, segment in enumerate(path.get('segments', []), 1):
            print(f"  {i}. {segment['type']}: {segment['source_device']} -> {segment['dest_device']}")
        
        return True
    else:
        print(f"❌ Path calculation failed for {source_leaf} -> {dest_leaf}")
        return False

def test_multiple_paths():
    """Test multiple path calculations to verify the fix works broadly."""
    print("\n" + "=" * 80)
    print("🔧 TESTING MULTIPLE PATH CALCULATIONS")
    print("=" * 80)
    
    # Initialize bridge domain builder
    builder = BridgeDomainBuilder()
    
    # Test cases from the failed QA tests
    test_cases = [
        ("DNAAS-LEAF-B16", "DNAAS-LEAF-B07"),
        ("DNAAS-LEAF-B02", "DNAAS-LEAF-A11-1"),
        ("DNAAS-LEAF-B14", "DNAAS-LEAF-B06-1"),
        ("DNAAS-LEAF-B06-2-NCP1", "DNAAS-LEAF-B16"),
        ("DNAAS-LEAF-B07", "DNAAS-LEAF-C11"),
        ("DNAAS-LEAF-D13", "DNAAS-LEAF-B02"),
        ("DNAAS-LEAF-D13", "DNAAS-LEAF-F16"),
    ]
    
    successful_paths = 0
    total_tests = len(test_cases)
    
    for source_leaf, dest_leaf in test_cases:
        print(f"\n🧪 Testing: {source_leaf} -> {dest_leaf}")
        
        path = builder.calculate_path(source_leaf, dest_leaf)
        
        if path:
            print(f"✅ SUCCESS: {path.get('source_spine')} -> {path.get('superspine', 'N/A')} -> {path.get('dest_spine')}")
            successful_paths += 1
        else:
            print(f"❌ FAILED: No path found")
    
    success_rate = (successful_paths / total_tests) * 100
    print(f"\n📊 RESULTS: {successful_paths}/{total_tests} paths successful ({success_rate:.1f}%)")
    
    return success_rate > 50  # Expect significant improvement

def main():
    """Run all tests."""
    print("🚀 STARTING SPINE-TO-SUPERSPINE CONNECTION FIX TESTS")
    print("=" * 80)
    
    # Test 1: Spine-to-superspine extraction
    extraction_success = test_spine_superspine_extraction()
    
    # Test 2: Path calculation
    path_success = test_path_calculation()
    
    # Test 3: Multiple path calculations
    multiple_paths_success = test_multiple_paths()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"🔧 Spine-to-superspine extraction: {'✅ PASS' if extraction_success else '❌ FAIL'}")
    print(f"🔧 Path calculation: {'✅ PASS' if path_success else '❌ FAIL'}")
    print(f"🔧 Multiple path calculations: {'✅ PASS' if multiple_paths_success else '❌ FAIL'}")
    
    overall_success = extraction_success and path_success and multiple_paths_success
    print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 The spine-to-superspine connection fix is working correctly!")
        print("💡 The enhanced topology discovery now properly extracts spine-to-superspine connections")
        print("💡 Path calculations should now work for 3-tier architectures")
    else:
        print("\n⚠️  Some tests failed. The fix may need additional work.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 