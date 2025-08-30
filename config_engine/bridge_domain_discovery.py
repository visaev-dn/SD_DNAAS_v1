#!/usr/bin/env python3
"""
Bridge Domain Discovery Engine

This module provides comprehensive bridge domain discovery and mapping capabilities.
It analyzes collected bridge domain data and creates structured mappings with confidence scoring.
"""

import os
import sys
import yaml
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.service_name_analyzer import ServiceNameAnalyzer

logger = logging.getLogger(__name__)

class BridgeDomainDiscovery:
    """
    Bridge Domain Discovery Engine
    
    Analyzes collected bridge domain data and creates comprehensive mappings
    with confidence scoring and pattern recognition.
    """
    
    def __init__(self):
        self.service_analyzer = ServiceNameAnalyzer()
        self.parsed_data_dir = Path('topology/configs/parsed_data')
        self.bridge_domain_parsed_dir = Path('topology/configs/parsed_data/bridge_domain_parsed')
        self.output_dir = Path('topology/bridge_domain_discovery')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def detect_device_type(self, device_name: str) -> str:
        """
        Detect device type based on device name.
        
        Args:
            device_name: Name of the device
            
        Returns:
            Device type: 'leaf', 'spine', 'superspine'
        """
        device_name_upper = device_name.upper()
        
        if 'SUPERSPINE' in device_name_upper:
            return 'superspine'
        elif 'SPINE' in device_name_upper:
            return 'spine'
        elif 'LEAF' in device_name_upper:
            return 'leaf'
        else:
            # Default to leaf if unknown
            return 'leaf'
    
    def extract_vlan_from_interface(self, interface_name: str) -> Optional[int]:
        """
        Extract VLAN ID from interface name.
        
        WARNING: This function should NOT be used to extract VLAN IDs from subinterface numbers
        as the subinterface number (e.g., bundle-3700.8101) is NOT the same as the VLAN ID.
        
        Args:
            interface_name: Interface name (e.g., 'bundle-60000.998', 'ge100-0/0/13.1360')
            
        Returns:
            VLAN ID if found, None otherwise
        """
        # Handle non-string inputs
        if not isinstance(interface_name, str):
            return None
        
        # ❌ REMOVED: Pattern for subinterface with VLAN: bundle-60000.998, ge100-0/0/13.1360
        # This was INCORRECT - subinterface numbers are NOT VLAN IDs
        # match = re.search(r'\.(\d+)$', interface_name)
        # if match:
        #     try:
        #         return int(match.group(1))
        #     except ValueError:
        #         pass
        
        # Pattern for VLAN in interface name: vlan123, vlan-123
        # This is still valid as these are explicitly named VLAN interfaces
        match = re.search(r'vlan[_-]?(\d+)', interface_name, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        
        # Return None for all other cases
        # VLAN IDs should be extracted from actual device configuration, not interface names
        return None
    
    def determine_interface_role(self, interface_name: str, device_type: str) -> str:
        """
        Determine interface role based on interface name and device type.
        
        Args:
            interface_name: Name of the interface
            device_type: Type of device (leaf, spine, superspine)
            
        Returns:
            Interface role: 'access', 'uplink', 'downlink'
        """
        interface_lower = interface_name.lower()
        
        # Bundle interfaces are typically uplinks
        if 'bundle-' in interface_lower:
            if device_type == 'leaf':
                return 'uplink'  # Leaf bundles go to spine
            elif device_type == 'spine':
                return 'downlink'  # Spine bundles go to leaf
            elif device_type == 'superspine':
                return 'downlink'  # Superspine bundles go to spine
        
        # Physical interfaces are typically access
        if 'ge' in interface_lower or 'et' in interface_lower:
            return 'access'
        
        # Default based on device type
        if device_type == 'leaf':
            return 'access'
        else:
            return 'uplink'
    
    def analyze_topology(self, devices: Dict[str, Dict]) -> Dict:
        """
        Analyze bridge domain topology based on total interfaces and access interfaces.
        
        Args:
            devices: Dictionary of devices and their interfaces
            
        Returns:
            Topology analysis information
        """
        leaf_devices = []
        spine_devices = []
        superspine_devices = []
        total_interfaces = 0
        access_interfaces = 0
        
        for device_name, device_info in devices.items():
            device_type = device_info.get('device_type', 'leaf')
            interfaces = device_info.get('interfaces', [])
            total_interfaces += len(interfaces)
            
            # Count actual access interfaces
            for interface in interfaces:
                if isinstance(interface, dict) and interface.get('role') == 'access':
                    access_interfaces += 1
            
            if device_type == 'leaf':
                leaf_devices.append(device_name)
            elif device_type == 'spine':
                spine_devices.append(device_name)
            elif device_type == 'superspine':
                superspine_devices.append(device_name)
        
        # Determine topology type based on Access Circuits (ACs) - actual access interfaces
        if access_interfaces == 2:
            topology_type = 'p2p'
        elif access_interfaces > 2:
            topology_type = 'p2mp'
        else:
            topology_type = 'unknown'
        
        # Determine path complexity
        if len(superspine_devices) > 0:
            path_complexity = '3-tier'
        elif len(spine_devices) > 0:
            path_complexity = '2-tier'
        else:
            path_complexity = 'local'
        
        # Estimate bandwidth (simplified)
        estimated_bandwidth = f"{total_interfaces * 10}G"  # Assume 10G per interface
        
        return {
            'topology_type': topology_type,
            'path_complexity': path_complexity,
            'leaf_devices': len(leaf_devices),
            'spine_devices': len(spine_devices),
            'superspine_devices': len(superspine_devices),
            'total_interfaces': total_interfaces,
            'access_interfaces': access_interfaces,
            'estimated_bandwidth': estimated_bandwidth
        }
    
    def load_parsed_data(self) -> Dict[str, Dict]:
        """
        Load all parsed bridge domain data from files.
        
        Returns:
            Dict mapping device names to their parsed data
        """
        parsed_data = {}
        
        # Load bridge domain instance data
        instance_files = list(self.bridge_domain_parsed_dir.glob('*_bridge_domain_instance_parsed_*.yaml'))
        for file_path in instance_files:
            try:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    device_name = data.get('device')
                    if device_name:
                        if device_name not in parsed_data:
                            parsed_data[device_name] = {}
                        parsed_data[device_name]['bridge_domain_instances'] = data.get('bridge_domain_instances', [])
            except Exception as e:
                logger.error(f"Error loading bridge domain instance file {file_path}: {e}")
        
        # Load VLAN configuration data
        vlan_files = list(self.bridge_domain_parsed_dir.glob('*_vlan_config_parsed_*.yaml'))
        for file_path in vlan_files:
            try:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    device_name = data.get('device')
                    if device_name:
                        if device_name not in parsed_data:
                            parsed_data[device_name] = {}
                        parsed_data[device_name]['vlan_configurations'] = data.get('vlan_configurations', [])
            except Exception as e:
                logger.error(f"Error loading VLAN config file {file_path}: {e}")
        
        return parsed_data
    
    def create_interface_vlan_mapping(self, device_name: str, vlan_configs: List[Dict]) -> Dict[str, Dict]:
        """
        Create interface to VLAN ID mapping for a device.
        
        Args:
            device_name: Name of the device
            vlan_configs: List of VLAN configurations
            
        Returns:
            Dict mapping interface names to VLAN information
        """
        interface_mapping = {}
        
        for config in vlan_configs:
            interface_name = config.get('interface')
            if not interface_name:
                continue
            
            if config.get('type') == 'subinterface':
                vlan_id = config.get('vlan_id')
                interface_mapping[interface_name] = {
                    'vlan_id': vlan_id,
                    'type': 'subinterface'
                }
            elif config.get('type') == 'manipulation':
                interface_mapping[interface_name] = {
                    'type': 'manipulation',
                    'configuration': config.get('configuration'),
                    'status': 'unsupported_template'
                }
        
        return interface_mapping
    
    def analyze_bridge_domains(self, parsed_data: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """
        Analyze bridge domains and create comprehensive mappings.
        
        Args:
            parsed_data: Parsed data from all devices
            
        Returns:
            Dict mapping device names to analyzed bridge domain data
        """
        analyzed_data = {}
        
        for device_name, device_data in parsed_data.items():
            bridge_domains = device_data.get('bridge_domain_instances', [])
            vlan_configs = device_data.get('vlan_configurations', [])
            
            # Create interface to VLAN mapping
            interface_vlan_mapping = self.create_interface_vlan_mapping(device_name, vlan_configs)
            
            # Analyze each bridge domain
            analyzed_bridge_domains = []
            for bridge_domain in bridge_domains:
                bridge_domain_name = bridge_domain.get('name')
                interfaces = bridge_domain.get('interfaces', [])
                
                # Analyze service name pattern
                service_analysis = self.service_analyzer.extract_service_info(bridge_domain_name)
                
                # Create detailed interface analysis
                analyzed_interfaces = []
                for interface in interfaces:
                    interface_info = {
                        'name': interface,
                        'type': 'physical' if '.' not in interface else 'subinterface',
                        'vlan_id': None
                    }
                    
                    # Map VLAN ID if it's a subinterface
                    if interface in interface_vlan_mapping:
                        vlan_info = interface_vlan_mapping[interface]
                        if vlan_info.get('type') == 'subinterface':
                            interface_info['vlan_id'] = vlan_info.get('vlan_id')
                    
                    analyzed_interfaces.append(interface_info)
                
                # Create analyzed bridge domain
                analyzed_bridge_domain = {
                    'service_name': bridge_domain_name,
                    'detected_username': service_analysis.get('username'),
                    'detected_vlan': service_analysis.get('vlan_id'),
                    'confidence': service_analysis.get('confidence', 0),
                    'detection_method': service_analysis.get('method', 'unknown'),
                    'scope': service_analysis.get('scope', 'unknown'),
                    'scope_description': self.service_analyzer.get_scope_description(service_analysis.get('scope', 'unknown')),
                    'interfaces': analyzed_interfaces,
                    'admin_state': bridge_domain.get('admin_state', 'unknown'),
                    'vlan_manipulation': None  # Will be populated if needed
                }
                
                analyzed_bridge_domains.append(analyzed_bridge_domain)
            
            analyzed_data[device_name] = {
                'bridge_domains': analyzed_bridge_domains,
                'vlan_manipulation_configs': [
                    config for config in vlan_configs 
                    if config.get('type') == 'manipulation'
                ]
            }
        
        return analyzed_data
    
    def consolidate_bridge_domains_by_vlan(self, bridge_domain_collections: Dict) -> Dict:
        """
        Consolidate bridge domains by VLAN ID and username to handle naming inconsistencies.
        
        Args:
            bridge_domain_collections: Dictionary of bridge domain collections by service name
            
        Returns:
            Consolidated bridge domains with consistent naming
        """
        # Group bridge domains by VLAN ID and username
        vlan_consolidation = defaultdict(lambda: {
            'bridge_domains': [],
            'devices': {},
            'consolidated_name': None,
            'detected_username': None,
            'detected_vlan': None,
            'confidence': 0,
            'detection_method': None,
            'scope': 'unknown',
            'scope_description': 'Unknown scope - unable to determine'
        })
        
        # First pass: group by VLAN ID and username
        for service_name, bridge_domain_data in bridge_domain_collections.items():
            if not bridge_domain_data['devices']:
                continue
            
            username = bridge_domain_data['detected_username']
            vlan_id = bridge_domain_data['detected_vlan']
            
            # Create a unique key for consolidation
            if vlan_id is not None and username is not None:
                consolidation_key = f"{username}_v{vlan_id}"
            elif vlan_id is not None:
                consolidation_key = f"unknown_user_v{vlan_id}"
            elif username is not None:
                consolidation_key = f"{username}_no_vlan"
            else:
                # No consolidation possible, keep as is
                continue
            
            vlan_consolidation[consolidation_key]['bridge_domains'].append({
                'service_name': service_name,
                'data': bridge_domain_data
            })
            
            # Merge device information
            for device_name, device_info in bridge_domain_data['devices'].items():
                vlan_consolidation[consolidation_key]['devices'][device_name] = device_info
            
            # Track the best confidence and method
            if bridge_domain_data['confidence'] > vlan_consolidation[consolidation_key]['confidence']:
                vlan_consolidation[consolidation_key]['confidence'] = bridge_domain_data['confidence']
                vlan_consolidation[consolidation_key]['detection_method'] = bridge_domain_data['detection_method']
                vlan_consolidation[consolidation_key]['scope'] = bridge_domain_data['scope']
                vlan_consolidation[consolidation_key]['scope_description'] = bridge_domain_data['scope_description']
            
            # Set username and VLAN ID
            vlan_consolidation[consolidation_key]['detected_username'] = username
            vlan_consolidation[consolidation_key]['detected_vlan'] = vlan_id
        
        # Second pass: create consolidated bridge domains
        consolidated_bridge_domains = {}
        
        for consolidation_key, consolidation_data in vlan_consolidation.items():
            if not consolidation_data['devices']:
                continue
            
            # Determine the best service name for the consolidated bridge domain
            bridge_domains = consolidation_data['bridge_domains']
            if len(bridge_domains) == 1:
                # Single bridge domain, use its name
                consolidated_name = bridge_domains[0]['service_name']
            else:
                # Multiple bridge domains, create a standardized name
                username = consolidation_data['detected_username']
                vlan_id = consolidation_data['detected_vlan']
                
                if vlan_id is not None:
                    # Use the standard format: g_username_vvlan
                    consolidated_name = f"g_{username}_v{vlan_id}"
                else:
                    # For local scope or no VLAN, use the first name
                    consolidated_name = bridge_domains[0]['service_name']
            
            # Create the consolidated bridge domain
            consolidated_bridge_domains[consolidated_name] = {
                'service_name': consolidated_name,
                'detected_username': consolidation_data['detected_username'],
                'detected_vlan': consolidation_data['detected_vlan'],
                'confidence': consolidation_data['confidence'],
                'detection_method': consolidation_data['detection_method'],
                'scope': consolidation_data['scope'],
                'scope_description': consolidation_data['scope_description'],
                'devices': consolidation_data['devices'],
                'consolidation_info': {
                    'original_names': [bd['service_name'] for bd in bridge_domains],
                    'consolidation_key': consolidation_key,
                    'consolidated_count': len(bridge_domains)
                }
            }
        
        return consolidated_bridge_domains
    
    def create_bridge_domain_mapping(self, parsed_data: Dict[str, Dict]) -> Dict:
        """
        Create comprehensive bridge domain mapping from parsed data.
        
        Args:
            parsed_data: Parsed data from all devices
            
        Returns:
            Complete bridge domain mapping
        """
        mapping = {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'devices_scanned': len(parsed_data),
                'bridge_domains_found': 0,
                'confidence_threshold': 70
            },
            'bridge_domains': {},
            'unmapped_configurations': [],
            'topology_summary': {
                'p2p_bridge_domains': 0,
                'p2mp_bridge_domains': 0,
                'unknown_topology': 0,
                'total_high_confidence': 0,
                'total_unmapped': 0
            }
        }
        
        # First, analyze all bridge domains to get proper VLAN configurations
        analyzed_data = self.analyze_bridge_domains(parsed_data)
        
        # Create consolidated bridge domain collections
        bridge_domain_collections = {}
        
        for device_name, device_data in analyzed_data.items():
            bridge_domains = device_data.get('bridge_domains', [])
            vlan_manipulation_configs = device_data.get('vlan_manipulation_configs', [])
            
            # Get device type
            device_type = 'leaf'  # Default to leaf
            if 'spine' in device_name.lower():
                device_type = 'spine'
            elif 'superspine' in device_name.lower():
                device_type = 'superspine'
            
            # Update discovery metadata
            mapping['discovery_metadata']['bridge_domains_found'] += len(bridge_domains)
            
            # Process bridge domains
            for bridge_domain in bridge_domains:
                service_name = bridge_domain['service_name']
                confidence = bridge_domain.get('confidence', 0)
                
                if confidence >= 70:
                    # High confidence - consolidate by service name
                    if service_name not in bridge_domain_collections:
                        bridge_domain_collections[service_name] = {
                            'devices': {},
                            'high_confidence': len([
                                bd for bd in bridge_domains 
                                if bd.get('confidence', 0) >= 70
                            ]),
                            'device_type': device_type,
                            'vlan_manipulation_configs': len(vlan_manipulation_configs)
                        }
                    
                    bridge_domain_collections[service_name].update({
                        'service_name': service_name,
                        'detected_username': bridge_domain['detected_username'],
                        'detected_vlan': bridge_domain['detected_vlan'],
                        'confidence': confidence,
                        'detection_method': bridge_domain['detection_method'],
                        'scope': bridge_domain.get('scope', 'unknown'),
                        'scope_description': bridge_domain.get('scope_description', 'Unknown scope - unable to determine')
                    })
                    
                    # Add device information with CORRECT VLAN IDs from analyzed data
                    device_info = {
                        'interfaces': [],
                        'admin_state': bridge_domain['admin_state'],
                        'device_type': device_type
                    }
                    
                    # Process interfaces using the CORRECT VLAN configurations from analyze_bridge_domains
                    for interface in bridge_domain['interfaces']:
                        # Handle both string and dict interface formats
                        if isinstance(interface, dict):
                            interface_name = interface.get('name', '')
                            # Use the VLAN ID that was already analyzed and corrected
                            vlan_id = interface.get('vlan_id')
                        else:
                            interface_name = str(interface)
                            # For string interfaces, we need to look up the VLAN ID
                            # This should be rare since analyze_bridge_domains should handle most cases
                            vlan_id = None
                        
                        role = self.determine_interface_role(interface_name, device_type)
                        
                        device_info['interfaces'].append({
                            'name': interface_name,
                            'type': 'subinterface' if '.' in interface_name else 'physical',
                            'vlan_id': vlan_id,  # ✅ Use the CORRECT VLAN ID from analyzed data
                            'role': role
                        })
                    
                    bridge_domain_collections[service_name]['devices'][device_name] = device_info
                else:
                    # Low confidence - add to unmapped
                    mapping['unmapped_configurations'].append({
                        'service_name': service_name,
                        'vlan_id': bridge_domain['detected_vlan'],
                        'devices': [device_name],
                        'confidence': confidence,
                        'scope': bridge_domain.get('scope', 'unknown'),
                        'scope_description': bridge_domain.get('scope_description', 'Unknown scope - unable to determine'),
                        'reason': 'low_confidence_pattern'
                    })
            
            # Add VLAN manipulation configs
            for vlan_config in vlan_manipulation_configs:
                mapping['unmapped_configurations'].append({
                    'service_name': f"vlan_manipulation_{vlan_config['interface']}",
                    'vlan_id': None,
                    'devices': [device_name],
                    'confidence': 0,
                    'reason': 'unsupported_template',
                    'configuration': vlan_config.get('configuration')
                })
        
        # Consolidate bridge domains by VLAN ID and username
        consolidated_bridge_domains = self.consolidate_bridge_domains_by_vlan(bridge_domain_collections)
        
        # Process consolidated bridge domains
        for consolidated_name, consolidated_data in consolidated_bridge_domains.items():
            # Analyze topology
            topology_analysis = self.analyze_topology(consolidated_data['devices'])
            
            # Create the bridge domain entry
            mapping['bridge_domains'][consolidated_name] = {
                'service_name': consolidated_name,
                'detected_username': consolidated_data['detected_username'],
                'detected_vlan': consolidated_data['detected_vlan'],
                'confidence': consolidated_data['confidence'],
                'detection_method': consolidated_data['detection_method'],
                'scope': consolidated_data['scope'],
                'scope_description': consolidated_data['scope_description'],
                'topology_type': topology_analysis['topology_type'],
                'devices': consolidated_data['devices'],
                'topology_analysis': topology_analysis,
                'consolidation_info': consolidated_data['consolidation_info']
            }
            
            # Update topology summary
            topology_type = topology_analysis['topology_type']
            if topology_type == 'p2p':
                mapping['topology_summary']['p2p_bridge_domains'] += 1
            elif topology_type == 'p2mp':
                mapping['topology_summary']['p2mp_bridge_domains'] += 1
            else:
                mapping['topology_summary']['unknown_topology'] += 1
        
        # Update summary counts
        mapping['topology_summary']['total_high_confidence'] = len(mapping['bridge_domains'])
        mapping['topology_summary']['total_unmapped'] = len(mapping['unmapped_configurations'])
        
        return mapping
    
    def save_mapping(self, mapping: Dict, filename: str = None) -> str:
        """
        Save the bridge domain mapping to a JSON file.
        
        Args:
            mapping: The mapping data to save
            filename: Optional filename, will generate one if not provided
            
        Returns:
            Path to the saved file
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bridge_domain_mapping_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(mapping, f, indent=2, default=str)
        
        logger.info(f"Bridge domain mapping saved to: {filepath}")
        return str(filepath)
    
    def generate_summary_report(self, mapping: Dict) -> str:
        """
        Generate a human-readable summary report of the bridge domain discovery.
        
        Args:
            mapping: The bridge domain mapping data
            
        Returns:
            Formatted summary report string
        """
        report = []
        
        metadata = mapping.get('discovery_metadata', {})
        bridge_domains = mapping.get('bridge_domains', {})
        unmapped = mapping.get('unmapped_configurations', [])
        topology_summary = mapping.get('topology_summary', {})
        
        report.append("🔍 BRIDGE DOMAIN DISCOVERY SUMMARY")
        report.append("=" * 50)
        report.append(f"📅 Discovery Time: {metadata.get('timestamp', 'Unknown')}")
        report.append(f"📊 Devices Scanned: {metadata.get('devices_scanned', 0)}")
        report.append(f"🏷️  Bridge Domains Found: {metadata.get('bridge_domains_found', 0)}")
        report.append(f"🎯 Confidence Threshold: {metadata.get('confidence_threshold', 70)}%")
        report.append("")
        
        # Topology Summary
        report.append("🌐 TOPOLOGY ANALYSIS:")
        report.append(f"   • P2P Bridge Domains: {topology_summary.get('p2p_bridge_domains', 0)}")
        report.append(f"   • P2MP Bridge Domains: {topology_summary.get('p2mp_bridge_domains', 0)}")
        report.append(f"   • Unknown Topology: {topology_summary.get('unknown_topology', 0)}")
        report.append(f"   • High Confidence: {topology_summary.get('total_high_confidence', 0)}")
        report.append(f"   • Unmapped Configurations: {topology_summary.get('total_unmapped', 0)}")
        report.append("")
        
        # High confidence bridge domains with topology info
        if bridge_domains:
            report.append("✅ HIGH CONFIDENCE BRIDGE DOMAINS:")
            for service_name, bd in bridge_domains.items():
                topology_type = bd.get('topology_type', 'unknown')
                topology_analysis = bd.get('topology_analysis', {})
                path_complexity = topology_analysis.get('path_complexity', 'unknown')
                
                # Check if this was a consolidated bridge domain
                consolidation_info = bd.get('consolidation_info', {})
                if consolidation_info.get('consolidated_count', 1) > 1:
                    original_names = consolidation_info.get('original_names', [])
                    report.append(f"   • {service_name} (VLAN: {bd['detected_vlan']}, User: {bd['detected_username']}, Confidence: {bd['confidence']}%)")
                    report.append(f"     - CONSOLIDATED from {consolidation_info['consolidated_count']} bridge domains:")
                    for orig_name in original_names:
                        report.append(f"       * {orig_name}")
                    report.append(f"     - Topology: {topology_type.upper()}, Path: {path_complexity}")
                    report.append(f"     - Devices: {len(bd['devices'])} total ({topology_analysis.get('leaf_devices', 0)} leaf, {topology_analysis.get('spine_devices', 0)} spine)")
                else:
                    report.append(f"   • {service_name} (VLAN: {bd['detected_vlan']}, User: {bd['detected_username']}, Confidence: {bd['confidence']}%)")
                    report.append(f"     - Topology: {topology_type.upper()}, Path: {path_complexity}")
                    report.append(f"     - Devices: {len(bd['devices'])} total ({topology_analysis.get('leaf_devices', 0)} leaf, {topology_analysis.get('spine_devices', 0)} spine)")
                
                for device, device_info in bd['devices'].items():
                    interfaces = device_info.get('interfaces', [])
                    interface_names = [iface.get('name', '') for iface in interfaces]
                    report.append(f"     - {device}: {', '.join(interface_names)}")
            report.append("")
        
        # Consolidation statistics
        consolidated_count = 0
        total_original_names = 0
        for bd in bridge_domains.values():
            consolidation_info = bd.get('consolidation_info', {})
            if consolidation_info.get('consolidated_count', 1) > 1:
                consolidated_count += 1
                total_original_names += consolidation_info['consolidated_count']
        
        if consolidated_count > 0:
            report.append("🔗 CONSOLIDATION SUMMARY:")
            report.append(f"   • {consolidated_count} bridge domains were consolidated")
            report.append(f"   • {total_original_names} original bridge domain names were merged")
            report.append(f"   • Consolidation was based on VLAN ID and username matching")
            report.append("")
        
        # Unmapped configurations
        if unmapped:
            report.append("⚠️  UNMAPPED CONFIGURATIONS:")
            for config in unmapped[:20]:  # Show first 20
                report.append(f"   • {config['service_name']} (Confidence: {config['confidence']}%, Reason: {config['reason']})")
            if len(unmapped) > 20:
                report.append(f"   ... and {len(unmapped) - 20} more")
            report.append("")
        
        # Device summaries
        report.append("📊 DEVICE SUMMARIES:")
        for device, summary in mapping.get('device_summary', {}).items():
            device_type = summary.get('device_type', 'unknown')
            report.append(f"   • {device}: {summary['total_bridge_domains']} bridge domains, {summary['high_confidence']} high confidence ({device_type})")
        
        return "\n".join(report)
    
    def run_discovery(self) -> Dict:
        """
        Run the complete bridge domain discovery process.
        
        Returns:
            The comprehensive bridge domain mapping
        """
        logger.info("Starting Bridge Domain Discovery...")
        
        # Load parsed data
        logger.info("Loading parsed bridge domain data...")
        parsed_data = self.load_parsed_data()
        logger.info(f"Loaded data from {len(parsed_data)} devices")
        
        # Create comprehensive mapping
        logger.info("Creating comprehensive mapping...")
        mapping = self.create_bridge_domain_mapping(parsed_data)
        
        # Save mapping
        logger.info("Saving bridge domain mapping...")
        self.save_mapping(mapping)
        
        # Generate and save summary report
        logger.info("Generating summary report...")
        summary_report = self.generate_summary_report(mapping)
        summary_file = self.output_dir / f"bridge_domain_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w') as f:
            f.write(summary_report)
        
        logger.info("Bridge Domain Discovery complete!")
        return mapping

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run discovery
    discovery = BridgeDomainDiscovery()
    mapping = discovery.run_discovery()
    
    # Print summary
    print(discovery.generate_summary_report(mapping)) 