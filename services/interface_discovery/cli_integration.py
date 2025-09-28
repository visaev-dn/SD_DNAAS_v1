#!/usr/bin/env python3
"""
CLI Integration for Interface Discovery

Functions to integrate interface discovery with main.py CLI.
"""

import logging
from typing import List, Dict, Optional, Tuple

from .simple_discovery import SimpleInterfaceDiscovery
from .smart_filter import SmartInterfaceFilter, get_smart_interface_options, get_devices_with_smart_preview

logger = logging.getLogger(__name__)


def enhanced_bd_editor_with_discovery(db_manager) -> Tuple[Optional[str], Optional[str]]:
    """Enhanced BD Editor that uses smart interface filtering"""
    try:
        print("\n" + "="*60)
        print("🎯 Smart BD Editor with Intelligent Interface Selection")
        print("="*60)
        print("💡 This editor uses smart filtering to show safe interface choices")
        
        # Get devices with smart interface preview
        devices = get_devices_with_smart_preview()
        
        if not devices:
            print("❌ No devices with interface data found.")
            print("💡 Use Advanced Tools → Interface Discovery Management to refresh data")
            return manual_interface_input()
        
        # Display devices with smart categorization
        print(f"\n📊 Available Devices ({len(devices)} devices with smart analysis):")
        print("-" * 60)
        
        for i, device in enumerate(devices, 1):
            counts = device['interface_counts']
            status_icon = "🟢" if device['status'] == "online" else "🔴" if device['status'] == "offline" else "🟡"
            
            print(f"   {i:2d}. {status_icon} {device['name']}")
            print(f"       ✅ {counts['safe']} safe  🔵 {counts['available']} available", end="")
            if counts['caution'] > 0:
                print(f"  ⚠️  {counts['caution']} with warnings", end="")
            print(f"  🎯 {counts['total_configurable']} configurable")
        
        print("   0. Cancel")
        
        # Device selection
        while True:
            try:
                choice = input(f"\nSelect device (0-{len(devices)}): ").strip()
                
                if choice == "0":
                    return None, None
                
                device_index = int(choice) - 1
                if 0 <= device_index < len(devices):
                    selected_device = devices[device_index]['name']
                    device_info = devices[device_index]
                    break
                else:
                    print(f"❌ Invalid choice. Please select 0-{len(devices)}.")
            except (ValueError, KeyboardInterrupt):
                return None, None
        
        # Show device selection summary
        counts = device_info['interface_counts']
        print(f"\n✅ Selected device: {selected_device}")
        if counts['safe'] > 0:
            print(f"💡 This device has {counts['safe']} safe interfaces - excellent choices!")
        elif counts['available'] > 0:
            print(f"💡 This device has {counts['available']} available interfaces")
        elif counts['caution'] > 0:
            print(f"⚠️  This device only has {counts['caution']} interfaces with warnings")
        else:
            print("❌ This device has no suitable interfaces for BD configuration")
            return None, None
        
        # Smart interface selection
        device_name, interface_name = get_smart_device_interface_menu(selected_device)
        
        if device_name and interface_name:
            print(f"\n✅ Smart Interface Selection Complete")
            return device_name, interface_name
        else:
            print("❌ Interface selection failed or cancelled")
            return None, None
        
    except Exception as e:
        logger.error(f"Error in enhanced BD editor: {e}")
        return manual_interface_input()


def get_smart_device_interface_menu(device_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Smart interface selection menu with intelligent filtering and recommendations.
    
    Returns:
        Tuple of (device_name, interface_name) or (None, None) if cancelled
    """
    
    try:
        filter_service = SmartInterfaceFilter()
        interfaces = filter_service.get_smart_interface_options(device_name)
        
        print(f"\n🎯 Smart Interface Selection: {device_name}")
        print("=" * 70)
        print("💡 Interfaces are categorized by suitability for BD configuration")
        
        # Build selection menu
        options = []
        option_num = 1
        
        # Safe interfaces (show first)
        if interfaces["safe"]:
            print(f"\n✅ SAFE INTERFACES ({len(interfaces['safe'])} available):")
            print("   These interfaces are safe for Bridge Domain configuration")
            for intf in interfaces["safe"]:
                print(f"   {option_num:2d}. {intf.name} ({intf.type}) - {intf.admin_status}/{intf.oper_status}")
                if intf.tips:
                    print(f"       💡 {intf.tips[0]}")
                options.append(intf)
                option_num += 1
        
        # Available interfaces
        if interfaces["available"]:
            print(f"\n🔵 AVAILABLE INTERFACES ({len(interfaces['available'])} available):")
            print("   These interfaces are suitable with minor considerations")
            for intf in interfaces["available"]:
                print(f"   {option_num:2d}. {intf.name} ({intf.type}) - {intf.admin_status}/{intf.oper_status}")
                if intf.warnings:
                    print(f"       ⚠️  {intf.warnings[0]}")
                options.append(intf)
                option_num += 1
        
        # Caution interfaces (optional)
        if interfaces["caution"]:
            show_caution = input(f"\n🤔 Show {len(interfaces['caution'])} interfaces with warnings? (y/N): ").lower() == 'y'
            if show_caution:
                print(f"\n⚠️  CAUTION - CHECK WARNINGS ({len(interfaces['caution'])} available):")
                print("   These interfaces can be used but require careful consideration")
                for intf in interfaces["caution"]:
                    print(f"   {option_num:2d}. {intf.name} ({intf.type}) - {intf.admin_status}/{intf.oper_status}")
                    for warning in intf.warnings[:2]:  # Show first 2 warnings
                        print(f"       ⚠️  {warning}")
                    options.append(intf)
                    option_num += 1
        
        # Show configured interfaces for reference
        if interfaces["configured"]:
            show_configured = input(f"\n📋 Show {len(interfaces['configured'])} already configured interfaces for reference? (y/N): ").lower() == 'y'
            if show_configured:
                print(f"\n📊 ALREADY CONFIGURED (Reference Only - {len(interfaces['configured'])} interfaces):")
                print("   These interfaces already have L2 service configuration")
                for intf in interfaces["configured"]:
                    print(f"       • {intf.name} ({intf.type}) - {intf.admin_status}/{intf.oper_status}")
        
        if not options:
            print("❌ No suitable interfaces found for BD configuration")
            print("💡 This device may only have uplink/management interfaces")
            return None, None
        
        # Interface selection
        try:
            choice = int(input(f"\nSelect interface [1-{len(options)}] (0 to cancel): ").strip())
            
            if choice == 0:
                print("❌ Interface selection cancelled")
                return None, None
            
            if 1 <= choice <= len(options):
                selected = options[choice - 1]
                
                # Show warnings and get confirmation if needed
                if selected.warnings:
                    print(f"\n⚠️  WARNINGS for {selected.name}:")
                    for warning in selected.warnings:
                        print(f"   • {warning}")
                    
                    print(f"\n💡 RECOMMENDATIONS:")
                    if selected.category == "caution":
                        print("   • This interface has potential issues - consider alternatives")
                        print("   • Verify configuration won't conflict with existing services")
                    
                    confirm = input("\nContinue with this interface despite warnings? (y/N): ").lower() == 'y'
                    if not confirm:
                        print("❌ Interface selection cancelled")
                        return None, None
                
                # Show success message with tips
                print(f"\n✅ Selected: {device_name} - {selected.name}")
                if selected.tips:
                    print(f"💡 {selected.tips[0]}")
                
                return device_name, selected.name
            else:
                print("❌ Invalid selection")
                return None, None
                
        except (ValueError, KeyboardInterrupt):
            print("❌ Interface selection cancelled")
            return None, None
            
    except Exception as e:
        logger.error(f"Error in smart interface selection: {e}")
        print(f"❌ Error in smart interface selection: {e}")
        print("💡 Falling back to manual input")
        return manual_interface_input()


def test_smart_interface_filtering(device_counts: dict) -> None:
    """Test smart interface filtering for troubleshooting and demonstration"""
    try:
        print("\n🎯 Smart Interface Filtering Test")
        print("="*50)
        print("💡 This shows how interfaces are categorized for BD configuration")
        
        # Device selection
        devices = list(device_counts.keys())
        print(f"\n📊 Available Devices ({len(devices)} devices):")
        
        for i, device in enumerate(devices, 1):
            count = device_counts[device]
            print(f"   {i:2d}. {device} ({count} interfaces)")
        
        try:
            choice = int(input(f"\nSelect device [1-{len(devices)}] (0 to cancel): ").strip())
            
            if choice == 0:
                print("❌ Test cancelled")
                return
            
            if 1 <= choice <= len(devices):
                selected_device = devices[choice - 1]
            else:
                print("❌ Invalid selection")
                return
                
        except (ValueError, KeyboardInterrupt):
            print("❌ Test cancelled")
            return
        
        # Run smart filtering test
        print(f"\n🔍 Running Smart Interface Filtering Test on: {selected_device}")
        print("="*60)
        
        try:
            filter_service = SmartInterfaceFilter()
            smart_options = filter_service.get_smart_interface_options(selected_device)
            
            # Show filtering results
            total_interfaces = sum(len(interfaces) for interfaces in smart_options.values())
            total_configurable = len(smart_options['safe']) + len(smart_options['available']) + len(smart_options['caution'])
            print(f"📊 FILTERING RESULTS SUMMARY:")
            print(f"   • Total interfaces processed: {total_interfaces}")
            print(f"   • ✅ Safe: {len(smart_options['safe'])}")
            print(f"   • 🔵 Available: {len(smart_options['available'])}")
            print(f"   • ⚠️  Caution: {len(smart_options['caution'])}")
            print(f"   • 📊 Configured: {len(smart_options['configured'])}")
            print(f"   • 🎯 Total configurable: {total_configurable}")
            
            # Show detailed categorization
            for category, interfaces in smart_options.items():
                if not interfaces:
                    continue
                
                icon = {'safe': '✅', 'available': '🔵', 'caution': '⚠️', 'configured': '📊'}[category]
                print(f"\n{icon} {category.upper()} INTERFACES ({len(interfaces)} interfaces):")
                
                # Show first 10 interfaces in each category
                for i, intf in enumerate(interfaces[:10], 1):
                    print(f"   {i:2d}. {intf.name} ({intf.type}) - {intf.admin_status}/{intf.oper_status}")
                    
                    # Show business logic reasoning
                    if intf.warnings:
                        for warning in intf.warnings[:2]:  # Show first 2 warnings
                            print(f"       ⚠️  {warning}")
                    
                    if intf.tips:
                        print(f"       💡 {intf.tips[0]}")
                    
                    if intf.existing_subinterfaces:
                        subs = ', '.join(intf.existing_subinterfaces[:3])
                        if len(intf.existing_subinterfaces) > 3:
                            subs += f" (+{len(intf.existing_subinterfaces) - 3} more)"
                        print(f"       📊 Existing subinterfaces: {subs}")
                
                if len(interfaces) > 10:
                    print(f"   ... and {len(interfaces) - 10} more {category} interfaces")
            
            # Show business rules testing
            print(f"\n🔍 BUSINESS RULES ANALYSIS:")
            print("-" * 60)
            
            from .smart_filter import InterfaceBusinessRules
            rules = InterfaceBusinessRules()
            
            # Test some sample interfaces from this device
            sample_interfaces = []
            for category_interfaces in smart_options.values():
                sample_interfaces.extend(category_interfaces[:3])
            
            if sample_interfaces:
                print("📋 Sample Interface Rule Analysis:")
                for intf in sample_interfaces[:5]:  # Show first 5
                    print(f"\n   • {intf.name} ({intf.type}):")
                    print(f"     - Category: {intf.category}")
                    print(f"     - Uplink: {rules.is_uplink_interface(intf.name)}")
                    print(f"     - Management: {rules.is_management_interface(intf.name)}")
                    print(f"     - Customer: {rules._is_customer_interface(intf.name)}")
                    
                    if intf.is_uplink or intf.is_management:
                        print(f"     → EXCLUDED from user selection")
                    elif intf.category == "safe":
                        print(f"     → SAFE for BD configuration")
                    elif intf.category == "caution":
                        print(f"     → CAUTION - requires user confirmation")
                    else:
                        print(f"     → {intf.category.upper()}")
            
            # Show filtering effectiveness
            excluded_count = device_counts[selected_device] - total_interfaces
            if excluded_count > 0:
                print(f"\n🛡️  PROTECTION ANALYSIS:")
                print(f"   • {excluded_count} interfaces automatically excluded")
                print(f"   • Likely uplinks, management, or infrastructure interfaces")
                print(f"   • Users protected from accidental misconfiguration")
            
            safe_count = len(smart_options['safe'])
            if safe_count > 0:
                total_visible = len(smart_options['safe']) + len(smart_options['available']) + len(smart_options['caution'])
                noise_reduction = ((total_visible - safe_count) / total_visible * 100) if total_visible > 0 else 0
                print(f"\n⚡ EFFICIENCY ANALYSIS:")
                print(f"   • {safe_count} interfaces marked as safe (best choices)")
                print(f"   • {noise_reduction:.1f}% noise reduction for users")
                print(f"   • Optimal interface selection guidance provided")
            
            print(f"\n✅ Smart Interface Filtering Test Complete!")
            print("💡 This filtering will be applied automatically in BD-Builder")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"❌ Error running smart filtering test: {e}")
            logger.error(f"Smart filtering test error: {e}")
            input("\nPress Enter to continue...")
            
    except Exception as e:
        print(f"❌ Error in smart filtering test: {e}")
        logger.error(f"Smart filtering test error: {e}")


def smart_device_selection_with_shorthand() -> Optional[str]:
    """
    Smart device selection with shorthand support (e.g., 'b-15' for DNAAS-LEAF-B15)
    
    Returns:
        Selected device name or None if cancelled
    """
    try:
        devices = get_devices_with_smart_preview()
        
        if not devices:
            print("❌ No devices with interface data found")
            return None
        
        print(f"\n🎯 Smart Device Selection ({len(devices)} devices available)")
        print("="*70)
        print("💡 You can enter device number OR shorthand (e.g., 'b-15' for DNAAS-LEAF-B15)")
        
        # Display devices in a grid format
        devices_per_row = 3
        for i in range(0, len(devices), devices_per_row):
            row_devices = devices[i:i+devices_per_row]
            
            # Device numbers and names
            for device in row_devices:
                device_num = devices.index(device) + 1
                counts = device['interface_counts']
                status_icon = "🟢" if device['status'] == "online" else "🔴" if device['status'] == "offline" else "🟡"
                shorthand = get_device_shorthand(device['name'])
                
                print(f"{device_num:3d}. {status_icon} {device['name']:<20} ({shorthand})", end="")
                if len(row_devices) > 1:
                    print("  ", end="")
            print()
            
            # Interface counts
            for device in row_devices:
                counts = device['interface_counts']
                count_str = f"✅{counts['safe']} 🔵{counts['available']} 🎯{counts['total_configurable']}"
                print(f"     {count_str:<25}", end="")
                if len(row_devices) > 1:
                    print("  ", end="")
            print()
            print()
        
        # Device selection with shorthand support
        while True:
            choice = input(f"Select device [1-{len(devices)}] or shorthand (0 to cancel): ").strip().lower()
            
            if choice == "0":
                print("❌ Device selection cancelled")
                return None
            
            # Try numeric selection
            if choice.isdigit():
                device_index = int(choice) - 1
                if 0 <= device_index < len(devices):
                    selected_device = devices[device_index]
                    print(f"✅ Selected: {selected_device['name']}")
                    return selected_device['name']
                else:
                    print(f"❌ Invalid number. Please select 1-{len(devices)}")
                    continue
            
            # Try shorthand matching
            matched_device = find_device_by_shorthand(choice, devices)
            if matched_device:
                print(f"✅ Selected by shorthand '{choice}': {matched_device['name']}")
                return matched_device['name']
            else:
                print(f"❌ No device found for '{choice}'. Try number or shorthand like 'b-15'")
                continue
                
    except KeyboardInterrupt:
        print("❌ Device selection cancelled")
        return None


def get_device_shorthand(device_name: str) -> str:
    """Generate shorthand for device name (e.g., DNAAS-LEAF-B15 -> b-15)"""
    if "LEAF-B" in device_name:
        return device_name.replace("DNAAS-LEAF-B", "b-")
    elif "LEAF-A" in device_name:
        return device_name.replace("DNAAS-LEAF-A", "a-")
    elif "LEAF-C" in device_name:
        return device_name.replace("DNAAS-LEAF-C", "c-")
    elif "LEAF-D" in device_name:
        return device_name.replace("DNAAS-LEAF-D", "d-")
    elif "LEAF-F" in device_name:
        return device_name.replace("DNAAS-LEAF-F", "f-")
    elif "SPINE-A" in device_name:
        return device_name.replace("DNAAS-SPINE-A", "sa-")
    elif "SPINE-B" in device_name:
        return device_name.replace("DNAAS-SPINE-B", "sb-")
    elif "SPINE-C" in device_name:
        return device_name.replace("DNAAS-SPINE-C", "sc-")
    elif "SPINE-F" in device_name:
        return device_name.replace("DNAAS-SPINE-F", "sf-")
    elif "SuperSpine" in device_name:
        return device_name.replace("DNAAS-SuperSpine-", "ss-").replace("-NCC", "")
    else:
        # Generic shorthand for other devices
        parts = device_name.split("-")
        if len(parts) >= 2:
            return f"{parts[-2][:1]}-{parts[-1]}"
        return device_name[:6].lower()


def find_device_by_shorthand(shorthand: str, devices: List[Dict]) -> Optional[Dict]:
    """Find device by shorthand input"""
    for device in devices:
        device_shorthand = get_device_shorthand(device['name'])
        if device_shorthand.lower() == shorthand.lower():
            return device
    return None


def enhanced_interface_selection_for_editor() -> Tuple[Optional[str], Optional[str]]:
    """
    Enhanced interface selection for BD Editor with improved CLI presentation
    """
    try:
        # Use enhanced CLI presentation only - no fallbacks
        from .enhanced_cli_display import enhanced_smart_selection_complete
        
        print("\n🎯 Using Enhanced Smart Selection with Improved CLI Presentation...")
        
        result = enhanced_smart_selection_complete()
        
        if result[0] and result[1]:
            return result
        else:
            print("❌ Enhanced selection cancelled")
            return None, None
        
    except ImportError:
        print("❌ Enhanced CLI presentation not available")
        return None, None
    except Exception as e:
        logger.error(f"Error in enhanced interface selection: {e}")
        print(f"❌ Enhanced selection failed: {e}")
        return None, None


def enhanced_interface_selection_for_editor_fallback() -> Tuple[Optional[str], Optional[str]]:
    """
    Fallback enhanced interface selection with original presentation
    """
    try:
        # Smart device selection with shorthand
        selected_device = smart_device_selection_with_shorthand()
        
        if not selected_device:
            return None, None
        
        # Smart interface selection for the chosen device
        device_name, interface_name = get_smart_device_interface_menu(selected_device)
        
        return device_name, interface_name
        
    except Exception as e:
        logger.error(f"Error in fallback interface selection: {e}")
        print(f"❌ Error in smart selection: {e}")
        print("💡 Falling back to manual input")
        return manual_interface_input()


def manual_interface_input() -> Tuple[Optional[str], Optional[str]]:
    """Fallback manual interface input"""
    try:
        print("\n📝 Manual Interface Entry:")
        device_name = input("Enter device name: ").strip()
        if not device_name:
            return None, None
        interface_name = input("Enter interface name: ").strip()
        if not interface_name:
            return None, None
        return device_name, interface_name
    except KeyboardInterrupt:
        return None, None


def interface_discovery_menu() -> None:
    """Interface discovery management menu for CLI"""
    while True:
        print("\n" + "="*50)
        print("🔍 Interface Discovery Management")
        print("="*50)
        print("1. 📊 Show discovery status")
        print("2. 🔄 Refresh interface discovery")
        print("0. 🔙 Back to main menu")
        
        try:
            choice = input("\nSelect option (0-2): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                display_discovery_status()
            elif choice == "2":
                refresh_interface_discovery()
            else:
                print("❌ Invalid choice. Please select 0-2.")
                
        except KeyboardInterrupt:
            break


def display_discovery_status() -> None:
    """Display current interface discovery status with device-specific options"""
    try:
        while True:
            print("\n📊 Interface Discovery Status")
            print("="*35)
            
            discovery = SimpleInterfaceDiscovery()
            device_counts = discovery.get_devices_with_interface_counts()
            
            if not device_counts:
                print("❌ No interface discovery data found")
                print("💡 Run interface discovery to populate data")
                return
            
            total_devices = len(device_counts)
            total_interfaces = sum(device_counts.values())
            
            print(f"📊 Summary:")
            print(f"   • Total devices: {total_devices}")
            print(f"   • Total available interfaces: {total_interfaces}")
            
            print(f"\n📋 Device Interface Counts:")
            for device, count in sorted(device_counts.items()):
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {device}: {count} interfaces")
            
            print(f"\n📋 Options:")
            print("1. 🔍 View specific device interfaces")
            print("2. 📊 View device raw discovery data")
            print("3. 🎯 Test smart interface filtering")
            print("4. 🔄 Refresh status")
            print("0. 🔙 Back")
            
            try:
                choice = input("\nSelect option (0-4): ").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    view_device_interfaces(device_counts)
                elif choice == "2":
                    view_device_raw_data(device_counts)
                elif choice == "3":
                    test_smart_interface_filtering(device_counts)
                elif choice == "4":
                    continue  # Refresh by reloading the menu
                else:
                    print("❌ Invalid choice. Please select 0-4.")
                    
            except KeyboardInterrupt:
                break
        
    except Exception as e:
        print(f"❌ Error getting discovery status: {e}")


def view_device_interfaces(device_counts: dict) -> None:
    """View detailed interface information for a specific device"""
    try:
        print("\n🔍 Device Interface Viewer")
        print("="*30)
        
        if not device_counts:
            print("❌ No devices available")
            return
        
        # Show device list
        device_list = list(device_counts.keys())
        print("📋 Select device to view interfaces:")
        
        for i, device in enumerate(device_list, 1):
            count = device_counts[device]
            status = "✅" if count > 0 else "❌"
            print(f"   {i:2d}. {device} ({count} interfaces) {status}")
        
        print("   0. Cancel")
        
        try:
            choice = input(f"\nSelect device (0-{len(device_list)}): ").strip()
            
            if choice == "0":
                return
            
            device_index = int(choice) - 1
            if 0 <= device_index < len(device_list):
                selected_device = device_list[device_index]
                show_device_interface_details(selected_device)
            else:
                print("❌ Invalid device selection")
                
        except (ValueError, IndexError):
            print("❌ Invalid input")
        
    except Exception as e:
        print(f"❌ Error viewing device interfaces: {e}")


def show_device_interface_details(device_name: str) -> None:
    """Show detailed interface information for a specific device"""
    try:
        print(f"\n🔌 Interface Details: {device_name}")
        print("="*50)
        
        import sqlite3
        
        conn = sqlite3.connect('instance/lab_automation.db')
        cursor = conn.cursor()
        
        # Get detailed interface information
        cursor.execute("""
            SELECT interface_name, interface_type, admin_status, oper_status, 
                   description, bundle_id, is_bundle_member, discovered_at
            FROM interface_discovery 
            WHERE device_name = ?
            ORDER BY 
                CASE interface_type 
                    WHEN 'bundle' THEN 1 
                    WHEN 'physical' THEN 2 
                    WHEN 'subinterface' THEN 3 
                    ELSE 4 
                END,
                interface_name
        """, (device_name,))
        
        interfaces = cursor.fetchall()
        conn.close()
        
        if not interfaces:
            print(f"❌ No interface data found for {device_name}")
            return
        
        print(f"📊 Found {len(interfaces)} interfaces:")
        print()
        
        # Group by interface type
        bundle_interfaces = []
        physical_interfaces = []
        subinterfaces = []
        
        for intf in interfaces:
            if intf[1] == 'bundle':
                bundle_interfaces.append(intf)
            elif intf[1] == 'physical':
                physical_interfaces.append(intf)
            elif intf[1] == 'subinterface':
                subinterfaces.append(intf)
        
        # Display bundle interfaces
        if bundle_interfaces:
            print("🔗 Bundle Interfaces:")
            for intf in bundle_interfaces:
                name, type_, admin, oper, desc, bundle_id, is_member, discovered = intf
                status_icon = "✅" if admin == 'up' else "❌"
                l2_indicator = "(L2)" if "(L2)" in name else ""
                print(f"   {status_icon} {name} {l2_indicator}")
                print(f"      Status: {admin}/{oper}")
                if desc:
                    print(f"      Description: {desc}")
                if bundle_id:
                    print(f"      Bundle ID: {bundle_id}")
        
        # Display physical interfaces
        if physical_interfaces:
            print(f"\n🔌 Physical Interfaces:")
            for intf in physical_interfaces:
                name, type_, admin, oper, desc, bundle_id, is_member, discovered = intf
                status_icon = "✅" if admin == 'up' else "❌"
                print(f"   {status_icon} {name}")
                print(f"      Status: {admin}/{oper}")
                if desc:
                    print(f"      Description: {desc}")
                if is_member:
                    print(f"      Bundle Member: Yes")
        
        # Display subinterfaces
        if subinterfaces:
            print(f"\n📊 Subinterfaces:")
            for intf in subinterfaces:
                name, type_, admin, oper, desc, bundle_id, is_member, discovered = intf
                status_icon = "✅" if admin == 'up' else "❌"
                l2_indicator = "(L2)" if "(L2)" in name else ""
                print(f"   {status_icon} {name} {l2_indicator}")
                print(f"      Status: {admin}/{oper}")
                if desc:
                    print(f"      Description: {desc}")
        
        # Show discovery metadata
        if interfaces:
            last_discovery = interfaces[0][7]  # discovered_at from first interface
            print(f"\n📅 Discovery Information:")
            print(f"   • Last Discovery: {last_discovery}")
            print(f"   • Total Interfaces: {len(interfaces)}")
            print(f"   • Available Interfaces: {len([i for i in interfaces if i[2] == 'up'])}")
        
        input("\nPress Enter to continue...")
        
    except Exception as e:
        print(f"❌ Error showing device details: {e}")


def view_device_raw_data(device_counts: dict) -> None:
    """View raw discovery data for a specific device"""
    try:
        print("\n📊 Device Raw Data Viewer")
        print("="*30)
        
        if not device_counts:
            print("❌ No devices available")
            return
        
        # Show device list
        device_list = list(device_counts.keys())
        print("📋 Select device to view raw data:")
        
        for i, device in enumerate(device_list, 1):
            count = device_counts[device]
            status = "✅" if count > 0 else "❌"
            print(f"   {i:2d}. {device} ({count} interfaces) {status}")
        
        print("   0. Cancel")
        
        try:
            choice = input(f"\nSelect device (0-{len(device_list)}): ").strip()
            
            if choice == "0":
                return
            
            device_index = int(choice) - 1
            if 0 <= device_index < len(device_list):
                selected_device = device_list[device_index]
                show_device_raw_discovery_data(selected_device)
            else:
                print("❌ Invalid device selection")
                
        except (ValueError, IndexError):
            print("❌ Invalid input")
        
    except Exception as e:
        print(f"❌ Error viewing raw data: {e}")


def show_device_raw_discovery_data(device_name: str) -> None:
    """Show raw discovery data for a specific device"""
    try:
        print(f"\n📊 Raw Discovery Data: {device_name}")
        print("="*50)
        
        import sqlite3
        
        conn = sqlite3.connect('instance/lab_automation.db')
        cursor = conn.cursor()
        
        # Get raw discovery data
        cursor.execute("""
            SELECT command_executed, raw_output, command_success, 
                   execution_time_ms, ssh_errors, discovered_at
            FROM discovery_raw_data 
            WHERE device_name = ?
            ORDER BY discovered_at DESC
            LIMIT 3
        """, (device_name,))
        
        raw_data = cursor.fetchall()
        
        if raw_data:
            for i, (command, output, success, exec_time, errors, timestamp) in enumerate(raw_data, 1):
                status = "✅ Success" if success else "❌ Failed"
                print(f"\n🔍 Discovery Attempt {i} ({timestamp}) - {status}")
                print(f"Command: {command}")
                print(f"Execution time: {exec_time}ms")
                
                if errors and errors != '[]':
                    print(f"SSH Errors: {errors}")
                
                if output:
                    print(f"Raw Output ({len(output)} chars):")
                    print("-" * 40)
                    print(output[:800])  # Show first 800 chars
                    if len(output) > 800:
                        print(f"... ({len(output) - 800} more characters)")
                    print("-" * 40)
                else:
                    print("❌ No output received")
        else:
            print(f"❌ No raw discovery data found for {device_name}")
        
        # Get parsed interface data
        cursor.execute("""
            SELECT interface_name, interface_type, admin_status, oper_status,
                   description, parsing_method
            FROM interface_discovery 
            WHERE device_name = ?
            ORDER BY interface_name
        """, (device_name,))
        
        parsed_data = cursor.fetchall()
        
        if parsed_data:
            print(f"\n📋 Parsed Interface Data ({len(parsed_data)} interfaces):")
            for intf_name, intf_type, admin, oper, desc, method in parsed_data:
                status_icon = "✅" if admin == 'up' else "❌"
                print(f"   {status_icon} {intf_name} ({intf_type}) - {admin}/{oper}")
                if desc:
                    print(f"      Description: {desc}")
            
            if parsed_data:
                print(f"\nParsing method used: {parsed_data[0][5] or 'unknown'}")
        else:
            print(f"\n❌ No parsed interface data found for {device_name}")
        
        conn.close()
        
        input("\nPress Enter to continue...")
        
    except Exception as e:
        print(f"❌ Error showing raw discovery data: {e}")


def refresh_interface_discovery() -> None:
    """Refresh interface discovery data"""
    try:
        print("\n🔄 Refreshing Interface Discovery")
        print("="*35)
        print("💡 This will discover interfaces from live devices")
        
        confirm = input("Continue with discovery? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Discovery cancelled")
            return
        
        # Ask user for discovery mode
        print("\n🔍 Discovery Mode Selection:")
        print("1. 🚀 Parallel Discovery (Fast - 10 concurrent connections)")
        print("2. 📡 Sequential Discovery (Slow - one device at a time)")
        print("3. 🧪 Test Discovery (First 5 devices only)")
        print("0. ❌ Cancel")
        
        mode_choice = input("\nSelect discovery mode (0-3): ").strip()
        
        if mode_choice == "0":
            print("❌ Discovery cancelled")
            return
        
        # Actually run the discovery
        discovery = SimpleInterfaceDiscovery()
        
        if mode_choice == "1":
            # Parallel discovery (fast)
            print("🚀 Starting PARALLEL interface discovery...")
            results = discovery.discover_all_devices_parallel(max_workers=10)
            
            successful = len([r for r in results.values() if r.success])
            total_interfaces = sum(len(r.interfaces) for r in results.values() if r.success)
            
        elif mode_choice == "3":
            # Test discovery (first 5 devices)
            devices = discovery._load_devices_from_yaml()[:5]
            print(f"🧪 Testing discovery on first {len(devices)} devices...")
            
            results = {}
            successful = 0
            total_interfaces = 0
            
            for i, device in enumerate(devices, 1):
                print(f"\n  📡 [{i}/{len(devices)}] {device}...")
                try:
                    result = discovery.discover_device_interfaces(device)
                    results[device] = result
                    
                    if result.success:
                        successful += 1
                        total_interfaces += len(result.interfaces)
                        print(f"     ✅ {len(result.interfaces)} interfaces")
                    else:
                        print(f"     ❌ {result.error_message}")
                except Exception as e:
                    print(f"     ❌ Error: {e}")
        
        else:
            # Sequential discovery (slow but reliable)
            devices = discovery._load_devices_from_yaml()
            print(f"📡 Starting sequential discovery on {len(devices)} devices...")
            print("⏰ This will take time - consider using parallel mode")
            
            results = {}
            successful = 0
            total_interfaces = 0
            
            for i, device in enumerate(devices, 1):
                print(f"\n  📡 [{i}/{len(devices)}] {device}...")
                try:
                    result = discovery.discover_device_interfaces(device)
                    results[device] = result
                    
                    if result.success:
                        successful += 1
                        total_interfaces += len(result.interfaces)
                        print(f"     ✅ {len(result.interfaces)} interfaces")
                    else:
                        print(f"     ❌ {result.error_message}")
                except Exception as e:
                    print(f"     ❌ Error: {e}")
        
        print(f"\n✅ Discovery complete:")
        print(f"   • {successful}/{len(results) if results else 0} devices successful")
        print(f"   • {total_interfaces} total interfaces discovered")
        
        if successful > 0:
            print("🎯 Discovery working! Interface data is now available for BD Editor.")
        else:
            print("⚠️  No devices responded. Check device connectivity.")
        
    except Exception as e:
        print(f"❌ Error in discovery refresh: {e}")


def get_device_interface_menu(device_name: str) -> List[str]:
    """Get interface menu for a specific device"""
    try:
        discovery = SimpleInterfaceDiscovery()
        return discovery.get_available_interfaces_for_device(device_name)
    except Exception as e:
        logger.error(f"Error getting interface menu for {device_name}: {e}")
        return []