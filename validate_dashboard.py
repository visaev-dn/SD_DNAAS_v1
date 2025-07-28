#!/usr/bin/env python3
"""
Dashboard Data Validator
Validates that the dashboard is showing correct data from the backend
"""

import json
import requests
import yaml
from pathlib import Path
from datetime import datetime

def check_api_health():
    """Check if API server is running"""
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def get_dashboard_stats():
    """Get dashboard stats from API"""
    try:
        response = requests.get('http://localhost:5000/api/dashboard/stats', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def get_recent_activity():
    """Get recent activity from API"""
    try:
        response = requests.get('http://localhost:5000/api/dashboard/recent-activity', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def count_real_devices():
    """Count actual devices from devices.yaml"""
    try:
        with open('devices.yaml', 'r') as f:
            devices = yaml.safe_load(f)
            return len([k for k in devices.keys() if k != 'defaults'])
    except:
        return 0

def count_real_config_files():
    """Count actual configuration files"""
    try:
        configs_dir = Path("configs")
        if configs_dir.exists():
            return len(list(configs_dir.rglob("*.yaml")))
        return 0
    except:
        return 0

def count_real_bridge_domains():
    """Count actual bridge domain configurations"""
    try:
        pending_dir = Path("configs/pending")
        if pending_dir.exists():
            return len([f for f in pending_dir.glob("*.yaml") 
                       if "bridge_domain" in f.name or "unified_bridge_domain" in f.name])
        return 0
    except:
        return 0

def validate_dashboard_data():
    """Validate dashboard data against real system state"""
    print("🔍 Dashboard Data Validation")
    print("=" * 50)
    
    # Check API health
    print(f"✅ API Server Health: {'Running' if check_api_health() else 'Not Running'}")
    
    # Get API data
    api_stats = get_dashboard_stats()
    api_activity = get_recent_activity()
    
    # Get real data
    real_devices = count_real_devices()
    real_configs = count_real_config_files()
    real_bridge_domains = count_real_bridge_domains()
    
    print(f"\n📊 API Dashboard Stats:")
    if api_stats:
        print(f"  Total Devices: {api_stats.get('totalDevices', 'N/A')}")
        print(f"  Bridge Domains: {api_stats.get('bridgeDomains', 'N/A')}")
        print(f"  Config Files: {api_stats.get('configFiles', 'N/A')}")
        print(f"  Active Deployments: {api_stats.get('activeDeployments', 'N/A')}")
    else:
        print("  ❌ Could not fetch API stats")
    
    print(f"\n📊 Real System Data:")
    print(f"  Total Devices: {real_devices}")
    print(f"  Bridge Domains: {real_bridge_domains}")
    print(f"  Config Files: {real_configs}")
    
    print(f"\n🔍 Validation Results:")
    
    # Validate device count
    if api_stats and api_stats.get('totalDevices') == real_devices:
        print(f"  ✅ Device count matches: {real_devices}")
    else:
        print(f"  ❌ Device count mismatch: API={api_stats.get('totalDevices') if api_stats else 'N/A'}, Real={real_devices}")
    
    # Validate bridge domain count
    if api_stats and api_stats.get('bridgeDomains') == real_bridge_domains:
        print(f"  ✅ Bridge domains count matches: {real_bridge_domains}")
    else:
        print(f"  ❌ Bridge domains count mismatch: API={api_stats.get('bridgeDomains') if api_stats else 'N/A'}, Real={real_bridge_domains}")
    
    # Validate config files count
    if api_stats and api_stats.get('configFiles') == real_configs:
        print(f"  ✅ Config files count matches: {real_configs}")
    else:
        print(f"  ❌ Config files count mismatch: API={api_stats.get('configFiles') if api_stats else 'N/A'}, Real={real_configs}")
    
    # Check recent activity
    if api_activity:
        print(f"  ✅ Recent activity available: {len(api_activity)} items")
        for i, activity in enumerate(api_activity[:3]):
            print(f"    {i+1}. {activity.get('action')} - {activity.get('device')} ({activity.get('time')})")
    else:
        print(f"  ❌ No recent activity data")
    
    print(f"\n📁 File System Check:")
    
    # Check key directories
    key_dirs = ['configs/pending', 'configs/deployed', 'configs/removed']
    for dir_path in key_dirs:
        path = Path(dir_path)
        if path.exists():
            files = list(path.glob("*.yaml"))
            print(f"  ✅ {dir_path}: {len(files)} files")
        else:
            print(f"  ❌ {dir_path}: Directory not found")
    
    # Check devices.yaml
    if Path('devices.yaml').exists():
        print(f"  ✅ devices.yaml: Found")
    else:
        print(f"  ❌ devices.yaml: Not found")
    
    print(f"\n🎯 Troubleshooting Tips:")
    print(f"  • If API server is not running: python3 api_server.py --debug")
    print(f"  • If React app is not loading: cd frontend && npm run dev")
    print(f"  • Check API endpoints: curl http://localhost:5000/api/health")
    print(f"  • View dashboard: http://localhost:8080")

if __name__ == "__main__":
    validate_dashboard_data() 