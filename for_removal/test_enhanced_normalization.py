#!/usr/bin/env python3
"""
Test Enhanced Normalization System
Demonstrates the future-proof naming inconsistency solution.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.device_name_normalizer import normalizer
from config_engine.enhanced_topology_discovery import enhanced_discovery

def test_device_normalization():
    """Test device name normalization with various patterns."""
    print("=" * 80)
    print("🧪 TESTING DEVICE NAME NORMALIZATION")
    print("=" * 80)
    
    # Test cases with various naming patterns
    test_cases = [
        # Original problematic devices
        "DNAAS-LEAF-B06-1",
        "DNAAS-LEAF-B06-2 (NCPL)",
        "DNAAS-SPINE-NCP1-B08",
        "DNAAS-SPINE-B08",
        
        # Various naming patterns
        "DNAAS-LEAF-A11-1",
        "DNAAS_LEAF_D13",
        "DNAAS-SPINE-C09",
        "DNAAS-SuperSpine-D04-NCC0",
        "DNAAS-SuperSpine-D04-NCC1",
        
        # Edge cases
        "DNAAS-LEAF-B06-2 (NCPL)",
        "DNAAS-LEAF-B06-2(NCPL)",
        "DNAAS-LEAF-B06-2 (NCP1)",
        "DNAAS-LEAF-B06-2 (NCP)",
    ]
    
    print("📋 NORMALIZATION RESULTS:")
    for device_name in test_cases:
        normalized = normalizer.normalize_device_name(device_name)
        status = "✅" if normalized != device_name else "➡️"
        print(f"  {status} {device_name} -> {normalized}")
    
    print()

def test_similar_device_finding():
    """Test finding similar devices."""
    print("🔍 TESTING SIMILAR DEVICE FINDING:")
    
    test_device = "DNAAS-LEAF-B06-1"
    similar_devices = normalizer.find_similar_devices(test_device)
    
    print(f"  Similar to '{test_device}':")
    for device in similar_devices:
        print(f"    • {device}")
    
    print()

def test_enhanced_topology_discovery():
    """Test enhanced topology discovery."""
    print("🚀 TESTING ENHANCED TOPOLOGY DISCOVERY:")
    
    try:
        # Run enhanced topology discovery
        enhanced_topology = enhanced_discovery.discover_topology_with_normalization()
        
        if enhanced_topology:
            print("  ✅ Enhanced topology discovery completed successfully")
            
            # Show normalization stats
            stats = enhanced_discovery.export_normalization_data()
            print(f"  📊 Device mappings: {len(stats['device_mappings'])}")
            print(f"  📊 Spine mappings: {len(stats['spine_mappings'])}")
            print(f"  📊 Issues found: {len(stats['issues_found'].get('missing_spine_connections', []))}")
            print(f"  📊 Fixes applied: {len(stats['fixes_applied'].get('spine_mappings', []))}")
        else:
            print("  ❌ Enhanced topology discovery failed")
            
    except Exception as e:
        print(f"  ❌ Error during enhanced topology discovery: {e}")
    
    print()

def test_specific_device_validation():
    """Test validation for specific problematic devices."""
    print("🔍 TESTING SPECIFIC DEVICE VALIDATION:")
    
    # Load topology data
    try:
        with open("topology/enhanced_topology.json", 'r') as f:
            topology_data = json.load(f)
    except FileNotFoundError:
        print("  ⚠️  Enhanced topology not found, using original topology")
        with open("topology/complete_topology_v2.json", 'r') as f:
            topology_data = json.load(f)
    
    # Test problematic devices
    problematic_devices = [
        "DNAAS-LEAF-B06-1",
        "DNAAS-LEAF-B06-2 (NCPL)",
        "DNAAS-SPINE-NCP1-B08"
    ]
    
    for device in problematic_devices:
        validation = enhanced_discovery.validate_specific_device(device, topology_data)
        
        print(f"  📋 {device}:")
        print(f"    • Normalized: {validation['normalized_name']}")
        print(f"    • Has spine connections: {validation['has_spine_connections']}")
        print(f"    • Connected spines: {validation['connected_spines']}")
        print(f"    • Device type: {validation['device_type']}")
        print(f"    • Bundles: {validation['bundles_count']}")
        print(f"    • Neighbors: {validation['neighbors_count']}")
        print(f"    • Similar devices: {len(validation['similar_devices'])}")
        print(f"    • Variations: {len(validation['variations'])}")
        print()
    
    print()

def test_normalization_report():
    """Test normalization report generation."""
    print("📊 TESTING NORMALIZATION REPORT:")
    
    try:
        report = enhanced_discovery.generate_normalization_report()
        print(report)
    except Exception as e:
        print(f"  ❌ Error generating report: {e}")
    
    print()

def demonstrate_future_proof_features():
    """Demonstrate future-proof features."""
    print("🔮 FUTURE-PROOF FEATURES:")
    
    # 1. Automatic pattern learning
    print("  1. 📚 Automatic Pattern Learning:")
    print("     • System learns new naming patterns automatically")
    print("     • Handles new suffixes, prefixes, and variations")
    print("     • Extensible regex pattern matching")
    
    # 2. Fuzzy matching
    print("  2. 🔍 Fuzzy Device Matching:")
    print("     • Finds similar devices even with typos")
    print("     • Handles partial matches and variations")
    print("     • Configurable similarity thresholds")
    
    # 3. Self-healing
    print("  3. 🛠️  Self-Healing Topology:")
    print("     • Automatically fixes missing spine connections")
    print("     • Suggests and applies device mappings")
    print("     • Validates and corrects connectivity issues")
    
    # 4. Persistence
    print("  4. 💾 Persistent Mappings:")
    print("     • Saves learned mappings for future use")
    print("     • Imports existing mappings on startup")
    print("     • Maintains consistency across runs")
    
    # 5. Comprehensive reporting
    print("  5. 📊 Comprehensive Reporting:")
    print("     • Detailed normalization statistics")
    print("     • Issue detection and resolution tracking")
    print("     • Validation and health checks")
    
    print()

def main():
    """Run all tests."""
    print("🧪 ENHANCED NORMALIZATION SYSTEM TEST")
    print("=" * 80)
    
    # Run tests
    test_device_normalization()
    test_similar_device_finding()
    test_enhanced_topology_discovery()
    test_specific_device_validation()
    test_normalization_report()
    demonstrate_future_proof_features()
    
    print("✅ All tests completed!")
    print("\n🎯 KEY BENEFITS:")
    print("  • Future-proof naming inconsistency handling")
    print("  • Automatic pattern recognition and learning")
    print("  • Self-healing topology discovery")
    print("  • Comprehensive validation and reporting")
    print("  • Persistent mappings for consistency")

if __name__ == "__main__":
    import json
    main() 