#!/usr/bin/env python3
"""
Bridge Domain Detector Component

SINGLE RESPONSIBILITY: Detect and parse bridge domains from raw CLI data

INPUT: Raw CLI data, YAML files
OUTPUT: Parsed bridge domain instances with VLAN configurations
DEPENDENCIES: None (pure parsing)
"""

import os
import sys
import yaml
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Add the parent directory to the path to import other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config_engine.phase1_data_structures.enums import BridgeDomainType, InterfaceType
from config_engine.bridge_domain_classifier import BridgeDomainClassifier

@dataclass
class VLANConfig:
    """VLAN configuration data structure"""
    vlan_id: Optional[int] = None
    outer_vlan: Optional[int] = None
    inner_vlan: Optional[int] = None
    vlan_range: Optional[str] = None
    vlan_list: Optional[List[int]] = None
    vlan_manipulation: Optional[Dict[str, Any]] = None
    interface_type: Optional[InterfaceType] = None

@dataclass
class BridgeDomainInstance:
    """Core bridge domain data structure"""
    name: str
    dnaas_type: BridgeDomainType
    vlan_config: VLANConfig
    interfaces: List[str]
    devices: List[str]
    confidence: float
    admin_state: str = "enabled"

class BridgeDomainDetector:
    """
    Bridge Domain Detector Component
    
    SINGLE RESPONSIBILITY: Detect and parse bridge domains from raw CLI data
    """
    
    def __init__(self):
        self.bridge_domain_classifier = BridgeDomainClassifier()
        self.bridge_domain_parsed_dir = Path('topology/configs/parsed_data/bridge_domain_parsed')
        self._vlan_config_cache = {}
    
    def detect_bridge_domains(self, parsed_data: Dict[str, Any]) -> List[BridgeDomainInstance]:
        """
        Detect and parse bridge domains from device data
        
        Args:
            parsed_data: Dictionary of device data with bridge domain instances
            
        Returns:
            List of parsed bridge domain instances
        """
        logger.info("🔍 Starting bridge domain detection...")
        
        all_bridge_domains = []
        
        # Collect all bridge domain instances from all devices
        all_bridge_domain_instances = {}
        
        for device_name, device_data in parsed_data.items():
            bridge_domain_instances = device_data.get('bridge_domain_instances', [])
            
            for bd_instance in bridge_domain_instances:
                bd_name = bd_instance.get('name', 'unknown')
                
                if bd_name not in all_bridge_domain_instances:
                    all_bridge_domain_instances[bd_name] = []
                
                all_bridge_domain_instances[bd_name].append({
                    'device_name': device_name,
                    'bd_instance': bd_instance,
                    'vlan_configs': device_data.get('enhanced_vlan_configurations', [])
                })
        
        # Process each bridge domain
        for bd_name, device_instances in all_bridge_domain_instances.items():
            try:
                bridge_domain = self._create_bridge_domain_instance(bd_name, device_instances)
                all_bridge_domains.append(bridge_domain)
                logger.debug(f"✅ Detected bridge domain: {bd_name}")
            except Exception as e:
                logger.error(f"❌ Failed to detect bridge domain {bd_name}: {e}")
                continue
        
        logger.info(f"🔍 Bridge domain detection complete: {len(all_bridge_domains)} domains detected")
        return all_bridge_domains
    
    def _create_bridge_domain_instance(self, bd_name: str, device_instances: List[Dict]) -> BridgeDomainInstance:
        """Create a bridge domain instance from device data"""
        
        # Collect all interfaces and devices
        all_interfaces = []
        all_devices = []
        all_vlan_configs = []
        
        for device_instance in device_instances:
            device_name = device_instance['device_name']
            bd_instance = device_instance['bd_instance']
            vlan_configs = device_instance['vlan_configs']
            
            all_devices.append(device_name)
            all_interfaces.extend(bd_instance.get('interfaces', []))
            all_vlan_configs.extend(vlan_configs)
        
        # Extract VLAN configuration
        vlan_config = self.extract_vlan_configuration(all_interfaces, all_vlan_configs)
        
        # Classify DNAAS type
        dnaas_type, confidence = self.classify_dnaas_type(bd_name, all_interfaces, vlan_config)
        
        # Create bridge domain instance
        bridge_domain = BridgeDomainInstance(
            name=bd_name,
            dnaas_type=dnaas_type,
            vlan_config=vlan_config,
            interfaces=all_interfaces,
            devices=list(set(all_devices)),  # Remove duplicates
            confidence=confidence,
            admin_state=device_instances[0]['bd_instance'].get('admin_state', 'enabled')
        )
        
        return bridge_domain
    
    def extract_vlan_configuration(self, interfaces: List[str], vlan_configs: List[Dict]) -> VLANConfig:
        """
        Extract VLAN configuration from interface configurations
        
        GOLDEN RULE: Only use CLI configuration data, never interface names
        """
        vlan_config = VLANConfig()
        
        # Find VLAN configuration for interfaces
        for interface_name in interfaces:
            interface_vlan_config = self._find_vlan_config_for_interface(interface_name, vlan_configs)
            
            if interface_vlan_config:
                # Extract VLAN information (following Golden Rule)
                if interface_vlan_config.get('vlan_id') and not vlan_config.vlan_id:
                    vlan_config.vlan_id = interface_vlan_config['vlan_id']
                
                if interface_vlan_config.get('outer_vlan') and not vlan_config.outer_vlan:
                    vlan_config.outer_vlan = interface_vlan_config['outer_vlan']
                
                if interface_vlan_config.get('inner_vlan') and not vlan_config.inner_vlan:
                    vlan_config.inner_vlan = interface_vlan_config['inner_vlan']
                
                if interface_vlan_config.get('vlan_range') and not vlan_config.vlan_range:
                    vlan_config.vlan_range = interface_vlan_config['vlan_range']
                
                if interface_vlan_config.get('vlan_list') and not vlan_config.vlan_list:
                    vlan_config.vlan_list = interface_vlan_config['vlan_list']
                
                if interface_vlan_config.get('vlan_manipulation') and not vlan_config.vlan_manipulation:
                    vlan_config.vlan_manipulation = interface_vlan_config['vlan_manipulation']
                
                # Determine interface type
                if '.' in interface_name:
                    vlan_config.interface_type = InterfaceType.SUBINTERFACE
                elif 'bundle-' in interface_name.lower():
                    vlan_config.interface_type = InterfaceType.BUNDLE
                else:
                    vlan_config.interface_type = InterfaceType.PHYSICAL
        
        return vlan_config
    
    def classify_dnaas_type(self, bd_name: str, interfaces: List[str], vlan_config: VLANConfig) -> Tuple[BridgeDomainType, float]:
        """
        Classify bridge domain according to DNAAS types 1-5
        
        Args:
            bd_name: Bridge domain name
            interfaces: List of interface names
            vlan_config: Extracted VLAN configuration
            
        Returns:
            Tuple of (DNAAS type, confidence score)
        """
        try:
            # Create interface data for classifier
            interface_data = []
            for interface_name in interfaces:
                interface_info = {
                    'name': interface_name,
                    'vlan_id': vlan_config.vlan_id,
                    'outer_vlan': vlan_config.outer_vlan,
                    'inner_vlan': vlan_config.inner_vlan,
                    'vlan_range': vlan_config.vlan_range,
                    'vlan_list': vlan_config.vlan_list,
                    'vlan_manipulation': vlan_config.vlan_manipulation,
                    'type': vlan_config.interface_type.value if vlan_config.interface_type else 'unknown'
                }
                interface_data.append(interface_info)
            
            # Use existing classifier
            dnaas_type, confidence = self.bridge_domain_classifier.classify_bridge_domain(bd_name, interface_data)
            
            logger.debug(f"Classified {bd_name} as {dnaas_type.value} with {confidence}% confidence")
            return dnaas_type, confidence / 100.0  # Convert to decimal
            
        except Exception as e:
            logger.error(f"Failed to classify bridge domain {bd_name}: {e}")
            return BridgeDomainType.SINGLE_TAGGED, 0.5  # Default with low confidence
    
    def _find_vlan_config_for_interface(self, interface_name: str, vlan_configs: List[Dict]) -> Optional[Dict]:
        """Find VLAN configuration for specific interface"""
        
        for vlan_config in vlan_configs:
            if vlan_config.get('interface') == interface_name:
                return vlan_config
        
        return None
    
    def _extract_device_name(self, file_path: Path) -> str:
        """Extract device name from file path"""
        filename = file_path.stem
        # Remove timestamp and file type suffixes
        device_name = re.sub(r'_bridge_domain_instance_parsed_\d+_\d+$', '', filename)
        return device_name
    
    def load_parsed_data(self) -> Dict[str, Any]:
        """
        Load all parsed YAML files and create device data structures
        
        Returns:
            Dictionary mapping device names to their bridge domain data
        """
        logger.info("📁 Loading parsed bridge domain data...")
        
        parsed_data = {}
        
        if not self.bridge_domain_parsed_dir.exists():
            logger.error(f"Bridge domain parsed directory not found: {self.bridge_domain_parsed_dir}")
            return parsed_data
        
        # Load bridge domain instance files
        for device_file in self.bridge_domain_parsed_dir.glob('*_bridge_domain_instance_parsed_*.yaml'):
            try:
                device_name = self._extract_device_name(device_file)
                
                # Load bridge domain instances
                with open(device_file, 'r') as f:
                    bd_data = yaml.safe_load(f)
                    bridge_domain_instances = bd_data.get('bridge_domain_instances', [])
                
                # Load VLAN configurations (if available)
                vlan_configs = self._load_real_vlan_configs(device_name)
                
                # Create device data structure
                parsed_data[device_name] = {
                    'bridge_domain_instances': bridge_domain_instances,
                    'enhanced_vlan_configurations': vlan_configs
                }
                
                logger.debug(f"Loaded {len(bridge_domain_instances)} bridge domains from {device_name}")
                
            except Exception as e:
                logger.error(f"Failed to load data from {device_file}: {e}")
                continue
        
        logger.info(f"📁 Loaded parsed data from {len(parsed_data)} devices")
        return parsed_data
    
    def _load_real_vlan_configs(self, device_name: str) -> List[Dict]:
        """Load real VLAN configurations for a device"""
        
        # Check cache first
        if device_name in self._vlan_config_cache:
            return self._vlan_config_cache[device_name]
        
        try:
            # Find VLAN config file for this device
            vlan_config_pattern = f"{self.bridge_domain_parsed_dir}/{device_name}_vlan_config_parsed_*.yaml"
            import glob
            vlan_config_files = glob.glob(vlan_config_pattern)
            
            if not vlan_config_files:
                logger.debug(f"No VLAN config file found for {device_name}")
                self._vlan_config_cache[device_name] = []
                return []
            
            # Use most recent file
            vlan_config_file = max(vlan_config_files, key=os.path.getctime)
            
            with open(vlan_config_file, 'r') as f:
                vlan_data = yaml.safe_load(f)
                vlan_configs = vlan_data.get('vlan_configurations', [])
            
            # Cache the result
            self._vlan_config_cache[device_name] = vlan_configs
            logger.debug(f"Loaded {len(vlan_configs)} VLAN configs for {device_name}")
            
            return vlan_configs
            
        except Exception as e:
            logger.error(f"Failed to load VLAN configs for {device_name}: {e}")
            self._vlan_config_cache[device_name] = []
            return []
