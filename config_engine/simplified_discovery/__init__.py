#!/usr/bin/env python3
"""
Simplified Bridge Domain Discovery Package
==========================================

This package implements the 3-Step Simplified Workflow for bridge domain discovery,
addressing all the logic flaws identified in the architectural analysis.

Architecture: 3-Step Simplified Workflow (ADR-001)

Components:
- data_structures: Standardized data structures with guided rails
- simplified_bridge_domain_discovery: Main 3-step workflow implementation
- cli_integration: CLI interface following user preferences

Usage:
    from config_engine.simplified_discovery import run_simplified_discovery
    results = run_simplified_discovery()
"""

# Import main functions for easy access
from .simplified_bridge_domain_discovery import (
    SimplifiedBridgeDomainDiscovery,
    run_simplified_discovery,
    validate_simplified_workflow
)

from .data_structures import (
    # Step 1 structures
    RawBridgeDomain,
    ValidationResult, 
    LoadedData,
    
    # Step 2 structures
    VLANConfiguration,
    InterfaceInfo,
    ProcessedBridgeDomain,
    
    # Step 3 structures
    ConsolidationGroup,
    ConsolidatedBridgeDomain,
    DiscoveryResults,
    
    # Error handling
    DiscoveryError,
    DataQualityError,
    ClassificationError,
    ConsolidationError,
    WorkflowError,
    
    # Validation functions
    validate_data_flow_step1_to_step2,
    validate_data_flow_step2_to_step3,
    enforce_data_structure_contracts
)

from .cli_integration import (
    SimplifiedDiscoveryCLI,
    run_enhanced_database_menu
)

# Package metadata
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Simplified Bridge Domain Discovery System with 3-Step Workflow"

# Export main interface
__all__ = [
    # Main discovery functions
    "SimplifiedBridgeDomainDiscovery",
    "run_simplified_discovery",
    "validate_simplified_workflow",
    
    # Data structures
    "RawBridgeDomain",
    "ValidationResult",
    "LoadedData", 
    "VLANConfiguration",
    "InterfaceInfo",
    "ProcessedBridgeDomain",
    "ConsolidationGroup",
    "ConsolidatedBridgeDomain",
    "DiscoveryResults",
    
    # Error handling
    "DiscoveryError",
    "DataQualityError", 
    "ClassificationError",
    "ConsolidationError",
    "WorkflowError",
    
    # Validation functions
    "validate_data_flow_step1_to_step2",
    "validate_data_flow_step2_to_step3", 
    "enforce_data_structure_contracts",
    
    # CLI integration
    "SimplifiedDiscoveryCLI",
    "run_enhanced_database_menu"
]

# Validate package on import
def _validate_package_integrity():
    """Validate package integrity on import"""
    try:
        # Test that all main components can be imported
        validate_simplified_workflow()
        enforce_data_structure_contracts()
        return True
    except Exception as e:
        import warnings
        warnings.warn(f"Package integrity validation failed: {e}", RuntimeWarning)
        return False

# Run validation on import
_package_valid = _validate_package_integrity()

if _package_valid:
    print("✅ Simplified Bridge Domain Discovery package loaded successfully")
else:
    print("⚠️  Package loaded with warnings - check system configuration")
