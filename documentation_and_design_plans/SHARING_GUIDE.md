# 📦 Sharing Guide: Lab Automation Framework

This guide explains how to share your lab automation framework with others.

## 🎯 **Option 1: Git Repository (Recommended)**

### **For GitHub/GitLab:**
```bash
# 1. Create a new repository on GitHub/GitLab
# 2. Add your remote origin
git remote add origin https://github.com/yourusername/lab-automation.git

# 3. Push to repository
git push -u origin main
```

### **For Direct Sharing:**
```bash
# Create a compressed archive
tar -czf lab-automation-framework.tar.gz --exclude='.git' --exclude='configs' --exclude='topology' --exclude='devices.yaml' .

# Or use zip
zip -r lab-automation-framework.zip . -x "*.git*" "configs/*" "topology/*" "devices.yaml"
```

## 📋 **What Gets Shared:**

### ✅ **Included Files:**
- `main.py` - Main application entry point
- `scripts/` - All automation scripts
- `config_engine/` - Core configuration engine
- `README.md` - Comprehensive documentation
- `requirements.txt` - Python dependencies
- `devices.yaml.example` - Example device configuration
- `.gitignore` - Git ignore rules

### ❌ **Excluded Files (Security):**
- `devices.yaml` - Contains SSH credentials
- `configs/` - Generated configurations
- `topology/` - Generated topology data
- `backups/` - Backup files
- `*.log` - Log files with device info

## 🚀 **Recipient Setup Instructions:**

### **1. Prerequisites:**
```bash
# Python 3.8+ required
python --version

# Install dependencies
pip install -r requirements.txt
```

### **2. Configuration:**
```bash
# Copy example device file
cp devices.yaml.example devices.yaml

# Edit with your device information
nano devices.yaml
```

### **3. Run the Framework:**
```bash
python main.py
```

## 📁 **File Structure for Recipients:**

```
lab_automation/
├── main.py                    # 🚀 Main entry point
├── README.md                  # 📖 Complete documentation
├── requirements.txt           # 📦 Python dependencies
├── devices.yaml.example      # 📋 Example device config
├── .gitignore               # 🔒 Security exclusions
├── scripts/                 # 🔧 Core automation
│   ├── inventory_manager.py
│   ├── collect_lacp_xml.py
│   ├── enhanced_topology_discovery.py
│   ├── ascii_topology_tree.py
│   ├── minimized_topology_tree.py
│   └── ssh_push_menu.py
└── config_engine/           # ⚙️ Configuration engine
    ├── bridge_domain_builder.py
    └── ssh_push_manager.py
```

## 🔒 **Security Considerations:**

### **Sensitive Data Protection:**
- ✅ SSH credentials excluded from sharing
- ✅ Generated configs excluded
- ✅ Device-specific data excluded
- ✅ Log files excluded

### **Recipient Security:**
- 🔐 Recipients must create their own `devices.yaml`
- 🔐 Recipients must provide their own SSH credentials
- 🔐 Recipients must have network access to devices

## 📤 **Sharing Methods:**

### **Method 1: Git Repository**
```bash
# Best for ongoing collaboration
git clone https://github.com/yourusername/lab-automation.git
cd lab-automation
```

### **Method 2: Compressed Archive**
```bash
# For one-time sharing
# Send: lab-automation-framework.tar.gz
# Recipient:
tar -xzf lab-automation-framework.tar.gz
cd lab-automation-framework
```

### **Method 3: Direct File Transfer**
```bash
# For local sharing
# Copy the entire directory (excluding sensitive files)
cp -r lab_automation/ /path/to/shared/location/
```

## 🛠️ **Recipient Quick Start:**

### **Step 1: Environment Setup**
```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Device Configuration**
```bash
# Copy and edit device configuration
cp devices.yaml.example devices.yaml
nano devices.yaml  # Edit with your device info
```

### **Step 3: Test Run**
```bash
# Run the framework
python main.py

# Select option 2 (User Options)
# Try option 3 (View ASCII Topology Tree) first
```

## 📞 **Support for Recipients:**

### **Common Issues:**
1. **"Missing SSH info"**: Check device name case in `devices.yaml`
2. **Connection timeouts**: Verify network connectivity
3. **Import errors**: Install missing dependencies

### **Debug Steps:**
```bash
# Check Python version
python --version

# Verify dependencies
pip list | grep -E "(paramiko|pyyaml|pandas)"

# Test SSH connectivity manually
ssh username@device_ip
```

## 🔄 **Updates and Maintenance:**

### **For Framework Updates:**
```bash
# Pull latest changes
git pull origin main

# Or download new archive and replace files
```

### **For Recipient Updates:**
- Send updated `requirements.txt` if dependencies change
- Send updated `README.md` for new features
- Send updated scripts for bug fixes

## 📊 **Sharing Checklist:**

- [ ] **Security**: Sensitive files excluded
- [ ] **Documentation**: README.md included
- [ ] **Dependencies**: requirements.txt included
- [ ] **Examples**: devices.yaml.example included
- [ ] **Testing**: Framework tested before sharing
- [ ] **Instructions**: Recipient setup guide provided

---

**🎯 Goal**: Enable others to use your lab automation framework while protecting sensitive information and providing clear setup instructions. 