#!/usr/bin/env python3
"""
Test script to check DNAAS-SPINE-A08 connectivity and data collection
"""

import yaml
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.dnos_ssh import DNOSSSH

def test_dnaas_spine_a08():
    """Test connectivity and data collection for DNAAS-SPINE-A08"""
    
    # Load device config
    with open('devices.yaml', 'r') as f:
        data = yaml.safe_load(f)
    
    defaults = data.get('defaults', {})
    device_config = data.get('DNAAS-SPINE-A08', {})
    merged_config = {**defaults, **device_config}
    
    print(f"Device config for DNAAS-SPINE-A08:")
    print(f"  mgmt_ip: {merged_config.get('mgmt_ip')}")
    print(f"  username: {merged_config.get('username')}")
    print(f"  password: {merged_config.get('password')}")
    print(f"  ssh_port: {merged_config.get('ssh_port')}")
    
    mgmt_ip = merged_config.get('mgmt_ip')
    username = merged_config.get('username', 'admin')
    password = merged_config.get('password', 'admin')
    ssh_port = merged_config.get('ssh_port', 22)
    
    if not mgmt_ip or mgmt_ip == 'TBD':
        print("❌ No management IP configured for DNAAS-SPINE-A08")
        return False
    
    print(f"\n🔍 Testing connectivity to {mgmt_ip}...")
    
    # Test SSH connection
    ssh = DNOSSSH(hostname=mgmt_ip, username=username, password=password, port=ssh_port)
    
    try:
        ssh.connect()
        print("✅ SSH connection successful")
        
        # Test LACP command
        print("\n🔍 Testing LACP command...")
        lacp_command = "show config protocols lacp | display-xml | no-more"
        lacp_output = ssh.send_command(lacp_command)
        
        if lacp_output and '<config' in lacp_output:
            print("✅ LACP XML collection successful")
            print(f"   Output length: {len(lacp_output)} characters")
            print(f"   Contains <config>: {'<config' in lacp_output}")
        else:
            print("❌ LACP XML collection failed")
            print(f"   Output: {lacp_output[:200] if lacp_output else 'None'}")
        
        # Test LLDP command
        print("\n🔍 Testing LLDP command...")
        lldp_command = "show lldp neighbors | no-more"
        lldp_output = ssh.send_command(lldp_command)
        
        if lldp_output and 'Interface' in lldp_output:
            print("✅ LLDP CLI collection successful")
            print(f"   Output length: {len(lldp_output)} characters")
            print(f"   Contains 'Interface': {'Interface' in lldp_output}")
        else:
            print("❌ LLDP CLI collection failed")
            print(f"   Output: {lldp_output[:200] if lldp_output else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        return False
        
    finally:
        ssh.disconnect()

if __name__ == "__main__":
    test_dnaas_spine_a08() 