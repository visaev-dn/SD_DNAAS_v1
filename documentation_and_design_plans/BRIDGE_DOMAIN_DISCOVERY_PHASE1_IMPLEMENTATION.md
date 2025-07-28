# Bridge Domain Discovery - Phase 1 Implementation Plan

## 🎯 Phase 1 Overview

**Goal**: Implement comprehensive data collection and parsing for bridge domain discovery, handling the complex relationship between bridge domains, interfaces, subinterfaces, and VLAN configurations.

**Focus**: Collect and parse bridge domain configurations from network devices, mapping the relationships between:
- Bridge domain instances
- Interface associations
- Subinterface VLAN mappings
- VLAN manipulation configurations

## 📊 Data Collection Requirements

### 1. Primary Collection Commands

#### A. Bridge Domain Instance Discovery
```bash
show config | fl | i "bridge-domain instance"
```

**Expected Output Pattern**:
```
network-services bridge-domain instance M_kazakov_1360 admin-state enabled
network-services bridge-domain instance M_kazakov_1360 interface ge100-0/0/4 ^
network-services bridge-domain instance M_kazakov_1360 interface ge100-0/0/13.1360 ^
network-services bridge-domain instance M_kazakov_1361 admin-state enabled
network-services bridge-domain instance M_kazakov_1361 interface ge100-0/0/6 ^
network-services bridge-domain instance M_kazakov_1361 interface ge100-0/0/13.1361 ^
```

**What We Extract**:
- Bridge domain instance names (e.g., `M_kazakov_1360`)
- Associated interfaces (e.g., `ge100-0/0/4`, `ge100-0/0/13.1360`)
- Admin state (enabled/disabled)

#### B. VLAN Configuration Discovery
```bash
show config | fl | i vlan
```

**Expected Output Pattern**:
```
interfaces bundle-445 vlan-manipulation egress-mapping action pop
interfaces bundle-447.447 vlan-id 447
interfaces bundle-1204 vlan-manipulation egress-mapping action pop
interfaces bundle-1204 vlan-manipulation ingress-mapping action push outer-tag 1191 outer-tpid 0x8100
interfaces bundle-5953.445 vlan-id 445
interfaces bundle-60000.190 vlan-id 190
interfaces bundle-60000.193 vlan-id 193
```

**What We Extract**:
- Interface/subinterface to VLAN ID mappings
- VLAN manipulation configurations
- QinQ and other advanced VLAN configurations

## 🔍 Parsing Challenges and Solutions

### Challenge 1: Subinterface to VLAN Mapping

**Problem**: Subinterface number doesn't always match VLAN ID
```
ge100-0/0/13.1360 → VLAN 1360 (matches)
ge100-0/0/13.1361 → VLAN 1361 (matches)
ge100-0/0/13.190  → VLAN 190  (matches)
ge100-0/0/13.193  → VLAN 193  (matches)
```

**Solution**: Create mapping table
```python
{
    "device": "DNAAS-LEAF-B13",
    "interface_mappings": {
        "ge100-0/0/13.1360": {"vlan_id": 1360, "type": "subinterface"},
        "ge100-0/0/13.1361": {"vlan_id": 1361, "type": "subinterface"},
        "ge100-0/0/13.190": {"vlan_id": 190, "type": "subinterface"},
        "ge100-0/0/13.193": {"vlan_id": 193, "type": "subinterface"}
    }
}
```

### Challenge 2: VLAN Manipulation Detection

**Problem**: Complex VLAN configurations that we don't fully support yet
```
interfaces bundle-1204 vlan-manipulation egress-mapping action pop
interfaces bundle-1204 vlan-manipulation ingress-mapping action push outer-tag 1191 outer-tpid 0x8100
```

**Solution**: Mark for future development
```python
{
    "device": "DNAAS-LEAF-B13",
    "vlan_manipulation": {
        "bundle-1204": {
            "type": "qinq",
            "egress": "pop",
            "ingress": "push outer-tag 1191",
            "status": "unsupported_template"
        }
    }
}
```

### Challenge 3: Service Name Pattern Recognition

**Key Insight**: The string after "instance" is always the bridge-domain name, regardless of format.

**Problem**: Various naming conventions in bridge domain instances
```
M_kazakov_1360  # Manual format
g_visaev_v253    # Automated format
visaev_253       # Simplified format
user_visaev_vlan_253  # Descriptive format
unknown_service_123    # Unknown format
```

**Solution**: Extract bridge domain name directly, then apply pattern recognition
```python
# Step 1: Extract bridge domain name from "instance" keyword
# network-services bridge-domain instance M_kazakov_1360 admin-state enabled
#                                    ^^^^^^^^^^^^^^^^
#                                    bridge_domain_name

# Step 2: Apply pattern recognition to extracted name
patterns = [
    r'g_(\w+)_v(\d+)',           # g_visaev_v253
    r'M_(\w+)_(\d+)',            # M_kazakov_1360
    r'(\w+)_(\d+)',              # visaev_253
    r'user_(\w+)_vlan_(\d+)',    # user_visaev_vlan_253
]

# Step 3: If no pattern matches, still capture the bridge domain name
# but mark as unknown format
```

## 🛠️ Implementation Architecture

### 1. Data Collection Engine

```python
class BridgeDomainCollector:
    def __init__(self):
        self.collection_commands = [
            'show config | fl | i "bridge-domain instance"',
            'show config | fl | i vlan'
        ]
    
    def collect_from_device(self, device_name):
        """Collect bridge domain data from a single device"""
        pass
    
    def collect_from_all_devices(self, devices):
        """Collect from all devices in parallel"""
        pass
```

### 2. Parsing Engine

```python
class BridgeDomainParser:
    def parse_bridge_domain_instances(self, raw_output):
        """Parse bridge-domain instance configurations"""
        # Extract bridge domain name directly from "instance" keyword
        # No lookup required - capture all bridge domain names
        pass
    
    def parse_vlan_configurations(self, raw_output):
        """Parse VLAN configurations and mappings"""
        pass
    
    def create_interface_vlan_mapping(self, device_name, vlan_configs):
        """Create interface to VLAN ID mapping"""
        pass
    
    def detect_vlan_manipulation(self, vlan_configs):
        """Detect and categorize VLAN manipulation configurations"""
        pass
```

### 3. Pattern Recognition Engine

```python
class ServiceNameAnalyzer:
    def __init__(self):
        self.patterns = [
            # Automated patterns
            r'g_(\w+)_v(\d+)',           # g_visaev_v253
            # Manual patterns
            r'M_(\w+)_(\d+)',            # M_kazakov_1360
            r'(\w+)_(\d+)',              # visaev_253
            r'user_(\w+)_vlan_(\d+)',    # user_visaev_vlan_253
        ]
    
    def extract_service_info(self, bridge_domain_name):
        """Extract username and VLAN from bridge domain name"""
        # Apply pattern matching to extracted bridge domain name
        # If no pattern matches, still capture the name but mark as unknown
        pass
    
    def calculate_confidence(self, match_result):
        """Calculate confidence score for pattern match"""
        pass
```

## 📋 Data Structures

### 1. Raw Collection Data
```json
{
    "device_name": "DNAAS-LEAF-B13",
    "collection_timestamp": "2024-01-15T10:30:00Z",
    "bridge_domain_instances": [
        {
            "name": "M_kazakov_1360",
            "admin_state": "enabled",
            "interfaces": ["ge100-0/0/4", "ge100-0/0/13.1360"]
        },
        {
            "name": "M_kazakov_1361", 
            "admin_state": "enabled",
            "interfaces": ["ge100-0/0/6", "ge100-0/0/13.1361"]
        }
    ],
    "vlan_configurations": [
        {
            "interface": "bundle-447.447",
            "vlan_id": 447,
            "type": "subinterface"
        },
        {
            "interface": "bundle-1204",
            "vlan_manipulation": {
                "egress": "pop",
                "ingress": "push outer-tag 1191 outer-tpid 0x8100"
            },
            "type": "manipulation"
        }
    ]
}
```

### 2. Parsed Bridge Domain Data
```json
{
    "device_name": "DNAAS-LEAF-B13",
    "bridge_domains": [
        {
            "service_name": "M_kazakov_1360",
            "detected_username": "kazakov",
            "detected_vlan": 1360,
            "confidence": 85,
            "detection_method": "manual_pattern",
            "interfaces": [
                {
                    "name": "ge100-0/0/4",
                    "type": "physical",
                    "vlan_id": null
                },
                {
                    "name": "ge100-0/0/13.1360",
                    "type": "subinterface",
                    "vlan_id": 1360
                }
            ],
            "vlan_manipulation": null
        },
        {
            "service_name": "unknown_service_123",
            "detected_username": null,
            "detected_vlan": null,
            "confidence": 0,
            "detection_method": "unknown_format",
            "interfaces": [
                {
                    "name": "ge100-0/0/10",
                    "type": "physical",
                    "vlan_id": null
                }
            ],
            "vlan_manipulation": null
        }
    ],
    "vlan_manipulation_configs": [
        {
            "interface": "bundle-1204",
            "type": "qinq",
            "status": "unsupported_template",
            "configuration": {
                "egress": "pop",
                "ingress": "push outer-tag 1191 outer-tpid 0x8100"
            }
        }
    ]
}
```

## 🔧 Implementation Steps

### Step 1: Extend Existing Collection Framework
```python
# Modify scripts/collect_lacp_xml.py to include bridge domain collection
def collect_bridge_domain_data(self, devices):
    """Add bridge domain collection to existing framework"""
    pass
```

### Step 2: Create Bridge Domain Parser
```python
# Create config_engine/bridge_domain_parser.py
class BridgeDomainParser:
    def parse_device_config(self, device_name, raw_configs):
        """Parse all bridge domain related configurations"""
        pass
```

### Step 3: Create Service Name Analyzer
```python
# Create config_engine/service_name_analyzer.py
class ServiceNameAnalyzer:
    def analyze_bridge_domain_names(self, bridge_domains):
        """Analyze and categorize bridge domain names"""
        pass
```

### Step 4: Create Data Mapper
```python
# Create config_engine/bridge_domain_mapper.py
class BridgeDomainMapper:
    def map_device_configurations(self, parsed_data):
        """Create comprehensive bridge domain mappings"""
        pass
```

## 🎯 Success Criteria for Phase 1

### 1. **Data Collection**
- ✅ Successfully collect bridge domain instances from all devices
- ✅ Successfully collect VLAN configurations from all devices
- ✅ Handle collection failures gracefully
- ✅ Store raw data in structured format

### 2. **Parsing Accuracy**
- ✅ Correctly parse bridge domain instance names (capture ALL names)
- ✅ Correctly map interfaces to bridge domains
- ✅ Correctly map subinterfaces to VLAN IDs
- ✅ Detect and categorize VLAN manipulation configurations

### 3. **Pattern Recognition**
- ✅ Extract bridge domain names directly from "instance" keyword
- ✅ Apply pattern recognition to extracted names
- ✅ Handle unknown formats gracefully (don't miss any bridge domains)
- ✅ Calculate confidence scores for pattern matches

### 4. **Data Quality**
- ✅ Validate parsed data against expected formats
- ✅ Handle missing or corrupted data gracefully
- ✅ Provide clear error messages for parsing failures
- ✅ Create comprehensive logging for debugging

## 🚀 Next Steps After Phase 1

1. **Phase 2**: Implement path validation against topology
2. **Phase 3**: Create comprehensive mapping across all devices
3. **Phase 4**: Generate reports and visualizations
4. **Phase 5**: Integrate with main menu system

## ⚠️ Potential Issues and Mitigation

### 1. **Collection Failures**
**Issue**: Some devices may not respond
**Mitigation**: Log failures and continue with available devices

### 2. **Parsing Errors**
**Issue**: Unexpected output formats or edge cases
**Mitigation**: Comprehensive error handling and logging

### 3. **Performance Issues**
**Issue**: Large networks may take long time to collect
**Mitigation**: Parallel collection and progress tracking

### 4. **Data Inconsistencies**
**Issue**: Manual configurations may be inconsistent
**Mitigation**: Confidence scoring and manual review prompts

Ready to start implementing Phase 1! 🚀 