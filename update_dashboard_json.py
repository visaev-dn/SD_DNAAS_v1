#!/usr/bin/env python3
"""
Update Dashboard JSON
Updates dashboard_data.json with current system data
"""

import json
import requests
import yaml
from pathlib import Path
from datetime import datetime

def update_dashboard_json():
    """Update dashboard_data.json with current system data"""
    
    # Get current API data
    api_stats = None
    api_activity = None
    
    try:
        response = requests.get('http://localhost:5000/api/dashboard/stats', timeout=5)
        if response.status_code == 200:
            api_stats = response.json()
    except:
        print("⚠️  Could not fetch API stats")
    
    try:
        response = requests.get('http://localhost:5000/api/dashboard/recent-activity', timeout=5)
        if response.status_code == 200:
            api_activity = response.json()
    except:
        print("⚠️  Could not fetch recent activity")
    
    # Get real system data
    real_devices = 0
    real_configs = 0
    real_bridge_domains = 0
    
    try:
        with open('devices.yaml', 'r') as f:
            devices = yaml.safe_load(f)
            real_devices = len([k for k in devices.keys() if k != 'defaults'])
    except:
        print("⚠️  Could not read devices.yaml")
    
    try:
        configs_dir = Path("configs")
        if configs_dir.exists():
            real_configs = len(list(configs_dir.rglob("*.yaml")))
    except:
        print("⚠️  Could not count config files")
    
    try:
        pending_dir = Path("configs/pending")
        if pending_dir.exists():
            real_bridge_domains = len([f for f in pending_dir.glob("*.yaml") 
                                      if "bridge_domain" in f.name or "unified_bridge_domain" in f.name])
    except:
        print("⚠️  Could not count bridge domains")
    
    # Create updated data structure
    updated_data = {
        "dashboard_stats": {
            "totalDevices": api_stats.get('totalDevices', real_devices) if api_stats else real_devices,
            "activeDeployments": api_stats.get('activeDeployments', 0) if api_stats else 0,
            "bridgeDomains": api_stats.get('bridgeDomains', real_bridge_domains) if api_stats else real_bridge_domains,
            "configFiles": api_stats.get('configFiles', real_configs) if api_stats else real_configs,
            "lastUpdated": datetime.now().isoformat(),
            "source": "Real data from devices.yaml and configs directory"
        },
        "recent_activity": api_activity if api_activity else [],
        "system_info": {
            "api_server": {
                "status": "running" if api_stats else "unknown",
                "port": 5000,
                "mode": "development",
                "lastCheck": datetime.now().isoformat()
            },
            "react_server": {
                "status": "running",
                "port": 8080,
                "url": "http://localhost:8080",
                "lastCheck": datetime.now().isoformat()
            },
            "data_sources": {
                "devices": "devices.yaml",
                "topology": "topology/",
                "configs": "configs/",
                "lastInventoryUpdate": datetime.now().isoformat()
            }
        },
        "validation": {
            "api_available": api_stats is not None,
            "activity_available": api_activity is not None,
            "devices_file_exists": Path('devices.yaml').exists(),
            "configs_directory_exists": Path('configs').exists(),
            "last_validation": datetime.now().isoformat()
        }
    }
    
    # Write updated data to file
    try:
        with open('dashboard_data.json', 'w') as f:
            json.dump(updated_data, f, indent=2)
        print("✅ Updated dashboard_data.json with current system data")
        print(f"📊 Current Stats:")
        print(f"  Total Devices: {updated_data['dashboard_stats']['totalDevices']}")
        print(f"  Bridge Domains: {updated_data['dashboard_stats']['bridgeDomains']}")
        print(f"  Config Files: {updated_data['dashboard_stats']['configFiles']}")
        print(f"  Recent Activities: {len(updated_data['recent_activity'])}")
    except Exception as e:
        print(f"❌ Error updating dashboard_data.json: {e}")

if __name__ == "__main__":
    update_dashboard_json() 