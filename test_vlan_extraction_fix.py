#!/usr/bin/env python3
"""
Test VLAN Extraction Fix
Verify that extract_vlan_from_interface no longer extracts VLANs from subinterface numbers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.bridge_domain_discovery import BridgeDomainDiscovery

def test_vlan_extraction_fix():
    """Test that VLAN extraction no longer uses subinterface numbers"""
    
    # Create a mock instance
    discovery = BridgeDomainDiscovery()
    
    print("🧪 Testing VLAN Extraction Fix")
    print("=" * 50)
    
    # Test cases that should NOT return VLAN IDs (these were incorrectly returning VLANs before)
    problematic_interfaces = [
        "bundle-3700.8101",      # TATA interface - was incorrectly returning 8101
        "bundle-3700.8102",      # TATA interface - was incorrectly returning 8102
        "bundle-3971.1001",      # TATA interface - was incorrectly returning 1001
        "bundle-60000.998",      # Generic bundle - was incorrectly returning 998
        "ge100-0/0/13.1360",    # Physical interface - was incorrectly returning 1360
        "et100-0/0/1.500",      # Physical interface - was incorrectly returning 500
    ]
    
    print("❌ Interfaces that should NOT return VLAN IDs (subinterface numbers):")
    for interface in problematic_interfaces:
        vlan_id = discovery.extract_vlan_from_interface(interface)
        status = "✅ FIXED" if vlan_id is None else "❌ STILL BROKEN"
        print(f"  {interface} -> VLAN ID: {vlan_id} {status}")
    
    print()
    
    # Test cases that SHOULD return VLAN IDs (explicit VLAN interfaces)
    valid_vlan_interfaces = [
        "vlan123",               # Explicit VLAN interface
        "vlan-456",              # Explicit VLAN interface with dash
        "VLAN_789",              # Explicit VLAN interface with underscore
        "vlan1000",              # Explicit VLAN interface
    ]
    
    print("✅ Interfaces that SHOULD return VLAN IDs (explicit VLAN interfaces):")
    for interface in valid_vlan_interfaces:
        vlan_id = discovery.extract_vlan_from_interface(interface)
        status = "✅ WORKING" if vlan_id is not None else "❌ BROKEN"
        print(f"  {interface} -> VLAN ID: {vlan_id} {status}")
    
    print()
    
    # Test edge cases
    edge_cases = [
        "bundle-3700",           # No subinterface number
        "ge100-0/0/13",         # No subinterface number
        "vlan",                  # Just "vlan" without number
        "bundle-3700.vlan123",  # Mixed case
        "",                      # Empty string
        None,                    # None value
        123,                     # Non-string input
    ]
    
    print("🔍 Edge cases:")
    for interface in edge_cases:
        vlan_id = discovery.extract_vlan_from_interface(interface)
        print(f"  {interface} -> VLAN ID: {vlan_id}")
    
    print()
    
    # Summary
    print("📊 Summary:")
    print("  • Subinterface numbers should NOT be treated as VLAN IDs")
    print("  • Only explicit 'vlan123' interfaces should return VLAN IDs")
    print("  • TATA interfaces should now return None for VLAN ID")
    print("  • This will require proper VLAN configuration parsing from device configs")
    
    print()
    print("✅ VLAN Extraction Fix Test Completed!")

if __name__ == "__main__":
    test_vlan_extraction_fix()
