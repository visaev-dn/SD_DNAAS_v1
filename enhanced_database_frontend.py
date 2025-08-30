#!/usr/bin/env python3
"""
Enhanced Database Frontend Server
Provides web-based user interfaces for Enhanced Database operations
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from flask_cors import CORS

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main API server components
from api_server import app as main_api_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app for frontend
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FRONTEND_SECRET_KEY', 'enhanced-database-frontend-2024')

# Enable CORS
CORS(app)

# HTML Templates
MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Database Management</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .nav { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .nav a { display: inline-block; padding: 10px 20px; margin: 0 10px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; transition: background 0.3s; }
        .nav a:hover { background: #2980b9; }
        .nav a.active { background: #27ae60; }
        .content { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { color: #2c3e50; margin-bottom: 15px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #2980b9; }
        .btn.success { background: #27ae60; }
        .btn.success:hover { background: #229954; }
        .btn.danger { background: #e74c3c; }
        .btn.danger:hover { background: #c0392b; }
        .table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background: #f8f9fa; font-weight: 600; }
        .form-group { margin: 15px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 600; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        .form-group textarea { height: 100px; resize: vertical; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗄️ Enhanced Database Management</h1>
            <p>Advanced topology management, validation, and data consistency tools</p>
        </div>
        
        <div class="nav">
            <a href="/" class="{{ 'active' if request.endpoint == 'index' else '' }}">🏠 Dashboard</a>
            <a href="/topologies" class="{{ 'active' if request.endpoint == 'topologies' else '' }}">🌐 Topologies</a>
            <a href="/devices" class="{{ 'active' if request.endpoint == 'devices' else '' }}">🖥️ Devices</a>
            <a href="/interfaces" class="{{ 'active' if request.endpoint == 'interfaces' else '' }}">🔌 Interfaces</a>
            <a href="/paths" class="{{ 'active' if request.endpoint == 'paths' else '' }}">🛣️ Paths</a>
            <a href="/bridge-domains" class="{{ 'active' if request.endpoint == 'bridge_domains' else '' }}">🌉 Bridge Domains</a>
            <a href="/migration" class="{{ 'active' if request.endpoint == 'migration' else '' }}">🔄 Migration</a>
            <a href="/export" class="{{ 'active' if request.endpoint == 'export' else '' }}">📤 Export/Import</a>
        </div>
        
        <div class="content">
            {{ content | safe }}
        </div>
    </div>
    
    <script>
        // Utility functions
        function showLoading(elementId) {
            document.getElementById(elementId).innerHTML = '<div class="loading">Loading...</div>';
        }
        
        function showError(elementId, message) {
            document.getElementById(elementId).innerHTML = '<div class="status error">❌ ' + message + '</div>';
        }
        
        function showSuccess(elementId, message) {
            document.getElementById(elementId).innerHTML = '<div class="status success">✅ ' + message + '</div>';
        }
        
        function formatDate(dateString) {
            if (!dateString) return 'N/A';
            try {
                return new Date(dateString).toLocaleString();
            } catch (e) {
                return dateString;
            }
        }
        
        // API calls
        async function apiCall(endpoint, method = 'GET', data = null) {
            try {
                const options = {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                    }
                };
                
                if (data) {
                    options.body = JSON.stringify(data);
                }
                
                const response = await fetch(endpoint, options);
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || 'API call failed');
                }
                
                return result;
            } catch (error) {
                console.error('API call error:', error);
                throw error;
            }
        }
    </script>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
    <h2>📊 Dashboard</h2>
    
    <div class="card">
        <h3>🚀 System Status</h3>
        <div id="system-status">Loading...</div>
    </div>
    
    <div class="card">
        <h3>📈 Database Statistics</h3>
        <div id="database-stats">Loading...</div>
    </div>
    
    <div class="card">
        <h3>🔧 Quick Actions</h3>
        <a href="/topologies" class="btn">View Topologies</a>
        <a href="/migration" class="btn">Migrate Legacy Data</a>
        <a href="/export" class="btn">Export Data</a>
        <a href="/bridge-domains" class="btn">Manage Bridge Domains</a>
    </div>
    
    <script>
        // Load dashboard data
        async function loadDashboard() {
            try {
                // Load system status
                const statusResponse = await apiCall('/api/enhanced-database/status');
                if (statusResponse.success) {
                    const integration = statusResponse.enhanced_database_integration;
                    document.getElementById('system-status').innerHTML = `
                        <div class="status success">
                            <strong>Status:</strong> ${integration.status}<br>
                            <strong>Version:</strong> ${integration.version}<br>
                            <strong>Database:</strong> ${integration.database.status}
                        </div>
                    `;
                }
                
                // Load database statistics
                const healthResponse = await apiCall('/api/enhanced-database/health');
                if (healthResponse.success) {
                    const health = healthResponse.health_status;
                    document.getElementById('database-stats').innerHTML = `
                        <div class="status success">
                            <strong>Total Tables:</strong> ${health.database.length}<br>
                            <strong>Total Records:</strong> ${health.total_records}<br>
                            <strong>API Status:</strong> ${health.status}
                        </div>
                    `;
                }
                
            } catch (error) {
                showError('system-status', 'Failed to load system status: ' + error.message);
                showError('database-stats', 'Failed to load database statistics: ' + error.message);
            }
        }
        
        // Load dashboard when page loads
        document.addEventListener('DOMContentLoaded', loadDashboard);
    </script>
"""

TOPOLOGIES_TEMPLATE = """
{% extends "main" %}
{% block content %}
    <h2>🌐 Topology Management</h2>
    
    <div class="card">
        <h3>📋 Topology List</h3>
        <div id="topologies-list">Loading...</div>
    </div>
    
    <div class="card">
        <h3>➕ Create New Topology</h3>
        <form id="create-topology-form">
            <div class="form-group">
                <label for="bridge_domain_name">Bridge Domain Name:</label>
                <input type="text" id="bridge_domain_name" name="bridge_domain_name" required>
            </div>
            <div class="form-group">
                <label for="service_name">Service Name:</label>
                <input type="text" id="service_name" name="service_name" required>
            </div>
            <div class="form-group">
                <label for="vlan_id">VLAN ID:</label>
                <input type="number" id="vlan_id" name="vlan_id" required>
            </div>
            <div class="form-group">
                <label for="topology_type">Topology Type:</label>
                <select id="topology_type" name="topology_type" required>
                    <option value="P2P">Point-to-Point (P2P)</option>
                    <option value="P2MP">Point-to-Multipoint (P2MP)</option>
                    <option value="MESH">Mesh</option>
                </select>
            </div>
            <button type="submit" class="btn success">Create Topology</button>
        </form>
        <div id="create-result"></div>
    </div>
    
    <script>
        // Load topologies
        async function loadTopologies() {
            try {
                showLoading('topologies-list');
                const response = await apiCall('/api/enhanced-database/topologies');
                
                if (response.success && response.topologies) {
                    if (response.topologies.length === 0) {
                        document.getElementById('topologies-list').innerHTML = '<p>No topologies found.</p>';
                        return;
                    }
                    
                    let html = '<table class="table"><thead><tr><th>ID</th><th>Bridge Domain</th><th>Service</th><th>VLAN</th><th>Type</th><th>Created</th><th>Actions</th></tr></thead><tbody>';
                    
                    response.topologies.forEach(topology => {
                        html += `
                            <tr>
                                <td>${topology.id}</td>
                                <td>${topology.bridge_domain_name}</td>
                                <td>${topology.service_name}</td>
                                <td>${topology.vlan_id}</td>
                                <td>${topology.topology_type}</td>
                                <td>${formatDate(topology.created_at)}</td>
                                <td>
                                    <button class="btn" onclick="viewTopology(${topology.id})">View</button>
                                    <button class="btn danger" onclick="deleteTopology(${topology.id})">Delete</button>
                                </td>
                            </tr>
                        `;
                    });
                    
                    html += '</tbody></table>';
                    document.getElementById('topologies-list').innerHTML = html;
                } else {
                    showError('topologies-list', 'Failed to load topologies');
                }
                
            } catch (error) {
                showError('topologies-list', 'Error loading topologies: ' + error.message);
            }
        }
        
        // Create topology
        document.getElementById('create-topology-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                bridge_domain_name: document.getElementById('bridge_domain_name').value,
                service_name: document.getElementById('service_name').value,
                vlan_id: parseInt(document.getElementById('vlan_id').value),
                topology_type: document.getElementById('topology_type').value
            };
            
            try {
                const response = await apiCall('/api/enhanced-database/topologies', 'POST', formData);
                if (response.success) {
                    showSuccess('create-result', 'Topology created successfully!');
                    document.getElementById('create-topology-form').reset();
                    loadTopologies(); // Reload the list
                } else {
                    showError('create-result', 'Failed to create topology: ' + response.error);
                }
            } catch (error) {
                showError('create-result', 'Error creating topology: ' + error.message);
            }
        });
        
        // Load topologies when page loads
        document.addEventListener('DOMContentLoaded', loadTopologies);
        
        // View topology details
        function viewTopology(id) {
            // TODO: Implement topology detail view
            alert('View topology ' + id + ' - Feature coming soon!');
        }
        
        // Delete topology
        async function deleteTopology(id) {
            if (confirm('Are you sure you want to delete this topology?')) {
                try {
                    const response = await apiCall(`/api/enhanced-database/topologies/${id}`, 'DELETE');
                    if (response.success) {
                        showSuccess('topologies-list', 'Topology deleted successfully!');
                        loadTopologies(); // Reload the list
                    } else {
                        showError('topologies-list', 'Failed to delete topology: ' + response.error);
                    }
                } catch (error) {
                    showError('topologies-list', 'Error deleting topology: ' + error.message);
                }
            }
        }
    </script>
{% endblock %}
"""

# Routes
@app.route('/')
def index():
    """Dashboard page"""
    return render_template_string(MAIN_TEMPLATE, content=DASHBOARD_TEMPLATE)

@app.route('/topologies')
def topologies():
    """Topology management page"""
    return render_template_string(MAIN_TEMPLATE, content=TOPOLOGIES_TEMPLATE)

@app.route('/devices')
def devices():
    """Device management page"""
    return render_template_string(MAIN_TEMPLATE, content="""
        <h2>🖥️ Device Management</h2>
        <div class="card">
            <h3>📋 Device List</h3>
            <div id="devices-list">Loading...</div>
        </div>
        
        <script>
            async function loadDevices() {
                try {
                    showLoading('devices-list');
                    const response = await apiCall('/api/enhanced-database/devices');
                    
                    if (response.success && response.devices) {
                        if (response.devices.length === 0) {
                            document.getElementById('devices-list').innerHTML = '<p>No devices found.</p>';
                            return;
                        }
                        
                        let html = '<table class="table"><thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Role</th><th>Model</th><th>Actions</th></tr></thead><tbody>';
                        
                        response.devices.forEach(device => {
                            html += `
                                <tr>
                                    <td>${device.id}</td>
                                    <td>${device.name}</td>
                                    <td>${device.device_type}</td>
                                    <td>${device.role}</td>
                                    <td>${device.model || 'N/A'}</td>
                                    <td>
                                        <button class="btn" onclick="viewDevice(${device.id})">View</button>
                                    </td>
                                </tr>
                            `;
                        });
                        
                        html += '</tbody></table>';
                        document.getElementById('devices-list').innerHTML = html;
                    } else {
                        showError('devices-list', 'Failed to load devices');
                    }
                    
                } catch (error) {
                    showError('devices-list', 'Error loading devices: ' + error.message);
                }
            }
            
            document.addEventListener('DOMContentLoaded', loadDevices);
            
            function viewDevice(id) {
                alert('View device ' + id + ' - Feature coming soon!');
            }
        </script>
    """)

@app.route('/interfaces')
def interfaces():
    """Interface management page"""
    return render_template_string(MAIN_TEMPLATE, content="""
        <h2>🔌 Interface Management</h2>
        <div class="card">
            <h3>📋 Interface List</h3>
            <div id="interfaces-list">Loading...</div>
        </div>
        
        <script>
            async function loadInterfaces() {
                try {
                    showLoading('interfaces-list');
                    const response = await apiCall('/api/enhanced-database/interfaces');
                    
                    if (response.success && response.interfaces) {
                        if (response.interfaces.length === 0) {
                            document.getElementById('interfaces-list').innerHTML = '<p>No interfaces found.</p>';
                            return;
                        }
                        
                        let html = '<table class="table"><thead><tr><th>ID</th><th>Name</th><th>Device</th><th>Type</th><th>Role</th><th>Actions</th></tr></thead><tbody>';
                        
                        response.interfaces.forEach(interface => {
                            html += `
                                <tr>
                                    <td>${interface.id}</td>
                                    <td>${interface.name}</td>
                                    <td>${interface.device_name}</td>
                                    <td>${interface.interface_type}</td>
                                    <td>${interface.interface_role}</td>
                                    <td>
                                        <button class="btn" onclick="viewInterface(${interface.id})">View</button>
                                    </td>
                                </tr>
                            `;
                        });
                        
                        html += '</tbody></table>';
                        document.getElementById('interfaces-list').innerHTML = html;
                    } else {
                        showError('interfaces-list', 'Failed to load interfaces');
                    }
                    
                } catch (error) {
                    showError('interfaces-list', 'Error loading interfaces: ' + error.message);
                }
            }
            
            document.addEventListener('DOMContentLoaded', loadInterfaces);
            
            function viewInterface(id) {
                alert('View interface ' + id + ' - Feature coming soon!');
            }
        </script>
    """)

@app.route('/paths')
def paths():
    """Path management page"""
    return render_template_string(MAIN_TEMPLATE, content="""
        <h2>🛣️ Path Management</h2>
        <div class="card">
            <h3>📋 Path List</h3>
            <div id="paths-list">Loading...</div>
        </div>
        
        <script>
            async function loadPaths() {
                try {
                    showLoading('paths-list');
                    const response = await apiCall('/api/enhanced-database/paths');
                    
                    if (response.success && response.paths) {
                        if (response.paths.length === 0) {
                            document.getElementById('paths-list').innerHTML = '<p>No paths found.</p>';
                            return;
                        }
                        
                        let html = '<table class="table"><thead><tr><th>ID</th><th>Name</th><th>Source</th><th>Destination</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
                        
                        response.paths.forEach(path => {
                            html += `
                                <tr>
                                    <td>${path.id}</td>
                                    <td>${path.name}</td>
                                    <td>${path.source_device}</td>
                                    <td>${path.destination_device}</td>
                                    <td>${path.status}</td>
                                    <td>
                                        <button class="btn" onclick="viewPath(${path.id})">View</button>
                                    </td>
                                </tr>
                            `;
                        });
                        
                        html += '</tbody></table>';
                        document.getElementById('paths-list').innerHTML = html;
                    } else {
                        showError('paths-list', 'Failed to load paths');
                    }
                    
                } catch (error) {
                    showError('paths-list', 'Error loading paths: ' + error.message);
                }
            }
            
            document.addEventListener('DOMContentLoaded', loadPaths);
            
            function viewPath(id) {
                alert('View path ' + id + ' - Feature coming soon!');
            }
        </script>
    """)

@app.route('/bridge-domains')
def bridge_domains():
    """Bridge domain management page"""
    return render_template_string(MAIN_TEMPLATE, content="""
        <h2>🌉 Bridge Domain Management</h2>
        <div class="card">
            <h3>📋 Bridge Domain List</h3>
            <div id="bridge-domains-list">Loading...</div>
        </div>
        
        <div class="card">
            <h3>🔨 Enhanced Bridge Domain Builder</h3>
            <form id="enhanced-builder-form">
                <div class="form-group">
                    <label for="service_name">Service Name:</label>
                    <input type="text" id="service_name" name="service_name" required>
                </div>
                <div class="form-group">
                    <label for="vlan_id">VLAN ID:</label>
                    <input type="number" id="vlan_id" name="vlan_id" required>
                </div>
                <div class="form-group">
                    <label for="source_device">Source Device:</label>
                    <input type="text" id="source_device" name="source_device" required>
                </div>
                <div class="form-group">
                    <label for="source_interface">Source Interface:</label>
                    <input type="text" id="source_interface" name="source_interface" required>
                </div>
                <div class="form-group">
                    <label for="destinations">Destinations (JSON array):</label>
                    <textarea id="destinations" name="destinations" placeholder='[{"device": "device1", "port": "port1"}, {"device": "device2", "port": "port2"}]' required></textarea>
                </div>
                <button type="submit" class="btn success">Build Bridge Domain</button>
            </form>
            <div id="builder-result"></div>
        </div>
        
        <script>
            // Load bridge domains
            async function loadBridgeDomains() {
                try {
                    showLoading('bridge-domains-list');
                    const response = await apiCall('/api/enhanced-database/bridge-domains');
                    
                    if (response.success && response.bridge_domains) {
                        if (response.bridge_domains.length === 0) {
                            document.getElementById('bridge-domains-list').innerHTML = '<p>No bridge domains found.</p>';
                            return;
                        }
                        
                        let html = '<table class="table"><thead><tr><th>ID</th><th>Name</th><th>VLAN</th><th>Type</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
                        
                        response.bridge_domains.forEach(bd => {
                            html += `
                                <tr>
                                    <td>${bd.id}</td>
                                    <td>${bd.name}</td>
                                    <td>${bd.vlan_id}</td>
                                    <td>${bd.bridge_domain_type}</td>
                                    <td>${bd.status}</td>
                                    <td>
                                        <button class="btn" onclick="viewBridgeDomain(${bd.id})">View</button>
                                    </td>
                                </tr>
                            `;
                        });
                        
                        html += '</tbody></table>';
                        document.getElementById('bridge-domains-list').innerHTML = html;
                    } else {
                        showError('bridge-domains-list', 'Failed to load bridge domains');
                    }
                    
                } catch (error) {
                    showError('bridge-domains-list', 'Error loading bridge domains: ' + error.message);
                }
            }
            
            // Enhanced builder form
            document.getElementById('enhanced-builder-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                try {
                    const destinations = JSON.parse(document.getElementById('destinations').value);
                    
                    const formData = {
                        service_name: document.getElementById('service_name').value,
                        vlan_id: parseInt(document.getElementById('vlan_id').value),
                        source_device: document.getElementById('source_device').value,
                        source_interface: document.getElementById('source_interface').value,
                        destinations: destinations
                    };
                    
                    const response = await apiCall('/api/bridge-domains/enhanced-builder', 'POST', formData);
                    if (response.success) {
                        showSuccess('builder-result', 'Bridge domain built successfully!');
                        document.getElementById('enhanced-builder-form').reset();
                        loadBridgeDomains(); // Reload the list
                    } else {
                        showError('builder-result', 'Failed to build bridge domain: ' + response.error);
                    }
                } catch (error) {
                    showError('builder-result', 'Error building bridge domain: ' + error.message);
                }
            });
            
            document.addEventListener('DOMContentLoaded', loadBridgeDomains);
            
            function viewBridgeDomain(id) {
                alert('View bridge domain ' + id + ' - Feature coming soon!');
            }
        </script>
    """)

@app.route('/migration')
def migration():
    """Migration page"""
    return render_template_string(MAIN_TEMPLATE, content="""
        <h2>🔄 Legacy Data Migration</h2>
        <div class="card">
            <h3>📊 Migration Status</h3>
            <div id="migration-status">Loading...</div>
        </div>
        
        <div class="card">
            <h3>🚀 Start Migration</h3>
            <p>Migrate legacy configurations to Enhanced Database format for better validation and consistency.</p>
            <button class="btn success" onclick="startMigration()">Start Migration Process</button>
            <div id="migration-result"></div>
        </div>
        
        <script>
            async function loadMigrationStatus() {
                try {
                    showLoading('migration-status');
                    const response = await apiCall('/api/enhanced-database/migrate/status');
                    
                    if (response.success) {
                        document.getElementById('migration-status').innerHTML = `
                            <div class="status success">
                                <strong>Migration System:</strong> Ready<br>
                                <strong>Legacy Configurations:</strong> Available for migration<br>
                                <strong>Enhanced Database:</strong> Ready to receive data
                            </div>
                        `;
                    } else {
                        showError('migration-status', 'Failed to load migration status');
                    }
                    
                } catch (error) {
                    showError('migration-status', 'Error loading migration status: ' + error.message);
                }
            }
            
            async function startMigration() {
                try {
                    showLoading('migration-result');
                    const response = await apiCall('/api/enhanced-database/migrate/start', 'POST');
                    
                    if (response.success) {
                        showSuccess('migration-result', 'Migration started successfully! Check the status for progress updates.');
                    } else {
                        showError('migration-result', 'Failed to start migration: ' + response.error);
                    }
                    
                } catch (error) {
                    showError('migration-result', 'Error starting migration: ' + error.message);
                }
            }
            
            document.addEventListener('DOMContentLoaded', loadMigrationStatus);
        </script>
    """)

@app.route('/export')
def export():
    """Export/Import page"""
    return render_template_string(MAIN_TEMPLATE, content="""
        <h2>📤 Export/Import Management</h2>
        <div class="card">
            <h3>📤 Export Data</h3>
            <p>Export Enhanced Database data in various formats for backup, analysis, or sharing.</p>
            <button class="btn" onclick="exportData('json')">Export as JSON</button>
            <button class="btn" onclick="exportData('yaml')">Export as YAML</button>
            <div id="export-result"></div>
        </div>
        
        <div class="card">
            <h3>📥 Import Data</h3>
            <p>Import data from external sources to populate the Enhanced Database.</p>
            <div class="form-group">
                <label for="import-file">Select File:</label>
                <input type="file" id="import-file" accept=".json,.yaml,.yml">
            </div>
            <button class="btn success" onclick="importData()">Import Data</button>
            <div id="import-result"></div>
        </div>
        
        <script>
            async function exportData(format) {
                try {
                    showLoading('export-result');
                    const response = await apiCall(`/api/enhanced-database/export/${format}`);
                    
                    if (response.success) {
                        // Create download link
                        const blob = new Blob([JSON.stringify(response.data, null, 2)], {type: 'application/json'});
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `enhanced-database-export.${format}`;
                        a.click();
                        window.URL.revokeObjectURL(url);
                        
                        showSuccess('export-result', `Data exported successfully as ${format.toUpperCase()}!`);
                    } else {
                        showError('export-result', 'Failed to export data: ' + response.error);
                    }
                    
                } catch (error) {
                    showError('export-result', 'Error exporting data: ' + error.message);
                }
            }
            
            async function importData() {
                const fileInput = document.getElementById('import-file');
                const file = fileInput.files[0];
                
                if (!file) {
                    showError('import-result', 'Please select a file to import');
                    return;
                }
                
                try {
                    showLoading('export-result');
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch('/api/enhanced-database/import', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        showSuccess('import-result', 'Data imported successfully!');
                        fileInput.value = '';
                    } else {
                        showError('import-result', 'Failed to import data: ' + result.error);
                    }
                    
                } catch (error) {
                    showError('import-result', 'Error importing data: ' + error.message);
                }
            }
        </script>
    """)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Database Frontend Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting Enhanced Database Frontend Server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
