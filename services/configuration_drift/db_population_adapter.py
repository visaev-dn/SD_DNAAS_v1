#!/usr/bin/env python3
"""
Database Population Adapter

Comprehensive adapter for populating bridge domain database from various discovery sources.
Handles different use cases: targeted discovery, drift resolution, full sync, etc.

Specifies exactly what data is needed for each database operation and use case.
"""

import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from .data_models import BridgeDomainDiscoveryResult, InterfaceConfig, SyncResult

logger = logging.getLogger(__name__)


class BridgeDomainDatabasePopulationAdapter:
    """Adapter for populating bridge domain database from discovery results"""
    
    def __init__(self, db_path: str = "instance/lab_automation.db"):
        self.db_path = db_path
        
    def populate_from_targeted_discovery(self, discovery_result: BridgeDomainDiscoveryResult) -> SyncResult:
        """Populate database from targeted discovery (drift resolution use case)"""
        
        try:
            print(f"\n📊 POPULATING DATABASE FROM TARGETED DISCOVERY")
            print("="*60)
            print(f"Bridge Domain: {discovery_result.bridge_domain_name}")
            print(f"Use Case: Drift Resolution - Sync database with device reality")
            
            # Step 1: Validate required data for bridge_domains table
            validation_result = self._validate_bridge_domain_data(discovery_result)
            if not validation_result['valid']:
                return SyncResult(
                    success=False,
                    error_message=f"Validation failed: {validation_result['errors']}"
                )
            
            # Step 2: Insert/Update bridge_domains table
            bd_id = self._insert_or_update_bridge_domain(discovery_result)
            if not bd_id:
                return SyncResult(
                    success=False,
                    error_message="Failed to insert/update bridge domain"
                )
            
            # Step 3: Insert/Update bridge_domain_interfaces table
            interface_count = self._insert_or_update_bridge_domain_interfaces(bd_id, discovery_result.interfaces)
            
            # Step 4: Update interface_discovery table for consistency
            self._update_interface_discovery_with_bd_context(discovery_result)
            
            print(f"✅ Database population successful")
            print(f"   • Bridge domain: {discovery_result.bridge_domain_name}")
            print(f"   • Interfaces: {len(discovery_result.interfaces)}")
            print(f"   • Devices: {len(discovery_result.devices)}")
            
            return SyncResult(
                success=True,
                added_count=1,  # Bridge domain
                updated_count=interface_count,
                total_processed=1 + interface_count
            )
            
        except Exception as e:
            logger.error(f"Database population from targeted discovery failed: {e}")
            return SyncResult(
                success=False,
                error_message=str(e)
            )
    
    def populate_from_full_device_discovery(self, device_name: str, 
                                          bridge_domains: List[BridgeDomainDiscoveryResult]) -> SyncResult:
        """Populate database from full device discovery (comprehensive sync use case)"""
        
        try:
            print(f"\n📊 POPULATING DATABASE FROM FULL DEVICE DISCOVERY")
            print("="*60)
            print(f"Device: {device_name}")
            print(f"Bridge Domains: {len(bridge_domains)}")
            print(f"Use Case: Comprehensive Sync - Full device configuration sync")
            
            total_added = 0
            total_updated = 0
            errors = []
            
            for bd_result in bridge_domains:
                try:
                    sync_result = self.populate_from_targeted_discovery(bd_result)
                    if sync_result.success:
                        total_added += sync_result.added_count
                        total_updated += sync_result.updated_count
                    else:
                        errors.extend(sync_result.errors)
                        
                except Exception as e:
                    errors.append(f"Failed to populate {bd_result.bridge_domain_name}: {e}")
            
            return SyncResult(
                success=len(errors) == 0,
                added_count=total_added,
                updated_count=total_updated,
                total_processed=len(bridge_domains),
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Full device discovery population failed: {e}")
            return SyncResult(
                success=False,
                error_message=str(e)
            )
    
    def populate_from_interface_drift(self, device_name: str, interface_name: str, 
                                    interface_config: InterfaceConfig) -> SyncResult:
        """Populate database from interface drift discovery (single interface use case)"""
        
        try:
            print(f"\n📊 POPULATING DATABASE FROM INTERFACE DRIFT")
            print("="*60)
            print(f"Device: {device_name}")
            print(f"Interface: {interface_name}")
            print(f"Use Case: Interface Drift - Single interface configuration sync")
            
            # Extract bridge domain name from interface VLAN context
            bd_name = self._infer_bridge_domain_from_interface(interface_config)
            
            if bd_name:
                # Create minimal bridge domain discovery result
                bd_result = BridgeDomainDiscoveryResult(
                    bridge_domain_name=bd_name,
                    username=self._extract_username_from_bd_name(bd_name),
                    vlan_id=interface_config.vlan_id,
                    interfaces=[interface_config],
                    devices=[device_name],
                    discovery_method="interface_drift_resolution"
                )
                
                # Enhance with classification
                bd_result = self._enhance_with_classification(bd_result)
                
                return self.populate_from_targeted_discovery(bd_result)
            else:
                # Just update interface_discovery table
                self._update_interface_discovery_standalone(interface_config)
                
                return SyncResult(
                    success=True,
                    updated_count=1,
                    total_processed=1
                )
                
        except Exception as e:
            logger.error(f"Interface drift population failed: {e}")
            return SyncResult(
                success=False,
                error_message=str(e)
            )
    
    def _validate_bridge_domain_data(self, discovery_result: BridgeDomainDiscoveryResult) -> Dict[str, Any]:
        """Validate that discovery result has all required data for database population"""
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'required_fields': [],
            'optional_fields': []
        }
        
        # Required fields for bridge_domains table
        required_fields = {
            'name': discovery_result.bridge_domain_name,
            'source': 'discovered',  # Always 'discovered' for targeted discovery
            'configuration_data': discovery_result.configuration_data or {}
        }
        
        # Check required fields
        for field, value in required_fields.items():
            if not value:
                validation['errors'].append(f"Required field missing: {field}")
                validation['valid'] = False
            else:
                validation['required_fields'].append(field)
        
        # Optional but important fields
        optional_fields = {
            'username': discovery_result.username,
            'vlan_id': discovery_result.vlan_id,
            'dnaas_type': discovery_result.dnaas_type,
            'topology_type': discovery_result.topology_type,
            'raw_cli_config': discovery_result.raw_cli_config,
            'discovery_data': discovery_result.discovery_metadata
        }
        
        for field, value in optional_fields.items():
            if value:
                validation['optional_fields'].append(field)
            else:
                validation['warnings'].append(f"Optional field missing: {field}")
        
        # Validate interfaces
        if not discovery_result.interfaces:
            validation['warnings'].append("No interfaces discovered")
        
        return validation
    
    def _insert_or_update_bridge_domain(self, discovery_result: BridgeDomainDiscoveryResult) -> Optional[int]:
        """Insert or update bridge domain in database"""
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if bridge domain exists
            cursor.execute("SELECT id FROM bridge_domains WHERE name = ?", (discovery_result.bridge_domain_name,))
            existing = cursor.fetchone()
            
            # Prepare data for database
            db_data = self._prepare_bridge_domain_database_data(discovery_result)
            
            if existing:
                # Update existing bridge domain
                bd_id = existing[0]
                cursor.execute("""
                    UPDATE bridge_domains 
                    SET username = ?, vlan_id = ?, topology_type = ?, dnaas_type = ?,
                        configuration_data = ?, raw_cli_config = ?, interface_data = ?,
                        discovery_data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    db_data['username'],
                    db_data['vlan_id'],
                    db_data['topology_type'],
                    db_data['dnaas_type'],
                    db_data['configuration_data'],
                    db_data['raw_cli_config'],
                    db_data['interface_data'],
                    db_data['discovery_data'],
                    bd_id
                ))
                print(f"   ✅ Updated existing bridge domain: {discovery_result.bridge_domain_name}")
            else:
                # Insert new bridge domain
                cursor.execute("""
                    INSERT INTO bridge_domains 
                    (name, source, username, vlan_id, topology_type, dnaas_type,
                     configuration_data, raw_cli_config, interface_data, discovery_data,
                     deployment_status, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (
                    discovery_result.bridge_domain_name,
                    'discovered',
                    db_data['username'],
                    db_data['vlan_id'],
                    db_data['topology_type'],
                    db_data['dnaas_type'],
                    db_data['configuration_data'],
                    db_data['raw_cli_config'],
                    db_data['interface_data'],
                    db_data['discovery_data'],
                    'discovered',
                    1  # Default user ID
                ))
                bd_id = cursor.lastrowid
                print(f"   ✅ Inserted new bridge domain: {discovery_result.bridge_domain_name}")
            
            conn.commit()
            conn.close()
            
            return bd_id
            
        except Exception as e:
            logger.error(f"Bridge domain database operation failed: {e}")
            return None
    
    def _prepare_bridge_domain_database_data(self, discovery_result: BridgeDomainDiscoveryResult) -> Dict[str, Any]:
        """Prepare bridge domain data for database insertion"""
        
        # Extract metadata if not already present
        if not discovery_result.username:
            discovery_result.username = self._extract_username_from_bd_name(discovery_result.bridge_domain_name)
        
        if not discovery_result.vlan_id and discovery_result.interfaces:
            # Get VLAN from first interface
            discovery_result.vlan_id = discovery_result.interfaces[0].vlan_id
        
        if not discovery_result.dnaas_type:
            discovery_result.dnaas_type = self._classify_dnaas_type(discovery_result)
        
        if not discovery_result.topology_type:
            discovery_result.topology_type = self._determine_topology_type(discovery_result)
        
        # Structure configuration data
        configuration_data = {
            'bridge_domain': {
                'name': discovery_result.bridge_domain_name,
                'admin_state': 'enabled',
                'vlan_configuration': {
                    'primary_vlan': discovery_result.vlan_id,
                    'vlan_type': 'single_tagged' if discovery_result.dnaas_type and '4A_SINGLE' in discovery_result.dnaas_type else 'unknown'
                }
            },
            'interfaces': [self._interface_config_to_dict(config) for config in discovery_result.interfaces],
            'devices': discovery_result.devices,
            'discovery_summary': {
                'total_interfaces': len(discovery_result.interfaces),
                'total_devices': len(discovery_result.devices),
                'discovery_method': discovery_result.discovery_method
            }
        }
        
        # Structure interface data
        interface_data = {
            'interface_count': len(discovery_result.interfaces),
            'device_count': len(discovery_result.devices),
            'interface_details': [self._interface_config_to_dict(config) for config in discovery_result.interfaces],
            'device_list': discovery_result.devices
        }
        
        # Structure discovery metadata
        discovery_metadata = {
            'discovery_method': discovery_result.discovery_method,
            'discovered_at': discovery_result.discovered_at,
            'confidence_score': discovery_result.confidence_score,
            'validation_status': discovery_result.validation_status,
            'source_commands': discovery_result.raw_cli_config,
            'discovery_metadata': discovery_result.discovery_metadata
        }
        
        return {
            'username': discovery_result.username,
            'vlan_id': discovery_result.vlan_id,
            'topology_type': discovery_result.topology_type,
            'dnaas_type': discovery_result.dnaas_type,
            'configuration_data': json.dumps(configuration_data),
            'raw_cli_config': json.dumps(discovery_result.raw_cli_config),
            'interface_data': json.dumps(interface_data),
            'discovery_data': json.dumps(discovery_metadata)
        }
    
    def _insert_or_update_bridge_domain_interfaces(self, bd_id: int, interfaces: List[InterfaceConfig]) -> int:
        """Insert or update bridge domain interfaces"""
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            
            for interface_config in interfaces:
                # Check if interface association exists
                cursor.execute("""
                    SELECT id FROM bridge_domain_interfaces 
                    WHERE bridge_domain_id = ? AND device_name = ? AND interface_name = ?
                """, (bd_id, interface_config.device_name, interface_config.interface_name))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing interface
                    cursor.execute("""
                        UPDATE bridge_domain_interfaces
                        SET interface_type = ?, vlan_id = ?, admin_status = ?, 
                            oper_status = ?, l2_service_enabled = ?, discovered_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        interface_config.interface_type,
                        interface_config.vlan_id,
                        interface_config.admin_status,
                        interface_config.oper_status,
                        interface_config.l2_service_enabled,
                        existing[0]
                    ))
                    print(f"   ✅ Updated interface: {interface_config.interface_name}")
                else:
                    # Insert new interface
                    cursor.execute("""
                        INSERT INTO bridge_domain_interfaces
                        (bridge_domain_id, device_name, interface_name, interface_type,
                         vlan_id, admin_status, oper_status, l2_service_enabled, discovered_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        bd_id,
                        interface_config.device_name,
                        interface_config.interface_name,
                        interface_config.interface_type,
                        interface_config.vlan_id,
                        interface_config.admin_status,
                        interface_config.oper_status,
                        interface_config.l2_service_enabled
                    ))
                    print(f"   ✅ Inserted interface: {interface_config.interface_name}")
                
                updated_count += 1
            
            conn.commit()
            conn.close()
            
            return updated_count
            
        except Exception as e:
            logger.error(f"Bridge domain interfaces update failed: {e}")
            return 0
    
    def _update_interface_discovery_with_bd_context(self, discovery_result: BridgeDomainDiscoveryResult):
        """Update interface_discovery table with bridge domain context"""
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for interface_config in discovery_result.interfaces:
                # Update interface_discovery with BD context
                cursor.execute("""
                    UPDATE interface_discovery 
                    SET description = ?, discovered_at = CURRENT_TIMESTAMP
                    WHERE device_name = ? AND interface_name = ?
                """, (
                    f"BD: {discovery_result.bridge_domain_name}, VLAN: {interface_config.vlan_id}",
                    interface_config.device_name,
                    interface_config.interface_name
                ))
                
                # Insert if not exists
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO interface_discovery
                        (device_name, interface_name, interface_type, description,
                         admin_status, oper_status, discovered_at, device_reachable, source)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                    """, (
                        interface_config.device_name,
                        interface_config.interface_name,
                        interface_config.interface_type,
                        f"BD: {discovery_result.bridge_domain_name}, VLAN: {interface_config.vlan_id}",
                        interface_config.admin_status,
                        interface_config.oper_status,
                        True,
                        interface_config.source
                    ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Interface discovery update failed: {e}")
    
    def _extract_username_from_bd_name(self, bd_name: str) -> Optional[str]:
        """Extract username from bridge domain name"""
        
        try:
            # Pattern: g_username_v251 or l_username_v251
            match = re.search(r'^[gl]_([^_]+)_v\d+', bd_name)
            if match:
                return match.group(1)
            
            # Pattern: username_v251
            match = re.search(r'^([^_]+)_v\d+', bd_name)
            if match:
                return match.group(1)
            
            # Pattern: g_username-something_v251
            match = re.search(r'^[gl]_([^_]+)', bd_name)
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            logger.error(f"Username extraction failed for {bd_name}: {e}")
            return None
    
    def _extract_vlan_from_bd_name(self, bd_name: str) -> Optional[int]:
        """Extract VLAN ID from bridge domain name"""
        
        try:
            # Pattern: *_v251 or *_v1234
            match = re.search(r'_v(\d+)', bd_name)
            if match:
                return int(match.group(1))
            
            # Pattern: *_vlan_251
            match = re.search(r'_vlan_(\d+)', bd_name)
            if match:
                return int(match.group(1))
            
            return None
            
        except Exception as e:
            logger.error(f"VLAN extraction failed for {bd_name}: {e}")
            return None
    
    def _classify_dnaas_type(self, discovery_result: BridgeDomainDiscoveryResult) -> str:
        """Classify DNAAS type based on discovered configuration"""
        
        try:
            # Analyze interface patterns to determine DNAAS type
            interfaces = discovery_result.interfaces
            vlan_id = discovery_result.vlan_id
            
            if not interfaces:
                return "DNAAS_TYPE_UNKNOWN"
            
            # Check for single VLAN pattern (most common)
            single_vlan_count = sum(1 for intf in interfaces if intf.vlan_id == vlan_id)
            total_interfaces = len(interfaces)
            
            if single_vlan_count == total_interfaces and vlan_id:
                return "DNAAS_TYPE_4A_SINGLE_TAGGED"
            
            # Check for QinQ patterns
            qinq_indicators = sum(1 for intf in interfaces if 'qinq' in intf.description.lower() or 'manipulation' in intf.description.lower())
            if qinq_indicators > 0:
                return "DNAAS_TYPE_2A_QINQ_SINGLE_BD"
            
            # Check for double tagged
            double_tag_indicators = sum(1 for intf in interfaces if intf.interface_name.count('.') > 1)
            if double_tag_indicators > 0:
                return "DNAAS_TYPE_1_DOUBLE_TAGGED"
            
            # Default to single tagged
            return "DNAAS_TYPE_4A_SINGLE_TAGGED"
            
        except Exception as e:
            logger.error(f"DNAAS type classification failed: {e}")
            return "DNAAS_TYPE_UNKNOWN"
    
    def _determine_topology_type(self, discovery_result: BridgeDomainDiscoveryResult) -> str:
        """Determine topology type based on discovered configuration"""
        
        try:
            interface_count = len(discovery_result.interfaces)
            device_count = len(discovery_result.devices)
            
            # Simple heuristics for topology determination
            if interface_count == 2 and device_count == 2:
                return "p2p"  # Point-to-point
            elif interface_count > 2 or device_count > 2:
                return "p2mp"  # Point-to-multipoint
            else:
                return "p2mp"  # Default to p2mp
                
        except Exception as e:
            logger.error(f"Topology type determination failed: {e}")
            return "unknown"
    
    def _interface_config_to_dict(self, interface_config: InterfaceConfig) -> Dict[str, Any]:
        """Convert InterfaceConfig to dictionary for JSON storage"""
        
        return {
            'device_name': interface_config.device_name,
            'interface_name': interface_config.interface_name,
            'vlan_id': interface_config.vlan_id,
            'admin_status': interface_config.admin_status,
            'oper_status': interface_config.oper_status,
            'interface_type': interface_config.interface_type,
            'l2_service_enabled': interface_config.l2_service_enabled,
            'discovered_at': interface_config.discovered_at,
            'source': interface_config.source
        }
    
    def _enhance_with_classification(self, discovery_result: BridgeDomainDiscoveryResult) -> BridgeDomainDiscoveryResult:
        """Enhance discovery result with classification data"""
        
        # Extract metadata from BD name
        if not discovery_result.username:
            discovery_result.username = self._extract_username_from_bd_name(discovery_result.bridge_domain_name)
        
        if not discovery_result.vlan_id:
            discovery_result.vlan_id = self._extract_vlan_from_bd_name(discovery_result.bridge_domain_name)
        
        # Classify DNAAS type
        if not discovery_result.dnaas_type:
            discovery_result.dnaas_type = self._classify_dnaas_type(discovery_result)
        
        # Determine topology type
        if not discovery_result.topology_type:
            discovery_result.topology_type = self._determine_topology_type(discovery_result)
        
        # Structure configuration data
        if not discovery_result.configuration_data:
            discovery_result.configuration_data = {
                'bridge_domain': {
                    'name': discovery_result.bridge_domain_name,
                    'username': discovery_result.username,
                    'vlan_id': discovery_result.vlan_id,
                    'dnaas_type': discovery_result.dnaas_type,
                    'topology_type': discovery_result.topology_type
                },
                'interfaces': [self._interface_config_to_dict(config) for config in discovery_result.interfaces],
                'devices': discovery_result.devices
            }
        
        return discovery_result
    
    def _infer_bridge_domain_from_interface(self, interface_config: InterfaceConfig) -> Optional[str]:
        """Infer bridge domain name from interface configuration"""
        
        try:
            # For drift resolution, we might need to query the device to find which BD this interface belongs to
            # For now, return None to indicate we need more context
            return None
            
        except Exception as e:
            logger.error(f"Bridge domain inference failed: {e}")
            return None
    
    def update_bridge_domain_discovery_data(self, bd_name: str, new_interface: InterfaceConfig) -> bool:
        """Update bridge domain's discovery_data JSON to include newly discovered interface"""
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Step 1: Get current bridge domain record
            cursor.execute("SELECT discovery_data FROM bridge_domains WHERE name = ?", (bd_name,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Bridge domain {bd_name} not found for discovery_data update")
                conn.close()
                return False
            
            # Step 2: Parse current discovery_data JSON
            current_discovery_data = result[0] or '{}'
            if isinstance(current_discovery_data, str):
                discovery_data = json.loads(current_discovery_data)
            else:
                discovery_data = current_discovery_data
            
            # Step 3: Ensure devices structure exists
            if 'devices' not in discovery_data:
                discovery_data['devices'] = {}
            
            device_name = new_interface.device_name
            if device_name not in discovery_data['devices']:
                discovery_data['devices'][device_name] = {'interfaces': []}
            
            if 'interfaces' not in discovery_data['devices'][device_name]:
                discovery_data['devices'][device_name]['interfaces'] = []
            
            # Step 4: Add new interface to discovery_data (if not already present)
            interfaces_list = discovery_data['devices'][device_name]['interfaces']
            
            # Check if interface already exists
            interface_exists = any(
                intf.get('name') == new_interface.interface_name 
                for intf in interfaces_list
            )
            
            if not interface_exists:
                # Add new interface to the list
                new_interface_data = {
                    'name': new_interface.interface_name,
                    'vlan_id': new_interface.vlan_id,
                    'role': 'access',  # Default role for customer interfaces
                    'type': new_interface.interface_type,
                    'admin_status': new_interface.admin_status,
                    'oper_status': new_interface.oper_status,
                    'l2_service_enabled': new_interface.l2_service_enabled,
                    'raw_cli_config': new_interface.raw_cli_config,  # NEW: Include raw CLI commands
                    'added_by_drift_sync': True,
                    'discovered_at': new_interface.discovered_at
                }
                
                interfaces_list.append(new_interface_data)
                
                print(f"   ✅ Added interface to discovery_data: {new_interface.interface_name}")
                print(f"      • Device: {device_name}")
                print(f"      • VLAN: {new_interface.vlan_id}")
                print(f"      • Role: access")
                print(f"      • Raw CLI commands: {len(new_interface.raw_cli_config)}")
                
            else:
                # UPDATE existing interface with new data (CRITICAL FIX)
                print(f"   🔄 Updating existing interface: {new_interface.interface_name}")
                
                # Find and update the existing interface
                for i, existing_intf in enumerate(interfaces_list):
                    if existing_intf.get('name') == new_interface.interface_name:
                        # Update with new data including raw CLI commands
                        interfaces_list[i].update({
                            'vlan_id': new_interface.vlan_id,
                            'admin_status': new_interface.admin_status,
                            'oper_status': new_interface.oper_status,
                            'l2_service_enabled': new_interface.l2_service_enabled,
                            'raw_cli_config': new_interface.raw_cli_config,  # UPDATE: Add raw CLI commands
                            'updated_by_drift_sync': True,
                            'last_updated': new_interface.discovered_at
                        })
                        
                        print(f"      • Updated VLAN: {new_interface.vlan_id}")
                        print(f"      • Updated status: {new_interface.admin_status}/{new_interface.oper_status}")
                        print(f"      • Updated L2 service: {new_interface.l2_service_enabled}")
                        print(f"      • Added raw CLI commands: {len(new_interface.raw_cli_config)}")
                        for cmd in new_interface.raw_cli_config:
                            print(f"         - {cmd}")
                        break
            
            # Always update the bridge domain record (whether interface was new or existing)
            cursor.execute("""
                UPDATE bridge_domains 
                SET discovery_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            """, (json.dumps(discovery_data), bd_name))
            
            conn.commit()
            print(f"   ✅ Bridge domain discovery_data updated")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Bridge domain discovery_data update failed: {e}")
            return False
    
    def _update_interface_discovery_standalone(self, interface_config: InterfaceConfig):
        """Update interface_discovery table for standalone interface"""
        
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO interface_discovery
                (device_name, interface_name, interface_type, description,
                 admin_status, oper_status, discovered_at, device_reachable)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (
                interface_config.device_name,
                interface_config.interface_name,
                interface_config.interface_type,
                f"VLAN: {interface_config.vlan_id}, L2: {interface_config.l2_service_enabled}",
                interface_config.admin_status,
                interface_config.oper_status,
                True
            ))
            
            conn.commit()
            conn.close()
            
            print(f"   ✅ Updated interface discovery: {interface_config.interface_name}")
            
        except Exception as e:
            logger.error(f"Standalone interface discovery update failed: {e}")


# Use Case Specifications
class DatabasePopulationUseCases:
    """Specifications for different database population use cases"""
    
    @staticmethod
    def targeted_drift_resolution_requirements() -> Dict[str, Any]:
        """Data requirements for targeted drift resolution use case"""
        
        return {
            'use_case': 'targeted_drift_resolution',
            'description': 'Sync database when device says "already configured"',
            'required_data': {
                'bridge_domain_name': 'string - BD name from drift context',
                'device_name': 'string - Device where drift detected',
                'interface_configurations': 'List[InterfaceConfig] - Discovered interface configs',
                'username': 'string - Extracted from BD name',
                'vlan_id': 'int - Primary VLAN ID',
                'dnaas_type': 'string - Classified from interface patterns'
            },
            'database_operations': [
                'INSERT/UPDATE bridge_domains table',
                'INSERT/UPDATE bridge_domain_interfaces table',
                'UPDATE interface_discovery table'
            ],
            'validation_requirements': [
                'BD name format validation',
                'Interface VLAN consistency',
                'DNAAS type classification accuracy'
            ]
        }
    
    @staticmethod
    def full_device_sync_requirements() -> Dict[str, Any]:
        """Data requirements for full device synchronization use case"""
        
        return {
            'use_case': 'full_device_sync',
            'description': 'Comprehensive device configuration synchronization',
            'required_data': {
                'device_name': 'string - Target device name',
                'all_bridge_domains': 'List[BridgeDomainDiscoveryResult] - All BDs on device',
                'device_interfaces': 'List[InterfaceConfig] - All device interfaces',
                'device_metadata': 'Dict - Device information and capabilities'
            },
            'database_operations': [
                'BULK INSERT/UPDATE bridge_domains table',
                'BULK INSERT/UPDATE bridge_domain_interfaces table',
                'BULK UPDATE interface_discovery table',
                'CLEANUP orphaned records'
            ],
            'validation_requirements': [
                'Device reachability validation',
                'Configuration consistency validation',
                'Data completeness validation'
            ]
        }
    
    @staticmethod
    def interface_drift_resolution_requirements() -> Dict[str, Any]:
        """Data requirements for single interface drift resolution use case"""
        
        return {
            'use_case': 'interface_drift_resolution',
            'description': 'Resolve drift for single interface configuration',
            'required_data': {
                'device_name': 'string - Device name',
                'interface_name': 'string - Specific interface',
                'interface_config': 'InterfaceConfig - Complete interface configuration',
                'bridge_domain_context': 'Optional[string] - BD name if determinable'
            },
            'database_operations': [
                'UPDATE interface_discovery table',
                'CONDITIONAL UPDATE bridge_domain_interfaces table'
            ],
            'validation_requirements': [
                'Interface existence validation',
                'VLAN configuration validation'
            ]
        }


# Convenience functions
def populate_database_from_targeted_discovery(discovery_result: BridgeDomainDiscoveryResult) -> SyncResult:
    """Convenience function for targeted discovery database population"""
    adapter = BridgeDomainDatabasePopulationAdapter()
    return adapter.populate_from_targeted_discovery(discovery_result)


def populate_database_from_interface_drift(device_name: str, interface_name: str, 
                                         interface_config: InterfaceConfig) -> SyncResult:
    """Convenience function for interface drift database population"""
    adapter = BridgeDomainDatabasePopulationAdapter()
    return adapter.populate_from_interface_drift(device_name, interface_name, interface_config)
