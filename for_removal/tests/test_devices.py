#!/usr/bin/env python3
"""
Test device connectivity and basic commands
"""

import sys
import os
import time
import yaml

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.dnos_ssh import DNOSSSH

def test_devices_file():
    """Test if devices.yaml exists and has correct format"""
    print("🔍 Testing devices.yaml file...")
    
    # Check current directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Try to find devices.yaml
    possible_paths = [
        "devices.yaml",
        "../devices.yaml",
        "../../devices.yaml",
        "lab_automation/devices.yaml"
    ]
    
    devices_file = None
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found devices.yaml at: {path}")
            devices_file = path
            break
        else:
            print(f"❌ Not found: {path}")
    
    if not devices_file:
        print("❌ Could not find devices.yaml in any common location")
        return False
    
    # Try to load and parse the file
    try:
        with open(devices_file, 'r') as f:
            content = f.read()
            print(f"\n📄 File content:\n{content}")
            
        with open(devices_file, 'r') as f:
            devices = yaml.safe_load(f)
        
        print(f"\n✅ Successfully parsed devices.yaml")
        print(f"  Devices found: {len(devices.get('devices', {}))}")
        
        # Show device details
        for device_name, device_config in devices.get('devices', {}).items():
            print(f"  📱 {device_name}:")
            print(f"    Hostname: {device_config.get('mgmt_ip', 'unknown')}")
            print(f"    Username: {device_config.get('username', 'unknown')}")
            print(f"    Device Type: {device_config.get('device_type', 'unknown')}")
            print(f"    SSH Port: {device_config.get('ssh_port', 22)}")
            print(f"    NETCONF Port: {device_config.get('netconf_port', 830)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing devices.yaml: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ssh_connectivity():
    """Test basic SSH connectivity to devices"""
    print("\n🔍 Testing SSH connectivity...")
    
    try:
        # Load devices
        with open("devices.yaml", 'r') as f:
            devices = yaml.safe_load(f)
        
        # Test each device
        for device_name, device_config in devices.get('devices', {}).items():
            print(f"\n📱 Testing {device_name} ({device_config['mgmt_ip']})...")
            
            # Test port connectivity
            import socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((device_config['mgmt_ip'], device_config.get('ssh_port', 22)))
                sock.close()
                
                if result == 0:
                    print(f"  ✅ Port {device_config.get('ssh_port', 22)} is open")
                else:
                    print(f"  ❌ Port {device_config.get('ssh_port', 22)} is closed")
                    
            except Exception as e:
                print(f"  ❌ Port test failed: {e}")
        
    except Exception as e:
        print(f"❌ SSH connectivity test failed: {e}")

if __name__ == "__main__":
    print("🧪 Device Configuration Test")
    print("=" * 50)
    
    if test_devices_file():
        test_ssh_connectivity()
    else:
        print("\n❌ Cannot proceed with SSH tests due to devices.yaml issues")
        sys.exit(1) 