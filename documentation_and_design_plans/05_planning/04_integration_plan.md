# Lab Automation Framework - Frontend Integration Plan
# Lovable-Generated React App + Python Backend Integration

## 📊 Analysis Summary

### **Generated Frontend Structure**
- **Framework**: React 18 + TypeScript + Vite
- **UI Library**: Radix UI + Shadcn/ui components
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React Query + React Hook Form
- **Routing**: React Router DOM
- **Charts**: Recharts for analytics

### **Key Components Generated**
1. **Dashboard**: Overview cards, stats, recent activity
2. **Bridge Builder**: Multi-step wizard for configuration
3. **Sidebar Navigation**: Main, Network, System sections
4. **UI Components**: Cards, forms, modals, progress indicators

## 🎯 Integration Strategy

### **Phase 1: Backend API Development (Priority 1)**

#### **1.1 Flask API Server**
```python
# New file: api_server.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
import yaml
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Import existing modules
from config_engine.unified_bridge_domain_builder import UnifiedBridgeDomainBuilder
from scripts.ssh_push_menu import SSHPushMenu
from scripts.inventory_manager import InventoryManager
```

#### **1.2 Authentication Endpoints**
```python
@app.route('/api/auth/login', methods=['POST'])
def login():
    # LDAP/AD integration or simple auth
    return jsonify({"token": "jwt_token", "user": user_data})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    # Return current user info
    return jsonify(user_data)
```

#### **1.3 Dashboard Data Endpoints**
```python
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    # Count devices, deployments, configurations
    return jsonify({
        "totalDevices": device_count,
        "activeDeployments": deployment_count,
        "bridgeDomains": bridge_domain_count,
        "configFiles": config_file_count
    })

@app.route('/api/dashboard/recent-activity', methods=['GET'])
def get_recent_activity():
    # Recent deployments, configurations, discoveries
    return jsonify(activity_data)
```

#### **1.4 Bridge Domain Builder API**
```python
@app.route('/api/builder/devices', methods=['GET'])
def get_devices():
    # Return device list from devices.yaml
    return jsonify(devices_data)

@app.route('/api/builder/interfaces/<device>', methods=['GET'])
def get_interfaces(device):
    # Return available interfaces for device
    return jsonify(interfaces_data)

@app.route('/api/builder/validate', methods=['POST'])
def validate_configuration():
    # Validate bridge domain configuration
    return jsonify({"valid": True, "errors": []})

@app.route('/api/builder/generate', methods=['POST'])
def generate_configuration():
    # Generate bridge domain configuration
    return jsonify({"config": config_data, "metadata": metadata})
```

#### **1.5 File Management API**
```python
@app.route('/api/files/list', methods=['GET'])
def list_files():
    # Return file tree structure
    return jsonify(file_tree)

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    # Handle file uploads
    return jsonify({"success": True})

@app.route('/api/files/download/<path:filepath>', methods=['GET'])
def download_file(filepath):
    # Serve file downloads
    return send_file(filepath)
```

#### **1.6 Deployment Management API**
```python
@app.route('/api/deployments/list', methods=['GET'])
def list_deployments():
    # Return pending and deployed configurations
    return jsonify(deployments_data)

@app.route('/api/deployments/start', methods=['POST'])
def start_deployment():
    # Start configuration deployment
    return jsonify({"deploymentId": "deployment_id"})

@app.route('/api/deployments/<deployment_id>/status', methods=['GET'])
def get_deployment_status(deployment_id):
    # Return real-time deployment status
    return jsonify(status_data)
```

### **Phase 2: Frontend Integration (Priority 2)**

#### **2.1 API Service Layer**
```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getRecentActivity: () => api.get('/dashboard/recent-activity'),
};

export const builderAPI = {
  getDevices: () => api.get('/builder/devices'),
  getInterfaces: (device: string) => api.get(`/builder/interfaces/${device}`),
  validateConfig: (data: any) => api.post('/builder/validate', data),
  generateConfig: (data: any) => api.post('/builder/generate', data),
};
```

#### **2.2 WebSocket Integration**
```typescript
// src/services/websocket.ts
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000');

export const useWebSocket = () => {
  const subscribeToDeployment = (deploymentId: string) => {
    socket.emit('subscribe', { deploymentId });
  };

  const onDeploymentUpdate = (callback: (data: any) => void) => {
    socket.on('deployment_update', callback);
  };

  return { subscribeToDeployment, onDeploymentUpdate };
};
```

#### **2.3 Bridge Builder Integration**
```typescript
// src/pages/BridgeBuilder.tsx - Update existing component
import { builderAPI } from '@/services/api';

// Replace hardcoded device data with API calls
const [devices, setDevices] = useState([]);
const [loading, setLoading] = useState(false);

useEffect(() => {
  const loadDevices = async () => {
    setLoading(true);
    try {
      const response = await builderAPI.getDevices();
      setDevices(response.data);
    } catch (error) {
      console.error('Failed to load devices:', error);
    } finally {
      setLoading(false);
    }
  };
  
  loadDevices();
}, []);
```

### **Phase 3: Real-time Features (Priority 3)**

#### **3.1 Deployment Progress**
```python
# WebSocket events for real-time updates
@socketio.on('subscribe')
def handle_subscription(data):
    deployment_id = data['deploymentId']
    # Join room for deployment updates
    join_room(deployment_id)

def emit_deployment_progress(deployment_id, progress_data):
    socketio.emit('deployment_update', progress_data, room=deployment_id)
```

#### **3.2 Live Status Updates**
```typescript
// src/hooks/useDeploymentStatus.ts
import { useWebSocket } from '@/services/websocket';

export const useDeploymentStatus = (deploymentId: string) => {
  const [status, setStatus] = useState(null);
  const { subscribeToDeployment, onDeploymentUpdate } = useWebSocket();

  useEffect(() => {
    subscribeToDeployment(deploymentId);
    onDeploymentUpdate((data) => {
      setStatus(data);
    });
  }, [deploymentId]);

  return status;
};
```

### **Phase 4: File System Integration (Priority 4)**

#### **4.1 File Browser Component**
```typescript
// src/components/FileBrowser.tsx
import { filesAPI } from '@/services/api';

export const FileBrowser = () => {
  const [files, setFiles] = useState([]);
  const [currentPath, setCurrentPath] = useState('/');

  const loadFiles = async (path: string) => {
    const response = await filesAPI.list(path);
    setFiles(response.data);
  };

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    await filesAPI.upload(formData);
    loadFiles(currentPath);
  };

  return (
    <div>
      {/* File tree component */}
      {/* Upload zone */}
      {/* File actions */}
    </div>
  );
};
```

#### **4.2 Terminal Integration**
```typescript
// src/components/Terminal.tsx
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';

export const TerminalComponent = () => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const [terminal, setTerminal] = useState<Terminal | null>(null);

  useEffect(() => {
    if (terminalRef.current) {
      const term = new Terminal();
      const fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(terminalRef.current);
      fitAddon.fit();
      setTerminal(term);

      // Connect to backend terminal process
      const socket = io('http://localhost:5000/terminal');
      socket.on('terminal_output', (data) => {
        term.write(data);
      });

      term.onData((data) => {
        socket.emit('terminal_input', data);
      });
    }
  }, []);

  return <div ref={terminalRef} className="h-96" />;
};
```

## 🔧 Implementation Steps

### **Step 1: Set Up Backend API Server**
1. Create `api_server.py` with Flask + SocketIO
2. Implement authentication endpoints
3. Create dashboard data endpoints
4. Add bridge domain builder API
5. Implement file management API
6. Add deployment management API

### **Step 2: Update Frontend API Integration**
1. Create API service layer in frontend
2. Replace hardcoded data with API calls
3. Add error handling and loading states
4. Implement WebSocket connections
5. Add real-time deployment tracking

### **Step 3: Integrate Existing Python Modules**
1. Import existing modules into API server
2. Create wrapper functions for CLI operations
3. Add configuration file management
4. Implement SSH deployment integration
5. Add device discovery integration

### **Step 4: Add Missing Frontend Pages**
1. File Manager page
2. Deployment Management page
3. Network Discovery page
4. Topology View page
5. System Monitoring page

### **Step 5: Testing & Refinement**
1. Test all API endpoints
2. Verify real-time functionality
3. Test file upload/download
4. Validate deployment workflows
5. Performance optimization

## 📁 File Structure After Integration

```
lab_automation/
├── api_server.py              # New Flask API server
├── main.py                    # Existing CLI entry point
├── config_engine/             # Existing modules
├── scripts/                   # Existing modules
├── frontend/                  # Lovable-generated React app
│   ├── src/
│   │   ├── services/          # API integration
│   │   ├── hooks/             # Custom hooks
│   │   ├── components/        # UI components
│   │   └── pages/             # Page components
│   └── package.json
├── configs/                   # Existing configs
├── devices.yaml               # Existing device data
└── requirements.txt           # Updated dependencies
```

## 🚀 Deployment Strategy

### **Development Environment**
```bash
# Terminal 1: Backend API
python api_server.py

# Terminal 2: Frontend Development
cd frontend
npm run dev
```

### **Production Deployment**
```bash
# Build frontend
cd frontend
npm run build

# Serve with backend
python api_server.py --production
```

## 🎯 Success Metrics

### **Technical Metrics**
- API response time < 200ms
- WebSocket latency < 100ms
- File upload success rate > 99%
- Deployment success rate > 95%

### **User Experience Metrics**
- Bridge domain creation < 3 minutes
- File operations < 1 second
- Real-time updates < 500ms
- Mobile responsiveness score > 90%

This integration plan provides a clear roadmap for connecting the Lovable-generated frontend with your existing Lab Automation Framework backend, creating a modern web interface while maintaining all existing functionality. 