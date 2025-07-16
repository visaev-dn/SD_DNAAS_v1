#!/usr/bin/env python3
"""
Fixed test script for bridge domain builder using devices with actual bundles
"""

from config_engine.bridge_domain_builder import BridgeDomainBuilder

def test_bridge_domain_with_valid_bundles():
    """Test the bridge domain builder with devices that have actual bundles"""
    print("=== Testing Bridge Domain Builder with Valid Bundles ===")
    
    # Initialize the builder
    builder = BridgeDomainBuilder()
    
    if not builder.topology_data:
        print("❌ No topology data available. Please run topology discovery first.")
        return False
    
    print("✅ Topology data loaded successfully")
    
    # Test cases using devices with actual bundles
    test_cases = [
        {
            'source_leaf': 'DNAAS-LEAF-A02',
            'dest_leaf': 'DNAAS-LEAF-A03', 
            'source_port': 'ge100-0/0/11',  # bundle-1002
            'dest_port': 'ge100-0/0/4',     # bundle-100
            'description': 'Leaf devices with valid bundles through DNAAS-SPINE-A09'
        },
        {
            'source_leaf': 'DNAAS-LEAF-A12',
            'dest_leaf': 'DNAAS-LEAF-A14',
            'source_port': 'ge100-0/0/14',  # bundle-1000
            'dest_port': 'ge100-0/0/4',     # bundle-171
            'description': 'Leaf devices with valid bundles through DNAAS-SPINE-A09'
        },
        {
            'source_leaf': 'DNAAS-LEAF-C11',
            'dest_leaf': 'DNAAS-LEAF-A16',
            'source_port': 'ge100-0/0/34',  # bundle-1
            'dest_port': 'ge100-0/0/36',    # bundle-60000
            'description': 'Remote leaf devices through different spines'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        print(f"Source: {test_case['source_leaf']} ({test_case['source_port']})")
        print(f"Destination: {test_case['dest_leaf']} ({test_case['dest_port']})")
        
        # Calculate path
        path = builder.calculate_path(test_case['source_leaf'], test_case['dest_leaf'])
        
        if path:
            print("✅ Path calculated successfully!")
            print(f"Path: {path['source_leaf']} → {path['source_spine']} → {path['superspine']} → {path['dest_spine']} → {path['destination_leaf']}")
            
            print("Path segments:")
            for segment in path['segments']:
                print(f"  {segment['type']}: {segment['source_device']}:{segment['source_interface']} → {segment['dest_device']}:{segment['dest_interface']}")
            
            # Test bridge domain configuration
            configs = builder.build_bridge_domain_config(
                service_name="test_service",
                vlan_id=1000,
                source_leaf=test_case['source_leaf'],
                source_port=test_case['source_port'],
                dest_leaf=test_case['dest_leaf'],
                dest_port=test_case['dest_port']
            )
            
            if configs:
                print(f"✅ Bridge domain configuration generated for {len(configs)} devices:")
                for device, config in configs.items():
                    print(f"  📋 {device}: {len(config)} configuration lines")
                    if config:  # Show first few lines if config exists
                        print("    Sample config:")
                        for line in config[:3]:
                            print(f"      {line}")
                        if len(config) > 3:
                            print(f"      ... and {len(config)-3} more lines")
            else:
                print("❌ Failed to generate bridge domain configuration")
        else:
            print("❌ Failed to calculate path")
    
    print("\n=== Bridge Domain Builder Test Complete ===")
    return True

if __name__ == "__main__":
    test_bridge_domain_with_valid_bundles() 