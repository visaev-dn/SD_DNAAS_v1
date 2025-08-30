#!/usr/bin/env python3
"""
Phase 1 API Integration Package
Provides REST API endpoints for Phase 1 data structures and database operations
"""

from .router import EnhancedDatabaseAPIRouter
from .endpoints import (
    create_topology_endpoints,
    create_device_endpoints,
    create_interface_endpoints,
    create_path_endpoints,
    create_bridge_domain_endpoints,
    create_migration_endpoints,
    create_export_endpoints
)

__all__ = [
    'Phase1APIRouter',
    'create_topology_endpoints',
    'create_device_endpoints',
    'create_interface_endpoints',
    'create_path_endpoints',
    'create_bridge_domain_endpoints',
    'create_migration_endpoints',
    'create_export_endpoints'
]

def create_enhanced_database_api_router(app, db_manager=None, blueprint_name=None):
    """
    Create and register Enhanced Database API router with Flask app.
    
    Args:
        app: Flask application instance
        db_manager: Optional Enhanced Database manager instance
        blueprint_name: Optional custom blueprint name to avoid conflicts
        
    Returns:
        EnhancedDatabaseAPIRouter instance
    """
    router = EnhancedDatabaseAPIRouter(app, db_manager, blueprint_name)
    router.register_routes()
    return router

def enable_enhanced_database_api(app, db_manager=None):
    """
    Enable Enhanced Database API integration with the Flask app.
    
    Args:
        app: Flask application instance
        db_manager: Optional Enhanced Database manager instance
        
    Returns:
        True if successful, False otherwise
    """
    try:
        router = create_enhanced_database_api_router(app, db_manager, 'enhanced_database_api')
        app.logger.info("🚀 Enhanced Database API integration enabled successfully")
        return True
    except Exception as e:
        app.logger.error(f"❌ Failed to enable Enhanced Database API integration: {e}")
        return False
