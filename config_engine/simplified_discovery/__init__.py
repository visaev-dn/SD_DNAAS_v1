#!/usr/bin/env python3
"""
COMPATIBILITY LAYER - Simplified Discovery
==========================================

This file provides backward compatibility for existing imports while the system
transitions to the new unified discovery namespace.

ALL IMPORTS ARE REDIRECTED TO: config_engine.discovery.simplified.*

This compatibility layer will be removed after all imports are updated.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "config_engine.simplified_discovery is deprecated. "
    "Use config_engine.discovery.simplified instead.",
    DeprecationWarning,
    stacklevel=2
)

# Redirect all imports to new location
from ..discovery.simplified.simplified_bridge_domain_discovery import (
    run_simplified_discovery,
    SimplifiedBridgeDomainDiscovery,
    DiscoveryResults
)
from ..discovery.simplified.enhanced_cli_display import run_enhanced_simplified_discovery_display
from ..discovery.simplified.cli_integration import SimplifiedDiscoveryCLI
from ..discovery.simplified.data_sync_manager import DataSyncManager
from ..discovery.simplified.data_structures import (
    RawBridgeDomain,
    ProcessedBridgeDomain,
    ConsolidatedBridgeDomain,
    InterfaceInfo,
    VLANConfiguration,
    LoadedData,
    ValidationResult
)

# Enhanced database menu function (for main.py compatibility)
def run_enhanced_database_menu():
    """Compatibility function for enhanced database menu"""
    from ..discovery.simplified.cli_integration import SimplifiedDiscoveryCLI
    cli = SimplifiedDiscoveryCLI()
    cli.show_discovery_menu()

# Export all original functions for backward compatibility
__all__ = [
    'run_simplified_discovery',
    'SimplifiedBridgeDomainDiscovery',
    'DiscoveryResults',
    'run_enhanced_simplified_discovery_display',
    'SimplifiedDiscoveryCLI',
    'DataSyncManager',
    'run_enhanced_database_menu',
    'RawBridgeDomain',
    'ProcessedBridgeDomain',
    'ConsolidatedBridgeDomain',
    'InterfaceInfo',
    'VLANConfiguration',
    'LoadedData',
    'ValidationResult'
]

print("⚠️  Using compatibility layer for simplified_discovery")
print("💡 Update imports to use config_engine.discovery.simplified")