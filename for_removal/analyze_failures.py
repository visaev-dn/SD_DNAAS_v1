#!/usr/bin/env python3
"""
Analyze failed cases in bridge domain test results
"""

import json
from collections import Counter, defaultdict

def analyze_failures():
    """Analyze failed cases in the comprehensive test results."""
    
    # Load the test results
    with open('QA/comprehensive_bridge_domain_test_results.json', 'r') as f:
        data = json.load(f)
    
    # Collect all failed cases
    failed_cases = []
    device_failures = Counter()
    scenario_failures = Counter()
    
    for scenario_name, scenario_results in data['scenarios'].items():
        for result in scenario_results:
            if not result.get('success', True):
                failed_cases.append(result)
                device_failures[result['source_leaf']] += 1
                device_failures[result['dest_leaf']] += 1
                scenario_failures[scenario_name] += 1
    
    print("=" * 80)
    print("🔍 FAILED CASES ANALYSIS")
    print("=" * 80)
    print(f"Total failed cases: {len(failed_cases)}")
    print(f"Total tests: {data['summary']['total_tests']}")
    print(f"Success rate: {data['summary']['overall_success_rate']:.1f}%")
    print()
    
    # Analyze by scenario
    print("📊 FAILURES BY SCENARIO:")
    for scenario, count in scenario_failures.most_common():
        total_in_scenario = len(data['scenarios'][scenario])
        print(f"  {scenario}: {count}/{total_in_scenario} ({count/total_in_scenario*100:.1f}%)")
    print()
    
    # Analyze by device
    print("📊 FAILURES BY DEVICE:")
    for device, count in device_failures.most_common():
        print(f"  {device}: {count} failures")
    print()
    
    # Analyze common patterns
    print("🔍 COMMON PATTERNS IN FAILED CASES:")
    
    # Check for specific device patterns
    problematic_devices = set()
    for device, count in device_failures.most_common():
        if count >= 2:  # Devices that failed multiple times
            problematic_devices.add(device)
    
    print(f"  Devices with multiple failures: {len(problematic_devices)}")
    for device in sorted(problematic_devices):
        print(f"    • {device}: {device_failures[device]} failures")
    print()
    
    # Check for specific error patterns
    error_patterns = Counter()
    for case in failed_cases:
        error = case.get('error', 'Unknown')
        error_patterns[error] += 1
    
    print("📋 ERROR PATTERNS:")
    for error, count in error_patterns.most_common():
        print(f"  • {error}: {count} times")
    print()
    
    # Check for specific device name patterns
    device_name_patterns = Counter()
    for case in failed_cases:
        source = case.get('source_leaf', '')
        dest = case.get('dest_leaf', '')
        device_name_patterns[source] += 1
        device_name_patterns[dest] += 1
    
    print("📋 MOST PROBLEMATIC DEVICES:")
    for device, count in device_name_patterns.most_common(10):
        print(f"  • {device}: {count} failures")
    print()
    
    # Check for naming pattern issues
    print("🔍 NAMING PATTERN ANALYSIS:")
    naming_issues = defaultdict(int)
    for case in failed_cases:
        source = case.get('source_leaf', '')
        dest = case.get('dest_leaf', '')
        
        # Check for special characters or patterns
        if 'NCPL' in source or 'NCPL' in dest:
            naming_issues['Contains NCPL'] += 1
        if ' (NCPL)' in source or ' (NCPL)' in dest:
            naming_issues['Contains (NCPL)'] += 1
        if source == dest:
            naming_issues['Same device'] += 1
    
    for pattern, count in naming_issues.items():
        print(f"  • {pattern}: {count} cases")
    print()
    
    # Detailed failed cases
    print("📋 DETAILED FAILED CASES:")
    for i, case in enumerate(failed_cases, 1):
        print(f"  {i}. {case['test_id']}: {case['source_leaf']} -> {case['dest_leaf']}")
        print(f"     Error: {case.get('error', 'Unknown')}")
        print(f"     Scenario: {case['scenario']}")
        print()

if __name__ == "__main__":
    analyze_failures() 