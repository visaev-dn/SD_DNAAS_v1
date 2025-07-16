#!/usr/bin/env python3
"""
Complete Topology Mapping Script
Maps the entire network topology including bundle mappings and spine-leaf connections
"""

import yaml
import os
import sys
from collections import defaultdict
from pathlib import Path

def load_yaml_file(file_path):
    """Load YAML file safely"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def analyze_topology():
    """Analyze the complete topology with bundle mappings only"""
    
    # Load topology data
    topology_dir = Path(__file__).parent.parent / 'topology'
    
    # Load bundle mappings
    bundle_mapping_file = topology_dir / 'bundle_interface_mapping.yaml'
    bundle_mappings = load_yaml_file(bundle_mapping_file)
    
    if not bundle_mappings:
        print("❌ Failed to load bundle mappings")
        return None
    
    print("🌐 Complete Network Topology Analysis (Bundle-Based)")
    print("=" * 80)
    
    # Analyze bundle mappings
    print("\n📦 Bundle Interface Mappings:")
    print("-" * 40)
    
    bundle_summary = defaultdict(list)
    device_bundles = defaultdict(set)
    
    for device, mappings in bundle_mappings.items():
        print(f"\n🔧 {device}:")
        if mappings:
            for phys_intf, bundle_name in mappings.items():
                print(f"  {phys_intf} → {bundle_name}")
                bundle_summary[bundle_name].append((device, phys_intf))
                device_bundles[device].add(bundle_name)
        else:
            print("  No bundle mappings found")
    
    # Analyze bundle patterns to infer topology
    print("\n🔍 Bundle Analysis:")
    print("-" * 40)
    
    # Group bundles by name pattern
    bundle_patterns = defaultdict(list)
    for bundle_name, mappings in bundle_summary.items():
        bundle_patterns[bundle_name].extend(mappings)
    
    # Identify spine and leaf devices based on bundle patterns
    spine_devices = set()
    leaf_devices = set()
    
    # Look for bundle patterns that suggest spine-leaf connections
    # Bundles like bundle-60000, bundle-60001, etc. typically connect spine to leaf
    for bundle_name, mappings in bundle_patterns.items():
        if bundle_name.startswith('bundle-6000'):
            # This is likely a spine-leaf bundle
            for device, interface in mappings:
                if device.startswith('spine'):
                    spine_devices.add(device)
                elif device.startswith('leaf'):
                    leaf_devices.add(device)
    
    # If no spine devices found, check all devices
    if not spine_devices:
        for device in bundle_mappings.keys():
            if device.startswith('spine'):
                spine_devices.add(device)
            elif device.startswith('leaf'):
                leaf_devices.add(device)
    
    # Create inferred connections based on bundle patterns
    inferred_connections = []
    
    # Look for matching bundle names across devices
    for bundle_name, mappings in bundle_patterns.items():
        if len(mappings) > 1:  # Multiple devices use this bundle
            devices_in_bundle = [device for device, _ in mappings]
            unique_devices = list(set(devices_in_bundle))  # Remove duplicates
            
            if len(unique_devices) == 2:  # Direct connection between 2 devices
                device1, device2 = unique_devices
                interface1 = next(intf for dev, intf in mappings if dev == device1)
                interface2 = next(intf for dev, intf in mappings if dev == device2)
                
                connection = {
                    'device1': device1,
                    'device2': device2,
                    'interface1': interface1,
                    'interface2': interface2,
                    'bundle': bundle_name,
                    'type': 'bundle'
                }
                inferred_connections.append(connection)
            elif len(unique_devices) > 2:  # Multiple devices share this bundle
                # This could be a spine connecting to multiple leafs
                # Find spine and leaf devices
                spine_devices_in_bundle = [d for d in unique_devices if d.startswith('spine')]
                leaf_devices_in_bundle = [d for d in unique_devices if d.startswith('leaf')]
                
                # Create connections between spine and each leaf
                for spine in spine_devices_in_bundle:
                    for leaf in leaf_devices_in_bundle:
                        spine_intf = next(intf for dev, intf in mappings if dev == spine)
                        leaf_intf = next(intf for dev, intf in mappings if dev == leaf)
                        
                        connection = {
                            'device1': spine,
                            'device2': leaf,
                            'interface1': spine_intf,
                            'interface2': leaf_intf,
                            'bundle': bundle_name,
                            'type': 'bundle'
                        }
                        inferred_connections.append(connection)
    
    # Display inferred connections
    print("\n🔗 Inferred Bundle Connections:")
    print("-" * 40)
    
    spine_leaf_connections = []
    for conn in inferred_connections:
        device1 = conn['device1']
        device2 = conn['device2']
        interface1 = conn['interface1']
        interface2 = conn['interface2']
        bundle = conn['bundle']
        
        print(f"  {device1}:{interface1} ↔ {device2}:{interface2} (via {bundle})")
        
        # Check if this is a spine-leaf connection
        if (device1.startswith('spine') and device2.startswith('leaf')) or \
           (device2.startswith('spine') and device1.startswith('leaf')):
            spine_leaf_connections.append(conn)
    
    # Create topology summary
    print("\n📊 Topology Summary:")
    print("-" * 40)
    
    print(f"🌳 Spine Devices: {', '.join(sorted(spine_devices))}")
    print(f"🍃 Leaf Devices: {', '.join(sorted(leaf_devices))}")
    print(f"🔗 Total Inferred Connections: {len(inferred_connections)}")
    print(f"🌳 Spine-Leaf Connections: {len(spine_leaf_connections)}")
    print(f"📦 Total Bundles: {len(bundle_patterns)}")
    
    # Show device details
    print("\n📋 Device Details:")
    print("-" * 40)
    
    for device_name in bundle_mappings.keys():
        bundles = device_bundles.get(device_name, set())
        print(f"\n🔧 {device_name}:")
        print(f"  Bundles: {len(bundles)}")
        for bundle in sorted(bundles):
            print(f"    - {bundle}")
    
    # Create visual topology map
    print("\n🗺️  Visual Topology Map:")
    print("-" * 40)
    
    # Group leafs by their spine connections
    spine_leaf_map = defaultdict(list)
    for conn in spine_leaf_connections:
        if conn['device1'].startswith('spine'):
            spine = conn['device1']
            leaf = conn['device2']
        else:
            spine = conn['device2']
            leaf = conn['device1']
        
        spine_leaf_map[spine].append(leaf)
    
    # If no spine-leaf connections found, show bundle-based connections
    if not spine_leaf_map:
        print("  No direct spine-leaf connections detected.")
        print("  Showing bundle-based connections:")
        
        # Group by bundles
        bundle_connections = defaultdict(list)
        for conn in inferred_connections:
            bundle_connections[conn['bundle']].append(conn)
        
        for bundle_name, connections in bundle_connections.items():
            print(f"\n  📦 Bundle {bundle_name}:")
            for conn in connections:
                print(f"    {conn['device1']}:{conn['interface1']} ↔ {conn['device2']}:{conn['interface2']}")
    else:
        for spine in sorted(spine_leaf_map.keys()):
            print(f"\n{spine}:")
            for leaf in sorted(spine_leaf_map[spine]):
                print(f"  └── {leaf}")
    
    return {
        'bundle_mappings': bundle_mappings,
        'spine_leaf_connections': spine_leaf_connections,
        'bundle_connections': inferred_connections,
        'spine_devices': list(spine_devices),
        'leaf_devices': list(leaf_devices),
        'total_connections': len(inferred_connections),
        'bundle_patterns': dict(bundle_patterns),
        'device_bundles': dict(device_bundles)
    }

def main():
    """Main function"""
    print("🚀 Complete Topology Mapping Tool")
    print("=" * 80)
    
    # Run analysis
    analysis = analyze_topology()
    
    if analysis:
        print("\n✅ Topology analysis completed successfully!")
        print("\n💡 Key Findings:")
        print(f"  • {len(analysis['spine_devices'])} spine device(s)")
        print(f"  • {len(analysis['leaf_devices'])} leaf device(s)")
        print(f"  • {analysis['total_connections']} total connections")
        print(f"  • {len(analysis['spine_leaf_connections'])} spine-leaf connections")
        print(f"  • {len(analysis['bundle_connections'])} bundle-based connections")
    else:
        print("❌ Topology analysis failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())