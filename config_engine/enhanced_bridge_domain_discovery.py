#!/usr/bin/env python3
"""
Enhanced Bridge Domain Discovery System

This module provides advanced bridge domain discovery with full support for:
- Double-tag scenarios (QinQ)
- VLAN manipulation configurations
- Complex interface role assignments
- Enhanced topology classification
- RFC-compliant VLAN validation
"""

import os
import sys
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.enhanced_discovery_integration.auto_population_service import EnhancedDatabasePopulationService
from config_engine.phase1_data_structures.enums import (
    BridgeDomainType, TopologyType, InterfaceRole, DeviceRole, 
    InterfaceType, ValidationStatus, DeviceType
)
from config_engine.service_name_analyzer import ServiceNameAnalyzer
from config_engine.bridge_domain_classifier import BridgeDomainClassifier

logger = logging.getLogger(__name__)

class EnhancedBridgeDomainDiscovery:
    """
    Enhanced Bridge Domain Discovery Engine
    
    Provides comprehensive bridge domain discovery with full support for:
    - Double-tag scenarios (QinQ)
    - VLAN manipulation configurations
    - Complex interface role assignments
    - Enhanced topology classification
    - RFC-compliant VLAN validation
    """
    
    def __init__(self):
        self.service_analyzer = ServiceNameAnalyzer()
        self.auto_population_service = EnhancedDatabasePopulationService(None)
        self.bridge_domain_classifier = BridgeDomainClassifier()
        self.parsed_data_dir = Path('topology/configs/parsed_data')
        
        # Performance optimization: Cache for VLAN configurations
        self._vlan_config_cache = {}
        self.bridge_domain_parsed_dir = Path('topology/configs/parsed_data/bridge_domain_parsed')
        self.output_dir = Path('topology/enhanced_bridge_domain_discovery')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_parsed_data(self) -> Dict[str, Any]:
        """
        Load parsed bridge domain data with enhanced VLAN configurations.
        
        Returns:
            Dictionary of device data with bridge domain instances and VLAN configs
        """
        parsed_data = {}
        
        # Load bridge domain instance data
        for instance_file in self.bridge_domain_parsed_dir.glob('*_bridge_domain_instance_parsed_*.yaml'):
            try:
                device_name = instance_file.name.split('_bridge_domain_instance_parsed_')[0]
                
                with open(instance_file, 'r') as f:
                    data = yaml.safe_load(f)
                    bridge_domain_instances = data.get('bridge_domain_instances', [])
                
                # Create enhanced VLAN configurations for this device
                enhanced_vlan_configs = self._create_enhanced_vlan_configs(device_name, bridge_domain_instances)
                
                parsed_data[device_name] = {
                    'bridge_domain_instances': bridge_domain_instances,
                    'enhanced_vlan_configurations': enhanced_vlan_configs,
                    'device_type': self._detect_device_type(device_name)
                }
                
                logger.info(f"Loaded {device_name}: {len(bridge_domain_instances)} bridge domains, {len(enhanced_vlan_configs)} enhanced VLAN configs")
                
            except Exception as e:
                logger.error(f"Error loading {instance_file}: {e}")
        
        return parsed_data
    
    def _create_enhanced_vlan_configs(self, device_name: str, bridge_domain_instances: List[Dict]) -> List[Dict]:
        """
        Load real VLAN configurations from parsed data files.
        
        Args:
            device_name: Name of the device
            bridge_domain_instances: List of bridge domain instances
            
        Returns:
            List of enhanced VLAN configurations
        """
        # First try to load real VLAN configurations
        real_configs = self._load_real_vlan_configs(device_name)
        if real_configs:
            print(f"Loaded {len(real_configs)} real VLAN configurations for {device_name}")
            return real_configs
        
        # Fallback to mock configurations if no real data available
        print(f"No real VLAN configs found for {device_name}, using fallback configurations")
        return self._create_fallback_vlan_configs(device_name, bridge_domain_instances)
    
    def _aggregate_vlan_configs(self, vlan_configs: List[Dict]) -> Dict:
        """
        Aggregate multiple VLAN configuration entries for the same interface.
        
        Args:
            vlan_configs: List of VLAN configuration dictionaries for the same interface
            
        Returns:
            Aggregated VLAN configuration dictionary
        """
        if not vlan_configs:
            return {}
        
        if len(vlan_configs) == 1:
            return vlan_configs[0]
        
        # Start with the first config as base
        aggregated = vlan_configs[0].copy()
        
        # Merge data from additional configs
        for config in vlan_configs[1:]:
            # Take non-null values, prioritizing non-null over null
            for key in ['vlan_id', 'outer_vlan', 'inner_vlan', 'vlan_range', 'vlan_list']:
                config_value = config.get(key)
                current_value = aggregated.get(key)
                
                # Prioritize non-null values
                if config_value is not None and current_value is None:
                    aggregated[key] = config_value
                # For vlan_list, merge lists
                elif key == 'vlan_list' and isinstance(config_value, list) and isinstance(current_value, list):
                    aggregated[key] = list(set(current_value + config_value))  # Remove duplicates
            
            # Merge vlan_manipulation dictionaries
            if config.get('vlan_manipulation') and aggregated.get('vlan_manipulation'):
                aggregated['vlan_manipulation'].update(config['vlan_manipulation'])
            elif config.get('vlan_manipulation'):
                aggregated['vlan_manipulation'] = config['vlan_manipulation']
            
            # Combine raw_config lists
            if config.get('raw_config'):
                if aggregated.get('raw_config'):
                    aggregated['raw_config'].extend(config['raw_config'])
                else:
                    aggregated['raw_config'] = config['raw_config']
        
        # Post-processing: Set primary VLAN ID if not explicitly set
        if aggregated.get('vlan_id') is None:
            # Try to derive from other VLAN sources
            if aggregated.get('inner_vlan'):
                aggregated['vlan_id'] = aggregated['inner_vlan']  # Inner VLAN is typically primary for QinQ
            elif aggregated.get('vlan_list') and len(aggregated['vlan_list']) > 0:
                aggregated['vlan_id'] = aggregated['vlan_list'][0]  # First VLAN in list
            elif aggregated.get('vlan_range'):
                # Extract first VLAN from range (e.g., "2000-2050" -> 2000)
                try:
                    if '-' in str(aggregated['vlan_range']):
                        start_vlan = int(aggregated['vlan_range'].split('-')[0])
                        aggregated['vlan_id'] = start_vlan
                except (ValueError, IndexError):
                    pass
        
        return aggregated
    
    def _load_real_vlan_configs(self, device_name: str) -> List[Dict]:
        """
        Load real VLAN configurations from parsed data files with caching.
        """
        # Check cache first
        if device_name in self._vlan_config_cache:
            return self._vlan_config_cache[device_name]
            
        try:
            # Look for the most recent VLAN config file for this device
            vlan_config_dir = Path('topology/configs/parsed_data/bridge_domain_parsed')
            if not vlan_config_dir.exists():
                self._vlan_config_cache[device_name] = []
                return []
            
            # Find files matching the device name
            vlan_files = list(vlan_config_dir.glob(f'{device_name}_vlan_config_parsed_*.yaml'))
            if not vlan_files:
                self._vlan_config_cache[device_name] = []
                return []
            
            # Get the most recent file
            latest_file = max(vlan_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                vlan_data = yaml.safe_load(f)
            
            vlan_configs = vlan_data.get('vlan_configurations', [])
            
            # Cache the result
            self._vlan_config_cache[device_name] = vlan_configs
            return vlan_configs
            
        except Exception as e:
            print(f"Failed to load real VLAN configs for {device_name}: {e}")
            return []
    
    def _create_fallback_vlan_configs(self, device_name: str, bridge_domain_instances: List[Dict]) -> List[Dict]:
        """
        Create fallback VLAN configurations when real data is not available.
        """
        enhanced_configs = []
        
        # Create realistic VLAN configurations based on device type and bridge domain patterns
        if 'TATA' in str(bridge_domain_instances) or 'LEAF' in device_name:
            # TATA devices typically use QinQ configurations
            for i, bd in enumerate(bridge_domain_instances):
                interfaces = bd.get('interfaces', [])
                
                for j, iface in enumerate(interfaces):
                    # Create realistic QinQ VLAN configurations
                    if 'bundle' in iface:
                        # Bundle interfaces often have outer tags
                        outer_vlan = 100 + (i * 10) + (j * 5)
                        inner_vlan = 200 + (i * 10) + (j * 5)
                        
                        enhanced_configs.append({
                            'interface': iface,
                            'vlan_id': inner_vlan,  # Primary VLAN ID
                            'outer_vlan': outer_vlan,
                            'inner_vlan': inner_vlan,
                            'type': 'qinq_subinterface',
                            'vlan_manipulation': {
                                'ingress': 'push outer-tag',
                                'egress': 'pop outer-tag'
                            },
                            'bridge_domain': bd.get('name', 'unknown')
                        })
                    else:
                        # Regular interfaces
                        vlan_id = 300 + (i * 10) + (j * 5)
                        enhanced_configs.append({
                            'interface': iface,
                            'vlan_id': vlan_id,
                            'type': 'subinterface',
                            'bridge_domain': bd.get('name', 'unknown')
                        })
        else:
            # Non-TATA devices use simpler configurations
            for i, bd in enumerate(bridge_domain_instances):
                interfaces = bd.get('interfaces', [])
                
                for j, iface in enumerate(interfaces):
                    vlan_id = 1000 + (i * 100) + (j * 10)
                    enhanced_configs.append({
                        'interface': iface,
                        'vlan_id': vlan_id,
                        'type': 'subinterface',
                        'bridge_domain': bd.get('name', 'unknown')
                    })
        
        return enhanced_configs
    
    def _detect_device_type(self, device_name: str) -> str:
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
            return 'leaf'
    
    def create_enhanced_bridge_domain_mapping(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create enhanced bridge domain mapping with full QinQ support.
        
        Args:
            parsed_data: Parsed data from devices
            
        Returns:
            Enhanced bridge domain mapping
        """
        enhanced_mapping = {
            'discovery_metadata': {
                'discovery_type': 'enhanced_with_qinq_support',
                'timestamp': datetime.now().isoformat(),
                'devices_scanned': len(parsed_data),
                'enhanced_features': [
                    'double-tag_scenarios',
                    'qinq_detection',
                    'vlan_manipulation',
                    'interface_role_assignment',
                    'rfc_compliant_validation'
                ]
            },
            'bridge_domains': {},
            'enhanced_topology_analysis': {},
            'qinq_detection_summary': {
                'total_qinq_bds': 0,
                'edge_imposition': 0,
                'leaf_imposition': 0,
                'mixed_configurations': 0
            },
            'vlan_validation_summary': {
                'rfc_compliant': 0,
                'rfc_violations': 0,
                'validation_errors': []
            }
        }
        
        # Process each device's bridge domains
        for device_name, device_data in parsed_data.items():
            bridge_domain_instances = device_data.get('bridge_domain_instances', [])
            enhanced_vlan_configs = device_data.get('enhanced_vlan_configurations', [])
            
            for bd_instance in bridge_domain_instances:
                bd_name = bd_instance.get('name', 'unknown')
                
                # Create enhanced bridge domain entry
                enhanced_bd = self._create_enhanced_bridge_domain(
                    bd_name, bd_instance, enhanced_vlan_configs, device_name
                )
                
                if enhanced_bd:
                    enhanced_mapping['bridge_domains'][bd_name] = enhanced_bd
                    
                    # Update QinQ detection summary
                    if enhanced_bd.get('bridge_domain_type') == BridgeDomainType.QINQ:
                        enhanced_mapping['qinq_detection_summary']['total_qinq_bds'] += 1
                        
                        # Count imposition types
                        imposition_type = enhanced_bd.get('qinq_config', {}).get('imposition_type')
                        if imposition_type == 'edge':
                            enhanced_mapping['qinq_detection_summary']['edge_imposition'] += 1
                        elif imposition_type == 'leaf':
                            enhanced_mapping['qinq_detection_summary']['leaf_imposition'] += 1
                        else:
                            enhanced_mapping['qinq_detection_summary']['mixed_configurations'] += 1
                    
                    # Update VLAN validation summary
                    vlan_validation = enhanced_bd.get('vlan_validation', {})
                    if vlan_validation.get('rfc_compliant', False):
                        enhanced_mapping['vlan_validation_summary']['rfc_compliant'] += 1
                    else:
                        enhanced_mapping['vlan_validation_summary']['rfc_violations'] += 1
                        
                        # Collect validation errors
                        if 'validation_errors' in vlan_validation:
                            enhanced_mapping['vlan_validation_summary']['validation_errors'].extend(
                                vlan_validation['validation_errors']
                            )
        
        # Generate enhanced topology analysis
        enhanced_mapping['enhanced_topology_analysis'] = self._analyze_enhanced_topologies(
            enhanced_mapping['bridge_domains']
        )
        
        return enhanced_mapping
    
    def _create_enhanced_bridge_domain(self, bd_name: str, bd_instance: Dict, 
                                     enhanced_vlan_configs: List[Dict], device_name: str) -> Optional[Dict]:
        """
        Create an enhanced bridge domain entry with full QinQ support.
        
        Args:
            bd_name: Bridge domain name
            bd_instance: Bridge domain instance data
            enhanced_vlan_configs: Enhanced VLAN configurations
            device_name: Device name
            
        Returns:
            Enhanced bridge domain entry or None if invalid
        """
        try:
            interfaces = bd_instance.get('interfaces', [])
            
            # Create interface-to-VLAN mapping from enhanced VLAN configurations
            # Note: Multiple VLAN config entries may exist for the same interface
            interface_vlan_mapping = {}
            for config in enhanced_vlan_configs:
                interface_name = config.get('interface')
                if interface_name:
                    if interface_name not in interface_vlan_mapping:
                        interface_vlan_mapping[interface_name] = []
                    interface_vlan_mapping[interface_name].append(config)
            
            # Create enhanced interfaces with proper VLAN assignments
            enhanced_interfaces = []
            for iface in interfaces:
                # Find matching VLAN configs by interface name (may be multiple)
                vlan_configs = interface_vlan_mapping.get(iface, [])
                
                if vlan_configs:
                    # Aggregate VLAN configuration data from multiple entries
                    aggregated_config = self._aggregate_vlan_configs(vlan_configs)
                    
                    enhanced_interface = {
                        'name': iface,
                        'device_name': device_name,
                        'vlan_id': aggregated_config.get('vlan_id'),
                        'outer_vlan': aggregated_config.get('outer_vlan'),
                        'inner_vlan': aggregated_config.get('inner_vlan'),
                        'vlan_range': aggregated_config.get('vlan_range'),
                        'vlan_list': aggregated_config.get('vlan_list'),
                        'type': InterfaceType.SUBINTERFACE if '.' in iface else InterfaceType.PHYSICAL,
                        'vlan_manipulation': aggregated_config.get('vlan_manipulation'),
                        'original_configs': vlan_configs
                    }
                else:
                    # Fallback for interfaces without VLAN config
                    enhanced_interface = {
                        'name': iface,
                        'device_name': device_name,
                        'vlan_id': None,
                        'type': InterfaceType.SUBINTERFACE if '.' in iface else InterfaceType.PHYSICAL
                    }
                
                enhanced_interfaces.append(enhanced_interface)
            
            # Detect bridge domain type using systematic classifier
            try:
                bd_type, confidence_score, classification_analysis = self.bridge_domain_classifier.classify_bridge_domain(
                    bd_name, enhanced_interfaces
                )
                logger.debug(f"Classified {bd_name} as {bd_type} with {confidence_score}% confidence")
            except Exception as e:
                logger.warning(f"Failed to classify bridge domain {bd_name}: {e}")
                bd_type = BridgeDomainType.SINGLE_VLAN  # Default fallback
                confidence_score = 30
                classification_analysis = {"error": str(e)}
            
            # Extract VLAN configuration
            try:
                vlan_config = self.auto_population_service.extract_vlan_configuration(enhanced_interfaces, bd_type, bd_name)
            except Exception as e:
                logger.warning(f"Failed to extract VLAN configuration for {bd_name}: {e}")
                vlan_config = {'vlan_id': None, 'error': str(e)}
            
            # Detect QinQ topology
            try:
                topology_type = self.auto_population_service.detect_qinq_topology(enhanced_interfaces)
            except Exception as e:
                logger.warning(f"Failed to detect QinQ topology for {bd_name}: {e}")
                topology_type = TopologyType.P2P  # Default fallback
            
            # Assign interface roles
            try:
                enhanced_interfaces_with_roles = self.auto_population_service.assign_qinq_interface_roles(
                    enhanced_interfaces, bd_type
                )
            except Exception as e:
                logger.warning(f"Failed to assign interface roles for {bd_name}: {e}")
                # Fallback: assign basic roles
                enhanced_interfaces_with_roles = []
                for iface in enhanced_interfaces:
                    iface_copy = iface.copy()
                    iface_copy['assigned_role'] = InterfaceRole.ACCESS
                    enhanced_interfaces_with_roles.append(iface_copy)
            
            # Create QinQ configuration if applicable
            qinq_config = None
            if bd_type == BridgeDomainType.QINQ:
                try:
                    qinq_config = self._create_qinq_configuration(enhanced_interfaces, vlan_config)
                    
                    # Check for QinQ configuration errors (don't mask with fallbacks)
                    if qinq_config.get('error'):
                        logger.error(f"QinQ configuration failed for {bd_name}: {qinq_config.get('error_details')}")
                        logger.error("This indicates VLAN parsing issues that need to be fixed")
                        # Keep as QinQ but mark the error for investigation
                        qinq_config['needs_investigation'] = True
                    
                    # Check for suspicious outer=inner (indicates parsing failure, not legitimate single VLAN)
                    outer_vlan = qinq_config.get('outer_vlan')
                    inner_vlan = qinq_config.get('inner_vlan')
                    
                    if (outer_vlan and inner_vlan and outer_vlan == inner_vlan):
                        logger.error(f"VLAN parsing failure detected for {bd_name}: outer=inner ({outer_vlan})")
                        logger.error("This should be investigated - likely indicates regex pattern issues")
                        qinq_config['parsing_failure'] = True
                        qinq_config['needs_investigation'] = True
                    
                    # QinQ configuration created successfully
                except Exception as e:
                    logger.warning(f"Failed to create QinQ configuration for {bd_name}: {e}")
                    qinq_config = {'type': 'qinq', 'error': str(e)}
            
            # Validate VLAN configuration
            try:
                vlan_validation = self._validate_vlan_configuration(vlan_config, bd_type)
            except Exception as e:
                logger.warning(f"Failed to validate VLAN configuration for {bd_name}: {e}")
                vlan_validation = {'rfc_compliant': False, 'validation_errors': [str(e)]}
            
            # Create enhanced bridge domain entry
            enhanced_bd = {
                'name': bd_name,
                'bridge_domain_type': bd_type,
                'topology_type': topology_type,
                'devices': {
                    device_name: {
                        'interfaces': enhanced_interfaces_with_roles,
                        'device_type': self._detect_device_type(device_name),
                        'role': DeviceType.LEAF if 'LEAF' in device_name else DeviceType.SPINE
                    }
                },
                'vlan_configuration': vlan_config,
                'qinq_configuration': qinq_config,
                'vlan_validation': vlan_validation,
                'interface_roles': {
                    iface['name']: iface.get('assigned_role', InterfaceRole.ACCESS)
                    for iface in enhanced_interfaces_with_roles
                },
                'confidence_score': confidence_score,  # From systematic classifier
                'classification_analysis': classification_analysis,  # Detailed analysis from classifier
                'discovery_timestamp': datetime.now().isoformat(),
                'enhanced_features': {
                    'qinq_detected': bd_type == BridgeDomainType.QINQ,
                    'double_tag_support': True,
                    'vlan_manipulation_support': True,
                    'interface_role_assignment': True
                }
            }
            
            return enhanced_bd
            
        except Exception as e:
            logger.error(f"Error creating enhanced bridge domain {bd_name}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _create_qinq_configuration(self, interfaces: List[Dict], vlan_config: Dict) -> Dict:
        """
        Create QinQ configuration details.
        
        Args:
            interfaces: List of enhanced interfaces
            vlan_config: VLAN configuration
            
        Returns:
            QinQ configuration dictionary
        """
        qinq_config = {
            'type': 'qinq',
            'outer_vlan': vlan_config.get('outer_vlan'),
            'inner_vlan': vlan_config.get('inner_vlan'),
            'imposition_type': 'edge',  # Default to edge imposition
            'vlan_manipulation': {},
            'interface_roles': {}
        }
        
        # Analyze interfaces for QinQ characteristics
        for iface in interfaces:
            if iface.get('vlan_manipulation'):
                qinq_config['vlan_manipulation'][iface['name']] = iface['vlan_manipulation']
            
            if iface.get('assigned_role'):
                qinq_config['interface_roles'][iface['name']] = iface['assigned_role']
        
        # Determine imposition type based on VLAN manipulation
        if any('push outer-tag' in str(manip) for manip in qinq_config['vlan_manipulation'].values()):
            qinq_config['imposition_type'] = 'leaf'
        
        return qinq_config
    
    def _validate_vlan_configuration(self, vlan_config: Dict, bd_type: BridgeDomainType) -> Dict:
        """
        Validate VLAN configuration for RFC compliance.
        
        Args:
            vlan_config: VLAN configuration
            bd_type: Bridge domain type
            
        Returns:
            Validation results
        """
        validation = {
            'rfc_compliant': True,
            'validation_errors': [],
            'warnings': []
        }
        
        # Check VLAN ID range (RFC 802.1Q: 1-4094)
        vlan_id = vlan_config.get('vlan_id')
        if vlan_id is not None:
            if not (1 <= vlan_id <= 4094):
                validation['rfc_compliant'] = False
                validation['validation_errors'].append(f"VLAN ID {vlan_id} outside RFC range (1-4094)")
        
        # Check QinQ VLANs
        if bd_type == BridgeDomainType.QINQ:
            outer_vlan = vlan_config.get('outer_vlan')
            inner_vlan = vlan_config.get('inner_vlan')
            
            if outer_vlan and not (1 <= outer_vlan <= 4094):
                validation['rfc_compliant'] = False
                validation['validation_errors'].append(f"Outer VLAN {outer_vlan} outside RFC range")
            
            if inner_vlan and not (1 <= inner_vlan <= 4094):
                validation['rfc_compliant'] = False
                validation['validation_errors'].append(f"Inner VLAN {inner_vlan} outside RFC range")
            
            if outer_vlan and inner_vlan and outer_vlan == inner_vlan:
                validation['rfc_compliant'] = False
                validation['validation_errors'].append("Outer and inner VLANs cannot be the same")
        
        return validation
    
    def _calculate_confidence_score(self, interfaces: List[Dict], vlan_config: Dict, bd_type: BridgeDomainType) -> int:
        """
        Calculate confidence score for bridge domain discovery.
        
        Args:
            interfaces: List of interfaces
            vlan_config: VLAN configuration
            bd_type: Bridge domain type
            
        Returns:
            Confidence score (0-100)
        """
        score = 50  # Base score
        
        # Interface count bonus
        if len(interfaces) >= 2:
            score += 20
        
        # VLAN configuration bonus
        if vlan_config.get('vlan_id') and 1 <= vlan_config['vlan_id'] <= 4094:
            score += 15
        
        # QinQ detection bonus
        if bd_type == BridgeDomainType.QINQ:
            score += 10
            
            if vlan_config.get('outer_vlan') and vlan_config.get('inner_vlan'):
                score += 5
        
        # Interface role assignment bonus
        if any(iface.get('assigned_role') for iface in interfaces):
            score += 10
        
        return min(score, 100)
    
    def _analyze_enhanced_topologies(self, bridge_domains: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Analyze enhanced topologies with QinQ support.
        
        Args:
            bridge_domains: Dictionary of bridge domains
            
        Returns:
            Enhanced topology analysis
        """
        analysis = {
            'topology_distribution': {
                'p2p': 0,
                'p2mp': 0,
                'qinq_hub_spoke': 0,
                'qinq_mesh': 0,
                'qinq_ring': 0
            },
            'bridge_domain_type_distribution': {
                'single_vlan': 0,
                'vlan_range': 0,
                'vlan_list': 0,
                'qinq': 0
            },
            'interface_role_distribution': {
                'access': 0,
                'uplink': 0,
                'downlink': 0,
                'transport': 0,
                'qinq_multi': 0,
                'qinq_edge': 0,
                'qinq_network': 0
            }
        }
        
        for bd_name, bd_data in bridge_domains.items():
            # Count topology types
            topology_type = bd_data.get('topology_type')
            if topology_type:
                topology_key = str(topology_type).lower().replace('topologytype.', '')
                if topology_key in analysis['topology_distribution']:
                    analysis['topology_distribution'][topology_key] += 1
            
            # Count bridge domain types
            bd_type = bd_data.get('bridge_domain_type')
            if bd_type:
                bd_type_key = str(bd_type).lower().replace('bridgedomaintype.', '')
                if bd_type_key in analysis['bridge_domain_type_distribution']:
                    analysis['bridge_domain_type_distribution'][bd_type_key] += 1
            
            # Count interface roles
            for device_data in bd_data.get('devices', {}).values():
                for iface in device_data.get('interfaces', []):
                    role = iface.get('assigned_role')
                    if role:
                        role_key = str(role).lower().replace('interfacerole.', '')
                        if role_key in analysis['interface_role_distribution']:
                            analysis['interface_role_distribution'][role_key] += 1
        
        return analysis
    
    def run_enhanced_discovery(self) -> Dict[str, Any]:
        """
        Run the enhanced bridge domain discovery process.
        
        Returns:
            Enhanced bridge domain mapping with full QinQ support
        """
        logger.info("Starting Enhanced Bridge Domain Discovery...")
        
        # Load parsed data
        logger.info("Loading parsed bridge domain data...")
        parsed_data = self.load_parsed_data()
        logger.info(f"Loaded data from {len(parsed_data)} devices")
        
        # Create enhanced mapping
        logger.info("Creating enhanced bridge domain mapping...")
        enhanced_mapping = self.create_enhanced_bridge_domain_mapping(parsed_data)
        
        # Save enhanced mapping
        logger.info("Saving enhanced mapping...")
        self.save_enhanced_mapping(enhanced_mapping)
        
        # Save to database
        logger.info("Saving bridge domains to database...")
        database_results = self._save_to_database(enhanced_mapping)
        logger.info(f"Database save results: {database_results}")
        
        # Generate enhanced summary report
        logger.info("Generating enhanced summary report...")
        summary_report = self.generate_enhanced_summary_report(enhanced_mapping)
        summary_file = self.output_dir / f"enhanced_bridge_domain_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w') as f:
            f.write(summary_report)
        
        logger.info("Enhanced Bridge Domain Discovery complete!")
        return enhanced_mapping
    
    def save_enhanced_mapping(self, enhanced_mapping: Dict[str, Any]) -> None:
        """
        Save enhanced bridge domain mapping to file.
        
        Args:
            enhanced_mapping: Enhanced mapping to save
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"enhanced_bridge_domain_mapping_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(enhanced_mapping, f, indent=2, default=str)
        
        logger.info(f"Enhanced mapping saved to: {output_file}")
    
    def _save_to_database(self, enhanced_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save discovered bridge domains to the Phase1 database.
        
        Args:
            enhanced_mapping: Enhanced mapping with all bridge domain data
            
        Returns:
            Dictionary with save results statistics
        """
        results = {
            'total_bridge_domains': 0,
            'saved_successfully': 0,
            'failed_saves': 0,
            'updated_existing': 0,
            'created_new': 0,
            'errors': []
        }
        
        try:
            # Import database manager
            from config_engine.phase1_database import create_phase1_database_manager
            from config_engine.phase1_data_structures.topology_data import TopologyData
            from config_engine.phase1_data_structures.enums import TopologyType, ValidationStatus
            from datetime import datetime
            import traceback
            
            db_manager = create_phase1_database_manager()
            
            bridge_domains = enhanced_mapping.get('bridge_domains', {})
            results['total_bridge_domains'] = len(bridge_domains)
            
            logger.info(f"Processing {len(bridge_domains)} bridge domains for database save...")
            
            for bd_name, bd_data in bridge_domains.items():
                try:
                    # Create TopologyData object from enhanced mapping data
                    topology_data = self._create_topology_data_from_bd(bd_name, bd_data)
                    
                    # Save to database
                    topology_id = db_manager.save_topology_data(topology_data)
                    
                    if topology_id:
                        results['saved_successfully'] += 1
                        logger.debug(f"Saved {bd_name} to database with ID: {topology_id}")
                    else:
                        results['failed_saves'] += 1
                        results['errors'].append(f"Failed to save {bd_name}: No ID returned")
                        
                except Exception as e:
                    results['failed_saves'] += 1
                    error_msg = f"Failed to save {bd_name}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)
                    logger.debug(f"Full traceback for {bd_name}: {traceback.format_exc()}")
                    
                    # If it's a validation error, log the actual data
                    if "validation" in str(e).lower() or "required" in str(e).lower():
                        logger.debug(f"BD data for {bd_name}: {bd_data}")
                        if devices:
                            logger.debug(f"Device data: {devices[0].__dict__ if devices else 'None'}")
                        if interfaces:
                            logger.debug(f"Interface data: {interfaces[0].__dict__ if interfaces else 'None'}")
            
            logger.info(f"Database save completed: {results['saved_successfully']}/{results['total_bridge_domains']} successful")
            
        except Exception as e:
            error_msg = f"Database save failed: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def _create_topology_data_from_bd(self, bd_name: str, bd_data: Dict) -> 'TopologyData':
        """
        Create a TopologyData object from bridge domain data.
        
        Args:
            bd_name: Bridge domain name
            bd_data: Bridge domain data from enhanced mapping
            
        Returns:
            TopologyData object ready for database save
        """
        from config_engine.phase1_data_structures.topology_data import TopologyData
        from config_engine.phase1_data_structures.device_info import DeviceInfo
        from config_engine.phase1_data_structures.interface_info import InterfaceInfo  
        from config_engine.phase1_data_structures.path_info import PathInfo
        from config_engine.phase1_data_structures.bridge_domain_config import BridgeDomainConfig
        from config_engine.phase1_data_structures.enums import TopologyType, ValidationStatus, DeviceRole, InterfaceRole, InterfaceType, DeviceType
        from datetime import datetime
        
        # Extract basic info
        bd_type = bd_data.get('bridge_domain_type', 'SINGLE_VLAN')
        confidence_score = bd_data.get('confidence_score', 85)
        
        # Extract VLAN ID from multiple sources
        vlan_id = bd_data.get('vlan_id')
        if vlan_id is None:
            vlan_config = bd_data.get('vlan_configuration', {})
            vlan_id = vlan_config.get('vlan_id')
            
            # For QinQ, prefer inner VLAN as primary VLAN ID
            if 'QINQ' in str(bd_type):
                qinq_config = bd_data.get('qinq_configuration') or {}
                if qinq_config.get('inner_vlan'):
                    vlan_id = qinq_config['inner_vlan']
                elif vlan_config.get('inner_vlan'):
                    vlan_id = vlan_config['inner_vlan']
        
        # If still None, try extracting from bridge domain name
        if vlan_id is None:
            import re
            vlan_match = re.search(r'v(\d+)', bd_name)
            if vlan_match:
                vlan_id = int(vlan_match.group(1))
        
        # Determine topology type
        device_count = len(bd_data.get('devices', {}))
        if device_count <= 2:
            topology_type = TopologyType.P2P
        else:
            topology_type = TopologyType.P2MP
            
        # Create device data
        devices = []
        interfaces = []
        
        for device_name, device_data in bd_data.get('devices', {}).items():
            # Create device
            device = DeviceInfo(
                name=device_name,
                device_type=DeviceType.LEAF,  # Default, could be enhanced  
                device_role=DeviceRole.SOURCE,  # Default, could be enhanced
                management_ip=device_data.get('management_ip', '')
            )
            devices.append(device)
            
            # Create interfaces for this device
            for interface_data in device_data.get('interfaces', []):
                interface = InterfaceInfo(
                    name=interface_data.get('name', ''),
                    device_name=device_name,
                    interface_type=InterfaceType.PHYSICAL,  # Default
                    interface_role=InterfaceRole.ACCESS,    # Default
                    vlan_id=interface_data.get('vlan_id', vlan_id),
                    description=interface_data.get('description', '')
                )
                interfaces.append(interface)
        
        # Create minimal path data (always create at least one path)
        from config_engine.phase1_data_structures.path_info import PathSegment
        
        paths = []
        if len(devices) >= 2 and len(interfaces) >= 2:
            # Create a segment for multi-device bridge domain
            segment = PathSegment(
                source_device=devices[0].name,
                dest_device=devices[1].name,
                source_interface=interfaces[0].name,
                dest_interface=interfaces[1].name,
                segment_type="leaf_to_leaf"
            )
            
            path = PathInfo(
                path_name=f"{devices[0].name}_to_{devices[1].name}",
                path_type=topology_type,
                source_device=devices[0].name,
                dest_device=devices[1].name,
                segments=[segment]
            )
            paths.append(path)
        elif len(devices) >= 1 and len(interfaces) >= 1:
            # Create a self-loop path for single device bridge domains
            segment = PathSegment(
                source_device=devices[0].name,
                dest_device=devices[0].name,
                source_interface=interfaces[0].name,
                dest_interface=interfaces[0].name,
                segment_type="self_loop"
            )
            
            path = PathInfo(
                path_name=f"{devices[0].name}_self",
                path_type=topology_type,
                source_device=devices[0].name,
                dest_device=devices[0].name,
                segments=[segment]
            )
            paths.append(path)
        else:
            # No devices/interfaces - create a minimal dummy path
            segment = PathSegment(
                source_device="unknown",
                dest_device="unknown",
                source_interface="unknown",
                dest_interface="unknown",
                segment_type="unknown"
            )
            
            path = PathInfo(
                path_name="unknown_path",
                path_type=topology_type,
                source_device="unknown",
                dest_device="unknown", 
                segments=[segment]
            )
            paths.append(path)
        
        # Create bridge domain config - use minimal config to avoid validation issues
        from config_engine.phase1_data_structures.enums import BridgeDomainType
        
        # Convert string to enum (handle both string and enum formats)
        bd_type_enum = BridgeDomainType.SINGLE_TAGGED  # Default (Type 4A)
        
        # Map to specific DNAAS types
        bd_type_str = str(bd_type)
        if 'DOUBLE_TAGGED' in bd_type_str:
            bd_type_enum = BridgeDomainType.DOUBLE_TAGGED
        elif 'QINQ_SINGLE_BD' in bd_type_str:
            bd_type_enum = BridgeDomainType.QINQ_SINGLE_BD
        elif 'QINQ_MULTI_BD' in bd_type_str:
            bd_type_enum = BridgeDomainType.QINQ_MULTI_BD
        elif 'HYBRID' in bd_type_str:
            bd_type_enum = BridgeDomainType.HYBRID
        elif 'SINGLE_TAGGED_RANGE' in bd_type_str:
            bd_type_enum = BridgeDomainType.SINGLE_TAGGED_RANGE
        elif 'SINGLE_TAGGED_LIST' in bd_type_str:
            bd_type_enum = BridgeDomainType.SINGLE_TAGGED_LIST
        elif 'PORT_MODE' in bd_type_str:
            bd_type_enum = BridgeDomainType.PORT_MODE
        elif 'SINGLE_TAGGED' in bd_type_str:
            bd_type_enum = BridgeDomainType.SINGLE_TAGGED
        # Legacy support
        elif 'QINQ' in bd_type_str:
            bd_type_enum = BridgeDomainType.QINQ
        elif 'VLAN_RANGE' in bd_type_str:
            bd_type_enum = BridgeDomainType.VLAN_RANGE
        elif 'VLAN_LIST' in bd_type_str:
            bd_type_enum = BridgeDomainType.VLAN_LIST
        
        # Create destinations from devices (skip first device as it's the source)
        destinations = []
        device_list = list(bd_data.get('devices', {}).items())
        if len(device_list) > 1:
            for device_name, device_data in device_list[1:]:  # Skip first device (source)
                device_interfaces = device_data.get('interfaces', [])
                if device_interfaces:
                    destinations.append({
                        'device': device_name,
                        'port': device_interfaces[0].get('name', 'unknown')
                    })
        
        # For single-device bridge domains, create self-destination
        if not destinations and len(device_list) == 1:
            device_name, device_data = device_list[0]
            device_interfaces = device_data.get('interfaces', [])
            if device_interfaces and len(device_interfaces) > 1:
                # Use second interface as destination
                destinations.append({
                    'device': device_name,
                    'port': device_interfaces[1].get('name', device_interfaces[0].get('name', 'unknown'))
                })
            else:
                # Use same interface as both source and destination
                destinations.append({
                    'device': device_name,
                    'port': device_interfaces[0].get('name', 'unknown') if device_interfaces else 'unknown'
                })
        
        # Extract QinQ-specific information from interface data (more reliable)
        outer_vlan = None
        inner_vlan = None
        if 'QINQ' in str(bd_type) or 'DOUBLE_TAGGED' in str(bd_type) or 'HYBRID' in str(bd_type):
            # Try bridge domain level first
            qinq_config = bd_data.get('qinq_configuration') or {}
            vlan_config = bd_data.get('vlan_configuration') or {}
            
            outer_vlan = qinq_config.get('outer_vlan') or vlan_config.get('outer_vlan')
            inner_vlan = qinq_config.get('inner_vlan') or vlan_config.get('inner_vlan')
            
            # If not found at BD level, extract from interface data
            if outer_vlan is None or inner_vlan is None:
                for device_data in bd_data.get('devices', {}).values():
                    for interface_data in device_data.get('interfaces', []):
                        if outer_vlan is None and interface_data.get('outer_vlan'):
                            outer_vlan = interface_data['outer_vlan']
                        if inner_vlan is None and interface_data.get('inner_vlan'):
                            inner_vlan = interface_data['inner_vlan']
                        
                        # If we found both, break
                        if outer_vlan is not None and inner_vlan is not None:
                            break
                    if outer_vlan is not None and inner_vlan is not None:
                        break
        
        # For QinQ types without explicit outer/inner, use derived values
        if bd_type_enum in [BridgeDomainType.QINQ_SINGLE_BD, BridgeDomainType.QINQ_MULTI_BD, BridgeDomainType.HYBRID]:
            if outer_vlan is None and inner_vlan is None:
                # For LEAF-managed QinQ, use primary VLAN as inner, derive outer from manipulation
                inner_vlan = vlan_id
                # Try to extract outer VLAN from first interface with manipulation
                for device_data in bd_data.get('devices', {}).values():
                    for interface_data in device_data.get('interfaces', []):
                        manipulation = interface_data.get('vlan_manipulation')
                        if manipulation and isinstance(manipulation, dict):
                            ingress = manipulation.get('ingress', '')
                            if 'push outer-tag' in ingress:
                                import re
                                match = re.search(r'push outer-tag (\d+)', ingress)
                                if match:
                                    outer_vlan = int(match.group(1))
                                    break
                    if outer_vlan:
                        break
                
                # If still no outer VLAN, use primary VLAN as outer (fallback)
                if outer_vlan is None:
                    outer_vlan = vlan_id
        
        bridge_domain_config = BridgeDomainConfig(
            service_name=bd_name,
            bridge_domain_type=bd_type_enum,
            source_device=devices[0].name if devices else 'unknown',
            source_interface=interfaces[0].name if interfaces else 'unknown',
            destinations=destinations,
            vlan_id=vlan_id,
            outer_vlan=outer_vlan,
            inner_vlan=inner_vlan
        )
        
        # Create topology data
        topology_data = TopologyData(
            bridge_domain_name=bd_name,
            topology_type=topology_type,
            vlan_id=vlan_id,
            devices=devices,
            interfaces=interfaces,
            paths=paths,
            bridge_domain_config=bridge_domain_config,
            discovered_at=datetime.now(),
            scan_method='enhanced_discovery',
            confidence_score=confidence_score / 100.0,  # Convert to 0.0-1.0 range
            validation_status=ValidationStatus.VALID
        )
        
        return topology_data
    
    def generate_enhanced_summary_report(self, enhanced_mapping: Dict[str, Any]) -> str:
        """
        Generate comprehensive, organized summary report with statistical analysis.
        
        Args:
            enhanced_mapping: Enhanced mapping data
            
        Returns:
            Formatted summary report with executive summary, statistics, and insights
        """
        report = []
        bridge_domains = enhanced_mapping.get('bridge_domains', {})
        metadata = enhanced_mapping.get('discovery_metadata', {})
        
        # ===== HEADER =====
        report.append("🔍 ENHANCED BRIDGE DOMAIN DISCOVERY SUMMARY")
        report.append("=" * 80)
        report.append(f"📅 Discovery Time: {metadata.get('timestamp', 'Unknown')}")
        report.append(f"🔬 Discovery Type: {metadata.get('discovery_type', 'enhanced_with_qinq_support')}")
        report.append(f"🌐 Devices Scanned: {metadata.get('devices_scanned', 0)}")
        report.append("")
        
        # ===== EXECUTIVE SUMMARY =====
        total_bds = len(bridge_domains)
        report.append("📊 EXECUTIVE SUMMARY")
        report.append("─" * 40)
        report.append(f"🏗️  Total Bridge Domains: {total_bds:,}")
        
        # Calculate key metrics
        bd_types = {}
        topology_types = {}
        confidence_levels = {'high': 0, 'medium': 0, 'low': 0}
        qinq_count = 0
        device_distribution = {}
        interface_count = 0
        
        for bd_name, bd_data in bridge_domains.items():
            # Bridge domain types
            bd_type = str(bd_data.get('bridge_domain_type', 'Unknown')).replace('BridgeDomainType.', '')
            bd_types[bd_type] = bd_types.get(bd_type, 0) + 1
            
            # Topology types
            topo_type = str(bd_data.get('topology_type', 'Unknown')).replace('TopologyType.', '')
            topology_types[topo_type] = topology_types.get(topo_type, 0) + 1
            
            # Confidence levels
            confidence = bd_data.get('confidence_score', 0)
            if confidence >= 85:
                confidence_levels['high'] += 1
            elif confidence >= 60:
                confidence_levels['medium'] += 1
            else:
                confidence_levels['low'] += 1
            
            # QinQ count
            if bd_data.get('qinq_configuration'):
                qinq_count += 1
            
            # Device distribution
            for device_name in bd_data.get('devices', {}):
                device_distribution[device_name] = device_distribution.get(device_name, 0) + 1
                
                # Interface count
                interfaces = bd_data['devices'][device_name].get('interfaces', [])
                interface_count += len(interfaces)
        
        report.append(f"🎯 High Confidence (≥85%): {confidence_levels['high']:,} ({confidence_levels['high']/total_bds*100:.1f}%)")
        report.append(f"⚠️  Medium Confidence (60-84%): {confidence_levels['medium']:,} ({confidence_levels['medium']/total_bds*100:.1f}%)")
        report.append(f"🔍 Low Confidence (<60%): {confidence_levels['low']:,} ({confidence_levels['low']/total_bds*100:.1f}%)")
        report.append(f"🔗 QinQ Bridge Domains: {qinq_count:,} ({qinq_count/total_bds*100:.1f}%)")
        report.append(f"📡 Total Interfaces: {interface_count:,}")
        report.append(f"🖥️  Active Devices: {len(device_distribution):,}")
        report.append("")
        
        # ===== TECHNOLOGY DISTRIBUTION =====
        report.append("🔧 TECHNOLOGY DISTRIBUTION")
        report.append("─" * 40)
        
        # Bridge Domain Types with percentages
        report.append("Bridge Domain Types:")
        for bd_type, count in sorted(bd_types.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_bds * 100
            report.append(f"   • {bd_type:<15}: {count:>4,} ({percentage:>5.1f}%)")
        
        report.append("")
        report.append("Topology Types:")
        for topo_type, count in sorted(topology_types.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_bds * 100
            report.append(f"   • {topo_type:<15}: {count:>4,} ({percentage:>5.1f}%)")
        report.append("")
        
        # ===== QINQ ANALYSIS =====
        if qinq_count > 0:
            report.append("🔗 QINQ DETAILED ANALYSIS")
            report.append("─" * 40)
            
            # QinQ subtypes
            dnaas_types = {}
            imposition_locations = {}
            traffic_distributions = {}
            
            for bd_name, bd_data in bridge_domains.items():
                if bd_data.get('qinq_configuration'):
                    classification = bd_data.get('classification_analysis', {})
                    qinq_subtype = classification.get('qinq_subtype', {})
                    
                    dnaas_type = qinq_subtype.get('dnaas_type')
                    if dnaas_type:
                        dnaas_types[dnaas_type] = dnaas_types.get(dnaas_type, 0) + 1
                    
                    imposition = qinq_subtype.get('imposition_location')
                    if imposition:
                        imposition_locations[imposition] = imposition_locations.get(imposition, 0) + 1
                    
                    traffic = qinq_subtype.get('traffic_distribution')
                    if traffic:
                        traffic_distributions[traffic] = traffic_distributions.get(traffic, 0) + 1
            
            report.append("DNAAS Types:")
            for dnaas_type, count in sorted(dnaas_types.items()):
                percentage = count / qinq_count * 100
                report.append(f"   • Type {dnaas_type:<3}: {count:>3,} ({percentage:>5.1f}%)")
            
            report.append("")
            report.append("Imposition Locations:")
            for location, count in sorted(imposition_locations.items(), key=lambda x: x[1], reverse=True):
                percentage = count / qinq_count * 100
                report.append(f"   • {location.title():<8}: {count:>3,} ({percentage:>5.1f}%)")
            
            report.append("")
            report.append("Traffic Distributions:")
            for traffic, count in sorted(traffic_distributions.items(), key=lambda x: x[1], reverse=True):
                percentage = count / qinq_count * 100
                report.append(f"   • {traffic.replace('_', ' ').title():<12}: {count:>3,} ({percentage:>5.1f}%)")
            report.append("")
        
        # ===== DEVICE ANALYSIS =====
        report.append("🖥️  DEVICE ANALYSIS")
        report.append("─" * 40)
        
        # Top 10 most active devices
        top_devices = sorted(device_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
        report.append("Most Active Devices (Top 10):")
        for i, (device, count) in enumerate(top_devices, 1):
            percentage = count / total_bds * 100
            device_short = device[:25] + "..." if len(device) > 28 else device
            report.append(f"   {i:>2}. {device_short:<28}: {count:>3,} BDs ({percentage:>4.1f}%)")
        report.append("")
        
        # Device type analysis
        device_types = {}
        for device in device_distribution.keys():
            if 'SPINE' in device:
                device_types['Spine'] = device_types.get('Spine', 0) + 1
            elif 'LEAF' in device:
                device_types['Leaf'] = device_types.get('Leaf', 0) + 1
            elif 'SuperSpine' in device:
                device_types['SuperSpine'] = device_types.get('SuperSpine', 0) + 1
            else:
                device_types['Other'] = device_types.get('Other', 0) + 1
        
        report.append("Device Type Distribution:")
        for dev_type, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(device_distribution) * 100
            report.append(f"   • {dev_type:<12}: {count:>2,} devices ({percentage:>5.1f}%)")
        report.append("")
        
        # ===== QUALITY METRICS =====
        report.append("🎯 QUALITY METRICS")
        report.append("─" * 40)
        
        # Confidence distribution
        report.append("Confidence Score Distribution:")
        conf_ranges = {
            '95-100%': 0, '90-94%': 0, '85-89%': 0, '80-84%': 0, 
            '70-79%': 0, '60-69%': 0, '50-59%': 0, '<50%': 0
        }
        
        for bd_data in bridge_domains.values():
            conf = bd_data.get('confidence_score', 0)
            if conf >= 95:
                conf_ranges['95-100%'] += 1
            elif conf >= 90:
                conf_ranges['90-94%'] += 1
            elif conf >= 85:
                conf_ranges['85-89%'] += 1
            elif conf >= 80:
                conf_ranges['80-84%'] += 1
            elif conf >= 70:
                conf_ranges['70-79%'] += 1
            elif conf >= 60:
                conf_ranges['60-69%'] += 1
            elif conf >= 50:
                conf_ranges['50-59%'] += 1
            else:
                conf_ranges['<50%'] += 1
        
        for range_name, count in conf_ranges.items():
            if count > 0:
                percentage = count / total_bds * 100
                report.append(f"   • {range_name:<8}: {count:>4,} ({percentage:>5.1f}%)")
        report.append("")
        
        # ===== VLAN ANALYSIS =====
        report.append("🏷️  VLAN ANALYSIS")
        report.append("─" * 40)
        
        vlan_ranges = {'1-100': 0, '101-500': 0, '501-1000': 0, '1001-2000': 0, '2001-3000': 0, '3001-4000': 0, '4001-4094': 0}
        vlan_ids = []
        
        for bd_data in bridge_domains.values():
            vlan_config = bd_data.get('vlan_configuration', {})
            vlan_id = vlan_config.get('vlan_id')
            if vlan_id:
                vlan_ids.append(vlan_id)
                
                if 1 <= vlan_id <= 100:
                    vlan_ranges['1-100'] += 1
                elif 101 <= vlan_id <= 500:
                    vlan_ranges['101-500'] += 1
                elif 501 <= vlan_id <= 1000:
                    vlan_ranges['501-1000'] += 1
                elif 1001 <= vlan_id <= 2000:
                    vlan_ranges['1001-2000'] += 1
                elif 2001 <= vlan_id <= 3000:
                    vlan_ranges['2001-3000'] += 1
                elif 3001 <= vlan_id <= 4000:
                    vlan_ranges['3001-4000'] += 1
                elif 4001 <= vlan_id <= 4094:
                    vlan_ranges['4001-4094'] += 1
        
        report.append("VLAN ID Distribution:")
        for vlan_range, count in vlan_ranges.items():
            if count > 0:
                percentage = count / len(vlan_ids) * 100 if vlan_ids else 0
                report.append(f"   • {vlan_range:<12}: {count:>4,} ({percentage:>5.1f}%)")
        
        if vlan_ids:
            report.append("")
            report.append(f"📈 VLAN Statistics:")
            report.append(f"   • Total VLANs Used: {len(set(vlan_ids)):,}")
            report.append(f"   • VLAN Range: {min(vlan_ids)} - {max(vlan_ids)}")
            report.append(f"   • Most Common VLAN: {max(set(vlan_ids), key=vlan_ids.count)} ({vlan_ids.count(max(set(vlan_ids), key=vlan_ids.count))} times)")
        report.append("")
        
        # ===== INTERESTING CASES =====
        report.append("🔍 NOTABLE CASES")
        report.append("─" * 40)
        
        # Find interesting bridge domains
        low_confidence = [(name, data) for name, data in bridge_domains.items() if data.get('confidence_score', 100) < 50]
        empty_interfaces = [(name, data) for name, data in bridge_domains.items() 
                           if sum(len(dev.get('interfaces', [])) for dev in data.get('devices', {}).values()) == 0]
        complex_qinq = [(name, data) for name, data in bridge_domains.items() 
                       if data.get('qinq_configuration') and 
                       sum(len(dev.get('interfaces', [])) for dev in data.get('devices', {}).values()) > 5]
        
        if low_confidence:
            report.append(f"⚠️  Low Confidence Bridge Domains ({len(low_confidence)}):")
            for name, data in low_confidence[:5]:  # Show top 5
                conf = data.get('confidence_score', 0)
                report.append(f"   • {name[:50]:<50} ({conf}%)")
            if len(low_confidence) > 5:
                report.append(f"   ... and {len(low_confidence) - 5} more")
            report.append("")
        
        if empty_interfaces:
            report.append(f"🚫 Empty Bridge Domains ({len(empty_interfaces)}):")
            for name, data in empty_interfaces[:5]:  # Show top 5
                report.append(f"   • {name[:60]}")
            if len(empty_interfaces) > 5:
                report.append(f"   ... and {len(empty_interfaces) - 5} more")
            report.append("")
        
        if complex_qinq:
            report.append(f"🔗 Complex QinQ Configurations ({len(complex_qinq)}):")
            for name, data in complex_qinq[:3]:  # Show top 3
                interface_count = sum(len(dev.get('interfaces', [])) for dev in data.get('devices', {}).values())
                qinq_config = data.get('qinq_configuration', {})
                outer = qinq_config.get('outer_vlan', 'N/A')
                inner = qinq_config.get('inner_vlan', 'N/A')
                report.append(f"   • {name[:40]:<40} ({interface_count} interfaces, {outer}.{inner})")
            if len(complex_qinq) > 3:
                report.append(f"   ... and {len(complex_qinq) - 3} more")
            report.append("")
        
        # ===== ENHANCED FEATURES STATUS =====
        enhanced_features = metadata.get('enhanced_features', [])
        if enhanced_features:
            report.append("✨ ENHANCED FEATURES STATUS")
            report.append("─" * 40)
            for feature in enhanced_features:
                feature_display = feature.replace('_', ' ').title()
                report.append(f"   ✅ {feature_display}")
            report.append("")
        
        # ===== VALIDATION SUMMARY =====
        vlan_summary = enhanced_mapping.get('vlan_validation_summary', {})
        if vlan_summary:
            report.append("✅ VALIDATION SUMMARY")
            report.append("─" * 40)
            rfc_compliant = vlan_summary.get('rfc_compliant', 0)
            rfc_violations = vlan_summary.get('rfc_violations', 0)
            total_validated = rfc_compliant + rfc_violations
            
            if total_validated > 0:
                compliance_rate = rfc_compliant / total_validated * 100
                report.append(f"📊 RFC 802.1Q Compliance: {compliance_rate:.1f}%")
                report.append(f"   • Compliant: {rfc_compliant:,}")
                report.append(f"   • Violations: {rfc_violations:,}")
            
            validation_errors = vlan_summary.get('validation_errors', [])
            if validation_errors:
                report.append(f"⚠️  Validation Issues ({len(validation_errors)}):")
                for error in validation_errors[:3]:  # Show first 3
                    report.append(f"   • {error}")
                if len(validation_errors) > 3:
                    report.append(f"   ... and {len(validation_errors) - 3} more")
            report.append("")
        
        # ===== RECOMMENDATIONS =====
        report.append("💡 RECOMMENDATIONS")
        report.append("─" * 40)
        
        recommendations = []
        
        if confidence_levels['low'] > total_bds * 0.1:  # >10% low confidence
            recommendations.append(f"🔍 Investigate {confidence_levels['low']} low-confidence bridge domains")
        
        if empty_interfaces:
            recommendations.append(f"🚫 Review {len(empty_interfaces)} bridge domains with no interfaces")
        
        if vlan_summary.get('rfc_violations', 0) > 0:
            recommendations.append(f"⚠️  Fix {vlan_summary['rfc_violations']} RFC compliance violations")
        
        # QinQ recommendations
        if qinq_count > 0:
            qinq_percentage = qinq_count / total_bds * 100
            if qinq_percentage > 20:
                recommendations.append(f"🔗 High QinQ usage ({qinq_percentage:.1f}%) - consider optimization")
            
            # Check for edge vs leaf imposition balance
            edge_count = imposition_locations.get('edge', 0)
            leaf_count = imposition_locations.get('leaf', 0)
            if edge_count > 0 and leaf_count > 0:
                if abs(edge_count - leaf_count) / max(edge_count, leaf_count) > 0.8:
                    recommendations.append("⚖️  Imbalanced QinQ imposition distribution - review architecture")
        
        if not recommendations:
            recommendations.append("✅ No major issues detected - configuration looks healthy")
        
        for rec in recommendations:
            report.append(f"   {rec}")
        
        report.append("")
        report.append("=" * 80)
        report.append(f"📝 Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📊 Total entries analyzed: {total_bds:,}")
        report.append("=" * 80)
        
        return "\n".join(report)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run enhanced discovery
    discovery = EnhancedBridgeDomainDiscovery()
    enhanced_mapping = discovery.run_enhanced_discovery()
    
    # Print summary
    print(discovery.generate_enhanced_summary_report(enhanced_mapping))
