#!/usr/bin/env python3
"""
Reverse Engineering Engine

This module provides the core functionality to reverse engineer discovered
bridge domain topologies into editable configurations that can be used
with the existing bridge domain builder system.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_engine.topology_mapper import TopologyMapper
from config_engine.config_generator import ReverseEngineeredConfigGenerator
from models import Configuration, PersonalBridgeDomain, db
from flask import current_app

logger = logging.getLogger(__name__)

class BridgeDomainReverseEngineer:
    """
    Reverse Engineering Engine
    
    Converts discovered bridge domain topologies into editable configurations
    that can be used with the existing bridge domain builder system.
    """
    
    def __init__(self):
        self.topology_mapper = TopologyMapper()
        self.config_generator = ReverseEngineeredConfigGenerator()
    
    def reverse_engineer_from_scan(self, scan_result: Dict, user_id: int, force_create: bool = False) -> Optional[Configuration]:
        """
        Main method to reverse engineer scan result into editable configuration.
        
        Args:
            scan_result: Complete scan result from EnhancedTopologyScanner
            user_id: ID of the user performing the reverse engineering
            
        Returns:
            Configuration object if successful, None if failed
        """
        try:
            logger.info("=== STARTING REVERSE ENGINEERING ===")
            logger.info(f"User ID: {user_id}")
            logger.info(f"Scan result keys: {list(scan_result.keys())}")
            
            # Extract key data from scan result
            bridge_domain_name = scan_result.get('bridge_domain_name')
            topology_data = scan_result.get('topology_data', {})
            path_data = scan_result.get('path_data', {})
            
            logger.info(f"Bridge domain: {bridge_domain_name}")
            logger.info(f"Topology data keys: {list(topology_data.keys())}")
            logger.info(f"Path data keys: {list(path_data.keys())}")
            
            # Step 1: Map topology to builder format
            logger.info("=== MAPPING TOPOLOGY TO BUILDER FORMAT ===")
            builder_config = self.topology_mapper.map_to_builder_format(
                topology_data, path_data, bridge_domain_name
            )
            
            if not builder_config:
                logger.error("Failed to map topology to builder format")
                return None
            
            logger.info(f"Mapped builder config keys: {list(builder_config.keys())}")
            
            # Step 2: Generate configuration using existing builders
            logger.info("=== GENERATING CONFIGURATION ===")
            config_data, metadata = self.config_generator.generate_configuration(
                builder_config, user_id
            )
            
            if not config_data:
                logger.error("Failed to generate configuration")
                return None
            
            logger.info(f"Generated config data keys: {list(config_data.keys())}")
            
            # Step 3/4: Persist configuration and update BD in a single transaction/app context
            logger.info("=== PERSISTING CONFIGURATION AND UPDATING BRIDGE DOMAIN ===")
            with current_app.app_context():
                # Infer VLAN ID
                vlan_id = None
                if isinstance(metadata, dict):
                    vlan_id = metadata.get('vlan_id')
                    if not vlan_id:
                        vlans_meta = metadata.get('vlans')
                        if isinstance(vlans_meta, list) and vlans_meta:
                            vlan_id = vlans_meta[0].get('vlan_id')
                if not vlan_id and isinstance(path_data, dict):
                    vlan_paths = path_data.get('vlan_paths', {})
                    for key in vlan_paths.keys():
                        if key.startswith('vlan_'):
                            parts = key.split('_')
                            if len(parts) > 1 and parts[1].isdigit():
                                vlan_id = int(parts[1])
                                break
                if not vlan_id:
                    logger.warning("VLAN ID not found; defaulting to 251")
                    vlan_id = 251

                # Build or extract builder_input consistently
                if not isinstance(metadata, dict):
                    metadata = {}
                builder_input_final = metadata.get('builder_input') if isinstance(metadata.get('builder_input'), dict) else None
                if not builder_input_final:
                    try:
                        builder_input_final = {
                            'vlanId': vlan_id,
                            'sourceDevice': builder_config.get('source_leaf') or builder_config.get('sourceDevice') or builder_config.get('source_device'),
                            'sourceInterface': builder_config.get('source_interface') or builder_config.get('sourceInterface'),
                            'destinations': []
                        }
                        potential_dests = builder_config.get('destinations') or builder_config.get('targets') or builder_config.get('destination_leaves') or []
                        if isinstance(potential_dests, list):
                            for d in potential_dests:
                                if isinstance(d, dict):
                                    device = d.get('leaf') or d.get('device')
                                    port = d.get('port') or d.get('interfaceName') or d.get('interface')
                                    if device:
                                        builder_input_final['destinations'].append({'device': device, 'interfaceName': port or ''})
                    except Exception:
                        builder_input_final = {'vlanId': vlan_id, 'sourceDevice': None, 'sourceInterface': None, 'destinations': []}
                # Mirror into metadata
                metadata['builder_input'] = builder_input_final

                # Find existing RE config for this user+service_name
                existing = None
                try:
                    existing = Configuration.query.filter_by(
                        user_id=user_id,
                        service_name=bridge_domain_name,
                        config_source='reverse_engineered'
                    ).order_by(Configuration.created_at.desc()).first()
                except Exception:
                    existing = None

                if existing and not force_create:
                    logger.info(f"Updating existing RE configuration id={existing.id} for {bridge_domain_name}")
                    existing.vlan_id = vlan_id
                    existing.config_data = json.dumps(config_data)
                    existing.config_metadata = json.dumps(metadata)
                    existing.status = 'deployed'  # Mark as deployed since it exists in the field
                    existing.is_reverse_engineered = True
                    existing.topology_data = json.dumps(topology_data)
                    existing.path_data = json.dumps(path_data)
                    existing.config_source = 'reverse_engineered'
                    existing.builder_type = (metadata or {}).get('builder_type') or 'unified'
                    existing.topology_type = (builder_config or {}).get('topology_type')
                    existing.deployed_at = datetime.utcnow()  # Update deployment time
                    existing.deployed_by = user_id  # Update deployer
                    try:
                        existing.builder_input = json.dumps(builder_input_final)
                    except Exception:
                        pass
                    configuration = existing
                else:
                    logger.info(f"Creating new RE configuration for {bridge_domain_name}")
                    configuration = Configuration(
                        user_id=user_id,
                        service_name=bridge_domain_name,
                        vlan_id=vlan_id,
                        config_type='reverse_engineered'
                    )
                    configuration.config_data = json.dumps(config_data)
                    configuration.config_metadata = json.dumps(metadata)
                    configuration.status = 'deployed'  # Mark as deployed since it exists in the field
                    configuration.is_reverse_engineered = True
                    configuration.topology_data = json.dumps(topology_data)
                    configuration.path_data = json.dumps(path_data)
                    configuration.created_at = datetime.utcnow()
                    configuration.deployed_at = datetime.utcnow()  # Set deployment time to now
                    configuration.deployed_by = user_id  # Set deployer to current user
                    configuration.config_source = 'reverse_engineered'
                    configuration.builder_type = (metadata or {}).get('builder_type') or 'unified'
                    configuration.topology_type = (builder_config or {}).get('topology_type')
                    try:
                        configuration.builder_input = json.dumps(builder_input_final)
                    except Exception:
                        pass
                    db.session.add(configuration)
                    db.session.flush()  # obtain ID if new

                # Link back to PersonalBridgeDomain
                bridge_domain = PersonalBridgeDomain.query.filter_by(
                    user_id=user_id,
                    bridge_domain_name=bridge_domain_name
                ).first()
                if bridge_domain:
                    bridge_domain.reverse_engineered_config_id = configuration.id
                    bridge_domain.config_source = 'reverse_engineered'

                # Commit all
                db.session.commit()

                # Fetch fresh, bound instance
                configuration_final = Configuration.query.get(configuration.id)

            if not configuration_final:
                logger.error("Failed to retrieve configuration after commit")
                return None

            logger.info("=== REVERSE ENGINEERING COMPLETED SUCCESSFULLY ===")
            logger.info(f"Returning configuration ID: {configuration_final.id}")
            return configuration_final
            
        except Exception as e:
            logger.error(f"Reverse engineering failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _create_configuration_entry(self, bridge_domain_name: str, config_data: Dict, 
                                  metadata: Dict, user_id: int, topology_data: Dict, 
                                  path_data: Dict) -> Optional[Configuration]:
        """Create configuration entry in database."""
        try:
            logger.info("=== CREATING CONFIGURATION ENTRY ===")
            logger.info(f"Bridge domain: {bridge_domain_name}")
            logger.info(f"User ID: {user_id}")
            logger.info(f"Config data keys: {list(config_data.keys())}")
            logger.info(f"Metadata keys: {list(metadata.keys())}")
            
            # Check if we have Flask application context
            try:
                from flask import current_app
                has_app_context = current_app is not None
                logger.info(f"Has Flask app context: {has_app_context}")
            except Exception as e:
                logger.warning(f"Could not check Flask app context: {e}")
                has_app_context = False
            
            if not has_app_context:
                logger.error("No Flask application context available")
                return None
                
            with current_app.app_context():
                # Derive VLAN ID
                vlan_id = None
                if isinstance(metadata, dict):
                    vlan_id = metadata.get('vlan_id')
                    if not vlan_id:
                        vlans_meta = metadata.get('vlans')
                        if isinstance(vlans_meta, list) and vlans_meta:
                            vlan_id = vlans_meta[0].get('vlan_id')
                # Fallback: try to infer from path_data keys (e.g., vlan_251_...)
                if not vlan_id and isinstance(path_data, dict):
                    vlan_paths = path_data.get('vlan_paths', {})
                    for key in vlan_paths.keys():
                        if key.startswith('vlan_'):
                            parts = key.split('_')
                            if len(parts) > 1 and parts[1].isdigit():
                                vlan_id = int(parts[1])
                                break
                if not vlan_id:
                    logger.warning("VLAN ID not found; defaulting to 251")
                    vlan_id = 251
                
                # Create configuration entry
                configuration = Configuration(
                    user_id=user_id,
                    service_name=bridge_domain_name,
                    vlan_id=vlan_id,
                    config_type='reverse_engineered'
                )
                configuration.config_data = json.dumps(config_data)
                configuration.config_metadata = json.dumps(metadata)
                configuration.status = 'deployed'  # Mark as deployed since it exists in the field
                configuration.is_reverse_engineered = True
                configuration.topology_data = json.dumps(topology_data)
                configuration.path_data = json.dumps(path_data)
                configuration.created_at = datetime.utcnow()
                configuration.deployed_at = datetime.utcnow()  # Set deployment time to now
                configuration.deployed_by = user_id  # Set deployer to current user
                
                logger.info("Configuration object created, adding to session...")
                db.session.add(configuration)
                
                logger.info("Flushing to get ID...")
                db.session.flush()  # Get the ID
                
                logger.info(f"Created configuration with ID: {configuration.id}")
                # Do not commit here; keep session open until after BD update to avoid detaching
                return configuration
                
        except Exception as e:
            logger.error(f"Failed to create configuration entry: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _update_bridge_domain_reference(self, bridge_domain_name: str, user_id: int, 
                                       config_id: int):
        """Update PersonalBridgeDomain with reference to reverse engineered config."""
        try:
            with current_app.app_context():
                bridge_domain = PersonalBridgeDomain.query.filter_by(
                    user_id=user_id,
                    bridge_domain_name=bridge_domain_name
                ).first()
                
                if bridge_domain:
                    bridge_domain.reverse_engineered_config_id = config_id
                    bridge_domain.config_source = 'reverse_engineered'
                    db.session.commit()
                    logger.info(f"Updated bridge domain {bridge_domain_name} with config ID {config_id}")
                else:
                    logger.warning(f"Bridge domain {bridge_domain_name} not found for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Failed to update bridge domain reference: {e}")
            
    def _finalize_and_return_configuration(self, config_id: int) -> Optional[Configuration]:
        """Fetch a fresh configuration instance by ID to ensure it's bound and committed."""
        try:
            with current_app.app_context():
                config = Configuration.query.get(config_id)
                if config:
                    # Ensure commit so it's persisted
                    db.session.commit()
                return config
        except Exception as e:
            logger.error(f"Failed to finalize configuration: {e}")
            return None
    
    def get_reverse_engineered_config(self, bridge_domain_name: str, user_id: int) -> Optional[Configuration]:
        """Get reverse engineered configuration for a bridge domain."""
        try:
            with current_app.app_context():
                bridge_domain = PersonalBridgeDomain.query.filter_by(
                    user_id=user_id,
                    bridge_domain_name=bridge_domain_name
                ).first()
                
                if bridge_domain and bridge_domain.reverse_engineered_config_id:
                    config = Configuration.query.get(bridge_domain.reverse_engineered_config_id)
                    return config
                return None
                
        except Exception as e:
            logger.error(f"Failed to get reverse engineered config: {e}")
            return None
    
    def is_reverse_engineered(self, bridge_domain_name: str, user_id: int) -> bool:
        """Check if bridge domain has been reverse engineered."""
        try:
            with current_app.app_context():
                bridge_domain = PersonalBridgeDomain.query.filter_by(
                    user_id=user_id,
                    bridge_domain_name=bridge_domain_name
                ).first()
                
                return bridge_domain and bridge_domain.reverse_engineered_config_id is not None
                
        except Exception as e:
            logger.error(f"Failed to check reverse engineered status: {e}")
            return False

# Example usage
def main():
    """Example usage of the reverse engineering engine."""
    engine = BridgeDomainReverseEngineer()
    
    # Example scan result (this would come from the scanner)
    scan_result = {
        "success": True,
        "bridge_domain_name": "test_bridge_domain",
        "topology_data": {
            "nodes": [],
            "edges": [],
            "device_mappings": {}
        },
        "path_data": {
            "device_paths": {},
            "vlan_paths": {},
            "path_statistics": {}
        }
    }
    
    # Reverse engineer the configuration
    config = engine.reverse_engineer_from_scan(scan_result, user_id=1)
    
    if config:
        print(f"Successfully created configuration: {config.id}")
    else:
        print("Failed to create configuration")

if __name__ == "__main__":
    main() 