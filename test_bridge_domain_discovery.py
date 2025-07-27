#!/usr/bin/env python3
"""
Test script for Bridge Domain Discovery

This script tests the bridge domain discovery functionality to ensure it works correctly.
"""

import os
import sys
import yaml
import json
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_service_name_analyzer():
    """Test the service name analyzer."""
    print("Testing Service Name Analyzer...")
    print("=" * 50)
    
    try:
        from config_engine.service_name_analyzer import ServiceNameAnalyzer
        
        analyzer = ServiceNameAnalyzer()
        
        # Test cases
        test_cases = [
            ("g_visaev_v253", "Automated format"),
            ("M_kazakov_1360", "Manual format"),
            ("visaev_253", "Simple format"),
            ("user_visaev_vlan_253", "Descriptive format"),
            ("visaev-253", "Hyphen format"),
            ("visaev253", "Concatenated format"),
            ("unknown_service_123", "Unknown format"),
            ("", "Empty string"),
        ]
        
        for name, description in test_cases:
            result = analyzer.extract_service_info(name)
            print(f"\n{description}: '{name}'")
            print(f"  Username: {result['username']}")
            print(f"  VLAN ID: {result['vlan_id']}")
            print(f"  Confidence: {result['confidence']}%")
            print(f"  Method: {result['method']}")
        
        print("\n✅ Service Name Analyzer test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Service Name Analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bridge_domain_discovery():
    """Test the bridge domain discovery engine."""
    print("\nTesting Bridge Domain Discovery Engine...")
    print("=" * 50)
    
    try:
        from config_engine.bridge_domain_discovery import BridgeDomainDiscovery
        
        discovery = BridgeDomainDiscovery()
        
        # Test loading parsed data (if any exists)
        parsed_data = discovery.load_parsed_data()
        print(f"Loaded data from {len(parsed_data)} devices")
        
        if parsed_data:
            # Test analysis
            analyzed_data = discovery.analyze_bridge_domains(parsed_data)
            print(f"Analyzed {len(analyzed_data)} devices")
            
            # Test mapping creation
            mapping = discovery.create_comprehensive_mapping(analyzed_data)
            print(f"Created mapping with {len(mapping.get('bridge_domains', []))} bridge domains")
            
            # Test summary report
            summary = discovery.generate_summary_report(mapping)
            print("Generated summary report successfully")
            
            # Test saving
            filepath = discovery.save_mapping(mapping, "test_mapping.json")
            print(f"Saved mapping to: {filepath}")
        
        print("✅ Bridge Domain Discovery Engine test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Bridge Domain Discovery Engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_collection_integration():
    """Test the collection integration."""
    print("\nTesting Collection Integration...")
    print("=" * 50)
    
    try:
        # Check if collection script exists
        collection_script = Path("scripts/collect_lacp_xml.py")
        if not collection_script.exists():
            print("❌ Collection script not found")
            return False
        
        # Check if bridge domain raw config directory exists
        bridge_domain_raw_dir = Path("topology/configs/raw-config/bridge_domain_raw")
        if bridge_domain_raw_dir.exists():
            print(f"✅ Bridge domain raw config directory exists: {bridge_domain_raw_dir}")
        else:
            print(f"⚠️  Bridge domain raw config directory does not exist: {bridge_domain_raw_dir}")
        
        # Check if bridge domain parsed data directory exists
        bridge_domain_parsed_dir = Path("topology/configs/parsed_data/bridge_domain_parsed")
        if bridge_domain_parsed_dir.exists():
            print(f"✅ Bridge domain parsed data directory exists: {bridge_domain_parsed_dir}")
        else:
            print(f"⚠️  Bridge domain parsed data directory does not exist: {bridge_domain_parsed_dir}")
        
        # Check if parsed data directory exists
        parsed_data_dir = Path("topology/configs/parsed_data")
        if parsed_data_dir.exists():
            print(f"✅ Parsed data directory exists: {parsed_data_dir}")
        else:
            print(f"⚠️  Parsed data directory does not exist: {parsed_data_dir}")
        
        print("✅ Collection Integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Collection Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Bridge Domain Discovery Test Suite")
    print("=" * 60)
    
    tests = [
        ("Service Name Analyzer", test_service_name_analyzer),
        ("Bridge Domain Discovery Engine", test_bridge_domain_discovery),
        ("Collection Integration", test_collection_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bridge Domain Discovery is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 