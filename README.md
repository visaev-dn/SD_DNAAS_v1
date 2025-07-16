# 🚀 Lab Automation Framework

A comprehensive Python framework for network device management, topology discovery, and SSH configuration deployment.

## 📋 Features

- **🔍 Topology Discovery**: Automated LACP/LLDP data collection and parsing
- **🌳 Visualization**: ASCII topology trees (detailed and minimized)
- **🔨 Bridge Domain Builder**: Interactive configuration generation
- **🚀 SSH Deployment**: Two-stage parallel deployment with validation
- **📊 Device Management**: Inventory population and device status tracking
- **🛡️ Safety**: Validation, preview, and verification capabilities

## 🏗️ Architecture

```
lab_automation/
├── main.py                          # Main entry point
├── devices.yaml                     # Device inventory (create your own)
├── scripts/                         # Core automation scripts
│   ├── inventory_manager.py         # Device inventory management
│   ├── collect_lacp_xml.py         # LACP/LLDP data collection
│   ├── enhanced_topology_discovery.py # Topology analysis
│   ├── ascii_topology_tree.py      # Detailed topology visualization
│   ├── minimized_topology_tree.py  # Simplified topology view
│   └── ssh_push_menu.py            # SSH deployment interface
├── config_engine/                   # Configuration management
│   ├── bridge_domain_builder.py    # Bridge domain configuration
│   └── ssh_push_manager.py         # SSH deployment engine
└── topology/                        # Generated topology data
    ├── visualizations/              # ASCII tree outputs
    └── device_status.json          # Device status tracking
```

## 🚀 Quick Start

### 1. **Prerequisites**
```bash
# Python 3.8+ required
python --version

# Install required packages
pip install paramiko pyyaml pandas openpyxl requests
```

### 2. **Setup**
```bash
# Clone or download the framework
git clone <repository-url>
cd lab_automation

# Create your devices.yaml file (see example below)
cp devices.yaml.example devices.yaml
# Edit devices.yaml with your device information
```

### 3. **Configure Devices**
Create a `devices.yaml` file with your network devices:

```yaml
defaults:
  username: your_username
  password: your_password
  ssh_port: 22

DNAAS-LEAF-A01:
  mgmt_ip: 192.168.1.10
  location: A01
  role: leaf
  status: active

DNAAS-SPINE-A01:
  mgmt_ip: 192.168.1.20
  location: A01
  role: spine
  status: active
```

### 4. **Run the Framework**
```bash
python main.py
```

## 📖 Usage Guide

### **Developer Workflow:**
1. **📊 Populate Devices**: Import devices from external inventory
2. **🔍 Probe+Parse**: Collect LACP/LLDP data from devices
3. **🌐 Topology Discovery**: Analyze and normalize topology
4. **🌳 Visualization**: Generate ASCII topology trees

### **User Workflow:**
1. **🔨 Bridge Domain Builder**: Create network configurations
2. **🚀 SSH Push**: Deploy configurations to devices
3. **🌳 View Topology**: See network structure

## 🔧 Configuration Options

### **SSH Settings**
- **Username/Password**: Set in `devices.yaml`
- **Connection Timeout**: 15 seconds (configurable)
- **Parallel Execution**: Up to device count workers

### **Deployment Safety**
- **Two-Stage Deployment**: Commit-check → Commit
- **Validation**: Pre-deployment configuration validation
- **Verification**: Post-deployment configuration verification
- **Rollback**: Configuration removal capabilities

## 📁 File Structure

### **Input Files:**
- `devices.yaml`: Device inventory and SSH credentials
- External inventory files (Excel, CSV) for device population

### **Generated Files:**
- `topology/`: Topology discovery outputs
- `configs/`: Bridge domain configurations
- `configs/deployment_logs/`: Deployment logs

## 🛡️ Security Notes

- **SSH Credentials**: Store in `devices.yaml` (excluded from git)
- **Sensitive Data**: `devices.yaml`, `configs/`, `topology/` are gitignored
- **Logs**: Deployment logs contain device information

## 🔍 Troubleshooting

### **Common Issues:**

1. **"Missing SSH info"**: Check device name case sensitivity in `devices.yaml`
2. **Connection timeouts**: Verify network connectivity and SSH credentials
3. **"Invalid command"**: Device may require interactive shell (already handled)

### **Debug Mode:**
- Check deployment logs in `configs/deployment_logs/`
- Verify device connectivity manually
- Review topology files for device relationships

## 📞 Support

For issues or questions:
1. Check deployment logs for detailed error messages
2. Verify device connectivity and credentials
3. Review the troubleshooting section above

## 🔄 Updates

The framework includes:
- **Parallel execution** for faster deployments
- **Real-time progress** feedback
- **Comprehensive logging** for debugging
- **Case-insensitive** device name handling
- **Two-stage deployment** for safety

---

**Version**: 1.0  
**Last Updated**: 2025-07-14  
**Python**: 3.8+  
**Dependencies**: paramiko, pyyaml, pandas, openpyxl, requests 