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
CORS(app, origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"])

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
            
            config_data = builder.build_bridge_domain_config(
                service_name=service_name,
                vlan_id=int(vlan_id),
                source_device=source_device,
                source_interface=source_interface,
                destinations=dest_list
            )
            
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
            # Save configuration to file
            config_filename = f"unified_bridge_domain_{service_name}.yaml"
            config_path = Path("configs/pending") / config_filename
            
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            logger.info(f"Configuration saved to: {config_path}")
            
            return jsonify({
                "success": True,
                "config": config_data,
                "filename": config_filename,
                "serviceName": service_name
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
def save_configuration():
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
    socketio.run(app, host=args.host, port=args.port, debug=args.debug, allow_unsafe_werkzeug=True) 