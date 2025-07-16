#!/bin/bash

# Manual Normalization Workflow
# Step-by-step execution of normalization workflow

set -e  # Exit on any error

echo "🚀 Manual Normalization Workflow"
echo "=================================="
echo "This script will guide you through the normalization workflow step by step."
echo ""

# Function to backup existing data
backup_data() {
    echo "📦 Step 1: Backing up existing data..."
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_dir="backups/backup_${timestamp}"
    mkdir -p "$backup_dir"
    
    # Backup topology files
    for file in topology/complete_topology_v2.json topology/device_summary_v2.yaml topology/bundle_mapping_v2.yaml topology/device_status.json topology/collection_summary.txt; do
        if [ -f "$file" ]; then
            cp "$file" "$backup_dir/"
            echo "  ✓ Backed up $file"
        fi
    done
    
    # Backup QA files
    for file in QA/comprehensive_bridge_domain_test_report.txt QA/comprehensive_bridge_domain_test_results.json; do
        if [ -f "$file" ]; then
            cp "$file" "$backup_dir/"
            echo "  ✓ Backed up $file"
        fi
    done
    
    echo "📦 Backup completed: $backup_dir"
    echo ""
}

# Function to run probe+parse
run_probe_parse() {
    echo "🔍 Step 2: Running probe+parse LACP+LLDP..."
    echo "This will collect fresh data from all devices."
    echo ""
    
    read -p "Press Enter to continue or Ctrl+C to abort..."
    
    # Run probe+parse
    echo "5" | python main.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Probe+parse completed successfully"
    else
        echo "❌ Probe+parse failed"
        exit 1
    fi
    echo ""
}

# Function to run enhanced topology discovery
run_enhanced_discovery() {
    echo "🔧 Step 3: Running enhanced topology discovery..."
    echo "This will apply normalization to device names and generate enhanced topology."
    echo ""
    
    read -p "Press Enter to continue or Ctrl+C to abort..."
    
    # Run enhanced topology discovery
    python scripts/enhanced_topology_discovery.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Enhanced topology discovery completed"
    else
        echo "❌ Enhanced topology discovery failed"
        exit 1
    fi
    echo ""
}

# Function to verify enhanced topology
verify_enhanced_topology() {
    echo "🔍 Step 4: Verifying enhanced topology..."
    
    if [ -f "topology/enhanced_topology.json" ]; then
        echo "✅ Enhanced topology file found"
        
        # Show some statistics
        device_count=$(python -c "
import json
with open('topology/enhanced_topology.json', 'r') as f:
    data = json.load(f)
print(len(data.get('devices', {})))
")
        echo "📊 Enhanced topology contains $device_count devices"
        
        # Show normalization examples
        echo "📋 Normalization examples:"
        python -c "
import json
with open('topology/enhanced_topology.json', 'r') as f:
    data = json.load(f)
devices = data.get('devices', {})
count = 0
for device_name, device_info in devices.items():
    original_name = device_info.get('original_name', device_name)
    if device_name != original_name:
        count += 1
        if count <= 5:
            print(f'  • {original_name} -> {device_name}')
if count > 5:
    print(f'  • ... and {count - 5} more devices normalized')
"
    else
        echo "❌ Enhanced topology file not found"
        exit 1
    fi
    echo ""
}

# Function to run QA tests
run_qa_tests() {
    echo "🧪 Step 5: Running QA tests..."
    echo "This will validate the normalization with comprehensive tests."
    echo ""
    
    read -p "Press Enter to continue or Ctrl+C to abort..."
    
    # Set PYTHONPATH and run QA tests
    export PYTHONPATH=$(pwd)
    python QA/advanced_bridge_domain_tester.py --random-iterations 20 --stress-iterations 10
    
    if [ $? -eq 0 ]; then
        echo "✅ QA tests completed successfully"
        
        # Show results
        if [ -f "QA/comprehensive_bridge_domain_test_report.txt" ]; then
            echo "📊 QA Test Results:"
            grep "Overall Success Rate:" QA/comprehensive_bridge_domain_test_report.txt || echo "  Results not available"
        fi
    else
        echo "❌ QA tests failed"
        exit 1
    fi
    echo ""
}

# Function to show final summary
show_summary() {
    echo "📋 Step 6: Final Summary"
    echo "========================"
    
    echo "📁 Generated files:"
    for file in topology/enhanced_topology.json topology/enhanced_topology_summary.json topology/device_mappings.json QA/comprehensive_bridge_domain_test_report.txt QA/comprehensive_bridge_domain_test_results.json; do
        if [ -f "$file" ]; then
            echo "  ✓ $file"
        else
            echo "  ❌ $file (missing)"
        fi
    done
    
    echo ""
    echo "🎉 Normalization workflow completed!"
    echo ""
    echo "Next steps:"
    echo "1. Test bridge domain builder with normalized topology"
    echo "2. Review QA test results for any remaining issues"
    echo "3. Use enhanced topology for all future operations"
    echo ""
}

# Main workflow
main() {
    echo "This workflow will:"
    echo "1. Backup existing data"
    echo "2. Run probe+parse to collect fresh data"
    echo "3. Run enhanced topology discovery with normalization"
    echo "4. Verify enhanced topology"
    echo "5. Run QA tests to validate normalization"
    echo "6. Show final summary"
    echo ""
    
    read -p "Press Enter to start the workflow or Ctrl+C to abort..."
    echo ""
    
    backup_data
    run_probe_parse
    run_enhanced_discovery
    verify_enhanced_topology
    run_qa_tests
    show_summary
}

# Run main function
main 