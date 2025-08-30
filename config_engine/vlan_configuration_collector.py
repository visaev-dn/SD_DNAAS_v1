#!/usr/bin/env python3
"""
VLAN Configuration Collector

This module collects real VLAN configurations from network devices via SSH
and parses them to extract detailed VLAN information including:
- Interface VLAN assignments
- QinQ configurations
- VLAN manipulation rules
- Bridge domain VLAN mappings
"""

import os
import sys
import re
import yaml
import json
import logging
import paramiko
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.ssh.connection.connection_manager import SSHConnectionManager
from config_engine.ssh.execution.command_executor import SSHCommandExecutor

logger = logging.getLogger(__name__)

@dataclass
class VLANConfiguration:
    """Structured VLAN configuration data"""
    interface: str
    vlan_id: Optional[int]
    outer_vlan: Optional[int]
    inner_vlan: Optional[int]
    vlan_range: Optional[str]
    vlan_list: Optional[List[int]]
    vlan_manipulation: Optional[Dict[str, str]]
    bridge_domain: Optional[str]
    interface_type: str
    description: Optional[str]
    status: str
    raw_config: str

class VLANConfigurationCollector:
    """
    Collects VLAN configurations from network devices via SSH.
    
    Supports:
    - DNOS/Arista devices
    - QinQ configurations
    - VLAN manipulation rules
    - Bridge domain mappings
    """
    
    def __init__(self, devices_file: str = "devices.yaml"):
        self.devices_file = Path(devices_file)
        self.output_dir = Path("topology/configs/parsed_data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # SSH connection manager
        self.ssh_manager = SSHConnectionManager()
        self.command_executor = SSHCommandExecutor()
        
        # DNOS VLAN configuration patterns
        self.vlan_patterns = {
            'interface_vlan': r'interfaces\s+(\S+)\s+vlan-id\s+(\d+)',
            'interface_vlan_range': r'interfaces\s+(\S+)\s+vlan-id\s+list\s+(\d+)-(\d+)',
            'interface_vlan_list': r'interfaces\s+(\S+)\s+vlan-id\s+list\s+([\d\s]+)',
            'vlan_manipulation_ingress': r'interfaces\s+(\S+)\s+vlan-manipulation\s+ingress-mapping\s+action\s+push\s+outer-tag\s+(\d+)',
            'vlan_manipulation_egress': r'interfaces\s+(\S+)\s+vlan-manipulation\s+egress-mapping\s+action\s+pop',
            'qinq_outer_inner': r'interfaces\s+(\S+)\s+vlan-tags\s+outer-tag\s+(\d+)\s+inner-tag\s+(\d+)',
            'l2_service': r'interfaces\s+(\S+)\s+l2-service\s+enabled',
            'bridge_domain_interface': r'network-services\s+bridge-domain\s+instance\s+(\S+)\s+interface\s+(\S+)',
            'interface_description': r'interfaces\s+(\S+)\s+description\s+(.+)'
        }
    
    def load_devices(self) -> Dict[str, Dict]:
        """Load device configurations from devices.yaml"""
        try:
            with open(self.devices_file, 'r') as f:
                devices = yaml.safe_load(f)
            logger.info(f"Loaded {len(devices)} devices from {self.devices_file}")
            return devices
        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
            return {}
    
    def collect_vlan_configurations(self, device_name: str, device_info: Dict) -> List[VLANConfiguration]:
        """
        Collect VLAN configurations from a specific device.
        
        Args:
            device_name: Name of the device
            device_info: Device connection information
            
        Returns:
            List of VLAN configurations
        """
        vlan_configs = []
        
        try:
            # Connect to device
            ssh_client = self.ssh_manager.connect_to_device(device_info)
            if not ssh_client:
                logger.error(f"Failed to connect to {device_name}")
                return vlan_configs
            
            # Collect VLAN-related configurations
            vlan_configs.extend(self._collect_interface_vlan_configs(ssh_client, device_name))
            vlan_configs.extend(self._collect_vlan_manipulation_configs(ssh_client, device_name))
            vlan_configs.extend(self._collect_qinq_configs(ssh_client, device_name))
            vlan_configs.extend(self._collect_bridge_domain_configs(ssh_client, device_name))
            vlan_configs.extend(self._collect_interface_descriptions(ssh_client, device_name))
            
            # Close SSH connection
            ssh_client.close()
            
            logger.info(f"Collected {len(vlan_configs)} VLAN configurations from {device_name}")
            
        except Exception as e:
            logger.error(f"Error collecting VLAN configurations from {device_name}: {e}")
        
        return vlan_configs
    
    def _collect_interface_vlan_configs(self, ssh_client: paramiko.SSHClient, device_name: str) -> List[VLANConfiguration]:
        """Collect interface VLAN ID configurations"""
        vlan_configs = []
        
        try:
            # Get interface VLAN configurations
            command = "show running-config interfaces | grep -E '(vlan-id|vlan-range|vlan-list)'"
            success, output = self.command_executor.execute_command(ssh_client, command)
            
            if not success:
                logger.warning(f"Failed to get VLAN configs from {device_name}")
                return vlan_configs
            
            # Parse VLAN ID assignments
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Match single VLAN ID
                match = re.search(self.vlan_patterns['interface_vlan'], line)
                if match:
                    interface, vlan_id = match.groups()
                    vlan_configs.append(VLANConfiguration(
                        interface=interface,
                        vlan_id=int(vlan_id),
                        outer_vlan=None,
                        inner_vlan=None,
                        vlan_range=None,
                        vlan_list=None,
                        vlan_manipulation=None,
                        bridge_domain=None,
                        interface_type='subinterface' if '.' in interface else 'physical',
                        description=None,
                        status='active',
                        raw_config=line
                    ))
                    continue
                
                # Match VLAN range
                match = re.search(self.vlan_patterns['interface_vlan_range'], line)
                if match:
                    interface, vlan_start, vlan_end = match.groups()
                    vlan_configs.append(VLANConfiguration(
                        interface=interface,
                        vlan_id=None,
                        outer_vlan=None,
                        inner_vlan=None,
                        vlan_range=f"{vlan_start}-{vlan_end}",
                        vlan_list=None,
                        vlan_manipulation=None,
                        bridge_domain=None,
                        interface_type='subinterface' if '.' in interface else 'physical',
                        description=None,
                        status='active',
                        raw_config=line
                    ))
                    continue
                
                # Match VLAN list
                match = re.search(self.vlan_patterns['interface_vlan_list'], line)
                if match:
                    interface, vlan_list_str = match.groups()
                    vlan_list = [int(v.strip()) for v in vlan_list_str.split() if v.strip().isdigit()]
                    vlan_configs.append(VLANConfiguration(
                        interface=interface,
                        vlan_id=None,
                        outer_vlan=None,
                        inner_vlan=None,
                        vlan_range=None,
                        vlan_list=vlan_list,
                        vlan_manipulation=None,
                        bridge_domain=None,
                        interface_type='subinterface' if '.' in interface else 'physical',
                        description=None,
                        status='active',
                        raw_config=line
                    ))
        
        except Exception as e:
            logger.error(f"Error collecting interface VLAN configs from {device_name}: {e}")
        
        return vlan_configs
    
    def _collect_vlan_manipulation_configs(self, ssh_client: paramiko.SSHClient, device_name: str) -> List[VLANConfiguration]:
        """Collect VLAN manipulation configurations (QinQ)"""
        vlan_configs = []
        
        try:
            # Get VLAN manipulation configurations
            command = "show running-config interfaces | grep -A 5 -B 5 'vlan-manipulation'"
            success, output = self.command_executor.execute_command(ssh_client, command)
            
            if not success:
                logger.warning(f"Failed to get VLAN manipulation configs from {device_name}")
                return vlan_configs
            
            # Parse VLAN manipulation
            current_interface = None
            manipulation_config = {}
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check for interface line
                interface_match = re.search(r'interfaces\s+(\S+)', line)
                if interface_match:
                    # Save previous interface if exists
                    if current_interface and manipulation_config:
                        vlan_configs.append(VLANConfiguration(
                            interface=current_interface,
                            vlan_id=None,
                            outer_vlan=None,
                            inner_vlan=None,
                            vlan_range=None,
                            vlan_list=None,
                            vlan_manipulation=manipulation_config.copy(),
                            bridge_domain=None,
                            interface_type='subinterface' if '.' in current_interface else 'physical',
                            description=None,
                            status='active',
                            raw_config=str(manipulation_config)
                        ))
                    
                    # Start new interface
                    current_interface = interface_match.group(1)
                    manipulation_config = {}
                    continue
                
                # Check for ingress mapping
                ingress_match = re.search(self.vlan_patterns['vlan_manipulation_ingress'], line)
                if ingress_match:
                    interface, outer_vlan = ingress_match.groups()
                    manipulation_config['ingress'] = f"push outer-tag {outer_vlan}"
                    manipulation_config['outer_vlan'] = int(outer_vlan)
                    continue
                
                # Check for egress mapping
                if 'egress-mapping' in line and 'pop' in line:
                    manipulation_config['egress'] = 'pop outer-tag'
                    continue
            
            # Save last interface
            if current_interface and manipulation_config:
                vlan_configs.append(VLANConfiguration(
                    interface=current_interface,
                    vlan_id=None,
                    outer_vlan=manipulation_config.get('outer_vlan'),
                    inner_vlan=None,
                    vlan_range=None,
                    vlan_list=None,
                    vlan_manipulation=manipulation_config.copy(),
                    bridge_domain=None,
                    interface_type='subinterface' if '.' in current_interface else 'physical',
                    description=None,
                    status='active',
                    raw_config=str(manipulation_config)
                ))
        
        except Exception as e:
            logger.error(f"Error collecting VLAN manipulation configs from {device_name}: {e}")
        
        return vlan_configs
    
    def _collect_qinq_configs(self, ssh_client: paramiko.SSHClient, device_name: str) -> List[VLANConfiguration]:
        """Collect QinQ outer/inner tag configurations"""
        vlan_configs = []
        
        try:
            # Get QinQ configurations
            command = "show running-config interfaces | grep -A 3 -B 3 'vlan-tags'"
            success, output = self.command_executor.execute_command(ssh_client, command)
            
            if not success:
                logger.warning(f"Failed to get QinQ configs from {device_name}")
                return vlan_configs
            
            # Parse QinQ configurations
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                match = re.search(self.vlan_patterns['qinq_outer_inner'], line)
                if match:
                    interface, outer_vlan, inner_vlan = match.groups()
                    vlan_configs.append(VLANConfiguration(
                        interface=interface,
                        vlan_id=int(inner_vlan),  # Inner VLAN is typically the primary
                        outer_vlan=int(outer_vlan),
                        inner_vlan=int(inner_vlan),
                        vlan_range=None,
                        vlan_list=None,
                        vlan_manipulation=None,
                        bridge_domain=None,
                        interface_type='subinterface' if '.' in interface else 'physical',
                        description=None,
                        status='active',
                        raw_config=line
                    ))
        
        except Exception as e:
            logger.error(f"Error collecting QinQ configs from {device_name}: {e}")
        
        return vlan_configs
    
    def _collect_bridge_domain_configs(self, ssh_client: paramiko.SSHClient, device_name: str) -> List[VLANConfiguration]:
        """Collect bridge domain interface mappings"""
        vlan_configs = []
        
        try:
            # Get bridge domain configurations
            command = "show running-config network-services | grep -A 10 -B 5 'bridge-domain instance'"
            success, output = self.command_executor.execute_command(ssh_client, command)
            
            if not success:
                logger.warning(f"Failed to get bridge domain configs from {device_name}")
                return vlan_configs
            
            # Parse bridge domain configurations
            current_bd = None
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check for bridge domain instance
                bd_match = re.search(r'bridge-domain\s+instance\s+(\S+)', line)
                if bd_match:
                    current_bd = bd_match.group(1)
                    continue
                
                # Check for interface assignment
                if current_bd and 'interface' in line:
                    interface_match = re.search(r'interface\s+(\S+)', line)
                    if interface_match:
                        interface = interface_match.group(1)
                        vlan_configs.append(VLANConfiguration(
                            interface=interface,
                            vlan_id=None,
                            outer_vlan=None,
                            inner_vlan=None,
                            vlan_range=None,
                            vlan_list=None,
                            vlan_manipulation=None,
                            bridge_domain=current_bd,
                            interface_type='subinterface' if '.' in interface else 'physical',
                            description=None,
                            status='active',
                            raw_config=line
                        ))
        
        except Exception as e:
            logger.error(f"Error collecting bridge domain configs from {device_name}: {e}")
        
        return vlan_configs
    
    def _collect_interface_descriptions(self, ssh_client: paramiko.SSHClient, device_name: str) -> List[VLANConfiguration]:
        """Collect interface descriptions"""
        vlan_configs = []
        
        try:
            # Get interface descriptions
            command = "show running-config interfaces | grep -E 'description'"
            success, output = self.command_executor.execute_command(ssh_client, command)
            
            if not success:
                logger.warning(f"Failed to get interface descriptions from {device_name}")
                return vlan_configs
            
            # Parse interface descriptions
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                match = re.search(self.vlan_patterns['interface_description'], line)
                if match:
                    interface, description = match.groups()
                    
                    # Find existing config for this interface
                    existing_config = next(
                        (config for config in vlan_configs if config.interface == interface),
                        None
                    )
                    
                    if existing_config:
                        existing_config.description = description
                    else:
                        # Create new config entry for description-only interfaces
                        vlan_configs.append(VLANConfiguration(
                            interface=interface,
                            vlan_id=None,
                            outer_vlan=None,
                            inner_vlan=None,
                            vlan_range=None,
                            vlan_list=None,
                            vlan_manipulation=None,
                            bridge_domain=None,
                            interface_type='subinterface' if '.' in interface else 'physical',
                            description=description,
                            status='active',
                            raw_config=line
                        ))
        
        except Exception as e:
            logger.error(f"Error collecting interface descriptions from {device_name}: {e}")
        
        return vlan_configs
    
    def save_vlan_configurations(self, device_name: str, vlan_configs: List[VLANConfiguration]) -> None:
        """Save VLAN configurations to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{device_name}_vlan_config_parsed_{timestamp}.yaml"
            filepath = self.output_dir / filename
            
            # Convert dataclass objects to dictionaries
            config_data = []
            for config in vlan_configs:
                config_dict = asdict(config)
                config_data.append(config_dict)
            
            output_data = {
                'device': device_name,
                'timestamp': timestamp,
                'vlan_configurations': config_data,
                'summary': {
                    'total_configs': len(config_data),
                    'subinterfaces': len([c for c in config_data if c['interface_type'] == 'subinterface']),
                    'physical_interfaces': len([c for c in config_data if c['interface_type'] == 'physical']),
                    'qinq_configs': len([c for c in config_data if c['vlan_manipulation']]),
                    'bridge_domain_mappings': len([c for c in config_data if c['bridge_domain']])
                }
            }
            
            with open(filepath, 'w') as f:
                yaml.dump(output_data, f, default_flow_style=False, indent=2)
            
            logger.info(f"Saved {len(config_data)} VLAN configurations to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving VLAN configurations for {device_name}: {e}")
    
    def run_collection(self) -> Dict[str, Any]:
        """Run complete VLAN configuration collection"""
        logger.info("🚀 Starting VLAN Configuration Collection...")
        
        devices = self.load_devices()
        if not devices:
            logger.error("No devices found to collect from")
            return {}
        
        collection_results = {
            'collection_metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_devices': len(devices),
                'successful_collections': 0,
                'failed_collections': 0
            },
            'device_results': {}
        }
        
        for device_name, device_info in devices.items():
            logger.info(f"🔍 Collecting VLAN configurations from {device_name}...")
            
            try:
                vlan_configs = self.collect_vlan_configurations(device_name, device_info)
                
                if vlan_configs:
                    self.save_vlan_configurations(device_name, vlan_configs)
                    collection_results['device_results'][device_name] = {
                        'status': 'success',
                        'configs_collected': len(vlan_configs),
                        'timestamp': datetime.now().isoformat()
                    }
                    collection_results['collection_metadata']['successful_collections'] += 1
                else:
                    collection_results['device_results'][device_name] = {
                        'status': 'no_configs',
                        'configs_collected': 0,
                        'timestamp': datetime.now().isoformat()
                    }
                    collection_results['collection_metadata']['successful_collections'] += 1
                
            except Exception as e:
                logger.error(f"Failed to collect from {device_name}: {e}")
                collection_results['device_results'][device_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                collection_results['collection_metadata']['failed_collections'] += 1
        
        # Save collection summary
        summary_file = self.output_dir / f"vlan_collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(collection_results, f, indent=2, default=str)
        
        logger.info("✅ VLAN Configuration Collection Complete!")
        logger.info(f"📊 Results: {collection_results['collection_metadata']['successful_collections']} successful, {collection_results['collection_metadata']['failed_collections']} failed")
        
        return collection_results

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run VLAN configuration collection
    collector = VLANConfigurationCollector()
    results = collector.run_collection()
    
    # Print summary
    print(f"\n🎯 Collection Summary:")
    print(f"   Total Devices: {results['collection_metadata']['total_devices']}")
    print(f"   Successful: {results['collection_metadata']['successful_collections']}")
    print(f"   Failed: {results['collection_metadata']['failed_collections']}")
