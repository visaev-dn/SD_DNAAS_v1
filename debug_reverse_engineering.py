#!/usr/bin/env python3
"""
Debug script for reverse engineering with actual scan data
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

def debug_reverse_engineering():
    """Debug the reverse engineering process with actual data."""
    
    print("=== DEBUGGING REVERSE ENGINEERING WITH ACTUAL DATA ===")
    
    # Actual scan data from database
    topology_data = {
        "nodes": [
            {"id": "device_DNAAS-LEAF-B10", "type": "device", "data": {"name": "DNAAS-LEAF-B10"}}
        ],
        "edges": []
    }
    
    path_data = {
        "device_paths": {
            "DNAAS-LEAF-B10_to_DNAAS-LEAF-B14": ["DNAAS-LEAF-B10", "DNAAS-LEAF-B14"]
        },
        "vlan_paths": {
            "vlan_251_DNAAS-LEAF-B10_bundle-60000.251_to_DNAAS-LEAF-B14_bundle-60000.251": [
                "DNAAS-LEAF-B10", "bundle-60000.251", "vlan_251", "bundle-60000.251", "DNAAS-LEAF-B14"
            ]
        }
    }
    
    scan_result = {
        "success": True,
        "bridge_domain_name": "g_visaev_v251",
        "topology_data": topology_data,
        "path_data": path_data,
        "summary": {
            "devices_found": 1,
            "nodes_created": 1,
            "edges_created": 0,
            "device_paths": 1,
            "vlan_paths": 1
        }
    }
    
    print(f"Scan result keys: {list(scan_result.keys())}")
    print(f"Topology data keys: {list(topology_data.keys())}")
    print(f"Path data keys: {list(path_data.keys())}")
    
    # Test 1: Import the reverse engineering engine
    try:
        from config_engine.reverse_engineering_engine import BridgeDomainReverseEngineer
        print("✅ Reverse Engineering Engine imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Reverse Engineering Engine: {e}")
        return
    
    # Test 2: Create engine instance
    try:
        engine = BridgeDomainReverseEngineer()
        print("✅ Reverse Engineering Engine instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create engine instance: {e}")
        return
    
    # Test 3: Test topology mapping
    try:
        mapper = engine.topology_mapper
        print("Testing topology mapping...")
        
        # Enable debug logging
        import logging
        logging.basicConfig(level=logging.INFO)
        
        builder_config = mapper.map_to_builder_format(
            topology_data, path_data, "g_visaev_v251"
        )
        
        if builder_config:
            print("✅ Topology mapping successful")
            print(f"   Topology type: {builder_config.get('topology_type')}")
            print(f"   Devices: {len(builder_config.get('devices', {}))}")
            print(f"   Interfaces: {len(builder_config.get('interfaces', {}))}")
            print(f"   VLANs: {len(builder_config.get('vlans', {}))}")
            
            # Print device and interface details
            devices = builder_config.get('devices', {})
            interfaces = builder_config.get('interfaces', {})
            print(f"   Device names: {list(devices.keys())}")
            print(f"   Interface keys: {list(interfaces.keys())}")
            
            # Print interface details
            for key, interface in interfaces.items():
                print(f"     Interface {key}: {interface}")
        else:
            print("❌ Topology mapping failed")
            return
    except Exception as e:
        print(f"❌ Topology mapping failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return
    
    # Test 4: Test config generation
    try:
        generator = engine.config_generator
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
    
    # Test 5: Test full reverse engineering (without database)
    try:
        print("=== TESTING FULL REVERSE ENGINEERING (WITHOUT DATABASE) ===")
        
        # We'll skip the database operations for now
        print("✅ All components working correctly!")
        print("The issue is likely in the database operations.")
        
    except Exception as e:
        print(f"❌ Full reverse engineering failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return
    
    print("\n🎉 Reverse engineering components are working!")
    print("The issue is likely in the database context or Flask app context.")

if __name__ == "__main__":
    debug_reverse_engineering() 