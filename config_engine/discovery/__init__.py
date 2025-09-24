#!/usr/bin/env python3
"""
Unified Discovery System Entry Point
===================================

Consolidated discovery namespace providing clean access to all discovery functionality.

Architecture:
- simplified/  : Production-ready 3-step workflow (primary)
- advanced/    : Component-based advanced discovery (secondary)  
- legacy/      : Archived legacy systems (compatibility)
"""

# Production discovery system (recommended)
from .simplified.simplified_bridge_domain_discovery import (
    run_simplified_discovery,
    SimplifiedBridgeDomainDiscovery,
    DiscoveryResults
)
from .simplified.enhanced_cli_display import run_enhanced_simplified_discovery_display
from .simplified.cli_integration import SimplifiedDiscoveryCLI
from .simplified.data_sync_manager import DataSyncManager

# Advanced discovery system (for complex analysis)
try:
    from .advanced.components.discovery_orchestrator import (
        EnhancedDiscoveryOrchestrator,
        run_refactored_enhanced_discovery
    )
except ImportError:
    # Advanced discovery not available
    def run_refactored_enhanced_discovery(**kwargs):
        print("⚠️ Advanced discovery not available")
        print("💡 Use simplified discovery instead")
        return run_simplified_discovery(**kwargs)
    
    class EnhancedDiscoveryOrchestrator:
        def run_enhanced_discovery(self, **kwargs):
            return run_refactored_enhanced_discovery(**kwargs)

# Legacy discovery system (compatibility)
from .legacy.bridge_domain_discovery import BridgeDomainDiscovery

try:
    from .legacy.enhanced_bridge_domain_discovery import EnhancedBridgeDomainDiscovery as LegacyEnhancedDiscovery
except ImportError:
    # Legacy enhanced discovery has broken dependencies, use simplified as fallback
    print("⚠️ Legacy enhanced discovery not available (broken dependencies)")
    LegacyEnhancedDiscovery = None

# Unified discovery function
def run_discovery(mode='simplified', **kwargs):
    """
    Unified discovery entry point with multiple modes
    
    Args:
        mode: 'simplified' (production), 'advanced' (complex), 'legacy' (compatibility)
        **kwargs: Additional arguments passed to discovery system
    
    Returns:
        Discovery results in appropriate format
    """
    if mode == 'simplified':
        return run_simplified_discovery(**kwargs)
    elif mode == 'advanced':
        orchestrator = EnhancedDiscoveryOrchestrator()
        return orchestrator.run_enhanced_discovery(**kwargs)
    elif mode == 'legacy':
        discovery = BridgeDomainDiscovery()
        return discovery.run_discovery(**kwargs)
    else:
        raise ValueError(f"Unknown discovery mode: {mode}. Use 'simplified', 'advanced', or 'legacy'")

# Enhanced CLI entry point
def run_discovery_cli(mode='simplified'):
    """
    Run discovery CLI interface
    
    Args:
        mode: 'simplified' (recommended) or 'advanced'
    """
    if mode == 'simplified':
        return run_enhanced_simplified_discovery_display()
    elif mode == 'advanced':
        # Advanced CLI not implemented yet
        print("⚠️ Advanced discovery CLI not yet implemented")
        print("💡 Use simplified discovery CLI for now")
        return run_enhanced_simplified_discovery_display()
    else:
        raise ValueError(f"Unknown CLI mode: {mode}")

# Default exports (primary interface)
__all__ = [
    # Primary discovery interface
    'run_discovery',
    'run_discovery_cli',
    'run_simplified_discovery',
    'run_enhanced_simplified_discovery_display',
    
    # Discovery classes
    'SimplifiedBridgeDomainDiscovery',
    'SimplifiedDiscoveryCLI',
    'DataSyncManager',
    
    # Advanced discovery
    'EnhancedDiscoveryOrchestrator',
    'run_refactored_enhanced_discovery',
    
    # Legacy compatibility
    'BridgeDomainDiscovery',
    'LegacyEnhancedDiscovery',
    
    # Data structures
    'DiscoveryResults'
]

# Validation on import
def _validate_discovery_systems():
    """Validate that all discovery systems are accessible"""
    try:
        # Test simplified discovery
        from .simplified.simplified_bridge_domain_discovery import SimplifiedBridgeDomainDiscovery
        
        # Test advanced discovery
        from .advanced.components.discovery_orchestrator import EnhancedDiscoveryOrchestrator
        
        # Test legacy discovery
        from .legacy.bridge_domain_discovery import BridgeDomainDiscovery
        
        print("✅ All discovery systems validated successfully")
        return True
    except ImportError as e:
        print(f"❌ Discovery system validation failed: {e}")
        return False

# Auto-validate on import
_validate_discovery_systems()
