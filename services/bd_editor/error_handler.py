#!/usr/bin/env python3
"""
BD Editor Error Handler

Comprehensive error handling system for BD editor operations,
providing graceful failure recovery and user-friendly error messages.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from .data_models import BDEditorException, BDEditorExitException, ValidationError

logger = logging.getLogger(__name__)


class BDEditorErrorHandler:
    """Comprehensive error handling for BD editor"""
    
    def __init__(self):
        self.error_handlers = {
            'smart_selection_failure': self.handle_smart_selection_failure,
            'unknown_bd_type': self.handle_unknown_bd_type,
            'corrupted_bd_data': self.handle_corrupted_bd_data,
            'validation_failure': self.handle_validation_failure,
            'template_generation_failure': self.handle_template_generation_failure,
            'session_failure': self.handle_session_failure,
            'integration_failure': self.handle_integration_failure
        }
    
    def handle_error(self, error_type: str, error: Exception, context: Dict = None) -> Any:
        """Handle specific error type with context"""
        
        try:
            handler = self.error_handlers.get(error_type)
            
            if handler:
                logger.info(f"Handling error type '{error_type}': {error}")
                return handler(error, context or {})
            else:
                logger.error(f"No handler for error type '{error_type}': {error}")
                return self._handle_generic_error(error, context or {})
                
        except Exception as e:
            logger.error(f"Error in error handler for '{error_type}': {e}")
            return self._handle_critical_error(e)
    
    def handle_smart_selection_failure(self, error: Exception, context: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Handle smart interface selection failure"""
        
        print(f"\n⚠️  Smart interface selection failed: {error}")
        print("💡 Available fallback options:")
        print("1. 🔄 Retry smart selection")
        print("2. 📝 Manual interface entry")
        print("3. ❌ Cancel interface addition")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                # Retry smart selection
                try:
                    from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
                    return enhanced_interface_selection_for_editor()
                except Exception as retry_error:
                    print(f"❌ Retry failed: {retry_error}")
                    return self._manual_interface_fallback()
            elif choice == '2':
                return self._manual_interface_fallback()
            else:
                print("❌ Interface addition cancelled")
                return None, None
                
        except KeyboardInterrupt:
            print("❌ Interface selection cancelled")
            return None, None
    
    def handle_unknown_bd_type(self, error: Exception, context: Dict) -> 'MenuAdapter':
        """Handle unknown or corrupted BD type"""
        
        bridge_domain = context.get('bridge_domain', {})
        session = context.get('session', {})
        
        bd_type = bridge_domain.get('dnaas_type', 'None')
        
        print(f"\n⚠️  Unknown BD type: {bd_type}")
        print("💡 Available options:")
        print("1. 🔍 Analyze BD configuration and suggest type")
        print("2. 🛠️  Use generic editing mode")
        print("3. ❌ Exit editor (recommend BD review)")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                return self._analyze_and_suggest_type(bridge_domain, session)
            elif choice == '2':
                from .menu_adapters import GenericMenuAdapter
                from .data_models import InterfaceAnalysis
                print("💡 Using generic editing mode with limited functionality")
                return GenericMenuAdapter(bridge_domain, session, InterfaceAnalysis())
            else:
                print("❌ Exiting editor due to unknown BD type")
                raise BDEditorExitException("User chose to exit due to unknown BD type")
                
        except KeyboardInterrupt:
            print("❌ Editor cancelled")
            raise BDEditorExitException("User cancelled due to unknown BD type")
    
    def handle_corrupted_bd_data(self, error: Exception, context: Dict) -> bool:
        """Handle corrupted or incomplete BD data"""
        
        bridge_domain = context.get('bridge_domain', {})
        
        print(f"\n❌ BD data appears corrupted: {error}")
        print("💡 Available options:")
        print("1. 🔄 Reload BD from database")
        print("2. 🛠️  Continue with limited functionality")
        print("3. ❌ Exit editor")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                return self._reload_bd_from_database(bridge_domain.get('name', ''))
            elif choice == '2':
                print("⚠️  Continuing with limited functionality")
                print("💡 Some features may not work correctly")
                return True
            else:
                print("❌ Exiting editor due to corrupted data")
                return False
                
        except KeyboardInterrupt:
            print("❌ Editor cancelled")
            return False
    
    def handle_validation_failure(self, error: Exception, context: Dict) -> bool:
        """Handle validation failures"""
        
        validation_result = context.get('validation_result')
        change = context.get('change', {})
        
        print(f"\n❌ Validation failed for change: {change.get('description', 'Unknown change')}")
        
        if validation_result:
            if validation_result.errors:
                print("🔴 Errors:")
                for error in validation_result.errors:
                    print(f"   • {error}")
            
            if validation_result.warnings:
                print("🟡 Warnings:")
                for warning in validation_result.warnings:
                    print(f"   • {warning}")
        
        print("💡 Available options:")
        print("1. ✏️  Modify change to fix validation issues")
        print("2. ⚠️  Proceed anyway (ignore warnings only)")
        print("3. ❌ Cancel change")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                print("🚧 Change modification - Coming in advanced features")
                return False
            elif choice == '2':
                if validation_result and validation_result.errors:
                    print("❌ Cannot proceed - validation has errors")
                    return False
                else:
                    print("⚠️  Proceeding despite warnings")
                    return True
            else:
                print("❌ Change cancelled due to validation failure")
                return False
                
        except KeyboardInterrupt:
            print("❌ Change cancelled")
            return False
    
    def handle_template_generation_failure(self, error: Exception, context: Dict) -> List[str]:
        """Handle CLI template generation failure"""
        
        bd_type = context.get('bd_type', 'unknown')
        action = context.get('action', 'unknown')
        
        print(f"\n❌ Template generation failed for {bd_type} {action}: {error}")
        print("💡 Available options:")
        print("1. 📝 Enter CLI commands manually")
        print("2. 🔄 Retry with different parameters")
        print("3. ❌ Cancel operation")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                return self._manual_cli_input()
            elif choice == '2':
                print("🚧 Parameter retry - Coming in advanced features")
                return []
            else:
                print("❌ Operation cancelled")
                return []
                
        except KeyboardInterrupt:
            print("❌ Operation cancelled")
            return []
    
    def handle_session_failure(self, error: Exception, context: Dict) -> bool:
        """Handle session management failures"""
        
        print(f"\n❌ Session management error: {error}")
        print("💡 Available options:")
        print("1. 💾 Save current work to temporary file")
        print("2. 🔄 Retry session operation")
        print("3. ❌ Continue without session persistence")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                return self._save_to_temporary_file(context.get('session', {}))
            elif choice == '2':
                print("🔄 Retrying session operation...")
                return True
            else:
                print("⚠️  Continuing without session persistence")
                return True
                
        except KeyboardInterrupt:
            print("❌ Session handling cancelled")
            return False
    
    def handle_integration_failure(self, error: Exception, context: Dict) -> Any:
        """Handle external integration failures"""
        
        integration_name = context.get('integration_name', 'unknown')
        
        print(f"\n⚠️  Integration '{integration_name}' failed: {error}")
        print("💡 Available options:")
        print("1. 🔄 Retry integration")
        print("2. 💡 Use fallback method")
        print("3. ❌ Continue without this integration")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                print("🔄 Retrying integration...")
                return 'retry'
            elif choice == '2':
                print("💡 Using fallback method")
                return 'fallback'
            else:
                print("⚠️  Continuing without integration")
                return 'skip'
                
        except KeyboardInterrupt:
            print("❌ Integration handling cancelled")
            return 'skip'
    
    def _manual_interface_fallback(self) -> Tuple[Optional[str], Optional[str]]:
        """Manual interface input fallback"""
        
        print("\n📝 Manual Interface Entry:")
        print("💡 Enter customer-facing interface only (ge100-0/0/*)")
        
        try:
            device = input("Device name: ").strip()
            if not device:
                return None, None
            
            interface = input("Interface name: ").strip()
            if not interface:
                return None, None
            
            # Basic validation
            from .interface_analyzer import BDInterfaceAnalyzer
            analyzer = BDInterfaceAnalyzer()
            
            if analyzer.is_infrastructure_interface(interface, ''):
                print(f"❌ {interface} is an infrastructure interface")
                print("🛡️  Please enter a customer-facing interface")
                return None, None
            
            return device, interface
            
        except KeyboardInterrupt:
            return None, None
    
    def _analyze_and_suggest_type(self, bridge_domain: Dict, session: Dict) -> 'MenuAdapter':
        """Analyze BD configuration and suggest type"""
        
        print("\n🔍 Analyzing BD configuration...")
        
        # Simple BD type analysis based on interface patterns
        devices = bridge_domain.get('devices', {})
        has_manipulation = False
        has_double_tags = False
        
        for device_name, device_info in devices.items():
            interfaces = device_info.get('interfaces', [])
            for interface in interfaces:
                config = interface.get('raw_cli_config', [])
                config_str = ' '.join(config) if config else ''
                
                if 'vlan-manipulation' in config_str:
                    has_manipulation = True
                if 'outer-tag' in config_str and 'inner-tag' in config_str:
                    has_double_tags = True
        
        # Suggest type
        if has_double_tags:
            suggested_type = 'DNAAS_TYPE_1_DOUBLE_TAGGED'
            suggested_name = 'Double-Tagged'
        elif has_manipulation:
            suggested_type = 'DNAAS_TYPE_2A_QINQ_SINGLE_BD'
            suggested_name = 'QinQ Single BD'
        else:
            suggested_type = 'DNAAS_TYPE_4A_SINGLE_TAGGED'
            suggested_name = 'Single-Tagged'
        
        print(f"💡 Suggested BD type: {suggested_name} ({suggested_type})")
        
        confirm = input("Use this suggested type? (Y/n): ").strip().lower()
        if confirm != 'n':
            # Update BD type and create appropriate menu
            bridge_domain['dnaas_type'] = suggested_type
            
            from .menu_system import IntelligentBDEditorMenu
            menu_system = IntelligentBDEditorMenu()
            return menu_system.create_menu_for_bd(bridge_domain, session)
        else:
            # Use generic menu
            from .menu_adapters import GenericMenuAdapter
            from .data_models import InterfaceAnalysis
            return GenericMenuAdapter(bridge_domain, session, InterfaceAnalysis())
    
    def _reload_bd_from_database(self, bd_name: str) -> bool:
        """Reload BD data from database"""
        
        print(f"🔄 Reloading BD {bd_name} from database...")
        
        try:
            # This would reload BD data from database
            # Implementation depends on database manager integration
            print("🚧 BD reload - Requires database integration")
            return True
            
        except Exception as e:
            print(f"❌ Failed to reload BD: {e}")
            return False
    
    def _manual_cli_input(self) -> List[str]:
        """Manual CLI command input"""
        
        print("\n📝 Manual CLI Command Entry:")
        print("💡 Enter CLI commands one per line (empty line to finish)")
        
        commands = []
        
        try:
            while True:
                command = input("CLI command: ").strip()
                if not command:
                    break
                commands.append(command)
            
            print(f"✅ Entered {len(commands)} manual commands")
            return commands
            
        except KeyboardInterrupt:
            print("❌ Manual CLI input cancelled")
            return []
    
    def _save_to_temporary_file(self, session: Dict) -> bool:
        """Save session to temporary file"""
        
        try:
            import os
            import json
            from datetime import datetime
            
            temp_dir = "instance/bd_editor_temp/"
            os.makedirs(temp_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = f"{temp_dir}/session_backup_{timestamp}.json"
            
            with open(temp_file, 'w') as f:
                json.dump(session, f, indent=2, default=str)
            
            print(f"✅ Session saved to temporary file: {temp_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save to temporary file: {e}")
            return False
    
    def _handle_generic_error(self, error: Exception, context: Dict) -> Any:
        """Handle generic errors"""
        
        print(f"\n❌ Unexpected error: {error}")
        print("💡 Available options:")
        print("1. 🔄 Retry operation")
        print("2. 📝 Report issue and continue")
        print("3. ❌ Exit editor")
        
        try:
            choice = input("Select option [1-3]: ").strip()
            
            if choice == '1':
                print("🔄 Retrying operation...")
                return 'retry'
            elif choice == '2':
                print("📝 Issue noted - continuing with limited functionality")
                logger.error(f"User-reported issue: {error}")
                return 'continue'
            else:
                print("❌ Exiting editor due to error")
                raise BDEditorExitException(f"User exit due to error: {error}")
                
        except KeyboardInterrupt:
            print("❌ Editor cancelled")
            raise BDEditorExitException("User cancelled due to error")
    
    def _handle_critical_error(self, error: Exception) -> Any:
        """Handle critical errors that prevent operation"""
        
        print(f"\n🚨 CRITICAL ERROR: {error}")
        print("❌ BD editor cannot continue safely")
        print("💡 Please report this issue to system administrators")
        
        logger.critical(f"Critical BD editor error: {error}")
        
        raise BDEditorExitException(f"Critical error: {error}")


class IntegrationFallbackManager:
    """Handle integration failures gracefully"""
    
    def __init__(self):
        self.fallback_strategies = {
            'interface_discovery': self._interface_discovery_fallback,
            'smart_selection': self._smart_selection_fallback,
            'database_integration': self._database_fallback,
            'performance_monitoring': self._performance_monitoring_fallback
        }
        self.integration_status = {}
    
    def check_integration_health(self) -> Dict[str, bool]:
        """Check health of all integrations"""
        
        health_status = {}
        
        # Interface Discovery System
        try:
            from services.interface_discovery import SimpleInterfaceDiscovery
            discovery = SimpleInterfaceDiscovery()
            device_counts = discovery.get_devices_with_interface_counts()
            health_status['interface_discovery'] = len(device_counts) > 0
        except Exception as e:
            health_status['interface_discovery'] = False
        
        # Smart Interface Selection
        try:
            from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
            health_status['smart_selection'] = True
        except Exception as e:
            health_status['smart_selection'] = False
        
        # Database Integration
        try:
            from database_manager import DatabaseManager
            health_status['database_integration'] = True
        except Exception as e:
            health_status['database_integration'] = False
        
        self.integration_status.update(health_status)
        return health_status
    
    def handle_integration_failure(self, integration_name: str, error: Exception, context: Dict = None) -> Any:
        """Handle specific integration failure"""
        
        logger.warning(f"Integration '{integration_name}' failed: {error}")
        print(f"⚠️  Integration '{integration_name}' failed: {error}")
        
        fallback = self.fallback_strategies.get(integration_name)
        if fallback:
            print(f"💡 Using fallback strategy for {integration_name}")
            return fallback(error, context or {})
        else:
            print(f"❌ No fallback available for {integration_name}")
            from .data_models import IntegrationFailureError
            raise IntegrationFailureError(f"Critical integration {integration_name} failed: {error}")
    
    def _interface_discovery_fallback(self, error: Exception, context: Dict) -> List[Dict]:
        """Fallback when interface discovery is unavailable"""
        
        print("💡 Interface discovery unavailable - using BD data only")
        print("⚠️  Real-time interface status not available")
        
        # Return empty list, BD editor will use BD data only
        return []
    
    def _smart_selection_fallback(self, error: Exception, context: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Fallback when smart selection is unavailable"""
        
        print("💡 Smart selection unavailable - using manual input")
        
        try:
            device = input("Enter device name: ").strip()
            interface = input("Enter interface name: ").strip()
            
            return (device, interface) if device and interface else (None, None)
            
        except KeyboardInterrupt:
            return None, None
    
    def _database_fallback(self, error: Exception, context: Dict) -> Dict:
        """Fallback when database integration fails"""
        
        print("❌ Database integration failed - cannot continue")
        print("🛡️  BD editor requires database access for safe operation")
        
        from .data_models import CriticalIntegrationError
        raise CriticalIntegrationError("Database integration is required for BD editor")
    
    def _performance_monitoring_fallback(self, error: Exception, context: Dict) -> None:
        """Fallback when performance monitoring fails"""
        
        print("💡 Performance monitoring unavailable - continuing without metrics")
        logger.warning("Performance monitoring disabled due to error")
        
        # Performance monitoring is optional, continue without it
        return None


# Convenience functions
def handle_bd_editor_error(error_type: str, error: Exception, context: Dict = None) -> Any:
    """Convenience function to handle BD editor errors"""
    handler = BDEditorErrorHandler()
    return handler.handle_error(error_type, error, context)


def handle_integration_failure(integration_name: str, error: Exception, context: Dict = None) -> Any:
    """Convenience function to handle integration failures"""
    fallback_manager = IntegrationFallbackManager()
    return fallback_manager.handle_integration_failure(integration_name, error, context)
