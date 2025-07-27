#!/usr/bin/env python3
"""
Test script to demonstrate P2MP UI flow with consistent row/number selection
"""

import sys
import logging
from pathlib import Path

# Add config_engine to path
sys.path.append('.')

from config_engine.p2mp_bridge_domain_builder import P2MPBridgeDomainBuilder

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def demonstrate_p2mp_ui_flow():
    """Demonstrate the P2MP UI flow with consistent interface"""
    print("🎯 Demonstrating P2MP UI Flow")
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
        
        # Simulate the UI flow
        print("\n📋 Simulating P2MP Bridge Domain Configuration")
        print("─" * 50)
        
        # Service configuration
        service_name = "g_demo_v400"
        vlan_id = 400
        source_leaf = "DNAAS-LEAF-A01"
        source_port = "ge100-0/0/10"
        
        print(f"Service Name: {service_name}")
        print(f"VLAN ID: {vlan_id}")
        print(f"Source: {source_leaf}:{source_port}")
        
        # Simulate destination selection using row/number interface
        print(f"\n🌐 P2MP Destination Selection")
        print("─" * 40)
        print("Select destinations for P2MP bridge domain:")
        
        # Simulate destinations that would be selected via row/number interface
        destinations = [
            {'leaf': 'DNAAS-LEAF-A02', 'port': 'ge100-0/0/20'},
            {'leaf': 'DNAAS-LEAF-A03', 'port': 'ge100-0/0/30'},
            {'leaf': 'DNAAS-LEAF-B01', 'port': 'ge100-0/0/40'}
        ]
        
        print(f"\nSimulated destination selection flow:")
        for i, dest in enumerate(destinations, 1):
            print(f"   {i}. Selected Row A, Rack {dest['leaf'].split('-')[-1]} -> {dest['leaf']}:{dest['port']}")
            print(f"      (User would select row and rack number, then enter port)")
        
        print(f"\n✅ Selected {len(destinations)} destinations:")
        for dest in destinations:
            print(f"   • {dest['leaf']}:{dest['port']}")
        
        # Optimization strategy
        optimization_strategy = "shared_spine"
        print(f"\n🔧 Path Optimization Strategy: {optimization_strategy}")
        
        # Calculate paths
        print(f"\n🛤️  Calculating paths...")
        dest_leaves = [dest['leaf'] for dest in destinations]
        path_calculation = builder.calculate_paths_for_destinations(source_leaf, dest_leaves)
        
        print(f"   Calculated paths: {len(path_calculation['destinations'])}")
        print(f"   Spine utilization: {path_calculation['spine_utilization']}")
        print(f"   Path efficiency: {path_calculation['optimization_metrics']['path_efficiency']:.1%}")
        
        # Show path visualization
        print(f"\n🌳 Path Visualization:")
        visualization = builder.visualize_p2mp_paths(path_calculation)
        print(visualization)
        
        # Generate configuration
        print(f"\n⚙️  Generating configuration...")
        configs = builder.build_p2mp_bridge_domain_config(
            service_name, vlan_id, source_leaf, source_port, destinations, optimization_strategy
        )
        
        if not configs:
            print("❌ Failed to generate configuration")
            return False
        
        print(f"✅ Generated configuration for {len(configs)-1} devices")
        
        # Show configuration summary
        print(f"\n📋 Configuration Summary:")
        summary = builder.get_configuration_summary(configs)
        print(summary)
        
        # Save configuration
        output_file = builder.save_configuration(configs)
        print(f"\n💾 Configuration saved to: {output_file}")
        
        print(f"\n🎉 P2MP UI flow demonstration completed!")
        return True
        
    except Exception as e:
        print(f"❌ UI flow demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_ui_comparison():
    """Show comparison between P2P and P2MP UI flows"""
    print("\n📊 UI Flow Comparison")
    print("=" * 40)
    
    print("🔨 P2P Bridge Domain Builder:")
    print("   1. Select source row and rack")
    print("   2. Enter source port")
    print("   3. Select destination row and rack")
    print("   4. Enter destination port")
    print("   5. Build configuration")
    
    print("\n🌐 P2MP Bridge Domain Builder:")
    print("   1. Select source row and rack")
    print("   2. Enter source port")
    print("   3. Select destination 1 row and rack")
    print("   4. Enter destination 1 port")
    print("   5. 'Add another destination? (y/n)'")
    print("   6. If yes, repeat steps 3-5")
    print("   7. If no, build configuration")
    
    print("\n✅ Both use the same row/rack selection interface!")
    print("✅ Consistent user experience across P2P and P2MP!")

if __name__ == "__main__":
    print("🚀 P2MP UI Flow Demonstration")
    print("=" * 60)
    
    # Run demonstration
    demo_passed = demonstrate_p2mp_ui_flow()
    
    # Show UI comparison
    show_ui_comparison()
    
    print("\n" + "=" * 60)
    if demo_passed:
        print("🎉 P2MP UI flow demonstration completed successfully!")
        print("\n📋 Key Benefits:")
        print("• Consistent interface between P2P and P2MP")
        print("• Familiar row/rack selection for users")
        print("• Simple y/n prompts for adding destinations")
        print("• No complex menu changes required")
    else:
        print("❌ UI flow demonstration failed.")
    
    print("=" * 60) 