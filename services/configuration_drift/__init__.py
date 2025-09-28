#!/usr/bin/env python3
"""
Configuration Drift Handling System

Detects and resolves configuration drift between database and device reality.
Provides graceful handling of sync issues during deployment operations.

Key Features:
- Drift detection from commit-check and deployment results
- Targeted configuration discovery using optimized filtering
- Interactive sync resolution with user options
- Database integration with existing interface_discovery system
- Smart integration with universal SSH framework
"""

from .data_models import (
    DriftType,
    DriftEvent,
    SyncAction,
    SyncResolution,
    InterfaceConfig,
    SyncResult,
    BridgeDomainDiscoveryResult,
    ConfigurationDriftException,
    TargetedDiscoveryError,
    DatabaseSyncError,
    DriftDetectionError,
    SyncResolutionError
)

from .drift_detector import (
    ConfigurationDriftDetector,
    detect_drift_from_commit_check,
    detect_drift_from_deployment
)

from .targeted_discovery import (
    TargetedConfigurationDiscovery,
    discover_interface_configurations,
    discover_bridge_domain_on_device,
    discover_device_configurations,
    discover_specific_interface
)

from .sync_resolver import (
    ConfigurationSyncResolver,
    resolve_drift_interactive,
    resolve_drift_automatic
)

from .database_updater import (
    DatabaseConfigurationUpdater,
    update_database_with_configs,
    sync_interface_configurations
)

from .deployment_integration import (
    DriftAwareDeploymentHandler,
    deploy_with_drift_handling
)

from .db_population_adapter import (
    BridgeDomainDatabasePopulationAdapter,
    DatabasePopulationUseCases,
    populate_database_from_targeted_discovery,
    populate_database_from_interface_drift
)

__version__ = "1.0.0"
__author__ = "Lab Automation Framework"

# Check integration health
def check_drift_system_health():
    """Check health of configuration drift system"""
    
    health_status = {}
    
    # Check universal SSH framework
    try:
        from services.universal_ssh import FRAMEWORK_READY
        health_status['universal_ssh'] = FRAMEWORK_READY
    except ImportError:
        health_status['universal_ssh'] = False
    
    # Check interface discovery integration
    try:
        from services.interface_discovery import SimpleInterfaceDiscovery
        health_status['interface_discovery'] = True
    except ImportError:
        health_status['interface_discovery'] = False
    
    # Check database manager
    try:
        from database_manager import DatabaseManager
        health_status['database_manager'] = True
    except ImportError:
        health_status['database_manager'] = False
    
    return health_status

__all__ = [
    # Data models
    'DriftType',
    'DriftEvent', 
    'SyncAction',
    'SyncResolution',
    'InterfaceConfig',
    'SyncResult',
    'BridgeDomainDiscoveryResult',
    'ConfigurationDriftException',
    'TargetedDiscoveryError',
    'DatabaseSyncError',
    'DriftDetectionError',
    'SyncResolutionError',
    
    # Core components
    'ConfigurationDriftDetector',
    'TargetedConfigurationDiscovery',
    'ConfigurationSyncResolver',
    'DatabaseConfigurationUpdater',
    'DriftAwareDeploymentHandler',
    'BridgeDomainDatabasePopulationAdapter',
    'DatabasePopulationUseCases',
    
    # Convenience functions
    'detect_drift_from_commit_check',
    'detect_drift_from_deployment',
    'discover_interface_configurations',
    'discover_bridge_domain_on_device',
    'discover_device_configurations',
    'discover_specific_interface',
    'resolve_drift_interactive',
    'resolve_drift_automatic',
    'update_database_with_configs',
    'sync_interface_configurations',
    'deploy_with_drift_handling',
    'populate_database_from_targeted_discovery',
    'populate_database_from_interface_drift',
    'check_drift_system_health'
]

# System health
DRIFT_SYSTEM_HEALTH = check_drift_system_health()
DRIFT_SYSTEM_READY = all(DRIFT_SYSTEM_HEALTH.values())
