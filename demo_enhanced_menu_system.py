#!/usr/bin/env python3
"""
Demo script for Enhanced Menu System with Row/Rack Selection
Demonstrates the new row/rack selection functionality with destination type choice.
"""

import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config_engine.enhanced_menu_system import EnhancedMenuSystem
from config_engine.enhanced_device_types import DeviceType, enhanced_classifier

def demo_enhanced_menu_system():
    """Demo the enhanced menu system with row/rack selection."""
    
    print("🎯 Enhanced Menu System Demo - Row/Rack Selection")
    print("=" * 60)
    print()
    print("This demo showcases the new row/rack selection functionality")
    print("with destination type choice (Leaf vs Superspine).")
    print()
    
    # Initialize the enhanced menu system
    menu_system = EnhancedMenuSystem()
    
    # Demo device name parsing
    print("📋 Device Name Parsing Demo:")
    print("─" * 40)
    
    test_devices = [
        "DNAAS-LEAF-A12",
        "DNAAS_LEAF_D13", 
        "DNAAS-LEAF-B06-2",
        "DNAAS-SUPERSPINE-01"
    ]
    
    for device in test_devices:
        row, rack = menu_system.parse_device_name(device)
        if row and rack:
            print(f"✅ {device} -> Row: {row}, Rack: {rack}")
        else:
            print(f"❌ {device} -> Could not parse")
    
    print()
    
    # Demo device organization by row
    print("📊 Device Organization by Row Demo:")
    print("─" * 40)
    
    # Create mock device data
    mock_devices = [
        {'name': 'DNAAS-LEAF-A01', 'device_type': DeviceType.LEAF},
        {'name': 'DNAAS-LEAF-A02', 'device_type': DeviceType.LEAF},
        {'name': 'DNAAS-LEAF-B01', 'device_type': DeviceType.LEAF},
        {'name': 'DNAAS-SUPERSPINE-01', 'device_type': DeviceType.SUPERSPINE},
        {'name': 'DNAAS-SUPERSPINE-02', 'device_type': DeviceType.SUPERSPINE}
    ]
    
    organized = menu_system.organize_devices_by_row(mock_devices)
    
    for row in sorted(organized.keys()):
        print(f"Row {row}:")
        for rack in sorted(organized[row].keys()):
            device = organized[row][rack]
            device_type = device['device_type']
            icon = enhanced_classifier.get_device_type_icon(device_type)
            print(f"  Rack {rack}: {icon} {device['name']} ({device_type.value})")
    
    print()
    
    # Demo destination type selection logic
    print("🎯 Destination Type Selection Demo:")
    print("─" * 40)
    
    print("When selecting a destination, the user will be prompted:")
    print("1. 🌿 Leaf Device (P2P or P2MP)")
    print("2. 🏗️  Superspine Device (P2P or P2MP)")
    print()
    print("If Leaf is chosen:")
    print("  → Prompts for Row selection (A, B, C, etc.)")
    print("  → Prompts for Rack selection (01, 02, 03, etc.)")
    print()
    print("If Superspine is chosen:")
    print("  → Prompts for Row selection (A, B, C, etc.)")
    print("  → Prompts for Rack selection (01, 02, 03, etc.)")
    print("  → Shows topology constraints")
    print()
    
    # Demo topology constraints
    print("📋 Topology Constraints Demo:")
    print("─" * 40)
    
    test_topologies = [
        (DeviceType.LEAF, DeviceType.LEAF, "✅ Valid"),
        (DeviceType.LEAF, DeviceType.SUPERSPINE, "✅ Valid"),
        (DeviceType.SUPERSPINE, DeviceType.LEAF, "❌ Invalid"),
        (DeviceType.SUPERSPINE, DeviceType.SUPERSPINE, "❌ Invalid")
    ]
    
    for source_type, dest_type, expected in test_topologies:
        is_valid = enhanced_classifier.validate_topology_constraints(source_type, dest_type)
        source_icon = enhanced_classifier.get_device_type_icon(source_type)
        dest_icon = enhanced_classifier.get_device_type_icon(dest_type)
        
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{source_icon} {source_type.value} → {dest_icon} {dest_type.value}: {status}")
    
    print()
    
    # Demo interface validation
    print("🔌 Interface Validation Demo:")
    print("─" * 40)
    
    test_interfaces = [
        ("ge1-0/0/10", DeviceType.LEAF, "✅ Valid"),
        ("ge100-0/0/10", DeviceType.LEAF, "✅ Valid"),
        ("ge10-0/0/5", DeviceType.SUPERSPINE, "✅ Valid"),
        ("ge1-0/0/10", DeviceType.SUPERSPINE, "❌ Invalid"),
        ("bundle-1", DeviceType.LEAF, "✅ Valid"),
        ("bundle-1", DeviceType.SUPERSPINE, "✅ Valid")
    ]
    
    for interface, device_type, expected in test_interfaces:
        is_valid = enhanced_classifier.validate_interface_for_device(interface, device_type)
        device_icon = enhanced_classifier.get_device_type_icon(device_type)
        
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{device_icon} {device_type.value} - {interface}: {status}")
    
    print()
    print("🎉 Enhanced Menu System Demo Complete!")
    print()
    print("Key Features Demonstrated:")
    print("• Row/Rack device selection (like original builder)")
    print("• Destination type choice (Leaf vs Superspine)")
    print("• Topology constraint validation")
    print("• Interface validation for different device types")
    print("• Enhanced error messages and user experience")

if __name__ == "__main__":
    demo_enhanced_menu_system() 