#!/usr/bin/env python3
"""
Database Configuration Updater

Updates database with discovered configurations to maintain
database-reality synchronization.
"""

import logging
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from .data_models import InterfaceConfig, SyncResult, DatabaseSyncError

logger = logging.getLogger(__name__)


class DatabaseConfigurationUpdater:
    """Updates database with discovered configurations"""
    
    def __init__(self, db_path: str = "instance/lab_automation.db"):
        self.db_path = db_path
        
    def update_database_with_discovered_configs(self, discovered_configs: List[InterfaceConfig]) -> SyncResult:
        """Update database with discovered interface configurations"""
        
        try:
            updated_count = 0
            added_count = 0
            skipped_count = 0
            errors = []
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for config in discovered_configs:
                try:
                    # Check if interface config already exists in database
                    existing_config = self._get_existing_interface_config(cursor, config.device_name, config.interface_name)
                    
                    if existing_config:
                        # Update existing configuration
                        if self._update_interface_config(cursor, config):
                            updated_count += 1
                            logger.debug(f"Updated config for {config.interface_name} on {config.device_name}")
                        else:
                            errors.append(f"Failed to update {config.interface_name}")
                    else:
                        # Add new configuration
                        if self._add_interface_config(cursor, config):
                            added_count += 1
                            logger.debug(f"Added config for {config.interface_name} on {config.device_name}")
                        else:
                            errors.append(f"Failed to add {config.interface_name}")
                            
                except Exception as e:
                    errors.append(f"Error processing {config.interface_name}: {e}")
                    logger.error(f"Error processing config for {config.interface_name}: {e}")
            
            # Commit changes
            conn.commit()
            conn.close()
            
            success = len(errors) == 0
            
            if success:
                logger.info(f"Database sync completed: {updated_count} updated, {added_count} added")
            else:
                logger.warning(f"Database sync completed with errors: {len(errors)} errors")
            
            return SyncResult(
                success=success,
                updated_count=updated_count,
                added_count=added_count,
                skipped_count=skipped_count,
                errors=errors,
                total_processed=len(discovered_configs),
                sync_duration=0.0  # Could add timing if needed
            )
            
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            return SyncResult(
                success=False,
                error_message=str(e),
                total_processed=len(discovered_configs) if discovered_configs else 0
            )
    
    def _get_existing_interface_config(self, cursor, device_name: str, interface_name: str) -> Optional[Dict]:
        """Check if interface config exists in database"""
        
        try:
            cursor.execute("""
                SELECT device_name, interface_name, interface_type, description,
                       admin_status, oper_status, discovered_at
                FROM interface_discovery 
                WHERE device_name = ? AND interface_name = ?
            """, (device_name, interface_name))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'device_name': result[0],
                    'interface_name': result[1],
                    'interface_type': result[2],
                    'description': result[3],
                    'admin_status': result[4],
                    'oper_status': result[5],
                    'discovered_at': result[6]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing interface config: {e}")
            return None
    
    def _update_interface_config(self, cursor, config: InterfaceConfig) -> bool:
        """Update existing interface configuration in database"""
        
        try:
            cursor.execute("""
                UPDATE interface_discovery 
                SET admin_status = ?, oper_status = ?, discovered_at = ?,
                    interface_type = ?, description = ?
                WHERE device_name = ? AND interface_name = ?
            """, (
                config.admin_status,
                config.oper_status,
                config.discovered_at,
                config.interface_type,
                f"VLAN {config.vlan_id} - Updated by drift sync" if config.vlan_id else config.description,
                config.device_name,
                config.interface_name
            ))
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating interface config: {e}")
            return False
    
    def _add_interface_config(self, cursor, config: InterfaceConfig) -> bool:
        """Add new interface configuration to database"""
        
        try:
            cursor.execute("""
                INSERT INTO interface_discovery (
                    device_name, interface_name, interface_type, description,
                    admin_status, oper_status, discovered_at, device_reachable, 
                    discovery_errors
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.device_name,
                config.interface_name,
                config.interface_type,
                f"VLAN {config.vlan_id} - Added by drift sync" if config.vlan_id else config.description,
                config.admin_status,
                config.oper_status,
                config.discovered_at,
                True,  # device_reachable
                '[]'   # discovery_errors
            ))
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error adding interface config: {e}")
            return False
    
    def sync_interface_configurations(self, device_name: str, interface_pattern: str = None) -> SyncResult:
        """Sync interface configurations for specific device"""
        
        try:
            # Discover configurations
            discovered_configs = self.targeted_discovery.discover_interface_vlan_configurations(
                device_name, interface_pattern
            )
            
            if discovered_configs:
                # Update database
                return self.update_database_with_discovered_configs(discovered_configs)
            else:
                return SyncResult(
                    success=True,
                    total_processed=0,
                    error_message="No configurations found to sync"
                )
                
        except Exception as e:
            logger.error(f"Interface configuration sync failed: {e}")
            return SyncResult(
                success=False,
                error_message=str(e)
            )


# Convenience functions
def update_database_with_configs(discovered_configs: List[InterfaceConfig]) -> SyncResult:
    """Convenience function to update database with configs"""
    updater = DatabaseConfigurationUpdater()
    return updater.update_database_with_discovered_configs(discovered_configs)


def sync_interface_configurations(device_name: str, interface_pattern: str = None) -> SyncResult:
    """Convenience function to sync interface configurations"""
    updater = DatabaseConfigurationUpdater()
    return updater.sync_interface_configurations(device_name, interface_pattern)
