#!/usr/bin/env python3
"""
BD Editor Integration Fallbacks

Comprehensive fallback management for external system integration failures,
ensuring graceful degradation when dependencies are unavailable.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from .data_models import IntegrationFailureError, CriticalIntegrationError

logger = logging.getLogger(__name__)


class IntegrationFallbackManager:
    """Handle integration failures gracefully with comprehensive fallback strategies"""
    
    def __init__(self):
        self.fallback_strategies = {
            'interface_discovery': self._interface_discovery_fallback,
            'smart_selection': self._smart_selection_fallback,
            'database_integration': self._database_fallback,
            'performance_monitoring': self._performance_monitoring_fallback,
            'configuration_preview': self._configuration_preview_fallback,
            'validation_system': self._validation_system_fallback,
            'session_management': self._session_management_fallback
        }
        
        self.integration_status = {}
    
    def check_integration_health(self) -> Dict[str, bool]:
        """Check health of all integrations"""
        
        health_status = {}
        
        # Interface Discovery System
        try:
            from services.interface_discovery import SimpleInterfaceDiscovery
            discovery = SimpleInterfaceDiscovery()
            # Test basic functionality
            device_counts = discovery.get_devices_with_interface_counts()
            health_status['interface_discovery'] = len(device_counts) > 0
        except Exception as e:
            health_status['interface_discovery'] = False
            logger.debug(f"Interface discovery health check failed: {e}")
        
        # Smart Interface Selection
        try:
            from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
            health_status['smart_selection'] = True
        except Exception as e:
            health_status['smart_selection'] = False
            logger.debug(f"Smart selection health check failed: {e}")
        
        # Database Integration
        try:
            from database_manager import DatabaseManager
            health_status['database_integration'] = True
        except Exception as e:
            health_status['database_integration'] = False
            logger.debug(f"Database integration health check failed: {e}")
        
        # Update internal status
        self.integration_status.update(health_status)
        
        return health_status
    
    def display_integration_status(self):
        """Display current integration status"""
        
        print(f"\n🔗 INTEGRATION STATUS")
        print("="*40)
        
        health_status = self.check_integration_health()
        
        for integration, is_healthy in health_status.items():
            status_icon = "✅" if is_healthy else "❌"
            fallback_available = integration in self.fallback_strategies
            fallback_icon = "🛡️" if fallback_available else "⚠️"
            
            print(f"{status_icon} {integration}: {'Available' if is_healthy else 'Failed'} {fallback_icon}")
        
        # Show fallback status
        failed_integrations = [name for name, status in health_status.items() if not status]
        if failed_integrations:
            print(f"\n💡 Fallback strategies active for: {', '.join(failed_integrations)}")
        else:
            print(f"\n✅ All integrations healthy")
    
    def handle_integration_failure(self, integration_name: str, error: Exception, context: Dict = None) -> Any:
        """Handle specific integration failure with appropriate fallback"""
        
        logger.warning(f"Integration '{integration_name}' failed: {error}")
        print(f"⚠️  Integration '{integration_name}' failed: {error}")
        
        # Mark integration as failed
        self.integration_status[integration_name] = False
        
        fallback = self.fallback_strategies.get(integration_name)
        if fallback:
            print(f"💡 Using fallback strategy for {integration_name}")
            try:
                return fallback(error, context or {})
            except Exception as fallback_error:
                logger.error(f"Fallback strategy failed for {integration_name}: {fallback_error}")
                return self._handle_fallback_failure(integration_name, fallback_error)
        else:
            print(f"❌ No fallback available for {integration_name}")
            raise IntegrationFailureError(f"Critical integration {integration_name} failed: {error}")
    
    def check_integration_health(self) -> Dict[str, bool]:
        """Check health of all integrations"""
        
        health_status = {}
        
        # Interface Discovery System
        try:
            from services.interface_discovery import SimpleInterfaceDiscovery
            discovery = SimpleInterfaceDiscovery()
            # Test basic functionality
            device_counts = discovery.get_devices_with_interface_counts()
            health_status['interface_discovery'] = len(device_counts) > 0
        except Exception as e:
            health_status['interface_discovery'] = False
            logger.debug(f"Interface discovery health check failed: {e}")
        
        # Smart Interface Selection
        try:
            from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
            health_status['smart_selection'] = True
        except Exception as e:
            health_status['smart_selection'] = False
            logger.debug(f"Smart selection health check failed: {e}")
        
        # Database Integration
        try:
            from database_manager import DatabaseManager
            health_status['database_integration'] = True
        except Exception as e:
            health_status['database_integration'] = False
            logger.debug(f"Database integration health check failed: {e}")
        
        # Update internal status
        self.integration_status.update(health_status)
        
        return health_status
    
    def display_integration_status(self):
        """Display current integration status"""
        
        print(f"\n🔗 INTEGRATION STATUS")
        print("="*40)
        
        health_status = self.check_integration_health()
        
        for integration, is_healthy in health_status.items():
            status_icon = "✅" if is_healthy else "❌"
            fallback_available = integration in self.fallback_strategies
            fallback_icon = "🛡️" if fallback_available else "⚠️"
            
            print(f"{status_icon} {integration}: {'Available' if is_healthy else 'Failed'} {fallback_icon}")
        
        # Show fallback status
        failed_integrations = [name for name, status in health_status.items() if not status]
        if failed_integrations:
            print(f"\n💡 Fallback strategies active for: {', '.join(failed_integrations)}")
        else:
            print(f"\n✅ All integrations healthy")
    
    def _interface_discovery_fallback(self, error: Exception, context: Dict) -> List[Dict]:
        """Fallback when interface discovery is unavailable"""
        
        print("💡 Interface discovery unavailable - using BD data only")
        print("⚠️  Real-time interface status not available")
        print("🛡️  BD editor will use stored interface data")
        
        # Return empty list, BD editor will use BD data only
        return []
    
    def _smart_selection_fallback(self, error: Exception, context: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Fallback when smart selection is unavailable"""
        
        print("💡 Smart selection unavailable - using manual input")
        print("📝 Please enter device and interface manually")
        
        try:
            device = input("Enter device name: ").strip()
            if not device:
                return None, None
            
            interface = input("Enter interface name: ").strip()
            if not interface:
                return None, None
            
            # Basic validation
            from .interface_analyzer import BDInterfaceAnalyzer
            analyzer = BDInterfaceAnalyzer()
            
            if analyzer.is_infrastructure_interface(interface, ''):
                print(f"⚠️  {interface} appears to be an infrastructure interface")
                confirm = input("Continue anyway? (y/N): ").strip().lower()
                if confirm != 'y':
                    return None, None
            
            return device, interface
            
        except KeyboardInterrupt:
            print("❌ Manual input cancelled")
            return None, None
    
    def _database_fallback(self, error: Exception, context: Dict) -> Any:
        """Fallback when database integration fails"""
        
        print("❌ Database integration failed - cannot continue safely")
        print("🛡️  BD editor requires database access for data integrity")
        print("💡 Please check database connection and try again")
        
        raise CriticalIntegrationError("Database integration is required for BD editor")
    
    def _performance_monitoring_fallback(self, error: Exception, context: Dict) -> None:
        """Fallback when performance monitoring fails"""
        
        print("💡 Performance monitoring unavailable - continuing without metrics")
        print("⚠️  Performance tracking disabled")
        
        logger.warning("Performance monitoring disabled due to error")
        
        # Performance monitoring is optional, continue without it
        return None
    
    def _configuration_preview_fallback(self, error: Exception, context: Dict) -> Dict:
        """Fallback when configuration preview fails"""
        
        print("💡 Configuration preview unavailable - showing basic change summary")
        
        changes = context.get('changes', [])
        
        # Create basic preview
        basic_preview = {
            'success': False,
            'error': str(error),
            'changes_count': len(changes),
            'basic_summary': f"{len(changes)} changes made",
            'fallback_used': True
        }
        
        return basic_preview
    
    def _validation_system_fallback(self, error: Exception, context: Dict) -> bool:
        """Fallback when validation system fails"""
        
        print("💡 Validation system unavailable - using basic safety checks")
        print("⚠️  Advanced validation disabled")
        
        # Perform basic infrastructure protection
        interface_config = context.get('interface_config', {})
        interface = interface_config.get('interface', '')
        
        from .interface_analyzer import BDInterfaceAnalyzer
        analyzer = BDInterfaceAnalyzer()
        
        if analyzer.is_infrastructure_interface(interface, ''):
            print(f"❌ Basic safety check: {interface} is infrastructure interface")
            return False
        
        print("✅ Basic safety check passed")
        return True
    
    def _session_management_fallback(self, error: Exception, context: Dict) -> bool:
        """Fallback when session management fails"""
        
        print("💡 Session management unavailable - using in-memory only")
        print("⚠️  Changes will not persist if editor is interrupted")
        
        # Continue with in-memory session only
        return True
    
    def _handle_fallback_failure(self, integration_name: str, fallback_error: Exception) -> Any:
        """Handle fallback strategy failure"""
        
        print(f"❌ Fallback strategy failed for {integration_name}: {fallback_error}")
        
        # Critical integrations cannot fail
        critical_integrations = ['database_integration']
        
        if integration_name in critical_integrations:
            print(f"🚨 Critical integration {integration_name} cannot be recovered")
            raise CriticalIntegrationError(f"Critical integration {integration_name} failed completely")
        else:
            print(f"⚠️  Non-critical integration {integration_name} will be disabled")
            return None


# Context managers for integration handling
class IntegrationContext:
    """Context manager for handling integration operations"""
    
    def __init__(self, integration_name: str, fallback_manager: IntegrationFallbackManager, context: Dict = None):
        self.integration_name = integration_name
        self.fallback_manager = fallback_manager
        self.context = context or {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Handle integration failure
            try:
                self.fallback_manager.handle_integration_failure(
                    self.integration_name, 
                    exc_val, 
                    self.context
                )
                return True  # Suppress exception, fallback handled it
            except CriticalIntegrationError:
                return False  # Let critical errors propagate
            except Exception as fallback_error:
                logger.error(f"Fallback handling failed: {fallback_error}")
                return False


# Convenience functions
def create_integration_context(integration_name: str, context: Dict = None) -> IntegrationContext:
    """Create integration context manager"""
    fallback_manager = IntegrationFallbackManager()
    return IntegrationContext(integration_name, fallback_manager, context)


def handle_integration_error(integration_name: str, error: Exception, context: Dict = None) -> Any:
    """Convenience function to handle integration errors"""
    fallback_manager = IntegrationFallbackManager()
    return fallback_manager.handle_integration_failure(integration_name, error, context)
