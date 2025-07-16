#!/usr/bin/env python3
"""
Test Improved Normalization Logic
Verifies that B06 device naming variations are properly unified.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.device_name_normalizer import normalizer

def test_b06_normalization():
    """Test B06 device name normalization with various patterns."""
    print("=" * 80)
    print("🧪 TESTING IMPROVED B06 DEVICE NORMALIZATION")
    print("=" * 80)
    
    # Test cases for B06 devices with various naming patterns
    test_cases = [
        # Original problematic devices from QA tests
        "DNAAS-LEAF-B06-1",
        "DNAAS-LEAF-B06-2-(NCPL)",
        "DNAAS-LEAF-B06-2 (NCPL)",
        "DNAAS-LEAF-B06-2(NCPL)",
        
        # Additional variations
        "DNAAS-LEAF-B06-2-NCP1",
        "DNAAS-LEAF-B06-2-NCPL",
        "DNAAS-LEAF-B06-2 (NCP1)",
        "DNAAS-LEAF-B06-2(NCP1)",
    ]
    
    print("📋 NORMALIZATION RESULTS:")
    results = {}
    
    for device_name in test_cases:
        normalized = normalizer.normalize_device_name(device_name)
        results[device_name] = normalized
        status = "✅" if normalized != device_name else "➡️"
        print(f"  {status} {device_name} -> {normalized}")
    
    print()
    
    # Check if B06 devices are unified
    b06_devices = [name for name in test_cases if "B06" in name]
    b06_normalized = [results[name] for name in b06_devices]
    unique_b06_normalized = set(b06_normalized)
    
    print("🔍 B06 DEVICE UNIFICATION ANALYSIS:")
    print(f"  Total B06 devices tested: {len(b06_devices)}")
    print(f"  Unique normalized names: {len(unique_b06_normalized)}")
    
    if len(unique_b06_normalized) == 1:
        print("  ✅ SUCCESS: All B06 devices unified to single normalized name")
        print(f"  Normalized name: {list(unique_b06_normalized)[0]}")
    else:
        print("  ❌ FAILURE: B06 devices not fully unified")
        print(f"  Normalized names: {sorted(unique_b06_normalized)}")
    
    return results

if __name__ == "__main__":
    results = test_b06_normalization()
    print("\n" + "=" * 80)
    print("✅ IMPROVED NORMALIZATION TEST COMPLETED")
    print("=" * 80) 