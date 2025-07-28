#!/usr/bin/env python3
"""
Device Status Viewer
Displays device connectivity and health information from collected data.
"""

import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class DeviceStatusViewer:
    """Display device status and connectivity information"""
    
    def __init__(self):
        self.device_status_file = Path("topology/device_status.json")
        self.devices_file = Path("devices.yaml")
        self.topology_file = Path("topology/complete_topology_v2.json")
        
    def load_device_status(self) -> Optional[Dict]:
        """Load device status from JSON file"""
        try:
            if not self.device_status_file.exists():
                print("❌ Device status file not found. Please run probe+parse first.")
                return None
            
            with open(self.device_status_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading device status: {e}")
            return None
    
    def load_devices(self) -> Optional[Dict]:
        """Load device information from devices.yaml"""
        try:
            if not self.devices_file.exists():
                print("❌ devices.yaml not found. Please populate devices first.")
                return None
            
            with open(self.devices_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Error loading devices: {e}")
            return None
    
    def display_device_status(self):
        """Display comprehensive device status information"""
        print("\n📊 DEVICE STATUS VIEWER")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Load data
        device_status = self.load_device_status()
        devices = self.load_devices()
        
        if not device_status and not devices:
            print("❌ No device data available.")
            print("💡 Please run:")
            print("   1. Populate Devices from Inventory")
            print("   2. Probe & Parse (LACP + LLDP)")
            return
        
        # Display device status if available
        if device_status:
            print("🔍 DEVICE CONNECTIVITY STATUS")
            print("-" * 40)
            
            devices_info = device_status.get('devices', {})
            total_devices = len(devices_info)
            successful_devices = sum(1 for dev in devices_info.values() if dev.get('status') == 'successful')
            failed_devices = total_devices - successful_devices
            
            print(f"📊 Total Devices: {total_devices}")
            print(f"✅ Successful: {successful_devices}")
            print(f"❌ Failed: {failed_devices}")
            print(f"📈 Success Rate: {(successful_devices/total_devices*100):.1f}%" if total_devices > 0 else "📈 Success Rate: 0%")
            print()
            
            # Show successful devices
            if successful_devices > 0:
                print("✅ SUCCESSFUL DEVICES:")
                for device_name, device_info in devices_info.items():
                    if device_info.get('status') == 'successful':
                        print(f"   • {device_name}")
                print()
            
            # Show failed devices
            if failed_devices > 0:
                print("❌ FAILED DEVICES:")
                for device_name, device_info in devices_info.items():
                    if device_info.get('status') != 'successful':
                        error = device_info.get('error', 'Unknown error')
                        print(f"   • {device_name}: {error}")
                print()
        
        # Display device inventory if available
        if devices:
            print("📋 DEVICE INVENTORY")
            print("-" * 40)
            
            # Remove defaults from device count
            device_count = len([k for k in devices.keys() if k != 'defaults'])
            print(f"📊 Total Devices in Inventory: {device_count}")
            
            if 'defaults' in devices:
                defaults = devices['defaults']
                print(f"🔧 Default Username: {defaults.get('username', 'N/A')}")
                print(f"🔧 Default SSH Port: {defaults.get('ssh_port', 'N/A')}")
                print(f"🔧 Default Device Type: {defaults.get('device_type', 'N/A')}")
            print()
            
            # Show device types
            device_types = {}
            for device_name, device_info in devices.items():
                if device_name != 'defaults':
                    device_type = device_info.get('device_type', 'unknown')
                    device_types[device_type] = device_types.get(device_type, 0) + 1
            
            if device_types:
                print("📊 DEVICE TYPES:")
                for device_type, count in device_types.items():
                    print(f"   • {device_type}: {count} devices")
                print()
        
        # Display topology information if available
        if self.topology_file.exists():
            try:
                with open(self.topology_file, 'r') as f:
                    topology = json.load(f)
                
                print("🌳 TOPOLOGY INFORMATION")
                print("-" * 40)
                
                tree = topology.get('tree', {})
                superspine_count = len(tree.get('superspine_devices', {}))
                spine_count = len(tree.get('spine_devices', {}))
                leaf_count = len(tree.get('leaf_devices', {}))
                
                print(f"🌲 Super Spines: {superspine_count}")
                print(f"🌲 Spines: {spine_count}")
                print(f"🍃 Leaves: {leaf_count}")
                print(f"📊 Total Topology Devices: {superspine_count + spine_count + leaf_count}")
                
            except Exception as e:
                print(f"⚠️  Could not load topology information: {e}")
        
        print("\n💡 TIPS:")
        print("   • Run 'Probe & Parse' to collect fresh device data")
        print("   • Run 'Populate Devices' to update device inventory")
        print("   • Check device connectivity if many devices are failing")
        print("   • Verify network connectivity and credentials")

def main():
    """Main entry point"""
    viewer = DeviceStatusViewer()
    viewer.display_device_status()

if __name__ == "__main__":
    main() 