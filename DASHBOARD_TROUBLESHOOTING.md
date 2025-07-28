# Dashboard Troubleshooting Guide

## 📊 Dashboard Data Files

### `dashboard_data.json`
Contains all dashboard values for easy troubleshooting:
- **Dashboard Stats**: Total devices, bridge domains, config files, deployments
- **Recent Activity**: Latest bridge domain creations and deployments
- **System Info**: API server status, React server status, data sources
- **Troubleshooting**: Common issues and solutions

### `validate_dashboard.py`
Validates that dashboard data matches real system state:
```bash
python3 validate_dashboard.py
```

### `update_dashboard_json.py`
Updates dashboard_data.json with current system data:
```bash
python3 update_dashboard_json.py
```

## 🔍 Quick Validation

### 1. Check API Server
```bash
curl http://localhost:5000/api/health
```

### 2. Check Dashboard Stats
```bash
curl http://localhost:5000/api/dashboard/stats
```

### 3. Check Recent Activity
```bash
curl http://localhost:5000/api/dashboard/recent-activity
```

### 4. Check React App
```bash
curl http://localhost:8080
```

## 🚨 Common Issues

### Issue: Dashboard shows 0 devices
**Solution:**
1. Check if `devices.yaml` exists: `ls -la devices.yaml`
2. Check API endpoint: `curl http://localhost:5000/api/builder/devices`
3. Restart API server: `python3 api_server.py --debug`

### Issue: Recent activity not updating
**Solution:**
1. Check `configs/pending` directory: `ls -la configs/pending/`
2. Verify bridge domain files exist
3. Check file timestamps: `stat configs/pending/*.yaml`

### Issue: API server not responding
**Solution:**
1. Check if server is running: `ps aux | grep api_server`
2. Restart server: `python3 api_server.py --debug`
3. Check port 5000: `lsof -i :5000`

### Issue: React app not loading
**Solution:**
1. Check if React server is running: `ps aux | grep "npm run dev"`
2. Restart React server: `cd frontend && npm run dev`
3. Check port 8080: `lsof -i :8080`

## 📁 File Structure

```
lab_automation/
├── dashboard_data.json          # Dashboard data snapshot
├── validate_dashboard.py        # Validation script
├── update_dashboard_json.py     # Update script
├── devices.yaml                 # Device inventory
├── configs/
│   ├── pending/                 # Bridge domain configs
│   ├── deployed/                # Deployed configs
│   └── removed/                 # Removed configs
├── api_server.py               # Flask API server
└── frontend/                   # React app
    └── src/
        └── pages/
            └── Dashboard.tsx    # Dashboard component
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/api/dashboard/recent-activity` | GET | Recent activity |
| `/api/builder/devices` | GET | Available devices |
| `/api/builder/interfaces/{device}` | GET | Device interfaces |
| `/api/builder/validate` | POST | Validate configuration |
| `/api/builder/generate` | POST | Generate configuration |

## 📊 Expected Data

### Dashboard Stats
- **Total Devices**: 63 (from devices.yaml)
- **Bridge Domains**: 6 (from configs/pending/*bridge_domain*.yaml)
- **Config Files**: 13 (all .yaml files in configs/)
- **Active Deployments**: 0 (files in configs/deployed/)

### Recent Activity
- Bridge Domain Created events
- Configuration Deployed events
- Based on file modification times

## 🎯 Quick Start

1. **Start API Server:**
   ```bash
   python3 api_server.py --debug
   ```

2. **Start React App:**
   ```bash
   cd frontend && npm run dev
   ```

3. **Validate System:**
   ```bash
   python3 validate_dashboard.py
   ```

4. **Access Dashboard:**
   - Open: http://localhost:8080
   - API: http://localhost:5000/api/health

## 🔄 Auto-Update

To keep dashboard_data.json current:
```bash
# Update every 5 minutes
watch -n 300 python3 update_dashboard_json.py
```

## 📝 Log Locations

- **API Server**: Terminal where `api_server.py` is running
- **React Server**: Terminal where `npm run dev` is running
- **Browser Console**: F12 in browser for frontend errors
- **System Logs**: Check validation script output

## 🆘 Emergency Reset

If dashboard is completely broken:

1. **Stop all servers:**
   ```bash
   pkill -f "python3 api_server.py"
   pkill -f "npm run dev"
   ```

2. **Restart API server:**
   ```bash
   python3 api_server.py --debug
   ```

3. **Restart React server:**
   ```bash
   cd frontend && npm run dev
   ```

4. **Validate:**
   ```bash
   python3 validate_dashboard.py
   ``` 