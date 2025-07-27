#!/usr/bin/env python3
"""
Test script for Streamlined Flow
Demonstrates the new order: Source Leaf → Source AC → Destination Type → (if Leaf: row/rack + dest AC, if Superspine: just dest AC)
"""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config_engine.enhanced_menu_system import EnhancedMenuSystem
from config_engine.enhanced_device_types import DeviceType, enhanced_classifier

def test_streamlined_flow():
    """Test the streamlined flow functionality."""
    
    print("🧪 Testing Streamlined Flow")
    print("=" * 60)
    print()
    print("New Flow Order:")
    print("1. Source Leaf (row/rack selection)")
    print("2. Source AC (interface selection)")
    print("3. Destination Type (Leaf or Superspine)")
    print("4. Destination:")
    print("   • If Leaf: row/rack + dest AC")
    print("   • If Superspine: just dest AC (skip row/rack)")
    print()
    
    # Initialize the enhanced menu system
    menu_system = EnhancedMenuSystem()
    
    # Test device discovery
    print("📊 Device Discovery Test:")
    print("─" * 40)
    
    successful_devices = menu_system.get_successful_devices_from_status()
    print(f"✅ Found {len(successful_devices)} devices")
    
    # Test available sources
    available_sources = menu_system.builder.get_available_sources()
    print(f"✅ Found {len(available_sources)} available sources (leafs)")
    
    # Test available destinations
    if available_sources:
        sample_source = available_sources[0]['name']
        available_destinations = menu_system.builder.get_available_destinations(sample_source)
        print(f"✅ Found {len(available_destinations)} available destinations")
        
        # Count device types
        leaf_destinations = [d for d in available_destinations if d.get('device_type') == DeviceType.LEAF]
        superspine_destinations = [d for d in available_destinations if d.get('device_type') == DeviceType.SUPERSPINE]
        
        print(f"   • Leaf destinations: {len(leaf_destinations)}")
        print(f"   • Superspine destinations: {len(superspine_destinations)}")
    
    print()
    
    # Test superspine consolidation
    print("🏗️  Superspine Consolidation Test:")
    print("─" * 40)
    
    if available_sources:
        sample_source = available_sources[0]['name']
        available_destinations = menu_system.builder.get_available_destinations(sample_source)
        superspine_destinations = [d for d in available_destinations if d.get('device_type') == DeviceType.SUPERSPINE]
        
        if superspine_destinations:
            print(f"Raw superspine destinations: {len(superspine_destinations)}")
            for d in superspine_destinations:
                print(f"  • {d.get('name')}")
            
            # Test consolidation
            organized = menu_system.organize_devices_by_row(superspine_destinations)
            print(f"\nConsolidated superspine chassis: {len(organized)}")
            for row, racks in organized.items():
                for rack, device in racks.items():
                    variants = device.get('chassis_variants', [])
                    print(f"  • Row {row}, Rack {rack}: {device.get('name')} - Variants: {', '.join(variants)}")
    
    print()
    
    # Test streamlined destination selection logic
    print("🎯 Streamlined Destination Selection Logic:")
    print("─" * 40)
    
    print("For Leaf Destination:")
    print("  → Prompts for Row selection (A, B, C, etc.)")
    print("  → Prompts for Rack selection (01, 02, 03, etc.)")
    print("  → Prompts for destination AC")
    print()
    print("For Superspine Destination:")
    print("  → Automatically selects the single superspine chassis")
    print("  → Shows chassis variant information (NCC0, NCC1)")
    print("  → Prompts for destination AC")
    print("  → No row/rack selection needed")
    
    print()
    
    # Test the new method exists
    print("🔧 Method Availability Test:")
    print("─" * 40)
    
    if hasattr(menu_system, 'select_destination_device_streamlined'):
        print("✅ select_destination_device_streamlined method exists")
    else:
        print("❌ select_destination_device_streamlined method missing")
    
    if hasattr(menu_system, 'select_destination_device'):
        print("✅ select_destination_device method exists (legacy)")
    else:
        print("❌ select_destination_device method missing")
    
    print()
    print("🎉 Streamlined Flow Test Complete!")
    print()
    print("Key Features:")
    print("• New order: Source Leaf → Source AC → Destination Type → Destination")
    print("• Superspine: Skip row/rack selection (single chassis)")
    print("• Leaf: Full row/rack + AC selection")
    print("• Automatic chassis consolidation (NCC0/NCC1)")
    print("• Clear variant information display")

if __name__ == "__main__":
    test_streamlined_flow() 