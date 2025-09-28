#!/usr/bin/env python3
"""
BD Editor Services - Intelligent Bridge Domain Editor

Intelligent, type-aware bridge domain editing system that adapts to different
DNAAS bridge domain types and provides appropriate editing workflows.

PHASE 1 IMPLEMENTATION: Core Infrastructure
- Data models and exceptions
- Interface role detection and analysis
- Type-aware menu system
- Session management with persistence
- Performance monitoring
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Core data models
from .data_models import (
    BDEditingComplexity,
    ValidationResult,
    InterfaceAnalysis,
    ImpactAnalysis,
    PreviewReport,
    HealthReport,
    DeploymentResult,
    DeviceDeploymentResult,
    BDTypeProfile,
    # Exceptions
    BDEditorException,
    BDDataRetrievalError,
    IntegrationFailureError,
    CriticalIntegrationError,
    BDEditorExitException,
    ValidationError,
    ConfigurationError,
    DeploymentError,
    SessionError,
    PerformanceError
)

# Core components
from .interface_analyzer import (
    BDInterfaceAnalyzer,
    BDTypeRegistry,
    analyze_bridge_domain_interfaces,
    get_bd_type_profile,
    display_bd_type_information
)

from .menu_system import (
    IntelligentBDEditorMenu,
    create_intelligent_menu,
    display_intelligent_header
)

from .menu_adapters import (
    MenuAdapter,
    SingleTaggedMenuAdapter,
    QinQSingleMenuAdapter,
    DoubleTaggedMenuAdapter,
    GenericMenuAdapter
)

from .session_manager import (
    BDEditingSessionManager,
    create_bd_editing_session,
    save_bd_session
)

from .performance_monitor import (
    BDEditorPerformanceMonitor,
    PerformanceTracker,
    create_performance_tracker
)

__version__ = "1.0.0-phase1"
__author__ = "Lab Automation Framework"

# Check integration availability
def check_integrations() -> Dict[str, bool]:
    """Check availability of external integrations"""
    
    integrations = {}
    
    # Interface Discovery System
    try:
        from services.interface_discovery import SimpleInterfaceDiscovery
        integrations['interface_discovery'] = True
    except ImportError:
        integrations['interface_discovery'] = False
    
    # Smart Interface Selection
    try:
        from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
        integrations['smart_selection'] = True
    except ImportError:
        integrations['smart_selection'] = False
    
    # Database Manager
    try:
        from database_manager import DatabaseManager
        integrations['database_manager'] = True
    except ImportError:
        integrations['database_manager'] = False
    
    return integrations

# Phase 1 exports
__all__ = [
    # Data models
    'BDEditingComplexity',
    'ValidationResult',
    'InterfaceAnalysis', 
    'ImpactAnalysis',
    'PreviewReport',
    'HealthReport',
    'DeploymentResult',
    'DeviceDeploymentResult',
    'BDTypeProfile',
    
    # Exceptions
    'BDEditorException',
    'BDDataRetrievalError',
    'IntegrationFailureError',
    'CriticalIntegrationError',
    'BDEditorExitException',
    'ValidationError',
    'ConfigurationError',
    'DeploymentError',
    'SessionError',
    'PerformanceError',
    
    # Core components
    'BDInterfaceAnalyzer',
    'BDTypeRegistry',
    'IntelligentBDEditorMenu',
    'MenuAdapter',
    'SingleTaggedMenuAdapter',
    'QinQSingleMenuAdapter', 
    'DoubleTaggedMenuAdapter',
    'GenericMenuAdapter',
    'BDEditingSessionManager',
    'BDEditorPerformanceMonitor',
    'PerformanceTracker',
    
    # Convenience functions
    'analyze_bridge_domain_interfaces',
    'get_bd_type_profile',
    'display_bd_type_information',
    'create_intelligent_menu',
    'display_intelligent_header',
    'create_bd_editing_session',
    'save_bd_session',
    'create_performance_tracker',
    'check_integrations'
]

# Integration status
INTEGRATIONS_AVAILABLE = check_integrations()

# Import Phase 2 components
try:
    from .config_templates import (
        ConfigTemplateEngine,
        generate_cli_commands,
        preview_cli_commands
    )
    from .validation_system import (
        TypeAwareValidator,
        validate_bd_for_editing,
        validate_interface_change
    )
    from .config_preview import (
        ConfigurationPreviewSystem,
        generate_configuration_preview,
        display_configuration_preview
    )
    from .impact_analyzer import (
        ChangeImpactAnalyzer,
        analyze_change_impact
    )
    from .template_validator import (
        CLITemplateValidator,
        validate_cli_commands,
        dry_run_cli_commands
    )
    
    PHASE_2_AVAILABLE = True
    
    # Add Phase 2 exports to __all__
    __all__.extend([
        'ConfigTemplateEngine',
        'TypeAwareValidator', 
        'ConfigurationPreviewSystem',
        'ChangeImpactAnalyzer',
        'CLITemplateValidator',
        'generate_cli_commands',
        'preview_cli_commands',
        'validate_bd_for_editing',
        'validate_interface_change',
        'generate_configuration_preview',
        'display_configuration_preview',
        'analyze_change_impact',
        'validate_cli_commands',
        'dry_run_cli_commands'
    ])
    
except ImportError as e:
    PHASE_2_AVAILABLE = False
    logger.warning(f"Phase 2 components not available: {e}")

# Import Phase 3 components
try:
    from .change_tracker import (
        AdvancedChangeTracker,
        create_change_tracker,
        track_bd_change
    )
    from .error_handler import (
        BDEditorErrorHandler,
        IntegrationFallbackManager,
        handle_bd_editor_error,
        handle_integration_failure
    )
    from .health_checker import (
        BDHealthChecker,
        check_bd_health,
        is_bd_ready_for_editing,
        display_bd_health_report
    )
    from .integration_fallbacks import (
        IntegrationContext,
        create_integration_context,
        handle_integration_error
    )
    
    PHASE_3_AVAILABLE = True
    
    # Add Phase 3 exports to __all__
    __all__.extend([
        'AdvancedChangeTracker',
        'BDEditorErrorHandler',
        'IntegrationFallbackManager', 
        'BDHealthChecker',
        'IntegrationContext',
        'create_change_tracker',
        'track_bd_change',
        'handle_bd_editor_error',
        'handle_integration_failure',
        'check_bd_health',
        'is_bd_ready_for_editing',
        'display_bd_health_report',
        'create_integration_context',
        'handle_integration_error'
    ])
    
except ImportError as e:
    PHASE_3_AVAILABLE = False
    logger.warning(f"Phase 3 components not available: {e}")

# Import Phase 4 components
try:
    from .deployment_integration import (
        BDEditorDeploymentIntegration,
        ProductionBDEditor,
        enhanced_bd_editor_with_intelligent_menu,
        replace_bd_editor_with_intelligent_system,
        deploy_bd_changes,
        start_intelligent_bd_editor
    )
    
    PHASE_4_AVAILABLE = True
    
    # Add Phase 4 exports to __all__
    __all__.extend([
        'BDEditorDeploymentIntegration',
        'ProductionBDEditor',
        'enhanced_bd_editor_with_intelligent_menu',
        'replace_bd_editor_with_intelligent_system',
        'deploy_bd_changes',
        'start_intelligent_bd_editor'
    ])
    
except ImportError as e:
    PHASE_4_AVAILABLE = False
    logger.warning(f"Phase 4 components not available: {e}")

# Phase status
PHASE_1_COMPLETE = True