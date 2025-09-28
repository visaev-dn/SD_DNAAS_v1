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
                'updated_at': bd.get('updated_at'),
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
                'updated_at': bd.get('updated_at'),
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


# =============================================================================
# BD ASSIGNMENT & USER WORKSPACE ENDPOINTS
# =============================================================================

@app.route('/api/bridge-domains/<int:bd_id>/assign', methods=['POST'])
@simple_auth_required
def assign_bridge_domain_to_workspace(bd_id):
    """Assign bridge domain to user's workspace"""
    try:
        from bd_assignment_manager import BDAssignmentManager
        
        # For development, use admin user (ID: 1)
        user_id = 1
        data = request.get_json() or {}
        reason = data.get('reason', 'User workspace assignment')
        
        manager = BDAssignmentManager()
        result = manager.assign_bridge_domain(user_id, bd_id, reason)
        
        if result.success:
            return jsonify({
                "success": True,
                "assignment_id": result.assignment_id,
                "message": f"Bridge domain assigned to your workspace"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.error
            }), 400
            
    except Exception as e:
        logger.error(f"Assignment failed for BD {bd_id}: {e}")
        return jsonify({
            "success": False,
            "error": f"Assignment failed: {str(e)}"
        }), 500


@app.route('/api/bridge-domains/<int:bd_id>/unassign', methods=['POST'])
@simple_auth_required
def unassign_bridge_domain_from_workspace(bd_id):
    """Remove bridge domain from user's workspace"""
    try:
        from bd_assignment_manager import BDAssignmentManager
        
        # For development, use admin user (ID: 1)
        user_id = 1
        
        manager = BDAssignmentManager()
        result = manager.unassign_bridge_domain(user_id, bd_id)
        
        if result.success:
            return jsonify({
                "success": True,
                "message": f"Bridge domain removed from your workspace"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.error
            }), 400
            
    except Exception as e:
        logger.error(f"Unassignment failed for BD {bd_id}: {e}")
        return jsonify({
            "success": False,
            "error": f"Unassignment failed: {str(e)}"
        }), 500


@app.route('/api/bridge-domains/<int:bd_id>/can-assign', methods=['GET'])
@simple_auth_required
def check_assignment_permission(bd_id):
    """Check if user can assign bridge domain"""
    try:
        from bd_assignment_manager import BDAssignmentManager
        
        # For development, use admin user (ID: 1)
        user_id = 1
        
        manager = BDAssignmentManager()
        permission = manager.can_user_assign_bd(user_id, bd_id)
        
        return jsonify({
            "success": True,
            "allowed": permission.allowed,
            "reason": permission.reason,
            "details": permission.details
        })
        
    except Exception as e:
        logger.error(f"Permission check failed for BD {bd_id}: {e}")
        return jsonify({
            "success": False,
            "error": f"Permission check failed: {str(e)}"
        }), 500


@app.route('/api/users/me/workspace/bridge-domains', methods=['GET'])
@simple_auth_required
def get_user_workspace_bridge_domains():
    """Get all bridge domains in user's workspace"""
    try:
        from bd_assignment_manager import BDAssignmentManager
        
        # For development, use admin user (ID: 1)
        user_id = 1
        
        manager = BDAssignmentManager()
        assigned_bds = manager.get_user_assigned_bridge_domains(user_id)
        
        return jsonify({
            "success": True,
            "assigned_bridge_domains": assigned_bds,
            "total_assigned": len(assigned_bds),
            "message": f"Found {len(assigned_bds)} bridge domains in your workspace"
        })
        
    except Exception as e:
        logger.error(f"Failed to get user workspace: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get workspace: {str(e)}"
        }), 500


@app.route('/api/bridge-domains/assignable', methods=['GET'])
@simple_auth_required
def get_assignable_bridge_domains():
    """Get bridge domains user can assign (within VLAN ranges)"""
    try:
        from bd_assignment_manager import BDAssignmentManager
        
        # For development, use admin user (ID: 1)
        user_id = 1
        
        manager = BDAssignmentManager()
        assignable_bds = manager.get_assignable_bridge_domains(user_id)
        
        return jsonify({
            "success": True,
            "assignable_bridge_domains": assignable_bds,
            "total_assignable": len(assignable_bds),
            "message": f"Found {len(assignable_bds)} bridge domains you can assign"
        })
        
    except Exception as e:
        logger.error(f"Failed to get assignable BDs: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get assignable BDs: {str(e)}"
        }), 500


# =============================================================================
# COMPATIBILITY ENDPOINTS (Placeholders for frontend compatibility)
# =============================================================================

@app.route('/api/builder/devices', methods=['GET'])
@simple_auth_required
def get_builder_devices():
    """Get available devices for builder (placeholder with proper structure)"""
    # Return empty but properly structured response for frontend compatibility
    return jsonify({
        "success": True,
        "devices": [],
        "device_types": {},
        "topology_info": {},
        "message": "Builder devices endpoint - use BD Editor instead"
    })


@app.route('/api/configurations', methods=['GET'])
@simple_auth_required
def get_configurations_compatibility():
    """Get configurations (placeholder - redirects to workspace)"""
    return jsonify({
        "success": True,
        "configurations": [],
        "message": "Use My Workspace tab for assigned bridge domains"
    })

@app.route('/api/bridge-domains/<bridge_domain_name>/edit-session', methods=['POST'])
@simple_auth_required
def create_editing_session(bridge_domain_name):
    """Create an editing session for a specific bridge domain"""
    try:
        logger.info(f"Creating editing session for BD: {bridge_domain_name}")
        
        db_manager = DatabaseManager()
        
        # Get the bridge domain from database
        bd_data = db_manager.get_bridge_domain_by_name(bridge_domain_name)
        if not bd_data:
            return jsonify({
                "success": False,
                "error": f"Bridge domain '{bridge_domain_name}' not found"
            }), 404
        
        # Extract interfaces from discovery_data if available
        interfaces = []
        if bd_data.get('discovery_data'):
            try:
                discovery_json = json.loads(bd_data['discovery_data'])
                
                # Extract interface information from discovery data
                for interface_name, interface_data in discovery_json.get('interfaces', {}).items():
                    # Only include user-editable interfaces (access role)
                    if interface_data.get('role') in ['access', 'endpoint']:
                        interfaces.append({
                            'device': interface_data.get('device', ''),
                            'interface': interface_name,
                            'vlan_id': interface_data.get('vlan_id', bd_data.get('vlan_id')),
                            'role': interface_data.get('role', 'access'),
                            'raw_cli_config': interface_data.get('raw_config', []),
                            'outer_vlan': interface_data.get('outer_vlan'),
                            'inner_vlan': interface_data.get('inner_vlan'),
                            'vlan_manipulation': interface_data.get('vlan_manipulation')
                        })
                        
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Could not parse discovery_data for {bridge_domain_name}: {e}")
        
        # Create editing session
        session_id = f"edit_{bridge_domain_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        editing_session = {
            "session_id": session_id,
            "bridge_domain": {
                "id": bd_data.get('id'),
                "name": bd_data.get('name', bridge_domain_name),
                "vlan_id": bd_data.get('vlan_id'),
                "dnaas_type": bd_data.get('dnaas_type', ''),
                "topology_type": bd_data.get('topology_type', 'p2mp'),
                "original_username": bd_data.get('original_username', ''),
                "interfaces": interfaces
            },
            "changes_made": [],
            "status": "active"
        }
        
        logger.info(f"✅ Created editing session: {session_id} with {len(interfaces)} interfaces")
        
        return jsonify({
            "success": True,
            "editing_session": editing_session,
            "message": f"Editing session created for {bridge_domain_name}"
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating editing session: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to create editing session: {str(e)}"
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
    print("   • POST /api/bridge-domains/<id>/assign - Assign BD to workspace")
    print("   • POST /api/bridge-domains/<id>/unassign - Remove BD from workspace")
    print("   • GET /api/bridge-domains/<id>/can-assign - Check assignment permission")
    print("   • GET /api/users/me/workspace/bridge-domains - Get user workspace")
    print("   • GET /api/bridge-domains/assignable - Get assignable BDs")
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
