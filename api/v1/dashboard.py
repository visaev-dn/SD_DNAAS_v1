#!/usr/bin/env python3
"""
Dashboard Routes
Provides statistics and recent activity for the dashboard
"""

from flask import jsonify
from datetime import datetime
from pathlib import Path
import yaml
import logging

from api.v1 import api_v1
from api.middleware.auth_middleware import token_required
from models import Configuration, PersonalBridgeDomain

logger = logging.getLogger(__name__)


@api_v1.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Count devices from devices.yaml
        devices_count = 0
        if Path("devices.yaml").exists():
            with open("devices.yaml", 'r') as f:
                devices = yaml.safe_load(f) or {}
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


@api_v1.route('/dashboard/recent-activity', methods=['GET'])
def get_recent_activity():
    """Get recent activity for dashboard"""
    try:
        activities = []
        
        # Recent bridge domain configurations
        pending_dir = Path("configs/pending")
        if pending_dir.exists():
            for config_file in pending_dir.glob("*.yaml"):
                if "bridge_domain" in config_file.name or "unified_bridge_domain" in config_file.name:
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
                        "action": "Bridge Domain Created",
                        "device": config_file.stem,
                        "time": time_ago,
                        "status": "success"
                    })
        
        # Recent deployments
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
        
        return jsonify({
            "activities": activities,
            "total": len(activities)
        })
        
    except Exception as e:
        logger.error(f"Recent activity error: {e}")
        return jsonify({"error": "Failed to get recent activity"}), 500


@api_v1.route('/dashboard/personal-stats', methods=['GET'])
@token_required
def get_personal_stats(current_user):
    """Get personal statistics for dashboard"""
    try:
        personal_bds = PersonalBridgeDomain.query.filter_by(user_id=current_user.id).all()
        user_configs = Configuration.query.filter_by(user_id=current_user.id).all()
        
        stats = {
            'totalBridgeDomains': len(personal_bds),
            'activeBridgeDomains': len([bd for bd in personal_bds if getattr(bd, 'topology_scanned', False)]),
            'totalConfigurations': len(user_configs),
            'activeConfigurations': len([c for c in user_configs if getattr(c, 'status', '') == 'deployed']),
            'vlanRangesUsed': len(getattr(current_user, 'get_vlan_ranges', lambda: [])()),
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
