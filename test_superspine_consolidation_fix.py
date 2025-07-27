#!/usr/bin/env python3
"""
Test script for Superspine Consolidation Fix
Verifies that superspine NCC0/NCC1 variants are properly consolidated.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config_engine.enhanced_menu_system import EnhancedMenuSystem
from config_engine.enhanced_device_types import DeviceType

def test_superspine_consolidation():
    """Test the superspine consolidation fix."""
    
    print("🧪 Testing Superspine Consolidation Fix")
    print("=" * 60)
    print()
    
    # Initialize the enhanced menu system
    menu_system = EnhancedMenuSystem()
    
    # Test with a sample source device
    sample_source = "DNAAS-LEAF-A03"
    print(f"📊 Testing with source device: {sample_source}")
    print()
    
    # Get available destinations
    available_destinations = menu_system.builder.get_available_destinations(sample_source)
    superspine_destinations = [d for d in available_destinations if d.get('device_type') == DeviceType.SUPERSPINE]
    
    print(f"Raw superspine devices found: {len(superspine_destinations)}")
    for d in superspine_destinations:
        print(f"  • {d.get('name')}")
    
    print()
    
    # Apply consolidation
    organized_superspines = menu_system.organize_devices_by_row(superspine_destinations)
    consolidated_superspines = []
    
    # Flatten the organized structure
    for row, racks in organized_superspines.items():
        for rack, device in racks.items():
            consolidated_superspines.append(device)
    
    print(f"Consolidated superspine chassis: {len(consolidated_superspines)}")
    for d in consolidated_superspines:
        variants = d.get('chassis_variants', [])
        print(f"  • {d.get('name')} - Variants: {', '.join(variants)}")
    
    print()
    
    # Test the auto-selection logic
    print("🎯 Auto-Selection Logic Test:")
    print("─" * 40)
    
    if len(consolidated_superspines) == 1:
        print("✅ Single superspine chassis detected - will auto-select")
        selected_device = consolidated_superspines[0]
        print(f"   • Device: {selected_device.get('name')}")
        print(f"   • Variants: {', '.join(selected_device.get('chassis_variants', []))}")
        print("   • No row/rack selection needed")
    else:
        print(f"⚠️  Multiple superspine chassis detected ({len(consolidated_superspines)})")
        print("   • Will use row/rack selection")
    
    print()
    print("🎉 Superspine Consolidation Test Complete!")
    print()
    print("Expected Result:")
    print("• Raw devices: 2 (NCC0, NCC1)")
    print("• Consolidated: 1 (DNAAS-SUPERSPINE-D04)")
    print("• Auto-selection: Yes (no row/rack prompts)")

if __name__ == "__main__":
    test_superspine_consolidation() 