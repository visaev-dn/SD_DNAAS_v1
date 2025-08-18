#!/usr/bin/env python3
"""
Lab Automation Framework - Modular API Server
Refactored version with clear separation of concerns and modular structure
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database models and configuration
from models import db
from database_manager import DatabaseManager

# Import the new modular API components
from api.v1 import api_v1
from api.websocket import websocket_handlers
from api.middleware.error_middleware import register_error_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version tracking
VERSION = "2.0.0"
logger.info(f"🚀 Starting Lab Automation Modular API Server v{VERSION}")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'lab-automation-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_automation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Lightweight migration: ensure new Configuration columns exist in SQLite
def _ensure_configuration_columns():
    try:
        with app.app_context():
            # Create tables if not present
            db.create_all()
            from sqlalchemy import text
            conn = db.session.connection()
            cols = conn.execute(text("PRAGMA table_info('configurations')")).fetchall()
            existing = {row[1] for row in cols}  # name is index 1

            to_add = []
            if 'config_source' not in existing:
                to_add.append("ADD COLUMN config_source VARCHAR(50)")
            if 'builder_type' not in existing:
                to_add.append("ADD COLUMN builder_type VARCHAR(50)")
            if 'topology_type' not in existing:
                to_add.append("ADD COLUMN topology_type VARCHAR(50)")
            if 'derived_from_scan_id' not in existing:
                to_add.append("ADD COLUMN derived_from_scan_id INTEGER")
            if 'builder_input' not in existing:
                to_add.append("ADD COLUMN builder_input TEXT")

            for clause in to_add:
                try:
                    conn.execute(text(f"ALTER TABLE configurations {clause}"))
                except Exception as e:
                    logger.warning(f"Migration step failed ({clause}): {e}")
            if to_add:
                db.session.commit()
                logger.info(f"Applied configuration column migration: {to_add}")
            else:
                logger.info("Configuration table up to date; no migration needed")
    except Exception as e:
        logger.error(f"Migration error: {e}")

_ensure_configuration_columns()

# Initialize CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register error handlers
register_error_handlers(app)

# Register API v1 blueprint
app.register_blueprint(api_v1)

# Register WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    websocket_handlers['connect']()

@socketio.on('disconnect')
def handle_disconnect():
    websocket_handlers['disconnect']()

@socketio.on('subscribe')
def handle_subscription(data):
    websocket_handlers['subscription'](data)

@socketio.on('unsubscribe')
def handle_unsubscription(data):
    websocket_handlers['unsubscription'](data)

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'version': VERSION,
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'version': VERSION,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

# Database health check
@app.route('/api/database/health', methods=['GET'])
def database_health_check():
    """Database health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Test database endpoint
@app.route('/api/test/db', methods=['GET'])
def test_database():
    """Test database connectivity"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'message': 'Database connection successful',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return jsonify({
            'error': 'Database connection failed',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'Lab Automation Framework API',
        'version': VERSION,
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat(),
        'endpoints': {
            'health': '/api/health',
            'database_health': '/api/database/health',
            'api_v1': '/api/v1',
            'websocket': 'WebSocket endpoint available'
        }
    }), 200

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status_code': 404,
        'timestamp': datetime.utcnow().isoformat()
    }), 404

# Error handler for 405
@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'error': 'Method Not Allowed',
        'message': 'The HTTP method is not supported for this endpoint',
        'status_code': 405,
        'timestamp': datetime.utcnow().isoformat()
    }), 405

if __name__ == '__main__':
    logger.info("Starting Lab Automation Modular API Server...")
    
    # Run the application
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )
