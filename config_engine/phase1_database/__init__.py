#!/usr/bin/env python3
"""
Phase 1 Database Integration Package
Provides database models and utilities for Phase 1 data structures
"""

# Core database components
from .models import (
    Phase1TopologyData, Phase1DeviceInfo, Phase1InterfaceInfo, 
    Phase1PathInfo, Phase1BridgeDomainConfig, Phase1Configuration
)

# Database utilities
from .manager import Phase1DatabaseManager
from .migrations import Phase1MigrationManager
from .serializers import Phase1DataSerializer

# Version information
__version__ = "1.0.0"
__author__ = "Lab Automation Team"
__description__ = "Phase 1 database integration layer"

# Public API
__all__ = [
    # Models
    'Phase1TopologyData',
    'Phase1DeviceInfo', 
    'Phase1InterfaceInfo',
    'Phase1PathInfo',
    'Phase1BridgeDomainConfig',
    'Phase1Configuration',
    
    # Managers
    'Phase1DatabaseManager',
    'Phase1MigrationManager',
    
    # Utilities
    'Phase1DataSerializer',
    
    # Metadata
    '__version__',
    '__author__',
    '__description__'
]

# Convenience functions
def create_phase1_database_manager(db_path: str = 'instance/lab_automation.db'):
    """Create a Phase 1 database manager instance"""
    return Phase1DatabaseManager(db_path)

def get_migration_manager(db_path: str = 'instance/lab_automation.db'):
    """Get a Phase 1 migration manager instance"""
    return Phase1MigrationManager(db_path)

def get_data_serializer():
    """Get a Phase 1 data serializer instance"""
    return Phase1DataSerializer()

# Add convenience functions to __all__
__all__.extend([
    'create_phase1_database_manager',
    'get_migration_manager', 
    'get_data_serializer'
])

print("🚀 Phase 1 Database Integration Package loaded")
print("💡 Use create_phase1_database_manager() to start database operations")

