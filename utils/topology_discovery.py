#!/usr/bin/env python3
"""
Topology Discovery - Automatically maps network topology using NETCONF LLDP data
Discovers device connections and builds topology map dynamically
"""

import logging
import yaml
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from ncclient import manager
from ncclient.transport.errors import AuthenticationError, SSHUnknownHostError

logger = logging.getLogger(__name__)

class TopologyDiscovery:
    """Automatic topology discovery using NETCONF LLDP data"""
    
    def __init__(self, devices: Dict[str, Dict[str, Any]]):
        """Initialize topology discovery with device information"""
        self.devices = devices
        self.discovered_topology = {}
        self.lldp_data = {}
        
    def discover_topology(self) -> Dict[str, Any]:
        """Main method to discover complete topology"""
        logger.info("Starting automatic topology discovery using LLDP data")
        
        try:
            # Step 1: Collect LLDP data from all devices
            self._collect_lldp_data()
            
            # Step 2: Parse LLDP data to find connections
            connections = self._parse_lldp_connections()
            
            # Step 3: Build topology map
            topology = self._build_topology_map(connections)
            
            # Step 4: Validate topology
            self._validate_topology(topology)
            
            logger.info("Topology discovery completed successfully")
            return topology
            
        except Exception as e:
            logger.error(f"Topology discovery failed: {e}")
            raise
    
    def _collect_lldp_data(self):
        """Collect LLDP data from all devices using NETCONF"""
        logger.info("Collecting LLDP data from devices...")
        
        for device_name, device_info in self.devices.items():
            try:
                logger.info(f"Connecting to {device_name} ({device_info['mgmt_ip']})")
                
                # Establish NETCONF connection
                with manager.connect(
                    host=device_info['mgmt_ip'],
                    port=device_info.get('netconf_port', 830),
                    username=device_info['username'],
                    password=device_info['password'],
                    hostkey_verify=False,
                    timeout=30
                ) as m:
                    
                    # Get LLDP neighbors data
                    lldp_filter = """
                    <lldp xmlns="http://openconfig.net/yang/lldp">
                        <interfaces>
                            <interface>
                                <name/>
                                <neighbors>
                                    <neighbor>
                                        <id/>
                                        <state>
                                            <system-name/>
                                            <port-id/>
                                            <port-description/>
                                        </state>
                                    </neighbor>
                                </neighbors>
                            </interface>
                        </interfaces>
                    </lldp>
                    """
                    
                    # Try different LLDP models for different vendors
                    lldp_models = [
                        # OpenConfig LLDP
                        lldp_filter,
                        # Cisco LLDP
                        """
                        <lldp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-lldp-oper">
                            <lldp-entries>
                                <lldp-entry>
                                    <device-id/>
                                    <local-interface/>
                                    <connecting-interface/>
                                    <ttl/>
                                </lldp-entry>
                            </lldp-entries>
                        </lldp>
                        """,
                        # Arista LLDP
                        """
                        <lldp xmlns="http://arista.com/yang/openconfig/lldp">
                            <interfaces>
                                <interface>
                                    <name/>
                                    <neighbors>
                                        <neighbor>
                                            <id/>
                                            <state>
                                                <system-name/>
                                                <port-id/>
                                            </state>
                                        </neighbor>
                                    </neighbors>
                                </interface>
                            </interfaces>
                        </lldp>
                        """
                    ]
                    
                    lldp_data = None
                    for model in lldp_models:
                        try:
                            response = m.get(filter=('subtree', model))
                            if response.xml:
                                lldp_data = response.xml
                                logger.info(f"Successfully collected LLDP data from {device_name}")
                                break
                        except Exception as e:
                            logger.debug(f"LLDP model failed for {device_name}: {e}")
                            continue
                    
                    if lldp_data:
                        self.lldp_data[device_name] = lldp_data
                    else:
                        logger.warning(f"No LLDP data available from {device_name}")
                        
            except AuthenticationError:
                logger.error(f"Authentication failed for {device_name}")
            except SSHUnknownHostError:
                logger.error(f"SSH connection failed for {device_name}")
            except Exception as e:
                logger.error(f"Failed to collect LLDP data from {device_name}: {e}")
    
    def _parse_lldp_connections(self) -> List[Dict[str, Any]]:
        """Parse LLDP data to extract device connections"""
        logger.info("Parsing LLDP data to discover connections...")
        
        connections = []
        
        for device_name, lldp_xml in self.lldp_data.items():
            try:
                root = ET.fromstring(lldp_xml)
                
                # Parse based on different LLDP models
                if 'openconfig' in lldp_xml.lower():
                    connections.extend(self._parse_openconfig_lldp(device_name, root))
                elif 'cisco' in lldp_xml.lower():
                    connections.extend(self._parse_cisco_lldp(device_name, root))
                elif 'arista' in lldp_xml.lower():
                    connections.extend(self._parse_arista_lldp(device_name, root))
                else:
                    # Try generic parsing
                    connections.extend(self._parse_generic_lldp(device_name, root))
                    
            except Exception as e:
                logger.error(f"Failed to parse LLDP data for {device_name}: {e}")
        
        return connections
    
    def _parse_openconfig_lldp(self, device_name: str, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse OpenConfig LLDP format"""
        connections = []
        
        # Find all interfaces with LLDP neighbors
        for interface in root.findall('.//{http://openconfig.net/yang/lldp}interface'):
            interface_name = interface.find('.//{http://openconfig.net/yang/lldp}name')
            if interface_name is not None:
                local_port = interface_name.text
                
                # Find neighbors for this interface
                for neighbor in interface.findall('.//{http://openconfig.net/yang/lldp}neighbor'):
                    neighbor_id = neighbor.find('.//{http://openconfig.net/yang/lldp}id')
                    system_name = neighbor.find('.//{http://openconfig.net/yang/lldp}system-name')
                    port_id = neighbor.find('.//{http://openconfig.net/yang/lldp}port-id')
                    
                    if neighbor_id is not None and system_name is not None:
                        connections.append({
                            'local_device': device_name,
                            'local_port': local_port,
                            'remote_device': system_name.text,
                            'remote_port': port_id.text if port_id is not None else 'unknown',
                            'neighbor_id': neighbor_id.text
                        })
        
        return connections
    
    def _parse_cisco_lldp(self, device_name: str, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse Cisco LLDP format"""
        connections = []
        
        for entry in root.findall('.//{http://cisco.com/ns/yang/Cisco-IOS-XE-lldp-oper}lldp-entry'):
            device_id = entry.find('.//{http://cisco.com/ns/yang/Cisco-IOS-XE-lldp-oper}device-id')
            local_interface = entry.find('.//{http://cisco.com/ns/yang/Cisco-IOS-XE-lldp-oper}local-interface')
            connecting_interface = entry.find('.//{http://cisco.com/ns/yang/Cisco-IOS-XE-lldp-oper}connecting-interface')
            
            if device_id is not None and local_interface is not None:
                connections.append({
                    'local_device': device_name,
                    'local_port': local_interface.text,
                    'remote_device': device_id.text,
                    'remote_port': connecting_interface.text if connecting_interface is not None else 'unknown',
                    'neighbor_id': device_id.text
                })
        
        return connections
    
    def _parse_arista_lldp(self, device_name: str, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse Arista LLDP format"""
        connections = []
        
        for interface in root.findall('.//{http://arista.com/yang/openconfig/lldp}interface'):
            interface_name = interface.find('.//{http://arista.com/yang/openconfig/lldp}name')
            if interface_name is not None:
                local_port = interface_name.text
                
                for neighbor in interface.findall('.//{http://arista.com/yang/openconfig/lldp}neighbor'):
                    neighbor_id = neighbor.find('.//{http://arista.com/yang/openconfig/lldp}id')
                    system_name = neighbor.find('.//{http://arista.com/yang/openconfig/lldp}system-name')
                    port_id = neighbor.find('.//{http://arista.com/yang/openconfig/lldp}port-id')
                    
                    if neighbor_id is not None and system_name is not None:
                        connections.append({
                            'local_device': device_name,
                            'local_port': local_port,
                            'remote_device': system_name.text,
                            'remote_port': port_id.text if port_id is not None else 'unknown',
                            'neighbor_id': neighbor_id.text
                        })
        
        return connections
    
    def _parse_generic_lldp(self, device_name: str, root: ET.Element) -> List[Dict[str, Any]]:
        """Generic LLDP parsing for unknown formats"""
        connections = []
        
        # Try to find common LLDP elements
        for neighbor in root.findall('.//*[contains(local-name(), "neighbor") or contains(local-name(), "entry")]'):
            # Look for common LLDP fields
            device_id = neighbor.find('.//*[contains(local-name(), "device-id") or contains(local-name(), "system-name")]')
            local_port = neighbor.find('.//*[contains(local-name(), "local-interface") or contains(local-name(), "interface")]')
            remote_port = neighbor.find('.//*[contains(local-name(), "connecting-interface") or contains(local-name(), "port-id")]')
            
            if device_id is not None:
                connections.append({
                    'local_device': device_name,
                    'local_port': local_port.text if local_port is not None else 'unknown',
                    'remote_device': device_id.text,
                    'remote_port': remote_port.text if remote_port is not None else 'unknown',
                    'neighbor_id': device_id.text
                })
        
        return connections
    
    def _build_topology_map(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build topology map from discovered connections"""
        logger.info("Building topology map from discovered connections...")
        
        topology = {
            'devices': {},
            'connections': connections,
            'spine_links': [],
            'leaf_links': []
        }
        
        # Initialize device information
        for device_name, device_info in self.devices.items():
            topology['devices'][device_name] = {
                'mgmt_ip': device_info['mgmt_ip'],
                'device_type': device_info.get('device_type', 'unknown'),
                'username': device_info['username'],
                'password': device_info['password'],
                'spine_links': [],
                'ports': []
            }
        
        # Process connections to identify spine and leaf links
        for conn in connections:
            local_device = conn['local_device']
            remote_device = conn['remote_device']
            
            # Add ports to device lists
            if local_device in topology['devices']:
                if conn['local_port'] not in topology['devices'][local_device]['ports']:
                    topology['devices'][local_device]['ports'].append(conn['local_port'])
            
            if remote_device in topology['devices']:
                if conn['remote_port'] not in topology['devices'][remote_device]['ports']:
                    topology['devices'][remote_device]['ports'].append(conn['remote_port'])
            
            # Identify spine links (connections between leaf and spine)
            if self._is_spine_link(local_device, remote_device):
                topology['spine_links'].append(conn)
                if local_device in topology['devices']:
                    topology['devices'][local_device]['spine_links'].append(conn['local_port'])
                if remote_device in topology['devices']:
                    topology['devices'][remote_device]['spine_links'].append(conn['remote_port'])
            else:
                topology['leaf_links'].append(conn)
        
        return topology
    
    def _is_spine_link(self, device1: str, device2: str) -> bool:
        """Determine if a connection is a spine link"""
        # Check if one device is a spine and the other is a leaf
        device1_is_spine = 'spine' in device1.lower()
        device2_is_spine = 'spine' in device2.lower()
        
        # Also check if devices are in the known spine list
        known_spines = [name for name, info in self.devices.items() if 'spine' in name.lower()]
        device1_is_known_spine = device1 in known_spines
        device2_is_known_spine = device2 in known_spines
        
        return (device1_is_spine or device1_is_known_spine) != (device2_is_spine or device2_is_known_spine)
    
    def _validate_topology(self, topology: Dict[str, Any]):
        """Validate discovered topology"""
        logger.info("Validating discovered topology...")
        
        # Check for missing devices
        discovered_devices = set(topology['devices'].keys())
        expected_devices = set(self.devices.keys())
        missing_devices = expected_devices - discovered_devices
        
        if missing_devices:
            logger.warning(f"Missing devices in discovery: {missing_devices}")
        
        # Check for spine-leaf connectivity
        leaf_devices = [name for name in topology['devices'].keys() if 'leaf' in name.lower()]
        spine_devices = [name for name in topology['devices'].keys() if 'spine' in name.lower()]
        
        logger.info(f"Discovered {len(leaf_devices)} leaf devices: {leaf_devices}")
        logger.info(f"Discovered {len(spine_devices)} spine devices: {spine_devices}")
        logger.info(f"Discovered {len(topology['spine_links'])} spine links")
        logger.info(f"Discovered {len(topology['leaf_links'])} leaf links")
        
        # Validate spine-leaf connectivity
        for leaf in leaf_devices:
            leaf_spine_links = [conn for conn in topology['spine_links'] 
                              if conn['local_device'] == leaf or conn['remote_device'] == leaf]
            if len(leaf_spine_links) < 2:
                logger.warning(f"Leaf device {leaf} has fewer than 2 spine connections")
    
    def save_topology(self, topology: Dict[str, Any], filename: str = "discovered_topology.yaml"):
        """Save discovered topology to YAML file"""
        try:
            with open(filename, 'w') as f:
                yaml.dump(topology, f, default_flow_style=False, indent=2)
            logger.info(f"Topology saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save topology: {e}")

def discover_topology_from_devices(devices: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function to discover topology from device list"""
    discovery = TopologyDiscovery(devices)
    return discovery.discover_topology()

def discover_and_save_topology(devices: Dict[str, Dict[str, Any]], 
                              output_file: str = "discovered_topology.yaml") -> Dict[str, Any]:
    """Discover topology and save to file"""
    discovery = TopologyDiscovery(devices)
    topology = discovery.discover_topology()
    discovery.save_topology(topology, output_file)
    return topology 