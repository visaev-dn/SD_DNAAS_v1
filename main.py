#!/usr/bin/env python3
"""
Main entry point for the lab automation framework.
Presents a menu for the user to choose an action.
"""
import subprocess
import sys
from pathlib import Path
import yaml
import json
import re

def parse_device_name(device_name):
    """
    Parse device name to extract DC row and rack number.
    Examples:
    - DNAAS-LEAF-A12 -> ('A', '12')
    - DNAAS_LEAF_D13 -> ('D', '13')
    - DNAAS-LEAF-B06-2 (NCPL) -> ('B', '06-2')
    """
    # Handle different naming patterns
    patterns = [
        r'DNAAS-LEAF-([A-Z])(\d+(?:-\d+)?)',  # DNAAS-LEAF-A12, DNAAS-LEAF-B06-2
        r'DNAAS_LEAF_([A-Z])(\d+)',           # DNAAS_LEAF_D13
    ]
    
    for pattern in patterns:
        match = re.match(pattern, device_name)
        if match:
            row = match.group(1)
            rack = match.group(2)
            return row, rack
    
    return None, None

def organize_leaf_devices_by_row(successful_devices):
    """
    Organize successful leaf devices by DC row.
    
    Args:
        successful_devices: List of successful device names
        
    Returns:
        dict: {row_letter: {rack_number: device_name}}
    """
    organized = {}
    
    for device in successful_devices:
        row, rack = parse_device_name(device)
        if row and rack:
            if row not in organized:
                organized[row] = {}
            organized[row][rack] = device
    
    return organized

def get_successful_devices_from_status():
    """
    Read the device status JSON file and extract successful devices.
    
    Returns:
        list: List of successful device names
    """
    status_file = Path("topology/device_status.json")
    if not status_file.exists():
        return []
    
    try:
        with open(status_file, 'r') as f:
            device_status = json.load(f)
        
        # Extract successful devices
        successful_devices = []
        for device_name, device_info in device_status['devices'].items():
            if device_info['status'] == 'successful':
                successful_devices.append(device_name)
        
        return successful_devices
    except Exception as e:
        print(f"Error reading device status file: {e}")
        return []

def get_successful_devices_from_summary():
    """
    Read the collection summary and extract successful devices.
    
    Returns:
        list: List of successful device names
    """
    summary_file = Path("topology/collection_summary.txt")
    if not summary_file.exists():
        return []
    
    successful_devices = []
    in_successful_section = False
    
    with open(summary_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("✅ SUCCESSFUL DEVICES"):
                in_successful_section = True
                continue
            elif line.startswith("💡 RECOMMENDATIONS") or line.startswith("❌ FAILED DEVICES"):
                in_successful_section = False
                continue
            
            if in_successful_section and line.startswith("   • "):
                # Extract device name from "   • DNAAS-LEAF-A01 (LACP+LLDP)"
                device_name = line[5:].split(" (")[0].strip()
                successful_devices.append(device_name)
    
    return successful_devices

def select_leaf_device(organized_devices, prompt_prefix=""):
    """
    Interactive selection of leaf device by row and rack number.
    
    Args:
        organized_devices: Dict of organized devices by row
        prompt_prefix: Prefix for the prompt (e.g., "Source", "Destination")
        
    Returns:
        str: Selected device name or None if cancelled
    """
    if not organized_devices:
        print("❌ No successful leaf devices found.")
        return None
    
    # Show available rows
    available_rows = sorted(organized_devices.keys())
    print(f"\n🏢 {prompt_prefix} DC Row Selection:")
    print("Available DC Rows:", ", ".join(available_rows))
    
    while True:
        row_choice = input(f"Select DC Row ({'/'.join(available_rows)}): ").strip().upper()
        if row_choice in available_rows:
            break
        print(f"❌ Invalid row. Available: {', '.join(available_rows)}")
    
    # Show available rack numbers for selected row
    rack_devices = organized_devices[row_choice]
    available_racks = sorted(rack_devices.keys(), key=lambda x: int(x.split('-')[0]) if '-' in x else int(x))
    
    print(f"\n📦 {prompt_prefix} Rack Selection (Row {row_choice}):")
    print("Available Rack Numbers:", ", ".join(available_racks))
    
    while True:
        rack_choice = input(f"Select Rack Number ({'/'.join(available_racks)}): ").strip()
        if rack_choice in rack_devices:
            selected_device = rack_devices[rack_choice]
            print(f"✅ Selected: {selected_device}")
            return selected_device
        print(f"❌ Invalid rack number. Available: {', '.join(available_racks)}")

def main_menu():
    """Main menu function with developer and user options"""
    while True:
        print("\n" + "=" * 70)
        print("🚀 LAB AUTOMATION FRAMEWORK")
        print("=" * 70)
        print("Welcome! Please select your role:")
        print()
        print("👨‍💻 [1] Developer Options")
        print("👤 [2] User Options")
        print("❌ [3] Exit")
        print()
        
        choice = input("Select your role [1-3]: ").strip()
        
        if choice == '1':
            show_developer_menu()
        elif choice == '2':
            show_user_menu()
        elif choice == '3':
            print("\n👋 Goodbye! Thanks for using Lab Automation Framework!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please select 1, 2, or 3.")

def show_developer_menu():
    """Developer options menu"""
    while True:
        print("\n" + "🔧" + "=" * 68)
        print("👨‍💻 DEVELOPER OPTIONS")
        print("🔧" + "=" * 68)
        print("📋 Development Workflow:")
        print("1. 📊 Populate Devices from Inventory")
        print("2. 🔍 Probe+Parse LACP+LLDP (Raw+Parsed Data)")
        print("3. 🌐 Enhanced Topology Discovery (With Normalization)")
        print("4. 🌳 Visualize Topology (ASCII Tree)")
        print("5. 🌳 Create Minimized Topology Tree")
        print("6. 🔙 Back to Main Menu")
        print()
        
        choice = input("Select an option [1-6]: ").strip()
        
        if choice == '1':
            run_inventory_population()
        elif choice == '2':
            run_probe_parse_lacp_lldp()
        elif choice == '3':
            run_enhanced_topology_discovery()
        elif choice == '4':
            run_ascii_topology_visualization()
        elif choice == '5':
            run_minimized_topology_visualization()
        elif choice == '6':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, or 6.")

def show_user_menu():
    """User options menu"""
    while True:
        print("\n" + "🎯" + "=" * 68)
        print("👤 USER OPTIONS")
        print("🎯" + "=" * 68)
        print("📋 User Workflow:")
        print("1. 🔨 Bridge-Domain Builder (P2P)")
        print("2. 🌐 P2MP Bridge-Domain Builder")
        print("3. 🔨 Enhanced Bridge-Domain Builder (with Superspine Support)")
        print("4. 🚀 Push Config via SSH")
        print("5. 🌳 View ASCII Topology Tree")
        print("6. 🌳 View Minimized Topology Tree")
        print("7. 🔍 Discover Existing Bridge Domains")
        print("8. 🌐 Visualize Bridge Domain Topology")
        print("9. 🔙 Back to Main Menu")
        print()
        
        choice = input("Select an option [1-9]: ").strip()
        
        if choice == '1':
            run_bridge_domain_builder()
        elif choice == '2':
            run_p2mp_bridge_domain_builder()
        elif choice == '3':
            run_enhanced_bridge_domain_builder()
        elif choice == '4':
            run_ssh_push_menu()
        elif choice == '5':
            run_ascii_tree_viewer()
        elif choice == '6':
            run_minimized_tree_viewer()
        elif choice == '7':
            run_bridge_domain_discovery()
        elif choice == '8':
            run_bridge_domain_visualization()
        elif choice == '9':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, 6, 7, 8, or 9.")

def run_enhanced_topology_discovery():
    print("\n" + "🌐" + "=" * 68)
    print("🌐 ENHANCED TOPOLOGY DISCOVERY")
    print("🌐" + "=" * 68)
    print("Running enhanced topology discovery...")
    result = subprocess.run([sys.executable, 'scripts/enhanced_topology_discovery.py'])
    if result.returncode == 0:
        print("\n✅ Enhanced Topology Discovery completed successfully!")
        print("📁 Check topology/enhanced_topology.json for normalized topology")
        print("📁 Check topology/complete_topology_v2.json for full topology")
        print("📁 Check topology/bundle_mapping_v2.yaml for bundle mappings")
    else:
        print("\n❌ Enhanced Topology Discovery failed. See output above.")

def run_bridge_domain_builder():
    print("\n" + "🔨" + "=" * 68)
    print("🔨 BRIDGE-DOMAIN BUILDER")
    print("🔨" + "=" * 68)
    
    # Check if topology files exist
    topology_file = Path("topology/complete_topology_v2.json")
    bundle_file = Path("topology/bundle_mapping_v2.yaml")
    
    if not topology_file.exists():
        print("❌ Topology file not found. Please run topology discovery first.")
        return
    
    if not bundle_file.exists():
        print("❌ Bundle mapping file not found. Please run topology discovery first.")
        return
    
    print("✅ Topology files found. Starting bridge domain builder...")
    
    # Import and run the bridge domain builder
    try:
        from config_engine.bridge_domain_builder import BridgeDomainBuilder
        
        # Initialize the builder
        builder = BridgeDomainBuilder()
        
        # Interactive prompts
        print("\n📋 Bridge Domain Configuration")
        print("─" * 40)
        
        # Username
        default_username = "visaev"
        username = input(f"👤 Username (e.g., {default_username}): ").strip()
        if not username:
            username = default_username
        
        # VLAN ID
        default_vlan_id = "253"
        vlan_id_input = input(f"🏷️  VLAN ID (e.g., {default_vlan_id}): ").strip()
        if not vlan_id_input:
            vlan_id_input = default_vlan_id
        try:
            vlan_id = int(vlan_id_input)
        except ValueError:
            print("❌ Invalid VLAN ID. Must be a number.")
            return
        
        # Format service name as g_"username"_v"vlan-id"
        service_name = f"g_{username}_v{vlan_id}"
        print(f"✅ Service name will be: {service_name}")
        
        # Get successful devices and organize by row
        successful_devices = get_successful_devices_from_status()
        if not successful_devices:
            print("❌ No successful devices found. Please run probe+parse first.")
            return
        
        # Filter to only leaf devices
        leaf_devices = [dev for dev in successful_devices if 'LEAF' in dev.upper()]
        if not leaf_devices:
            print("❌ No successful leaf devices found.")
            return
        
        # Get available leaves from bridge domain builder
        builder = BridgeDomainBuilder()
        available_leaves = builder.get_available_leaves()
        unavailable_reasons = builder.get_unavailable_leaves()
        
        if not available_leaves:
            print("❌ No available leaf devices found for bridge domain calculations.")
            if unavailable_reasons:
                print("🔴 Unavailable leaves:")
                for leaf, reason in unavailable_reasons.items():
                    print(f"   • {leaf}: {reason.get('description', 'Unknown reason')}")
            return
        
        # Filter to only available leaf devices
        available_leaf_devices = [dev for dev in leaf_devices if dev in available_leaves]
        if not available_leaf_devices:
            print("❌ No available leaf devices found after filtering.")
            return
        
        # Show information about unavailable leaves
        unavailable_leaf_devices = [dev for dev in leaf_devices if dev not in available_leaves]
        if unavailable_leaf_devices:
            print(f"\n⚠️  {len(unavailable_leaf_devices)} leaf devices are unavailable for bridge domain calculations:")
            for leaf in unavailable_leaf_devices:
                reason = unavailable_reasons.get(leaf, {})
                description = reason.get('description', 'Unknown reason')
                print(f"   • {leaf}: {description}")
            print()
        
        # Organize by DC row
        organized_devices = organize_leaf_devices_by_row(available_leaf_devices)
        
        print(f"\n📊 Found {len(available_leaf_devices)} available leaf devices across {len(organized_devices)} DC rows")
        
        # Source leaf selection
        source_leaf = select_leaf_device(organized_devices, "Source")
        if not source_leaf:
            return
        
        # Source port
        default_source_port_num = "10"
        source_port_num = input(f"🔌 Enter the interface number (X) for ge100-0/0/X (e.g., {default_source_port_num}): ").strip()
        if not source_port_num:
            source_port_num = default_source_port_num
        source_port = f"ge100-0/0/{source_port_num}"
        
        # Destination selection
        print(f"\n🌐 P2MP Destination Selection")
        print("─" * 40)
        print("Select destinations for P2MP bridge domain:")
        
        destinations = []
        while True:
            # Destination leaf selection using same interface as P2P
            dest_leaf = select_leaf_device(organized_devices, "Destination")
            if not dest_leaf:
                if destinations:
                    print("✅ Finished adding destinations.")
                    break
                else:
                    print("❌ No destinations selected.")
                    return
            
            # Destination port
            default_dest_port_num = str(20 + len(destinations))
            dest_port_num = input(f"🔌 Enter the interface number (X) for ge100-0/0/X (e.g., {default_dest_port_num}): ").strip()
            if not dest_port_num:
                dest_port_num = default_dest_port_num
            dest_port = f"ge100-0/0/{dest_port_num}"
            
            destinations.append({
                'leaf': dest_leaf,
                'port': dest_port
            })
            
            print(f"✅ Added destination: {dest_leaf}:{dest_port}")
            
            # Ask if user wants to add another destination
            add_another = input(f"\nAdd another destination? (y/n): ").strip().lower()
            if add_another not in ['y', 'yes']:
                break
        
        if not destinations:
            print("❌ No destinations selected.")
            return
        
        print(f"\n✅ Selected {len(destinations)} destinations:")
        for dest in destinations:
            print(f"   • {dest['leaf']}:{dest['port']}")
        
        # Build the configuration (automatic path determination)
        print(f"\n🔨 Building P2MP bridge domain configuration...")
        print("📡 Automatically determining optimal paths (2-tier for same spine, 3-tier for different spines)")
        configs = builder.build_p2mp_bridge_domain_config(
            service_name, vlan_id,
            source_leaf, source_port,
            destinations
        )
        
        if not configs:
            print("❌ Failed to build P2MP bridge domain configuration.")
            return
        
        # Show configuration summary
        print(f"\n📋 Configuration Summary:")
        summary = builder.get_configuration_summary(configs)
        print(summary)
        
        # Show path visualization
        metadata = configs.get('_metadata', {})
        path_calculation = metadata.get('path_calculation', {})
        if path_calculation:
            print(f"\n🌳 Path Visualization:")
            visualization = builder.visualize_p2mp_paths(path_calculation)
            print(visualization)
        
        # Save the configuration
        output_file = f"p2mp_bridge_domain_{service_name}.yaml"
        builder.save_configuration(configs, output_file)
        
        print(f"\n✅ P2MP bridge domain configuration built successfully!")
        print(f"📁 Configuration saved to: {output_file}")
        
        # Show device count
        device_count = len([k for k in configs.keys() if k != '_metadata'])
        print(f"📋 Devices configured: {device_count}")
        
    except ImportError as e:
        print(f"❌ Failed to import bridge domain builder: {e}")
    except Exception as e:
        print(f"❌ Bridge domain builder failed: {e}")
        import traceback
        traceback.print_exc()

def run_p2mp_bridge_domain_builder():
    print("\n" + "🌐" + "=" * 68)
    print("🌐 P2MP BRIDGE-DOMAIN BUILDER")
    print("🌐" + "=" * 68)
    
    # Check if topology files exist
    topology_file = Path("topology/complete_topology_v2.json")
    bundle_file = Path("topology/bundle_mapping_v2.yaml")
    
    if not topology_file.exists():
        print("❌ Topology file not found. Please run topology discovery first.")
        return
    
    if not bundle_file.exists():
        print("❌ Bundle mapping file not found. Please run topology discovery first.")
        return
    
    print("✅ Topology files found. Starting P2MP bridge domain builder...")
    
    # Import and run the P2MP bridge domain builder
    try:
        from config_engine.p2mp_bridge_domain_builder import P2MPBridgeDomainBuilder
        
        # Initialize the builder
        builder = P2MPBridgeDomainBuilder()
        
        # Interactive prompts
        print("\n📋 P2MP Bridge Domain Configuration")
        print("─" * 40)
        
        # Username
        default_username = "visaev"
        username = input(f"👤 Username (e.g., {default_username}): ").strip()
        if not username:
            username = default_username
        
        # VLAN ID
        default_vlan_id = "253"
        vlan_id_input = input(f"🏷️  VLAN ID (e.g., {default_vlan_id}): ").strip()
        if not vlan_id_input:
            vlan_id_input = default_vlan_id
        try:
            vlan_id = int(vlan_id_input)
        except ValueError:
            print("❌ Invalid VLAN ID. Must be a number.")
            return
        
        # Format service name as g_"username"_v"vlan-id"
        service_name = f"g_{username}_v{vlan_id}"
        print(f"✅ Service name will be: {service_name}")
        
        # Get successful devices and organize by row
        successful_devices = get_successful_devices_from_status()
        if not successful_devices:
            print("❌ No successful devices found. Please run probe+parse first.")
            return
        
        # Filter to only leaf devices
        leaf_devices = [dev for dev in successful_devices if 'LEAF' in dev.upper()]
        if not leaf_devices:
            print("❌ No successful leaf devices found.")
            return
        
        # Get available leaves from P2MP bridge domain builder
        available_leaves = builder.get_available_leaves()
        unavailable_reasons = builder.get_unavailable_leaves()
        
        if not available_leaves:
            print("❌ No available leaf devices found for bridge domain calculations.")
            if unavailable_reasons:
                print("🔴 Unavailable leaves:")
                for leaf, reason in unavailable_reasons.items():
                    print(f"   • {leaf}: {reason.get('description', 'Unknown reason')}")
            return
        
        # Filter to only available leaf devices
        available_leaf_devices = [dev for dev in leaf_devices if dev in available_leaves]
        if not available_leaf_devices:
            print("❌ No available leaf devices found after filtering.")
            return
        
        # Show information about unavailable leaves
        unavailable_leaf_devices = [dev for dev in leaf_devices if dev not in available_leaves]
        if unavailable_leaf_devices:
            print(f"\n⚠️  {len(unavailable_leaf_devices)} leaf devices are unavailable for bridge domain calculations:")
            for leaf in unavailable_leaf_devices:
                reason = unavailable_reasons.get(leaf, {})
                description = reason.get('description', 'Unknown reason')
                print(f"   • {leaf}: {description}")
            print()
        
        # Organize by DC row
        organized_devices = organize_leaf_devices_by_row(available_leaf_devices)
        
        print(f"\n📊 Found {len(available_leaf_devices)} available leaf devices across {len(organized_devices)} DC rows")
        
        # Source leaf selection
        source_leaf = select_leaf_device(organized_devices, "Source")
        if not source_leaf:
            return
        
        # Source port
        default_source_port_num = "10"
        source_port_num = input(f"🔌 Enter the interface number (X) for ge100-0/0/X (e.g., {default_source_port_num}): ").strip()
        if not source_port_num:
            source_port_num = default_source_port_num
        source_port = f"ge100-0/0/{source_port_num}"
        
        # Destination selection
        print(f"\n🌐 P2MP Destination Selection")
        print("─" * 40)
        print("Select destinations for P2MP bridge domain:")
        
        destinations = []
        while True:
            # Destination leaf selection using same interface as P2P
            dest_leaf = select_leaf_device(organized_devices, "Destination")
            if not dest_leaf:
                if destinations:
                    print("✅ Finished adding destinations.")
                    break
                else:
                    print("❌ No destinations selected.")
                    return
            
            # Destination port
            default_dest_port_num = str(20 + len(destinations))
            dest_port_num = input(f"🔌 Enter the interface number (X) for ge100-0/0/X (e.g., {default_dest_port_num}): ").strip()
            if not dest_port_num:
                dest_port_num = default_dest_port_num
            dest_port = f"ge100-0/0/{dest_port_num}"
            
            destinations.append({
                'leaf': dest_leaf,
                'port': dest_port
            })
            
            print(f"✅ Added destination: {dest_leaf}:{dest_port}")
            
            # Ask if user wants to add another destination
            add_another = input(f"\nAdd another destination? (y/n): ").strip().lower()
            if add_another not in ['y', 'yes']:
                break
        
        if not destinations:
            print("❌ No destinations selected.")
            return
        
        print(f"\n✅ Selected {len(destinations)} destinations:")
        for dest in destinations:
            print(f"   • {dest['leaf']}:{dest['port']}")
        
        # Build the configuration (automatic path determination)
        print(f"\n🔨 Building P2MP bridge domain configuration...")
        print("📡 Automatically determining optimal paths (2-tier for same spine, 3-tier for different spines)")
        configs = builder.build_p2mp_bridge_domain_config(
            service_name, vlan_id,
            source_leaf, source_port,
            destinations
        )
        
        if not configs:
            print("❌ Failed to build P2MP bridge domain configuration.")
            return
        
        # Show configuration summary
        print(f"\n📋 Configuration Summary:")
        summary = builder.get_configuration_summary(configs)
        print(summary)
        
        # Show path visualization
        metadata = configs.get('_metadata', {})
        path_calculation = metadata.get('path_calculation', {})
        if path_calculation:
            print(f"\n🌳 Path Visualization:")
            visualization = builder.visualize_p2mp_paths(path_calculation)
            print(visualization)
        
        # Save the configuration
        output_file = f"p2mp_bridge_domain_{service_name}.yaml"
        builder.save_configuration(configs, output_file)
        
        print(f"\n✅ P2MP bridge domain configuration built successfully!")
        print(f"📁 Configuration saved to: {output_file}")
        
        # Show device count
        device_count = len([k for k in configs.keys() if k != '_metadata'])
        print(f"📋 Devices configured: {device_count}")
        
    except ImportError as e:
        print(f"❌ Failed to import P2MP bridge domain builder: {e}")
    except Exception as e:
        print(f"❌ P2MP bridge domain builder failed: {e}")
        import traceback
        traceback.print_exc()

def run_inventory_population():
    print("\n" + "📊" + "=" * 68)
    print("📊 INVENTORY POPULATION")
    print("📊" + "=" * 68)
    print("Populating devices.yaml from external inventory...")
    
    # Check if required dependencies are available
    try:
        import pandas as pd
        import requests
    except ImportError as e:
        print(f"❌ Missing required dependencies: {e}")
        print("Please install required packages: pip install pandas openpyxl requests")
        return
    
    # Run inventory population
    result = subprocess.run([sys.executable, 'scripts/inventory_manager.py', 'populate'])
    if result.returncode == 0:
        print("\n✅ Inventory Population completed successfully!")
        print("📁 devices.yaml has been updated with deployed devices from inventory")
    else:
        print("\n❌ Inventory Population failed. See output above.")

def run_probe_parse_lacp_lldp():
    print("\n" + "🔍" + "=" * 68)
    print("🔍 PROBE+PARSE LACP+LLDP")
    print("🔍" + "=" * 68)
    print("Collecting and parsing LACP/LLDP data for all devices...")
    result = subprocess.run([sys.executable, 'scripts/collect_lacp_xml.py', '--phase', 'both'])
    if result.returncode == 0:
        print("\n✅ Probe+Parse LACP+LLDP completed successfully!")
        print("📁 Raw data in topology/configs/raw-config/ and parsed data in topology/configs/parsed_data/")
    else:
        print("\n❌ Probe+Parse LACP+LLDP failed. See output above.")

def run_ascii_topology_visualization():
    print("\n" + "🌳" + "=" * 68)
    print("🌳 ASCII TOPOLOGY VISUALIZATION")
    print("🌳" + "=" * 68)
    print("Creating bundle-aware topology tree...")
    result = subprocess.run([sys.executable, 'scripts/ascii_topology_tree.py'])
    if result.returncode == 0:
        print("\n✅ ASCII Topology Visualization completed successfully!")
        print("📁 Check topology/visualizations/topology_bundle_aware_tree.txt")
    else:
        print("\n❌ ASCII Topology Visualization failed. See output above.")

def run_minimized_topology_visualization():
    print("\n" + "🌳" + "=" * 68)
    print("�� MINIMIZED TOPOLOGY VISUALIZATION")
    print("🌳" + "=" * 68)
    print("Creating minimized topology tree...")
    result = subprocess.run([sys.executable, 'scripts/minimized_topology_tree.py'])
    if result.returncode == 0:
        print("\n✅ Minimized Topology Visualization completed successfully!")
        print("📁 Check topology/visualizations/topology_minimized_tree.txt")
    else:
        print("\n❌ Minimized Topology Visualization failed. See output above.")

def run_ssh_push_menu():
    print("\n" + "🚀" + "=" * 68)
    print("🚀 SSH CONFIGURATION PUSH")
    print("🚀" + "=" * 68)
    
    # Check if configs directory exists
    configs_dir = Path("configs")
    if not configs_dir.exists():
        print("❌ Configs directory not found. Please run bridge domain builder first.")
        return
    
    # Check if there are any pending bridge domain configs
    pending_dir = configs_dir / "pending"
    if not pending_dir.exists() or not list(pending_dir.glob("*.yaml")):
        print("❌ No bridge domain configurations found.")
        print("   Please run bridge domain builder first to generate configurations.")
        return
    
    print("✅ Bridge domain configurations found. Starting SSH push menu...")
    
    # Import and run the SSH push menu
    try:
        from scripts.ssh_push_menu import SSHPushMenu
        
        menu = SSHPushMenu()
        menu.show_main_menu()
        
    except ImportError as e:
        print(f"❌ Failed to import SSH push menu: {e}")
    except Exception as e:
        print(f"❌ SSH push menu failed: {e}")
        import traceback
        traceback.print_exc()

def run_ascii_tree_viewer():
    print("\n" + "🌳" + "=" * 68)
    print("🌳 ASCII TOPOLOGY TREE VIEWER")
    print("🌳" + "=" * 68)
    print("Loading ASCII topology tree...")
    tree_file = Path("topology/visualizations/topology_bundle_aware_tree.txt")
    if not tree_file.exists():
        print("❌ ASCII topology tree file not found. Please run ASCII Topology Visualization first.")
        return
    
    try:
        with open(tree_file, 'r') as f:
            for line in f:
                print(line.strip())
    except Exception as e:
        print(f"❌ Failed to read ASCII topology tree file: {e}")
        import traceback
        traceback.print_exc()

def run_minimized_tree_viewer():
    print("\n" + "🌳" + "=" * 68)
    print("🌳 MINIMIZED TOPOLOGY TREE VIEWER")
    print("🌳" + "=" * 68)
    print("Loading minimized topology tree...")
    tree_file = Path("topology/visualizations/topology_minimized_tree.txt")
    if not tree_file.exists():
        print("❌ Minimized topology tree file not found. Please run Minimized Topology Visualization first.")
        return
    
    try:
        with open(tree_file, 'r') as f:
            for line in f:
                print(line.strip())
    except Exception as e:
        print(f"❌ Failed to read minimized topology tree file: {e}")
        import traceback
        traceback.print_exc()

def run_bridge_domain_discovery():
    print("\n" + "🔍" + "=" * 68)
    print("🔍 BRIDGE DOMAIN DISCOVERY")
    print("🔍" + "=" * 68)
    
    # Check if parsed data exists
    parsed_data_dir = Path("topology/configs/parsed_data")
    if not parsed_data_dir.exists():
        print("❌ Parsed data directory not found. Please run probe+parse first.")
        return
    
    # Check if bridge domain data exists
    bridge_domain_parsed_dir = Path("topology/configs/parsed_data/bridge_domain_parsed")
    if not bridge_domain_parsed_dir.exists():
        print("❌ Bridge domain parsed data directory not found. Please run probe+parse first.")
        return
    
    bridge_domain_files = list(bridge_domain_parsed_dir.glob("*_bridge_domain_instance_parsed_*.yaml"))
    if not bridge_domain_files:
        print("❌ No bridge domain data found. Please run probe+parse first.")
        return
    
    print("✅ Bridge domain data found. Starting discovery...")
    
    # Import and run the bridge domain discovery
    try:
        from config_engine.bridge_domain_discovery import BridgeDomainDiscovery
        
        # Initialize the discovery engine
        discovery = BridgeDomainDiscovery()
        
        # Run discovery
        print("\n🔍 Analyzing bridge domain configurations...")
        mapping = discovery.run_discovery()
        
        # Show summary
        print("\n" + "=" * 80)
        print("BRIDGE DOMAIN DISCOVERY COMPLETE")
        print("=" * 80)
        
        summary_report = discovery.generate_summary_report(mapping)
        print(summary_report)
        
        # Show file locations
        output_dir = Path("topology/bridge_domain_discovery")
        mapping_files = list(output_dir.glob("bridge_domain_mapping_*.json"))
        summary_files = list(output_dir.glob("bridge_domain_summary_*.txt"))
        
        if mapping_files:
            latest_mapping = max(mapping_files, key=lambda x: x.stat().st_mtime)
            print(f"\n📁 Latest mapping file: {latest_mapping}")
        
        if summary_files:
            latest_summary = max(summary_files, key=lambda x: x.stat().st_mtime)
            print(f"📁 Latest summary file: {latest_summary}")
        
        print(f"\n✅ Bridge domain discovery completed successfully!")
        print(f"📊 Found {len(mapping.get('bridge_domains', []))} high-confidence bridge domains")
        print(f"⚠️  Found {len(mapping.get('unmapped_configurations', []))} unmapped configurations")
        
    except ImportError as e:
        print(f"❌ Failed to import bridge domain discovery: {e}")
    except Exception as e:
        print(f"❌ Bridge domain discovery failed: {e}")
        import traceback
        traceback.print_exc()

def run_bridge_domain_visualization():
    print("\n" + "🌐" + "=" * 68)
    print("🌐 BRIDGE DOMAIN VISUALIZATION")
    print("🌐" + "=" * 68)
    
    # Check if parsed data exists
    parsed_data_dir = Path("topology/configs/parsed_data")
    if not parsed_data_dir.exists():
        print("❌ Parsed data directory not found. Please run probe+parse first.")
        return
    
    # Check if bridge domain data exists
    bridge_domain_parsed_dir = Path("topology/configs/parsed_data/bridge_domain_parsed")
    if not bridge_domain_parsed_dir.exists():
        print("❌ Bridge domain parsed data directory not found. Please run probe+parse first.")
        return
    
    bridge_domain_files = list(bridge_domain_parsed_dir.glob("*_bridge_domain_instance_parsed_*.yaml"))
    if not bridge_domain_files:
        print("❌ No bridge domain data found. Please run probe+parse first.")
        return
    
    print("✅ Bridge domain data found. Starting visualization...")
    
    # Import and run the bridge domain visualization
    try:
        from config_engine.bridge_domain_visualization import BridgeDomainVisualization
        
        # Initialize the visualization engine
        visualization = BridgeDomainVisualization()
        
        # Run visualization
        print("\n🌐 Analyzing bridge domain configurations...")
        visualization.run_visualization()
        
        # Show file locations
        output_dir = Path("topology/bridge_domain_visualization")
        visualization_files = list(output_dir.glob("bridge_domain_visualization_*.txt"))
        
        if visualization_files:
            latest_visualization = max(visualization_files, key=lambda x: x.stat().st_mtime)
            print(f"\n📁 Latest visualization file: {latest_visualization}")
        
        print(f"\n✅ Bridge domain visualization completed successfully!")
        
    except ImportError as e:
        print(f"❌ Failed to import bridge domain visualization: {e}")
    except Exception as e:
        print(f"❌ Bridge domain visualization failed: {e}")
        import traceback
        traceback.print_exc()

def run_enhanced_bridge_domain_builder():
    """Run the enhanced bridge domain builder with Superspine support."""
    try:
        from config_engine.enhanced_menu_system import EnhancedMenuSystem
        
        menu_system = EnhancedMenuSystem()
        success = menu_system.run_enhanced_bridge_domain_builder()
        
        if success:
            print("\n✅ Enhanced bridge domain builder completed successfully!")
        else:
            print("\n❌ Enhanced bridge domain builder failed.")
            
    except ImportError as e:
        print(f"❌ Failed to import enhanced menu system: {e}")
        print("   Please ensure all enhanced modules are available.")
    except Exception as e:
        print(f"❌ Enhanced bridge domain builder failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main_menu() 