#!/usr/bin/env python3
"""
Phase 1 API Router
Main router class for Phase 1 API endpoints
"""

import logging
from typing import Optional
from flask import Flask, Blueprint

from .endpoints import (
    create_topology_endpoints,
    create_device_endpoints,
    create_interface_endpoints,
    create_path_endpoints,
    create_bridge_domain_endpoints,
    create_migration_endpoints,
    create_export_endpoints
)

logger = logging.getLogger(__name__)


class EnhancedDatabaseAPIRouter:
    """
    Enhanced Database API Router for managing all enhanced database endpoints.
    
    This router provides a clean separation of enhanced database functionality
    while maintaining compatibility with existing API structure.
    """
    
    def __init__(self, app: Flask, db_manager=None, blueprint_name=None):
        """
        Initialize Phase 1 API router.
        
        Args:
            app: Flask application instance
            db_manager: Optional Phase 1 database manager instance
            blueprint_name: Optional custom blueprint name to avoid conflicts
        """
        self.app = app
        self.db_manager = db_manager
        self.logger = logger
        
        # Create Enhanced Database blueprint with unique name
        blueprint_name = blueprint_name or 'enhanced_database_api'
        self.blueprint = Blueprint(blueprint_name, __name__, url_prefix='/api/enhanced-database')
        
        # Ensure database manager is available
        if not self.db_manager:
            self.db_manager = self.get_db_manager()
        
        self.logger.info(f"🚀 Enhanced Database API Router initialized with blueprint '{blueprint_name}'")
        if self.db_manager:
            self.logger.info(f"🔧 Database manager available: {type(self.db_manager).__name__}")
        else:
            self.logger.warning("⚠️ No database manager available")
    
    def register_routes(self):
        """Register all Enhanced Database API routes"""
        try:
            # Create and register endpoint groups
            create_topology_endpoints(self.blueprint, self.db_manager)
            create_device_endpoints(self.blueprint, self.db_manager)
            create_interface_endpoints(self.blueprint, self.db_manager)
            create_path_endpoints(self.blueprint, self.db_manager)
            create_bridge_domain_endpoints(self.blueprint, self.db_manager)
            create_migration_endpoints(self.blueprint, self.db_manager)
            create_export_endpoints(self.blueprint, self.db_manager)
            
            # Store database manager in app context for endpoints to access
            if self.db_manager:
                self.app.enhanced_db_manager = self.db_manager
            
            # Register blueprint with app after all routes are added
            self.app.register_blueprint(self.blueprint)
            
            self.logger.info("✅ All Enhanced Database API routes registered successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to register Enhanced Database API routes: {e}")
            raise
    
    def get_db_manager(self):
        """Get the database manager instance"""
        if self.db_manager is None:
            # Try to get from app context if available
            try:
                from config_engine.phase1_database import create_phase1_database_manager
                self.db_manager = create_phase1_database_manager()
                self.logger.info("🔧 Phase 1 database manager created from app context")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not create database manager from app context: {e}")
                return None
        
        return self.db_manager
    
    def health_check(self):
        """Health check for Enhanced Database API components"""
        try:
            db_manager = self.get_db_manager()
            if db_manager:
                db_info = db_manager.get_database_info()
                return {
                    'status': 'healthy',
                    'enhanced_database_api': True,
                    'database': db_info.get('phase1_tables', []),
                    'total_records': db_info.get('total_phase1_records', 0)
                }
            else:
                return {
                    'status': 'degraded',
                    'enhanced_database_api': True,
                    'database': False,
                    'message': 'Database manager not available'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'enhanced_database_api': True,
                'error': str(e)
            }
