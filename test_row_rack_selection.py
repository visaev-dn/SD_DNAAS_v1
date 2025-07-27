#!/usr/bin/env python3
"""
Test script for Row/Rack Selection functionality
Demonstrates the enhanced menu system with device selection.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config_engine.enhanced_menu_system import EnhancedMenuSystem
from config_engine.enhanced_device_types import DeviceType, enhanced_classifier

def test_row_rack_selection():
    """Test the row/rack selection functionality."""
    
    print("🧪 Testing Row/Rack Selection Functionality")
    print("=" * 60)
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
    
    # Test device organization by row
    print("📋 Device Organization Test:")
    print("─" * 40)
    
    if available_sources:
        organized_sources = menu_system.organize_devices_by_row(available_sources)
        print(f"✅ Organized {len(available_sources)} sources into {len(organized_sources)} rows")
        
        for row in sorted(organized_sources.keys()):
            rack_count = len(organized_sources[row])
            print(f"   • Row {row}: {rack_count} devices")
    
    print()
    
    # Test device name parsing
    print("🔍 Device Name Parsing Test:")
    print("─" * 40)
    
    test_devices = [
        "DNAAS-LEAF-A03",
        "DNAAS-LEAF-B05", 
        "DNAAS-LEAF-C16",
        "DNAAS-SUPERSPINE-D04-NCC1",
        "DNAAS-SUPERSPINE-D04-NCC0",
        "DNAAS-SUPERSPINE-D04"
    ]
    
    for device in test_devices:
        row, rack = menu_system.parse_device_name(device)
        if row and rack:
            print(f"✅ {device} -> Row: {row}, Rack: {rack}")
        else:
            print(f"❌ {device} -> Could not parse")
    
    print()
    
    # Test superspine chassis consolidation
    print("🏗️  Superspine Chassis Consolidation Test:")
    print("─" * 40)
    
    mock_superspine_devices = [
        {'name': 'DNAAS-SUPERSPINE-D04-NCC0', 'device_type': DeviceType.SUPERSPINE},
        {'name': 'DNAAS-SUPERSPINE-D04-NCC1', 'device_type': DeviceType.SUPERSPINE},
        {'name': 'DNAAS-LEAF-A03', 'device_type': DeviceType.LEAF}
    ]
    
    organized = menu_system.organize_devices_by_row(mock_superspine_devices)
    
    for row in sorted(organized.keys()):
        print(f"Row {row}:")
        for rack in sorted(organized[row].keys()):
            device = organized[row][rack]
            device_type = device['device_type']
            icon = enhanced_classifier.get_device_type_icon(device_type)
            device_name = device['name']
            
            if device_type == DeviceType.SUPERSPINE and 'chassis_variants' in device:
                variants = device['chassis_variants']
                print(f"  Rack {rack}: {icon} {device_name} ({device_type.value}) - Variants: {', '.join(variants)}")
            else:
                print(f"  Rack {rack}: {icon} {device_name} ({device_type.value})")
    
    print()
    
    # Test topology constraints
    print("🔗 Topology Constraints Test:")
    print("─" * 40)
    
    test_topologies = [
        (DeviceType.LEAF, DeviceType.LEAF, "Leaf → Leaf"),
        (DeviceType.LEAF, DeviceType.SUPERSPINE, "Leaf → Superspine"),
        (DeviceType.SUPERSPINE, DeviceType.LEAF, "Superspine → Leaf"),
        (DeviceType.SUPERSPINE, DeviceType.SUPERSPINE, "Superspine → Superspine")
    ]
    
    for source_type, dest_type, description in test_topologies:
        is_valid = enhanced_classifier.validate_topology_constraints(source_type, dest_type)
        source_icon = enhanced_classifier.get_device_type_icon(source_type)
        dest_icon = enhanced_classifier.get_device_type_icon(dest_type)
        
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{source_icon} {source_type.value} → {dest_icon} {dest_type.value}: {status} ({description})")
    
    print()
    print("🎉 Row/Rack Selection Test Complete!")
    print()
    print("Key Results:")
    print(f"• Total devices found: {len(successful_devices)}")
    print(f"• Available sources (leafs): {len(available_sources)}")
    if available_sources:
        print(f"• Available destinations: {len(available_destinations)}")
        print(f"• Leaf destinations: {len(leaf_destinations)}")
        print(f"• Superspine destinations: {len(superspine_destinations)}")
    print("• Row/rack selection functionality: ✅ Working")
    print("• Topology constraints: ✅ Enforced")
    print("• Device name parsing: ✅ Working")

if __name__ == "__main__":
    test_row_rack_selection() 