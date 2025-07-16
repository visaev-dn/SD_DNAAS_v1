#!/usr/bin/env python3
"""
ASCII Topology Tree - Simple text-based visualization of spine-leaf connections
Creates a clear hierarchical view of which leaves connect to which spines using bundle information.
"""

import os
import sys
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsciiTopologyTree:
    def __init__(self):
        self.topology_file = Path('topology/complete_topology_v2.json')
        self.output_dir = Path('topology/visualizations')
        self.output_dir.mkdir(exist_ok=True)
        
        self.topology = None
        
    def load_topology(self):
        """Load topology data from JSON file."""
        logger.info("Loading topology data...")
        
        if not self.topology_file.exists():
            logger.error(f"Topology file not found: {self.topology_file}")
            logger.error("Please run topology discovery first")
            return False
        
        try:
            with open(self.topology_file, 'r') as f:
                self.topology = json.load(f)
            logger.info("Topology data loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading topology: {e}")
            return False
    
    def create_bundle_aware_tree(self):
        """Create a tree showing the complete three-tier architecture: Super Spine → Spine → Leaf."""
        logger.info("Creating three-tier topology tree...")
        
        tree = self.topology.get('tree', {})
        bundles = self.topology.get('bundles', {})
        
        if not tree:
            logger.error("No topology tree data available")
            return None
        
        superspine_devices = tree.get('superspine_devices', {})
        spine_devices = tree.get('spine_devices', {})
        
        if not superspine_devices and not spine_devices:
            logger.warning("No spine or superspine devices found")
            return None
        
        # Build three-tier tree
        tree_lines = []
        tree_lines.append("🌳 THREE-TIER TOPOLOGY TREE")
        tree_lines.append("=" * 60)
        tree_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        tree_lines.append("")
        
        # Show Super Spine → Spine → Leaf hierarchy
        for superspine_name, superspine_info in superspine_devices.items():
            tree_lines.append(f"🌲 SUPER SPINE: {superspine_name}")
            tree_lines.append(f"   📊 Bundles: {superspine_info['bundles']}, Neighbors: {superspine_info['neighbors']}")
            
            connected_spines = superspine_info.get('connected_spines', [])
            if connected_spines:
                # Group spines by their connections to leaves
                spine_leaf_map = {}
                for spine_conn in connected_spines:
                    spine_name = spine_conn['name']
                    if spine_name in spine_devices:
                        spine_info = spine_devices[spine_name]
                        connected_leaves = spine_info.get('connected_leaves', [])
                        spine_leaf_map[spine_name] = {
                            'spine_info': spine_info,
                            'spine_conn': spine_conn,
                            'connected_leaves': connected_leaves
                        }
                
                # Show each spine and its connected leaves
                spine_names = list(spine_leaf_map.keys())
                for i, spine_name in enumerate(spine_names):
                    spine_data = spine_leaf_map[spine_name]
                    spine_info = spine_data['spine_info']
                    spine_conn = spine_data['spine_conn']
                    connected_leaves = spine_data['connected_leaves']
                    
                    if i == len(spine_names) - 1:  # Last spine
                        tree_lines.append(f"    └── 🌲 SPINE: {spine_name}")
                    else:
                        tree_lines.append(f"    ├── 🌲 SPINE: {spine_name}")
                    
                    tree_lines.append(f"        📊 Bundles: {spine_info['bundles']}, Neighbors: {spine_info['neighbors']}")
                    tree_lines.append(f"        🔗 Connection: {spine_conn['local_interface']} ↔ {spine_conn['remote_interface']}")
                    
                    if connected_leaves:
                        # Group connections by leaf device
                        leaf_connections = {}
                        for conn in connected_leaves:
                            leaf_name = conn['name']
                            if leaf_name not in leaf_connections:
                                leaf_connections[leaf_name] = []
                            leaf_connections[leaf_name].append(conn)
                        
                        # Show each leaf with its bundle information
                        leaf_names = list(leaf_connections.keys())
                        for j, leaf_name in enumerate(leaf_names):
                            connections = leaf_connections[leaf_name]
                            
                            if i == len(spine_names) - 1:  # Last spine
                                if j == len(leaf_names) - 1:  # Last leaf
                                    tree_lines.append(f"            └── 🍃 {leaf_name}")
                                else:
                                    tree_lines.append(f"            ├── 🍃 {leaf_name}")
                            else:
                                if j == len(leaf_names) - 1:  # Last leaf
                                    tree_lines.append(f"    │       └── 🍃 {leaf_name}")
                                else:
                                    tree_lines.append(f"    │       ├── 🍃 {leaf_name}")
                            
                            # Find bundle information for this leaf
                            leaf_bundles = []
                            for bundle_name, bundle_info in bundles.items():
                                if bundle_info['device'] == leaf_name:
                                    # Check if this bundle connects to our spine
                                    for bundle_conn in bundle_info.get('connections', []):
                                        if bundle_conn['remote_device'] == spine_name:
                                            leaf_bundles.append({
                                                'bundle_name': bundle_name,
                                                'local_interface': bundle_conn['local_interface'],
                                                'remote_interface': bundle_conn['remote_interface']
                                            })
                            
                            # Show bundle information
                            if leaf_bundles:
                                for k, bundle in enumerate(leaf_bundles):
                                    if i == len(spine_names) - 1:  # Last spine
                                        if j == len(leaf_names) - 1:  # Last leaf
                                            if k == len(leaf_bundles) - 1:  # Last bundle
                                                tree_lines.append(f"                └── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"                    └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                                            else:
                                                tree_lines.append(f"                ├── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"                │   └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                                        else:
                                            if k == len(leaf_bundles) - 1:  # Last bundle
                                                tree_lines.append(f"            │   └── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"            │       └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                                            else:
                                                tree_lines.append(f"            │   ├── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"            │   │   └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                                    else:
                                        if j == len(leaf_names) - 1:  # Last leaf
                                            if k == len(leaf_bundles) - 1:  # Last bundle
                                                tree_lines.append(f"    │           └── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"    │               └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                                            else:
                                                tree_lines.append(f"    │           ├── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"    │           │   └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                                        else:
                                            if k == len(leaf_bundles) - 1:  # Last bundle
                                                tree_lines.append(f"    │       │   └── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"    │       │       └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                                            else:
                                                tree_lines.append(f"    │       │   ├── Bundle: {bundle['bundle_name']}")
                                                tree_lines.append(f"    │       │   │   └── {bundle['local_interface']} ↔ {bundle['remote_interface']}")
                            else:
                                # Fallback to interface connections if no bundle info
                                for k, conn in enumerate(connections):
                                    if i == len(spine_names) - 1:  # Last spine
                                        if j == len(leaf_names) - 1:  # Last leaf
                                            if k == len(connections) - 1:  # Last connection
                                                tree_lines.append(f"                └── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                            else:
                                                tree_lines.append(f"                ├── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                        else:
                                            if k == len(connections) - 1:  # Last connection
                                                tree_lines.append(f"            │   └── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                            else:
                                                tree_lines.append(f"            │   ├── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                    else:
                                        if j == len(leaf_names) - 1:  # Last leaf
                                            if k == len(connections) - 1:  # Last connection
                                                tree_lines.append(f"    │           └── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                            else:
                                                tree_lines.append(f"    │           ├── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                        else:
                                            if k == len(connections) - 1:  # Last connection
                                                tree_lines.append(f"    │       │   └── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                            else:
                                                tree_lines.append(f"    │       │   ├── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                    else:
                        if i == len(spine_names) - 1:  # Last spine
                            tree_lines.append("            └── ❌ No connected leaves")
                        else:
                            tree_lines.append("    │       └── ❌ No connected leaves")
            else:
                tree_lines.append("    └── ❌ No connected spines")
            
            tree_lines.append("")
        
        # Show standalone spine devices (not connected to super spine)
        standalone_spines = []
        for spine_name, spine_info in spine_devices.items():
            # Check if this spine is connected to any super spine
            connected_to_superspine = False
            for superspine_info in superspine_devices.values():
                for spine_conn in superspine_info.get('connected_spines', []):
                    if spine_conn['name'] == spine_name:
                        connected_to_superspine = True
                        break
                if connected_to_superspine:
                    break
            
            if not connected_to_superspine:
                standalone_spines.append((spine_name, spine_info))
        
        if standalone_spines:
            tree_lines.append("🌲 STANDALONE SPINES (Not connected to Super Spine):")
            for spine_name, spine_info in standalone_spines:
                tree_lines.append(f"    🌲 {spine_name}")
                tree_lines.append(f"        📊 Bundles: {spine_info['bundles']}, Neighbors: {spine_info['neighbors']}")
                
                connected_leaves = spine_info.get('connected_leaves', [])
                if connected_leaves:
                    # Group connections by leaf device
                    leaf_connections = {}
                    for conn in connected_leaves:
                        leaf_name = conn['name']
                        if leaf_name not in leaf_connections:
                            leaf_connections[leaf_name] = []
                        leaf_connections[leaf_name].append(conn)
                    
                    # Show each leaf
                    leaf_names = list(leaf_connections.keys())
                    for i, leaf_name in enumerate(leaf_names):
                        connections = leaf_connections[leaf_name]
                        
                        if i == len(leaf_names) - 1:  # Last leaf
                            tree_lines.append(f"        └── 🍃 {leaf_name}")
                        else:
                            tree_lines.append(f"        ├── 🍃 {leaf_name}")
                        
                        # Show interface connections
                        for j, conn in enumerate(connections):
                            if i == len(leaf_names) - 1:  # Last leaf
                                if j == len(connections) - 1:  # Last connection
                                    tree_lines.append(f"            └── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                else:
                                    tree_lines.append(f"            ├── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                            else:
                                if j == len(connections) - 1:  # Last connection
                                    tree_lines.append(f"        │   └── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                                else:
                                    tree_lines.append(f"        │   ├── Interface: {conn['local_interface']} ↔ {conn['remote_interface']}")
                else:
                    tree_lines.append("        └── ❌ No connected leaves")
                
                tree_lines.append("")
        
        # Add summary
        tree_lines.append("📊 SUMMARY:")
        tree_lines.append(f"   Super Spines: {len(superspine_devices)}")
        tree_lines.append(f"   Spines: {len(spine_devices)}")
        tree_lines.append(f"   Total Leaves: {len(tree.get('leaf_devices', {}))}")
        tree_lines.append(f"   Total Bundles: {len(bundles)}")
        tree_lines.append(f"   Total Connections: {len(self.topology['connections'])}")
        tree_lines.append("=" * 60)
        
        return tree_lines
    
    def save_bundle_aware_tree(self):
        """Save bundle-aware tree to file."""
        logger.info("Saving bundle-aware topology tree...")
        
        tree_lines = self.create_bundle_aware_tree()
        if tree_lines:
            output_file = self.output_dir / 'topology_bundle_aware_tree.txt'
            with open(output_file, 'w') as f:
                f.write('\n'.join(tree_lines))
            logger.info(f"Bundle-aware tree saved to: {output_file}")
            return output_file
        return None
    
    def print_bundle_aware_tree(self):
        """Print the bundle-aware tree to console."""
        tree_lines = self.create_bundle_aware_tree()
        if tree_lines:
            print('\n'.join(tree_lines))
    
    def run_ascii_visualization(self):
        """Run bundle-aware topology visualization."""
        logger.info("=== Starting Bundle-Aware Topology Visualization ===")
        
        # Load topology data
        if not self.load_topology():
            return False
        
        # Save bundle-aware tree
        output_file = self.save_bundle_aware_tree()
        
        # Print to console
        print("\n" + "="*80)
        print("🌳 BUNDLE-AWARE TOPOLOGY TREE")
        print("="*80)
        self.print_bundle_aware_tree()
        
        logger.info("=== Bundle-Aware Topology Visualization Complete ===")
        return True

def main():
    """Main function."""
    visualizer = AsciiTopologyTree()
    success = visualizer.run_ascii_visualization()
    
    if success:
        print("\n✅ Bundle-aware topology visualization completed successfully!")
        print("📁 Check topology/visualizations/topology_bundle_aware_tree.txt")
    else:
        print("\n❌ Bundle-aware topology visualization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 