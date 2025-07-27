#!/usr/bin/env python3
"""
Demo Script for Enhanced Superspine Implementation
Showcases the enhanced Superspine destination feature with examples and validation.
"""

import json
import yaml
from pathlib import Path
import tempfile
import shutil

# Import the enhanced modules
from config_engine.enhanced_device_types import (
    DeviceType, InterfaceType, enhanced_classifier
)
from config_engine.enhanced_bridge_domain_builder import EnhancedBridgeDomainBuilder
from config_engine.enhanced_menu_system import EnhancedMenuSystem

def create_demo_topology():
    """Create a demo topology with leaf, spine, and superspine devices."""
    topology_data = {
        "devices": {
            "DNAAS-LEAF-A01": {
                "name": "DNAAS-LEAF-A01",
                "type": "leaf",
                "connected_spines": ["DNAAS-SPINE-B08"]
            },
            "DNAAS-LEAF-A02": {
                "name": "DNAAS-LEAF-A02",
                "type": "leaf",
                "connected_spines": ["DNAAS-SPINE-B08"]
            },
            "DNAAS-LEAF-B14": {
                "name": "DNAAS-LEAF-B14",
                "type": "leaf",
                "connected_spines": ["DNAAS-SPINE-D14"]
            },
            "DNAAS-SUPERSPINE-01": {
                "name": "DNAAS-SUPERSPINE-01",
                "type": "superspine",
                "connected_spines": ["DNAAS-SPINE-B08", "DNAAS-SPINE-D14"]
            },
            "DNAAS-SUPERSPINE-02": {
                "name": "DNAAS-SUPERSPINE-02",
                "type": "superspine",
                "connected_spines": ["DNAAS-SPINE-B08", "DNAAS-SPINE-D14"]
            },
            "DNAAS-SPINE-B08": {
                "name": "DNAAS-SPINE-B08",
                "type": "spine",
                "connected_leaves": ["DNAAS-LEAF-A01", "DNAAS-LEAF-A02"],
                "connected_superspines": ["DNAAS-SUPERSPINE-01", "DNAAS-SUPERSPINE-02"]
            },
            "DNAAS-SPINE-D14": {
                "name": "DNAAS-SPINE-D14",
                "type": "spine",
                "connected_leaves": ["DNAAS-LEAF-B14"],
                "connected_superspines": ["DNAAS-SUPERSPINE-01", "DNAAS-SUPERSPINE-02"]
            }
        },
        "available_leaves": ["DNAAS-LEAF-A01", "DNAAS-LEAF-A02", "DNAAS-LEAF-B14"],
        "superspine_devices": ["DNAAS-SUPERSPINE-01", "DNAAS-SUPERSPINE-02"],
        "spine_devices": ["DNAAS-SPINE-B08", "DNAAS-SPINE-D14"]
    }
    
    return topology_data

def setup_demo_environment():
    """Set up demo environment with topology files."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    topology_dir = Path(temp_dir) / "topology"
    topology_dir.mkdir()
    
    # Create topology file
    topology_data = create_demo_topology()
    topology_file = topology_dir / "complete_topology_v2.json"
    with open(topology_file, 'w') as f:
        json.dump(topology_data, f)
    
    # Create bundle mapping file
    bundle_data = {
        "DNAAS-LEAF-A01": {
            "bundle-100": ["ge100-0/0/1", "ge100-0/0/2"]
        },
        "DNAAS-SUPERSPINE-01": {
            "bundle-200": ["ge100-0/0/1", "ge100-0/0/2"]
        }
    }
    bundle_file = topology_dir / "bundle_mapping_v2.yaml"
    with open(bundle_file, 'w') as f:
        yaml.dump(bundle_data, f)
    
    return temp_dir, topology_dir

def demo_device_type_detection():
    """Demo device type detection functionality."""
    print("🔍 Device Type Detection Demo")
    print("=" * 50)
    
    test_devices = [
        "DNAAS-LEAF-A01",
        "DNAAS-SPINE-B08",
        "DNAAS-SUPERSPINE-01",
        "DNAAS-SS-02",  # SS abbreviation
        "UNKNOWN-DEVICE"
    ]
    
    for device in test_devices:
        device_type = enhanced_classifier.detect_device_type(device)
        icon = enhanced_classifier.get_device_type_icon(device_type)
        print(f"{icon} {device} → {device_type.value}")
    
    print()

def demo_interface_validation():
    """Demo interface validation for different device types."""
    print("🔌 Interface Validation Demo")
    print("=" * 50)
    
    # Test interfaces for different device types
    test_cases = [
        ("DNAAS-LEAF-A01", "ge1-0/0/1", "Access interface on Leaf"),
        ("DNAAS-LEAF-A01", "ge100-0/0/10", "Transport interface on Leaf"),
        ("DNAAS-LEAF-A01", "bundle-100", "Bundle interface on Leaf"),
        ("DNAAS-SUPERSPINE-01", "ge10-0/0/5", "10GE transport on Superspine"),
        ("DNAAS-SUPERSPINE-01", "ge100-0/0/10", "100GE transport on Superspine"),
        ("DNAAS-SUPERSPINE-01", "bundle-200", "Bundle interface on Superspine"),
        ("DNAAS-SUPERSPINE-01", "ge1-0/0/1", "Access interface on Superspine (INVALID)"),
    ]
    
    for device, interface, description in test_cases:
        device_type = enhanced_classifier.detect_device_type(device)
        is_valid = enhanced_classifier.validate_interface_for_device(interface, device_type)
        status = "✅" if is_valid else "❌"
        print(f"{status} {device}: {interface} ({description})")
    
    print()

def demo_topology_constraints():
    """Demo topology constraint validation."""
    print("🌐 Topology Constraints Demo")
    print("=" * 50)
    
    # Test topology combinations
    test_topologies = [
        ("DNAAS-LEAF-A01", "DNAAS-LEAF-A02", "Leaf → Leaf"),
        ("DNAAS-LEAF-A01", "DNAAS-SUPERSPINE-01", "Leaf → Superspine"),
        ("DNAAS-SUPERSPINE-01", "DNAAS-LEAF-A01", "Superspine → Leaf (INVALID)"),
        ("DNAAS-SUPERSPINE-01", "DNAAS-SUPERSPINE-02", "Superspine → Superspine (INVALID)"),
    ]
    
    for source, dest, description in test_topologies:
        source_type = enhanced_classifier.detect_device_type(source)
        dest_type = enhanced_classifier.detect_device_type(dest)
        is_valid = enhanced_classifier.validate_topology_constraints(source_type, dest_type)
        status = "✅" if is_valid else "❌"
        print(f"{status} {source} → {dest} ({description})")
    
    print()

def demo_enhanced_bridge_domain_builder():
    """Demo enhanced bridge domain builder functionality."""
    print("🔨 Enhanced Bridge Domain Builder Demo")
    print("=" * 50)
    
    # Set up demo environment
    temp_dir, topology_dir = setup_demo_environment()
    
    try:
        # Initialize builder
        builder = EnhancedBridgeDomainBuilder(topology_dir=str(topology_dir))
        
        # Demo available sources (leafs only)
        print("📋 Available Source Devices (Leafs only):")
        available_sources = builder.get_available_sources()
        for source in available_sources:
            icon = enhanced_classifier.get_device_type_icon(source['device_type'])
            print(f"  {icon} {source['name']} ({source['device_type'].value})")
        
        print()
        
        # Demo available destinations (leafs + superspines)
        source_device = "DNAAS-LEAF-A01"
        print(f"📋 Available Destination Devices for {source_device}:")
        available_destinations = builder.get_available_destinations(source_device)
        for dest in available_destinations:
            icon = enhanced_classifier.get_device_type_icon(dest['device_type'])
            print(f"  {icon} {dest['name']} ({dest['device_type'].value})")
        
        print()
        
        # Demo bridge domain configuration building
        print("🔨 Building Bridge Domain Configuration:")
        configs = builder.build_bridge_domain_config(
            "g_demo_v253", 253,
            "DNAAS-LEAF-A01", "ge100-0/0/10",
            "DNAAS-SUPERSPINE-01", "ge10-0/0/5"
        )
        
        # Show configuration summary
        summary = builder.get_configuration_summary(configs)
        print(summary)
        
        # Show path visualization
        metadata = configs.get('_metadata', {})
        path = metadata.get('path', [])
        if path:
            print("🌳 Path Visualization:")
            for i, device in enumerate(path):
                device_type = builder.get_device_type(device)
                icon = enhanced_classifier.get_device_type_icon(device_type)
                
                if i == 0:
                    print(f"  {icon} {device} (Source)")
                elif i == len(path) - 1:
                    print(f"  {icon} {device} (Destination)")
                else:
                    print(f"  {icon} {device} (Intermediate)")
                
                if i < len(path) - 1:
                    print("  ↓")
        
        print()
        
        # Demo error handling
        print("❌ Error Handling Demo:")
        try:
            # Try to use Superspine as source (should fail)
            builder.build_bridge_domain_config(
                "g_demo_v253", 253,
                "DNAAS-SUPERSPINE-01", "ge10-0/0/5",  # Superspine as source
                "DNAAS-LEAF-A01", "ge100-0/0/10"
            )
        except ValueError as e:
            print(f"  ✅ Caught error: {e}")
        
        try:
            # Try to use access interface on Superspine (should fail)
            builder.build_bridge_domain_config(
                "g_demo_v253", 253,
                "DNAAS-LEAF-A01", "ge100-0/0/10",
                "DNAAS-SUPERSPINE-01", "ge1-0/0/1"  # Access interface on Superspine
            )
        except ValueError as e:
            print(f"  ✅ Caught error: {e}")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def demo_enhanced_menu_system():
    """Demo enhanced menu system functionality."""
    print("🎯 Enhanced Menu System Demo")
    print("=" * 50)
    
    # Set up demo environment
    temp_dir, topology_dir = setup_demo_environment()
    
    try:
        # Initialize menu system
        menu_system = EnhancedMenuSystem()
        
        # Demo device selection menu display
        devices = [
            {"name": "DNAAS-LEAF-A01", "device_type": DeviceType.LEAF},
            {"name": "DNAAS-LEAF-A02", "device_type": DeviceType.LEAF},
            {"name": "DNAAS-SUPERSPINE-01", "device_type": DeviceType.SUPERSPINE},
            {"name": "DNAAS-SUPERSPINE-02", "device_type": DeviceType.SUPERSPINE},
        ]
        
        print("📋 Device Selection Menu Example:")
        menu_system.display_device_selection_menu(devices, "destination")
        
        print()
        
        # Demo service configuration
        print("⚙️  Service Configuration Example:")
        with open('/dev/null', 'w') as f:  # Suppress input prompts
            import sys
            original_input = sys.stdin
            sys.stdin = open('/dev/null', 'r')
            try:
                # This would normally get user input, but we're demoing the structure
                print("  Username: visaev")
                print("  VLAN ID: 253")
                print("  Service Name: g_visaev_v253")
            finally:
                sys.stdin = original_input
        
        print()
        
        # Demo error message display
        print("❌ Enhanced Error Messages:")
        context = {"source": "DNAAS-SUPERSPINE-01", "destination": "DNAAS-LEAF-A01"}
        error = ValueError("Invalid topology: Superspine devices can only be destinations")
        menu_system.display_enhanced_error_message(error, context)
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def run_comprehensive_demo():
    """Run comprehensive demo of all enhanced features."""
    print("🚀 Enhanced Superspine Implementation Demo")
    print("=" * 60)
    print("This demo showcases the enhanced Superspine destination feature")
    print("with all constraints, validations, and user experience improvements.")
    print()
    
    # Run all demos
    demo_device_type_detection()
    demo_interface_validation()
    demo_topology_constraints()
    demo_enhanced_bridge_domain_builder()
    demo_enhanced_menu_system()
    
    print("🎉 Demo completed successfully!")
    print()
    print("📋 Key Features Demonstrated:")
    print("  ✅ Enhanced device type detection with Superspine support")
    print("  ✅ Interface validation for different device types")
    print("  ✅ Topology constraint validation")
    print("  ✅ Enhanced bridge domain builder")
    print("  ✅ Improved menu system with device type indicators")
    print("  ✅ Comprehensive error handling and user feedback")
    print()
    print("🔧 Constraints Enforced:")
    print("  • Superspine devices can only be destinations (never sources)")
    print("  • No AC interfaces allowed on Superspine (transport only)")
    print("  • No Superspine → Superspine topologies")
    print("  • Support for P2P and P2MP topologies ending at Superspine")

if __name__ == "__main__":
    run_comprehensive_demo() 