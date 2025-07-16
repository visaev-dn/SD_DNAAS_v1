#!/usr/bin/env python3
"""
Test script to verify bridge domain builder fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.bridge_domain_builder import BridgeDomainBuilder

def test_bridge_domain_fixes():
    """Test the bridge domain builder fixes"""
    print("🧪 Testing Bridge Domain Builder Fixes")
    print("=" * 50)
    
    try:
        # Initialize the bridge domain builder
        builder = BridgeDomainBuilder()
        
        # Test bundle mapping with naming inconsistencies
        print("\n1. Testing bundle mapping with naming inconsistencies...")
        
        # Test case 1: DNAAS-SUPERSPINE-D04-NCC0 (should find DNAAS-SuperSpine-D04-NCC0)
        bundle1 = builder.get_bundle_for_interface("DNAAS-SUPERSPINE-D04-NCC0", "ge100-5/0/12")
        print(f"   DNAAS-SUPERSPINE-D04-NCC0:ge100-5/0/12 -> {bundle1}")
        
        # Test case 2: DNAAS-SPINE-D14 (should find DNAAS-Spine-D14 or similar)
        bundle2 = builder.get_bundle_for_interface("DNAAS-SPINE-D14", "ge100-0/0/0")
        print(f"   DNAAS-SPINE-D14:ge100-0/0/0 -> {bundle2}")
        
        # Test available leaves
        print("\n2. Testing available leaves...")
        available_leaves = builder.get_available_leaves()
        print(f"   Available leaves: {len(available_leaves)}")
        print(f"   First 5: {available_leaves[:5]}")
        
        # Test unavailable leaves
        print("\n3. Testing unavailable leaves...")
        unavailable_reasons = builder.get_unavailable_leaves()
        print(f"   Unavailable leaves: {len(unavailable_reasons)}")
        for leaf, reason in list(unavailable_reasons.items())[:3]:
            print(f"   • {leaf}: {reason.get('description', 'Unknown')}")
        
        # Test path calculation
        print("\n4. Testing path calculation...")
        if available_leaves:
            source_leaf = available_leaves[0]
            dest_leaf = available_leaves[1] if len(available_leaves) > 1 else available_leaves[0]
            print(f"   Testing path: {source_leaf} -> {dest_leaf}")
            
            path = builder.calculate_path(source_leaf, dest_leaf)
            if path:
                print(f"   ✅ Path found: {path.get('source_leaf')} -> {path.get('source_spine')} -> {path.get('superspine', 'N/A')} -> {path.get('dest_spine')} -> {path.get('destination_leaf')}")
            else:
                print(f"   ❌ No path found")
        
        print("\n✅ Bridge domain builder fixes test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bridge_domain_fixes() 