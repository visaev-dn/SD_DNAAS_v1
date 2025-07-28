# Network Automation Framework - Quick Reference

## 🚀 Quick Start Commands

### Complete Workflow (One Command)
```bash
python scripts/build_bridge_domain.py \
    --service-name "g_visaev_v253" \
    --vlan-id 253 \
    --source-leaf "DNAAS-LEAF-B06" \
    --source-port "xe-0/0/0" \
    --dest-leaf "DNAAS-LEAF-B07" \
    --dest-port "xe-0/0/0"
```

### Enhanced Topology Discovery
```bash
python scripts/enhanced_topology_discovery.py
```

### QA Testing
```bash
python qa/advanced_tester.py
```

## 📋 Phase-by-Phase Commands

### Phase 1: Discovery & Collection
```bash
# 1. Populate device inventory
python scripts/populate_devices_from_inventory.py

# 2. Collect XML configurations
python scripts/collect_xml_configs.py

# 3. Parse LLDP neighbors
python scripts/parse_lldp_from_xml.py

# 4. Parse bundle mappings
python scripts/parse_bundle_mapping_from_xml.py
```

### Phase 2: Topology Discovery
```bash
# 5. Discover base topology
python scripts/discover_topology.py

# 6. Apply enhanced topology discovery
python scripts/enhanced_topology_discovery.py
```

### Phase 3: Bridge Domain Configuration
```bash
# 7. Build bridge domain configurations
python scripts/build_bridge_domain.py \
    --service-name "test_service" \
    --vlan-id 100 \
    --source-leaf "DNAAS-LEAF-B06" \
    --source-port "xe-0/0/0" \
    --dest-leaf "DNAAS-LEAF-B07" \
    --dest-port "xe-0/0/0"
```

### Phase 4: Quality Assurance
```bash
# 8. Validate configurations
python qa/validator.py

# 9. Run comprehensive testing
python qa/advanced_tester.py

# 10. Review test reports
ls qa/test_reports/
```

## 🔧 Debugging Commands

### Normalization Testing
```bash
# Test device name normalization
python scripts/test_normalization.py

# Show normalization patterns
python scripts/show_normalization_patterns.py

# Clear normalization cache
python scripts/clear_normalization_cache.py
```

### Topology Validation
```bash
# Check spine connections
python scripts/check_spine_connections.py

# Validate topology data
python scripts/validate_topology_data.py

# Check bundle mappings
python scripts/validate_bundle_mappings.py
```

### Bridge Domain Debugging
```bash
# Debug path calculation
python scripts/debug_path_calculation.py --source DNAAS-LEAF-B06 --dest DNAAS-LEAF-B07

# Debug bundle mapping
python scripts/debug_bundle_mapping.py --device DNAAS-LEAF-B06 --interface xe-0/0/0

# Debug configuration generation
python scripts/debug_config_generation.py --config bridge_domain_config.yaml
```

## 📊 Monitoring Commands

### Check System Status
```bash
# Check collection status
python scripts/check_collection_status.py

# Validate topology
python scripts/validate_topology.py

# Test bridge domain builder
python scripts/test_bridge_domain.py
```

### Review Logs
```bash
# View topology discovery logs
tail -f logs/topology_discovery.log

# View bridge domain builder logs
tail -f logs/bridge_domain_builder.log

# View normalization logs
tail -f logs/normalization.log
```

### Check Test Results
```bash
# View latest test report
cat qa/test_reports/latest_test_report.txt

# Check success rates
grep "Success Rate" qa/test_reports/*.txt

# Analyze failures
grep "FAILED" qa/test_reports/*.txt
```

## 🛠️ Troubleshooting Commands

### Common Issues

#### Bundle Lookup Failures
```bash
# Check bundle mappings
cat topology/bundle_mapping_v2.yaml

# Test normalization
python scripts/test_normalization.py

# Verify device names
python scripts/verify_device_names.py
```

#### Path Calculation Errors
```bash
# Run enhanced topology discovery
python scripts/enhanced_topology_discovery.py

# Check spine connections
python scripts/check_spine_connections.py

# Validate bundle mappings
python scripts/validate_bundle_mappings.py
```

#### Normalization Issues
```bash
# Clear normalization cache
python scripts/clear_normalization_cache.py

# Add new patterns
# Edit config_engine/device_name_normalizer.py

# Test normalization
python scripts/test_normalization.py
```

### Debug Mode
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

## 📁 File Structure Reference

### Key Directories
```
config_engine/          # Core engine components
├── device_name_normalizer.py      # Canonical key normalization
├── enhanced_topology_discovery.py # Enhanced topology discovery
├── bridge_domain_builder.py      # Bridge domain configuration builder
└── cli_deployer.py              # Configuration deployment

scripts/               # Workflow scripts
├── collect_xml_configs.py       # XML configuration collection
├── parse_lldp_from_xml.py       # LLDP neighbor parsing
├── parse_bundle_mapping_from_xml.py # Bundle interface mapping
├── build_bridge_domain.py       # Bridge domain workflow
└── enhanced_topology_discovery.py # Enhanced topology discovery

qa/                   # Quality assurance tools
├── validator.py                  # Configuration validation
├── advanced_tester.py           # Comprehensive QA testing
└── test_reports/               # Test results and reports

topology/             # Topology data files
├── complete_topology_v2.json    # Enhanced topology data
├── bundle_mapping_v2.yaml      # Bundle interface mappings
├── enhanced_topology.json      # Normalized topology
└── device_status.json          # Device collection status
```

### Key Files
```
devices.yaml                    # Device inventory
bridge_domain_config.yaml       # Generated bridge domain configuration
logs/                          # Log files directory
qa/test_reports/               # Test result reports
```

## 🔍 Common Patterns

### Device Name Variations
```bash
# Examples of normalization:
"DNAAS-SPINE-NCP1-B08" -> "DNAAS-SPINE-B08"
"DNAAS_LEAF_B06_2" -> "DNAAS-LEAF-B06-2"
"DNAAS-SUPERSPINE-D04-NCC" -> "DNAAS-SUPERSPINE-D04-NCC"
```

### Bundle Mapping Format
```yaml
bundles:
  DNAAS-LEAF-B06_bundle-ae1:
    device: DNAAS-LEAF-B06
    name: ae1
    members: [xe-0/0/0, xe-0/0/1]
    connections:
      - remote_device: DNAAS-SPINE-B08
        local_interface: xe-0/0/0
        remote_interface: xe-0/0/0
```

### Bridge Domain Configuration Format
```yaml
DNAAS-LEAF-B06:
  - network-services bridge-domain instance g_visaev_v253 interface ae1.253
  - interfaces ae1.253 l2-service enabled
  - interfaces ae1.253 vlan-id 253
  - network-services bridge-domain instance g_visaev_v253 interface xe-0/0/0.253
  - interfaces xe-0/0/0.253 l2-service enabled
  - interfaces xe-0/0/0.253 vlan-id 253
```

## 📊 Success Metrics

### Recent Results
- **100% success rate** achieved with enhanced normalization
- **Comprehensive error handling** for naming inconsistencies
- **Robust bundle mapping** with canonical key lookups
- **Detailed logging** for debugging and monitoring

### Key Performance Indicators
1. **Collection Success Rate**: Percentage of devices successfully collected
2. **Topology Accuracy**: Percentage of correct connections identified
3. **Configuration Success Rate**: Percentage of successful config generations
4. **Test Pass Rate**: Percentage of QA tests passing

## 🚨 Emergency Commands

### Reset System
```bash
# Clear all caches
python scripts/clear_all_caches.py

# Reset topology data
python scripts/reset_topology.py

# Clear test reports
rm -rf qa/test_reports/*
```

### Backup and Restore
```bash
# Backup working configuration
python scripts/backup_configuration.py

# Restore from backup
python scripts/restore_configuration.py --backup backup_20240115.tar.gz
```

### Force Rebuild
```bash
# Force complete rebuild
python scripts/force_rebuild.py

# Rebuild with enhanced discovery
python scripts/enhanced_topology_discovery.py --force
```

## 📞 Support Commands

### Get Help
```bash
# Show help for bridge domain builder
python scripts/build_bridge_domain.py --help

# Show help for enhanced topology discovery
python scripts/enhanced_topology_discovery.py --help

# Show help for QA tester
python qa/advanced_tester.py --help
```

### Generate Reports
```bash
# Generate normalization report
python scripts/generate_normalization_report.py

# Generate topology report
python scripts/generate_topology_report.py

# Generate QA report
python qa/generate_qa_report.py
```

This quick reference provides the most commonly used commands and workflows for the network automation framework. 