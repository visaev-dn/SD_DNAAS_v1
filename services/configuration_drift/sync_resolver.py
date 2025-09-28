#!/usr/bin/env python3
"""
Configuration Sync Resolver

Resolves configuration drift issues through interactive user options
and automatic database synchronization.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from .data_models import DriftEvent, SyncResolution, SyncAction, SyncResult
from .targeted_discovery import TargetedConfigurationDiscovery

logger = logging.getLogger(__name__)


class ConfigurationSyncResolver:
    """Resolves sync issues between database and device reality"""
    
    def __init__(self):
        self.targeted_discovery = TargetedConfigurationDiscovery()
        
        # Import database updater when available
        try:
            from .database_updater import DatabaseConfigurationUpdater
            self.database_updater = DatabaseConfigurationUpdater()
            self.database_available = True
        except ImportError:
            self.database_updater = None
            self.database_available = False
            logger.warning("Database updater not available")
    
    def resolve_drift_interactive(self, drift_event: DriftEvent) -> SyncResolution:
        """Interactive drift resolution with user options"""
        
        try:
            print(f"\\n⚠️  CONFIGURATION DRIFT DETECTED")
            print("="*60)
            print(f"Device: {drift_event.device_name}")
            print(f"Issue: {drift_event.drift_type.value.replace('_', ' ').title()}")
            print(f"Detection: {drift_event.detection_source}")
            
            if drift_event.interface_name:
                print(f"Interface: {drift_event.interface_name}")
            
            print(f"\\n💡 EXPLANATION:")
            print("This means the device has configurations that our database doesn't know about.")
            print("This could be due to:")
            print("   • Manual configuration changes on the device")
            print("   • Other automation tools modifying configurations")
            print("   • Historical configurations from before our system")
            print("   • Emergency changes bypassing our database")
            
            print(f"\\n🔧 RESOLUTION OPTIONS:")
            print("1. 🔍 Discover and sync (recommended)")
            print("   - Scan device for actual configurations")
            print("   - Update database with discovered configs")
            print("   - Re-evaluate deployment plan")
            
            print("2. ⏭️  Skip conflicting interfaces")
            print("   - Continue deployment without conflicting interfaces")
            print("   - Log sync issue for later resolution")
            
            print("3. 🔄 Override (force reconfiguration)")
            print("   - Force configuration even if already exists")
            print("   - May cause configuration conflicts")
            
            print("4. ❌ Abort deployment")
            print("   - Stop deployment to investigate manually")
            
            try:
                choice = input("\\nSelect resolution option [1-4]: ").strip()
                
                if choice == '1':
                    return self._execute_discover_and_sync(drift_event)
                elif choice == '2':
                    return SyncResolution(
                        action=SyncAction.SKIP,
                        message="User chose to skip conflicting interfaces",
                        user_choice="skip"
                    )
                elif choice == '3':
                    return SyncResolution(
                        action=SyncAction.OVERRIDE,
                        message="User chose to override existing configuration",
                        user_choice="override"
                    )
                elif choice == '4':
                    return SyncResolution(
                        action=SyncAction.ABORT,
                        message="User chose to abort deployment",
                        user_choice="abort"
                    )
                else:
                    print("❌ Invalid selection, aborting deployment")
                    return SyncResolution(
                        action=SyncAction.ABORT,
                        message="Invalid user selection"
                    )
                    
            except KeyboardInterrupt:
                print("\\n❌ User cancelled resolution")
                return SyncResolution(
                    action=SyncAction.ABORT,
                    message="User cancelled drift resolution"
                )
                
        except Exception as e:
            logger.error(f"Interactive drift resolution failed: {e}")
            return SyncResolution(
                action=SyncAction.FAILED,
                message=f"Resolution failed: {e}"
            )
    
    def _execute_discover_and_sync(self, drift_event: DriftEvent) -> SyncResolution:
        """Execute discovery and sync operation"""
        
        try:
            print(f"\\n🔍 RUNNING TARGETED CONFIGURATION DISCOVERY")
            print("="*60)
            print(f"Device: {drift_event.device_name}")
            
            # Determine discovery scope
            if drift_event.interface_name:
                # Targeted interface discovery
                base_interface = drift_event.interface_name.split('.')[0]
                print(f"Scope: Interface pattern '{base_interface}*'")
                
                discovered_configs = self.targeted_discovery.discover_interface_vlan_configurations(
                    drift_event.device_name, base_interface
                )
            else:
                # General interface discovery
                print(f"Scope: All interface VLAN configurations")
                
                discovered_configs = self.targeted_discovery.discover_interface_vlan_configurations(
                    drift_event.device_name
                )
            
            if discovered_configs:
                print(f"\\n✅ DISCOVERED CONFIGURATIONS:")
                print(f"Found {len(discovered_configs)} interface configurations")
                
                for config in discovered_configs[:5]:  # Show first 5
                    print(f"   • {config.interface_name} (VLAN {config.vlan_id}) - {config.admin_status}/{config.oper_status}")
                
                if len(discovered_configs) > 5:
                    print(f"   ... and {len(discovered_configs) - 5} more configurations")
                
                # Update database if available - ENHANCED for bridge domain context
                if self.database_available and self.database_updater:
                    print(f"\\n📊 UPDATING DATABASE WITH BRIDGE DOMAIN CONTEXT...")
                    
                    # Step 1: Update interface_discovery table
                    sync_result = self.database_updater.update_database_with_discovered_configs(discovered_configs)
                    
                    if sync_result.success:
                        print(f"✅ Interface discovery table updated")
                        print(f"   • Updated: {sync_result.updated_count} configurations")
                        print(f"   • Added: {sync_result.added_count} new configurations")
                        
                        # Step 2: Update bridge domain discovery_data JSON (CRITICAL FIX for BD Editor)
                        try:
                            from .db_population_adapter import BridgeDomainDatabasePopulationAdapter
                            
                            # Infer bridge domain name from drift context
                            bd_name = self._infer_bridge_domain_from_drift_event(drift_event)
                            if bd_name:
                                print(f"   🔗 Updating bridge domain: {bd_name}")
                                
                                # Update bridge domain discovery_data JSON for BD Editor
                                db_adapter = BridgeDomainDatabasePopulationAdapter()
                                
                                for interface_config in discovered_configs:
                                    bd_update_success = db_adapter.update_bridge_domain_discovery_data(bd_name, interface_config)
                                    
                                    if bd_update_success:
                                        print(f"   ✅ BD Editor data updated for: {interface_config.interface_name}")
                                    else:
                                        print(f"   ⚠️  BD Editor data update failed for: {interface_config.interface_name}")
                                
                                print(f"✅ Bridge domain discovery_data updated")
                                print(f"   • BD Editor will now show newly discovered interfaces")
                                print(f"   • User-Editable Endpoints count will increase")
                                
                            else:
                                print(f"⚠️  Could not determine bridge domain context")
                                
                        except ImportError:
                            print(f"⚠️  Bridge domain population adapter not available")
                        except Exception as e:
                            print(f"⚠️  Bridge domain update failed: {e}")
                        
                        return SyncResolution(
                            action=SyncAction.SYNCED,
                            message=f"Discovered and synced {len(discovered_configs)} configurations with BD context",
                            discovered_configs=discovered_configs,
                            sync_result=sync_result
                        )
                    else:
                        print(f"❌ Database update failed: {sync_result.error_message}")
                        return SyncResolution(
                            action=SyncAction.FAILED,
                            message=f"Discovery succeeded but database update failed: {sync_result.error_message}",
                            discovered_configs=discovered_configs
                        )
                else:
                    print(f"⚠️  Database updater not available - configs discovered but not synced")
                    return SyncResolution(
                        action=SyncAction.FAILED,
                        message="Discovery succeeded but database updater not available",
                        discovered_configs=discovered_configs
                    )
            else:
                print(f"❌ No configurations discovered")
                return SyncResolution(
                    action=SyncAction.FAILED,
                    message="No configurations discovered on device"
                )
                
        except Exception as e:
            logger.error(f"Discover and sync failed: {e}")
            return SyncResolution(
                action=SyncAction.FAILED,
                message=f"Discovery and sync failed: {e}"
            )
    
    def resolve_drift_automatic(self, drift_event: DriftEvent, policy: str = "conservative") -> SyncResolution:
        """Automatic drift resolution based on policies"""
        
        try:
            if policy == "conservative":
                # Conservative: Always sync database with reality
                return self._execute_discover_and_sync(drift_event)
            elif policy == "permissive":
                # Permissive: Skip conflicts and continue
                return SyncResolution(
                    action=SyncAction.SKIP,
                    message="Automatic resolution: skipped conflicting interface"
                )
            elif policy == "aggressive":
                # Aggressive: Override existing configurations
                return SyncResolution(
                    action=SyncAction.OVERRIDE,
                    message="Automatic resolution: overriding existing configuration"
                )
            else:
                return SyncResolution(
                    action=SyncAction.FAILED,
                    message=f"Unknown automatic resolution policy: {policy}"
                )
                
        except Exception as e:
            logger.error(f"Automatic drift resolution failed: {e}")
            return SyncResolution(
                action=SyncAction.FAILED,
                message=f"Automatic resolution failed: {e}"
            )
    
    def _infer_bridge_domain_from_drift_event(self, drift_event: DriftEvent) -> Optional[str]:
        """Infer bridge domain name from drift event context"""
        
        try:
            # Check if interface name has VLAN that matches BD pattern
            if drift_event.interface_name and '.' in drift_event.interface_name:
                vlan_part = drift_event.interface_name.split('.')[-1]
                if vlan_part.isdigit():
                    vlan_id = int(vlan_part)
                    
                    # Look for bridge domain with matching VLAN
                    # For now, use a simple pattern - could be enhanced
                    potential_bd_names = [
                        f"g_visaev_v{vlan_id}",  # Common pattern
                        f"l_user_v{vlan_id}",   # Local pattern
                    ]
                    
                    # In a real implementation, we'd query the database
                    # For drift resolution, we often have the BD name in the drift context
                    return f"g_visaev_v{vlan_id}"  # Simplified for now
            
            return None
            
        except Exception as e:
            logger.error(f"Error inferring bridge domain from drift event: {e}")
            return None


# Convenience functions
def resolve_drift_interactive(drift_event: DriftEvent) -> SyncResolution:
    """Convenience function for interactive drift resolution"""
    resolver = ConfigurationSyncResolver()
    return resolver.resolve_drift_interactive(drift_event)


def resolve_drift_automatic(drift_event: DriftEvent, policy: str = "conservative") -> SyncResolution:
    """Convenience function for automatic drift resolution"""
    resolver = ConfigurationSyncResolver()
    return resolver.resolve_drift_automatic(drift_event, policy)
