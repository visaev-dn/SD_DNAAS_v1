#!/usr/bin/env python3
"""
Enhanced Menu System with Superspine Support
Implements the enhanced menu system for bridge domain builder with Superspine destination support.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

from .enhanced_device_types import DeviceType, InterfaceType, enhanced_classifier
from .enhanced_bridge_domain_builder import EnhancedBridgeDomainBuilder

class EnhancedMenuSystem:
    """
    Enhanced menu system with Superspine support.
    
    Features:
    - Enhanced device selection with device type indicators
    - Interface validation for different device types
    - Topology constraint validation
    - Improved error messages and user experience
    """
    
    def __init__(self):
        """Initialize the enhanced menu system."""
        self.builder = EnhancedBridgeDomainBuilder()
    
    def parse_device_name(self, device_name):
        """
        Parse device name to extract DC row and rack number.
        Examples:
        - DNAAS-LEAF-A12 -> ('A', '12')
        - DNAAS_LEAF_D13 -> ('D', '13')
        - DNAAS-LEAF-B06-2 (NCPL) -> ('B', '06-2')
        - DNAAS-SUPERSPINE-D04-NCC1 -> ('D', '04') (consolidated as DNAAS-SUPERSPINE-D04)
        - DNAAS-SUPERSPINE-D04 -> ('D', '04')
        """
        # Handle different naming patterns
        patterns = [
            r'DNAAS-LEAF-([A-Z])(\d+(?:-\d+)?)',  # DNAAS-LEAF-A12, DNAAS-LEAF-B06-2
            r'DNAAS_LEAF_([A-Z])(\d+)',           # DNAAS_LEAF_D13
            r'DNAAS-SUPERSPINE-([A-Z])(\d+(?:-\w+)?)',  # DNAAS-SUPERSPINE-D04-NCC1
            r'DNAAS-SUPERSPINE-([A-Z])(\d+)',     # DNAAS-SUPERSPINE-D04 (consolidated)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, device_name)
            if match:
                row = match.group(1)
                rack = match.group(2)
                # For superspine, use just the rack number without NCC suffix
                if 'SUPERSPINE' in device_name and '-NCC' in rack:
                    rack = rack.split('-NCC')[0]
                return row, rack
        
        return None, None
    
    def organize_devices_by_row(self, devices: List[Dict]) -> Dict:
        """
        Organize devices by DC row.
        For superspine devices, combine NCC0/NCC1 variants into single chassis.
        
        Args:
            devices: List of devices with device info
            
        Returns:
            dict: {row_letter: {rack_number: device_info}}
        """
        organized = {}
        
        # Group superspine devices by chassis (combine NCC0/NCC1)
        superspine_chassis = {}
        other_devices = []
        
        for device in devices:
            device_name = device.get('name', '')
            device_type = device.get('device_type')
            
            if device_type == DeviceType.SUPERSPINE:
                # Extract chassis name (remove NCC0/NCC1 suffix)
                if '-NCC0' in device_name or '-NCC1' in device_name:
                    chassis_name = device_name.replace('-NCC0', '').replace('-NCC1', '')
                    if chassis_name not in superspine_chassis:
                        superspine_chassis[chassis_name] = device.copy()
                        superspine_chassis[chassis_name]['name'] = chassis_name
                        superspine_chassis[chassis_name]['chassis_variants'] = []
                    
                    # Add variant info
                    variant = 'NCC0' if '-NCC0' in device_name else 'NCC1'
                    superspine_chassis[chassis_name]['chassis_variants'].append(variant)
                else:
                    other_devices.append(device)
            else:
                other_devices.append(device)
        
        # Process all devices (including consolidated superspine chassis)
        all_devices = list(superspine_chassis.values()) + other_devices
        
        for device in all_devices:
            device_name = device.get('name', '')
            row, rack = self.parse_device_name(device_name)
            if row and rack:
                if row not in organized:
                    organized[row] = {}
                organized[row][rack] = device
        
        return organized
    
    def get_successful_devices_from_status(self) -> List[str]:
        """
        Read the device status JSON file and extract successful devices.
        Falls back to enhanced topology data if device status is empty.
        
        Returns:
            list: List of successful device names
        """
        # First try device status file
        status_file = Path("topology/device_status.json")
        if status_file.exists():
            try:
                with open(status_file, 'r') as f:
                    device_status = json.load(f)
                
                # Extract successful devices
                successful_devices = []
                for device_name, device_info in device_status['devices'].items():
                    if device_info['status'] == 'successful':
                        successful_devices.append(device_name)
                
                # If we found successful devices, return them
                if successful_devices:
                    return successful_devices
            except Exception as e:
                print(f"Error reading device status file: {e}")
        
        # Fallback to enhanced topology data
        enhanced_topology_file = Path("topology/enhanced_topology.json")
        if enhanced_topology_file.exists():
            try:
                with open(enhanced_topology_file, 'r') as f:
                    enhanced_topology = json.load(f)
                
                # Extract all devices from enhanced topology
                devices = list(enhanced_topology.get('devices', {}).keys())
                print(f"📊 Using enhanced topology data: {len(devices)} devices found")
                return devices
            except Exception as e:
                print(f"Error reading enhanced topology file: {e}")
        
        return []
    
    def select_device_by_row_rack(self, organized_devices: Dict, device_type: str, prompt_prefix: str = "") -> Optional[Dict]:
        """
        Interactive selection of device by row and rack number.
        
        Args:
            organized_devices: Dict of organized devices by row
            device_type: Type of device being selected (leaf/superspine)
            prompt_prefix: Prefix for the prompt (e.g., "Source", "Destination")
            
        Returns:
            Selected device info dict or None if cancelled
        """
        if not organized_devices:
            print(f"❌ No successful {device_type} devices found.")
            return None
        
        # Show available rows
        available_rows = sorted(organized_devices.keys())
        print(f"\n🏢 {prompt_prefix} DC Row Selection:")
        print("Available DC Rows:", ", ".join(available_rows))
        
        while True:
            row_choice = input(f"Select DC Row ({'/'.join(available_rows)}): ").strip().upper()
            if row_choice in available_rows:
                break
            print(f"❌ Invalid row. Available: {', '.join(available_rows)}")
        
        # Show available rack numbers for selected row
        rack_devices = organized_devices[row_choice]
        available_racks = sorted(rack_devices.keys(), key=lambda x: int(x.split('-')[0]) if '-' in x else int(x))
        
        print(f"\n📦 {prompt_prefix} Rack Selection (Row {row_choice}):")
        print("Available Rack Numbers:", ", ".join(available_racks))
        
        while True:
            rack_choice = input(f"Select Rack Number ({'/'.join(available_racks)}): ").strip()
            if rack_choice in rack_devices:
                selected_device = rack_devices[rack_choice]
                device_name = selected_device.get('name', 'Unknown')
                device_type_enum = selected_device.get('device_type', DeviceType.UNKNOWN)
                icon = enhanced_classifier.get_device_type_icon(device_type_enum)
                
                print(f"✅ Selected: {icon} {device_name} ({device_type_enum.value})")
                return selected_device
            print(f"❌ Invalid rack number. Available: {', '.join(available_racks)}")
    
    def display_device_selection_menu(self, devices: List[Dict], device_type: str) -> None:
        """
        Display device selection menu with device type indicators.
        
        Args:
            devices: List of devices with device type info
            device_type: Type of device being selected (source/destination)
        """
        print(f"\n📋 Available {device_type} devices:")
        print("─" * 60)
        
        for i, device in enumerate(devices, 1):
            device_type_enum = device.get('device_type', DeviceType.UNKNOWN)
            icon = enhanced_classifier.get_device_type_icon(device_type_enum)
            device_name = device.get('name', 'Unknown')
            
            print(f"{i:2d}. {icon} {device_name} ({device_type_enum.value})")
        
        print("─" * 60)
    
    def select_source_device(self) -> Optional[str]:
        """
        Select source device (leafs only) using row/rack selection.
        
        Returns:
            Selected source device name or None if cancelled
        """
        print("\n🌐 Enhanced Bridge Domain Builder - Source Selection")
        print("=" * 60)
        
        # Get successful devices
        successful_devices = self.get_successful_devices_from_status()
        if not successful_devices:
            print("❌ No successful devices found. Please run probe+parse first.")
            return None
        
        # Get available sources (leafs only)
        available_sources = self.builder.get_available_sources()
        
        if not available_sources:
            print("❌ No available source devices found.")
            print("   Source devices must be leaf devices with successful topology discovery.")
            return None
        
        # Organize by DC row
        organized_sources = self.organize_devices_by_row(available_sources)
        
        print(f"\n📊 Found {len(available_sources)} available source devices across {len(organized_sources)} DC rows")
        
        # Source device selection using row/rack
        selected_device_info = self.select_device_by_row_rack(organized_sources, "leaf", "Source")
        if not selected_device_info:
            return None
        
        return selected_device_info.get('name')
    
    def select_destination_device_streamlined(self, source_device: str) -> Optional[str]:
        """
        Select destination device with streamlined flow.
        For superspine: skip row/rack selection since there's only one.
        
        Args:
            source_device: Source device name for validation
            
        Returns:
            Selected destination device name or None if cancelled
        """
        print(f"\n🌐 Enhanced Bridge Domain Builder - Destination Selection")
        print("=" * 60)
        
        # First, ask user if they want a leaf or superspine as destination
        print("\n🎯 Destination Type Selection:")
        print("1. 🌿 Leaf Device (P2P or P2MP)")
        print("2. 🏗️  Superspine Device (P2P or P2MP)")
        print()
        
        while True:
            dest_type_choice = input("Select destination type (1-2): ").strip()
            
            if dest_type_choice == "1":
                # Leaf destination - use row/rack selection
                print("\n🌿 Leaf Destination Selection")
                print("─" * 40)
                
                # Get available destinations (leafs only for leaf destination)
                available_destinations = self.builder.get_available_destinations(source_device)
                leaf_destinations = [d for d in available_destinations if d.get('device_type') == DeviceType.LEAF]
                
                if not leaf_destinations:
                    print("❌ No available leaf destination devices found.")
                    return None
                
                # Organize by DC row
                organized_destinations = self.organize_devices_by_row(leaf_destinations)
                
                print(f"\n📊 Found {len(leaf_destinations)} available leaf destination devices across {len(organized_destinations)} DC rows")
                
                # Destination device selection using row/rack
                selected_device_info = self.select_device_by_row_rack(organized_destinations, "leaf", "Destination")
                if not selected_device_info:
                    return None
                
                selected_device = selected_device_info.get('name')
                device_type = selected_device_info.get('device_type')
                
                # Validate topology constraints
                source_type = self.builder.get_device_type(source_device)
                if not enhanced_classifier.validate_topology_constraints(source_type, device_type):
                    print(f"❌ Invalid topology: {source_type.value} → {device_type.value}")
                    print("   This topology is not supported.")
                    return None
                
                return selected_device
                
            elif dest_type_choice == "2":
                # Superspine destination - skip row/rack selection since there's only one
                print("\n🏗️  Superspine Destination Selection")
                print("─" * 40)
                
                # Get available destinations (superspines only for superspine destination)
                available_destinations = self.builder.get_available_destinations(source_device)
                superspine_destinations = [d for d in available_destinations if d.get('device_type') == DeviceType.SUPERSPINE]
                
                if not superspine_destinations:
                    print("❌ No available superspine destination devices found.")
                    return None
                
                # Apply consolidation to get the actual number of chassis
                organized_superspines = self.organize_devices_by_row(superspine_destinations)
                consolidated_superspines = []
                
                # Flatten the organized structure to get consolidated devices
                for row, racks in organized_superspines.items():
                    for rack, device in racks.items():
                        consolidated_superspines.append(device)
                
                # Since there's only one superspine chassis, just select it directly
                if len(consolidated_superspines) == 1:
                    selected_device_info = consolidated_superspines[0]
                    selected_device = selected_device_info.get('name')
                    device_type = selected_device_info.get('device_type')
                    
                    # Show chassis variant information if available
                    chassis_variants = selected_device_info.get('chassis_variants', [])
                    if chassis_variants:
                        print(f"📋 Selected superspine chassis has {len(chassis_variants)} routing engine(s): {', '.join(chassis_variants)}")
                    
                    print(f"✅ Selected: 🌐 {selected_device} ({device_type.value})")
                    
                    # Validate topology constraints
                    source_type = self.builder.get_device_type(source_device)
                    if not enhanced_classifier.validate_topology_constraints(source_type, device_type):
                        print(f"❌ Invalid topology: {source_type.value} → {device_type.value}")
                        print("   Superspine devices can only be destinations.")
                        return None
                    
                    return selected_device
                else:
                    # If there are multiple superspines (unlikely), use row/rack selection
                    print(f"⚠️  Found {len(consolidated_superspines)} superspine chassis, using row/rack selection")
                    
                    # Show topology constraints
                    print("\n📋 Topology Constraints:")
                    print("   • Superspine devices can only be destinations (never sources)")
                    print("   • No Superspine → Superspine topologies")
                    print("   • Superspine supports transport interfaces only (10GE, 100GE, bundles)")
                    
                    # Destination device selection using row/rack
                    selected_device_info = self.select_device_by_row_rack(organized_superspines, "superspine", "Destination")
                    if not selected_device_info:
                        return None
                    
                    selected_device = selected_device_info.get('name')
                    device_type = selected_device_info.get('device_type')
                    
                    # Show chassis variant information if available
                    chassis_variants = selected_device_info.get('chassis_variants', [])
                    if chassis_variants:
                        print(f"📋 Selected superspine chassis has {len(chassis_variants)} routing engine(s): {', '.join(chassis_variants)}")
                    
                    # Validate topology constraints
                    source_type = self.builder.get_device_type(source_device)
                    if not enhanced_classifier.validate_topology_constraints(source_type, device_type):
                        print(f"❌ Invalid topology: {source_type.value} → {device_type.value}")
                        print("   Superspine devices can only be destinations.")
                        return None
                    
                    return selected_device
                
            else:
                print("❌ Invalid choice. Please select 1 or 2.")
    
    def get_interface_input(self, device_name: str, interface_type: str) -> Optional[str]:
        """
        Get interface input with validation.
        For leaf devices: just ask for the number X and construct ge100-0/0/X
        
        Args:
            device_name: Device name for validation
            interface_type: Type of interface (source/destination)
            
        Returns:
            Validated interface name or None if cancelled
        """
        device_type = self.builder.get_device_type(device_name)
        icon = enhanced_classifier.get_device_type_icon(device_type)
        
        print(f"\n🔌 {interface_type.title()} Interface Selection")
        print(f"Device: {icon} {device_name} ({device_type.value})")
        print("─" * 50)
        
        # Handle leaf devices differently (just ask for the number)
        if device_type == DeviceType.LEAF:
            print("Valid interfaces for Leaf:")
            print("   • AC interfaces: ge100-0/0/X (transport)")
            print("   • Just enter the interface number (X)")
            
            # Get interface number input
            while True:
                try:
                    default_interface_num = "10"
                    interface_num = input(f"Enter the interface number (X) for ge100-0/0/X (e.g., {default_interface_num}): ").strip()
                    
                    if not interface_num:
                        interface_num = default_interface_num
                    
                    # Validate that it's a number
                    try:
                        int(interface_num)
                    except ValueError:
                        print("❌ Invalid interface number. Must be a number.")
                        continue
                    
                    # Construct the full interface name
                    interface = f"ge100-0/0/{interface_num}"
                    
                    print(f"✅ Valid interface: {interface}")
                    return interface
                    
                except KeyboardInterrupt:
                    print("\n❌ Interface input cancelled.")
                    return None
        
        # For non-leaf devices (spine, superspine), use the original validation
        else:
            # Show valid interface types for device
            if device_type == DeviceType.SPINE:
                print("Valid interfaces for Spine devices:")
                print("   • Transport interfaces: ge10-0/0/X, ge100-0/0/X")
                print("   • Bundle interfaces: bundle-X")
                print("   • No access interfaces allowed")
            elif device_type == DeviceType.SUPERSPINE:
                print("Valid interfaces for Superspine devices:")
                print("   • Any GE interface: ge10-0/0/X, ge100-0/0/X, ge100-4/0/X, ge100-5/0/X")
                print("   • Bundle interfaces: bundle-X")
                print("   • Note: Some interfaces are reserved for spine connections")
                
                # Get available interfaces for this superspine
                available_interfaces = self.builder.get_available_superspine_interfaces(device_name)
                if available_interfaces:
                    print(f"   • Available AC interfaces for {device_name}:")
                    # Group interfaces by type for better display
                    ge10_interfaces = [i for i in available_interfaces if i.startswith('ge10-')]
                    ge100_interfaces = [i for i in available_interfaces if i.startswith('ge100-')]
                    bundle_interfaces = [i for i in available_interfaces if i.startswith('bundle-')]
                    
                    if ge10_interfaces:
                        print(f"     - 10GE: {', '.join(sorted(ge10_interfaces)[:10])}{'...' if len(ge10_interfaces) > 10 else ''}")
                    if ge100_interfaces:
                        print(f"     - 100GE: {', '.join(sorted(ge100_interfaces)[:10])}{'...' if len(ge100_interfaces) > 10 else ''}")
                    if bundle_interfaces:
                        print(f"     - Bundles: {', '.join(sorted(bundle_interfaces)[:10])}{'...' if len(bundle_interfaces) > 10 else ''}")
                    
                    if len(available_interfaces) > 30:
                        print(f"     - Total available: {len(available_interfaces)} interfaces")
                else:
                    print("   • No available interfaces found (all interfaces may be reserved for spine connections)")
            
            # Get interface input
            while True:
                try:
                    if device_type in [DeviceType.SPINE, DeviceType.SUPERSPINE]:
                        default_interface = "ge10-0/0/5"
                    else:
                        default_interface = "ge100-0/0/10"
                    
                    interface = input(f"Enter interface name (e.g., {default_interface}): ").strip()
                    
                    if not interface:
                        print("❌ Interface name cannot be empty.")
                        continue
                    
                    # Validate interface for device type
                    if not enhanced_classifier.validate_interface_for_device(interface, device_type):
                        print(f"❌ Invalid interface '{interface}' for {device_type.value} device.")
                        if device_type == DeviceType.SPINE:
                            print("   Spine devices only support transport interfaces (ge10-*, ge100-*, bundle-*)")
                        elif device_type == DeviceType.SUPERSPINE:
                            print("   Superspine devices support any GE interface (ge10-*, ge100-*, bundle-*)")
                            print("   Note: Some interfaces are reserved for spine connections")
                            
                            # Show available interfaces for superspine
                            available_interfaces = self.builder.get_available_superspine_interfaces(device_name)
                            if available_interfaces:
                                print(f"   Available interfaces for {device_name}:")
                                ge10_interfaces = [i for i in available_interfaces if i.startswith('ge10-')]
                                ge100_interfaces = [i for i in available_interfaces if i.startswith('ge100-')]
                                bundle_interfaces = [i for i in available_interfaces if i.startswith('bundle-')]
                                
                                if ge10_interfaces:
                                    print(f"     - 10GE: {', '.join(sorted(ge10_interfaces)[:5])}{'...' if len(ge10_interfaces) > 5 else ''}")
                                if ge100_interfaces:
                                    print(f"     - 100GE: {', '.join(sorted(ge100_interfaces)[:5])}{'...' if len(ge100_interfaces) > 5 else ''}")
                                if bundle_interfaces:
                                    print(f"     - Bundles: {', '.join(sorted(bundle_interfaces)[:5])}{'...' if len(bundle_interfaces) > 5 else ''}")
                            else:
                                print("   No available interfaces found")
                        continue
                    
                    print(f"✅ Valid interface: {interface}")
                    return interface
                    
                except KeyboardInterrupt:
                    print("\n❌ Interface input cancelled.")
                    return None
    
    def get_service_configuration(self) -> Tuple[str, int]:
        """
        Get service configuration (username and VLAN ID).
        
        Returns:
            Tuple of (service_name, vlan_id)
        """
        print("\n📋 Service Configuration")
        print("─" * 40)
        
        # Username
        default_username = "visaev"
        username = input(f"👤 Username (e.g., {default_username}): ").strip()
        if not username:
            username = default_username
        
        # VLAN ID
        default_vlan_id = "253"
        vlan_id_input = input(f"🏷️  VLAN ID (e.g., {default_vlan_id}): ").strip()
        if not vlan_id_input:
            vlan_id_input = default_vlan_id
        
        try:
            vlan_id = int(vlan_id_input)
        except ValueError:
            print("❌ Invalid VLAN ID. Must be a number.")
            raise ValueError("Invalid VLAN ID")
        
        # Format service name as g_"username"_v"vlan-id"
        service_name = f"g_{username}_v{vlan_id}"
        print(f"✅ Service name will be: {service_name}")
        
        return service_name, vlan_id
    
    def run_enhanced_bridge_domain_builder(self) -> bool:
        """
        Run the enhanced bridge domain builder with Superspine support.
        
        Returns:
            True if successful, False otherwise
        """
        print("\n" + "🔨" + "=" * 68)
        print("🔨 ENHANCED BRIDGE-DOMAIN BUILDER (with Superspine Support)")
        print("🔨" + "=" * 68)
        
        try:
            # Check if topology files exist
            topology_file = Path("topology/complete_topology_v2.json")
            if not topology_file.exists():
                print("❌ Topology file not found. Please run topology discovery first.")
                return False
            
            print("✅ Topology files found. Starting enhanced bridge domain builder...")
            
            # Get service configuration
            service_name, vlan_id = self.get_service_configuration()
            
            # Step 1: Select source device (leaf only)
            source_device = self.select_source_device()
            if not source_device:
                return False
            
            # Step 2: Get source interface
            source_interface = self.get_interface_input(source_device, "source")
            if not source_interface:
                return False
            
            # Step 3: Select destination type and device
            dest_device = self.select_destination_device_streamlined(source_device)
            if not dest_device:
                return False
            
            # Step 4: Get destination interface
            dest_interface = self.get_interface_input(dest_device, "destination")
            if not dest_interface:
                return False
            
            # Validate path topology
            if not self.builder.validate_path_topology(source_device, dest_device):
                print("❌ Invalid topology configuration.")
                source_type = self.builder.get_device_type(source_device)
                dest_type = self.builder.get_device_type(dest_device)
                print(f"   Source: {source_type.value}, Destination: {dest_type.value}")
                print("   Superspine devices can only be destinations.")
                return False
            
            # Build bridge domain configuration
            print(f"\n🔨 Building enhanced bridge domain configuration...")
            
            configs = self.builder.build_bridge_domain_config(
                service_name, vlan_id,
                source_device, source_interface,
                dest_device, dest_interface
            )
            
            if not configs:
                print("❌ Failed to build bridge domain configuration.")
                return False
            
            # Show configuration summary
            print(self.builder.get_configuration_summary(configs))
            
            # Show path visualization
            metadata = configs.get('_metadata', {})
            path = metadata.get('path', [])
            if path:
                print(f"\n🌳 Path Visualization:")
                for i, device in enumerate(path):
                    device_type = self.builder.get_device_type(device)
                    icon = enhanced_classifier.get_device_type_icon(device_type)
                    
                    if i == 0:
                        print(f"  {icon} {device} (Source)")
                    elif i == len(path) - 1:
                        print(f"  {icon} {device} (Destination)")
                    else:
                        print(f"  {icon} {device} (Intermediate)")
                    
                    if i < len(path) - 1:
                        print("  ↓")
            
            # Save configuration
            output_file = f"enhanced_bridge_domain_{service_name}.yaml"
            self.builder.save_configuration(configs, output_file)
            
            print(f"\n✅ Enhanced bridge domain configuration built successfully!")
            print(f"📁 Configuration saved to: {output_file}")
            
            # Show device count
            device_count = len([k for k in configs.keys() if k != '_metadata'])
            print(f"📋 Devices configured: {device_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Enhanced bridge domain builder failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def display_enhanced_error_message(self, error: Exception, context: Dict) -> None:
        """
        Display enhanced error messages with helpful information.
        
        Args:
            error: The error that occurred
            context: Context information about the operation
        """
        print(f"\n❌ Error: {error}")
        
        if "Invalid topology" in str(error):
            print("\n🔧 Topology Constraint Violation:")
            print("   • Superspine devices can only be destinations, not sources")
            print("   • No Superspine → Superspine topologies are allowed")
            print("   • Please select a leaf device as source")
        
        elif "Invalid source interface" in str(error):
            print("\n🔧 Interface Validation Error:")
            print("   • Source interfaces must be valid for the device type")
            print("   • Leaf devices support: ge1-0/0/X, ge10-0/0/X, ge100-0/0/X, bundle-X")
            print("   • Please check the interface name and device type")
        
        elif "Invalid destination interface" in str(error):
            print("\n🔧 Interface Validation Error:")
            print("   • Destination interfaces must be valid for the device type")
            print("   • Superspine devices support: ge10-0/0/X, ge100-0/0/X, bundle-X only")
            print("   • No access interfaces (ge1-0/0/X) allowed on Superspine")
            print("   • Please check the interface name and device type")
        
        else:
            print("\n🔧 General Error:")
            print("   • Please check your input and try again")
            print("   • Ensure topology discovery has been completed")
            print("   • Verify device names and interface names")
        
        print(f"\n📋 Context: {context}") 
        print(f"\n📋 Context: {context}") 