# Normalization Workflow Guide

## Overview

The normalization workflow addresses the naming inconsistencies that were causing QA test failures. It ensures that the bridge domain builder uses properly normalized device names throughout the entire process.

## Problem Analysis

### Why QA Tests Were Failing

The QA tests showed an **81.7% success rate** (down from previous higher rates) because:

1. **Naming Inconsistencies**: Device names in LLDP data didn't match collected device names
   - LLDP: `DNAAS-SPINE-NCP1-B08` 
   - Collected: `DNAAS_SPINE_B08`

2. **Bridge Domain Builder Issues**: The bridge domain builder wasn't using normalized topology data
3. **Missing Spine Connections**: Failed devices couldn't find their spine connections due to naming mismatches

### Root Cause

The normalization system was **implemented but not fully integrated**:
- ✅ Device name normalizer was created
- ✅ Enhanced topology discovery was implemented  
- ❌ Bridge domain builder wasn't using enhanced topology
- ❌ Main workflow wasn't running enhanced discovery

## Solution: Comprehensive Normalization Workflow

### Two Workflow Options

#### Option 1: Automated Workflow (Recommended)
```bash
python scripts/comprehensive_normalization_workflow.py
```

**Features:**
- Fully automated execution
- Comprehensive backup of existing data
- Detailed logging and progress tracking
- Automatic QA testing
- Workflow report generation

#### Option 2: Manual Step-by-Step Workflow
```bash
./scripts/manual_normalization_workflow.sh
```

**Features:**
- Interactive step-by-step execution
- User confirmation at each step
- Detailed explanations of each step
- Manual control over the process

### Workflow Steps

#### Step 1: Backup Existing Data
- Creates timestamped backup of all topology and QA files
- Preserves existing data for rollback if needed
- Backup location: `backups/backup_YYYYMMDD_HHMMSS/`

#### Step 2: Run Probe+Parse
- Collects fresh LACP and LLDP data from all devices
- Generates `topology/device_status.json`
- Updates `topology/collection_summary.txt`

#### Step 3: Run Enhanced Topology Discovery
- Applies device name normalization to all device names
- Generates `topology/enhanced_topology.json`
- Creates `topology/device_mappings.json`
- Produces `topology/enhanced_topology_summary.json`

#### Step 4: Verify Enhanced Topology
- Validates that enhanced topology file exists
- Shows normalization statistics and examples
- Confirms device count and mapping quality

#### Step 5: Run QA Tests
- Executes comprehensive bridge domain tests
- Uses normalized topology data
- Generates new QA reports
- Shows success rate improvement

#### Step 6: Final Summary
- Lists all generated files
- Provides next steps
- Shows workflow completion status

## Expected Results

### Before Normalization
- **QA Success Rate**: ~81.7%
- **Failed Cases**: 20 out of 109 tests
- **Common Error**: "No configuration generated"
- **Root Cause**: Naming inconsistencies

### After Normalization
- **Expected QA Success Rate**: >95%
- **Failed Cases**: <5 out of 109 tests
- **Error Resolution**: Proper spine connection mapping
- **Root Cause**: Resolved naming inconsistencies

### Generated Files

#### Enhanced Topology Files
- `topology/enhanced_topology.json` - Normalized topology data
- `topology/enhanced_topology_summary.json` - Normalization statistics
- `topology/device_mappings.json` - Device name mappings

#### QA Test Files
- `QA/comprehensive_bridge_domain_test_report.txt` - Detailed test report
- `QA/comprehensive_bridge_domain_test_results.json` - Test results data

#### Workflow Reports
- `workflow_report_YYYYMMDD_HHMMSS.json` - Workflow execution report
- `backups/backup_YYYYMMDD_HHMMSS/` - Backup of original data

## Integration Points

### Bridge Domain Builder
The bridge domain builder now automatically:
1. **Checks for enhanced topology**: `topology/enhanced_topology.json`
2. **Uses enhanced topology if available**: Applies normalization automatically
3. **Falls back to legacy topology**: With normalization applied
4. **Normalizes device names**: For all path calculations

### Main Workflow
The main menu now includes:
- **Option 2**: Enhanced Topology Discovery (With Normalization)
- **Automatic integration**: Enhanced topology used by bridge domain builder

### QA Testing
QA tests now:
- **Use normalized topology**: For all bridge domain calculations
- **Handle naming inconsistencies**: Automatically
- **Provide better success rates**: Due to resolved naming issues

## Troubleshooting

### Common Issues

#### Issue: Enhanced topology not found
**Solution**: Run enhanced topology discovery first
```bash
python scripts/enhanced_topology_discovery.py
```

#### Issue: QA tests still failing
**Solution**: Verify enhanced topology is being used
```bash
python -c "
import json
with open('topology/enhanced_topology.json', 'r') as f:
    data = json.load(f)
print(f'Enhanced topology contains {len(data.get(\"devices\", {}))} devices')
"
```

#### Issue: Device mappings not working
**Solution**: Check device mappings file
```bash
python -c "
import json
with open('topology/device_mappings.json', 'r') as f:
    data = json.load(f)
print(f'Device mappings: {len(data.get(\"name_mappings\", {}))} entries')
"
```

### Rollback Procedure

If issues occur, rollback to previous state:
```bash
# Find latest backup
ls -la backups/

# Restore from backup
cp backups/backup_YYYYMMDD_HHMMSS/* topology/
cp backups/backup_YYYYMMDD_HHMMSS/* QA/
```

## Best Practices

### For Production Use
1. **Always run enhanced topology discovery** after probe+parse
2. **Use enhanced topology** for all bridge domain operations
3. **Monitor QA test results** for any remaining issues
4. **Keep backups** of working configurations

### For Development
1. **Test normalization** with small device sets first
2. **Validate device mappings** before full deployment
3. **Review QA test results** for edge cases
4. **Update device mappings** as new naming patterns are discovered

## Future Enhancements

### Planned Improvements
1. **Automatic pattern detection**: Learn new naming patterns
2. **Fuzzy matching improvements**: Better handling of similar names
3. **Real-time normalization**: Apply during data collection
4. **Validation rules**: Ensure normalization quality

### Integration Opportunities
1. **Device inventory integration**: Use inventory data for validation
2. **Network management systems**: Export normalized data
3. **Configuration management**: Apply normalization to configs
4. **Monitoring integration**: Use normalized names in monitoring

## Conclusion

The normalization workflow provides a comprehensive solution to the naming inconsistency issues that were affecting QA test success rates. By properly integrating the normalization system throughout the entire workflow, the bridge domain builder can now handle naming inconsistencies automatically, leading to significantly improved success rates and more reliable automation.

The workflow is designed to be both automated and manual, providing flexibility for different operational needs while ensuring consistent results across all environments. 