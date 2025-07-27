#!/usr/bin/env python3
"""
Test script for P2MP Bridge Domain Builder
"""

import sys
import logging
from pathlib import Path

# Add config_engine to path
sys.path.append('.')

from config_engine.p2mp_bridge_domain_builder import P2MPBridgeDomainBuilder

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_p2mp_bridge_domain():
    """Test P2MP bridge domain builder"""
    print("🧪 Testing P2MP Bridge Domain Builder")
    print("=" * 50)
    
    # Check if topology files exist
    topology_file = Path("topology/complete_topology_v2.json")
    if not topology_file.exists():
        print("❌ Topology file not found. Please run topology discovery first.")
        return False
    
    try:
        # Initialize P2MP builder
        print("🔧 Initializing P2MP Bridge Domain Builder...")
        builder = P2MPBridgeDomainBuilder()
        
        # Get available leaves
        available_leaves = builder.get_available_leaves()
        print(f"✅ Found {len(available_leaves)} available leaf devices")
        
        if len(available_leaves) < 3:
            print("❌ Need at least 3 leaf devices for P2MP testing")
            return False
        
        # Test data
        service_name = "g_test_v100"
        vlan_id = 100
        source_leaf = available_leaves[0]  # Use first available leaf as source
        source_port = "ge100-0/0/10"
        
        # Create test destinations (use next 3 available leaves)
        destinations = []
        for i, leaf in enumerate(available_leaves[1:4]):  # Use next 3 leaves
            destinations.append({
                'leaf': leaf,
                'port': f"ge100-0/0/{20 + i}"  # Ports 20, 21, 22
            })
        
        print(f"📋 Test Configuration:")
        print(f"   Service: {service_name}")
        print(f"   VLAN: {vlan_id}")
        print(f"   Source: {source_leaf}:{source_port}")
        print(f"   Destinations: {len(destinations)}")
        for dest in destinations:
            print(f"     - {dest['leaf']}:{dest['port']}")
        
        # Test source analysis
        print("\n🔍 Testing source analysis...")
        source_analysis = builder.analyze_source_capabilities(source_leaf)
        print(f"   Connected spines: {source_analysis['connected_spines']}")
        print(f"   Available paths: {len(source_analysis['available_paths'])}")
        
        # Test path calculation
        print("\n🛤️  Testing path calculation...")
        dest_leaves = [dest['leaf'] for dest in destinations]
        path_calculation = builder.calculate_paths_for_destinations(source_leaf, dest_leaves)
        
        print(f"   Calculated paths: {len(path_calculation['destinations'])}")
        print(f"   Spine utilization: {path_calculation['spine_utilization']}")
        print(f"   Path efficiency: {path_calculation['optimization_metrics']['path_efficiency']:.1%}")
        
        # Test path visualization
        print("\n🌳 Testing path visualization...")
        visualization = builder.visualize_p2mp_paths(path_calculation)
        print(visualization)
        
        # Test configuration generation
        print("\n⚙️  Testing configuration generation...")
        configs = builder.build_p2mp_bridge_domain_config(
            service_name, vlan_id, source_leaf, source_port, destinations
        )
        
        if not configs:
            print("❌ Failed to generate configuration")
            return False
        
        print(f"✅ Generated configuration for {len(configs)-1} devices")  # -1 for metadata
        
        # Test configuration summary
        print("\n📋 Configuration Summary:")
        summary = builder.get_configuration_summary(configs)
        print(summary)
        
        # Test saving configuration
        print("\n💾 Testing configuration save...")
        output_file = builder.save_configuration(configs)
        print(f"✅ Configuration saved to: {output_file}")
        
        print("\n🎉 All P2MP tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_p2mp_with_custom_data():
    """Test P2MP with custom test data"""
    print("\n🧪 Testing P2MP with custom data")
    print("=" * 40)
    
    try:
        # Initialize builder
        builder = P2MPBridgeDomainBuilder()
        
        # Custom test data
        service_name = "g_custom_v200"
        vlan_id = 200
        source_leaf = "DNAAS-LEAF-A01"
        source_port = "ge100-0/0/15"
        
        destinations = [
            {'leaf': 'DNAAS-LEAF-A02', 'port': 'ge100-0/0/25'},
            {'leaf': 'DNAAS-LEAF-B01', 'port': 'ge100-0/0/35'},
            {'leaf': 'DNAAS-LEAF-B02', 'port': 'ge100-0/0/45'},
            {'leaf': 'DNAAS-LEAF-C01', 'port': 'ge100-0/0/55'}
        ]
        
        print(f"📋 Custom Test Configuration:")
        print(f"   Service: {service_name}")
        print(f"   VLAN: {vlan_id}")
        print(f"   Source: {source_leaf}:{source_port}")
        print(f"   Destinations: {len(destinations)}")
        
        # Test path calculation
        dest_leaves = [dest['leaf'] for dest in destinations]
        path_calculation = builder.calculate_paths_for_destinations(source_leaf, dest_leaves)
        
        print(f"\n🛤️  Path Calculation Results:")
        print(f"   Successful paths: {len(path_calculation['destinations'])}")
        print(f"   Failed destinations: {path_calculation['optimization_metrics']['failed_destinations']}")
        
        # Show visualization
        visualization = builder.visualize_p2mp_paths(path_calculation)
        print(f"\n🌳 Path Visualization:")
        print(visualization)
        
        # Generate configuration
        configs = builder.build_p2mp_bridge_domain_config(
            service_name, vlan_id, source_leaf, source_port, destinations
        )
        
        if configs:
            print(f"\n✅ Generated configuration for {len(configs)-1} devices")
            
            # Show summary
            summary = builder.get_configuration_summary(configs)
            print(f"\n📋 Summary:")
            print(summary)
            
            # Save configuration
            output_file = builder.save_configuration(configs)
            print(f"\n💾 Saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Custom test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting P2MP Bridge Domain Tests")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_p2mp_bridge_domain()
    test2_passed = test_p2mp_with_custom_data()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 All tests passed! P2MP Bridge Domain Builder is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    print("=" * 60) 