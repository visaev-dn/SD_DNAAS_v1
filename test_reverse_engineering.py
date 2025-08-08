#!/usr/bin/env python3
"""
Test script for reverse engineering functionality
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def test_reverse_engineering():
    """Test the reverse engineering process step by step."""
    
    print("=== TESTING REVERSE ENGINEERING PROCESS ===")
    
    # Test 1: Import the reverse engineering engine
    try:
        from config_engine.reverse_engineering_engine import BridgeDomainReverseEngineer
        print("✅ Reverse Engineering Engine imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Reverse Engineering Engine: {e}")
        return
    
    # Test 2: Import topology mapper
    try:
        from config_engine.topology_mapper import TopologyMapper
        print("✅ Topology Mapper imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Topology Mapper: {e}")
        return
    
    # Test 3: Import config generator
    try:
        from config_engine.config_generator import ReverseEngineeredConfigGenerator
        print("✅ Config Generator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Config Generator: {e}")
        return
    
    # Test 4: Create engine instance
    try:
        engine = BridgeDomainReverseEngineer()
        print("✅ Reverse Engineering Engine instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create engine instance: {e}")
        return
    
    # Test 5: Create test scan result
    test_scan_result = {
        "success": True,
        "bridge_domain_name": "test_bridge_domain",
        "topology_data": {
            "nodes": [
                {
                    "id": "device_DNAAS-LEAF-B10",
                    "type": "device",
                    "data": {
                        "name": "DNAAS-LEAF-B10",
                        "device_type": "leaf",
                        "status": "active"
                    }
                },
                {
                    "id": "device_DNAAS-LEAF-B14",
                    "type": "device",
                    "data": {
                        "name": "DNAAS-LEAF-B14",
                        "device_type": "leaf",
                        "status": "active"
                    }
                },
                {
                    "id": "interface_DNAAS-LEAF-B10_bundle-60000.251",
                    "type": "interface",
                    "data": {
                        "name": "bundle-60000.251",
                        "device_name": "DNAAS-LEAF-B10",
                        "interface_type": "bundle",
                        "vlan_id": 251,
                        "status": "active"
                    }
                },
                {
                    "id": "interface_DNAAS-LEAF-B14_bundle-60000.251",
                    "type": "interface",
                    "data": {
                        "name": "bundle-60000.251",
                        "device_name": "DNAAS-LEAF-B14",
                        "interface_type": "bundle",
                        "vlan_id": 251,
                        "status": "active"
                    }
                }
            ],
            "edges": [
                {
                    "source": "device_DNAAS-LEAF-B10",
                    "target": "interface_DNAAS-LEAF-B10_bundle-60000.251"
                },
                {
                    "source": "device_DNAAS-LEAF-B14",
                    "target": "interface_DNAAS-LEAF-B14_bundle-60000.251"
                }
            ]
        },
        "path_data": {
            "device_paths": {
                "DNAAS-LEAF-B10_to_DNAAS-LEAF-B14": ["DNAAS-LEAF-B10", "DNAAS-LEAF-B14"]
            },
            "vlan_paths": {
                "vlan_251_DNAAS-LEAF-B10_bundle-60000.251_to_DNAAS-LEAF-B14_bundle-60000.251": [
                    "DNAAS-LEAF-B10", "bundle-60000.251", "vlan_251", "bundle-60000.251", "DNAAS-LEAF-B14"
                ]
            }
        }
    }
    
    print("✅ Test scan result created successfully")
    print(f"   Bridge domain: {test_scan_result['bridge_domain_name']}")
    print(f"   Nodes: {len(test_scan_result['topology_data']['nodes'])}")
    print(f"   Edges: {len(test_scan_result['topology_data']['edges'])}")
    print(f"   Device paths: {len(test_scan_result['path_data']['device_paths'])}")
    print(f"   VLAN paths: {len(test_scan_result['path_data']['vlan_paths'])}")
    
    # Test 6: Test topology mapping
    try:
        mapper = TopologyMapper()
        builder_config = mapper.map_to_builder_format(
            test_scan_result['topology_data'],
            test_scan_result['path_data'],
            test_scan_result['bridge_domain_name']
        )
        
        if builder_config:
            print("✅ Topology mapping successful")
            print(f"   Topology type: {builder_config.get('topology_type')}")
            print(f"   Devices: {len(builder_config.get('devices', {}))}")
            print(f"   Interfaces: {len(builder_config.get('interfaces', {}))}")
            print(f"   VLANs: {len(builder_config.get('vlans', {}))}")
        else:
            print("❌ Topology mapping failed")
            return
    except Exception as e:
        print(f"❌ Topology mapping failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return
    
    # Test 7: Test config generation
    try:
        generator = ReverseEngineeredConfigGenerator()
        config_data, metadata = generator.generate_configuration(builder_config, user_id=1)
        
        if config_data and metadata:
            print("✅ Configuration generation successful")
            print(f"   Config data keys: {list(config_data.keys())}")
            print(f"   Metadata keys: {list(metadata.keys())}")
        else:
            print("❌ Configuration generation failed")
            return
    except Exception as e:
        print(f"❌ Configuration generation failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return
    
    print("\n🎉 All reverse engineering components working correctly!")
    print("The reverse engineering system is ready for integration.")

if __name__ == "__main__":
    test_reverse_engineering() 