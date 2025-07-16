#!/usr/bin/env python3
"""
CLI-based topology discovery for DNOS devices
Uses SSH and CLI parsing instead of NETCONF for compatibility
"""

import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys
import os
import time # Added for time.sleep

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.dnos_ssh import DNOSSSH
from utils.cli_parser import DNOSCLIParser, LLDPNeighbor, LACPBundle

class CLITopologyDiscovery:
    """CLI-based topology discovery using SSH and CLI parsing"""
    
    def __init__(self, devices_file: str = "devices.yaml", debug: bool = False):
        """
        Initialize CLI topology discovery
        
        Args:
            devices_file: Path to devices configuration file
            debug: Enable debug logging
        """
        self.devices_file = devices_file
        self.logger = logging.getLogger('CLITopologyDiscovery')
        
        if debug:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        
        self.parser = DNOSCLIParser(debug=debug)
        self.devices = self._load_devices()
    
    def _load_devices(self) -> Dict[str, Any]:
        """Load device configuration from YAML file"""
        try:
            # Debug: Check if file exists
            if not os.path.exists(self.devices_file):
                self.logger.error(f"Devices file does not exist: {self.devices_file}")
                self.logger.error(f"Current working directory: {os.getcwd()}")
                self.logger.error(f"Absolute path to devices file: {os.path.abspath(self.devices_file)}")
                
                # Try to find the file in common locations
                possible_paths = [
                    "devices.yaml",
                    "../devices.yaml",
                    "../../devices.yaml",
                    "lab_automation/devices.yaml",
                    os.path.join(os.path.dirname(__file__), "..", "devices.yaml"),
                    os.path.join(os.path.dirname(__file__), "..", "..", "devices.yaml")
                ]
                
                self.logger.info("Searching for devices.yaml in common locations:")
                for path in possible_paths:
                    if os.path.exists(path):
                        self.logger.info(f"  Found devices.yaml at: {path}")
                        self.devices_file = path
                        break
                    else:
                        self.logger.debug(f"  Not found: {path}")
                else:
                    self.logger.error("Could not find devices.yaml in any common location")
                    return {}
            
            # Debug: Show file contents
            self.logger.debug(f"Loading devices from: {self.devices_file}")
            with open(self.devices_file, 'r') as f:
                content = f.read()
                self.logger.debug(f"Devices file content:\n{content}")
            
            # Parse YAML
            with open(self.devices_file, 'r') as f:
                devices = yaml.safe_load(f)
            
            self.logger.info(f"Loaded {len(devices.get('devices', {}))} devices from {self.devices_file}")
            
            # Debug: Show loaded devices
            for device_name, device_config in devices.get('devices', {}).items():
                self.logger.debug(f"  Device: {device_name} -> {device_config.get('mgmt_ip', 'unknown')}")
            
            return devices.get('devices', {})
            
        except Exception as e:
            self.logger.error(f"Failed to load devices from {self.devices_file}: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {}
    
    def discover_device_topology(self, device_name: str, device_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Discover topology information for a single device
        
        Args:
            device_name: Name of the device
            device_config: Device configuration dictionary
            
        Returns:
            Dict containing device topology information
        """
        self.logger.info(f"Discovering topology for device: {device_name}")
        self.logger.debug(f"Device config: {device_config}")
        
        # Create SSH connection
        ssh = DNOSSSH(
            hostname=device_config['mgmt_ip'],
            username=device_config['username'],
            password=device_config['password'],
            port=device_config.get('ssh_port', 22),
            debug=True  # Enable SSH debugging
        )
        
        device_info = {
            'name': device_name,
            'hostname': device_config['mgmt_ip'],
            'device_type': device_config.get('device_type', 'unknown'),
            'interfaces': [],
            'neighbors': [],
            'lacp_bundles': {},
            'interface_mapping': {},
            'status': 'discovered'
        }
        
        try:
            self.logger.debug(f"Attempting SSH connection to {device_config['mgmt_ip']}:{device_config.get('ssh_port', 22)}")
            
            if not ssh.connect():
                self.logger.error(f"Failed to connect to {device_name}")
                device_info['status'] = 'connection_failed'
                return device_info
            
            self.logger.info(f"Successfully connected to {device_name}")
            
            # Test basic connectivity first
            self.logger.debug("Testing basic connectivity...")
            test_output = ssh.send_command('whoami')
            self.logger.debug(f"whoami output: {test_output}")
            
            # Get LLDP neighbors
            self.logger.debug("Running 'show lldp neighbors' command...")
            lldp_output = ssh.send_command('show lldp neighbors', wait_time=2.0)
            
            neighbors = []
            if lldp_output:
                self.logger.debug(f"LLDP output received (length: {len(lldp_output)}):")
                self.logger.debug(f"First 500 chars: {lldp_output[:500]}")
                
                neighbors = self.parser.parse_lldp_neighbors(lldp_output)
                device_info['neighbors'] = [
                    {
                        'local_interface': n.local_interface,
                        'neighbor_system_name': n.neighbor_system_name,
                        'neighbor_interface': n.neighbor_interface,
                        'neighbor_ttl': n.neighbor_ttl
                    }
                    for n in neighbors
                ]
                self.logger.info(f"Found {len(neighbors)} LLDP neighbors on {device_name}")
                
                # Debug: Show parsed neighbors
                for i, neighbor in enumerate(neighbors):
                    self.logger.debug(f"  Neighbor {i+1}: {neighbor.local_interface} -> {neighbor.neighbor_system_name}")
            else:
                self.logger.warning(f"No LLDP output received from {device_name}")
            
            # Clear buffer and wait before next command
            ssh._clear_buffer()
            time.sleep(2)
            
            # Get interfaces and parse bundle information
            self.logger.debug("Running 'show interfaces' command...")
            interfaces_output = ssh.send_command('show interfaces', wait_time=2.0)
            
            interfaces = []
            bundles = {}
            if interfaces_output:
                self.logger.debug(f"Interfaces output received (length: {len(interfaces_output)})")
                
                # Parse regular interfaces
                interfaces = self.parser.parse_interfaces(interfaces_output)
                device_info['interfaces'] = [
                    {
                        'name': i.name,
                        'status': i.status,
                        'description': i.description,
                        'ip_address': i.ip_address,
                        'vlan': i.vlan
                    }
                    for i in interfaces
                ]
                
                # Parse bundle interfaces
                bundles = self.parser.parse_bundle_interfaces(interfaces_output)
                device_info['bundles'] = {
                    bundle_name: {
                        'interfaces': bundle.interfaces,
                        'status': bundle.status
                    }
                    for bundle_name, bundle in bundles.items()
                }
                
                self.logger.info(f"Found {len(interfaces)} interfaces and {len(bundles)} bundles on {device_name}")
                
                # Debug: Show parsed bundles
                for bundle_name, bundle in bundles.items():
                    self.logger.debug(f"  Bundle {bundle_name}: status: {bundle.status}")
            else:
                device_info['interfaces'] = []
                device_info['bundles'] = {}
                self.logger.warning(f"No interfaces data for {device_name}")

            # Clear buffer before next command
            ssh._clear_buffer()
            time.sleep(1)
            
            # Get LACP counters to map physical interfaces to bundles
            self.logger.debug("Running 'show lacp counters' command...")
            lacp_counters_output = ssh.send_command('show lacp counters', wait_time=2.0)
            
            lacp_bundles = {}
            if lacp_counters_output:
                self.logger.debug(f"LACP counters output received (length: {len(lacp_counters_output)})")
                
                # Parse LACP counters to get physical interface to bundle mappings
                lacp_bundles = self.parser.parse_lacp_counters(lacp_counters_output)
                device_info['lacp_bundles'] = {
                    bundle_name: {
                        'interfaces': bundle.interfaces,
                        'status': bundle.status,
                        'local_key': bundle.local_key,
                        'peer_key': bundle.peer_key,
                        'peer_system_id': bundle.peer_system_id
                    }
                    for bundle_name, bundle in lacp_bundles.items()
                }
                
                self.logger.info(f"Found {len(lacp_bundles)} LACP bundles on {device_name}")
                
                # Debug: Show parsed LACP bundles
                for bundle_name, bundle in lacp_bundles.items():
                    self.logger.debug(f"  LACP Bundle {bundle_name}: {len(bundle.interfaces)} interfaces, status: {bundle.status}")
                    for interface in bundle.interfaces:
                        self.logger.debug(f"    - {interface}")
            else:
                device_info['lacp_bundles'] = {}
                self.logger.warning(f"No LACP counters data for {device_name}")

            # Clear buffer before next command
            ssh._clear_buffer()
            time.sleep(1)
            
            # Create interface mapping (physical interfaces to logical bundles)
            if device_info.get('neighbors') and lacp_bundles:
                self.logger.debug("Creating interface mapping...")
                interface_mapping = self.parser.create_interface_mapping(
                    device_info['neighbors'], 
                    lacp_bundles
                )
                device_info['interface_mapping'] = interface_mapping
                self.logger.info(f"Created interface mapping for {len(interface_mapping)} interfaces")
            else:
                device_info['interface_mapping'] = {}
                self.logger.debug("No interface mapping created (no neighbors or LACP bundles)")
            
        except Exception as e:
            self.logger.error(f"Error discovering topology for {device_name}: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            device_info['status'] = 'discovery_failed'
            device_info['error'] = str(e)
        
        finally:
            ssh.disconnect()
        
        return device_info
    
    def discover_full_topology(self) -> Dict[str, Any]:
        """
        Discover topology for all devices
        
        Returns:
            Dict containing full topology information
        """
        self.logger.info("Starting full topology discovery")
        self.logger.debug(f"Devices to discover: {list(self.devices.keys())}")
        
        topology = {
            'devices': {},
            'connections': [],
            'lacp_connections': [],
            'discovery_time': None,
            'status': 'completed'
        }
        
        discovered_devices = {}
        
        # Discover each device
        for device_name, device_config in self.devices.items():
            try:
                self.logger.info(f"Processing device: {device_name}")
                device_info = self.discover_device_topology(device_name, device_config)
                discovered_devices[device_name] = device_info
                
                if device_info['status'] == 'discovered':
                    self.logger.info(f"Successfully discovered {device_name}")
                else:
                    self.logger.warning(f"Failed to discover {device_name}: {device_info.get('status', 'unknown')}")
                    if 'error' in device_info:
                        self.logger.warning(f"  Error: {device_info['error']}")
                    
            except Exception as e:
                self.logger.error(f"Exception during discovery of {device_name}: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                discovered_devices[device_name] = {
                    'name': device_name,
                    'hostname': device_config.get('mgmt_ip', 'unknown'),
                    'status': 'discovery_failed',
                    'error': str(e)
                }
        
        topology['devices'] = discovered_devices
        
        # Build connections from LLDP data
        connections = self._build_connections(discovered_devices)
        topology['connections'] = connections
        
        # Build LACP connections (CRITICAL for spine-leaf)
        lacp_connections = self._build_lacp_connections(discovered_devices)
        topology['lacp_connections'] = lacp_connections
        
        self.logger.info(f"Topology discovery completed. Found {len(connections)} LLDP connections and {len(lacp_connections)} LACP connections.")
        
        # Debug: Show summary
        successful_devices = [d for d in discovered_devices.values() if d['status'] == 'discovered']
        failed_devices = [d for d in discovered_devices.values() if d['status'] != 'discovered']
        
        self.logger.info(f"Summary: {len(successful_devices)} successful, {len(failed_devices)} failed")
        
        if failed_devices:
            self.logger.warning("Failed devices:")
            for device in failed_devices:
                self.logger.warning(f"  {device['name']}: {device.get('error', 'Unknown error')}")
        
        return topology
    
    def _build_connections(self, devices: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Build connection list from device LLDP data
        
        Args:
            devices: Dictionary of discovered devices
            
        Returns:
            List of connection dictionaries
        """
        connections = []
        processed_connections = set()
        
        for device_name, device_info in devices.items():
            if device_info.get('status') != 'discovered':
                continue
            
            for neighbor in device_info.get('neighbors', []):
                # Create a unique connection identifier
                local_side = f"{device_name}:{neighbor['local_interface']}"
                remote_side = f"{neighbor['neighbor_system_name']}:{neighbor['neighbor_interface']}"
                
                # Sort to ensure consistent ordering
                connection_id = tuple(sorted([local_side, remote_side]))
                
                if connection_id not in processed_connections:
                    connection = {
                        'device1': device_name,
                        'interface1': neighbor['local_interface'],
                        'device2': neighbor['neighbor_system_name'],
                        'interface2': neighbor['neighbor_interface'],
                        'type': 'lldp'
                    }
                    connections.append(connection)
                    processed_connections.add(connection_id)
                    
                    self.logger.debug(f"Added LLDP connection: {device_name}:{neighbor['local_interface']} <-> {neighbor['neighbor_system_name']}:{neighbor['neighbor_interface']}")
        
        return connections
    
    def _build_lacp_connections(self, devices: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build LACP connection list from device LACP data (CRITICAL for spine-leaf)
        
        Args:
            devices: Dictionary of discovered devices
            
        Returns:
            List of LACP connection dictionaries
        """
        lacp_connections = []
        processed_bundles = set()
        
        for device_name, device_info in devices.items():
            if device_info.get('status') != 'discovered':
                continue
            
            # Process LACP bundles
            for bundle_name, bundle_info in device_info.get('lacp_bundles', {}).items():
                # Create unique bundle identifier
                bundle_id = f"{device_name}:{bundle_name}"
                
                if bundle_id not in processed_bundles:
                    # Find the logical interface mapping for this bundle
                    logical_interface = None
                    physical_interfaces = []
                    neighbor_info = None
                    
                    # Look through interface mapping to find bundle members
                    for physical_interface, mapping in device_info.get('interface_mapping', {}).items():
                        if mapping['type'] == 'lacp_member' and mapping['logical_interface'] == bundle_name:
                            physical_interfaces.append(physical_interface)
                            logical_interface = mapping['logical_interface']
                            neighbor_info = mapping['lldp_neighbor']
                    
                    if logical_interface and neighbor_info:
                        lacp_connection = {
                            'device1': device_name,
                            'bundle1': bundle_name,
                            'logical_interface1': logical_interface,
                            'physical_interfaces1': physical_interfaces,
                            'bundle_key1': bundle_info['local_key'],
                            'peer_key1': bundle_info['peer_key'],
                            'peer_system_id1': bundle_info['peer_system_id'],
                            'bundle_status1': bundle_info['status'],
                            'device2': neighbor_info['system_name'],
                            'neighbor_interface2': neighbor_info['interface'],
                            'type': 'lacp_bundle'
                        }
                        
                        lacp_connections.append(lacp_connection)
                        processed_bundles.add(bundle_id)
                        
                        self.logger.debug(f"Added LACP connection: {device_name}:{bundle_name} ({', '.join(physical_interfaces)}) <-> {neighbor_info['system_name']}:{neighbor_info['interface']}")
        
        return lacp_connections
    
    def save_topology(self, topology: Dict[str, Any], output_file: str = "discovered_topology_cli.yaml"):
        """
        Save discovered topology to YAML file
        
        Args:
            topology: Topology dictionary
            output_file: Output file path
        """
        try:
            self.logger.debug(f"Saving topology to: {output_file}")
            with open(output_file, 'w') as f:
                yaml.dump(topology, f, default_flow_style=False, indent=2)
            self.logger.info(f"Topology saved to {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to save topology to {output_file}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def save_lacp_bundles(self, topology: Dict[str, Any], output_file: str = "lacp_bundles.yaml"):
        """
        Save all LACP bundles per device to a YAML file
        """
        bundles_data = {"devices": {}}
        for device_name, device_info in topology.get("devices", {}).items():
            bundles = device_info.get("lacp_bundles", {})
            bundles_data["devices"][device_name] = {"bundles": bundles}
        with open(output_file, "w") as f:
            yaml.dump(bundles_data, f, default_flow_style=False, indent=2)
        self.logger.info(f"LACP bundles saved to {output_file}")

    def save_lacp_interface_mapping(self, topology: Dict[str, Any], output_file: str = "lacp_interface_mapping.yaml"):
        """
        Save physical-to-logical interface mapping per device to a YAML file
        """
        mapping_data = {"devices": {}}
        for device_name, device_info in topology.get("devices", {}).items():
            mapping = device_info.get("interface_mapping", {})
            # Only keep physical->logical mapping (not all neighbor info)
            mapping_data["devices"][device_name] = {
                k: v["logical_interface"] for k, v in mapping.items()
            }
        with open(output_file, "w") as f:
            yaml.dump(mapping_data, f, default_flow_style=False, indent=2)
        self.logger.info(f"LACP interface mapping saved to {output_file}")

    def get_xml_config(self, device_name: str, ssh: DNOSSSH) -> Optional[str]:
        """
        Get full XML configuration from device
        """
        try:
            self.logger.debug(f"Getting XML config for {device_name}...")
            xml_output = ssh.send_command('show config | display-xml', wait_time=5.0)
            
            if xml_output:
                # Save to temporary file for debugging
                temp_file = f"temp_config_{device_name}.xml"
                with open(temp_file, 'w') as f:
                    f.write(xml_output)
                self.logger.info(f"XML config saved to {temp_file}")
                return xml_output
            else:
                self.logger.warning(f"No XML config received from {device_name}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting XML config from {device_name}: {e}")
            return None

    def parse_xml_bundle_mapping(self, xml_config: str) -> Dict[str, Any]:
        """
        Parse XML configuration to find bundle-physical interface mappings
        """
        import xml.etree.ElementTree as ET
        
        bundle_mapping = {
            'bundles': {},
            'interface_mapping': {}
        }
        
        try:
            # Parse XML
            root = ET.fromstring(xml_config)
            
            # Look for bundle interfaces and their member interfaces
            # This will depend on the actual XML structure from your devices
            
            # Common patterns to look for:
            # 1. Bundle interfaces (port-channel, bundle, ae, etc.)
            # 2. Member interfaces under bundles
            # 3. Interface configurations
            
            # For now, let's create a basic structure and we'll refine based on actual XML
            self.logger.info("Parsing XML for bundle mappings...")
            
            # Save parsed structure for debugging
            bundle_mapping['xml_structure'] = self._extract_xml_structure(root)
            
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {e}")
        except Exception as e:
            self.logger.error(f"Error parsing XML: {e}")
        
        return bundle_mapping

    def _extract_xml_structure(self, root, max_depth=3, current_depth=0):
        """
        Extract basic XML structure for debugging
        """
        if current_depth >= max_depth:
            return f"... (truncated at depth {max_depth})"
        
        structure = {}
        for child in root:
            tag = child.tag
            if tag not in structure:
                structure[tag] = []
            
            if len(child) > 0:
                structure[tag].append(self._extract_xml_structure(child, max_depth, current_depth + 1))
            else:
                structure[tag].append(child.text if child.text else "")
        
        return structure

def main():
    """Main function for CLI topology discovery"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CLI-based topology discovery for DNOS devices')
    parser.add_argument('--devices', default='devices.yaml', help='Devices configuration file')
    parser.add_argument('--output', default='discovered_topology_cli.yaml', help='Output topology file')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run discovery
    discovery = CLITopologyDiscovery(devices_file=args.devices, debug=args.debug)
    topology = discovery.discover_full_topology()
    
    # Save results
    discovery.save_topology(topology, args.output)
    discovery.save_lacp_bundles(topology, "lacp_bundles.yaml")
    discovery.save_lacp_interface_mapping(topology, "lacp_interface_mapping.yaml")
    
    # Print summary
    print(f"\nTopology Discovery Summary:")
    print(f"  Devices discovered: {len([d for d in topology['devices'].values() if d['status'] == 'discovered'])}")
    print(f"  LLDP connections: {len(topology['connections'])}")
    print(f"  LACP connections: {len(topology['lacp_connections'])}")
    print(f"  Output file: {args.output}")
    print(f"  LACP bundles: lacp_bundles.yaml")
    print(f"  LACP interface mapping: lacp_interface_mapping.yaml")

if __name__ == "__main__":
    main() 