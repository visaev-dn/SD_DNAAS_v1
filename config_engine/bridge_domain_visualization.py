#!/usr/bin/env python3
"""
Bridge Domain Visualization Engine

This module provides ASCII visualization capabilities for discovered bridge domain topologies.
It creates P2P and P2MP topology diagrams based on the bridge domain mapping data.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from difflib import get_close_matches

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class BridgeDomainVisualization:
    """
    Bridge Domain Visualization Engine
    
    Creates ASCII tree diagrams for bridge domain topologies discovered from JSON mapping data.
    Supports both P2P and P2MP visualizations with fuzzy matching for bridge domain names.
    """
    
    def __init__(self):
        self.output_dir = Path('topology/bridge_domain_visualization')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_latest_mapping(self) -> Optional[Dict]:
        """
        Load the latest bridge domain mapping file.
        
        Returns:
            Mapping data or None if not found
        """
        mapping_dir = Path("topology/bridge_domain_discovery")
        mapping_files = list(mapping_dir.glob("bridge_domain_mapping_*.json"))
        if not mapping_files:
            return None
        
        latest_file = max(mapping_files, key=lambda x: x.stat().st_mtime)
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading mapping file {latest_file}: {e}")
            return None
    
    def find_similar_bridge_domains(self, service_name: str, available_bridge_domains: List[str]) -> List[str]:
        """
        Find similar bridge domain names using fuzzy matching.
        
        Args:
            service_name: The input service name
            available_bridge_domains: List of available bridge domain names
            
        Returns:
            List of similar bridge domain names
        """
        if not available_bridge_domains:
            return []
        
        # Use difflib to find close matches with very lenient cutoff
        matches = get_close_matches(service_name, available_bridge_domains, n=10, cutoff=0.2)
        
        # Also check for partial matches (contains the input string)
        partial_matches = []
        for bd in available_bridge_domains:
            bd_lower = bd.lower()
            service_lower = service_name.lower()
            
            # Check if service name is contained in bridge domain name
            if service_lower in bd_lower:
                if bd not in matches:
                    partial_matches.append(bd)
            
            # Check if bridge domain username is contained in service name
            # Extract username from bridge domain (e.g., g_username_v123 -> username)
            if '_' in bd:
                parts = bd.split('_')
                if len(parts) >= 2:
                    username = parts[1]
                    if username.lower() in service_lower:
                        if bd not in matches and bd not in partial_matches:
                            partial_matches.append(bd)
        
        # Combine exact matches, fuzzy matches, and partial matches
        all_matches = matches + partial_matches
        
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in all_matches:
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)
        
        return unique_matches[:5]  # Limit to 5 suggestions
    
    def count_total_interfaces(self, bridge_domain_data: Dict) -> int:
        """
        Count total number of interfaces across all devices.
        
        Args:
            bridge_domain_data: Bridge domain data
            
        Returns:
            Total number of interfaces
        """
        total_interfaces = 0
        devices = bridge_domain_data.get('devices', {})
        
        for device_name, device_info in devices.items():
            interfaces = device_info.get('interfaces', [])
            total_interfaces += len(interfaces)
        
        return total_interfaces
    
    def count_access_interfaces(self, bridge_domain_data: Dict) -> int:
        """
        Count actual access interfaces across all devices.
        
        Args:
            bridge_domain_data: Bridge domain data
            
        Returns:
            Number of access interfaces
        """
        access_interfaces = 0
        devices = bridge_domain_data.get('devices', {})
        
        for device_name, device_info in devices.items():
            interfaces = device_info.get('interfaces', [])
            for interface in interfaces:
                if isinstance(interface, dict) and interface.get('role') == 'access':
                    access_interfaces += 1
        
        return access_interfaces
    
    def calculate_topology_summary(self, bridge_domain_data: Dict) -> Dict:
        """
        Calculate topology summary information.
        
        Args:
            bridge_domain_data: Bridge domain data
            
        Returns:
            Summary information dictionary
        """
        devices = bridge_domain_data.get('devices', {})
        topology_analysis = bridge_domain_data.get('topology_analysis', {})
        
        return {
            'total_devices': len(devices),
            'total_interfaces': topology_analysis.get('total_interfaces', 0),
            'access_interfaces': topology_analysis.get('access_interfaces', 0),
            'path_complexity': topology_analysis.get('path_complexity', 'unknown'),
            'estimated_bandwidth': topology_analysis.get('estimated_bandwidth', 'unknown'),
            'confidence': bridge_domain_data.get('confidence', 0),
            'detection_method': bridge_domain_data.get('detection_method', 'unknown'),
            'username': bridge_domain_data.get('detected_username', 'unknown'),
            'vlan': bridge_domain_data.get('detected_vlan', 'unknown'),
            'topology_type': bridge_domain_data.get('topology_type', 'unknown')
        }
    
    def format_interface_details(self, interface: Dict) -> str:
        """
        Format interface information consistently.
        
        Args:
            interface: Interface data dictionary
            
        Returns:
            Formatted interface string
        """
        name = interface.get('name', '')
        vlan_id = interface.get('vlan_id', '')
        role = interface.get('role', '')
        interface_type = interface.get('type', '')
        
        if vlan_id:
            return f"{name} (VLAN {vlan_id}, {role}, {interface_type})"
        else:
            return f"{name} ({role}, {interface_type})"
    
    def create_p2p_visualization(self, bridge_domain_data: Dict) -> str:
        """
        Create P2P bridge domain visualization (horizontal flow).
        
        Args:
            bridge_domain_data: Bridge domain data
            
        Returns:
            ASCII visualization string
        """
        service_name = bridge_domain_data.get('service_name', 'unknown')
        summary = self.calculate_topology_summary(bridge_domain_data)
        devices = bridge_domain_data.get('devices', {})
        
        # Build visualization
        lines = []
        lines.append(f"🌐 {service_name} (VLAN {summary['vlan']}) - P2P Topology")
        lines.append("═" * 80)
        lines.append("")
        lines.append(f"📊 Summary: {summary['total_devices']} devices, {summary['total_interfaces']} total interfaces ({summary['access_interfaces']} access), {summary['path_complexity']} path, ~{summary['estimated_bandwidth']} bandwidth")
        lines.append(f"🔧 Admin State: enabled (all devices)")
        lines.append(f"🎯 Confidence: {summary['confidence']}% ({summary['detection_method']})")
        lines.append(f"👤 Username: {summary['username']}")
        lines.append("")
        
        # For P2P, show devices in a simple horizontal flow
        if len(devices) == 1:
            # Single device case
            device_name = list(devices.keys())[0]
            device_info = devices[device_name]
            device_type = device_info.get('device_type', 'unknown')
            admin_state = device_info.get('admin_state', 'unknown')
            
            lines.append(f"┌─────────────────┐")
            lines.append(f"│ {device_name}")
            lines.append(f"│   (device_type: {device_type})")
            lines.append(f"│   (admin_state: {admin_state})")
            lines.append(f"└─────────────────┘")
            lines.append("")
            
            # Show interfaces
            interfaces = device_info.get('interfaces', [])
            if interfaces:
                lines.append("Interface Details:")
                for interface in interfaces:
                    lines.append(f"• {self.format_interface_details(interface)}")
        else:
            # Multiple devices case (should be rare for P2P)
            lines.append("LEAF DEVICES                    SPINE DEVICES                    LEAF DEVICES")
            
            # Group devices by type
            leaf_devices = []
            spine_devices = []
            
            for device_name, device_info in devices.items():
                device_type = device_info.get('device_type', 'unknown')
                if device_type == 'leaf':
                    leaf_devices.append((device_name, device_info))
                elif device_type == 'spine':
                    spine_devices.append((device_name, device_info))
            
            # Show connections
            for i, (device_name, device_info) in enumerate(leaf_devices):
                device_type = device_info.get('device_type', 'unknown')
                admin_state = device_info.get('admin_state', 'unknown')
                
                if i == 0:
                    # First leaf device
                    lines.append(f"┌─────────────────┐")
                    lines.append(f"│ {device_name}")
                    lines.append(f"│   (device_type: {device_type})")
                    lines.append(f"│   (admin_state: {admin_state})")
                    
                    # Show access interfaces directly on the leaf device
                    interfaces = device_info.get('interfaces', [])
                    access_interfaces = [iface for iface in interfaces if iface.get('role') == 'access']
                    uplink_interfaces = [iface for iface in interfaces if iface.get('role') == 'uplink']
                    
                    if access_interfaces:
                        lines.append(f"│")
                        lines.append(f"│ 🔌 ACCESS INTERFACES:")
                        for interface in access_interfaces:
                            lines.append(f"│   • {self.format_interface_details(interface)}")
                    
                    lines.append(f"└─────────┬───────┘")
                    lines.append(f"          │")
                    
                    # Show uplink interfaces in connection lines
                    if uplink_interfaces:
                        for interface in uplink_interfaces:
                            lines.append(f"          │ {self.format_interface_details(interface)}")
                    lines.append(f"          │")
                    
                    # Connect to spine if available
                    if spine_devices:
                        spine_name, spine_info = spine_devices[0]
                        spine_type = spine_info.get('device_type', 'unknown')
                        spine_admin = spine_info.get('admin_state', 'unknown')
                        
                        lines.append(f"          ▼")
                        lines.append(f"┌─────────────────┐")
                        lines.append(f"│ {spine_name}")
                        lines.append(f"│   (device_type: {spine_type})")
                        lines.append(f"│   (admin_state: {spine_admin})")
                        lines.append(f"└─────────┬───────┘")
                        lines.append(f"          │")
                        
                        # Show spine interfaces
                        spine_interfaces = spine_info.get('interfaces', [])
                        for interface in spine_interfaces:
                            lines.append(f"          │ {self.format_interface_details(interface)}")
                        lines.append(f"          │")
                        lines.append(f"          ▼")
                        
                        # Connect to second leaf if available
                        if len(leaf_devices) > 1:
                            second_leaf_name, second_leaf_info = leaf_devices[1]
                            second_leaf_type = second_leaf_info.get('device_type', 'unknown')
                            second_leaf_admin = second_leaf_info.get('admin_state', 'unknown')
                            
                            lines.append(f"┌─────────────────┐")
                            lines.append(f"│ {second_leaf_name}")
                            lines.append(f"│   (device_type: {second_leaf_type})")
                            lines.append(f"│   (admin_state: {second_leaf_admin})")
                            
                            # Show access interfaces directly on the second leaf device
                            second_leaf_interfaces = second_leaf_info.get('interfaces', [])
                            second_leaf_access = [iface for iface in second_leaf_interfaces if iface.get('role') == 'access']
                            second_leaf_uplink = [iface for iface in second_leaf_interfaces if iface.get('role') == 'uplink']
                            
                            if second_leaf_access:
                                lines.append(f"│")
                                lines.append(f"│ 🔌 ACCESS INTERFACES:")
                                for interface in second_leaf_access:
                                    lines.append(f"│   • {self.format_interface_details(interface)}")
                            
                            lines.append(f"└─────────────────┘")
                            
                            # Show uplink interfaces for second leaf
                            if second_leaf_uplink:
                                lines.append("")
                                lines.append("Second Leaf Uplink Interfaces:")
                                for interface in second_leaf_uplink:
                                    lines.append(f"• {self.format_interface_details(interface)}")
        
        return "\n".join(lines)
    
    def create_p2mp_visualization(self, bridge_domain_data: Dict) -> str:
        """
        Create P2MP bridge domain visualization (grouped by device type).
        
        Args:
            bridge_domain_data: Bridge domain data
            
        Returns:
            ASCII visualization string
        """
        service_name = bridge_domain_data.get('service_name', 'unknown')
        summary = self.calculate_topology_summary(bridge_domain_data)
        devices = bridge_domain_data.get('devices', {})
        
        # Build visualization
        lines = []
        lines.append(f"🌐 {service_name} (VLAN {summary['vlan']}) - P2MP Topology")
        lines.append("═" * 80)
        lines.append("")
        lines.append(f"📊 Summary: {summary['total_devices']} devices, {summary['total_interfaces']} total interfaces ({summary['access_interfaces']} access), {summary['path_complexity']} path, ~{summary['estimated_bandwidth']} bandwidth")
        lines.append(f"🔧 Admin State: enabled (all devices)")
        lines.append(f"🎯 Confidence: {summary['confidence']}% ({summary['detection_method']})")
        lines.append(f"👤 Username: {summary['username']}")
        lines.append("")
        
        # Group devices by type
        leaf_devices = []
        spine_devices = []
        superspine_devices = []
        
        for device_name, device_info in devices.items():
            device_type = device_info.get('device_type', 'unknown')
            if device_type == 'leaf':
                leaf_devices.append((device_name, device_info))
            elif device_type == 'spine':
                spine_devices.append((device_name, device_info))
            elif device_type == 'superspine':
                superspine_devices.append((device_name, device_info))
        
        # Show leaf devices
        if leaf_devices:
            lines.append(f"🌿 LEAF DEVICES ({len(leaf_devices)} total)")
            for i, (device_name, device_info) in enumerate(leaf_devices[:5]):  # Show first 5
                device_type = device_info.get('device_type', 'unknown')
                admin_state = device_info.get('admin_state', 'unknown')
                
                if i == len(leaf_devices) - 1 or i == 4:
                    lines.append(f"└─ {device_name} (device_type: {device_type}, admin_state: {admin_state})")
                else:
                    lines.append(f"├─ {device_name} (device_type: {device_type}, admin_state: {admin_state})")
                
                # Separate access and uplink interfaces
                interfaces = device_info.get('interfaces', [])
                access_interfaces = [iface for iface in interfaces if iface.get('role') == 'access']
                uplink_interfaces = [iface for iface in interfaces if iface.get('role') == 'uplink']
                
                # Show access interfaces first (more important for topology)
                if access_interfaces:
                    if i == len(leaf_devices) - 1 or i == 4:
                        lines.append(f"   └─ 🔌 ACCESS INTERFACES:")
                    else:
                        lines.append(f"   ├─ 🔌 ACCESS INTERFACES:")
                    
                    for j, interface in enumerate(access_interfaces):
                        if j == len(access_interfaces) - 1:
                            if i == len(leaf_devices) - 1 or i == 4:
                                lines.append(f"      └─ {self.format_interface_details(interface)}")
                            else:
                                lines.append(f"      ├─ {self.format_interface_details(interface)}")
                        else:
                            lines.append(f"      ├─ {self.format_interface_details(interface)}")
                
                # Show uplink interfaces
                if uplink_interfaces:
                    if i == len(leaf_devices) - 1 or i == 4:
                        lines.append(f"   └─ 🔗 UPLINK INTERFACES:")
                    else:
                        lines.append(f"   ├─ 🔗 UPLINK INTERFACES:")
                    
                    for j, interface in enumerate(uplink_interfaces):
                        if j == len(uplink_interfaces) - 1:
                            if i == len(leaf_devices) - 1 or i == 4:
                                lines.append(f"      └─ {self.format_interface_details(interface)}")
                            else:
                                lines.append(f"      ├─ {self.format_interface_details(interface)}")
                        else:
                            lines.append(f"      ├─ {self.format_interface_details(interface)}")
            
            if len(leaf_devices) > 5:
                lines.append(f"   └─ ... +{len(leaf_devices) - 5} more leaf devices")
            lines.append("")
        
        # Show spine devices
        if spine_devices:
            lines.append(f"🌳 SPINE DEVICES ({len(spine_devices)} total)")
            for i, (device_name, device_info) in enumerate(spine_devices[:3]):  # Show first 3
                device_type = device_info.get('device_type', 'unknown')
                admin_state = device_info.get('admin_state', 'unknown')
                
                if i == len(spine_devices) - 1 or i == 2:
                    lines.append(f"└─ {device_name} (device_type: {device_type}, admin_state: {admin_state})")
                else:
                    lines.append(f"├─ {device_name} (device_type: {device_type}, admin_state: {admin_state})")
                
                # Separate downlink and uplink interfaces for spines
                interfaces = device_info.get('interfaces', [])
                downlink_interfaces = [iface for iface in interfaces if iface.get('role') == 'downlink']
                uplink_interfaces = [iface for iface in interfaces if iface.get('role') == 'uplink']
                
                # Show downlink interfaces first (connections to leaves)
                if downlink_interfaces:
                    if i == len(spine_devices) - 1 or i == 2:
                        lines.append(f"   └─ 🔽 DOWNLINK INTERFACES:")
                    else:
                        lines.append(f"   ├─ 🔽 DOWNLINK INTERFACES:")
                    
                    for j, interface in enumerate(downlink_interfaces):
                        if j == len(downlink_interfaces) - 1:
                            if i == len(spine_devices) - 1 or i == 2:
                                lines.append(f"      └─ {self.format_interface_details(interface)}")
                            else:
                                lines.append(f"      ├─ {self.format_interface_details(interface)}")
                        else:
                            lines.append(f"      ├─ {self.format_interface_details(interface)}")
                
                # Show uplink interfaces
                if uplink_interfaces:
                    if i == len(spine_devices) - 1 or i == 2:
                        lines.append(f"   └─ 🔼 UPLINK INTERFACES:")
                    else:
                        lines.append(f"   ├─ 🔼 UPLINK INTERFACES:")
                    
                    for j, interface in enumerate(uplink_interfaces):
                        if j == len(uplink_interfaces) - 1:
                            if i == len(spine_devices) - 1 or i == 2:
                                lines.append(f"      └─ {self.format_interface_details(interface)}")
                            else:
                                lines.append(f"      ├─ {self.format_interface_details(interface)}")
                        else:
                            lines.append(f"      ├─ {self.format_interface_details(interface)}")
                
                if len(interfaces) > 5:
                    lines.append(f"   └─ ... +{len(interfaces) - 5} more interfaces")
            
            if len(spine_devices) > 3:
                lines.append(f"   └─ ... +{len(spine_devices) - 3} more spine devices")
            lines.append("")
        
        # Show superspine devices
        if superspine_devices:
            lines.append(f"🏔️ SUPERSPINE DEVICES ({len(superspine_devices)} total)")
            for i, (device_name, device_info) in enumerate(superspine_devices):
                device_type = device_info.get('device_type', 'unknown')
                admin_state = device_info.get('admin_state', 'unknown')
                
                if i == len(superspine_devices) - 1:
                    lines.append(f"└─ {device_name} (device_type: {device_type}, admin_state: {admin_state})")
                else:
                    lines.append(f"├─ {device_name} (device_type: {device_type}, admin_state: {admin_state})")
                
                interfaces = device_info.get('interfaces', [])
                for j, interface in enumerate(interfaces):
                    if j == len(interfaces) - 1:
                        if i == len(superspine_devices) - 1:
                            lines.append(f"   └─ {self.format_interface_details(interface)}")
                        else:
                            lines.append(f"   ├─ {self.format_interface_details(interface)}")
                    else:
                        lines.append(f"   ├─ {self.format_interface_details(interface)}")
                
                if len(interfaces) > 5:
                    lines.append(f"   └─ ... +{len(interfaces) - 5} more interfaces")
        
        return "\n".join(lines)
    
    def visualize_bridge_domain_topology(self, service_name: str, mapping_data: Dict) -> str:
        """
        Main function to visualize bridge domain topology.
        This function is called by run_visualization after interactive prompts are handled.
        
        Args:
            service_name: Name of the bridge domain to visualize
            mapping_data: Bridge domain mapping data
            
        Returns:
            ASCII visualization string
        """
        # Extract bridge domain data
        bridge_domains = mapping_data.get('bridge_domains', {})
        bridge_domain_data = bridge_domains.get(service_name)
        
        if not bridge_domain_data:
            # This should not happen in run_visualization since interactive logic handles it
            return f"❌ Bridge domain '{service_name}' not found."
        
        # Count access interfaces (ACs) for topology determination
        access_interfaces_count = self.count_access_interfaces(bridge_domain_data)
        
        # Determine visualization type based on Access Circuits (ACs) - actual access interfaces
        if access_interfaces_count == 2:
            return self.create_p2p_visualization(bridge_domain_data)
        elif access_interfaces_count > 2:
            return self.create_p2mp_visualization(bridge_domain_data)
        else:
            # Unknown topology (1 AC or 0 ACs)
            return self.create_p2mp_visualization(bridge_domain_data)  # Default to P2MP for unknown
    
    def run_visualization(self):
        """
        Interactive function to visualize bridge domain topologies.
        """
        # Load mapping data
        mapping = self.load_latest_mapping()
        if not mapping:
            print("❌ No bridge domain mapping found. Please run bridge domain discovery first.")
            return
        
        # Show available bridge domains
        bridge_domains = list(mapping.get('bridge_domains', {}).keys())
        if not bridge_domains:
            print("❌ No bridge domains found in mapping data.")
            return
        
        print(f"📋 Available Bridge Domains ({len(bridge_domains)}):")
        for i, bd in enumerate(bridge_domains[:20], 1):
            print(f"   {i}. {bd}")
        if len(bridge_domains) > 20:
            print(f"   ... and {len(bridge_domains) - 20} more")
        
        # Main interactive loop
        while True:
            # Prompt for selection
            service_name = input("\n🌐 Enter bridge domain name to visualize: ").strip()
            if not service_name:
                print("❌ No bridge domain name provided.")
                continue
            
            # Check if bridge domain exists
            bridge_domains_dict = mapping.get('bridge_domains', {})
            if service_name in bridge_domains_dict:
                # Found a valid bridge domain, break out of the loop
                break
            
            # Try fuzzy matching
            similar_names = self.find_similar_bridge_domains(service_name, bridge_domains)
            
            if similar_names:
                print(f"\n❌ Bridge domain '{service_name}' not found.")
                print("\nDid you mean one of these?")
                for i, name in enumerate(similar_names, 1):
                    print(f"{i}. {name}")
                print(f"{len(similar_names) + 1}. Enter a different name")
                print(f"{len(similar_names) + 2}. Cancel")
                
                while True:
                    try:
                        choice = input(f"\nSelect an option [1-{len(similar_names) + 2}]: ").strip()
                        choice_num = int(choice)
                        
                        if 1 <= choice_num <= len(similar_names):
                            # User selected one of the suggested names
                            selected_name = similar_names[choice_num - 1]
                            print(f"✅ Selected: {selected_name}")
                            service_name = selected_name
                            # Break out of the inner loop and continue with the main loop
                            break
                        elif choice_num == len(similar_names) + 1:
                            # User wants to enter a different name - continue with main loop
                            break
                        elif choice_num == len(similar_names) + 2:
                            # User wants to cancel
                            print("❌ Operation cancelled.")
                            return
                        else:
                            print(f"❌ Invalid choice. Please select 1-{len(similar_names) + 2}.")
                    except ValueError:
                        print(f"❌ Invalid input. Please enter a number 1-{len(similar_names) + 2}.")
                
                # If user selected a suggested name, break out of main loop
                if service_name in bridge_domains_dict:
                    break
                # Otherwise, continue with the main loop to get another input
                
            else:
                # No fuzzy matches found, but still provide interactive options
                print(f"\n❌ Bridge domain '{service_name}' not found.")
                print("\nAvailable bridge domains:")
                for i, name in enumerate(bridge_domains[:10], 1):
                    print(f"{i}. {name}")
                if len(bridge_domains) > 10:
                    print(f"... and {len(bridge_domains) - 10} more")
                
                print(f"\nOptions:")
                print(f"1. Enter a different name")
                print(f"2. Cancel")
                
                while True:
                    try:
                        choice = input(f"\nSelect an option [1-2]: ").strip()
                        choice_num = int(choice)
                        
                        if choice_num == 1:
                            # User wants to enter a different name - continue with main loop
                            break
                        elif choice_num == 2:
                            # User wants to cancel
                            print("❌ Operation cancelled.")
                            return
                        else:
                            print("❌ Invalid choice. Please select 1 or 2.")
                    except ValueError:
                        print("❌ Invalid input. Please enter 1 or 2.")
                
                # Continue with the main loop to get another input
        
        # Generate visualization
        visualization = self.visualize_bridge_domain_topology(service_name, mapping)
        print(f"\n{visualization}")
        
        # Generate and display bridge domain details
        bridge_domain_data = mapping.get('bridge_domains', {}).get(service_name)
        if bridge_domain_data:
            details = self.generate_bridge_domain_details(bridge_domain_data)
            print(f"\n{details}")
        
        # Only save file if bridge domain was found (not an error message)
        if not visualization.startswith("❌ Bridge domain"):
            # Save visualization to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bridge_domain_visualization_{service_name}_{timestamp}.txt"
            filepath = self.output_dir / filename
            
            try:
                with open(filepath, 'w') as f:
                    f.write(visualization)
                print(f"\n📁 Visualization saved to: {filepath}")
            except Exception as e:
                print(f"❌ Error saving visualization: {e}")
        else:
            print(f"\n💡 Tip: Try one of the suggested bridge domain names above.")

    def generate_bridge_domain_details(self, bridge_domain_data: Dict) -> str:
        """
        Generate user-friendly bridge domain details in a structured format.
        
        Args:
            bridge_domain_data: Bridge domain data
            
        Returns:
            Formatted details string
        """
        lines = []
        lines.append("🔍 BRIDGE DOMAIN DETAILS")
        lines.append("═" * 80)
        lines.append("")
        
        # Get devices early to avoid scope issues
        devices = bridge_domain_data.get('devices', {})
        
        # Basic Information
        lines.append("📋 Basic Information")
        lines.append(f"   • Service Name: {bridge_domain_data.get('service_name', 'unknown')}")
        lines.append(f"   • VLAN ID: {bridge_domain_data.get('detected_vlan', 'unknown')}")
        lines.append(f"   • Username: {bridge_domain_data.get('detected_username', 'unknown')}")
        lines.append(f"   • Confidence: {bridge_domain_data.get('confidence', 0)}% ({bridge_domain_data.get('detection_method', 'unknown')})")
        lines.append(f"   • Detection Method: {bridge_domain_data.get('detection_method', 'unknown')}")
        lines.append(f"   • Scope: {bridge_domain_data.get('scope', 'unknown')}")
        lines.append(f"   • Topology Type: {bridge_domain_data.get('topology_type', 'unknown')}")
        lines.append("")
        
        # Topology Analysis
        topology_analysis = bridge_domain_data.get('topology_analysis', {})
        lines.append("🌐 Topology Analysis")
        lines.append(f"   • Path Complexity: {topology_analysis.get('path_complexity', 'unknown')}")
        lines.append(f"   • Total Devices: {len(devices)}")
        lines.append(f"   • Total Interfaces: {topology_analysis.get('total_interfaces', 0)}")
        lines.append(f"   • Access Interfaces: {topology_analysis.get('access_interfaces', 0)}")
        lines.append(f"   • Estimated Bandwidth: {topology_analysis.get('estimated_bandwidth', 'unknown')}")
        lines.append("")
        
        # Device Summary
        if devices:
            lines.append("📊 Device Summary")
            for device_name, device_info in devices.items():
                device_type = device_info.get('device_type', 'unknown')
                interfaces = device_info.get('interfaces', [])
                lines.append(f"   • {device_name} ({device_type})")
                lines.append(f"     - Interfaces: {len(interfaces)}")
                lines.append(f"     - Admin State: {device_info.get('admin_state', 'unknown')}")
            lines.append("")
        
        # Interface Details
        if devices:
            lines.append("🔌 Interface Details")
            for device_name, device_info in devices.items():
                lines.append(f"   • {device_name}")
                interfaces = device_info.get('interfaces', [])
                for interface in interfaces:
                    name = interface.get('name', '')
                    vlan_id = interface.get('vlan_id', '')
                    role = interface.get('role', '')
                    interface_type = interface.get('type', '')
                    
                    if vlan_id:
                        lines.append(f"     - {name} ({role}, {interface_type}, VLAN {vlan_id})")
                    else:
                        lines.append(f"     - {name} ({role}, {interface_type})")
            lines.append("")
        
        # Consolidation Info (if applicable)
        consolidation_info = bridge_domain_data.get('consolidation_info', {})
        if consolidation_info.get('consolidated_count', 1) > 1:
            lines.append("🔗 Consolidation Info")
            lines.append(f"   • Original Names: {consolidation_info.get('original_names', [])}")
            lines.append(f"   • Consolidated Count: {consolidation_info.get('consolidated_count', 0)}")
            lines.append(f"   • Consolidation Key: {consolidation_info.get('consolidation_key', 'unknown')}")
            lines.append("")
        
        return "\n".join(lines)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run visualization
    visualization = BridgeDomainVisualization()
    visualization.run_visualization() 