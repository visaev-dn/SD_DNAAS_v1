#!/usr/bin/env python3
"""
Test script for Phase 1 data structure implementation
"""

import sys
from pathlib import Path

# Add config_engine to path
sys.path.append(str(Path(__file__).parent / "config_engine"))

def test_phase1_implementation():
    """Test the Phase 1 data structure implementation"""
    print("🧪 Testing Phase 1 Data Structure Implementation")
    print("=" * 60)
    
    try:
        # Test 1: Import all classes
        print("\n📦 Test 1: Importing Phase 1 classes...")
        from phase1_data_structures import (
            TopologyData, DeviceInfo, InterfaceInfo, PathInfo, PathSegment,
            BridgeDomainConfig, TopologyValidator, TopologyType, DeviceType,
            InterfaceType, InterfaceRole, DeviceRole, ValidationStatus,
            BridgeDomainType, OuterTagImposition
        )
        print("✅ All classes imported successfully")
        
        # Test 2: Create simple P2P topology
        print("\n🔗 Test 2: Creating P2P topology...")
        from phase1_data_structures import create_p2p_topology
        
        p2p_topology = create_p2p_topology(
            bridge_domain_name="test_p2p_v100",
            vlan_id=100,
            source_device="DNAAS-LEAF-A01",
            source_interface="ge100-0/0/1",
            dest_device="DNAAS-LEAF-A02",
            dest_interface="ge100-0/0/2"
        )
        print(f"✅ P2P topology created: {p2p_topology.topology_summary}")
        
        # Test 3: Create P2MP topology
        print("\n🌐 Test 3: Creating P2MP topology...")
        from phase1_data_structures import create_p2mp_topology
        
        destinations = [
            {'device': 'DNAAS-LEAF-B01', 'port': 'ge100-0/0/3'},
            {'device': 'DNAAS-LEAF-B02', 'port': 'ge100-0/0/4'},
            {'device': 'DNAAS-LEAF-B03', 'port': 'ge100-0/0/5'}
        ]
        
        p2mp_topology = create_p2mp_topology(
            bridge_domain_name="test_p2mp_v200",
            vlan_id=200,
            source_device="DNAAS-LEAF-A01",
            source_interface="ge100-0/0/1",
            destinations=destinations
        )
        print(f"✅ P2MP topology created: {p2mp_topology.topology_summary}")
        
        # Test 4: Validation
        print("\n✅ Test 4: Testing validation...")
        validator = TopologyValidator()
        
        # Validate P2P topology
        p2p_passed, p2p_errors, p2p_warnings = validator.validate_topology(p2p_topology)
        print(f"P2P validation: {'PASSED' if p2p_passed else 'FAILED'}")
        if p2p_errors:
            print(f"  Errors: {p2p_errors}")
        if p2p_warnings:
            print(f"  Warnings: {p2p_warnings}")
        
        # Validate P2MP topology
        p2mp_passed, p2mp_errors, p2mp_warnings = validator.validate_topology(p2mp_topology)
        print(f"P2MP validation: {'PASSED' if p2mp_passed else 'FAILED'}")
        if p2mp_errors:
            print(f"  Errors: {p2mp_errors}")
        if p2mp_warnings:
            print(f"  Warnings: {p2mp_warnings}")
        
        # Test 5: Serialization
        print("\n💾 Test 5: Testing serialization...")
        
        # Convert to dict
        p2p_dict = p2p_topology.to_dict()
        p2mp_dict = p2mp_topology.to_dict()
        print("✅ Topology data converted to dictionaries")
        
        # Convert back from dict
        p2p_reconstructed = TopologyData.from_dict(p2p_dict)
        p2mp_reconstructed = TopologyData.from_dict(p2mp_dict)
        print("✅ Topology data reconstructed from dictionaries")
        
        # Test 6: Properties and methods
        print("\n🔧 Test 6: Testing properties and methods...")
        
        print(f"P2P topology properties:")
        print(f"  - Is P2P: {p2p_topology.is_p2p}")
        print(f"  - Is P2MP: {p2p_topology.is_p2mp}")
        print(f"  - Device count: {p2p_topology.device_count}")
        print(f"  - Interface count: {p2p_topology.interface_count}")
        print(f"  - Path count: {p2p_topology.path_count}")
        print(f"  - Leaf devices: {len(p2p_topology.leaf_devices)}")
        print(f"  - Source devices: {len(p2p_topology.source_devices)}")
        print(f"  - Destination devices: {len(p2p_topology.destination_devices)}")
        
        print(f"\nP2MP topology properties:")
        print(f"  - Is P2P: {p2mp_topology.is_p2p}")
        print(f"  - Is P2MP: {p2mp_topology.is_p2mp}")
        print(f"  - Device count: {p2mp_topology.device_count}")
        print(f"  - Interface count: {p2mp_topology.interface_count}")
        print(f"  - Path count: {p2mp_topology.path_count}")
        print(f"  - Leaf devices: {len(p2mp_topology.leaf_devices)}")
        print(f"  - Source devices: {len(p2mp_topology.source_devices)}")
        print(f"  - Destination devices: {len(p2mp_topology.destination_devices)}")
        
        # Test 7: Bridge domain configuration
        print("\n🏗️ Test 7: Testing bridge domain configuration...")
        
        bd_config = p2p_topology.bridge_domain_config
        print(f"Bridge domain config:")
        print(f"  - Service name: {bd_config.service_name}")
        print(f"  - Bridge domain type: {bd_config.bridge_domain_type.value}")
        print(f"  - VLAN ID: {bd_config.vlan_id}")
        print(f"  - Is P2P: {bd_config.is_p2p}")
        print(f"  - Is P2MP: {bd_config.is_p2mp}")
        print(f"  - Destination count: {bd_config.destination_count}")
        print(f"  - VLAN count: {bd_config.vlan_count}")
        print(f"  - VLAN summary: {bd_config.vlan_summary}")
        print(f"  - Topology summary: {bd_config.topology_summary}")
        print(f"  - Configuration summary: {bd_config.configuration_summary}")
        
        # Test 8: Enum functionality
        print("\n🔢 Test 8: Testing enum functionality...")
        
        from phase1_data_structures import (
            get_enum_values, get_enum_names, validate_enum_value, get_enum_by_value
        )
        
        print(f"TopologyType values: {get_enum_values(TopologyType)}")
        print(f"DeviceType names: {get_enum_names(DeviceType)}")
        print(f"Is 'p2p' valid TopologyType? {validate_enum_value(TopologyType, 'p2p')}")
        print(f"Is 'invalid' valid TopologyType? {validate_enum_value(TopologyType, 'invalid')}")
        
        p2p_enum = get_enum_by_value(TopologyType, 'p2p')
        print(f"TopologyType enum for 'p2p': {p2p_enum}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase1_implementation()
    sys.exit(0 if success else 1)

