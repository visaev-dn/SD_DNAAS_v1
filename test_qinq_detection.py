#!/usr/bin/env python3
"""
Test QinQ Detection and RFC-Compliant VLAN Validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_engine.enhanced_discovery_integration.auto_population_service import EnhancedDatabasePopulationService
from config_engine.phase1_data_structures.enums import BridgeDomainType, TopologyType, InterfaceRole

def test_qinq_detection():
    """Test QinQ detection logic"""
    
    # Create a mock service instance
    service = EnhancedDatabasePopulationService(None)
    
    print("🧪 Testing QinQ Detection Logic")
    print("=" * 50)
    
    # Test 1: TATA double-tag service name
    service_name = "TATA_double_tag_1"
    interfaces = [
        {'vlan_id': 8101, 'device_name': 'DNAAS-LEAF-A14', 'name': 'bundle-3700.8101'},
        {'vlan_id': 8102, 'device_name': 'DNAAS-LEAF-A14', 'name': 'bundle-3700.8102'},
        {'vlan_id': 1001, 'device_name': 'DNAAS-LEAF-A14', 'name': 'bundle-3971.1001'}
    ]
    
    print(f"Test 1: {service_name}")
    print(f"Interfaces: {interfaces}")
    
    # Test bridge domain type detection
    bd_type = service.detect_bridge_domain_type(service_name, interfaces)
    print(f"Bridge Domain Type: {bd_type}")
    
    # Test VLAN configuration extraction
    vlan_config = service.extract_vlan_configuration(interfaces, bd_type)
    print(f"VLAN Config: {vlan_config}")
    
    # Test QinQ topology detection
    topology_type = service.detect_qinq_topology(interfaces)
    print(f"Topology Type: {topology_type}")
    
    # Test interface role assignment
    enhanced_interfaces = service.assign_qinq_interface_roles(interfaces, bd_type)
    print(f"Enhanced Interfaces: {enhanced_interfaces}")
    
    print()
    
    # Test 2: Invalid VLAN (above 4094)
    service_name2 = "TATA_invalid_vlan"
    interfaces2 = [
        {'vlan_id': 5000, 'device_name': 'DNAAS-LEAF-A14', 'name': 'bundle-3700.5000'},
        {'vlan_id': 1001, 'device_name': 'DNAAS-LEAF-A14', 'name': 'bundle-3971.1001'}
    ]
    
    print(f"Test 2: {service_name2}")
    print(f"Interfaces: {interfaces2}")
    
    # Test VLAN validation
    valid_vlans = service.extract_valid_vlans(interfaces2)
    print(f"Valid VLANs: {valid_vlans}")
    
    # Test bridge domain type detection
    bd_type2 = service.detect_bridge_domain_type(service_name2, interfaces2)
    print(f"Bridge Domain Type: {bd_type2}")
    
    # Test VLAN configuration extraction
    vlan_config2 = service.extract_vlan_configuration(interfaces2, bd_type2)
    print(f"VLAN Config: {vlan_config2}")
    
    print()
    
    # Test 3: Single VLAN service
    service_name3 = "simple_vlan_service"
    interfaces3 = [
        {'vlan_id': 100, 'device_name': 'DNAAS-LEAF-A15', 'name': 'ge100-0/0/1'}
    ]
    
    print(f"Test 3: {service_name3}")
    print(f"Interfaces: {interfaces3}")
    
    # Test bridge domain type detection
    bd_type3 = service.detect_bridge_domain_type(service_name3, interfaces3)
    print(f"Bridge Domain Type: {bd_type3}")
    
    # Test VLAN configuration extraction
    vlan_config3 = service.extract_vlan_configuration(interfaces3, bd_type3)
    print(f"VLAN Config: {vlan_config3}")
    
    print()
    print("✅ QinQ Detection Tests Completed!")

if __name__ == "__main__":
    test_qinq_detection()
