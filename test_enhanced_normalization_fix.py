#!/usr/bin/env python3
"""
Test Enhanced Normalization Fix
Verifies that the enhanced normalization logic properly fixes spine connections.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.enhanced_topology_discovery import enhanced_discovery
import json

def test_enhanced_normalization():
    """Test the enhanced normalization logic."""
    print("=" * 80)
    print("🧪 TESTING ENHANCED NORMALIZATION FIX")
    print("=" * 80)
    
    try:
        # Run enhanced topology discovery
        enhanced_topology = enhanced_discovery.discover_topology_with_normalization()
        
        if enhanced_topology:
            print("✅ Enhanced topology discovery completed successfully!")
            
            # Check specific B06 devices
            devices = enhanced_topology.get('devices', {})
            
            # Test B06-1
            b06_1_info = devices.get('DNAAS-LEAF-B06-1', {})
            b06_1_spines = b06_1_info.get('connected_spines', [])
            print(f"\n📋 DNAAS-LEAF-B06-1:")
            print(f"  • Connected spines: {b06_1_spines}")
            print(f"  • Has spine connections: {len(b06_1_spines) > 0}")
            
            # Test B06-2-NCP1
            b06_2_info = devices.get('DNAAS-LEAF-B06-2-NCP1', {})
            b06_2_spines = b06_2_info.get('connected_spines', [])
            print(f"\n📋 DNAAS-LEAF-B06-2-NCP1:")
            print(f"  • Connected spines: {b06_2_spines}")
            print(f"  • Has spine connections: {len(b06_2_spines) > 0}")
            
            # Show normalization statistics
            stats = enhanced_discovery.export_normalization_data()
            print(f"\n📊 Normalization Statistics:")
            print(f"  • Device mappings: {len(stats['device_mappings'])}")
            print(f"  • Spine mappings: {len(stats['spine_mappings'])}")
            print(f"  • Issues found: {len(stats['issues_found'].get('missing_spine_connections', []))}")
            print(f"  • Fixes applied: {len(stats['fixes_applied'].get('spine_mappings', []))}")
            print(f"  • Bundle-based fixes: {stats['fixes_applied'].get('bundle_based_fixes', 0)}")
            
            # Generate and display normalization report
            report = enhanced_discovery.generate_normalization_report()
            print(f"\n📋 Normalization Report:")
            print(report)
            
            # Test specific validation
            print(f"\n🔍 SPECIFIC DEVICE VALIDATION:")
            
            b06_1_validation = enhanced_discovery.validate_specific_device("DNAAS-LEAF-B06-1", enhanced_topology)
            print(f"DNAAS-LEAF-B06-1 validation:")
            print(f"  • Has spine connections: {b06_1_validation['has_spine_connections']}")
            print(f"  • Connected spines: {b06_1_validation['connected_spines']}")
            
            b06_2_validation = enhanced_discovery.validate_specific_device("DNAAS-LEAF-B06-2-(NCPL)", enhanced_topology)
            print(f"DNAAS-LEAF-B06-2-(NCPL) validation:")
            print(f"  • Has spine connections: {b06_2_validation['has_spine_connections']}")
            print(f"  • Connected spines: {b06_2_validation['connected_spines']}")
            
            return True
        else:
            print("❌ Enhanced topology discovery failed")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced normalization test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_normalization()
    sys.exit(0 if success else 1) 