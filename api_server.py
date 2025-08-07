#!/usr/bin/env python3
"""
Lab Automation Framework - Flask API Server
Provides REST API endpoints and WebSocket support for the frontend integration.
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import time # Added for time.time()

from flask import Flask, jsonify, request, send_file, current_app
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database models and authentication
from models import db, User, Configuration, AuditLog, UserVlanAllocation, UserPermission, PersonalBridgeDomain
from auth import token_required, permission_required, admin_required, user_ownership_required, create_audit_log
from database_manager import DatabaseManager
from deployment_manager import DeploymentManager

# Import existing modules
from config_engine.unified_bridge_domain_builder import UnifiedBridgeDomainBuilder
from config_engine.device_scanner import DeviceScanner
from scripts.ssh_push_menu import SSHPushMenu
from scripts.inventory_manager import InventoryManager
from scripts.device_status_viewer import DeviceStatusViewer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version tracking
VERSION = "1.0.2"
logger.info(f"🚀 Starting Lab Automation API Server v{VERSION}")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'lab-automation-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_automation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize database manager
db_manager = DatabaseManager()

CORS(app, origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"])

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize deployment manager
deployment_manager = DeploymentManager(socketio)

# Global instances
builder = UnifiedBridgeDomainBuilder()
inventory_manager = InventoryManager()
device_viewer = DeviceStatusViewer()
device_scanner = DeviceScanner()

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate required fields
        if not username or not email or not password:
            return jsonify({
                "success": False,
                "error": "Username, email, and password are required"
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                "success": False,
                "error": "Username already exists"
            }), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                "success": False,
                "error": "Email already exists"
            }), 409
        
        # Create new user (default role is 'user')
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        
        # Create user directories
        from auth import ensure_user_directories
        ensure_user_directories(new_user.id)
        
        # Create audit log
        create_audit_log(new_user.id, 'register', 'user', new_user.id, {
            'username': username,
            'email': email,
            'role': new_user.role
        })
        
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "user": new_user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            "success": False,
            "error": "Registration failed"
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Username and password are required"
            }), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                "success": False,
                "error": "Invalid username or password"
            }), 401
        
        if not user.is_active:
            return jsonify({
                "success": False,
                "error": "Account is deactivated"
            }), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token
        token = user.generate_token()
        
        # Create audit log
        create_audit_log(user.id, 'login', 'user', user.id, {
            'username': username,
            'ip_address': request.remote_addr
        })
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            "success": False,
            "error": "Login failed"
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """User logout endpoint"""
    try:
        # Create audit log
        create_audit_log(current_user.id, 'logout', 'user', current_user.id, {
            'username': current_user.username
        })
        
        return jsonify({
            "success": True,
            "message": "Logout successful"
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({
            "success": False,
            "error": "Logout failed"
        }), 500

@app.route('/api/auth/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    """Refresh JWT token"""
    try:
        # Generate new token
        new_token = current_user.generate_token()
        
        return jsonify({
            "success": True,
            "token": new_token,
            "user": current_user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({
            "success": False,
            "error": "Token refresh failed"
        }), 500

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """Get current user information"""
    return jsonify({
        "success": True,
        "user": current_user.to_dict()
    })

@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """Change user password"""
    try:
        data = request.get_json()
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')
        
        if not current_password or not new_password:
            return jsonify({
                "success": False,
                "error": "Current password and new password are required"
            }), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({
                "success": False,
                "error": "Current password is incorrect"
            }), 401
        
        # Validate new password strength
        from auth import validate_password_strength
        is_valid, message = validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                "success": False,
                "error": message
            }), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'change_password', 'user', current_user.id, {
            'username': current_user.username
        })
        
        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        })
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({
            "success": False,
            "error": "Password change failed"
        }), 500

@app.route('/api/test/db', methods=['GET'])
def test_database():
    """Test database connectivity"""
    try:
        users = User.query.all()
        return jsonify({
            "success": True,
            "message": "Database connection successful",
            "user_count": len(users),
            "users": [{"username": u.username, "role": u.role} for u in users]
        })
    except Exception as e:
        logger.error(f"Database test error: {e}")
        return jsonify({
            "success": False,
            "error": f"Database test failed: {str(e)}"
        }), 500

# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Count devices from devices.yaml
        devices_count = 0
        if Path("devices.yaml").exists():
            with open("devices.yaml", 'r') as f:
                devices = yaml.safe_load(f)
                devices_count = len([k for k in devices.keys() if k != 'defaults'])
        
        # Count configuration files (all yaml files in configs directory)
        config_files_count = 0
        configs_dir = Path("configs")
        if configs_dir.exists():
            config_files_count = len(list(configs_dir.rglob("*.yaml")))
        
        # Count bridge domains (bridge domain configuration files)
        bridge_domains_count = 0
        pending_dir = Path("configs/pending")
        if pending_dir.exists():
            bridge_domains_count = len([f for f in pending_dir.glob("*.yaml") 
                                      if "bridge_domain" in f.name or "unified_bridge_domain" in f.name])
        
        # Count active deployments (files in deployed directory)
        active_deployments_count = 0
        deployed_dir = Path("configs/deployed")
        if deployed_dir.exists():
            active_deployments_count = len(list(deployed_dir.glob("*.yaml")))
        
        return jsonify({
            "totalDevices": devices_count,
            "activeDeployments": active_deployments_count,
            "bridgeDomains": bridge_domains_count,
            "configFiles": config_files_count
        })
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({"error": "Failed to get dashboard stats"}), 500

@app.route('/api/dashboard/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity for dashboard"""
    try:
        activities = []
        
        # Get recent bridge domain configurations
        pending_dir = Path("configs/pending")
        if pending_dir.exists():
            for config_file in pending_dir.glob("*.yaml"):
                if "bridge_domain" in config_file.name or "unified_bridge_domain" in config_file.name:
                    # Get file modification time
                    mtime = datetime.fromtimestamp(config_file.stat().st_mtime)
                    time_diff = datetime.now() - mtime
                    
                    # Format time difference
                    if time_diff.total_seconds() < 60:
                        time_ago = "just now"
                    elif time_diff.total_seconds() < 3600:
                        minutes = int(time_diff.total_seconds() / 60)
                        time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                    elif time_diff.total_seconds() < 86400:
                        hours = int(time_diff.total_seconds() / 3600)
                        time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
                    else:
                        days = int(time_diff.total_seconds() / 86400)
                        time_ago = f"{days} day{'s' if days != 1 else ''} ago"
                    
                    activities.append({
                        "action": "Bridge Domain Created",
                        "device": config_file.stem,
                        "time": time_ago,
                        "status": "success"
                    })
        
        # Get recent deployments
        deployed_dir = Path("configs/deployed")
        if deployed_dir.exists():
            for config_file in deployed_dir.glob("*.yaml"):
                mtime = datetime.fromtimestamp(config_file.stat().st_mtime)
                time_diff = datetime.now() - mtime
                
                if time_diff.total_seconds() < 60:
                    time_ago = "just now"
                elif time_diff.total_seconds() < 3600:
                    minutes = int(time_diff.total_seconds() / 60)
                    time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
                elif time_diff.total_seconds() < 86400:
                    hours = int(time_diff.total_seconds() / 3600)
                    time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
                else:
                    days = int(time_diff.total_seconds() / 86400)
                    time_ago = f"{days} day{'s' if days != 1 else ''} ago"
                
                activities.append({
                    "action": "Configuration Deployed",
                    "device": config_file.stem,
                    "time": time_ago,
                    "status": "success"
                })
        
        # Sort by time (most recent first) and limit to 10 activities
        activities.sort(key=lambda x: x.get('time', ''), reverse=True)
        activities = activities[:10]
        
        # If no real activities, add some placeholder ones
        if not activities:
            activities = [
                {
                    "action": "System Ready",
                    "device": "Lab Automation Framework",
                    "time": "just now",
                    "status": "success"
                }
            ]
        
        return jsonify(activities)
        
    except Exception as e:
        logger.error(f"Recent activity error: {e}")
        return jsonify({"error": "Failed to get recent activity"}), 500

# ============================================================================
# BRIDGE DOMAIN BUILDER ENDPOINTS
# ============================================================================

@app.route('/api/builder/devices', methods=['GET'])
def get_devices():
    """Get list of available devices"""
    try:
        if not Path("devices.yaml").exists():
            return jsonify({"error": "devices.yaml not found"}), 404
        
        with open("devices.yaml", 'r') as f:
            devices = yaml.safe_load(f)
        
        # Filter out defaults and format for frontend
        device_list = []
        for device_name, device_info in devices.items():
            if device_name != 'defaults':
                device_type = device_info.get('device_type', 'unknown')
                device_list.append({
                    "name": device_name,
                    "type": device_type,
                    "mgmt_ip": device_info.get('mgmt_ip', ''),
                    "location": device_info.get('location', ''),
                    "status": device_info.get('status', 'unknown')
                })
        
        return jsonify(device_list)
        
    except Exception as e:
        logger.error(f"Get devices error: {e}")
        return jsonify({"error": "Failed to get devices"}), 500

@app.route('/api/builder/interfaces/<device>', methods=['GET'])
def get_interfaces(device):
    """Get available interfaces for a device"""
    try:
        # Generate interfaces like in CLI (ge100-0/0/1 through ge100-0/0/48)
        interfaces = []
        for i in range(1, 49):
            interfaces.append(f"ge100-0/0/{i}")
        
        # Add bundle interfaces
        bundle_interfaces = [
            "bundle-60000", "bundle-60001", "bundle-60002", "bundle-60003",
            "bundle-60004", "bundle-60005", "bundle-60006", "bundle-60007"
        ]
        interfaces.extend(bundle_interfaces)
        
        return jsonify(interfaces)
        
    except Exception as e:
        logger.error(f"Get interfaces error: {e}")
        return jsonify({"error": "Failed to get interfaces"}), 500

@app.route('/api/builder/validate', methods=['POST'])
def validate_builder_configuration():
    """Validate bridge domain configuration"""
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['username', 'vlanId', 'sourceDevice', 'sourceInterface', 'destinations']
        for field in required_fields:
            if field not in data:
                return jsonify({"valid": False, "errors": [f"Missing required field: {field}"]})
        
        # Additional validation logic here
        errors = []
        
        if not data['username']:
            errors.append("Username is required")
        
        if not data['vlanId'] or not data['vlanId'].isdigit():
            errors.append("Valid VLAN ID is required")
        
        if not data['sourceDevice']:
            errors.append("Source device is required")
        
        if not data['sourceInterface']:
            errors.append("Source interface is required")
        
        if not data['destinations'] or len(data['destinations']) == 0:
            errors.append("At least one destination is required")
        
        return jsonify({
            "valid": len(errors) == 0,
            "errors": errors
        })
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"valid": False, "errors": ["Internal validation error"]}), 500

@app.route('/api/builder/generate', methods=['POST'])
def generate_builder_configuration():
    """Generate bridge domain configuration"""
    try:
        data = request.get_json()
        logger.info(f"Received configuration request: {data}")
        
        # Extract configuration data
        username = data.get('username', '')
        vlan_id = data.get('vlanId', '')
        source_device = data.get('sourceDevice', '')
        source_interface = data.get('sourceInterface', '')
        destinations = data.get('destinations', [])
        
        # Validate required fields
        if not username:
            return jsonify({"success": False, "error": "Username is required"}), 400
        if not vlan_id:
            return jsonify({"success": False, "error": "VLAN ID is required"}), 400
        if not source_device:
            return jsonify({"success": False, "error": "Source device is required"}), 400
        if not source_interface:
            return jsonify({"success": False, "error": "Source interface is required"}), 400
        if not destinations or len(destinations) == 0:
            return jsonify({"success": False, "error": "At least one destination is required"}), 400
        
        # Generate service name
        service_name = f"g_{username}_v{vlan_id}"
        logger.info(f"Generated service name: {service_name}")
        
        # Convert destinations to the format expected by unified builder
        dest_list = []
        for dest in destinations:
            dest_list.append({
                'device': dest['device'],
                'port': dest['interfaceName']
            })
        
        logger.info(f"Converted destinations: {dest_list}")
        
        # Check if devices.yaml exists and has data
        if not Path("devices.yaml").exists():
            return jsonify({"success": False, "error": "devices.yaml not found. Please populate devices from inventory first."}), 500
        
        with open("devices.yaml", 'r') as f:
            devices_data = yaml.safe_load(f)
        
        if not devices_data or 'defaults' not in devices_data:
            return jsonify({"success": False, "error": "devices.yaml is empty or invalid. Please populate devices from inventory first."}), 500
        
        # Check if source device exists in devices.yaml
        if source_device not in devices_data:
            return jsonify({"success": False, "error": f"Source device '{source_device}' not found in devices.yaml"}), 400
        
        # Check if destination devices exist in devices.yaml
        missing_devices = []
        for dest in dest_list:
            if dest['device'] not in devices_data:
                missing_devices.append(dest['device'])
        
        if missing_devices:
            return jsonify({"success": False, "error": f"Destination devices not found in devices.yaml: {', '.join(missing_devices)}"}), 400
        
        # Check topology data for spine connections
        topology_file = Path("topology/enhanced_topology.json")
        if topology_file.exists():
            with open(topology_file, 'r') as f:
                topology_data = json.load(f)
            
            devices = topology_data.get('devices', {})
            source_device_info = devices.get(source_device, {})
            connected_spines = source_device_info.get('connected_spines', [])
            
            if not connected_spines:
                # Check if there are any connections in the connections array
                connections = source_device_info.get('connections', [])
                spine_connections = [conn for conn in connections if 'DNAAS-SPINE' in conn.get('target_device', '')]
                
                if spine_connections:
                    spine_devices = list(set([conn['target_device'] for conn in spine_connections]))
                    return jsonify({
                        "success": False, 
                        "error": f"Source device '{source_device}' has spine connections but they are not properly formatted in topology data",
                        "details": f"Found spine connections to: {', '.join(spine_devices)}. The topology data needs to be updated to include these in the 'connected_spines' array."
                    }), 500
                else:
                    return jsonify({
                        "success": False, 
                        "error": f"Source device '{source_device}' has no spine connections in topology data",
                        "details": "This device cannot be used as a source for bridge domain configuration because it has no spine connections."
                    }), 500
        
        # Use the unified builder to generate configuration
        try:
            logger.info(f"Calling unified builder with: service_name={service_name}, vlan_id={vlan_id}, source_device={source_device}, source_interface={source_interface}, destinations={dest_list}")
            
            result = builder.build_bridge_domain_config(
                service_name=service_name,
                vlan_id=int(vlan_id),
                source_device=source_device,
                source_interface=source_interface,
                destinations=dest_list
            )
            
            # Handle both old format (dict) and new format (tuple with metadata)
            if isinstance(result, tuple):
                config_data, metadata = result
                logger.info(f"Unified builder returned config_data and metadata separately")
            else:
                config_data = result
                metadata = None
                logger.info(f"Unified builder returned config_data only (legacy format)")
            
            logger.info(f"Unified builder returned: {config_data}")
            
        except Exception as e:
            logger.error(f"Unified builder error: {e}")
            import traceback
            full_traceback = traceback.format_exc()
            logger.error(f"Full traceback: {full_traceback}")
            return jsonify({
                "success": False, 
                "error": f"Configuration generation failed: {str(e)}",
                "details": full_traceback
            }), 500
        
        if config_data:
            # Save configuration to database only (no file system)
            logger.info("=" * 50)
            logger.info("DATABASE SAVE DEBUG START")
            logger.info("=" * 50)
            
            # Get current count
            current_count = db_manager.get_configuration_count()
            logger.info(f"Current configurations in database: {current_count}")
            
            # Save configuration to database only
            save_success = db_manager.save_configuration(
                service_name=service_name,
                vlan_id=int(vlan_id),
                config_data=config_data,
                file_path=None,  # No file path needed
                config_metadata=metadata  # Pass metadata separately
            )
            
            if save_success:
                logger.info("✅ Database save successful")
                
                # Verify the save
                if db_manager.verify_save(service_name):
                    logger.info("✅ Database save verified")
                else:
                    logger.error("❌ Database save verification failed")
            else:
                logger.error("❌ Database save failed")
            
            # Get new count
            new_count = db_manager.get_configuration_count()
            logger.info(f"New configurations count: {new_count}")
            
            logger.info("=" * 50)
            logger.info("DATABASE SAVE DEBUG END")
            logger.info("=" * 50)
                
            return jsonify({
                "success": True,
                "config": config_data,
                "serviceName": service_name,
                "message": "Configuration saved to database successfully"
            })
        else:
            logger.error("Unified builder returned None/empty config")
            return jsonify({
                "success": False, 
                "error": "Failed to generate configuration - builder returned empty result",
                "details": "The unified builder did not generate any configuration. This might be due to topology issues or missing device connections."
            }), 500
        
    except Exception as e:
        logger.error(f"Generate configuration error: {e}")
        import traceback
        full_traceback = traceback.format_exc()
        logger.error(f"Full traceback: {full_traceback}")
        return jsonify({
            "success": False, 
            "error": f"Configuration generation failed: {str(e)}",
            "details": full_traceback
        }), 500

# ============================================================================
# BRIDGE DOMAIN DISCOVERY & VISUALIZATION ENDPOINTS
# ============================================================================

@app.route('/api/bridge-domains/discover', methods=['POST'])
def discover_bridge_domains():
    """Discover existing bridge domains across the network"""
    try:
        from config_engine.bridge_domain_discovery import BridgeDomainDiscovery
        
        discovery = BridgeDomainDiscovery()
        result = discovery.run_discovery()
        
        if result:
            return jsonify({
                "success": True,
                "message": "Bridge domain discovery completed successfully",
                "discovered_count": len(result.get('bridge_domains', {})),
                "mapping_file": str(discovery.output_dir / f"bridge_domain_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            })
        else:
            return jsonify({
                "success": False,
                "error": "Bridge domain discovery failed"
            }), 500
            
    except Exception as e:
        logger.error(f"Bridge domain discovery error: {e}")
        return jsonify({
            "success": False,
            "error": f"Bridge domain discovery failed: {str(e)}"
        }), 500

@app.route('/api/bridge-domains/list', methods=['GET'])
def list_bridge_domains():
    """Get list of discovered bridge domains"""
    try:
        from config_engine.bridge_domain_visualization import BridgeDomainVisualization
        
        visualization = BridgeDomainVisualization()
        mapping = visualization.load_latest_mapping()
        
        if not mapping:
            return jsonify({
                "success": False,
                "error": "No bridge domain mapping found. Please run discovery first."
            }), 404
        
        bridge_domains = mapping.get('bridge_domains', {})
        bridge_domain_list = []
        
        for name, data in bridge_domains.items():
            topology_analysis = data.get('topology_analysis', {})
            bridge_domain_list.append({
                "name": name,
                "vlan": data.get('detected_vlan', 'unknown'),
                "username": data.get('detected_username', 'unknown'),
                "confidence": data.get('confidence', 0),
                "topology_type": data.get('topology_type', 'unknown'),
                "total_devices": len(data.get('devices', {})),
                "total_interfaces": topology_analysis.get('total_interfaces', 0),
                "access_interfaces": topology_analysis.get('access_interfaces', 0),
                "path_complexity": topology_analysis.get('path_complexity', 'unknown'),
                "detection_method": data.get('detection_method', 'unknown')
            })
        
        return jsonify({
            "success": True,
            "bridge_domains": bridge_domain_list,
            "total_count": len(bridge_domain_list),
            "summary": mapping.get('topology_summary', {})
        })
        
    except Exception as e:
        logger.error(f"List bridge domains error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to list bridge domains: {str(e)}"
        }), 500

@app.route('/api/bridge-domains/<bridge_domain_name>/details', methods=['GET'])
def get_bridge_domain_details(bridge_domain_name):
    """Get detailed information about a specific bridge domain"""
    try:
        from config_engine.bridge_domain_visualization import BridgeDomainVisualization
        
        visualization = BridgeDomainVisualization()
        mapping = visualization.load_latest_mapping()
        
        if not mapping:
            return jsonify({
                "success": False,
                "error": "No bridge domain mapping found. Please run discovery first."
            }), 404
        
        bridge_domains = mapping.get('bridge_domains', {})
        bridge_domain_data = bridge_domains.get(bridge_domain_name)
        
        if not bridge_domain_data:
            return jsonify({
                "success": False,
                "error": f"Bridge domain '{bridge_domain_name}' not found"
            }), 404
        
        return jsonify({
            "success": True,
            "bridge_domain": bridge_domain_data
        })
        
    except Exception as e:
        logger.error(f"Get bridge domain details error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get bridge domain details: {str(e)}"
        }), 500

@app.route('/api/bridge-domains/<bridge_domain_name>/visualize', methods=['GET'])
def visualize_bridge_domain(bridge_domain_name):
    """Generate visualization for a specific bridge domain"""
    try:
        from config_engine.bridge_domain_visualization import BridgeDomainVisualization
        
        visualization = BridgeDomainVisualization()
        mapping = visualization.load_latest_mapping()
        
        if not mapping:
            return jsonify({
                "success": False,
                "error": "No bridge domain mapping found. Please run discovery first."
            }), 404
        
        # Generate visualization
        viz_result = visualization.visualize_bridge_domain_topology(bridge_domain_name, mapping)
        
        if viz_result.startswith("❌"):
            return jsonify({
                "success": False,
                "error": viz_result
            }), 404
        
        # Generate details
        bridge_domain_data = mapping.get('bridge_domains', {}).get(bridge_domain_name)
        if bridge_domain_data:
            details = visualization.generate_bridge_domain_details(bridge_domain_data)
        else:
            details = "Details not available"
        
        return jsonify({
            "success": True,
            "visualization": viz_result,
            "details": details,
            "bridge_domain_name": bridge_domain_name
        })
        
    except Exception as e:
        logger.error(f"Visualize bridge domain error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to visualize bridge domain: {str(e)}"
        }), 500

@app.route('/api/bridge-domains/search', methods=['GET'])
def search_bridge_domains():
    """Search bridge domains by name, VLAN, or username"""
    try:
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify({
                "success": False,
                "error": "Search query is required"
            }), 400
        
        from config_engine.bridge_domain_visualization import BridgeDomainVisualization
        
        visualization = BridgeDomainVisualization()
        mapping = visualization.load_latest_mapping()
        
        if not mapping:
            return jsonify({
                "success": False,
                "error": "No bridge domain mapping found. Please run discovery first."
            }), 404
        
        bridge_domains = mapping.get('bridge_domains', {})
        results = []
        
        for name, data in bridge_domains.items():
            # Search in name, VLAN, and username
            if (query in name.lower() or 
                query in str(data.get('detected_vlan', '')).lower() or
                query in str(data.get('detected_username', '')).lower()):
                
                topology_analysis = data.get('topology_analysis', {})
                results.append({
                    "name": name,
                    "vlan": data.get('detected_vlan', 'unknown'),
                    "username": data.get('detected_username', 'unknown'),
                    "confidence": data.get('confidence', 0),
                    "topology_type": data.get('topology_type', 'unknown'),
                    "total_devices": len(data.get('devices', {})),
                    "total_interfaces": topology_analysis.get('total_interfaces', 0),
                    "access_interfaces": topology_analysis.get('access_interfaces', 0),
                    "path_complexity": topology_analysis.get('path_complexity', 'unknown'),
                    "detection_method": data.get('detection_method', 'unknown')
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "total_count": len(results),
            "query": query
        })
        
    except Exception as e:
        logger.error(f"Search bridge domains error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to search bridge domains: {str(e)}"
        }), 500

# ============================================================================
# FILE MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/files/list', methods=['GET'])
def list_files():
    """List files in the project directory"""
    try:
        path = request.args.get('path', '.')
        base_path = Path(path)
        
        if not base_path.exists():
            return jsonify({"error": "Path not found"}), 404
        
        files = []
        for item in base_path.iterdir():
            if item.name.startswith('.'):
                continue  # Skip hidden files
            
            file_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            }
            files.append(file_info)
        
        # Sort: directories first, then files
        files.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        
        return jsonify({
            "path": str(base_path),
            "files": files
        })
        
    except Exception as e:
        logger.error(f"List files error: {e}")
        return jsonify({"error": "Failed to list files"}), 500

@app.route('/api/files/download/<path:filepath>', methods=['GET'])
def download_file(filepath):
    """Download a file"""
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Download file error: {e}")
        return jsonify({"error": "Failed to download file"}), 500

@app.route('/api/files/content/<path:filepath>', methods=['GET'])
def get_file_content(filepath):
    """Get file content as text"""
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        if not file_path.is_file():
            return jsonify({"error": "Not a file"}), 400
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "content": content,
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get file content error: {e}")
        return jsonify({"error": "Failed to read file content"}), 500

@app.route('/api/files/delete/<path:filepath>', methods=['DELETE'])
def delete_file(filepath):
    """Delete a file"""
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        # Only allow deletion of files in configs directories for safety
        if not (str(file_path).startswith('configs/') or str(file_path).startswith('./configs/')):
            return jsonify({"error": "Can only delete files in configs directory"}), 403
        
        file_path.unlink()
        
        return jsonify({
            "success": True,
            "message": f"File {file_path.name} deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return jsonify({"error": "Failed to delete file"}), 500

@app.route('/api/files/save-config', methods=['POST'])
def save_file_configuration():
    """Save generated configuration to pending directory"""
    try:
        data = request.get_json()
        config_content = data.get('content')
        filename = data.get('filename')
        
        if not config_content:
            return jsonify({"error": "Configuration content is required"}), 400
        
        if not filename:
            return jsonify({"error": "Filename is required"}), 400
        
        # Ensure configs/pending directory exists
        pending_dir = Path("configs/pending")
        pending_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the configuration
        config_path = pending_dir / filename
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return jsonify({
            "success": True,
            "message": f"Configuration saved as {filename}",
            "path": str(config_path)
        })
        
    except Exception as e:
        logger.error(f"Save configuration error: {e}")
        return jsonify({"error": "Failed to save configuration"}), 500

# ============================================================================
# DEPLOYMENT MANAGEMENT ENDPOINTS (LEGACY - REMOVED)
# ============================================================================
# Note: These endpoints have been replaced by the unified configuration endpoints
# below. The old deployment endpoints caused function name conflicts.

@app.route('/api/deployments/list', methods=['GET'])
def list_deployments():
    """List pending and deployed configurations"""
    try:
        deployments = []
        
        # Check configs/pending directory
        pending_dir = Path("configs/pending")
        if pending_dir.exists():
            for config_file in pending_dir.glob("*.yaml"):
                deployments.append({
                    "name": config_file.stem,
                    "status": "pending",
                    "filename": config_file.name,
                    "modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                })
        
        # Check configs/deployed directory
        deployed_dir = Path("configs/deployed")
        if deployed_dir.exists():
            for config_file in deployed_dir.glob("*.yaml"):
                deployments.append({
                    "name": config_file.stem,
                    "status": "deployed",
                    "filename": config_file.name,
                    "modified": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
                })
        
        return jsonify(deployments)
        
    except Exception as e:
        logger.error(f"List deployments error: {e}")
        return jsonify({"error": "Failed to list deployments"}), 500

@app.route('/api/deployments/start', methods=['POST'])
def start_deployment():
    """Start a configuration deployment"""
    try:
        data = request.get_json()
        config_filename = data.get('filename')
        
        if not config_filename:
            return jsonify({"error": "Filename is required"}), 400
        
        # Generate deployment ID
        deployment_id = f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start deployment in background (placeholder)
        # In production, use Celery or similar for background tasks
        
        return jsonify({
            "success": True,
            "deploymentId": deployment_id,
            "message": "Deployment started"
        })
        
    except Exception as e:
        logger.error(f"Start deployment error: {e}")
        return jsonify({"error": "Failed to start deployment"}), 500

@app.route('/api/deployments/configurations', methods=['GET'])
@token_required
def get_user_configurations(current_user):
    """Get user's configurations for deployment management"""
    try:
        # Get configurations for the current user
        configs = Configuration.query.filter_by(user_id=current_user.id).all()
        
        configurations = []
        for config in configs:
            config_dict = config.to_dict()
            # Parse config_data if it's JSON
            if config.config_data:
                try:
                    import json
                    config_dict['config_data'] = json.dumps(json.loads(config.config_data), indent=2)
                except:
                    config_dict['config_data'] = config.config_data
            
            configurations.append(config_dict)
        
        return jsonify({
            "success": True,
            "configurations": configurations
        })
        
    except Exception as e:
        logger.error(f"Get configurations error: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to get configurations"
        }), 500

@app.route('/api/deployments/test', methods=['GET'])
def test_deployments():
    """Test route for deployments"""
    return jsonify({
        "success": True,
        "message": "Deployments test route works"
    })

@app.route('/api/deployments/<deployment_id>/status', methods=['GET'])
@token_required
def get_deployment_status(current_user, deployment_id):
    """Get current deployment or removal status"""
    try:
        # Use the global deployment manager instance
        status = deployment_manager.get_deployment_status(deployment_id)
        
        if status:
            return jsonify({
                'success': True,
                'deployment_id': deployment_id,
                'status': status['status'],
                'progress': status['progress'],
                'stage': status['stage'],
                'logs': status['logs'][-20:],  # Last 20 log entries
                'errors': status.get('errors', []),
                'device_results': status.get('device_results', {}),
                'start_time': status['start_time'],
                'end_time': status.get('end_time'),
                'timestamp': status['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Deployment/removal not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get status: {str(e)}'
        }), 500

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'data': 'Connected to Lab Automation API'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscription(data):
    """Handle deployment subscription"""
    deployment_id = data.get('deploymentId')
    if deployment_id:
        join_room(deployment_id)
        logger.info(f"Client {request.sid} subscribed to deployment {deployment_id}")
        
        # Send current status immediately
        deployment_info = deployment_manager.get_deployment_status(deployment_id)
        if deployment_info:
            emit('deployment_update', {
                'deployment_id': deployment_id,
                'status': deployment_info['status'],
                'progress': deployment_info['progress'],
                'stage': deployment_info['stage'],
                'logs': deployment_info['logs'][-10:],
                'errors': deployment_info.get('errors', []),
                'device_results': deployment_info.get('device_results', {}),
                'timestamp': datetime.utcnow().isoformat()
            })

@socketio.on('unsubscribe')
def handle_unsubscription(data):
    """Handle deployment unsubscription"""
    deployment_id = data.get('deploymentId')
    if deployment_id:
        leave_room(deployment_id)
        logger.info(f"Client {request.sid} unsubscribed from deployment {deployment_id}")

def emit_deployment_progress(deployment_id, progress_data):
    """Emit deployment progress to subscribed clients"""
    socketio.emit('deployment_update', progress_data, room=deployment_id)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": VERSION
    })

@app.route('/api/database/health', methods=['GET'])
def database_health_check():
    """Check database health and test save operations"""
    try:
        # Perform database health check
        health_result = db_manager.health_check()
        
        return jsonify({
            "success": True,
            **health_result
        })
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return jsonify({
            "success": False,
            "database_healthy": False,
            "error": str(e)
        }), 500

# ============================================================================
# UNIFIED CONFIGURATION MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/configurations', methods=['GET'])
@token_required
def get_configurations(current_user):
    """Get all configurations for the current user"""
    try:
        # Get configurations from database
        configurations = Configuration.query.filter_by(user_id=current_user.id).order_by(Configuration.created_at.desc()).all()
        
        config_list = []
        for config in configurations:
            config_list.append({
                'id': config.id,
                'service_name': config.service_name,
                'vlan_id': config.vlan_id,
                'config_type': config.config_type,
                'status': config.status,
                'config_data': config.config_data,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'deployed_at': config.deployed_at.isoformat() if config.deployed_at else None,
                'deployed_by': config.deployed_by
            })
        
        return jsonify({
            "success": True,
            "configurations": config_list,
            "total": len(config_list)
        })
        
    except Exception as e:
        logger.error(f"Get configurations error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get configurations: {str(e)}"
        }), 500

@app.route('/api/test/metadata', methods=['GET'])
def test_metadata():
    """Test endpoint for metadata"""
    return jsonify({
        "success": True,
        "message": "Test metadata endpoint works"
    })

@app.route('/api/configurations/<int:config_id>/metadata', methods=['GET'])
@token_required
@user_ownership_required
def get_configuration_metadata(current_user, config_id):
    """Get metadata for a specific configuration"""
    try:
        # Get configuration from database
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Parse metadata if it exists
        metadata = None
        if config.config_metadata:
            try:
                metadata = json.loads(config.config_metadata)
            except json.JSONDecodeError:
                return jsonify({
                    "success": False,
                    "error": "Invalid metadata format"
                }), 500
        
        return jsonify({
            "success": True,
            "metadata": metadata,
            "service_name": config.service_name,
            "vlan_id": config.vlan_id
        })
        
    except Exception as e:
        logger.error(f"Error getting configuration metadata: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get configuration metadata: {str(e)}"
        }), 500

@app.route('/api/configurations/<int:config_id>/preview-deployment', methods=['GET'])
@token_required
@user_ownership_required
def preview_deployment_commands(current_user, config_id):
    """Preview deployment commands for a configuration"""
    try:
        # Get configuration details
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Import SSH push manager for preview
        from config_engine.ssh_push_manager import SSHPushManager
        push_manager = SSHPushManager()
        
        # Get deployment preview
        success, errors, device_commands = push_manager.preview_cli_commands(config.service_name)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Failed to generate deployment preview: {'; '.join(errors)}"
            }), 400
        
        # Format the preview for display
        preview_data = {
            "configuration": {
                "id": config.id,
                "service_name": config.service_name,
                "vlan_id": config.vlan_id,
                "status": config.status,
                "devices": list(device_commands.keys())
            },
            "deployment_commands": device_commands,
            "total_devices": len(device_commands),
            "total_commands": sum(len(cmds) for cmds in device_commands.values())
        }
        
        return jsonify({
            "success": True,
            "preview": preview_data
        })
        
    except Exception as e:
        logger.error(f"Error previewing deployment commands: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to preview deployment commands: {str(e)}"
        }), 500

@app.route('/api/configurations/<int:config_id>', methods=['GET'])
@token_required
@user_ownership_required
def get_configuration_details(current_user, config_id):
    """Get detailed configuration information"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Parse configuration data
        import json
        config_data = json.loads(config.config_data) if config.config_data else {}
        
        return jsonify({
            "success": True,
            "configuration": {
                'id': config.id,
                'service_name': config.service_name,
                'vlan_id': config.vlan_id,
                'config_type': config.config_type,
                'status': config.status,
                'config_data': config_data,
                'created_at': config.created_at.isoformat() if config.created_at else None,
                'deployed_at': config.deployed_at.isoformat() if config.deployed_at else None,
                'deployed_by': config.deployed_by
            }
        })
        
    except Exception as e:
        logger.error(f"Get configuration details error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get configuration details: {str(e)}"
        }), 500

@app.route('/api/configurations/<int:config_id>/validate', methods=['POST'])
@token_required
@user_ownership_required
def validate_unified_configuration(current_user, config_id):
    """Validate a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Parse configuration data
        import json
        config_data = json.loads(config.config_data) if config.config_data else {}
        
        if not config_data:
            return jsonify({
                "success": False,
                "error": "Configuration data is empty"
            }), 400
        
        # Check that we have devices in the configuration
        devices = list(config_data.keys())
        if not devices:
            return jsonify({
                "success": False,
                "error": "No devices found in configuration"
            }), 400
        
        # Validate device connectivity
        validation_errors = []
        for device in devices:
            # Check if device exists in devices.yaml
            if not Path("devices.yaml").exists():
                validation_errors.append("devices.yaml not found")
                break
            
            with open("devices.yaml", 'r') as f:
                devices_data = yaml.safe_load(f)
            
            if device not in devices_data:
                validation_errors.append(f"Device '{device}' not found in devices.yaml")
        
        if validation_errors:
            return jsonify({
                "success": False,
                "error": "Configuration validation failed",
                "details": validation_errors
            }), 400
        
        return jsonify({
            "success": True,
            "message": f"Configuration validated successfully for {len(devices)} devices",
            "device_count": len(devices)
        })
        
    except Exception as e:
        logger.error(f"Validate configuration error: {e}")
        return jsonify({
            "success": False,
            "error": f"Validation failed: {str(e)}"
        }), 500

@app.route('/api/configurations/<int:config_id>/deploy', methods=['POST'])
@token_required
@user_ownership_required
def deploy_unified_configuration(current_user, config_id):
    """Deploy a configuration via SSH with real-time progress"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Generate deployment ID
        deployment_id = f"deploy_{config_id}_{int(datetime.now().timestamp())}"
        
        # Parse configuration data
        import json
        config_data = json.loads(config.config_data) if config.config_data else {}
        
        if not config_data:
            return jsonify({
                "success": False,
                "error": "Configuration data is empty"
            }), 400
        
        # Start deployment with real-time progress
        success = deployment_manager.start_deployment(
            deployment_id=deployment_id,
            config_id=config_id,
            config_data=config_data,
            user_id=current_user.id
        )
        
        if not success:
            return jsonify({
                "success": False,
                "error": "Failed to start deployment"
            }), 500
        
        # Create audit log for deployment start
        create_audit_log(current_user.id, 'deploy_start', 'configuration', config_id, {
            'service_name': config.service_name,
            'deployment_id': deployment_id
        })
        
        return jsonify({
            "success": True,
            "deploymentId": deployment_id,
            "message": "Deployment started with real-time progress monitoring"
        })
        
    except Exception as e:
        logger.error(f"Deploy configuration error: {e}")
        return jsonify({
            "success": False,
            "error": f"Deployment failed: {str(e)}"
        }), 500

@app.route('/api/configurations/<int:config_id>', methods=['DELETE'])
@token_required
@user_ownership_required
def delete_unified_configuration(current_user, config_id):
    """Delete a configuration"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Check if configuration is currently being deployed
        deployment_info = deployment_manager.get_deployment_status(f"deploy_{config_id}_*")
        if deployment_info and deployment_info.get('status') == 'running':
            return jsonify({
                "success": False,
                "error": "Cannot delete configuration while deployment is in progress"
            }), 400
        
        # Delete the configuration
        db.session.delete(config)
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'delete', 'configuration', config_id, {
            'service_name': config.service_name
        })
        
        return jsonify({
            "success": True,
            "message": f"Configuration '{config.service_name}' deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Delete configuration error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to delete configuration: {str(e)}"
        }), 500

@app.route('/api/configurations/<int:config_id>/export', methods=['POST'])
@token_required
@user_ownership_required
def export_configuration(current_user, config_id):
    """Export configuration to file (optional feature)"""
    try:
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Parse configuration data
        import json
        config_data = json.loads(config.config_data) if config.config_data else {}
        
        # Create export directory
        export_dir = Path("configs/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{config.service_name}_{timestamp}.yaml"
        file_path = export_dir / filename
        
        # Save to file
        with open(file_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        return jsonify({
            "success": True,
            "message": f"Configuration exported to {filename}",
            "file_path": str(file_path)
        })
        
    except Exception as e:
        logger.error(f"Export configuration error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to export configuration: {str(e)}"
        }), 500

# ============================================================================
# DEPLOYMENT ENDPOINTS
# ============================================================================

@app.route('/api/deployments/<int:config_id>/preview-deletion', methods=['GET'])
@token_required
@user_ownership_required
def preview_deletion_commands(current_user, config_id):
    """Preview deletion commands for a configuration"""
    try:
        # Get configuration details
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Import SSH push manager for preview
        from config_engine.ssh_push_manager import SSHPushManager
        push_manager = SSHPushManager()
        
        # Get deletion preview
        success, errors, device_commands = push_manager.preview_deletion_commands(config.service_name)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"Failed to generate deletion preview: {'; '.join(errors)}"
            }), 400
        
        # Format the preview for display
        preview_data = {
            "configuration": {
                "id": config.id,
                "service_name": config.service_name,
                "vlan_id": config.vlan_id,
                "status": config.status,
                "devices": list(device_commands.keys())
            },
            "deletion_commands": device_commands,
            "total_devices": len(device_commands),
            "total_commands": sum(len(cmds) for cmds in device_commands.values())
        }
        
        return jsonify({
            "success": True,
            "preview": preview_data
        })
        
    except Exception as e:
        logger.error(f"Error previewing deletion commands: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to preview deletion commands: {str(e)}"
        }), 500

@app.route('/api/deployments/<int:config_id>/remove', methods=['POST'])
@token_required
@user_ownership_required
def remove_from_devices(current_user, config_id):
    """Remove a configuration from devices with progress tracking"""
    try:
        # Get configuration details
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Create a unique removal ID for tracking
        removal_id = f"remove_{config_id}_{int(time.time())}"
        
        # Start removal in background with progress tracking
        from deployment_manager import DeploymentManager
        deployment_manager = DeploymentManager(socketio)
        
        # Start the removal process
        success = deployment_manager.start_removal(
            removal_id, config_id, config.config_data, current_user.id
        )
        
        if success:
            return jsonify({
                'success': True, 
                'message': 'Configuration removal started',
                'removal_id': removal_id
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to start removal'}), 500
        
    except Exception as e:
        logger.error(f"Error starting removal: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/deployments/<int:config_id>/restore', methods=['POST'])
@token_required
@user_ownership_required
def restore_configuration(current_user, config_id):
    """Restore a deleted configuration to pending status"""
    try:
        # Get configuration details
        config = Configuration.query.get(config_id)
        if not config:
            return jsonify({
                "success": False,
                "error": "Configuration not found"
            }), 404
        
        # Update configuration status to 'pending'
        config.status = 'pending'
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'restore', 'configuration', config_id, {
            'service_name': config.service_name
        })
        
        return jsonify({
            "success": True,
            "message": f"Configuration '{config.service_name}' restored successfully"
        })
        
    except Exception as e:
        logger.error(f"Error restoring configuration: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to restore configuration: {str(e)}"
        }), 500

# ============================================================================
# ADMIN USER MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/admin/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        users_data = []
        
        for user in users:
            user_data = user.to_dict()
            # Add additional info for admin view
            user_data['configurations_count'] = len(user.configurations)
            user_data['personal_bridge_domains_count'] = len(user.personal_bridge_domains)
            users_data.append(user_data)
        
        return jsonify({
            "success": True,
            "users": users_data
        })
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get users: {str(e)}"
        }), 500

@app.route('/api/admin/users', methods=['POST'])
@token_required
@admin_required
def create_user(current_user):
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({
                "success": False,
                "error": "Username, email, and password are required"
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({
                "success": False,
                "error": "Username already exists"
            }), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                "success": False,
                "error": "Email already exists"
            }), 409
        
        # Create user
        user = User(
            username=username,
            email=email,
            password=password,
            role=data.get('role', 'user'),
            created_by=current_user.id
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create VLAN allocations
        vlan_ranges = data.get('vlanRanges', [])
        for vlan_range in vlan_ranges:
            vlan_allocation = UserVlanAllocation(
                user_id=user.id,
                start_vlan=vlan_range['startVlan'],
                end_vlan=vlan_range['endVlan'],
                description=vlan_range.get('description', '')
            )
            db.session.add(vlan_allocation)
        
        # Create permissions
        permissions_data = data.get('permissions', {})
        user_permissions = UserPermission(
            user_id=user.id,
            can_edit_topology=permissions_data.get('canEditTopology', True),
            can_deploy_changes=permissions_data.get('canDeployChanges', True),
            can_view_global=permissions_data.get('canViewGlobal', False),
            can_edit_others=permissions_data.get('canEditOthers', False),
            max_bridge_domains=permissions_data.get('maxBridgeDomains', 50),
            require_approval=permissions_data.get('requireApproval', False)
        )
        db.session.add(user_permissions)
        
        # Create user directories
        from auth import ensure_user_directories
        ensure_user_directories(user.id)
        
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'create', 'user', user.id, {
            'username': username,
            'email': email,
            'role': user.role,
            'vlan_ranges': vlan_ranges
        })
        
        return jsonify({
            "success": True,
            "message": f"User '{username}' created successfully",
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to create user: {str(e)}"
        }), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id):
    """Update user (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        data = request.get_json()
        
        # Update basic user info
        if 'username' in data:
            # Check if username is already taken by another user
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({
                    "success": False,
                    "error": "Username already exists"
                }), 409
            user.username = data['username']
        
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user_id:
                return jsonify({
                    "success": False,
                    "error": "Email already exists"
                }), 409
            user.email = data['email']
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        if 'role' in data:
            user.role = data['role']
            user.is_admin = (data['role'] == 'admin')
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        # Update VLAN allocations
        if 'vlanRanges' in data:
            # Remove existing allocations
            UserVlanAllocation.query.filter_by(user_id=user_id).delete()
            
            # Create new allocations
            for vlan_range in data['vlanRanges']:
                vlan_allocation = UserVlanAllocation(
                    user_id=user_id,
                    start_vlan=vlan_range['startVlan'],
                    end_vlan=vlan_range['endVlan'],
                    description=vlan_range.get('description', '')
                )
                db.session.add(vlan_allocation)
        
        # Update permissions
        if 'permissions' in data:
            permissions_data = data['permissions']
            if user.permissions:
                user.permissions.can_edit_topology = permissions_data.get('canEditTopology', True)
                user.permissions.can_deploy_changes = permissions_data.get('canDeployChanges', True)
                user.permissions.can_view_global = permissions_data.get('canViewGlobal', False)
                user.permissions.can_edit_others = permissions_data.get('canEditOthers', False)
                user.permissions.max_bridge_domains = permissions_data.get('maxBridgeDomains', 50)
                user.permissions.require_approval = permissions_data.get('requireApproval', False)
            else:
                # Create permissions if they don't exist
                user_permissions = UserPermission(
                    user_id=user_id,
                    **permissions_data
                )
                db.session.add(user_permissions)
        
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'update', 'user', user_id, {
            'updated_fields': list(data.keys())
        })
        
        return jsonify({
            "success": True,
            "message": f"User '{user.username}' updated successfully",
            "user": user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to update user: {str(e)}"
        }), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    """Delete user (admin only)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({
                "success": False,
                "error": "Cannot delete your own account"
            }), 400
        
        username = user.username
        
        # Delete user (cascades to related records)
        db.session.delete(user)
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'delete', 'user', user_id, {
            'deleted_username': username
        })
        
        return jsonify({
            "success": True,
            "message": f"User '{username}' deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to delete user: {str(e)}"
        }), 500

# ============================================================================
# PERSONAL BRIDGE DOMAIN MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/configurations/import', methods=['POST'])
@token_required
def import_bridge_domain(current_user):
    """Import bridge domain to personal workspace"""
    try:
        data = request.get_json()
        bridge_domain_name = data.get('bridgeDomainName')
        
        if not bridge_domain_name:
            return jsonify({
                "success": False,
                "error": "Bridge domain name is required"
            }), 400
        
        # Check if user has access to this bridge domain (VLAN range check)
        # This would require checking the bridge domain's VLAN against user's VLAN ranges
        # For now, we'll allow import and check access later
        
        # Check if already imported
        existing = PersonalBridgeDomain.query.filter_by(
            user_id=current_user.id,
            bridge_domain_name=bridge_domain_name
        ).first()
        
        if existing:
            return jsonify({
                "success": False,
                "error": "Bridge domain already imported to your workspace"
            }), 409
        
        # Import to personal workspace
        personal_bd = PersonalBridgeDomain(
            user_id=current_user.id,
            bridge_domain_name=bridge_domain_name,
            imported_from_topology=True
        )
        db.session.add(personal_bd)
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'import', 'bridge_domain', None, {
            'bridge_domain_name': bridge_domain_name
        })
        
        return jsonify({
            "success": True,
            "message": f"Bridge domain '{bridge_domain_name}' imported successfully"
        })
        
    except Exception as e:
        logger.error(f"Error importing bridge domain: {e}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to import bridge domain: {str(e)}"
        }), 500

@app.route('/api/configurations/<bridge_domain_name>/scan', methods=['POST'])
@token_required
def scan_bridge_domain_topology(current_user, bridge_domain_name):
    """Scan and reverse engineer bridge domain topology"""
    try:
        # Check ownership
        personal_bd = PersonalBridgeDomain.query.filter_by(
            user_id=current_user.id,
            bridge_domain_name=bridge_domain_name
        ).first()
        
        if not personal_bd:
            return jsonify({
                "success": False,
                "error": "Bridge domain not found in your workspace"
            }), 404
        
        # Perform topology scan (placeholder - would integrate with existing discovery)
        # For now, we'll just mark as scanned
        personal_bd.topology_scanned = True
        personal_bd.last_scan_at = datetime.utcnow()
        db.session.commit()
        
        # Create audit log
        create_audit_log(current_user.id, 'scan', 'bridge_domain', None, {
            'bridge_domain_name': bridge_domain_name
        })
        
        return jsonify({
            "success": True,
            "message": f"Bridge domain '{bridge_domain_name}' topology scanned successfully"
        })
        
    except Exception as e:
        logger.error(f"Error scanning bridge domain: {e}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": f"Failed to scan bridge domain: {str(e)}"
        }), 500

@app.route('/api/dashboard/personal-stats', methods=['GET'])
@token_required
def get_personal_stats(current_user):
    """Get personal statistics for dashboard"""
    try:
        # Get user's personal bridge domains
        personal_bds = PersonalBridgeDomain.query.filter_by(user_id=current_user.id).all()
        
        # Get user's configurations
        user_configs = Configuration.query.filter_by(user_id=current_user.id).all()
        
        # Calculate stats
        stats = {
            'totalBridgeDomains': len(personal_bds),
            'activeBridgeDomains': len([bd for bd in personal_bds if bd.topology_scanned]),
            'totalConfigurations': len(user_configs),
            'activeConfigurations': len([c for c in user_configs if c.status == 'deployed']),
            'vlanRangesUsed': len(current_user.get_vlan_ranges()),
            'lastActivity': current_user.last_login.isoformat() if current_user.last_login else None
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting personal stats: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to get personal stats: {str(e)}"
        }), 500

# ============================================================================
# DEVICE SCANNING ENDPOINTS
# ============================================================================

@app.route('/api/devices/scan', methods=['POST'])
@token_required
def scan_devices(current_user):
    """Scan devices for existing bridge domains and sync to database"""
    try:
        data = request.get_json() or {}
        sync_to_db = data.get('sync', True)
        specific_device = data.get('device')
        
        if specific_device:
            # Scan specific device
            results = device_scanner.scan_device(specific_device)
            return jsonify({
                "success": True,
                "message": f"Scanned device {specific_device}",
                "device": specific_device,
                "bridge_domains": results
            })
        else:
            # Scan all devices
            if sync_to_db:
                # Scan and sync to database
                result = device_scanner.scan_and_sync(current_user.id)
                return jsonify(result)
            else:
                # Just scan without syncing
                results = device_scanner.scan_all_devices()
                return jsonify({
                    "success": True,
                    "message": "Device scan completed",
                    "results": results
                })
                
    except Exception as e:
        logger.error(f"Device scanning error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to scan devices: {str(e)}"
        }), 500

@app.route('/api/devices/scan/preview', methods=['GET'])
@token_required
def preview_device_scan(current_user):
    """Preview what would be discovered without syncing to database"""
    try:
        results = device_scanner.scan_all_devices()
        consolidated = device_scanner.consolidate_bridge_domains(results)
        
        return jsonify({
            "success": True,
            "message": "Device scan preview",
            "scanned_devices": list(results.keys()),
            "found_domains": len(consolidated),
            "configurations": consolidated
        })
        
    except Exception as e:
        logger.error(f"Device scan preview error: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to preview device scan: {str(e)}"
        }), 500

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Lab Automation API Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--production', action='store_true', help='Production mode')
    
    args = parser.parse_args()
    
    if args.production:
        # Production settings
        app.config['DEBUG'] = False
        logger.info("Starting API server in production mode")
    else:
        # Development settings
        app.config['DEBUG'] = args.debug
        logger.info("Starting API server in development mode")
    
    logger.info(f"API server starting on {args.host}:{args.port}")
    socketio.run(app, host=args.host, port=args.port, debug=args.debug, allow_unsafe_werkzeug=True) 