#!/usr/bin/env python3
"""
Minimized ASCII Topology Tree - Simplified text-based visualization
Shows only logical connections between leafs, spines, and superspines without interface and bundle details.
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

class MinimizedTopologyTree:
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
    
    def create_minimized_tree(self):
        """Create a minimized tree showing only logical connections between devices."""
        logger.info("Creating minimized topology tree...")
        
        tree = self.topology.get('tree', {})
        
        if not tree:
            logger.error("No topology tree data available")
            return None
        
        superspine_devices = tree.get('superspine_devices', {})
        spine_devices = tree.get('spine_devices', {})
        
        if not superspine_devices and not spine_devices:
            logger.warning("No spine or superspine devices found")
            return None
        
        # Build minimized tree
        tree_lines = []
        tree_lines.append("🌳 MINIMIZED TOPOLOGY TREE")
        tree_lines.append("=" * 50)
        tree_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        tree_lines.append("📋 Shows only logical connections between devices")
        tree_lines.append("")
        
        # Show Super Spine → Spine → Leaf hierarchy (minimized)
        for superspine_name, superspine_info in superspine_devices.items():
            tree_lines.append(f"🌲 SUPER SPINE: {superspine_name}")
            
            connected_spines = superspine_info.get('connected_spines', [])
            if connected_spines:
                # Get unique spine names
                spine_names = list(set([conn['name'] for conn in connected_spines]))
                
                # Show each spine and its connected leaves
                for i, spine_name in enumerate(spine_names):
                    if spine_name in spine_devices:
                        spine_info = spine_devices[spine_name]
                        connected_leaves = spine_info.get('connected_leaves', [])
                        
                        if i == len(spine_names) - 1:  # Last spine
                            tree_lines.append(f"    └── 🌲 SPINE: {spine_name}")
                        else:
                            tree_lines.append(f"    ├── 🌲 SPINE: {spine_name}")
                        
                        if connected_leaves:
                            # Get unique leaf names
                            leaf_names = list(set([conn['name'] for conn in connected_leaves]))
                            
                            # Show each leaf
                            for j, leaf_name in enumerate(leaf_names):
                                if i == len(spine_names) - 1:  # Last spine
                                    if j == len(leaf_names) - 1:  # Last leaf
                                        tree_lines.append(f"        └── 🍃 {leaf_name}")
                                    else:
                                        tree_lines.append(f"        ├── 🍃 {leaf_name}")
                                else:
                                    if j == len(leaf_names) - 1:  # Last leaf
                                        tree_lines.append(f"    │   └── 🍃 {leaf_name}")
                                    else:
                                        tree_lines.append(f"    │   ├── 🍃 {leaf_name}")
                        else:
                            if i == len(spine_names) - 1:  # Last spine
                                tree_lines.append("        └── ❌ No connected leaves")
                            else:
                                tree_lines.append("    │   └── ❌ No connected leaves")
                    else:
                        if i == len(spine_names) - 1:  # Last spine
                            tree_lines.append(f"    └── 🌲 SPINE: {spine_name} (Not in topology)")
                        else:
                            tree_lines.append(f"    ├── 🌲 SPINE: {spine_name} (Not in topology)")
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
                
                connected_leaves = spine_info.get('connected_leaves', [])
                if connected_leaves:
                    # Get unique leaf names
                    leaf_names = list(set([conn['name'] for conn in connected_leaves]))
                    
                    # Show each leaf
                    for i, leaf_name in enumerate(leaf_names):
                        if i == len(leaf_names) - 1:  # Last leaf
                            tree_lines.append(f"        └── 🍃 {leaf_name}")
                        else:
                            tree_lines.append(f"        ├── 🍃 {leaf_name}")
                else:
                    tree_lines.append("        └── ❌ No connected leaves")
                
                tree_lines.append("")
        
        # Add summary
        tree_lines.append("📊 SUMMARY:")
        tree_lines.append(f"   Super Spines: {len(superspine_devices)}")
        tree_lines.append(f"   Spines: {len(spine_devices)}")
        tree_lines.append(f"   Total Leaves: {len(tree.get('leaf_devices', {}))}")
        
        # Count total connections
        total_connections = 0
        for superspine_info in superspine_devices.values():
            total_connections += len(superspine_info.get('connected_spines', []))
        for spine_info in spine_devices.values():
            total_connections += len(spine_info.get('connected_leaves', []))
        
        tree_lines.append(f"   Total Logical Connections: {total_connections}")
        tree_lines.append("=" * 50)
        
        return tree_lines
    
    def save_minimized_tree(self):
        """Save minimized tree to file."""
        logger.info("Saving minimized topology tree...")
        
        tree_lines = self.create_minimized_tree()
        if tree_lines:
            output_file = self.output_dir / 'topology_minimized_tree.txt'
            with open(output_file, 'w') as f:
                f.write('\n'.join(tree_lines))
            logger.info(f"Minimized tree saved to: {output_file}")
            return output_file
        return None
    
    def print_minimized_tree(self):
        """Print the minimized tree to console."""
        tree_lines = self.create_minimized_tree()
        if tree_lines:
            print('\n'.join(tree_lines))
    
    def run_minimized_visualization(self):
        """Run minimized topology visualization."""
        logger.info("=== Starting Minimized Topology Visualization ===")
        
        # Load topology data
        if not self.load_topology():
            return False
        
        # Save minimized tree
        output_file = self.save_minimized_tree()
        
        # Print to console
        print("\n" + "="*80)
        print("🌳 MINIMIZED TOPOLOGY TREE")
        print("="*80)
        self.print_minimized_tree()
        
        logger.info("=== Minimized Topology Visualization Complete ===")
        return True

def main():
    """Main function."""
    visualizer = MinimizedTopologyTree()
    success = visualizer.run_minimized_visualization()
    
    if success:
        print("\n✅ Minimized topology visualization completed successfully!")
        print("📁 Check topology/visualizations/topology_minimized_tree.txt")
    else:
        print("\n❌ Minimized topology visualization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 