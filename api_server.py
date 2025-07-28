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

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing modules
from config_engine.unified_bridge_domain_builder import UnifiedBridgeDomainBuilder
from scripts.ssh_push_menu import SSHPushMenu
from scripts.inventory_manager import InventoryManager
from scripts.device_status_viewer import DeviceStatusViewer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lab-automation-secret-key-2024'
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global instances
builder = UnifiedBridgeDomainBuilder()
inventory_manager = InventoryManager()
device_viewer = DeviceStatusViewer()

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple authentication endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        # Simple validation (in production, use proper auth)
        if username and password:
            return jsonify({
                "success": True,
                "token": f"token_{username}_{datetime.now().timestamp()}",
                "user": {
                    "username": username,
                    "role": "admin",
                    "permissions": ["read", "write", "deploy"]
                }
            })
        else:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    # In production, validate JWT token
    return jsonify({
        "username": "admin",
        "role": "admin",
        "permissions": ["read", "write", "deploy"]
    })

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
        
        # Count configuration files
        config_files_count = 0
        configs_dir = Path("configs")
        if configs_dir.exists():
            config_files_count = len(list(configs_dir.rglob("*.yaml")))
        
        # Count bridge domains (placeholder)
        bridge_domains_count = 0
        
        # Count active deployments (placeholder)
        active_deployments_count = 0
        
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
        # Placeholder recent activity
        activities = [
            {
                "action": "Bridge Domain Created",
                "device": "spine-01",
                "time": "2 minutes ago",
                "status": "success"
            },
            {
                "action": "Configuration Deployed",
                "device": "leaf-23",
                "time": "15 minutes ago",
                "status": "success"
            },
            {
                "action": "Device Discovery",
                "device": "superspine-02",
                "time": "1 hour ago",
                "status": "warning"
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
def validate_configuration():
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
def generate_configuration():
    """Generate bridge domain configuration"""
    try:
        data = request.get_json()
        
        # Extract configuration data
        username = data.get('username', '')
        vlan_id = data.get('vlanId', '')
        source_device = data.get('sourceDevice', '')
        source_interface = data.get('sourceInterface', '')
        destinations = data.get('destinations', [])
        
        # Generate service name
        service_name = f"g_{username}_v{vlan_id}"
        
        # Use the unified builder to generate configuration
        config_data = builder.build_bridge_domain_config(
            source_device=source_device,
            source_interface=source_interface,
            destinations=destinations,
            username=username,
            vlan_id=vlan_id
        )
        
        if config_data:
            # Save configuration to file
            config_filename = f"unified_bridge_domain_{service_name}.yaml"
            config_path = Path("configs/pending") / config_filename
            
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            return jsonify({
                "success": True,
                "config": config_data,
                "filename": config_filename,
                "serviceName": service_name
            })
        else:
            return jsonify({"success": False, "error": "Failed to generate configuration"}), 500
        
    except Exception as e:
        logger.error(f"Generate configuration error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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

# ============================================================================
# DEPLOYMENT MANAGEMENT ENDPOINTS
# ============================================================================

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

@app.route('/api/deployments/<deployment_id>/status', methods=['GET'])
def get_deployment_status(deployment_id):
    """Get deployment status"""
    try:
        # Placeholder status
        return jsonify({
            "deploymentId": deployment_id,
            "status": "in_progress",
            "progress": 50,
            "message": "Deploying to devices..."
        })
        
    except Exception as e:
        logger.error(f"Get deployment status error: {e}")
        return jsonify({"error": "Failed to get deployment status"}), 500

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
        "version": "1.0.0"
    })

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
    socketio.run(app, host=args.host, port=args.port, debug=args.debug) 