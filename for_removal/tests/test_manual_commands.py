#!/usr/bin/env python3
"""
Manual command testing script to debug SSH output issues
"""

import sys
import os
import time
import yaml

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.dnos_ssh import DNOSSSH

def test_device_commands(device_name, device_config):
    """Test individual commands on a device"""
    print(f"\n{'='*60}")
    print(f"Testing device: {device_name}")
    print(f"Host: {device_config['mgmt_ip']}")
    print(f"{'='*60}")
    
    try:
        # Connect to device
        ssh = DNOSSSH(
            hostname=device_config['mgmt_ip'],
            username=device_config['username'],
            password=device_config['password'],
            port=device_config.get('ssh_port', 22)
        )
        
        if not ssh.connect():
            print(f"Failed to connect to {device_name}")
            return
        
        print(f"Successfully connected to {device_name}")
        
        # Test different commands
        commands = [
            'show interfaces',
            'show lacp counters', 
            'show lacp interfaces',
            'show port-channel summary',
            'show etherchannel summary',
            'show bundle interfaces'
        ]
        
        for cmd in commands:
            print(f"\n--- Testing command: {cmd} ---")
            print(f"Command: {cmd}")
            
            # Clear buffer and wait
            ssh._clear_buffer()
            time.sleep(2)
            
            # Send command
            output = ssh.send_command(cmd, wait_time=3.0)
            
            if output:
                print(f"Output length: {len(output)}")
                print(f"First 200 chars: {output[:200]}")
                print(f"Last 200 chars: {output[-200:]}")
                
                # Check if output contains expected patterns
                if 'bundle-' in output:
                    print("✓ Found 'bundle-' in output")
                if 'Aggregate Interface:' in output:
                    print("✓ Found 'Aggregate Interface:' in output")
                if 'Interface' in output and '|' in output:
                    print("✓ Found table format in output")
                if 'LLDP' in output or 'Neighbor' in output:
                    print("⚠ Output appears to be LLDP data")
            else:
                print("No output received")
            
            print("-" * 50)
            time.sleep(1)
        
        ssh.disconnect()
        
    except Exception as e:
        print(f"Error testing {device_name}: {e}")

def main():
    """Main function"""
    # Load devices
    try:
        with open('devices.yaml', 'r') as f:
            devices_data = yaml.safe_load(f)
    except FileNotFoundError:
        print("devices.yaml not found")
        return
    
    devices = devices_data.get('devices', {})
    
    if not devices:
        print("No devices found in devices.yaml")
        return
    
    print(f"Found {len(devices)} devices to test")
    
    # Test each device
    for device_name, device_config in devices.items():
        test_device_commands(device_name, device_config)

if __name__ == "__main__":
    main() 