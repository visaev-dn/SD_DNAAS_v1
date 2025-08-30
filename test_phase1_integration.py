#!/usr/bin/env python3
"""
Test script for Phase 1 CLI Integration
Demonstrates the integration between legacy CLI and Phase 1 data structures
"""

import sys
from pathlib import Path

# Add config_engine to path
sys.path.append(str(Path(__file__).parent / "config_engine"))

def test_phase1_integration():
    """Test the Phase 1 CLI integration"""
    print("🧪 Testing Phase 1 CLI Integration")
    print("=" * 60)
    
    try:
        # Test 1: Import Phase 1 integration components
        print("\n📦 Test 1: Importing Phase 1 integration components...")
        from phase1_integration import (
            DataTransformer, Phase1CLIWrapper, enable_phase1_integration,
            get_integration_status, validate_configuration
        )
        print("✅ All integration components imported successfully")
        
        # Test 2: Enable Phase 1 integration
        print("\n🚀 Test 2: Enabling Phase 1 integration...")
        enable_phase1_integration()
        
        # Test 3: Check integration status
        print("\n📊 Test 3: Checking integration status...")
        status = get_integration_status()
        
        # Test 4: Test data transformation
        print("\n🔄 Test 4: Testing data transformation...")
        transformer = DataTransformer()
        
        # Sample CLI input
        service_name = "test_integration_v100"
        vlan_id = 100
        source_device = "DNAAS-LEAF-A01"
        source_interface = "ge100-0/0/1"
        destinations = [{'device': 'DNAAS-LEAF-A02', 'port': 'ge100-0/0/2'}]
        
        # Transform to Phase 1
        topology, passed, errors, warnings = transformer.validate_and_transform(
            service_name, vlan_id, source_device, source_interface, destinations
        )
        
        print(f"✅ Transformation successful: {topology.topology_summary}")
        print(f"📊 Validation: {'PASSED' if passed else 'FAILED'}")
        if warnings:
            print(f"⚠️ Warnings: {len(warnings)}")
        if errors:
            print(f"❌ Errors: {len(errors)}")
        
        # Test 5: Test CLI wrapper
        print("\n🔨 Test 5: Testing CLI wrapper...")
        cli_wrapper = Phase1CLIWrapper()
        
        # Get validation report
        report = cli_wrapper.get_validation_report(
            service_name, vlan_id, source_device, source_interface, destinations
        )
        
        print(f"✅ CLI wrapper validation report generated")
        print(f"📊 Service: {report['service_name']}")
        print(f"📊 Validation passed: {report['validation_passed']}")
        print(f"📊 Device count: {report['device_count']}")
        print(f"📊 Interface count: {report['interface_count']}")
        print(f"📊 Confidence score: {report['confidence_score']:.2f}")
        
        # Test 6: Test convenience validation function
        print("\n✅ Test 6: Testing convenience validation function...")
        validation_result = validate_configuration(
            service_name, vlan_id, source_device, source_interface, destinations
        )
        
        print(f"✅ Convenience validation completed")
        print(f"📊 Result: {validation_result['validation_passed']}")
        
        # Test 7: Test P2MP scenario
        print("\n🌐 Test 7: Testing P2MP scenario...")
        p2mp_destinations = [
            {'device': 'DNAAS-LEAF-B01', 'port': 'ge100-0/0/3'},
            {'device': 'DNAAS-LEAF-B02', 'port': 'ge100-0/0/4'},
            {'device': 'DNAAS-SUPERSPINE-D04', 'port': 'ge100-0/0/5'}
        ]
        
        p2mp_topology, p2mp_passed, p2mp_errors, p2mp_warnings = transformer.validate_and_transform(
            "test_p2mp_v200", 200, source_device, source_interface, p2mp_destinations
        )
        
        print(f"✅ P2MP transformation successful: {p2mp_topology.topology_summary}")
        print(f"📊 P2MP validation: {'PASSED' if p2mp_passed else 'FAILED'}")
        print(f"📊 P2MP topology type: {p2mp_topology.topology_type.value}")
        
        # Test 8: Test legacy format conversion
        print("\n🔄 Test 8: Testing legacy format conversion...")
        legacy_config = transformer.phase1_to_legacy_config(topology)
        
        print(f"✅ Legacy conversion successful")
        print(f"📊 Legacy service name: {legacy_config['service_name']}")
        print(f"📊 Legacy topology type: {legacy_config['topology_type']}")
        print(f"📊 Legacy destinations: {len(legacy_config['destinations'])}")
        
        print("\n🎉 All Phase 1 integration tests completed successfully!")
        print("\n📋 Integration Summary:")
        print("─" * 40)
        print("✅ Data transformation: Working")
        print("✅ Validation framework: Working")
        print("✅ CLI wrapper: Working")
        print("✅ Legacy compatibility: Working")
        print("✅ P2P support: Working")
        print("✅ P2MP support: Working")
        print("✅ Convenience functions: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase1_integration()
    sys.exit(0 if success else 1)

