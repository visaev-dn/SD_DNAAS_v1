#!/usr/bin/env python3
"""
CLI Parser for DNOS devices
Handles parsing of various CLI command outputs with support for future NETCONF migration
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import logging

@dataclass
class LLDPNeighbor:
    """Data class for LLDP neighbor information"""
    local_interface: str
    neighbor_system_name: str
    neighbor_interface: str
    neighbor_ttl: str

@dataclass
class InterfaceInfo:
    """Data class for interface information"""
    name: str
    status: str
    description: Optional[str] = None
    ip_address: Optional[str] = None
    vlan: Optional[str] = None

@dataclass
class LACPBundle:
    """Data class for LACP bundle information"""
    bundle_name: str
    local_key: Optional[str] = None
    peer_key: Optional[str] = None
    peer_system_id: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    status: str = "active"  # active, standby, etc.

@dataclass
class LACPInterface:
    """Data class for LACP interface information"""
    interface_name: str
    bundle_name: str
    role: str  # actor, partner
    port_state: str  # active, standby, etc.
    protocol_state: str  # ascd, N/A, etc.
    port_priority: str
    port_id: str

class DNOSCLIParser:
    """Parser for DNOS CLI command outputs"""
    
    def __init__(self, debug: bool = False):
        """
        Initialize the CLI parser
        
        Args:
            debug: Enable debug logging
        """
        self.logger = logging.getLogger('DNOSCLIParser')
        if debug:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
    
    def parse_lldp_neighbors(self, output: str) -> List[LLDPNeighbor]:
        """
        Parse LLDP neighbors output from DNOS devices
        
        Args:
            output: Raw CLI output from 'show lldp neighbors' command
            
        Returns:
            List[LLDPNeighbor]: List of parsed LLDP neighbor information
        """
        neighbors = []
        
        # Split output into lines and skip header lines
        lines = output.strip().split('\n')
        
        # Find the table header line (contains | characters)
        header_index = -1
        for i, line in enumerate(lines):
            if '|' in line and 'Interface' in line and 'Neighbor' in line:
                header_index = i
                break
        
        if header_index == -1:
            self.logger.warning("Could not find LLDP neighbors table header")
            return neighbors
        
        # Skip the header and separator lines
        data_lines = []
        for line in lines[header_index + 1:]:
            line = line.strip()
            if line and '|' in line and not line.startswith('|--'):
                data_lines.append(line)
        
        # Parse each data line
        for line in data_lines:
            try:
                # Split by | and clean up whitespace
                parts = [part.strip() for part in line.split('|')]
                
                # Skip empty lines or lines without enough data
                if len(parts) < 4 or not parts[1].strip():
                    continue
                
                # Extract data (parts[0] is empty due to leading |)
                local_interface = parts[1]
                neighbor_system_name = parts[2]
                neighbor_interface = parts[3]
                neighbor_ttl = parts[4] if len(parts) > 4 else "120"
                
                # Skip entries with empty neighbor names (no neighbors)
                if not neighbor_system_name or neighbor_system_name == "":
                    continue
                
                neighbor = LLDPNeighbor(
                    local_interface=local_interface,
                    neighbor_system_name=neighbor_system_name,
                    neighbor_interface=neighbor_interface,
                    neighbor_ttl=neighbor_ttl
                )
                neighbors.append(neighbor)
                
                self.logger.debug(f"Parsed LLDP neighbor: {neighbor}")
                
            except Exception as e:
                self.logger.warning(f"Failed to parse LLDP line '{line}': {e}")
                continue
        
        self.logger.info(f"Successfully parsed {len(neighbors)} LLDP neighbors")
        return neighbors
    
    def parse_lacp_interfaces(self, output: str) -> Dict[str, LACPBundle]:
        """
        Parse LACP interfaces output from DNOS devices
        
        Args:
            output: Raw CLI output from 'show lacp interfaces' command
            
        Returns:
            Dict[str, LACPBundle]: Dictionary mapping bundle names to LACP bundle information
        """
        bundles = {}
        
        # Split output into lines
        lines = output.strip().split('\n')
        
        current_bundle = None
        in_table = False
        
        for line in lines:
            line = line.strip()
            
            # Look for bundle interface header
            if line.startswith('Aggregate Interface:'):
                bundle_name = line.split('Aggregate Interface:')[1].strip()
                current_bundle = LACPBundle(bundle_name=bundle_name)
                bundles[bundle_name] = current_bundle
                in_table = False
                self.logger.debug(f"Found LACP bundle: {bundle_name}")
                
            # Parse local key
            elif current_bundle and 'Key:' in line and 'Local:' in line:
                match = re.search(r'Key:\s*(\d+)', line)
                if match:
                    current_bundle.local_key = match.group(1)
                    self.logger.debug(f"  Local key: {current_bundle.local_key}")
                    
            # Parse peer key
            elif current_bundle and 'Key:' in line and 'Peer:' in line:
                match = re.search(r'Key:\s*(\d+|N/A)', line)
                if match and match.group(1) != 'N/A':
                    current_bundle.peer_key = match.group(1)
                    self.logger.debug(f"  Peer key: {current_bundle.peer_key}")
                    
            # Parse peer system ID
            elif current_bundle and 'System-id:' in line and 'Peer:' in line:
                match = re.search(r'System-id:\s*([a-fA-F0-9:]+)', line)
                if match and match.group(1) != 'N/A':
                    current_bundle.peer_system_id = match.group(1)
                    self.logger.debug(f"  Peer system ID: {current_bundle.peer_system_id}")
                    
            # Look for table header
            elif '| Interface' in line and '| Role' in line:
                in_table = True
                self.logger.debug("Found LACP table header")
                
            # Parse table data
            elif in_table and '|' in line and not line.startswith('|--'):
                try:
                    # Split by | and clean up whitespace
                    parts = [part.strip() for part in line.split('|')]
                    
                    if len(parts) >= 7:
                        interface_name = parts[1]
                        role = parts[2]
                        port_state = parts[3]
                        protocol_state = parts[4]
                        port_priority = parts[5]
                        port_id = parts[6]
                        
                        # Only process actor entries (avoid duplicates)
                        if role == 'actor':
                            current_bundle.interfaces.append(interface_name)
                            
                            # Update bundle status based on port state
                            if port_state == 'standby':
                                current_bundle.status = 'standby'
                                
                            self.logger.debug(f"  Interface {interface_name} -> {current_bundle.bundle_name} (state: {port_state})")
                            
                except Exception as e:
                    self.logger.warning(f"Failed to parse LACP table line '{line}': {e}")
                    continue
                    
            # End of table (empty line or new section)
            elif in_table and (not line or line.startswith('Aggregate Interface:')):
                in_table = False
        
        self.logger.info(f"Successfully parsed {len(bundles)} LACP bundles")
        for bundle_name, bundle in bundles.items():
            self.logger.debug(f"Bundle {bundle_name}: {len(bundle.interfaces)} interfaces, status: {bundle.status}")
            
        return bundles
    
    def parse_lacp_counters(self, output: str) -> Dict[str, LACPBundle]:
        """
        Parse LACP counters output to find bundle-physical interface mappings
        Handles multi-line records where Bundle-Id is on the following indented line.
        """
        bundles = {}
        if not output:
            return bundles
        lines = output.strip().split('\n')
        last_physical_interface = None
        for idx, line in enumerate(lines):
            line = line.strip()
            # Bundle interface line
            if line.startswith('|') and 'bundle-' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    interface_name = parts[1].strip()
                    admin_status = parts[2].strip()
                    operational_status = parts[3].strip()
                    bundle_name = interface_name.split(' ')[0]
                    bundle_name = bundle_name.split('.')[0]
                    if bundle_name.startswith('bundle-'):
                        if bundle_name not in bundles:
                            bundle = LACPBundle(bundle_name=bundle_name)
                            bundle.status = operational_status
                            bundles[bundle_name] = bundle
                            self.logger.debug(f"Found LACP bundle: {bundle_name} (status: {operational_status})")
                        else:
                            if '.' not in interface_name:
                                bundles[bundle_name].status = operational_status
                last_physical_interface = None
            # Physical interface line
            elif line.startswith('|') and 'ge' in line and 'bundle-' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    interface_name = parts[1].strip()
                    if interface_name.startswith('ge') and interface_name != 'Interface':
                        last_physical_interface = interface_name
                        # Look ahead for Bundle-Id in the next indented line
                        bundle_id = None
                        if idx + 1 < len(lines):
                            next_line = lines[idx + 1]
                            if '|' in next_line and next_line.startswith(' '):
                                next_parts = [p.strip() for p in next_line.split('|')]
                                if len(next_parts) >= 8:
                                    bundle_id_str = next_parts[7].strip()
                                    if bundle_id_str and bundle_id_str.isdigit():
                                        bundle_id = f"bundle-{bundle_id_str}"
                        if bundle_id and bundle_id in bundles:
                            bundles[bundle_id].interfaces.append(interface_name)
                            self.logger.debug(f"  Added interface {interface_name} to bundle {bundle_id}")
                        else:
                            self.logger.debug(f"  Interface {interface_name} has bundle ID {bundle_id} but bundle not found")
                else:
                    last_physical_interface = None
            else:
                last_physical_interface = None
        self.logger.info(f"Successfully parsed {len(bundles)} LACP bundles from counters")
        return bundles
    
    def parse_bundle_interfaces(self, output: str) -> Dict[str, LACPBundle]:
        """
        Parse bundle interfaces from 'show interfaces' output
        Format:
        | bundle-60000             | enabled  | up              |                        |
        | bundle-445 (L2)          | enabled  | down            |                        |
        """
        bundles = {}
        
        if not output:
            return bundles
        
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for bundle interface lines (start with | and contain 'bundle-')
            if line.startswith('|') and 'bundle-' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    interface_name = parts[1].strip()
                    admin_status = parts[2].strip()
                    operational_status = parts[3].strip()
                    
                    # Extract bundle name (remove any suffixes like (L2) or .150)
                    bundle_name = interface_name.split(' ')[0]  # Remove (L2) suffix
                    bundle_name = bundle_name.split('.')[0]     # Remove .150 suffix
                    
                    if bundle_name.startswith('bundle-'):
                        # Create or update bundle
                        if bundle_name not in bundles:
                            bundle = LACPBundle(bundle_name=bundle_name)
                            bundle.status = operational_status
                            bundles[bundle_name] = bundle
                            self.logger.debug(f"Found bundle interface: {bundle_name} (status: {operational_status})")
                        else:
                            # Update status if this is the main bundle (not a sub-interface)
                            if '.' not in interface_name:
                                bundles[bundle_name].status = operational_status
        
        self.logger.info(f"Successfully parsed {len(bundles)} bundle interfaces from 'show interfaces'")
        return bundles
    
    def create_interface_mapping(self, lldp_neighbors: List[LLDPNeighbor], 
                                lacp_bundles: Dict[str, LACPBundle]) -> Dict[str, Dict[str, Any]]:
        """
        Create mapping between physical interfaces and logical bundles
        
        Args:
            lldp_neighbors: List of LLDP neighbors
            lacp_bundles: Dictionary of LACP bundles
            
        Returns:
            Dict mapping physical interfaces to logical information
        """
        interface_mapping = {}
        
        # Create reverse mapping from physical interface to bundle
        physical_to_bundle = {}
        for bundle_name, bundle in lacp_bundles.items():
            for interface in bundle.interfaces:
                physical_to_bundle[interface] = {
                    'bundle_name': bundle_name,
                    'bundle_key': bundle.local_key,
                    'peer_key': bundle.peer_key,
                    'peer_system_id': bundle.peer_system_id,
                    'bundle_status': bundle.status
                }
        
        # Process LLDP neighbors and map to bundles
        for neighbor in lldp_neighbors:
            physical_interface = neighbor.local_interface
            
            # Check if this physical interface is part of a bundle
            if physical_interface in physical_to_bundle:
                bundle_info = physical_to_bundle[physical_interface]
                
                interface_mapping[physical_interface] = {
                    'type': 'lacp_member',
                    'logical_interface': bundle_info['bundle_name'],
                    'bundle_key': bundle_info['bundle_key'],
                    'peer_key': bundle_info['peer_key'],
                    'peer_system_id': bundle_info['peer_system_id'],
                    'bundle_status': bundle_info['bundle_status'],
                    'lldp_neighbor': {
                        'system_name': neighbor.neighbor_system_name,
                        'interface': neighbor.neighbor_interface,
                        'ttl': neighbor.neighbor_ttl
                    }
                }
                
                self.logger.debug(f"Mapped {physical_interface} -> {bundle_info['bundle_name']} (neighbor: {neighbor.neighbor_system_name})")
            else:
                # Standalone interface
                interface_mapping[physical_interface] = {
                    'type': 'standalone',
                    'logical_interface': physical_interface,
                    'lldp_neighbor': {
                        'system_name': neighbor.neighbor_system_name,
                        'interface': neighbor.neighbor_interface,
                        'ttl': neighbor.neighbor_ttl
                    }
                }
                
                self.logger.debug(f"Mapped {physical_interface} -> standalone (neighbor: {neighbor.neighbor_system_name})")
        
        return interface_mapping
    
    def parse_interfaces(self, output: str) -> List[InterfaceInfo]:
        """
        Parse interface information from 'show interfaces' command
        
        Args:
            output: Raw CLI output from 'show interfaces' command
            
        Returns:
            List[InterfaceInfo]: List of parsed interface information
        """
        interfaces = []
        
        # This is a placeholder - implement based on actual 'show interfaces' output
        # You'll need to provide the actual output format for this command
        
        self.logger.info(f"Parsed {len(interfaces)} interfaces")
        return interfaces
    
    def parse_interface_brief(self, output: str) -> List[InterfaceInfo]:
        """
        Parse interface brief information from 'show ip interface brief' command
        
        Args:
            output: Raw CLI output from 'show ip interface brief' command
            
        Returns:
            List[InterfaceInfo]: List of parsed interface information
        """
        interfaces = []
        
        # This is a placeholder - implement based on actual 'show ip interface brief' output
        # You'll need to provide the actual output format for this command
        
        self.logger.info(f"Parsed {len(interfaces)} interfaces from brief output")
        return interfaces
    
    def parse_version(self, output: str) -> Dict[str, str]:
        """
        Parse version information from 'show version' command
        
        Args:
            output: Raw CLI output from 'show version' command
            
        Returns:
            Dict[str, str]: Parsed version information
        """
        version_info = {}
        
        # This is a placeholder - implement based on actual 'show version' output
        # You'll need to provide the actual output format for this command
        
        self.logger.info("Parsed version information")
        return version_info
    
    def parse_running_config(self, output: str) -> Dict[str, Any]:
        """
        Parse running configuration
        
        Args:
            output: Raw CLI output from 'show running-config' command
            
        Returns:
            Dict[str, Any]: Parsed configuration
        """
        config = {}
        
        # This is a placeholder - implement based on actual 'show running-config' output
        # You'll need to provide the actual output format for this command
        
        self.logger.info("Parsed running configuration")
        return config

# Example usage and testing
if __name__ == "__main__":
    # Test with the provided LLDP output
    test_lldp_output = """DNAAS-LEAF-B14(06-Jul-2025-16:06:42)# show lldp neighbors 

| Interface    | Neighbor System Name    | Neighbor interface   | Neighbor TTL   |
|--------------+-------------------------+----------------------+----------------|
| ge100-0/0/0  | ARIEL-Metropolis        | ge100-0/0/2          | 120            |
| ge100-0/0/1  | ARIEL-Metropolis        | ge100-0/0/36         | 120            |
| ge100-0/0/2  | NCP-3-Zohar             | ge400-0/0/11         | 120            |
| ge100-0/0/3  | NCP-3-Zohar             | ge400-0/0/33         | 120            |
| ge100-0/0/4  | YOR_PE-3                | ge100-0/0/71         | 120            |
| ge100-0/0/5  |                         |                      |                |
| ge100-0/0/6  |                         |                      |                |
| ge100-0/0/7  |                         |                      |                |
| ge100-0/0/8  |                         |                      |                |
| ge100-0/0/9  |                         |                      |                |
| ge100-0/0/10 |                         |                      |                |
| ge100-0/0/11 | Slava_2_WNG1C57500001P2 | ge100-0/0/69         | 120            |
| ge100-0/0/12 | Slava_2_WNG1C57500001P2 | ge100-0/0/70         | 120            |
| ge100-0/0/13 | arista410               | Ethernet21/1         | 120            |
| ge100-0/0/14 |                         |                      |                |
| ge100-0/0/15 | YOR_SPIRENT             | 00:00:00:00:00:02    | 120            |
| ge100-0/0/15 | YOR_SPIRENT             | 00:00:00:00:00:03    | 120            |
| ge100-0/0/16 | ARIEL-CL16              | ge100-0/0/5          | 120            |
| ge100-0/0/17 | ARIEL-CL16              | ge100-3/0/7          | 120            |
| ge100-0/0/18 | sysp171-Cris            | ge400-0/0/31         | 120            |
| ge100-0/0/19 | Slava_2_WNG1C57500001P2 | ge100-0/0/71         | 120            |
| ge100-0/0/20 |                         |                      |                |
| ge100-0/0/21 |                         |                      |                |
| ge100-0/0/22 |                         |                      |                |
| ge100-0/0/23 |                         |                      |                |
| ge100-0/0/24 |                         |                      |                |
| ge100-0/0/25 |                         |                      |                |
| ge100-0/0/26 |                         |                      |                |
| ge100-0/0/27 |                         |                      |                |
| ge100-0/0/28 |                         |                      |                |
| ge100-0/0/29 |                         |                      |                |
| ge100-0/0/30 |                         |                      |                |
| ge100-0/0/31 |                         |                      |                |
| ge100-0/0/32 |                         |                      |                |
| ge100-0/0/33 |                         |                      |                |
| ge100-0/0/34 |                         |                      |                |
| ge100-0/0/35 |                         |                      |                |
| ge100-0/0/36 | DNAAS-SPINE-B09         | ge100-0/0/8          | 120            |
| ge100-0/0/37 | DNAAS-SPINE-B09         | ge100-0/0/9          | 120            |
| ge100-0/0/38 | DNAAS-SPINE-B09         | ge100-0/0/10         | 120            |
| ge100-0/0/39 |                         |                      |                |"""
    
    # Test with the provided LACP output
    test_lacp_output = """DNAAS-LEAF-B14(06-Jul-2025-16:33:16)# show lacp interfaces 

System Default LACP Settings:
        System-priority: 1, System-id: 84:40:76:c7:6c:2f

Aggregate Interface: bundle-60000
        Local:
                Mode: active, Period: short, Key: 60000
                System-priority: 1, System-id: 84:40:76:c7:6c:2f
                Force-up: disabled

        Peer:
                Mode: active, Key: 60003
                System-priority: 1, System-id: 84:40:76:1e:e5:35

Legend: a - aggregatable, s - synchronized, c - collecting, d - distributing, e - evpn unsync, i - incompatible

| Interface    | Role    | Port State   | Protocol State   | Port Priority   | Port Id   | Period   |
|--------------+---------+--------------+------------------+-----------------+-----------+----------|
| ge100-0/0/36 | actor   | active       | ascd             | 32768           | 37        | short    |
| ge100-0/0/36 | partner | active       | ascd             | 32768           | 9         | short    |
| ge100-0/0/37 | actor   | active       | ascd             | 32768           | 38        | short    |
| ge100-0/0/37 | partner | active       | ascd             | 32768           | 10        | short    |
| ge100-0/0/38 | actor   | active       | ascd             | 32768           | 39        | short    |
| ge100-0/0/38 | partner | active       | ascd             | 32768           | 11        | short    |

Aggregate Interface: bundle-445
        Local:
                Mode: active, Period: short, Key: 445
                System-priority: 1, System-id: 84:40:76:c7:6c:2f
                Force-up: disabled

        Peer:
                Mode: N/A, Key: N/A
                System-priority: N/A, System-id: N/A

Legend: a - aggregatable, s - synchronized, c - collecting, d - distributing, e - evpn unsync, i - incompatible

| Interface    | Role    | Port State   | Protocol State   | Port Priority   | Port Id   | Period   |
|--------------+---------+--------------+------------------+-----------------+-----------+----------|
| ge100-0/0/9  | actor   | standby      | N/A              | 32768           | 10        | short    |
| ge100-0/0/9  | partner |              |                  |                 |           |          |
| ge100-0/0/10 | actor   | standby      | N/A              | 32768           | 11        | short    |
| ge100-0/0/10 | partner |              |                  |                 |           |          |"""
    
    parser = DNOSCLIParser(debug=True)
    
    # Parse LLDP neighbors
    neighbors = parser.parse_lldp_neighbors(test_lldp_output)
    print(f"\nParsed {len(neighbors)} LLDP neighbors:")
    for neighbor in neighbors:
        print(f"  {neighbor.local_interface} -> {neighbor.neighbor_system_name} ({neighbor.neighbor_interface})")
    
    # Parse LACP bundles
    bundles = parser.parse_lacp_interfaces(test_lacp_output)
    print(f"\nParsed {len(bundles)} LACP bundles:")
    for bundle_name, bundle in bundles.items():
        print(f"  {bundle_name}: {len(bundle.interfaces)} interfaces, status: {bundle.status}")
        for interface in bundle.interfaces:
            print(f"    - {interface}")
    
    # Create interface mapping
    interface_mapping = parser.create_interface_mapping(neighbors, bundles)
    print(f"\nInterface mapping:")
    for physical_interface, mapping in interface_mapping.items():
        if mapping['type'] == 'lacp_member':
            print(f"  {physical_interface} -> {mapping['logical_interface']} (LACP bundle)")
        else:
            print(f"  {physical_interface} -> {mapping['logical_interface']} (standalone)") 