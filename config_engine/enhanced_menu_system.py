#!/usr/bin/env python3
"""
Enhanced Menu System with Unified Bridge Domain Builder
Implements the enhanced menu system for bridge domain builder with unified P2P and P2MP support.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

from .enhanced_device_types import DeviceType, InterfaceType, enhanced_classifier
from .unified_bridge_domain_builder import UnifiedBridgeDomainBuilder

class EnhancedMenuSystem:
    """
    Enhanced menu system with unified bridge domain builder support.
    
    Features:
    - Enhanced device selection with device type indicators
    - Interface validation for different device types
    - Topology constraint validation
    - Unified P2P and P2MP bridge domain configurations
    - Improved error messages and user experience
    """
    
    def __init__(self):
        """Initialize the enhanced menu system."""
        self.builder = UnifiedBridgeDomainBuilder()
    
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
        
        Returns:
            list: List of successful device names
        """
        status_file = Path("topology/device_status.json")
        if not status_file.exists():
            return []
        
        try:
            with open(status_file, 'r') as f:
                device_status = json.load(f)
            
            # Extract successful devices
            successful_devices = []
            for device_name, device_info in device_status['devices'].items():
                if device_info['status'] == 'successful':
                    successful_devices.append(device_name)
            
            return successful_devices
        except Exception as e:
            print(f"Error reading device status file: {e}")
            return []
    
    def select_device_by_row_rack(self, organized_devices: Dict, device_type: str, prompt_prefix: str = "") -> Optional[Dict]:
        """
        Enhanced device selection with row/rack organization.
        
        Args:
            organized_devices: Devices organized by row and rack
            device_type: Type of device to select
            prompt_prefix: Prefix for the prompt
            
        Returns:
            Selected device info or None
        """
        if not organized_devices:
            print(f"❌ No {device_type} devices available.")
            return None
        
        print(f"\n📋 {prompt_prefix} {device_type} Selection")
        print("─" * 50)
        
        # Display available devices by row
        for row in sorted(organized_devices.keys()):
            print(f"\n🏢 Row {row}:")
            for rack in sorted(organized_devices[row].keys()):
                device = organized_devices[row][rack]
                device_name = device.get('name', 'Unknown')
                device_type_enum = device.get('device_type', 'Unknown')
                
                # Add device type indicator
                type_indicator = "🌿" if device_type_enum == DeviceType.LEAF else "🌲" if device_type_enum == DeviceType.SUPERSPINE else "🔧"
                
                # Add chassis variant info for superspine
                variant_info = ""
                if device_type_enum == DeviceType.SUPERSPINE and 'chassis_variants' in device:
                    variants = device['chassis_variants']
                    if variants:
                        variant_info = f" ({', '.join(variants)})"
                
                print(f"   {type_indicator} {device_name}{variant_info}")
        
        # Get user selection
        while True:
            try:
                selection = input(f"\n🎯 Select {device_type} (row-rack format, e.g., A-12): ").strip().upper()
                
                if not selection:
                    print("❌ Please enter a valid selection.")
                    continue
                
                # Parse row-rack format
                if '-' in selection:
                    row, rack = selection.split('-', 1)
                else:
                    print("❌ Please use format: row-rack (e.g., A-12)")
                    continue
                
                # Find the device
                if row in organized_devices and rack in organized_devices[row]:
                    selected_device = organized_devices[row][rack]
                    print(f"✅ Selected: {selected_device.get('name', 'Unknown')}")
                    return selected_device
                else:
                    print(f"❌ Device {row}-{rack} not found. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n❌ Selection cancelled.")
                return None
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    def display_device_selection_menu(self, devices: List[Dict], device_type: str) -> None:
        """Display a menu of available devices."""
        print(f"\n📋 Available {device_type} Devices:")
        print("─" * 40)
        
        for i, device in enumerate(devices, 1):
            device_name = device.get('name', 'Unknown')
            device_type_enum = device.get('device_type', 'Unknown')
            
            # Add device type indicator
            type_indicator = "🌿" if device_type_enum == DeviceType.LEAF else "🌲" if device_type_enum == DeviceType.SUPERSPINE else "🔧"
            
            print(f"{i:2d}. {type_indicator} {device_name}")
    
    def select_source_device(self) -> Optional[str]:
        """Select source device for bridge domain configuration."""
        print("\n🎯 Source Device Selection")
        print("─" * 30)
        
        # Get available devices
        available_devices = self.builder.get_available_sources()
        
        if not available_devices:
            print("❌ No devices available for selection.")
            return None
        
        # Organize devices by row
        organized_devices = self.organize_devices_by_row(available_devices)
        
        # Select source device
        source_device = self.select_device_by_row_rack(organized_devices, "Source", "Source")
        
        if source_device:
            return source_device.get('name')
        
        return None
    
    def select_destination_device_streamlined(self, source_device: str) -> Optional[str]:
        """Select destination device with streamlined validation."""
        print("\n🎯 Destination Device Selection")
        print("─" * 35)
        
        # Get available devices
        available_devices = self.builder.get_available_destinations(source_device)
        
        if not available_devices:
            print("❌ No devices available for selection.")
            return None
        
        # Organize devices by row
        organized_devices = self.organize_devices_by_row(available_devices)
        
        # Select destination device
        destination_device = self.select_device_by_row_rack(organized_devices, "Destination", "Destination")
        
        if destination_device:
            return destination_device.get('name')
        
        return None
    
    def get_interface_input(self, device_name: str, interface_type: str) -> Optional[str]:
        """
        Get interface input from user with validation.
        
        Args:
            device_name: Name of the device
            interface_type: Type of interface (source/destination)
            
        Returns:
            Interface name or None if cancelled
        """
        print(f"\n🔌 {interface_type.title()} Interface Selection")
        print("─" * 40)
        
        # Get available interfaces for the device
        try:
            available_interfaces = self.builder.get_available_interfaces(device_name)
            
            if not available_interfaces:
                print(f"❌ No interfaces available for {device_name}")
                return None
            
            print(f"📋 Available interfaces for {device_name}:")
            for i, interface in enumerate(available_interfaces, 1):
                print(f"   {i:2d}. {interface}")
            
            while True:
                try:
                    selection = input(f"\n🎯 Select {interface_type} interface (number or name): ").strip()
                    
                    if not selection:
                        print("❌ Please enter a valid selection.")
                        continue
                    
                    # Try to parse as number
                    try:
                        index = int(selection) - 1
                        if 0 <= index < len(available_interfaces):
                            selected_interface = available_interfaces[index]
                            print(f"✅ Selected: {selected_interface}")
                            return selected_interface
                        else:
                            print("❌ Invalid number. Please try again.")
                            continue
                    except ValueError:
                        # Try to match by name
                        if selection in available_interfaces:
                            print(f"✅ Selected: {selection}")
                            return selection
                        else:
                            print(f"❌ Interface '{selection}' not found. Please try again.")
                            continue
                    
                except KeyboardInterrupt:
                    print("\n❌ Interface selection cancelled.")
                    return None
                except Exception as e:
                    print(f"❌ Error: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error getting interfaces for {device_name}: {e}")
            return None
    
    def get_service_configuration(self) -> Tuple[str, int]:
        """
        Get service configuration from user.
        
        Returns:
            Tuple of (service_name, vlan_id)
        """
        print("\n⚙️  Service Configuration")
        print("─" * 25)
        
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
            return None, None
        
        # Format service name as g_"username"_v"vlan-id"
        service_name = f"g_{username}_v{vlan_id}"
        print(f"✅ Service name will be: {service_name}")
        
        return service_name, vlan_id
    
    def run_enhanced_bridge_domain_builder(self) -> bool:
        """
        Run the unified bridge domain builder with automatic P2P/P2MP detection.
        
        Returns:
            True if successful, False otherwise
        """
        print("\n" + "🔨" + "=" * 68)
        print("🔨 UNIFIED BRIDGE-DOMAIN BUILDER (P2P & P2MP)")
        print("🔨" + "=" * 68)
        
        try:
            # Check if topology files exist
            topology_file = Path("topology/complete_topology_v2.json")
            bundle_file = Path("topology/bundle_mapping_v2.yaml")
            
            if not topology_file.exists():
                print("❌ Topology file not found. Please run topology discovery first.")
                return False
            
            if not bundle_file.exists():
                print("❌ Bundle mapping file not found. Please run topology discovery first.")
                return False
            
            print("✅ Topology files found. Starting unified bridge domain builder...")
            
            # Get service configuration
            service_name, vlan_id = self.get_service_configuration()
            if not service_name or vlan_id is None:
                return False
            
            # Start with source device selection
            print("\n🎯 Source Device Selection")
            print("─" * 30)
            
            source_device = self.select_source_device()
            if not source_device:
                return False
            
            # Get source interface
            source_interface = self.get_interface_input(source_device, "source")
            if not source_interface:
                return False
            
            # Now let user add destinations naturally
            destinations = self._collect_destinations_interactively(source_device)
            if not destinations:
                return False
            
            # Build unified configuration
            configs = self.builder.build_bridge_domain_config(
                service_name, vlan_id,
                source_device, source_interface,
                destinations
            )
            
            if not configs:
                print("❌ Failed to build bridge domain configuration.")
                return False
            
            # Show configuration summary
            print(f"\n📋 Configuration Summary:")
            summary = self.builder.get_configuration_summary(configs)
            print(summary)
            
            # Save configuration
            output_file = f"unified_bridge_domain_{service_name}.yaml"
            
            # Ensure configs/pending directory exists
            configs_pending_dir = Path("configs/pending")
            configs_pending_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to configs/pending directory
            output_path = configs_pending_dir / output_file
            self.builder.save_configuration(configs, str(output_path))
            
            print(f"\n✅ Unified bridge domain configuration built successfully!")
            print(f"📁 Configuration saved to: {output_path}")
            
            # Show device count
            device_count = len([k for k in configs.keys() if k != '_metadata'])
            print(f"📋 Devices configured: {device_count}")
            
            return True
            
        except Exception as e:
            self.display_enhanced_error_message(e, {"context": "unified_bridge_domain_builder"})
            return False
    
    def _collect_destinations_interactively(self, source_device: str) -> List[Dict]:
        """
        Collect destinations interactively, allowing user to add multiple destinations.
        
        Returns:
            List of destination dictionaries with 'device' and 'port' keys
        """
        print("\n🎯 Destination Selection")
        print("─" * 25)
        print("Add destinations for your bridge domain configuration.")
        print("You can add multiple destinations for P2MP scenarios.")
        
        destinations = []
        
        while True:
            print(f"\n📋 Current destinations: {len(destinations)}")
            if destinations:
                for i, dest in enumerate(destinations, 1):
                    print(f"   {i}. {dest['device']}:{dest['port']}")
            
            # Select destination device
            destination_device = self.select_destination_device_streamlined(source_device)
            if not destination_device:
                if destinations:
                    print("✅ Finished adding destinations.")
                    break
                else:
                    print("❌ No destinations selected.")
                    return []
            
            # Get destination interface
            destination_interface = self.get_interface_input(destination_device, "destination")
            if not destination_interface:
                continue
            
            # Add to destinations
            destinations.append({
                'device': destination_device,
                'port': destination_interface
            })
            
            print(f"✅ Added destination: {destination_device}:{destination_interface}")
            
            # Ask if user wants to add another destination
            if len(destinations) == 1:
                print("\n💡 You can add more destinations for P2MP configuration.")
            
            add_another = input(f"\nAdd another destination? (y/n): ").strip().lower()
            if add_another not in ['y', 'yes']:
                break
        
        return destinations
    
    def display_enhanced_error_message(self, error: Exception, context: Dict) -> None:
        """Display enhanced error messages with context."""
        print(f"\n❌ Error in {context.get('context', 'unknown')}: {error}")
        
        # Provide specific guidance based on error type
        if "topology" in str(error).lower():
            print("💡 Tip: Please run topology discovery first.")
        elif "interface" in str(error).lower():
            print("💡 Tip: Check interface names and availability.")
        elif "device" in str(error).lower():
            print("💡 Tip: Verify device names and connectivity.")
        else:
            print("💡 Tip: Check the configuration and try again.")
        
        import traceback
        traceback.print_exc() 