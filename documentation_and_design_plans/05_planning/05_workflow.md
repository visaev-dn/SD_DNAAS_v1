# Network Automation Framework - Complete Workflow

This document details the complete workflow for the network automation framework, from initial device discovery to final bridge domain configuration deployment.

## 🎯 Workflow Overview

The framework operates in four main phases:

1. **Discovery & Collection** - Gather device information and configurations
2. **Topology Discovery** - Build and enhance network topology
3. **Configuration Building** - Generate bridge domain configurations
4. **Quality Assurance** - Validate and test configurations

## 📋 Phase 1: Discovery & Collection

### Step 1.1: Device Inventory Population

**Purpose**: Populate device inventory from network discovery or manual input

**Script**: `scripts/populate_devices_from_inventory.py`

**Input**: Device inventory file or manual device list
**Output**: `devices.yaml` with device credentials and metadata

**Process**:
```bash
python scripts/populate_devices_from_inventory.py
```

**Key Features**:
- SSH connectivity testing
- Device type classification (leaf/spine/superspine)
- Credential validation
- Inventory file generation

### Step 1.2: XML Configuration Collection

**Purpose**: Collect XML configurations from all devices

**Script**: `scripts/collect_xml_configs.py`

**Input**: `devices.yaml`
**Output**: XML config files in `configs/` directory

**Process**:
```bash
python scripts/collect_xml_configs.py
```

**Key Features**:
- Parallel SSH connections
- Configuration backup
- Error handling and retry logic
- Progress reporting

### Step 1.3: LLDP Neighbor Parsing

**Purpose**: Extract LLDP neighbor information for topology building

**Script**: `scripts/parse_lldp_from_xml.py`

**Input**: XML config files
**Output**: `topology/lldp_neighbors.json`

**Process**:
```bash
python scripts/parse_lldp_from_xml.py
```

**Key Features**:
- LLDP neighbor extraction
- Interface mapping
- Device relationship discovery
- Neighbor validation

### Step 1.4: Bundle Mapping Parsing

**Purpose**: Extract bundle interface mappings from configurations

**Script**: `scripts/parse_bundle_mapping_from_xml.py`

**Input**: XML config files
**Output**: `topology/bundle_mapping_v2.yaml`

**Process**:
```bash
python scripts/parse_bundle_mapping_from_xml.py
```

**Key Features**:
- Bundle interface discovery
- Physical to logical interface mapping
- Connection relationship extraction
- Bundle validation

## 🏗️ Phase 2: Topology Discovery & Enhancement

### Step 2.1: Base Topology Discovery

**Purpose**: Build initial topology from collected data

**Script**: `scripts/discover_topology.py`

**Input**: LLDP neighbors, bundle mappings, device status
**Output**: `topology/complete_topology_v2.json`

**Process**:
```bash
python scripts/discover_topology.py
```

**Key Features**:
- Device classification
- Connection mapping
- Topology validation
- Summary generation

### Step 2.2: Enhanced Topology Discovery

**Purpose**: Apply normalization and fix connectivity issues

**Script**: `config_engine/enhanced_topology_discovery.py`

**Input**: `complete_topology_v2.json`
**Output**: `topology/enhanced_topology.json`

**Process**:
```bash
python scripts/enhanced_topology_discovery.py
```

**Key Features**:
- Canonical key normalization
- Connectivity validation
- Self-healing fixes
- Bundle-based mapping
- Comprehensive logging

**Normalization Process**:
1. **Load existing topology** from `complete_topology_v2.json`
2. **Apply canonical key normalization** to all device names
3. **Validate connectivity** using bundle mappings
4. **Fix spine connections** based on bundle data
5. **Extract spine-to-superspine** connections
6. **Generate enhanced topology** with normalized names

**Canonical Key System**:
```python
# Examples of normalization:
"DNAAS-SPINE-NCP1-B08" -> "DNAAS-SPINE-B08"
"DNAAS_LEAF_B06_2" -> "DNAAS-LEAF-B06-2"
"DNAAS-SUPERSPINE-D04-NCC" -> "DNAAS-SUPERSPINE-D04-NCC"
```

## ⚙️ Phase 3: Bridge Domain Configuration

### Step 3.1: Bridge Domain Configuration Building

**Purpose**: Generate bridge domain configurations for service paths

**Script**: `config_engine/bridge_domain_builder.py`

**Input**: Enhanced topology, bundle mappings, service parameters
**Output**: Bridge domain configuration files

**Process**:
```bash
python scripts/build_bridge_domain.py \
    --service-name "g_visaev_v253" \
    --vlan-id 253 \
    --source-leaf "DNAAS-LEAF-B06" \
    --source-port "xe-0/0/0" \
    --dest-leaf "DNAAS-LEAF-B07" \
    --dest-port "xe-0/0/0"
```

**Key Features**:
- Path calculation (2-tier or 3-tier)
- Bundle interface mapping
- Configuration generation
- Comprehensive logging

**Path Calculation Logic**:

#### 2-Tier Path (Shared Spine)
```
Source Leaf → Shared Spine → Destination Leaf
```

#### 3-Tier Path (Different Spines)
```
Source Leaf → Source Spine → SuperSpine → Destination Spine → Destination Leaf
```

**Configuration Generation**:
1. **Bridge domain instance** configuration
2. **L2 service** enablement
3. **VLAN ID** assignment
4. **Bundle interface** mapping

**Bundle Mapping Process**:
```python
# Example bundle lookup
device: "DNAAS-LEAF-B06"
interface: "xe-0/0/0"
bundle: "ae1"
```

## 🧪 Phase 4: Quality Assurance

### Step 4.1: Configuration Validation

**Purpose**: Validate generated configurations

**Script**: `qa/validator.py`

**Input**: Bridge domain configuration files
**Output**: Validation reports

**Process**:
```bash
python qa/validator.py
```

**Validation Checks**:
- Configuration syntax validation
- Path verification
- Bundle mapping validation
- Device connectivity verification

### Step 4.2: Advanced Testing

**Purpose**: Comprehensive testing with detailed reporting

**Script**: `qa/advanced_tester.py`

**Input**: Test scenarios and configurations
**Output**: Test reports in `qa/test_reports/`

**Process**:
```bash
python qa/advanced_tester.py
```

**Test Features**:
- Multiple test scenarios
- Success/failure analysis
- Iteration support
- Performance metrics
- Detailed logging

### Step 4.3: Test Report Analysis

**Purpose**: Analyze test results and identify issues

**Process**:
```bash
# Review latest test report
cat qa/test_reports/latest_test_report.txt

# Check success rates
grep "Success Rate" qa/test_reports/*.txt

# Analyze failures
grep "FAILED" qa/test_reports/*.txt
```

## 🔧 Key Components Deep Dive

### Canonical Key Normalization System

**Location**: `config_engine/device_name_normalizer.py`

**Purpose**: Handle naming inconsistencies across the network

**Features**:
- **Pattern Matching**: Regex patterns for suffix normalization
- **Fuzzy Matching**: Handle separator variations
- **Caching**: Performance optimization
- **Extensibility**: Easy pattern addition

**Normalization Rules**:
1. **Uppercase conversion**: All names to uppercase
2. **Separator normalization**: Underscores/spaces to hyphens
3. **Suffix handling**: Parenthesis to hyphenated form
4. **Device type consistency**: Standardized type naming

### Enhanced Topology Discovery

**Location**: `config_engine/enhanced_topology_discovery.py`

**Purpose**: Future-proof topology with automatic fixes

**Features**:
1. **Automatic Normalization**: Apply canonical keys to all data
2. **Connectivity Validation**: Detect missing connections
3. **Bundle-Based Mapping**: Use bundle data for validation
4. **Self-Healing**: Automatic issue fixes
5. **Comprehensive Logging**: Detailed debugging info

**Process Flow**:
1. Load existing topology
2. Apply normalization
3. Validate connectivity
4. Fix spine connections
5. Extract superspine connections
6. Generate enhanced topology

### Bridge Domain Builder

**Location**: `config_engine/bridge_domain_builder.py`

**Purpose**: Generate complete bridge domain configurations

**Features**:
- **Path Calculation**: 2-tier or 3-tier path determination
- **Bundle Mapping**: Physical to logical interface conversion
- **Configuration Generation**: Complete config creation
- **Comprehensive Logging**: Detailed trace information

**Path Calculation Logic**:
```python
# Check for shared spine (2-tier)
shared_spines = source_leaf_spines & dest_leaf_spines
if shared_spines:
    # Use 2-tier path
else:
    # Use 3-tier path with superspine
```

## 📊 Success Metrics & Monitoring

### Key Performance Indicators

1. **Collection Success Rate**: Percentage of devices successfully collected
2. **Topology Accuracy**: Percentage of correct connections identified
3. **Configuration Success Rate**: Percentage of successful config generations
4. **Test Pass Rate**: Percentage of QA tests passing

### Recent Results

- **100% success rate** achieved with enhanced normalization
- **Comprehensive error handling** for naming inconsistencies
- **Robust bundle mapping** with canonical key lookups
- **Detailed logging** for debugging and monitoring

### Monitoring Commands

```bash
# Check collection status
python scripts/check_collection_status.py

# Validate topology
python scripts/validate_topology.py

# Test bridge domain builder
python scripts/test_bridge_domain.py

# Run comprehensive QA
python qa/advanced_tester.py
```

## 🚨 Troubleshooting Guide

### Common Issues

#### 1. Bundle Lookup Failures

**Symptoms**: "Bundle lookup: device interface -> NOT FOUND"

**Causes**:
- Device name variations not normalized
- Bundle mapping file format issues
- Interface names not matching

**Solutions**:
```bash
# Check bundle mappings
cat topology/bundle_mapping_v2.yaml

# Test normalization
python scripts/test_normalization.py

# Verify device names
python scripts/verify_device_names.py
```

#### 2. Path Calculation Errors

**Symptoms**: "Could not find spine connection for leaf"

**Causes**:
- Missing spine connections in topology
- Naming inconsistencies
- Bundle mapping issues

**Solutions**:
```bash
# Run enhanced topology discovery
python scripts/enhanced_topology_discovery.py

# Check spine connections
python scripts/check_spine_connections.py

# Validate bundle mappings
python scripts/validate_bundle_mappings.py
```

#### 3. Normalization Issues

**Symptoms**: Device names not matching expected patterns

**Causes**:
- New naming conventions not covered
- Pattern matching failures
- Cache corruption

**Solutions**:
```bash
# Clear normalization cache
python scripts/clear_normalization_cache.py

# Add new patterns
# Edit config_engine/device_name_normalizer.py

# Test normalization
python scripts/test_normalization.py
```

### Debug Commands

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python scripts/build_bridge_domain.py --verbose

# Check normalization patterns
python scripts/show_normalization_patterns.py

# Validate topology data
python scripts/validate_topology_data.py
```

## 🔮 Future Enhancements

### Planned Improvements

1. **Real-time Monitoring**: Live topology validation
2. **Advanced Path Optimization**: Multi-path and load balancing
3. **Configuration Templates**: Customizable config formats
4. **API Integration**: REST API for external tools
5. **Machine Learning**: Predictive issue detection

### Extension Points

1. **New Device Types**: Support for additional network devices
2. **Custom Normalization**: User-defined naming patterns
3. **Advanced Testing**: Custom test scenarios
4. **Integration Hooks**: External system integration

## 📝 Best Practices

### Development Workflow

1. **Test Changes**: Always run QA tests after modifications
2. **Version Control**: Commit changes with descriptive messages
3. **Documentation**: Update docs for new features
4. **Backup**: Keep backups of working configurations

### Operational Workflow

1. **Regular Validation**: Run validation tests regularly
2. **Monitor Logs**: Check logs for issues
3. **Update Mappings**: Keep device mappings current
4. **Test New Patterns**: Validate new normalization patterns

### Maintenance

1. **Cache Management**: Clear caches when needed
2. **Log Rotation**: Manage log file sizes
3. **Configuration Backup**: Backup working configurations
4. **Pattern Updates**: Update normalization patterns as needed

## 📞 Support & Resources

### Documentation Files

- `README.md`: Main framework documentation
- `WORKFLOW.md`: This detailed workflow guide
- `TROUBLESHOOTING.md`: Common issues and solutions
- `API_REFERENCE.md`: Technical API documentation

### Key Scripts

- `scripts/build_bridge_domain.py`: Main workflow script
- `qa/advanced_tester.py`: Comprehensive testing
- `scripts/enhanced_topology_discovery.py`: Topology enhancement
- `scripts/test_normalization.py`: Normalization testing

### Log Files

- `logs/topology_discovery.log`: Topology discovery logs
- `logs/bridge_domain_builder.log`: Configuration building logs
- `qa/test_reports/`: Test result reports
- `logs/normalization.log`: Normalization process logs

This workflow provides a complete, end-to-end solution for network automation with robust handling of naming inconsistencies and comprehensive quality assurance. 