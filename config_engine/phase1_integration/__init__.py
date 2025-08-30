#!/usr/bin/env python3
"""
Phase 1 Integration Package
Provides seamless integration between legacy CLI and Phase 1 data structures
"""

# Core integration components
from .data_transformers import DataTransformer, LegacyConfigAdapter
from .cli_wrapper import Phase1CLIWrapper, Phase1MenuSystemWrapper
from .legacy_adapter import (
    LegacyFunctionAdapter, phase1_enhanced, BackwardCompatibilityManager,
    compatibility_manager
)

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Phase 1 integration layer for CLI compatibility"

# Public API
__all__ = [
    # Core transformers
    'DataTransformer',
    'LegacyConfigAdapter',
    
    # CLI wrappers
    'Phase1CLIWrapper',
    'Phase1MenuSystemWrapper',
    
    # Legacy adapters
    'LegacyFunctionAdapter',
    'phase1_enhanced',
    'BackwardCompatibilityManager',
    'compatibility_manager',
    
    # Metadata
    '__version__',
    '__author__',
    '__description__'
]

# Convenience functions for easy integration
def enable_phase1_integration():
    """Enable Phase 1 integration system-wide"""
    compatibility_manager.enable_phase1_integration()
    print("✅ Phase 1 integration enabled!")
    print("🚀 CLI functions now use advanced validation and topology insights")

def disable_phase1_integration():
    """Disable Phase 1 integration (fall back to legacy)"""
    compatibility_manager.disable_phase1_integration()
    print("⚠️ Phase 1 integration disabled")
    print("🔄 Using legacy CLI functions")

def get_integration_status():
    """Get current integration status"""
    report = compatibility_manager.get_compatibility_report()
    
    print("\n📊 Phase 1 Integration Status:")
    print("─" * 35)
    print(f"Status: {'🟢 ACTIVE' if report['phase1_enabled'] else '🔴 DISABLED'}")
    print(f"Data Transformer: {'✅' if report['adapter_available'] else '❌'}")
    print(f"CLI Wrapper: {'✅' if report['cli_wrapper_available'] else '❌'}")
    print(f"Menu Wrapper: {'✅' if report['menu_wrapper_available'] else '❌'}")
    
    return report

def create_enhanced_menu_system():
    """Create an enhanced menu system with Phase 1 integration"""
    if compatibility_manager.is_phase1_enabled():
        return Phase1MenuSystemWrapper()
    else:
        # Fall back to original
        from config_engine.enhanced_menu_system import EnhancedMenuSystem
        return EnhancedMenuSystem()

def create_enhanced_cli_wrapper():
    """Create a CLI wrapper with Phase 1 integration"""
    return Phase1CLIWrapper()

def validate_configuration(service_name: str, vlan_id: int,
                         source_device: str, source_interface: str,
                         destinations: list) -> dict:
    """
    Validate configuration using Phase 1 framework.
    
    Args:
        service_name: Service identifier
        vlan_id: VLAN ID
        source_device: Source device name
        source_interface: Source interface name
        destinations: List of destination dictionaries
        
    Returns:
        Validation report dictionary
    """
    cli_wrapper = Phase1CLIWrapper()
    return cli_wrapper.get_validation_report(
        service_name, vlan_id, source_device, source_interface, destinations
    )

# Add convenience functions to __all__
__all__.extend([
    'enable_phase1_integration',
    'disable_phase1_integration', 
    'get_integration_status',
    'create_enhanced_menu_system',
    'create_enhanced_cli_wrapper',
    'validate_configuration'
])

# Initialize integration on import
print("🚀 Phase 1 Integration Package loaded")
print("💡 Use enable_phase1_integration() to activate enhanced CLI features")
