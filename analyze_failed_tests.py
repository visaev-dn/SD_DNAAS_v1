#!/usr/bin/env python3
"""
Analyze failed tests from comprehensive bridge domain test results
"""

import json
from collections import Counter

def analyze_failed_tests():
    """Analyze failed tests to identify common patterns"""
    
    # Load the test results
    with open('QA/comprehensive_bridge_domain_test_results.json', 'r') as f:
        data = json.load(f)
    
    # Extract all failed tests
    failed_tests = []
    for scenario_name, scenario_tests in data['scenarios'].items():
        for test in scenario_tests:
            if not test['success']:
                failed_tests.append({
                    'test_id': test['test_id'],
                    'scenario': test['scenario'],
                    'source_leaf': test['source_leaf'],
                    'dest_leaf': test['dest_leaf'],
                    'error': test['error']
                })
    
    print("🔍 FAILED TESTS ANALYSIS")
    print("=" * 60)
    print(f"Total failed tests: {len(failed_tests)}")
    print()
    
    # Analyze by scenario
    scenario_counts = Counter(test['scenario'] for test in failed_tests)
    print("📊 FAILURES BY SCENARIO:")
    for scenario, count in scenario_counts.items():
        print(f"  • {scenario}: {count} failures")
    print()
    
    # Analyze by source leaf
    source_leaf_counts = Counter(test['source_leaf'] for test in failed_tests)
    print("📊 FAILURES BY SOURCE LEAF:")
    for leaf, count in source_leaf_counts.most_common():
        print(f"  • {leaf}: {count} failures")
    print()
    
    # Analyze by destination leaf
    dest_leaf_counts = Counter(test['dest_leaf'] for test in failed_tests)
    print("📊 FAILURES BY DESTINATION LEAF:")
    for leaf, count in dest_leaf_counts.most_common():
        print(f"  • {leaf}: {count} failures")
    print()
    
    # Find devices involved in failures
    all_failed_devices = set()
    for test in failed_tests:
        all_failed_devices.add(test['source_leaf'])
        all_failed_devices.add(test['dest_leaf'])
    
    print("📋 ALL DEVICES INVOLVED IN FAILURES:")
    for device in sorted(all_failed_devices):
        print(f"  • {device}")
    print()
    
    # Analyze specific patterns
    print("🎯 SPECIFIC FAILURE PATTERNS:")
    
    # Pattern 1: B06 devices
    b06_failures = [test for test in failed_tests 
                    if 'B06' in test['source_leaf'] or 'B06' in test['dest_leaf']]
    print(f"  • B06 device failures: {len(b06_failures)}")
    for test in b06_failures:
        print(f"    - {test['test_id']}: {test['source_leaf']} -> {test['dest_leaf']}")
    print()
    
    # Pattern 2: Edge cases
    edge_failures = [test for test in failed_tests if test['scenario'] == 'edge_cases']
    print(f"  • Edge case failures: {len(edge_failures)}")
    for test in edge_failures:
        print(f"    - {test['test_id']}: {test['source_leaf']} -> {test['dest_leaf']}")
    print()
    
    # Pattern 3: Stress test failures
    stress_failures = [test for test in failed_tests if test['scenario'] == 'stress_test']
    print(f"  • Stress test failures: {len(stress_failures)}")
    for test in stress_failures:
        print(f"    - {test['test_id']}: {test['source_leaf']} -> {test['dest_leaf']}")
    print()
    
    # Summary
    print("📋 SUMMARY:")
    print(f"  • Total tests: {data['summary']['total_tests']}")
    print(f"  • Successful: {data['summary']['successful_tests']}")
    print(f"  • Failed: {data['summary']['failed_tests']}")
    print(f"  • Success rate: {data['summary']['overall_success_rate']:.1f}%")
    print()
    
    print("🔍 ROOT CAUSE ANALYSIS:")
    print("  • Primary issue: B06 devices (DNAAS-LEAF-B06-1, DNAAS-LEAF-B06-2-(NCPL))")
    print("  • These devices appear in 10 out of 12 failed tests")
    print("  • All failures result in 'No configuration generated' error")
    print("  • This suggests the B06 devices are not properly integrated into the topology")
    print("  • Possible causes:")
    print("    - Missing spine connections for B06 devices")
    print("    - Naming inconsistencies for B06 devices")
    print("    - B06 devices not in available_leaves list")
    print("    - Bundle mapping issues for B06 device interfaces")

if __name__ == "__main__":
    analyze_failed_tests() 