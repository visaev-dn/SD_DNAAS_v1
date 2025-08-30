#!/usr/bin/env python3
"""
Enhanced Discovery Integration Package

This package provides seamless integration between legacy discovery systems
and the Enhanced Database (Phase 1) structures.

Components:
- EnhancedDiscoveryAdapter: Main adapter for data conversion
- EnhancedDataConverter: Specific data format conversions
- EnhancedDatabasePopulationService: Automatic database population
- EnhancedDiscoveryErrorHandler: Comprehensive error handling
- EnhancedDiscoveryLoggingManager: Enhanced logging and monitoring
"""

from .discovery_adapter import EnhancedDiscoveryAdapter
from .data_converter import EnhancedDataConverter
from .auto_population_service import EnhancedDatabasePopulationService
from .error_handler import EnhancedDiscoveryErrorHandler
from .logging_manager import EnhancedDiscoveryLoggingManager
from .migration_manager import EnhancedDiscoveryMigrationManager
from .unified_workflow import EnhancedDiscoveryWorkflow
from .troubleshooting_guide import EnhancedDiscoveryTroubleshootingGuide

__version__ = "1.0.0"
__author__ = "Development Team"

# Main entry points
def create_enhanced_discovery_adapter(legacy_data_path: str, enhanced_db_manager):
    """Create and configure Enhanced Discovery Adapter"""
    return EnhancedDiscoveryAdapter(legacy_data_path, enhanced_db_manager)

def create_enhanced_database_population_service(enhanced_db_manager):
    """Create and configure Enhanced Database Population Service"""
    return EnhancedDatabasePopulationService(enhanced_db_manager)

def create_enhanced_discovery_workflow(enhanced_db_manager):
    """Create and configure Enhanced Discovery Workflow"""
    return EnhancedDiscoveryWorkflow(enhanced_db_manager)

# Package-level logging setup
import logging
logger = logging.getLogger(__name__)
logger.info("🚀 Enhanced Discovery Integration Package loaded")
logger.info("💡 Use create_enhanced_discovery_adapter() to start enhanced discovery operations")
