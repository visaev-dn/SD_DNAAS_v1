#!/usr/bin/env python3
"""
Minimal API Server for BD Editor Frontend Integration
Provides only the essential endpoints needed for BD Editor functionality
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import only essential modules
from database_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Enhanced CORS configuration for frontend
CORS(app, 
     origins=['http://localhost:8080', 'http://localhost:3000'], 
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=True)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/lab_automation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'bd-editor-dev-key'

# Simple auth for development (no token validation for now)
def simple_auth_required(f):
    """Simple auth decorator for development"""
    def decorated(*args, **kwargs):
        # For development, skip auth validation
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

# =============================================================================
# BD EDITOR API ENDPOINTS
# =============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple login for development"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Simple validation for development
        if username == 'admin' and password == 'Admin123!':
            return jsonify({
                "success": True,
                "token": "dev-token-admin",
                "user": {
                    "id": 1,
                    "username": "admin",
                    "email": "admin@lab-automation.local",
                    "role": "admin",
                    "is_admin": True
                },
                "message": "Login successful"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid credentials"
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            "success": False,
            "error": f"Login failed: {str(e)}"
        }), 500


@app.route('/api/bridge-domains/unified-list', methods=['GET'])
@simple_auth_required
def get_unified_bridge_domains():
    """Get all discovered + user-created BDs from unified table for BD Editor"""
    try:
        # Import our CLI BD Editor logic
        from main import get_discovered_bridge_domains, get_user_created_bridge_domains
        
        db_manager = DatabaseManager()
        
        # Get discovered BDs (using our CLI logic)
        discovered_bds = get_discovered_bridge_domains(db_manager)
        
        # Get user-created BDs (using our CLI logic)
        user_bds = get_user_created_bridge_domains(db_manager)
        
        # Combine and enhance for frontend
        all_bds = []
        
        # Add discovered BDs
        for bd in discovered_bds:
            # Simplify DNAAS type for frontend
            dnaas_type = bd['dnaas_type'] or 'unknown'
            if 'TYPE_2A_QINQ' in dnaas_type:
                simplified_type = '2A_QINQ'
            elif 'TYPE_4A_SINGLE' in dnaas_type:
                simplified_type = '4A_SINGLE'
            elif 'TYPE_1_DOUBLE' in dnaas_type:
                simplified_type = '1_DOUBLE'
            else:
                simplified_type = 'OTHER'
            
            # Calculate user-editable endpoint count from discovery data
            endpoint_count = 0
            if bd.get('discovery_data'):
                try:
                    discovery_json = json.loads(bd['discovery_data'])
                    devices = discovery_json.get('devices', {})
                    
                    for device_name, device_info in devices.items():
                        if isinstance(device_info, dict) and 'interfaces' in device_info:
                            for iface in device_info['interfaces']:
                                # Count only access interfaces (user endpoints)
                                if iface.get('role') == 'access':
                                    endpoint_count += 1
                except:
                    endpoint_count = 0  # Failed to parse, default to 0
            
            all_bds.append({
                'id': bd['id'],
                'name': bd['name'],
                'vlan_id': bd['vlan_id'],
                'username': bd['username'],
                'dnaas_type': bd['dnaas_type'],
                'dnaas_type_display': simplified_type,
                'topology_type': bd['topology_type'],
                'source': 'discovered',
                'source_icon': '🔍',
                'deployment_status': bd.get('deployment_status', 'pending'),
                'created_at': bd['created_at'],
                'can_edit': True,
                'interface_count': endpoint_count,  # Calculated from discovery data
                'has_raw_config': bool(bd.get('discovery_data'))
            })
        
        # Add user-created BDs
        for bd in user_bds:
            all_bds.append({
                'id': bd['id'],
                'name': bd['name'],
                'vlan_id': bd['vlan_id'],
                'username': bd.get('username', 'admin'),
                'dnaas_type': bd['dnaas_type'],
                'dnaas_type_display': 'USER_CREATED',
                'topology_type': bd['topology_type'],
                'source': 'user_created',
                'source_icon': '🔨',
                'deployment_status': bd.get('deployment_status', 'pending'),
                'created_at': bd['created_at'],
                'can_edit': True,
                'interface_count': 0,
                'has_raw_config': bool(bd.get('discovery_data'))
            })
        
        logger.info(f"Returning {len(all_bds)} bridge domains to frontend")
        
        return jsonify({
            "success": True,
            "bridge_domains": all_bds,
            "total_count": len(all_bds),
            "discovered_count": len(discovered_bds),
            "user_created_count": len(user_bds),
            "message": f"Found {len(all_bds)} bridge domains available for editing"
        })
        
    except Exception as e:
        logger.error(f"Failed to get unified bridge domains: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to load bridge domains: {str(e)}"
        }), 500


@app.route('/api/bridge-domains/<bd_name>/interfaces/raw-config', methods=['GET'])
@simple_auth_required
def get_bd_raw_config(bd_name):
    """Get raw CLI configuration for bridge domain interfaces"""
    try:
        import sqlite3
        
        # Get BD from unified bridge_domains table
        conn = sqlite3.connect('instance/lab_automation.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT discovery_data, interface_data, dnaas_type
            FROM bridge_domains 
            WHERE name = ? AND source = 'discovered'
        """, (bd_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({
                "success": False,
                "error": f"Bridge domain '{bd_name}' not found"
            }), 404
        
        discovery_data, interface_data, dnaas_type = result
        
        # Extract raw config from discovery data
        raw_configs = []
        if discovery_data:
            discovery_json = json.loads(discovery_data)
            devices = discovery_json.get('devices', {})
            
            for device_name, device_info in devices.items():
                if 'interfaces' in device_info:
                    for iface in device_info['interfaces']:
                        # Only include access interfaces (user endpoints)
                        if iface.get('role') == 'access':
                            raw_configs.append({
                                'device': device_name,
                                'interface': iface.get('name'),
                                'vlan_id': iface.get('vlan_id'),
                                'role': iface.get('role'),
                                'raw_cli_config': iface.get('raw_cli_config', []),
                                'outer_vlan': iface.get('outer_vlan'),
                                'inner_vlan': iface.get('inner_vlan'),
                                'vlan_manipulation': iface.get('vlan_manipulation')
                            })
        
        return jsonify({
            "success": True,
            "bridge_domain_name": bd_name,
            "dnaas_type": dnaas_type,
            "user_editable_endpoints": raw_configs,
            "total_endpoints": len(raw_configs),
            "message": f"Raw configuration for {len(raw_configs)} user-editable endpoints"
        })
        
    except Exception as e:
        logger.error(f"Failed to get raw config for {bd_name}: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get raw configuration: {str(e)}"
        }), 500


@app.route('/api/auth/me', methods=['GET'])
@simple_auth_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        "success": True,
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@lab-automation.local",
            "role": "admin",
            "is_admin": True
        }
    })


@app.route('/api/dashboard/stats', methods=['GET'])
@simple_auth_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        db_manager = DatabaseManager()
        from main import get_discovered_bridge_domains, get_user_created_bridge_domains
        
        discovered_bds = get_discovered_bridge_domains(db_manager)
        user_bds = get_user_created_bridge_domains(db_manager)
        
        return jsonify({
            "success": True,
            "stats": {
                "total_bridge_domains": len(discovered_bds) + len(user_bds),
                "discovered_bridge_domains": len(discovered_bds),
                "user_created_bridge_domains": len(user_bds),
                "pending_deployments": 0,
                "active_deployments": 0
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/dashboard/personal-stats', methods=['GET'])
@simple_auth_required
def get_personal_stats():
    """Get personal user statistics"""
    return jsonify({
        "success": True,
        "stats": {
            "personal_configurations": 0,
            "personal_deployments": 0,
            "vlan_usage": 0
        }
    })


@app.route('/api/dashboard/recent-activity', methods=['GET'])
@simple_auth_required
def get_recent_activity():
    """Get recent activity"""
    return jsonify({
        "success": True,
        "activities": []
    })


@app.route('/api/configurations', methods=['GET'])
@simple_auth_required
def get_configurations():
    """Get user configurations (placeholder for compatibility)"""
    return jsonify({
        "success": True,
        "configurations": [],
        "message": "No configurations in BD Editor API (use BD Browser instead)"
    })


@app.route('/api/bridge-domains/list', methods=['GET'])
@simple_auth_required
def get_bridge_domains_list():
    """Legacy bridge domains list endpoint (redirect to unified)"""
    try:
        # Redirect to our unified endpoint logic
        from main import get_discovered_bridge_domains
        db_manager = DatabaseManager()
        discovered_bds = get_discovered_bridge_domains(db_manager)
        
        # Convert to legacy format
        legacy_bds = []
        for bd in discovered_bds[:50]:  # Limit for performance
            legacy_bds.append({
                "name": bd['name'],
                "vlan": str(bd['vlan_id']) if bd['vlan_id'] else 'N/A',
                "username": bd['username'],
                "confidence": 1.0,
                "topology_type": bd.get('topology_type', 'unknown'),
                "total_devices": 1,
                "total_interfaces": 1,
                "access_interfaces": 1,
                "path_complexity": "simple",
                "detection_method": "simplified_workflow"
            })
        
        return jsonify({
            "success": True,
            "bridge_domains": legacy_bds,
            "discovered_count": len(legacy_bds),
            "message": f"Found {len(legacy_bds)} bridge domains"
        })
        
    except Exception as e:
        logger.error(f"Failed to get bridge domains list: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to load bridge domains: {str(e)}"
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "success": True,
        "status": "healthy",
        "message": "BD Editor API server running",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("🚀 Starting BD Editor API Server...")
    print("📋 Endpoints available:")
    print("   • POST /api/auth/login - Simple authentication")
    print("   • GET /api/bridge-domains/unified-list - Get all BDs")
    print("   • GET /api/bridge-domains/<name>/interfaces/raw-config - Get raw config")
    print("   • GET /api/health - Health check")
    print()
    print("🌐 Frontend: http://localhost:8080")
    print("🔗 API Server: http://localhost:5001")
    print()
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )
