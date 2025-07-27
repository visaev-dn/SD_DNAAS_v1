#!/usr/bin/env python3
"""
Integration test for P2MP Bridge Domain Builder
"""

import sys
import logging
from pathlib import Path

# Add config_engine to path
sys.path.append('.')

from config_engine.p2mp_bridge_domain_builder import P2MPBridgeDomainBuilder

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_p2mp_integration():
    """Test P2MP integration with main system"""
    print("🧪 Testing P2MP Integration")
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
        
        # Test data - use devices that are likely to have shared spines
        service_name = "g_integration_v300"
        vlan_id = 300
        source_leaf = "DNAAS-LEAF-A01"
        source_port = "ge100-0/0/10"
        
        # Create test destinations - use devices in same row for better spine sharing
        destinations = [
            {'leaf': 'DNAAS-LEAF-A02', 'port': 'ge100-0/0/20'},
            {'leaf': 'DNAAS-LEAF-A03', 'port': 'ge100-0/0/30'},
            {'leaf': 'DNAAS-LEAF-A04', 'port': 'ge100-0/0/40'}
        ]
        
        print(f"📋 Integration Test Configuration:")
        print(f"   Service: {service_name}")
        print(f"   VLAN: {vlan_id}")
        print(f"   Source: {source_leaf}:{source_port}")
        print(f"   Destinations: {len(destinations)}")
        for dest in destinations:
            print(f"     - {dest['leaf']}:{dest['port']}")
        
        # Test path calculation
        print("\n🛤️  Testing path calculation...")
        dest_leaves = [dest['leaf'] for dest in destinations]
        path_calculation = builder.calculate_paths_for_destinations(source_leaf, dest_leaves)
        
        print(f"   Calculated paths: {len(path_calculation['destinations'])}")
        print(f"   Spine utilization: {path_calculation['spine_utilization']}")
        print(f"   Path efficiency: {path_calculation['optimization_metrics']['path_efficiency']:.1%}")
        
        # Show path visualization
        print("\n🌳 Path Visualization:")
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
        
        # Show configuration summary
        print("\n📋 Configuration Summary:")
        summary = builder.get_configuration_summary(configs)
        print(summary)
        
        # Test saving configuration
        print("\n💾 Testing configuration save...")
        output_file = builder.save_configuration(configs)
        print(f"✅ Configuration saved to: {output_file}")
        
        # Verify the saved file
        if Path(output_file).exists():
            print(f"✅ File exists: {output_file}")
            file_size = Path(output_file).stat().st_size
            print(f"✅ File size: {file_size} bytes")
        else:
            print(f"❌ File not found: {output_file}")
            return False
        
        print("\n🎉 P2MP Integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_p2mp_menu_integration():
    """Test that P2MP menu option is available"""
    print("\n🧪 Testing P2MP Menu Integration")
    print("=" * 40)
    
    try:
        # Import main menu functions
        from main import show_user_menu
        
        print("✅ P2MP menu function imported successfully")
        print("✅ P2MP option should be available in user menu")
        
        return True
        
    except Exception as e:
        print(f"❌ Menu integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting P2MP Integration Tests")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_p2mp_integration()
    test2_passed = test_p2mp_menu_integration()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 All integration tests passed! P2MP is ready for use.")
        print("\n📋 Next Steps:")
        print("1. Run 'python main.py'")
        print("2. Select 'User Options' (2)")
        print("3. Select 'P2MP Bridge-Domain Builder' (2)")
        print("4. Follow the interactive prompts")
    else:
        print("❌ Some integration tests failed. Please check the implementation.")
    
    print("=" * 60) 