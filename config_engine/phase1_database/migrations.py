#!/usr/bin/env python3
"""
Phase 1 Migration Manager
Handles migration of existing data to Phase 1 data structures
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Import Phase 1 components
from .manager import Phase1DatabaseManager
from config_engine.phase1_integration import DataTransformer

logger = logging.getLogger(__name__)


class Phase1MigrationManager:
    """
    Phase 1 Migration Manager for migrating existing data.
    
    This manager provides:
    1. Migration of existing configurations to Phase 1 format
    2. Data validation during migration
    3. Rollback capabilities
    4. Migration progress tracking
    """
    
    def __init__(self, db_path: str = 'instance/lab_automation.db'):
        """Initialize Phase 1 migration manager"""
        self.db_path = db_path
        self.db_manager = Phase1DatabaseManager(db_path)
        self.transformer = DataTransformer()
        self.logger = logger
        
        self.logger.info("🚀 Phase 1 Migration Manager initialized")
    
    def migrate_existing_configurations(self, limit: int = 100, dry_run: bool = True) -> Dict[str, Any]:
        """
        Migrate existing configurations to Phase 1 format.
        
        Args:
            limit: Maximum number of configurations to migrate
            dry_run: If True, only analyze without making changes
            
        Returns:
            Migration report dictionary
        """
        try:
            self.logger.info(f"🔄 Starting migration of existing configurations (dry_run: {dry_run})")
            
            # Get existing configurations from legacy database
            legacy_configs = self._get_legacy_configurations(limit)
            
            if not legacy_configs:
                return {
                    'status': 'no_data',
                    'message': 'No legacy configurations found to migrate',
                    'total_analyzed': 0,
                    'migrated': 0,
                    'failed': 0,
                    'skipped': 0
                }
            
            migration_report = {
                'status': 'completed',
                'total_analyzed': len(legacy_configs),
                'migrated': 0,
                'failed': 0,
                'skipped': 0,
                'errors': [],
                'details': []
            }
            
            for config in legacy_configs:
                try:
                    config_report = self._migrate_single_configuration(config, dry_run)
                    migration_report['details'].append(config_report)
                    
                    if config_report['status'] == 'migrated':
                        migration_report['migrated'] += 1
                    elif config_report['status'] == 'failed':
                        migration_report['failed'] += 1
                    else:
                        migration_report['skipped'] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to migrate config {config.get('id', 'unknown')}: {str(e)}"
                    migration_report['errors'].append(error_msg)
                    migration_report['failed'] += 1
                    self.logger.error(error_msg)
            
            self.logger.info(f"✅ Migration completed: {migration_report['migrated']} migrated, "
                           f"{migration_report['failed']} failed, {migration_report['skipped']} skipped")
            
            return migration_report
            
        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
            return {
                'status': 'failed',
                'message': str(e),
                'total_analyzed': 0,
                'migrated': 0,
                'failed': 0,
                'skipped': 0,
                'errors': [str(e)]
            }
    
    def _get_legacy_configurations(self, limit: int) -> List[Dict[str, Any]]:
        """Get existing configurations from legacy database"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query existing configurations
            cursor.execute("""
                SELECT id, user_id, service_name, vlan_id, config_type, status, 
                       config_data, config_metadata, created_at
                FROM configurations 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            configs = []
            for row in cursor.fetchall():
                config = {
                    'id': row[0],
                    'user_id': row[1],
                    'service_name': row[2],
                    'vlan_id': row[3],
                    'config_type': row[4],
                    'status': row[5],
                    'config_data': json.loads(row[6]) if row[6] else {},
                    'config_metadata': json.loads(row[7]) if row[7] else {},
                    'created_at': row[8]
                }
                configs.append(config)
            
            conn.close()
            return configs
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get legacy configurations: {e}")
            return []
    
    def _migrate_single_configuration(self, config: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """
        Migrate a single configuration to Phase 1 format.
        
        Args:
            config: Legacy configuration dictionary
            dry_run: If True, only analyze without making changes
            
        Returns:
            Migration report for this configuration
        """
        config_id = config.get('id', 'unknown')
        service_name = config.get('service_name', 'unknown')
        
        try:
            self.logger.info(f"🔄 Analyzing configuration {config_id}: {service_name}")
            
            # Extract configuration parameters
            migration_data = self._extract_migration_data(config)
            
            if not migration_data:
                return {
                    'config_id': config_id,
                    'service_name': service_name,
                    'status': 'skipped',
                    'reason': 'Insufficient data for migration',
                    'details': {}
                }
            
            # Transform to Phase 1 format
            topology_data, passed, errors, warnings = self.transformer.validate_and_transform(
                migration_data['service_name'],
                migration_data['vlan_id'],
                migration_data['source_device'],
                migration_data['source_interface'],
                migration_data['destinations']
            )
            
            if not passed and errors:
                return {
                    'config_id': config_id,
                    'service_name': service_name,
                    'status': 'failed',
                    'reason': 'Phase 1 validation failed',
                    'errors': errors,
                    'warnings': warnings,
                    'details': {}
                }
            
            # Migration analysis report
            analysis_report = {
                'legacy_config': config,
                'extracted_data': migration_data,
                'phase1_topology': topology_data.to_dict() if topology_data else None,
                'validation_passed': passed,
                'validation_errors': errors,
                'validation_warnings': warnings
            }
            
            if dry_run:
                return {
                    'config_id': config_id,
                    'service_name': service_name,
                    'status': 'analyzed',
                    'reason': 'Dry run - no changes made',
                    'details': analysis_report
                }
            
            # Perform actual migration
            topology_id = self.db_manager.save_topology_data(topology_data, config_id)
            
            if topology_id:
                # Link to legacy configuration
                self.db_manager.link_to_legacy_config(topology_id, config_id)
                
                return {
                    'config_id': config_id,
                    'service_name': service_name,
                    'status': 'migrated',
                    'reason': 'Successfully migrated to Phase 1',
                    'topology_id': topology_id,
                    'details': analysis_report
                }
            else:
                return {
                    'config_id': config_id,
                    'service_name': service_name,
                    'status': 'failed',
                    'reason': 'Failed to save Phase 1 topology data',
                    'details': analysis_report
                }
                
        except Exception as e:
            return {
                'config_id': config_id,
                'service_name': service_name,
                'status': 'failed',
                'reason': f'Migration error: {str(e)}',
                'details': {}
            }
    
    def _extract_migration_data(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract migration data from legacy configuration.
        
        Args:
            config: Legacy configuration dictionary
            
        Returns:
            Extracted migration data or None if insufficient
        """
        try:
            # Try to extract from config_metadata first
            metadata = config.get('config_metadata', {})
            
            if metadata and isinstance(metadata, dict):
                # Check if metadata has builder input
                if 'builder_input' in metadata:
                    builder_input = metadata['builder_input']
                    if isinstance(builder_input, dict):
                        return {
                            'service_name': builder_input.get('service_name') or config.get('service_name'),
                            'vlan_id': builder_input.get('vlan_id') or config.get('vlan_id'),
                            'source_device': builder_input.get('source_device'),
                            'source_interface': builder_input.get('source_interface'),
                            'destinations': builder_input.get('destinations', [])
                        }
                
                # Check if metadata has direct configuration data
                if 'source_device' in metadata and 'destinations' in metadata:
                    return {
                        'service_name': config.get('service_name'),
                        'vlan_id': config.get('vlan_id'),
                        'source_device': metadata['source_device'],
                        'source_interface': metadata.get('source_interface', 'unknown'),
                        'destinations': metadata['destinations']
                    }
            
            # Try to extract from config_data
            config_data = config.get('config_data', {})
            if config_data and isinstance(config_data, dict):
                # Look for device configurations that might indicate topology
                devices = [k for k in config_data.keys() if k != '_metadata']
                
                if len(devices) >= 2:
                    # This might be a bridge domain configuration
                    # We'll need to make some assumptions
                    return {
                        'service_name': config.get('service_name'),
                        'vlan_id': config.get('vlan_id'),
                        'source_device': devices[0] if devices else 'unknown',
                        'source_interface': 'unknown',
                        'destinations': [{'device': devices[1], 'port': 'unknown'}] if len(devices) > 1 else []
                    }
            
            # Insufficient data for migration
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to extract migration data: {e}")
            return None
    
    def migrate_bridge_domain_discoveries(self, limit: int = 100, dry_run: bool = True) -> Dict[str, Any]:
        """
        Migrate existing bridge domain discoveries to Phase 1 format.
        
        Args:
            limit: Maximum number of discoveries to migrate
            dry_run: If True, only analyze without making changes
            
        Returns:
            Migration report dictionary
        """
        try:
            self.logger.info(f"🔄 Starting migration of bridge domain discoveries (dry_run: {dry_run})")
            
            # Get existing bridge domain discoveries
            discoveries = self._get_bridge_domain_discoveries(limit)
            
            if not discoveries:
                return {
                    'status': 'no_data',
                    'message': 'No bridge domain discoveries found to migrate',
                    'total_analyzed': 0,
                    'migrated': 0,
                    'failed': 0,
                    'skipped': 0
                }
            
            migration_report = {
                'status': 'completed',
                'total_analyzed': len(discoveries),
                'migrated': 0,
                'failed': 0,
                'skipped': 0,
                'errors': [],
                'details': []
            }
            
            for discovery in discoveries:
                try:
                    discovery_report = self._migrate_single_discovery(discovery, dry_run)
                    migration_report['details'].append(discovery_report)
                    
                    if discovery_report['status'] == 'migrated':
                        migration_report['migrated'] += 1
                    elif discovery_report['status'] == 'failed':
                        migration_report['failed'] += 1
                    else:
                        migration_report['skipped'] += 1
                        
                except Exception as e:
                    error_msg = f"Failed to migrate discovery {discovery.get('id', 'unknown')}: {str(e)}"
                    migration_report['errors'].append(error_msg)
                    migration_report['failed'] += 1
                    self.logger.error(error_msg)
            
            self.logger.info(f"✅ Bridge domain discovery migration completed: "
                           f"{migration_report['migrated']} migrated, "
                           f"{migration_report['failed']} failed, "
                           f"{migration_report['skipped']} skipped")
            
            return migration_report
            
        except Exception as e:
            self.logger.error(f"❌ Bridge domain discovery migration failed: {e}")
            return {
                'status': 'failed',
                'message': str(e),
                'total_analyzed': 0,
                'migrated': 0,
                'failed': 0,
                'skipped': 0,
                'errors': [str(e)]
            }
    
    def _get_bridge_domain_discoveries(self, limit: int) -> List[Dict[str, Any]]:
        """Get existing bridge domain discoveries from legacy database"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Query existing bridge domain discoveries
            cursor.execute("""
                SELECT id, user_id, bridge_domain_name, imported_from_topology, 
                       discovery_data, devices, topology_analysis, vlan_id, 
                       topology_type, detection_method, confidence, username
                FROM personal_bridge_domains 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            discoveries = []
            for row in cursor.fetchall():
                discovery = {
                    'id': row[0],
                    'user_id': row[1],
                    'bridge_domain_name': row[2],
                    'imported_from_topology': row[3],
                    'discovery_data': json.loads(row[4]) if row[4] else {},
                    'devices': json.loads(row[5]) if row[5] else {},
                    'topology_analysis': json.loads(row[6]) if row[6] else {},
                    'vlan_id': row[7],
                    'topology_type': row[8],
                    'detection_method': row[9],
                    'confidence': row[10],
                    'username': row[11]
                }
                discoveries.append(discovery)
            
            conn.close()
            return discoveries
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get bridge domain discoveries: {e}")
            return []
    
    def _migrate_single_discovery(self, discovery: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """
        Migrate a single bridge domain discovery to Phase 1 format.
        
        Args:
            discovery: Bridge domain discovery dictionary
            dry_run: If True, only analyze without making changes
            
        Returns:
            Migration report for this discovery
        """
        discovery_id = discovery.get('id', 'unknown')
        bridge_domain_name = discovery.get('bridge_domain_name', 'unknown')
        
        try:
            self.logger.info(f"🔄 Analyzing discovery {discovery_id}: {bridge_domain_name}")
            
            # Check if we have sufficient data for migration
            if not discovery.get('discovery_data') and not discovery.get('devices'):
                return {
                    'discovery_id': discovery_id,
                    'bridge_domain_name': bridge_domain_name,
                    'status': 'skipped',
                    'reason': 'Insufficient discovery data for migration',
                    'details': {}
                }
            
            # Create a basic topology structure from discovery data
            topology_data = self._create_topology_from_discovery(discovery)
            
            if not topology_data:
                return {
                    'discovery_id': discovery_id,
                    'bridge_domain_name': bridge_domain_name,
                    'status': 'skipped',
                    'reason': 'Could not create topology from discovery data',
                    'details': {}
                }
            
            # Migration analysis report
            analysis_report = {
                'legacy_discovery': discovery,
                'phase1_topology': topology_data.to_dict(),
                'validation_passed': True,
                'validation_errors': [],
                'validation_warnings': []
            }
            
            if dry_run:
                return {
                    'discovery_id': discovery_id,
                    'bridge_domain_name': bridge_domain_name,
                    'status': 'analyzed',
                    'reason': 'Dry run - no changes made',
                    'details': analysis_report
                }
            
            # Perform actual migration
            topology_id = self.db_manager.save_topology_data(topology_data)
            
            if topology_id:
                return {
                    'discovery_id': discovery_id,
                    'bridge_domain_name': bridge_domain_name,
                    'status': 'migrated',
                    'reason': 'Successfully migrated to Phase 1',
                    'topology_id': topology_id,
                    'details': analysis_report
                }
            else:
                return {
                    'discovery_id': discovery_id,
                    'bridge_domain_name': bridge_domain_name,
                    'status': 'failed',
                    'reason': 'Failed to save Phase 1 topology data',
                    'details': analysis_report
                }
                
        except Exception as e:
            return {
                'discovery_id': discovery_id,
                'bridge_domain_name': bridge_domain_name,
                'status': 'failed',
                'reason': f'Migration error: {str(e)}',
                'details': {}
            }
    
    def _create_topology_from_discovery(self, discovery: Dict[str, Any]):
        """Create Phase 1 topology from discovery data"""
        try:
            from config_engine.phase1_data_structures import (
                TopologyData, DeviceInfo, InterfaceInfo, PathInfo, PathSegment,
                BridgeDomainConfig, TopologyType, DeviceType, InterfaceType, 
                InterfaceRole, DeviceRole, ValidationStatus, BridgeDomainType, OuterTagImposition
            )
            
            # Extract basic information
            bridge_domain_name = discovery.get('bridge_domain_name', 'unknown')
            vlan_id = discovery.get('vlan_id')
            topology_type = discovery.get('topology_type', 'unknown')
            confidence = discovery.get('confidence', 0.0)
            
            # Create basic device information
            devices = []
            interfaces = []
            paths = []
            
            # Try to extract device information
            discovery_data = discovery.get('discovery_data', {})
            devices_data = discovery.get('devices', {})
            
            if devices_data:
                for device_name, device_info in devices_data.items():
                    if isinstance(device_info, dict):
                        # Create device info
                        device = DeviceInfo(
                            name=device_name,
                            device_type=DeviceType.LEAF,  # Default assumption
                            device_role=DeviceRole.SOURCE,  # Default assumption
                            discovered_at=datetime.now(),
                            confidence_score=confidence
                        )
                        devices.append(device)
                        
                        # Create basic interface info
                        interface = InterfaceInfo(
                            name='unknown',
                            interface_type=InterfaceType.PHYSICAL,
                            interface_role=InterfaceRole.ACCESS,
                            device_name=device_name,
                            vlan_id=vlan_id,
                            discovered_at=datetime.now(),
                            confidence_score=confidence
                        )
                        interfaces.append(interface)
            
            # Create basic bridge domain configuration
            bridge_domain_config = BridgeDomainConfig(
                service_name=bridge_domain_name,
                bridge_domain_type=BridgeDomainType.SINGLE_VLAN,
                source_device=devices[0].name if devices else 'unknown',
                source_interface='unknown',
                destinations=[],
                vlan_id=vlan_id,
                created_at=datetime.now(),
                confidence_score=confidence
            )
            
            # Create topology data
            topology_data = TopologyData(
                bridge_domain_name=bridge_domain_name,
                topology_type=TopologyType.P2P if topology_type == 'p2p' else TopologyType.P2MP,
                vlan_id=vlan_id,
                devices=devices,
                interfaces=interfaces,
                paths=paths,
                bridge_domain_config=bridge_domain_config,
                discovered_at=datetime.now(),
                scan_method=discovery.get('detection_method', 'discovery'),
                confidence_score=confidence,
                validation_status=ValidationStatus.PENDING
            )
            
            return topology_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create topology from discovery: {e}")
            return None
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and statistics"""
        try:
            db_info = self.db_manager.get_database_info()
            stats = self.db_manager.get_topology_statistics()
            
            return {
                'database_info': db_info,
                'topology_statistics': stats,
                'migration_ready': True,
                'total_phase1_records': db_info.get('total_phase1_records', 0),
                'phase1_tables': db_info.get('phase1_tables', [])
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get migration status: {e}")
            return {
                'migration_ready': False,
                'error': str(e)
            }
    
    def rollback_migration(self, topology_id: int) -> bool:
        """
        Rollback a specific migration by deleting Phase 1 data.
        
        Args:
            topology_id: ID of the topology data to rollback
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"🔄 Rolling back migration for topology {topology_id}")
            
            success = self.db_manager.delete_topology_data(topology_id)
            
            if success:
                self.logger.info(f"✅ Successfully rolled back migration for topology {topology_id}")
            else:
                self.logger.error(f"❌ Failed to rollback migration for topology {topology_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Rollback failed: {e}")
            return False

