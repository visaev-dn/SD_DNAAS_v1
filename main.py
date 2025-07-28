#!/usr/bin/env python3
"""
Lab Automation Framework - Main Entry Point
Provides unified interface for all lab automation tools
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

def show_main_menu():
    """Main menu for lab automation framework"""
    print("\n" + "🚀" + "=" * 68)
    print("🚀 LAB AUTOMATION FRAMEWORK")
    print("🚀" + "=" * 68)
    print("📋 Main Options:")
    print("1. 🔍 Discovery & Topology")
    print("2. 👤 User Workflow")
    print("3. 🛠️  Advanced Tools")
    print("4. 📊 Reports & Analytics")
    print("5. ⚙️  Configuration")
    print("6. ❌ Exit")
    print()

def show_discovery_menu():
    """Discovery and topology menu"""
    print("\n" + "🔍" + "=" * 68)
    print("🔍 DISCOVERY & TOPOLOGY")
    print("🔍" + "=" * 68)
    print("📋 Discovery Options:")
    print("1. 🔍 Probe & Parse (LACP + LLDP)")
    print("2. 📊 Populate Devices from Inventory")
    print("3. 🌳 Generate ASCII Topology Tree")
    print("4. 🌳 Generate Minimized Topology Tree")
    print("5. 📊 View Device Status")
    print("6. 🔙 Back to Main Menu")
    print()

def show_user_menu():
    """User options menu"""
    while True:
        print("\n" + "🎯" + "=" * 68)
        print("👤 USER OPTIONS")
        print("🎯" + "=" * 68)
        print("📋 User Workflow:")
        print("1. 🔨 Bridge-Domain Builder (P2P)")
        print("2. 🔨 Unified Bridge-Domain Builder (P2P & P2MP with Superspine Support)")
        print("3. 🚀 Push Config via SSH")
        print("4. 🌳 View ASCII Topology Tree")
        print("5. 🌳 View Minimized Topology Tree")
        print("6. 🔍 Discover Existing Bridge Domains")
        print("7. 🌐 Visualize Bridge Domain Topology")
        print("8. 🔙 Back to Main Menu")
        print()
        
        choice = input("Select an option [1-8]: ").strip()
        
        if choice == '1':
            run_bridge_domain_builder()
        elif choice == '2':
            run_unified_bridge_domain_builder()
        elif choice == '3':
            run_ssh_push_menu()
        elif choice == '4':
            run_ascii_tree_viewer()
        elif choice == '5':
            run_minimized_tree_viewer()
        elif choice == '6':
            run_bridge_domain_discovery()
        elif choice == '7':
            run_bridge_domain_visualization()
        elif choice == '8':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, 6, 7, or 8.")

def show_advanced_menu():
    """Advanced tools menu"""
    print("\n" + "🛠️" + "=" * 68)
    print("🛠️ ADVANCED TOOLS")
    print("🛠️" + "=" * 68)
    print("📋 Advanced Options:")
    print("1. 🔧 Device Management")
    print("2. 📊 Performance Monitoring")
    print("3. 🔒 Security Analysis")
    print("4. 🔙 Back to Main Menu")
    print()

def show_reports_menu():
    """Reports and analytics menu"""
    print("\n" + "📊" + "=" * 68)
    print("📊 REPORTS & ANALYTICS")
    print("📊" + "=" * 68)
    print("📋 Report Options:")
    print("1. 📈 Topology Reports")
    print("2. 📊 Configuration Reports")
    print("3. 📋 Device Status Reports")
    print("4. 🔙 Back to Main Menu")
    print()

def show_config_menu():
    """Configuration menu"""
    print("\n" + "⚙️" + "=" * 68)
    print("⚙️ CONFIGURATION")
    print("⚙️" + "=" * 68)
    print("📋 Configuration Options:")
    print("1. 🔧 System Settings")
    print("2. 📁 File Management")
    print("3. 🔙 Back to Main Menu")
    print()

def run_discovery_menu():
    """Run discovery and topology menu"""
    while True:
        show_discovery_menu()
        choice = input("Select an option [1-6]: ").strip()
        
        if choice == '1':
            run_probe_and_parse()
        elif choice == '2':
            run_populate_devices_from_inventory()
        elif choice == '3':
            run_ascii_tree_viewer()
        elif choice == '4':
            run_minimized_tree_viewer()
        elif choice == '5':
            run_device_status_viewer()
        elif choice == '6':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, or 6.")

def run_advanced_menu():
    """Run advanced tools menu"""
    while True:
        show_advanced_menu()
        choice = input("Select an option [1-4]: ").strip()
        
        if choice == '1':
            print("🔧 Device Management - Coming Soon!")
        elif choice == '2':
            print("📊 Performance Monitoring - Coming Soon!")
        elif choice == '3':
            print("🔒 Security Analysis - Coming Soon!")
        elif choice == '4':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, or 4.")

def run_reports_menu():
    """Run reports and analytics menu"""
    while True:
        show_reports_menu()
        choice = input("Select an option [1-4]: ").strip()
        
        if choice == '1':
            print("📈 Topology Reports - Coming Soon!")
        elif choice == '2':
            print("📊 Configuration Reports - Coming Soon!")
        elif choice == '3':
            print("📋 Device Status Reports - Coming Soon!")
        elif choice == '4':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, or 4.")

def run_config_menu():
    """Run configuration menu"""
    while True:
        show_config_menu()
        choice = input("Select an option [1-3]: ").strip()
        
        if choice == '1':
            print("🔧 System Settings - Coming Soon!")
        elif choice == '2':
            print("📁 File Management - Coming Soon!")
        elif choice == '3':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")

def run_probe_and_parse():
    """Run probe and parse functionality"""
    print("\n🔍 Running Probe & Parse (LACP + LLDP)...")
    try:
        from scripts.inventory_manager import InventoryManager
        inventory_manager = InventoryManager()
        success = inventory_manager.run_probe_and_parse()
        if success:
            print("✅ Probe & Parse completed successfully!")
            print("📊 Data collected and parsed for topology analysis")
        else:
            print("❌ Probe & Parse failed. Check device connectivity and try again.")
    except Exception as e:
        print(f"❌ Probe & Parse failed: {e}")
        import traceback
        traceback.print_exc()

def run_populate_devices_from_inventory():
    """Run populate devices from inventory functionality"""
    print("\n📊 Running Populate Devices from Inventory...")
    try:
        from scripts.inventory_manager import InventoryManager
        inventory_manager = InventoryManager()
        success = inventory_manager.populate_from_inventory()
        if success:
            print("✅ Successfully populated devices.yaml from inventory")
        else:
            print("❌ Failed to populate devices.yaml from inventory")
    except Exception as e:
        print(f"❌ Populate Devices from Inventory failed: {e}")
        import traceback
        traceback.print_exc()

def run_bridge_domain_builder():
    """Run bridge domain builder"""
    print("\n🔨 Running Bridge Domain Builder...")
    try:
        from config_engine.bridge_domain_builder import BridgeDomainBuilder
        builder = BridgeDomainBuilder()
        
        # Get service configuration
        service_name = input("Enter service name (e.g., g_visaev_v253): ").strip()
        if not service_name:
            service_name = "g_visaev_v253"
        
        vlan_id_input = input("Enter VLAN ID (e.g., 253): ").strip()
        if not vlan_id_input:
            vlan_id_input = "253"
        
        try:
            vlan_id = int(vlan_id_input)
        except ValueError:
            print("❌ Invalid VLAN ID. Must be a number.")
            return
        
        # Get source and destination
        source_leaf = input("Enter source leaf device: ").strip()
        if not source_leaf:
            print("❌ Source leaf device is required.")
            return
        
        source_port = input("Enter source port (e.g., ge100-0/0/1): ").strip()
        if not source_port:
            print("❌ Source port is required.")
            return
        
        dest_leaf = input("Enter destination leaf device: ").strip()
        if not dest_leaf:
            print("❌ Destination leaf device is required.")
            return
        
        dest_port = input("Enter destination port (e.g., ge100-0/0/2): ").strip()
        if not dest_port:
            print("❌ Destination port is required.")
            return
        
        # Build configuration
        configs = builder.build_bridge_domain_config(
            service_name, vlan_id,
            source_leaf, source_port,
            dest_leaf, dest_port
        )
        
        if configs:
            print(f"\n✅ Bridge domain configuration generated successfully!")
            print(f"📁 Configuration saved for {len(configs)} devices")
            
            # Save to file in configs/pending directory
            output_file = f"bridge_domain_{service_name}.yaml"
            
            # Ensure configs/pending directory exists
            configs_pending_dir = Path("configs/pending")
            configs_pending_dir.mkdir(parents=True, exist_ok=True)
            
            # Save to configs/pending directory
            output_path = configs_pending_dir / output_file
            builder.save_configuration(configs, str(output_path))
            print(f"📁 Configuration saved to: {output_path}")
        else:
            print("❌ Failed to generate bridge domain configuration.")
            
    except Exception as e:
        print(f"❌ Bridge domain builder failed: {e}")
        import traceback
        traceback.print_exc()

def run_unified_bridge_domain_builder():
    """Run unified bridge domain builder"""
    print("\n🔨 Running Unified Bridge Domain Builder...")
    try:
        from config_engine.enhanced_menu_system import EnhancedMenuSystem
        menu_system = EnhancedMenuSystem()
        
        success = menu_system.run_enhanced_bridge_domain_builder()
        
        if success:
            print("✅ Unified bridge domain builder completed successfully!")
        else:
            print("❌ Unified bridge domain builder failed.")
            
    except Exception as e:
        print(f"❌ Unified bridge domain builder failed: {e}")
        import traceback
        traceback.print_exc()

def run_ssh_push_menu():
    """Run SSH push menu"""
    print("\n🚀 Running SSH Push Menu...")
    try:
        from scripts.ssh_push_menu import SSHPushMenu
        ssh_menu = SSHPushMenu()
        ssh_menu.show_main_menu()
    except Exception as e:
        print(f"❌ SSH push menu failed: {e}")

def run_ascii_tree_viewer():
    """Run ASCII tree viewer"""
    print("\n🌳 Running ASCII Topology Tree Viewer...")
    try:
        from scripts.ascii_topology_tree import AsciiTopologyTree
        tree_viewer = AsciiTopologyTree()
        tree_viewer.run_ascii_visualization()
    except Exception as e:
        print(f"❌ ASCII tree viewer failed: {e}")
        import traceback
        traceback.print_exc()

def run_minimized_tree_viewer():
    """Run minimized tree viewer"""
    print("\n🌳 Running Minimized Topology Tree Viewer...")
    try:
        from scripts.minimized_topology_tree import MinimizedTopologyTree
        tree_viewer = MinimizedTopologyTree()
        tree_viewer.run_minimized_visualization()
    except Exception as e:
        print(f"❌ Minimized tree viewer failed: {e}")
        import traceback
        traceback.print_exc()

def run_bridge_domain_discovery():
    """Run bridge domain discovery"""
    print("\n🔍 Running Bridge Domain Discovery...")
    try:
        from config_engine.bridge_domain_discovery import BridgeDomainDiscovery
        discovery = BridgeDomainDiscovery()
        result = discovery.run_discovery()
        if result:
            print("✅ Bridge domain discovery completed successfully!")
            print("📊 Bridge domain mapping data generated")
        else:
            print("❌ Bridge domain discovery failed.")
    except Exception as e:
        print(f"❌ Bridge domain discovery failed: {e}")
        import traceback
        traceback.print_exc()

def run_bridge_domain_visualization():
    """Run bridge domain visualization"""
    print("\n🌐 Running Bridge Domain Visualization...")
    try:
        from config_engine.bridge_domain_visualization import BridgeDomainVisualization
        visualization = BridgeDomainVisualization()
        result = visualization.run_visualization()
        if result:
            print("✅ Bridge domain visualization completed successfully!")
            print("📊 Bridge domain topology diagrams generated")
        else:
            print("❌ Bridge domain visualization failed.")
    except Exception as e:
        print(f"❌ Bridge domain visualization failed: {e}")
        import traceback
        traceback.print_exc()

def run_device_status_viewer():
    """Run device status viewer"""
    print("\n📊 Running Device Status Viewer...")
    try:
        from scripts.device_status_viewer import DeviceStatusViewer
        viewer = DeviceStatusViewer()
        viewer.display_device_status()
    except Exception as e:
        print(f"❌ Device status viewer failed: {e}")

def main():
    """Main function"""
    print("🚀 Welcome to Lab Automation Framework!")
    print("📋 This framework provides tools for network automation and topology management.")
    
    while True:
        show_main_menu()
        choice = input("Select an option [1-6]: ").strip()
        
        if choice == '1':
            run_discovery_menu()
        elif choice == '2':
            show_user_menu()
        elif choice == '3':
            run_advanced_menu()
        elif choice == '4':
            run_reports_menu()
        elif choice == '5':
            run_config_menu()
        elif choice == '6':
            print("\n👋 Thank you for using Lab Automation Framework!")
            print("🚀 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, or 6.")

if __name__ == "__main__":
    main() 