#!/usr/bin/env python3
"""
Configuration Generator

This module generates configurations using the existing bridge domain builders
from reverse engineered topology data.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_engine.unified_bridge_domain_builder import UnifiedBridgeDomainBuilder
from config_engine.p2mp_bridge_domain_builder import P2MPBridgeDomainBuilder
from config_engine.enhanced_bridge_domain_builder import EnhancedBridgeDomainBuilder

logger = logging.getLogger(__name__)

class ReverseEngineeredConfigGenerator:
    """
    Configuration Generator
    
    Generates configurations using existing bridge domain builders
    from reverse engineered topology data.
    """
    
    def __init__(self):
        self.unified_builder = UnifiedBridgeDomainBuilder()
        self.p2mp_builder = P2MPBridgeDomainBuilder()
        self.enhanced_builder = EnhancedBridgeDomainBuilder()
    
    def generate_configuration(self, builder_config: Dict, user_id: int) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Generate configuration using appropriate builder.
        
        Args:
            builder_config: Mapped topology data in builder format
            user_id: ID of the user generating the configuration
            
        Returns:
            Tuple of (config_data, metadata) or (None, None) if failed
        """
        try:
            logger.info("=== GENERATING CONFIGURATION ===")
            logger.info(f"User ID: {user_id}")
            logger.info(f"Builder config keys: {list(builder_config.keys())}")
            
            # Extract key information
            bridge_domain_name = builder_config.get('bridge_domain_name')
            topology_type = builder_config.get('topology_type', 'unknown')
            devices = builder_config.get('devices', {})
            interfaces = builder_config.get('interfaces', {})
            vlans = builder_config.get('vlans', {})
            
            logger.info(f"Bridge domain: {bridge_domain_name}")
            logger.info(f"Topology type: {topology_type}")
            logger.info(f"Devices: {list(devices.keys())}")
            logger.info(f"Interfaces: {len(interfaces)}")
            logger.info(f"VLANs: {len(vlans)}")
            
            # Step 1: Prepare builder input data
            builder_input = self._prepare_builder_input(builder_config)
            logger.info(f"Prepared builder input with keys: {list(builder_input.keys())}")
            
            # Step 2: Select appropriate builder based on topology type
            config_data, metadata = self._select_and_run_builder(
                topology_type, builder_input, user_id
            )
            
            if not config_data:
                logger.error("Failed to generate configuration")
                return None, None
            
            logger.info(f"Generated configuration with keys: {list(config_data.keys())}")
            logger.info(f"Generated metadata with keys: {list(metadata.keys())}")
            # Attach normalized builder_input for persistence by callers
            metadata = dict(metadata or {})
            metadata['builder_input'] = builder_input
            
            return config_data, metadata
            
        except Exception as e:
            logger.error(f"Failed to generate configuration: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None, None
    
    def _prepare_builder_input(self, builder_config: Dict) -> Dict:
        """Prepare input data for bridge domain builders."""
        try:
            bridge_domain_name = builder_config.get('bridge_domain_name')
            devices = builder_config.get('devices', {})
            interfaces = builder_config.get('interfaces', {})
            vlans = builder_config.get('vlans', {})
            
            # Convert to builder input format
            builder_input = {
                'bridge_domain_name': bridge_domain_name,
                'devices': list(devices.keys()),
                'interfaces': self._format_interfaces_for_builder(interfaces),
                'vlans': self._format_vlans_for_builder(vlans),
                'topology_type': builder_config.get('topology_type', 'unknown'),
                'metadata': builder_config.get('metadata', {})
            }
            
            logger.info(f"Prepared builder input for {len(devices)} devices")
            return builder_input
            
        except Exception as e:
            logger.error(f"Failed to prepare builder input: {e}")
            return {}
    
    def _format_interfaces_for_builder(self, interfaces: Dict[str, Dict]) -> List[Dict]:
        """Format interfaces for builder input."""
        formatted_interfaces = []
        
        for interface_key, interface_data in interfaces.items():
            formatted_interface = {
                'name': interface_data.get('name'),
                'device_name': interface_data.get('device_name'),
                'interface_type': interface_data.get('interface_type'),
                'vlan_id': interface_data.get('vlan_id', 0),
                'status': interface_data.get('status', 'active'),
                'is_subinterface': interface_data.get('is_subinterface', False)
            }
            formatted_interfaces.append(formatted_interface)
        
        return formatted_interfaces
    
    def _format_vlans_for_builder(self, vlans: Dict[str, Dict]) -> List[Dict]:
        """Format VLANs for builder input."""
        formatted_vlans = []
        
        for vlan_key, vlan_data in vlans.items():
            formatted_vlan = {
                'vlan_id': vlan_data.get('vlan_id'),
                'name': vlan_data.get('name'),
                'status': vlan_data.get('status', 'active'),
                'interfaces': vlan_data.get('interfaces', [])
            }
            formatted_vlans.append(formatted_vlan)
        
        return formatted_vlans
    
    def _select_and_run_builder(self, topology_type: str, builder_input: Dict, 
                               user_id: int) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Select appropriate builder and run configuration generation."""
        try:
            logger.info(f"Selecting builder for topology type: {topology_type}")
            
            # Extract basic information
            bridge_domain_name = builder_input['bridge_domain_name']
            devices = builder_input['devices']
            interfaces = builder_input['interfaces']
            vlans = builder_input['vlans']
            
            # For now, we'll create a simple P2P configuration
            # In a real implementation, this would be more sophisticated
            if len(devices) >= 2 and len(interfaces) >= 2:
                # Use the first two devices and interfaces for P2P
                source_device = devices[0]
                dest_device = devices[1]
                source_interface = interfaces[0]['name']
                dest_interface = interfaces[1]['name']
                vlan_id = vlans[0]['vlan_id'] if vlans else 251
                
                logger.info(f"Creating P2P config: {source_device} -> {dest_device}")
                logger.info(f"Interfaces: {source_interface} -> {dest_interface}")
                logger.info(f"VLAN: {vlan_id}")
                
                result = None
                
                if topology_type == 'p2mp':
                    logger.info("Using P2MP Bridge Domain Builder")
                    # Select a source leaf and destinations (other leaves)
                    def is_leaf(name: str) -> bool:
                        return 'LEAF' in name.upper()

                    leaf_devices = [d for d in devices if is_leaf(d)] or devices

                    if len(leaf_devices) < 2:
                        logger.error(f"Insufficient leaf devices for P2MP: {leaf_devices}")
                        return None, None

                    source_leaf = leaf_devices[0]
                    dest_leaves = [d for d in leaf_devices[1:]]

                    # Helper: pick preferred interface for a device, prefer ge* over bundle*
                    def pick_port_for_device(device_name: str) -> Optional[str]:
                        device_ifaces = [i for i in interfaces if i.get('device_name') == device_name]
                        if not device_ifaces:
                            return None
                        # Prefer ge* names
                        ge_ifaces = [i for i in device_ifaces if str(i.get('name','')).startswith('ge')]
                        chosen = ge_ifaces[0] if ge_ifaces else device_ifaces[0]
                        name = str(chosen.get('name',''))
                        # Strip VLAN suffix if present (e.g., ge100-0/0/3.251 -> ge100-0/0/3)
                        base = name.split('.')[0]
                        return base

                    source_port = pick_port_for_device(source_leaf)
                    if not source_port:
                        logger.error(f"No interface found for source leaf {source_leaf}")
                        return None, None

                    p2mp_destinations = []
                    for leaf in dest_leaves:
                        port = pick_port_for_device(leaf)
                        if port:
                            p2mp_destinations.append({'leaf': leaf, 'port': port})

                    if not p2mp_destinations:
                        logger.error("No valid destinations with ports for P2MP")
                        return None, None

                    result = self.p2mp_builder.build_p2mp_bridge_domain_config(
                        bridge_domain_name,
                        vlan_id,
                        source_leaf,
                        source_port,
                        p2mp_destinations
                    )
                
                elif topology_type == 'p2p':
                    logger.info("Using Enhanced Bridge Domain Builder for P2P")
                    result = self.enhanced_builder.build_bridge_domain_config(
                        bridge_domain_name,
                        vlan_id,
                        source_device,
                        source_interface,
                        dest_device,
                        dest_interface
                    )
                
                else:
                    # Default to unified builder for mixed or unknown topologies
                    logger.info("Using Unified Bridge Domain Builder")
                    # Create destinations list for unified builder
                    destinations = [{
                        'device': dest_device,
                        'port': dest_interface
                    }]
                    result = self.unified_builder.build_bridge_domain_config(
                        bridge_domain_name,
                        vlan_id,
                        source_device,
                        source_interface,
                        destinations
                    )
                    
                # Handle different return types
                if result is None:
                    logger.error("Builder returned None")
                    return None, None
                elif isinstance(result, tuple):
                    # Builder returned (config_data, metadata)
                    config_data, metadata = result
                    logger.info(f"Builder returned tuple: config_data={type(config_data)}, metadata={type(metadata)}")
                    return config_data, metadata
                else:
                    # Builder returned just config_data
                    logger.info(f"Builder returned single dict: {type(result)}")
                    # Create basic metadata
                    metadata = {
                        'topology_type': topology_type,
                        'source': 'reverse_engineered',
                        'devices': devices,
                        'interfaces': interfaces,
                        'vlans': vlans
                    }
                    return result, metadata
            else:
                logger.error(f"Insufficient devices ({len(devices)}) or interfaces ({len(interfaces)}) for configuration")
                return None, None
                
        except Exception as e:
            logger.error(f"Failed to run builder: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None, None
    
    def validate_generated_config(self, config_data: Dict, metadata: Dict) -> bool:
        """Validate generated configuration."""
        try:
            # Check that config_data exists
            if not config_data:
                logger.error("No configuration data generated")
                return False
            
            # Check that metadata exists
            if not metadata:
                logger.error("No metadata generated")
                return False
            
            # Check for required keys in config_data
            required_config_keys = ['devices', 'interfaces', 'vlans']
            for key in required_config_keys:
                if key not in config_data:
                    logger.error(f"Missing required config key: {key}")
                    return False
            
            # Check for required keys in metadata
            required_metadata_keys = ['topology_type', 'source']
            for key in required_metadata_keys:
                if key not in metadata:
                    logger.error(f"Missing required metadata key: {key}")
                    return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def get_builder_info(self, topology_type: str) -> Dict:
        """Get information about the builder that would be used."""
        builder_info = {
            'topology_type': topology_type,
            'builder_name': 'unknown',
            'description': 'Unknown topology type'
        }
        
        if topology_type == 'p2mp':
            builder_info.update({
                'builder_name': 'P2MPBridgeDomainBuilder',
                'description': 'Point-to-multipoint bridge domain configuration'
            })
        elif topology_type == 'p2p':
            builder_info.update({
                'builder_name': 'EnhancedBridgeDomainBuilder',
                'description': 'Point-to-point bridge domain configuration'
            })
        else:
            builder_info.update({
                'builder_name': 'UnifiedBridgeDomainBuilder',
                'description': 'Unified bridge domain configuration for mixed topologies'
            })
        
        return builder_info

# Example usage
def main():
    """Example usage of the configuration generator."""
    generator = ReverseEngineeredConfigGenerator()
    
    # Example builder config (this would come from topology mapper)
    builder_config = {
        'bridge_domain_name': 'test_bridge_domain',
        'topology_type': 'p2mp',
        'devices': {
            'DNAAS-LEAF-B10': {
                'name': 'DNAAS-LEAF-B10',
                'device_type': 'leaf',
                'status': 'active'
            },
            'DNAAS-LEAF-B14': {
                'name': 'DNAAS-LEAF-B14',
                'device_type': 'leaf',
                'status': 'active'
            }
        },
        'interfaces': {
            'DNAAS-LEAF-B10_bundle-60000.251': {
                'name': 'bundle-60000.251',
                'device_name': 'DNAAS-LEAF-B10',
                'interface_type': 'bundle',
                'vlan_id': 251,
                'status': 'active'
            },
            'DNAAS-LEAF-B14_bundle-60000.251': {
                'name': 'bundle-60000.251',
                'device_name': 'DNAAS-LEAF-B14',
                'interface_type': 'bundle',
                'vlan_id': 251,
                'status': 'active'
            }
        },
        'vlans': {
            'vlan_251': {
                'vlan_id': 251,
                'name': 'VLAN251',
                'status': 'active',
                'interfaces': ['bundle-60000.251']
            }
        }
    }
    
    # Generate configuration
    config_data, metadata = generator.generate_configuration(builder_config, user_id=1)
    
    if config_data and metadata:
        print("Successfully generated configuration")
        print(f"Config data keys: {list(config_data.keys())}")
        print(f"Metadata keys: {list(metadata.keys())}")
    else:
        print("Failed to generate configuration")

if __name__ == "__main__":
    main() 