# Bridge Domain Discovery and Mapping Design Plan

## 🎯 Overview

**Goal**: Automatically discover and map existing bridge domain configurations across the network, handling manual misconfigurations and inconsistent formats.

**Challenge**: Users often manually configure bridge domains with:
- Inconsistent naming conventions
- Non-standard VLAN assignments
- Manual path configurations that don't follow automation patterns
- Mixed configuration styles across devices

## 🏗️ Architecture

### 1. Data Collection Layer
```
Network Devices → Raw Config Collection → Parsed Bridge Domain Data
```

### 2. Analysis Layer
```
Parsed Data → Pattern Recognition → Bridge Domain Mapping → Validation
```

### 3. Output Layer
```
Validated Mappings → JSON Structure → Visualization → Integration
```

## 📊 Data Collection Strategy

### Phase 1: Comprehensive Config Collection
- **Show commands to collect**:
  - `show bridge-domain brief`
  - `show bridge-domain detail`
  - `show interfaces brief`
  - `show vlan brief`
  - `show running-config interface ge100-0/0/*`
  - `show l2vpn xconnect brief`
  - `show l2vpn xconnect detail`

### Phase 2: Targeted Bridge Domain Discovery
- **Pattern-based collection**:
  - Search for `bridge-domain` configurations
  - Extract VLAN mappings
  - Identify interface associations
  - Map service names to configurations

## 🔍 Pattern Recognition Engine

### 1. Service Name Patterns
```python
# Expected patterns (from our automation)
g_username_vvlan_id
g_visaev_v253

# Manual patterns (users might use)
visaev_v253
visaev-253
visaev253
user_visaev_vlan_253
```

### 2. VLAN ID Patterns
```python
# Standard VLAN ranges
1-4094 (standard)
1000-4094 (extended)

# Common user assignments
100-999 (user VLANs)
2000-2999 (service VLANs)
```

### 3. Interface Pattern Recognition
```python
# Expected patterns
ge100-0/0/X
ge100-0/0/X.Y

# Manual variations
ge100-0/0/X
ge100-0/0/X.Y
ge100-0/0/X:Y
```

## 🗺️ Mapping Strategy

### 1. Multi-Level Validation
```python
# Level 1: Exact Pattern Match
if service_name matches "g_username_vvlan":
    confidence = 100%

# Level 2: Fuzzy Pattern Match
if service_name contains username and vlan:
    confidence = 80%

# Level 3: Contextual Match
if vlan_id matches and interface patterns match:
    confidence = 60%
```

### 2. Bridge Domain Association
```python
# Map bridge domains to:
{
    "service_name": "g_visaev_v253",
    "vlan_id": 253,
    "username": "visaev",
    "devices": {
        "DNAAS-LEAF-A01": {
            "interfaces": ["ge100-0/0/10"],
            "bridge_domain": "g_visaev_v253",
            "vlan": 253
        }
    },
    "confidence": 95,
    "detection_method": "pattern_match"
}
```

## ⚠️ Potential Issues and Solutions

### 1. **Manual Misconfigurations**
**Issues**:
- Users create bridge domains without following naming conventions
- Inconsistent VLAN assignments
- Manual path configurations that bypass automation

**Solutions**:
- Fuzzy matching algorithms
- Contextual analysis (VLAN ranges, interface patterns)
- Confidence scoring system
- Manual review prompts for low-confidence matches

### 2. **Inconsistent Naming**
**Issues**:
- `visaev_v253` vs `g_visaev_v253`
- `user_visaev_vlan_253` vs `visaev253`

**Solutions**:
- Multiple regex patterns
- Levenshtein distance matching
- Username extraction from various formats
- VLAN ID extraction from service names

### 3. **Path Inconsistencies**
**Issues**:
- Manual path configurations don't follow automation patterns
- Mixed 2-tier and 3-tier paths
- Incomplete configurations

**Solutions**:
- Path validation against topology
- Detection of manual vs automated paths
- Gap analysis for incomplete configurations

### 4. **Data Quality Issues**
**Issues**:
- Incomplete show command output
- Device connectivity issues
- Parsing errors

**Solutions**:
- Multiple data collection methods
- Fallback parsing strategies
- Error handling and retry mechanisms
- Data validation checks

## 🛠️ Implementation Plan

### Phase 1: Data Collection Engine
```python
class BridgeDomainCollector:
    def collect_raw_configs(self, devices):
        # Collect show commands from all devices
        pass
    
    def parse_bridge_domains(self, raw_configs):
        # Parse bridge domain configurations
        pass
    
    def extract_service_patterns(self, configs):
        # Identify service naming patterns
        pass
```

### Phase 2: Pattern Recognition Engine
```python
class BridgeDomainAnalyzer:
    def identify_service_patterns(self, bridge_domains):
        # Match against known patterns
        pass
    
    def extract_username_vlan(self, service_name):
        # Extract username and VLAN from service name
        pass
    
    def calculate_confidence(self, match):
        # Calculate confidence score
        pass
```

### Phase 3: Mapping Engine
```python
class BridgeDomainMapper:
    def map_bridge_domains(self, analyzed_data):
        # Create comprehensive mapping
        pass
    
    def validate_paths(self, mappings):
        # Validate against topology
        pass
    
    def generate_report(self, mappings):
        # Generate JSON and visual reports
        pass
```

## 📋 Data Structures

### Bridge Domain Mapping JSON
```json
{
    "discovery_metadata": {
        "timestamp": "2024-01-15T10:30:00Z",
        "devices_scanned": 45,
        "bridge_domains_found": 23,
        "confidence_threshold": 70
    },
    "bridge_domains": [
        {
            "service_name": "g_visaev_v253",
            "detected_name": "g_visaev_v253",
            "vlan_id": 253,
            "username": "visaev",
            "confidence": 95,
            "detection_method": "exact_pattern",
            "devices": {
                "DNAAS-LEAF-A01": {
                    "interfaces": ["ge100-0/0/10"],
                    "bridge_domain": "g_visaev_v253",
                    "vlan": 253,
                    "path_type": "automated_2_tier"
                },
                "DNAAS-LEAF-B02": {
                    "interfaces": ["ge100-0/0/20"],
                    "bridge_domain": "g_visaev_v253",
                    "vlan": 253,
                    "path_type": "automated_2_tier"
                }
            },
            "path_validation": {
                "is_valid": true,
                "path_type": "2_tier",
                "spine_devices": ["DNAAS-SPINE-A01"],
                "issues": []
            }
        }
    ],
    "unmapped_configurations": [
        {
            "service_name": "unknown_service_123",
            "vlan_id": 123,
            "devices": ["DNAAS-LEAF-C03"],
            "confidence": 30,
            "reason": "no_pattern_match"
        }
    ]
}
```

## 🎯 Success Metrics

### 1. **Discovery Accuracy**
- Percentage of bridge domains correctly identified
- Confidence score distribution
- False positive/negative rates

### 2. **Coverage**
- Number of devices successfully scanned
- Percentage of network coverage
- Data completeness metrics

### 3. **Performance**
- Collection time per device
- Total discovery time
- Resource utilization

## 🚀 Integration Points

### 1. **Main Menu Integration**
```python
def show_user_menu():
    # Add new option:
    print("7. 🔍 Discover Existing Bridge Domains")
```

### 2. **Topology Integration**
- Validate discovered paths against topology
- Identify gaps in configurations
- Suggest optimizations

### 3. **Configuration Management**
- Compare discovered configs with automation templates
- Identify manual vs automated configurations
- Suggest standardization opportunities

## 🔧 Technical Implementation

### 1. **Collection Scripts**
- `scripts/bridge_domain_collector.py`
- `scripts/bridge_domain_analyzer.py`
- `scripts/bridge_domain_mapper.py`

### 2. **Configuration Engine**
- `config_engine/bridge_domain_discovery.py`
- `config_engine/pattern_matcher.py`
- `config_engine/confidence_calculator.py`

### 3. **Output Formats**
- JSON mapping files
- HTML reports
- ASCII visualizations
- Integration with existing topology tools

## 🎯 Next Steps

1. **Start with data collection** - Implement comprehensive config collection
2. **Build pattern recognition** - Create flexible pattern matching
3. **Implement confidence scoring** - Develop reliable confidence metrics
4. **Create mapping engine** - Build comprehensive mapping system
5. **Add validation** - Integrate with topology for path validation
6. **Generate reports** - Create useful output formats
7. **Integrate with main menu** - Add to user workflow

This feature will provide tremendous value by:
- **Visibility** - Understanding what's actually configured
- **Compliance** - Identifying manual vs automated configurations
- **Optimization** - Finding opportunities for standardization
- **Documentation** - Creating comprehensive network maps

Ready to start implementing! 🚀 