#!/usr/bin/env python3
"""
Collect and parse device data with parallel processing.
This script performs a complete refresh with two phases:
1. PROBE: Collect raw LACP XML, LLDP neighbors, and Bridge Domain data to raw-config/
2. PARSE: Process raw data and store parsed results to parsed_data/
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import shutil
import re
import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.dnos_ssh import DNOSSSH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread-local storage for timing
thread_local = threading.local()

# ANSI escape sequence pattern for stripping color codes
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def strip_ansi_codes(text):
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE.sub('', text)

RAW_CONFIG_DIR = Path('topology/configs/raw-config')
RAW_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Bridge domain specific directory
BRIDGE_DOMAIN_RAW_DIR = Path('topology/configs/raw-config/bridge_domain_raw')
BRIDGE_DOMAIN_RAW_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_DOMAIN_PARSED_DIR = Path('topology/configs/parsed_data/bridge_domain_parsed')
BRIDGE_DOMAIN_PARSED_DIR.mkdir(parents=True, exist_ok=True)

class ProbeSummary:
    """Track and report comprehensive probe and parse results."""
    
    def __init__(self):
        self.start_time = time.time()
        self.end_time = None
        
        # Device tracking
        self.total_devices = 0
        self.available_devices = 0
        self.invalid_devices = []
        self.failed_devices = []
        self.successful_devices = []
        
        # Collection results - track which devices had successful collection
        self.lacp_successful_devices = set()
        self.lldp_successful_devices = set()
        self.bridge_domain_successful_devices = set()
        self.lacp_successful = 0
        self.lldp_successful = 0
        self.bridge_domain_successful = 0
        self.lacp_failed = 0
        self.lldp_failed = 0
        self.bridge_domain_failed = 0
        
        # Parse results
        self.parse_lacp_successful = 0
        self.parse_lldp_successful = 0
        self.parse_bridge_domain_successful = 0
        self.parse_lacp_failed = 0
        self.parse_lldp_failed = 0
        self.parse_bridge_domain_failed = 0
        self.parse_lacp_successful_devices = set()
        self.parse_lldp_successful_devices = set()
        self.parse_bridge_domain_successful_devices = set()
        self.parse_lacp_bundles = {}
        self.parse_lldp_neighbors = {}
        self.parse_bridge_domain_data = {}
        
        # Error tracking
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)
        
        # Statistics
        self.total_bundles = 0
        self.total_neighbors = 0
        self.total_bridge_domains = 0
        
    def add_device_result(self, device_name, lacp_success, lldp_success, bridge_domain_success, error=None):
        """Add result for a single device."""
        if lacp_success or lldp_success or bridge_domain_success:
            self.successful_devices.append(device_name)
            if lacp_success:
                self.lacp_successful_devices.add(device_name)
                self.lacp_successful += 1
            else:
                self.lacp_failed += 1
            if lldp_success:
                self.lldp_successful_devices.add(device_name)
                self.lldp_successful += 1
            else:
                self.lldp_failed += 1
            if bridge_domain_success:
                self.bridge_domain_successful_devices.add(device_name)
                self.bridge_domain_successful += 1
            else:
                self.bridge_domain_failed += 1
        else:
            self.failed_devices.append(device_name)
            self.lacp_failed += 1
            self.lldp_failed += 1
            self.bridge_domain_failed += 1
        
        if error:
            self.errors[device_name].append(error)
    
    def add_parse_result(self, device_name, data_type, success, bundles_count=0, neighbors_count=0, bridge_domains_count=0, error=None):
        """Add parse result for a single device."""
        if data_type == 'lacp':
            if success:
                self.parse_lacp_successful_devices.add(device_name)
                self.parse_lacp_successful += 1
                self.parse_lacp_bundles[device_name] = bundles_count
                self.total_bundles += bundles_count
            else:
                self.parse_lacp_failed += 1
        elif data_type == 'lldp':
            if success:
                self.parse_lldp_successful_devices.add(device_name)
                self.parse_lldp_successful += 1
                self.parse_lldp_neighbors[device_name] = neighbors_count
                self.total_neighbors += neighbors_count
            else:
                self.parse_lldp_failed += 1
        elif data_type == 'bridge_domain':
            if success:
                self.parse_bridge_domain_successful_devices.add(device_name)
                self.parse_bridge_domain_successful += 1
                self.parse_bridge_domain_data[device_name] = bridge_domains_count
                self.total_bridge_domains += bridge_domains_count
            else:
                self.parse_bridge_domain_failed += 1
        
        if error:
            self.errors[device_name].append(error)
    
    def add_invalid_device(self, device_name, reason):
        """Add device with invalid configuration."""
        self.invalid_devices.append(device_name)
        self.warnings[device_name].append(reason)
    
    def finish(self):
        """Mark the end of the process."""
        self.end_time = time.time()
    
    def get_duration(self):
        """Get total duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def print_summary(self):
        """Print comprehensive summary report to console and write to a txt file."""
        duration = self.get_duration()
        lines = []
        lines.append("\n" + "="*80)
        lines.append("📊 PROBE + PARSE SUMMARY REPORT")
        lines.append("="*80)
        lines.append(f"\n⏱️  TIMING:")
        lines.append(f"   Total duration: {duration:.2f} seconds")
        if self.lacp_successful > 0:
            avg_time = duration / self.lacp_successful
            lines.append(f"   Average time per successful device: {avg_time:.2f} seconds")
            lines.append(f"   Processing rate: {self.lacp_successful / duration:.1f} devices per second")
        lines.append(f"\n📋 DEVICE STATISTICS:")
        lines.append(f"   Total devices in devices.yaml: {self.total_devices}")
        lines.append(f"   Available devices (valid mgmt_ip): {self.available_devices}")
        lines.append(f"   Invalid devices (missing/invalid mgmt_ip): {len(self.invalid_devices)}")
        lines.append(f"   Successful devices: {len(self.successful_devices)}")
        lines.append(f"   Failed devices: {len(self.failed_devices)}")
        lines.append(f"\n🔍 COLLECTION RESULTS:")
        lines.append(f"   LACP XML collection: {self.lacp_successful} successful, {self.lacp_failed} failed")
        lines.append(f"   LLDP CLI collection: {self.lldp_successful} successful, {self.lldp_failed} failed")
        lines.append(f"\n📝 PARSE RESULTS:")
        lines.append(f"   LACP parsing: {self.parse_lacp_successful} successful, {self.parse_lacp_failed} failed")
        lines.append(f"   LLDP parsing: {self.parse_lldp_successful} successful, {self.parse_lldp_failed} failed")
        lines.append(f"   Total bundles extracted: {self.total_bundles}")
        lines.append(f"   Total neighbors extracted: {self.total_neighbors}")
        if self.failed_devices:
            lines.append(f"\n❌ FAILED DEVICES ({len(self.failed_devices)}):")
            for device in sorted(self.failed_devices):
                errors = self.errors.get(device, [])
                lines.append(f"   • {device}")
                for error in errors:
                    lines.append(f"     - {error}")
        if self.invalid_devices:
            lines.append(f"\n⚠️  INVALID DEVICES ({len(self.invalid_devices)}):")
            for device in sorted(self.invalid_devices):
                warnings = self.warnings.get(device, [])
                lines.append(f"   • {device}")
                for warning in warnings:
                    lines.append(f"     - {warning}")
        if self.successful_devices:
            lines.append(f"\n✅ SUCCESSFUL DEVICES ({len(self.successful_devices)}):")
            for device in sorted(self.successful_devices):
                status = []
                if device in self.lacp_successful_devices:
                    status.append("LACP")
                if device in self.lldp_successful_devices:
                    status.append("LLDP")
                if device in self.bridge_domain_successful_devices:
                    status.append("Bridge Domain")
                lines.append(f"   • {device} ({'+'.join(status)})")
        lines.append(f"\n💡 RECOMMENDATIONS:")
        if self.failed_devices:
            lines.append(f"   • {len(self.failed_devices)} devices failed collection - check network connectivity and credentials")
        if self.invalid_devices:
            lines.append(f"   • {len(self.invalid_devices)} devices have invalid mgmt_ip - update devices.yaml")
        if self.parse_lacp_failed > 0:
            lines.append(f"   • {self.parse_lacp_failed} LACP files failed parsing - check XML format")
        if self.parse_lldp_failed > 0:
            lines.append(f"   • {self.parse_lldp_failed} LLDP files failed parsing - check CLI output format")
        lines.append("\n" + "="*80)

        # Print to console
        print("\n".join(lines))

        # Write to file
        summary_path = Path("topology/collection_summary.txt")
        try:
            with open(summary_path, "w") as f:
                f.write("\n".join(lines) + "\n")
            logger.info(f"Summary report written to {summary_path}")
        except Exception as e:
            logger.error(f"Failed to write summary report to {summary_path}: {e}")
        
        # Create structured device status file
        self.create_device_status_file()
    
    def create_device_status_file(self):
        """Create a structured JSON file with all device statuses for easy access."""
        try:
            # Create device status data structure
            device_status = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_devices': self.total_devices,
                    'available_devices': self.available_devices,
                    'successful_devices': len(self.successful_devices),
                    'failed_devices': len(self.failed_devices),
                    'invalid_devices': len(self.invalid_devices),
                    'lacp_successful': self.lacp_successful,
                    'lacp_failed': self.lacp_failed,
                    'lldp_successful': self.lldp_successful,
                    'lldp_failed': self.lldp_failed,
                    'bridge_domain_successful': self.bridge_domain_successful,
                    'bridge_domain_failed': self.bridge_domain_failed,
                    'parse_lacp_successful': self.parse_lacp_successful,
                    'parse_lacp_failed': self.parse_lacp_failed,
                    'parse_lldp_successful': self.parse_lldp_successful,
                    'parse_lldp_failed': self.parse_lldp_failed,
                    'parse_bridge_domain_successful': self.parse_bridge_domain_successful,
                    'parse_bridge_domain_failed': self.parse_bridge_domain_failed,
                    'total_bundles': self.total_bundles,
                    'total_neighbors': self.total_neighbors,
                    'total_bridge_domains': self.total_bridge_domains
                },
                'devices': {}
            }
            
            # Add successful devices
            for device in self.successful_devices:
                device_status['devices'][device] = {
                    'status': 'successful',
                    'lacp_collection': device in self.lacp_successful_devices,
                    'lldp_collection': device in self.lldp_successful_devices,
                    'bridge_domain_collection': device in self.bridge_domain_successful_devices,
                    'lacp_parsing': device in self.parse_lacp_successful_devices,
                    'lldp_parsing': device in self.parse_lldp_successful_devices,
                    'bridge_domain_parsing': device in self.parse_bridge_domain_successful_devices,
                    'bundles_count': self.parse_lacp_bundles.get(device, 0),
                    'neighbors_count': self.parse_lldp_neighbors.get(device, 0),
                    'bridge_domains_count': self.parse_bridge_domain_data.get(device, 0),
                    'errors': [],
                    'warnings': []
                }
            
            # Add failed devices
            for device in self.failed_devices:
                device_status['devices'][device] = {
                    'status': 'failed',
                    'lacp_collection': device in self.lacp_successful_devices,
                    'lldp_collection': device in self.lldp_successful_devices,
                    'bridge_domain_collection': device in self.bridge_domain_successful_devices,
                    'lacp_parsing': device in self.parse_lacp_successful_devices,
                    'lldp_parsing': device in self.parse_lldp_successful_devices,
                    'bridge_domain_parsing': device in self.parse_bridge_domain_successful_devices,
                    'bundles_count': self.parse_lacp_bundles.get(device, 0),
                    'neighbors_count': self.parse_lldp_neighbors.get(device, 0),
                    'bridge_domains_count': self.parse_bridge_domain_data.get(device, 0),
                    'errors': self.errors.get(device, []),
                    'warnings': []
                }
            
            # Add invalid devices
            for device in self.invalid_devices:
                device_status['devices'][device] = {
                    'status': 'invalid',
                    'lacp_collection': False,
                    'lldp_collection': False,
                    'bridge_domain_collection': False,
                    'lacp_parsing': False,
                    'lldp_parsing': False,
                    'bridge_domain_parsing': False,
                    'bundles_count': 0,
                    'neighbors_count': 0,
                    'bridge_domains_count': 0,
                    'errors': [],
                    'warnings': self.warnings.get(device, [])
                }
            
            # Write to JSON file
            status_path = Path("topology/device_status.json")
            with open(status_path, "w") as f:
                json.dump(device_status, f, indent=2)
            
            logger.info(f"Device status file written to {status_path}")
            
        except Exception as e:
            logger.error(f"Failed to create device status file: {e}")

# Global summary object
summary = ProbeSummary()

def load_devices():
    """Load devices from devices.yaml and merge with defaults for each device."""
    try:
        with open('devices.yaml', 'r') as f:
            data = yaml.safe_load(f)
        defaults = data.get('defaults', {})
        merged_devices = {}
        for device_name, device_config in data.items():
            if device_name == 'defaults':
                continue
            if isinstance(device_config, dict):
                merged = {**defaults, **device_config}
                merged_devices[device_name] = merged
        return merged_devices
    except Exception as e:
        logger.error(f"Error loading devices: {e}")
        return {}

def clear_previous_data():
    """Clear previous data directories before fresh collection."""
    data_dirs = [
        'topology/configs/raw-config',
        'topology/configs/parsed_data',
        'topology/configs/raw-config/bridge_domain_raw',
        'topology/configs/parsed_data/bridge_domain_parsed'
    ]
    
    for dir_path in data_dirs:
        if os.path.exists(dir_path):
            logger.info(f"Clearing previous data from {dir_path}")
            shutil.rmtree(dir_path)
        
        # Recreate empty directory
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created fresh directory: {dir_path}")

def collect_raw_device_data(device_name, device_config):
    """Collect raw LACP, LLDP, and Bridge Domain data from a single device."""
    try:
        # Merge device config with defaults
        defaults = device_config.get('defaults', {})
        device_config = {**defaults, **device_config}
        
        mgmt_ip = device_config.get('mgmt_ip')
        username = device_config.get('username', 'admin')
        password = device_config.get('password', 'admin')
        ssh_port = device_config.get('ssh_port', 22)
        
        if not mgmt_ip or mgmt_ip == 'TBD' or mgmt_ip == 'unknown':
            summary.add_invalid_device(device_name, "Invalid mgmt_ip")
            return False, False, False
        
        # Create SSH connection
        ssh = DNOSSSH(hostname=mgmt_ip, username=username, password=password, port=ssh_port)
        
        try:
            ssh.connect()
            
            # Collect LACP XML data
            lacp_command = "show config protocols lacp | display-xml | no-more"
            lacp_output = ssh.send_command(lacp_command)
            
            if lacp_output and '<config' in lacp_output:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_lacp_raw_{timestamp}.xml"
                filepath = RAW_CONFIG_DIR / filename
                
                with open(filepath, 'w') as f:
                    f.write(lacp_output)
                
                logger.info(f"Collected LACP XML for {device_name}")
                lacp_success = True
            else:
                logger.warning(f"Failed to collect LACP XML for {device_name}")
                lacp_success = False
            
            # Small delay between commands
            time.sleep(0.5)
            
            # Collect LLDP CLI data
            lldp_command = "show lldp neighbors | no-more"
            lldp_output = ssh.send_command(lldp_command)
            
            if lldp_output and 'Interface' in lldp_output:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_lldp_raw_{timestamp}.txt"
                filepath = RAW_CONFIG_DIR / filename
                
                with open(filepath, 'w') as f:
                    f.write(lldp_output)
                
                logger.info(f"Collected LLDP CLI for {device_name}")
                lldp_success = True
            else:
                logger.warning(f"Failed to collect LLDP CLI for {device_name}")
                lldp_success = False
            
            # Small delay between commands
            time.sleep(0.5)
            
            # Collect Bridge Domain Instance data
            bridge_domain_instance_command = 'show config | fl | i "bridge-domain instance" | no-more'
            bridge_domain_instance_output = ssh.send_command(bridge_domain_instance_command)
            
            if bridge_domain_instance_output and 'bridge-domain instance' in bridge_domain_instance_output:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_bridge_domain_instance_raw_{timestamp}.txt"
                filepath = BRIDGE_DOMAIN_RAW_DIR / filename
                
                with open(filepath, 'w') as f:
                    f.write(bridge_domain_instance_output)
                
                logger.info(f"Collected Bridge Domain Instance for {device_name}")
                bridge_domain_instance_success = True
            else:
                logger.warning(f"Failed to collect Bridge Domain Instance for {device_name}")
                bridge_domain_instance_success = False
            
            # Small delay between commands
            time.sleep(0.5)
            
            # Collect VLAN Configuration data
            vlan_config_command = 'show config | fl | i vlan | no-more'
            vlan_config_output = ssh.send_command(vlan_config_command)
            
            if vlan_config_output and 'vlan' in vlan_config_output:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_vlan_config_raw_{timestamp}.txt"
                filepath = BRIDGE_DOMAIN_RAW_DIR / filename
                
                with open(filepath, 'w') as f:
                    f.write(vlan_config_output)
                
                logger.info(f"Collected VLAN Config for {device_name}")
                vlan_config_success = True
            else:
                logger.warning(f"Failed to collect VLAN Config for {device_name}")
                vlan_config_success = False
            
            # Bridge domain collection is successful if either command succeeded
            bridge_domain_success = bridge_domain_instance_success or vlan_config_success
            
            return lacp_success, lldp_success, bridge_domain_success
            
        finally:
            ssh.disconnect()
            
    except Exception as e:
        logger.error(f"Error collecting data from {device_name}: {e}")
        summary.add_device_result(device_name, False, False, False, error=f"SSH connection failed: {e}")
        return False, False, False

def parse_lldp_neighbors(lldp_output):
    """Parse LLDP neighbor data from CLI output."""
    neighbors = []
    
    # Split output into lines and look for neighbor entries
    lines = lldp_output.split('\n')
    
    for line in lines:
        # Look for LLDP neighbor patterns
        # Example: "DNAAS-LEAF-B14    ge100-0/0/36    100.64.101.5    ge100-0/0/36"
        if 'ge' in line and ('100.64.' in line or 'DNAAS-' in line):
            parts = line.strip().split()
            if len(parts) >= 4:
                neighbor = {
                    'local_interface': parts[1],
                    'neighbor_device': parts[0],
                    'neighbor_interface': parts[3],
                    'neighbor_ip': parts[2] if len(parts) > 2 else 'unknown'
                }
                neighbors.append(neighbor)
    
    return neighbors

def parse_lldp_xml(xml_content):
    """Parse LLDP XML to extract neighbor information using ElementTree."""
    neighbors = []
    try:
        # Extract only the XML block between <config ...> and </config>
        match = re.search(r'(<config[\s\S]*?</config>)', xml_content)
        if not match:
            return []
        xml_block = match.group(1)
        root = ET.fromstring(xml_block)
        # Find the <interfaces> element (namespace-agnostic)
        interfaces = None
        for elem in root.iter():
            if elem.tag.endswith('interfaces'):
                interfaces = elem
                break
        if interfaces is None:
            return []
        for iface in interfaces.findall('.//'):
            if iface.tag.endswith('interface'):
                # Check if this interface has LLDP neighbors
                name_elem = iface.find('.//')
                if name_elem is not None and name_elem.tag.endswith('name'):
                    local_interface = name_elem.text
                    if local_interface:
                        # Find LLDP neighbors
                        lldp_elem = iface.find('.//')
                        if lldp_elem is not None and lldp_elem.tag.endswith('lldp'):
                            for neighbor in lldp_elem.findall('.//'):
                                if neighbor.tag.endswith('neighbor'):
                                    neighbor_interface_elem = neighbor.find('.//')
                                    if neighbor_interface_elem is not None and neighbor_interface_elem.tag.endswith('interface'):
                                        neighbor_interface_name_elem = neighbor_interface_elem.find('.//')
                                        if neighbor_interface_name_elem is not None and neighbor_interface_name_elem.tag.endswith('name'):
                                            neighbor_interface = neighbor_interface_name_elem.text
                                            if neighbor_interface:
                                                neighbors.append({
                                                    'local_interface': local_interface,
                                                    'neighbor_interface': neighbor_interface
                                                })
        return neighbors
    except Exception as e:
        print(f"Error parsing LLDP XML: {e}")
        return []

def parse_lldp_cli(cli_output):
    """Parse LLDP neighbor data from CLI output."""
    neighbors = []
    
    # Split output into lines and look for neighbor entries
    lines = cli_output.split('\n')
    
    for line in lines:
        # Look for LLDP neighbor patterns
        # Example: "DNAAS-LEAF-B14    ge100-0/0/36    100.64.101.5    ge100-0/0/36"
        if 'ge' in line and ('100.64.' in line or 'DNAAS-' in line):
            parts = line.strip().split()
            if len(parts) >= 4:
                neighbor = {
                    'local_interface': parts[1],
                    'neighbor_device': parts[0],
                    'neighbor_interface': parts[3],
                    'neighbor_ip': parts[2] if len(parts) > 2 else 'unknown'
                }
                neighbors.append(neighbor)
    
    return neighbors

def parse_lacp_xml(xml_content):
    """Parse LACP XML to extract bundle and member information using ElementTree."""
    bundles = []
    try:
        # Extract only the XML block between <config ...> and </config>
        match = re.search(r'(<config[\s\S]*?</config>)', xml_content)
        if not match:
            return []
        xml_block = match.group(1)
        root = ET.fromstring(xml_block)
        
        # Define namespace mapping
        namespaces = {
            'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
            'dn-top': 'http://drivenets.com/ns/yang/dn-top',
            'dn-protocol': 'http://drivenets.com/ns/yang/dn-protocol',
            'dn-lacp': 'http://drivenets.com/ns/yang/dn-lacp'
        }
        
        # Find all interface elements that are bundles
        for interface in root.findall('.//dn-lacp:interface', namespaces):
            # Get bundle name
            name_elem = interface.find('dn-lacp:name', namespaces)
            if name_elem is not None and name_elem.text and 'bundle-' in name_elem.text:
                bundle_name = name_elem.text
                bundle = {
                    'name': bundle_name,
                    'members': []
                }
                
                # Find member interfaces
                members_elem = interface.find('dn-lacp:members', namespaces)
                if members_elem is not None:
                    for member in members_elem.findall('dn-lacp:member', namespaces):
                        interface_elem = member.find('dn-lacp:interface', namespaces)
                        if interface_elem is not None and interface_elem.text:
                            bundle['members'].append(interface_elem.text)
                
                bundles.append(bundle)
        
        return bundles
    except Exception as e:
        print(f"Error parsing LACP XML: {e}")
        return []

def parse_bridge_domain_instance(cli_output):
    """Parse Bridge Domain Instance CLI output."""
    bridge_domains = []
    
    try:
        lines = cli_output.split('\n')
        current_bridge_domain = None
        
        logger.info(f"Parsing bridge domain instance CLI output with {len(lines)} lines")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Strip ANSI color codes from the line
            line = strip_ansi_codes(line)
            
            # Debug: log every 10th line to see what we're processing
            if i % 10 == 0:
                logger.info(f"Processing line {i}: {line[:50]}...")
            
            # Debug: log lines that contain "bridge-domain" to see what we're getting
            if 'bridge-domain' in line:
                logger.info(f"DEBUG: Found line with 'bridge-domain': {line}")
                logger.info(f"DEBUG: Line length: {len(line)}")
                logger.info(f"DEBUG: Line repr: {repr(line)}")
                logger.info(f"DEBUG: Checking if 'network-services bridge-domain instance' in line: {'network-services bridge-domain instance' in line}")
            
            # Look for bridge domain instance lines
            # Example: network-services bridge-domain instance DLITVI_V1555_IX_IX interface ge100-0/0/21.1555 ^
            if 'network-services bridge-domain instance' in line:
                logger.info(f"FOUND BRIDGE DOMAIN LINE: {line}")
                # Extract bridge domain name from the line
                # The format is: network-services bridge-domain instance <NAME> <optional-attributes>
                parts = line.split('network-services bridge-domain instance')
                if len(parts) > 1:
                    bridge_domain_part = parts[1].strip()
                    # Extract the bridge domain name (first word after "instance")
                    bridge_domain_name = bridge_domain_part.split()[0]
                    
                    logger.info(f"Found bridge domain instance: {bridge_domain_name}")
                    
                    # Check if this bridge domain already exists
                    existing_bd = None
                    for bd in bridge_domains:
                        if bd['name'] == bridge_domain_name:
                            existing_bd = bd
                            break
                    
                    if existing_bd:
                        current_bridge_domain = existing_bd
                        logger.info(f"Using existing bridge domain: {bridge_domain_name}")
                    else:
                        current_bridge_domain = {
                            'name': bridge_domain_name,
                            'admin_state': 'enabled',  # Default to enabled
                            'interfaces': []
                        }
                        bridge_domains.append(current_bridge_domain)
                        logger.info(f"Created new bridge domain: {bridge_domain_name}")
                else:
                    logger.error(f"Could not parse bridge domain name from line: {line}")
                
                # Check for admin-state in the same line
                if 'admin-state enabled' in line:
                    current_bridge_domain['admin_state'] = 'enabled'
                elif 'admin-state disabled' in line:
                    current_bridge_domain['admin_state'] = 'disabled'
                
                # Check for interface in the same line
                if 'interface ' in line:
                    interface_match = re.search(r'interface ([^\s^]+)', line)
                    if interface_match:
                        interface_name = interface_match.group(1)
                        if interface_name not in current_bridge_domain['interfaces']:
                            current_bridge_domain['interfaces'].append(interface_name)
                            logger.info(f"Added interface {interface_name} to {current_bridge_domain['name']}")
            
            # Look for interface lines (separate lines)
            # Example: network-services bridge-domain instance DLITVI_V1555_IX_IX interface ge100-0/0/21.1556 ^
            elif 'interface ' in line and current_bridge_domain:
                interface_match = re.search(r'interface ([^\s^]+)', line)
                if interface_match:
                    interface_name = interface_match.group(1)
                    if interface_name not in current_bridge_domain['interfaces']:
                        current_bridge_domain['interfaces'].append(interface_name)
                        logger.info(f"Added interface {interface_name} to {current_bridge_domain['name']}")
            
            # Look for admin-state lines (separate lines)
            # Example: network-services bridge-domain instance DLITVI_V3180_IX_SL2_B51 admin-state enabled
            elif 'admin-state ' in line and current_bridge_domain:
                if 'admin-state enabled' in line:
                    current_bridge_domain['admin_state'] = 'enabled'
                elif 'admin-state disabled' in line:
                    current_bridge_domain['admin_state'] = 'disabled'
        
        logger.info(f"Final bridge domains found: {len(bridge_domains)}")
        for bd in bridge_domains:
            logger.info(f"  - {bd['name']}: {len(bd['interfaces'])} interfaces, admin_state: {bd['admin_state']}")
        
        return bridge_domains
        
    except Exception as e:
        logger.error(f"Error parsing bridge domain instance CLI: {e}")
        return []

def parse_vlan_configuration(cli_output):
    """Parse VLAN Configuration CLI output."""
    vlan_configs = []
    
    try:
        lines = cli_output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for VLAN ID configurations
            # Example: interfaces bundle-447.447 vlan-id 447
            vlan_id_match = re.search(r'interfaces ([^\s]+) vlan-id (\d+)', line)
            if vlan_id_match:
                interface_name = vlan_id_match.group(1)
                vlan_id = int(vlan_id_match.group(2))
                vlan_configs.append({
                    'interface': interface_name,
                    'vlan_id': vlan_id,
                    'type': 'subinterface'
                })
            
            # Look for VLAN manipulation configurations
            # Example: interfaces bundle-1204 vlan-manipulation egress-mapping action pop
            elif 'vlan-manipulation' in line:
                interface_match = re.search(r'interfaces ([^\s]+) vlan-manipulation', line)
                if interface_match:
                    interface_name = interface_match.group(1)
                    vlan_configs.append({
                        'interface': interface_name,
                        'type': 'manipulation',
                        'configuration': line.strip()
                    })
        
        return vlan_configs
    except Exception as e:
        logger.error(f"Error parsing VLAN configuration CLI: {e}")
        return []

def parse_raw_data():
    """Phase 2: Parse raw data and save structured results."""
    logger.info("=== PARSE PHASE ===")
    parse_start_time = time.time()
    
    raw_dir = Path('topology/configs/raw-config')
    parsed_dir = Path('topology/configs/parsed_data')
    parsed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all raw data files
    lacp_files = list(raw_dir.glob('*_lacp_raw_*.xml'))
    lldp_files = list(raw_dir.glob('*_lldp_raw_*.txt'))
    bridge_domain_instance_files = list(BRIDGE_DOMAIN_RAW_DIR.glob('*_bridge_domain_instance_raw_*.txt'))
    vlan_config_files = list(BRIDGE_DOMAIN_RAW_DIR.glob('*_vlan_config_raw_*.txt'))
    
    logger.info(f"Found {len(lacp_files)} LACP files, {len(lldp_files)} LLDP files, {len(bridge_domain_instance_files)} Bridge Domain Instance files, and {len(vlan_config_files)} VLAN Config files to parse")
    
    # Parse LACP files
    for lacp_file in lacp_files:
        try:
            device_name = lacp_file.name.split('_lacp_raw_')[0]
            
            with open(lacp_file, 'r') as f:
                xml_content = f.read()
            
            bundles = parse_lacp_xml(xml_content)
            
            if bundles:
                # Save parsed LACP data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_lacp_parsed_{timestamp}.yaml"
                filepath = parsed_dir / filename
                
                output_data = {
                    'device': device_name,
                    'timestamp': timestamp,
                    'bundles': bundles
                }
                
                with open(filepath, 'w') as f:
                    yaml.dump(output_data, f, default_flow_style=False, indent=2)
                
                logger.info(f"Parsed LACP for {device_name}: {len(bundles)} bundles")
                summary.add_parse_result(device_name, 'lacp', True, bundles_count=len(bundles))
            else:
                logger.warning(f"No LACP bundles found in {device_name}")
                summary.add_parse_result(device_name, 'lacp', False, error="No bundles found in XML")
                
        except Exception as e:
            logger.error(f"Error parsing LACP file {lacp_file}: {e}")
            summary.add_parse_result(device_name, 'lacp', False, error=f"Error parsing LACP XML: {e}")
    
    # Parse LLDP files
    for lldp_file in lldp_files:
        try:
            device_name = lldp_file.name.split('_lldp_raw_')[0]
            
            with open(lldp_file, 'r') as f:
                cli_output = f.read()
            
            neighbors = parse_lldp_cli(cli_output)
            
            if neighbors:
                # Save parsed LLDP data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_lldp_parsed_{timestamp}.yaml"
                filepath = parsed_dir / filename
                
                output_data = {
                    'device': device_name,
                    'timestamp': timestamp,
                    'neighbors': neighbors
                }
                
                with open(filepath, 'w') as f:
                    yaml.dump(output_data, f, default_flow_style=False, indent=2)
                
                logger.info(f"Parsed LLDP for {device_name}: {len(neighbors)} neighbors")
                summary.add_parse_result(device_name, 'lldp', True, neighbors_count=len(neighbors))
            else:
                logger.warning(f"No LLDP neighbors found in {device_name}")
                summary.add_parse_result(device_name, 'lldp', False, error="No neighbors found in CLI output")
                
        except Exception as e:
            logger.error(f"Error parsing LLDP file {lldp_file}: {e}")
            summary.add_parse_result(device_name, 'lldp', False, error=f"Error parsing LLDP CLI: {e}")
    
    # Parse Bridge Domain Instance files
    for bridge_domain_instance_file in bridge_domain_instance_files:
        try:
            device_name = bridge_domain_instance_file.name.split('_bridge_domain_instance_raw_')[0]
            
            with open(bridge_domain_instance_file, 'r') as f:
                cli_output = f.read()
            
            bridge_domains = parse_bridge_domain_instance(cli_output)
            
            if bridge_domains:
                # Save parsed Bridge Domain Instance data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_bridge_domain_instance_parsed_{timestamp}.yaml"
                filepath = BRIDGE_DOMAIN_PARSED_DIR / filename
                
                output_data = {
                    'device': device_name,
                    'timestamp': timestamp,
                    'bridge_domain_instances': bridge_domains
                }
                
                with open(filepath, 'w') as f:
                    yaml.dump(output_data, f, default_flow_style=False, indent=2)
                
                logger.info(f"Parsed Bridge Domain Instance for {device_name}: {len(bridge_domains)} bridge domains")
                summary.add_parse_result(device_name, 'bridge_domain', True, bridge_domains_count=len(bridge_domains))
            else:
                logger.warning(f"No Bridge Domain instances found in {device_name}")
                summary.add_parse_result(device_name, 'bridge_domain', False, error="No bridge domain instances found in CLI output")
                
        except Exception as e:
            logger.error(f"Error parsing Bridge Domain Instance file {bridge_domain_instance_file}: {e}")
            summary.add_parse_result(device_name, 'bridge_domain', False, error=f"Error parsing Bridge Domain Instance CLI: {e}")
    
    # Parse VLAN Config files
    for vlan_config_file in vlan_config_files:
        try:
            device_name = vlan_config_file.name.split('_vlan_config_raw_')[0]
            
            with open(vlan_config_file, 'r') as f:
                cli_output = f.read()
            
            vlan_configs = parse_vlan_configuration(cli_output)
            
            if vlan_configs:
                # Save parsed VLAN Config data
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_name}_vlan_config_parsed_{timestamp}.yaml"
                filepath = BRIDGE_DOMAIN_PARSED_DIR / filename
                
                output_data = {
                    'device': device_name,
                    'timestamp': timestamp,
                    'vlan_configurations': vlan_configs
                }
                
                with open(filepath, 'w') as f:
                    yaml.dump(output_data, f, default_flow_style=False, indent=2)
                
                logger.info(f"Parsed VLAN Config for {device_name}: {len(vlan_configs)} configurations")
            else:
                logger.warning(f"No VLAN configurations found in {device_name}")
                
        except Exception as e:
            logger.error(f"Error parsing VLAN Config file {vlan_config_file}: {e}")
    
    parse_total_time = time.time() - parse_start_time
    logger.info(f"Parse phase complete!")
    logger.info(f"LACP parsed: {summary.parse_lacp_successful} devices, {summary.total_bundles} total bundles")
    logger.info(f"LLDP parsed: {summary.parse_lldp_successful} devices, {summary.total_neighbors} total neighbors")
    logger.info(f"Bridge Domain parsed: {summary.parse_bridge_domain_successful} devices, {summary.total_bridge_domains} total bridge domains")
    logger.info(f"Total parse time: {parse_total_time:.2f} seconds")

def probe_phase():
    """Phase 1: Collect raw data from all devices."""
    import time
    script_start_time = time.time()
    
    logger.info("=== PHASE 1: PROBE - Collecting raw data ===")
    
    # Clear previous data
    clear_previous_data()
    
    devices = load_devices()
    if not devices:
        logger.error("No devices found in devices.yaml")
        return
    
    summary.total_devices = len(devices)
    logger.info(f"Found {len(devices)} devices")
    
    # Process all devices in parallel
    target_devices = list(devices.keys())
    
    # Filter out devices with invalid mgmt_ip
    available_devices = {}
    invalid_devices = []
    
    for device_name, device_config in devices.items():
        mgmt_ip = device_config.get('mgmt_ip', '')
        if mgmt_ip and mgmt_ip != 'TBD' and mgmt_ip != 'unknown':
            available_devices[device_name] = device_config
        else:
            invalid_devices.append(device_name)
            summary.add_invalid_device(device_name, f"Invalid mgmt_ip: {mgmt_ip}")
    
    summary.available_devices = len(available_devices)
    
    if invalid_devices:
        logger.warning(f"Skipping {len(invalid_devices)} devices with invalid mgmt_ip: {invalid_devices[:5]}{'...' if len(invalid_devices) > 5 else ''}")
    
    if not available_devices:
        logger.error("No valid devices found in devices.yaml")
        return
    
    logger.info(f"Probing {len(available_devices)} devices in parallel")
    
    # Use ThreadPoolExecutor for parallel processing
    max_workers = min(len(available_devices), 15)
    logger.info(f"Using {max_workers} parallel workers")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_device = {
            executor.submit(collect_raw_device_data, device_name, device_config): device_name
            for device_name, device_config in available_devices.items()
        }
        
        # Process completed tasks
        completed = 0
        total = len(available_devices)
        
        for future in as_completed(future_to_device):
            device_name = future_to_device[future]
            completed += 1
            
            try:
                lacp_success, lldp_success, bridge_domain_success = future.result()
                summary.add_device_result(device_name, lacp_success, lldp_success, bridge_domain_success)
                
                status = []
                if lacp_success:
                    status.append("LACP")
                if lldp_success:
                    status.append("LLDP")
                if bridge_domain_success:
                    status.append("Bridge Domain")
                if not status:
                    status.append("FAILED")
                
                logger.info(f"Progress: {completed}/{total} - {device_name}: {'+'.join(status)}")
                
            except Exception as e:
                logger.error(f"Progress: {completed}/{total} - {device_name}: EXCEPTION - {e}")
                summary.add_device_result(device_name, False, False, False, error=f"Exception: {e}")
            
            # Log progress every 10 devices
            if completed % 10 == 0 or completed == total:
                logger.info(f"Progress: {completed}/{total} devices processed (LACP: {summary.lacp_successful}, LLDP: {summary.lldp_successful}, Bridge Domain: {summary.bridge_domain_successful}, Failed: {len(summary.failed_devices)})")
    
    script_total_time = time.time() - script_start_time
    logger.info(f"=== PROBE PHASE COMPLETE ===")
    logger.info(f"LACP XML: {summary.lacp_successful} successful, {summary.lacp_failed} failed")
    logger.info(f"LLDP Neighbors: {summary.lldp_successful} successful")
    logger.info(f"Bridge Domain: {summary.bridge_domain_successful} successful")
    logger.info(f"Total probe time: {script_total_time:.2f} seconds")
    if summary.lacp_successful > 0:
        avg_time = script_total_time / summary.lacp_successful
        logger.info(f"Average time per successful device: {avg_time:.2f} seconds")
        logger.info(f"Processing rate: {summary.lacp_successful / script_total_time:.1f} devices per second")

def main():
    """Main function with probe and parse phases."""
    parser = argparse.ArgumentParser(description='Collect and parse device data')
    parser.add_argument('--phase', choices=['probe', 'parse', 'both'], default='both',
                       help='Which phase to run: probe (collect), parse (process), or both')
    
    args = parser.parse_args()
    
    if args.phase in ['probe', 'both']:
        probe_phase()
    
    if args.phase in ['parse', 'both']:
        parse_raw_data()
    
    # Print comprehensive summary
    summary.finish()
    summary.print_summary()
    
    logger.info("=== COMPLETE DEVICE DATA COLLECTION FINISHED ===")

if __name__ == "__main__":
    main()
