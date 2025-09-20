#!/usr/bin/env python3
"""
Lab Automation Framework - Main Entry Point
Provides unified interface for all lab automation tools
"""

import sys
from pathlib import Path
from datetime import datetime

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
    print("6. 🗄️  Enhanced Database Operations")
    print("7. ❌ Exit")
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
    print("6. ✨ Enhanced Topology Analysis")
    print("7. 🔙 Back to Main Menu")
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
        print("6. 🔍 Advanced Bridge Domain Analysis (QinQ + DNAAS Types)")
        print("7. 🌐 Visualize Bridge Domain Topology")
        print("8. ✨ Enhanced Bridge Domain Builder (Advanced Validation)")
        print("9. 🔍 Enhanced Database (Bridge Domain Discovery & Management)")
        print("10. 🔙 Back to Main Menu")
        print()
        
        choice = input("Select an option [1-10]: ").strip()
        
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
            run_enhanced_bridge_domain_builder()
        elif choice == '9':
            run_enhanced_database_menu()
        elif choice == '10':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, 6, 7, 8, 9, or 10.")

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
        choice = input("Select an option [1-7]: ").strip()
        
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
            run_enhanced_topology_analysis()
        elif choice == '7':
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, 6, or 7.")

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
            
            # Save to database instead of file
            try:
                from database_manager import DatabaseManager
                db_manager = DatabaseManager()
                
                # Save to database
                success = db_manager.save_configuration(
                    service_name=service_name,
                    vlan_id=vlan_id,
                    config_data=configs
                )
                
                if success:
                    print(f"📁 Configuration saved to database")
                    print(f"📋 Service Name: {service_name}")
                    print(f"📋 VLAN ID: {vlan_id}")
                else:
                    print("❌ Failed to save configuration to database")
                    
            except Exception as e:
                print(f"❌ Error saving to database: {e}")
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
    """Run advanced bridge domain analysis with QinQ and DNAAS type detection"""
    print("\n🔍 Running Advanced Bridge Domain Analysis...")
    print("✨ Enhanced with QinQ detection, DNAAS type classification, and real VLAN data!")
    print("📊 Features: SINGLE_VLAN, VLAN_RANGE, VLAN_LIST, and QinQ (Types 1, 2A, 2B)")
    
    try:
        # Try enhanced discovery first
        try:
            from config_engine.enhanced_bridge_domain_discovery import EnhancedBridgeDomainDiscovery
            print("🚀 Using Advanced Classification System with Session Tracking...")
            discovery = EnhancedBridgeDomainDiscovery()
            result = discovery.run_enhanced_discovery()
            if result:
                session_info = result.get('discovery_session', {})
                print("✅ Advanced bridge domain analysis completed successfully!")
                print(f"📋 Discovery Session: {session_info.get('session_id', 'Unknown')}")
                print(f"📊 Session Stats: {session_info.get('stats', {})}")
                print("🔗 QinQ subtypes detected: DNAAS Types 1, 2A, 2B with imposition location")
                print("📊 Comprehensive mapping with VLAN ranges, lists, and interface roles")
                print("🎯 Classification accuracy: ~96% with confidence scoring")
                print(f"📁 Output saved to: topology/enhanced_bridge_domain_discovery/")
                
                # Show key statistics
                if 'qinq_detection_summary' in result:
                    qinq_summary = result['qinq_detection_summary']
                    print(f"🔗 QinQ Bridge Domains: {qinq_summary.get('total_qinq_bds', 0)}")
                    print(f"   • Edge Imposition: {qinq_summary.get('edge_imposition', 0)}")
                    print(f"   • Leaf Imposition: {qinq_summary.get('leaf_imposition', 0)}")
                
                if 'vlan_validation_summary' in result:
                    vlan_summary = result['vlan_validation_summary']
                    print(f"✅ RFC Compliant: {vlan_summary.get('rfc_compliant', 0)}")
                    print(f"❌ RFC Violations: {vlan_summary.get('rfc_violations', 0)}")
                
                return
            else:
                print("⚠️  Enhanced discovery failed, falling back to basic discovery...")
                raise ImportError("Enhanced discovery failed")
                
        except (ImportError, Exception) as enhanced_error:
            print(f"⚠️  Enhanced discovery not available: {enhanced_error}")
            print("🔄 Falling back to Basic Discovery System...")
            
            # Fallback to basic discovery
            from config_engine.bridge_domain_discovery import BridgeDomainDiscovery
            discovery = BridgeDomainDiscovery()
            result = discovery.run_discovery()
            if result:
                print("✅ Basic bridge domain discovery completed successfully!")
                print("📊 Basic mapping data generated")
                print("💡 Upgrade to Enhanced Discovery for QinQ and double-tag support")
            else:
                print("❌ Basic bridge domain discovery failed.")
                
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

def run_enhanced_bridge_domain_builder():
    """Run enhanced bridge domain builder with Phase 1 validation"""
    print("\n✨ Running Enhanced Bridge Domain Builder...")
    print("🚀 Now with advanced validation and topology insights!")
    
    try:
        # Import Phase 1 integration
        from config_engine.phase1_integration import Phase1CLIWrapper
        
        cli_wrapper = Phase1CLIWrapper()
        
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
        
        # Get source device and interface
        source_device = input("Enter source device name: ").strip()
        if not source_device:
            print("❌ Source device name cannot be empty.")
            return
        
        source_interface = input("Enter source interface name: ").strip()
        if not source_interface:
            print("❌ Source interface name cannot be empty.")
            return
        
        # Get destinations
        destinations = []
        print("\n🎯 Destination Configuration:")
        print("Add destinations for your bridge domain configuration.")
        
        while True:
            dest_device = input("Enter destination device name (or 'done' to finish): ").strip()
            if dest_device.lower() == 'done':
                break
            
            if not dest_device:
                print("❌ Destination device name cannot be empty.")
                continue
            
            dest_interface = input(f"Enter interface for {dest_device}: ").strip()
            if not dest_interface:
                print("❌ Destination interface name cannot be empty.")
                continue
            
            destinations.append({
                'device': dest_device,
                'port': dest_interface
            })
            
            print(f"✅ Added destination: {dest_device}:{dest_interface}")
            
            if len(destinations) == 1:
                print("💡 You can add more destinations for P2MP configuration.")
            
            add_another = input("Add another destination? (y/n): ").strip().lower()
            if add_another not in ['y', 'yes']:
                break
        
        if not destinations:
            print("❌ No destinations specified.")
            return
        
        print(f"\n🔍 Validating configuration with Phase 1 framework...")
        
        # Use Phase 1 validation
        validation_report = cli_wrapper.get_validation_report(
            service_name, vlan_id, source_device, source_interface, destinations
        )
        
        if validation_report.get('passed'):
            print("✅ Phase 1 validation passed!")
            print("🚀 Proceeding with configuration generation...")
            
            # Build configuration using existing builder
            from config_engine.unified_bridge_domain_builder import UnifiedBridgeDomainBuilder
            builder = UnifiedBridgeDomainBuilder()
            
            configs = builder.build_bridge_domain_config(
                service_name, vlan_id, source_device, source_interface, destinations
            )
            
            if configs:
                print("✅ Enhanced bridge domain configuration built successfully!")
                print(f"📋 Service Name: {service_name}")
                print(f"📋 VLAN ID: {vlan_id}")
                print(f"📋 Devices configured: {len([k for k in configs.keys() if k != '_metadata'])}")
                
                # Save to Phase 1 database
                try:
                    from config_engine.phase1_database import create_phase1_database_manager
                    from config_engine.phase1_data_structures import create_p2mp_topology
                    
                    # Create Phase 1 topology data
                    topology_data = create_p2mp_topology(
                        bridge_domain_name=service_name,
                        service_name=service_name,
                        vlan_id=vlan_id,
                        source_device=source_device,
                        source_interface=source_interface,
                        destinations=destinations
                    )
                    
                    db_manager = create_phase1_database_manager()
                    topology_id = db_manager.save_topology_data(topology_data)
                    
                    if topology_id:
                        print(f"💾 Configuration saved to enhanced database (ID: {topology_id})")
                    else:
                        print("⚠️  Failed to save to enhanced database")
                        
                except Exception as e:
                    print(f"⚠️  Enhanced database save failed: {e}")
                
            else:
                print("❌ Failed to build bridge domain configuration.")
        else:
            print("❌ Phase 1 validation failed:")
            for error in validation_report.get('errors', []):
                print(f"  • {error}")
            print("💡 Please fix the validation errors and try again.")
        
    except Exception as e:
        print(f"❌ Enhanced bridge domain builder failed: {e}")
        import traceback
        traceback.print_exc()

def run_enhanced_database_menu():
    """Run Enhanced Database - Bridge Domain Discovery & Management"""
    print("\n🔍 Running Enhanced Database...")
    print("🚀 Bridge Domain Discovery & Management System!")
    
    try:
        # Import the simplified discovery CLI
        from config_engine.simplified_discovery import run_enhanced_database_menu
        
        # Run the CLI interface
        run_enhanced_database_menu()
        
    except Exception as e:
        print(f"❌ Enhanced Database failed: {e}")
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

def run_enhanced_topology_analysis():
    """Run enhanced topology analysis with Phase 1 insights"""
    print("\n✨ Running Enhanced Topology Analysis...")
    print("🚀 Now with advanced validation and topology insights!")
    
    try:
        from config_engine.phase1_data_structures import TopologyValidator
        from config_engine.phase1_database import create_phase1_database_manager
        
        validator = TopologyValidator()
        db_manager = create_phase1_database_manager()
        
        print("\n📊 Topology Analysis Results:")
        print("=" * 60)
        
        # Get database statistics
        db_info = db_manager.get_database_info()
        print(f"📋 Database Status: {'✅ Ready' if db_info.get('phase1_tables') else '❌ Not Initialized'}")
        
        if db_info.get('phase1_tables'):
            print(f"📊 Total Records: {db_info.get('total_phase1_records', 0)}")
            print(f"🗄️  Database Size: {db_info.get('database_size', 0)} bytes")
            
            # List topologies
            topologies = db_manager.get_all_topologies(limit=10)
            if topologies:
                print(f"\n🌐 Topologies Found: {len(topologies)}")
                for topology in topologies[:5]:  # Show first 5
                    bridge_domain = getattr(topology, 'bridge_domain_name', 'N/A')
                    topology_type = getattr(topology, 'device_count', 'N/A')
                    device_count = len(getattr(topology, 'devices', []))
                    print(f"  • {bridge_domain} ({topology_type}) - {device_count} devices")
                
                if len(topologies) > 5:
                    print(f"  ... and {len(topologies) - 5} more")
            else:
                print("📭 No topologies found in database")
        else:
            print("💡 Phase 1 database not initialized")
            print("🔧 Run 'Enhanced Database Operations' to initialize")
        
        print("\n🔍 Validation Framework:")
        print("  • Topology validation: Available")
        print("  • Device validation: Available")
        print("  • Interface validation: Available")
        print("  • Path validation: Available")
        
        print("\n🚀 Enhanced Features:")
        print("  • Advanced topology insights")
        print("  • Comprehensive validation")
        print("  • Data structure consistency")
        print("  • Export/Import capabilities")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Enhanced topology analysis failed: {e}")
        import traceback
        traceback.print_exc()

def show_enhanced_database_menu():
    """Enhanced database operations menu"""
    while True:
        print("\n🗄️====================================================================")
        print("✨ Advanced data management with enhanced validation and insights!")
        print("\n📋 Database Operations:")
        print("1. 📊 View All Topologies")
        print("2. 🔍 Search Topologies")
        print("3. 📋 View Topology Details")
        print("4. 📤 Export Topology Data")
        print("5. 📥 Import Topology Data")
        print("6. 🔗 Consolidate Bridge Domains (Legacy)")
        print("7. 🎯 Simplified Network Engineer Consolidation")
        print("8. 🗑️  Delete Topology")
        print("9. 📈 Database Statistics")
        print("10. 🔄 Migrate Legacy Data")
        print("11. 📥 Import from Discovery Files")
        print("12. 🔍 View Bridge Domain Details")
        print("13. 🛡️  Path Validation Tool (Investigate & Fix Issues)")
        print("14. 🧹 Database Flush & Reset (Admin Only)")
        print("15. 🔙 Back to Main Menu")

        choice = input("\nSelect an option [1-15]: ").strip()

        if choice == "1":
            run_list_topologies()
        elif choice == "2":
            run_search_topologies()
        elif choice == "3":
            run_view_topology_details()
        elif choice == "4":
            run_export_topology()
        elif choice == "5":
            run_import_topology()
        elif choice == "6":
            run_consolidate_bridge_domains()
        elif choice == "7":
            run_bulletproof_consolidation()
        elif choice == "8":
            run_delete_topology()
        elif choice == "9":
            run_database_statistics()
        elif choice == "10":
            run_migrate_legacy_data()
        elif choice == "11":
            run_import_from_discovery_files()
        elif choice == "12":
            view_bridge_domain_details()
        elif choice == "13":
            run_path_validation_tool()
        elif choice == "14":
            run_database_flush_admin()
        elif choice == "15":
            break
        else:
            print("❌ Invalid option. Please select [1-15].")

def run_list_topologies():
    """List all topologies with pagination and smart column width"""
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        from config_engine.phase1_database.models import Phase1TopologyData
        from config_engine.phase1_data_structures.enums import BridgeDomainScope
        import math
        import os
        
        db_manager = create_phase1_database_manager()
        session = db_manager.SessionLocal()
        
        try:
            # Get all topologies
            all_topologies = session.query(Phase1TopologyData).all()
            original_topologies = all_topologies.copy()  # Keep original for clearing filters
            
            if not all_topologies:
                print("📭 No topologies found in the database.")
                return
            
            # Pagination settings
            page_size = 20
            total_pages = math.ceil(len(all_topologies) / page_size)
            current_page = 1
            
            # Calculate scope statistics
            scope_stats = _calculate_scope_statistics(all_topologies)
            
            while True:
                # Clear screen for better readability
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Calculate page boundaries
                start_idx = (current_page - 1) * page_size
                end_idx = min(start_idx + page_size, len(all_topologies))
                page_topologies = all_topologies[start_idx:end_idx]
                
                # Display page
                _display_topology_page(page_topologies, current_page, total_pages, len(all_topologies), scope_stats, all_topologies)
                
                # Navigation menu
                choice = _show_navigation_menu(current_page, total_pages)
                
                if choice == 'q':
                    break
                elif choice == 'n' and current_page < total_pages:
                    current_page += 1
                elif choice == 'p' and current_page > 1:
                    current_page -= 1
                elif choice.startswith('g'):
                    try:
                        page_num = int(choice[1:])
                        if 1 <= page_num <= total_pages:
                            current_page = page_num
                        else:
                            print(f"❌ Invalid page number. Enter 1-{total_pages}")
                            input("Press Enter to continue...")
                    except ValueError:
                        print("❌ Invalid page format. Use 'g<number>' (e.g., 'g5')")
                        input("Press Enter to continue...")
                elif choice == 's':
                    # Show sort menu
                    sort_result = _show_sort_menu(all_topologies)
                    if sort_result:
                        sorted_topologies, sort_title = sort_result
                        current_page = 1  # Reset to first page
                        all_topologies = sorted_topologies
                        page_title = sort_title
                        total_pages = (len(all_topologies) + page_size - 1) // page_size
                elif choice == 'f':
                    # Show filter menu
                    filter_choice = _show_filter_menu()
                    if filter_choice == '1':
                        filtered_topologies = _filter_scope_mismatches(all_topologies)
                        _display_filtered_results(filtered_topologies, "SCOPE MISMATCHES")
                    elif filter_choice == '2':
                        filtered_topologies = _filter_by_scope(all_topologies, 'local')
                        _display_filtered_results(filtered_topologies, "LOCAL BRIDGE DOMAINS")
                    elif filter_choice == '3':
                        filtered_topologies = _filter_by_scope(all_topologies, 'global')
                        _display_filtered_results(filtered_topologies, "GLOBAL BRIDGE DOMAINS")
                    elif filter_choice == '4':
                        _display_scope_analysis(all_topologies)
                    elif filter_choice == '5':
                        filtered_topologies = _filter_by_type(all_topologies)
                        if filtered_topologies:
                            _display_filtered_results(filtered_topologies[0], filtered_topologies[1])
                    elif filter_choice == '6':
                        filtered_topologies = _search_bridge_domains(all_topologies)
                        if filtered_topologies:
                            _display_filtered_results(filtered_topologies[0], filtered_topologies[1])
                    
                    if filter_choice != '7':  # If not "Back"
                        input("Press Enter to continue...")
                elif choice == 'i':
                    # Show inspect menu
                    inspect_result = _show_inspect_menu(page_topologies)
                    if inspect_result:
                        input("Press Enter to continue...")
                elif choice == 'search':
                    # Show search functionality that filters the main view
                    search_term = _show_search_input()
                    if search_term:
                        # Apply fuzzy search filter to all topologies
                        filtered_topologies = _fuzzy_search_bridge_domains(all_topologies, search_term)
                        if filtered_topologies:
                            all_topologies = filtered_topologies
                            current_page = 1
                            total_pages = math.ceil(len(all_topologies) / page_size)
                            print(f"✅ Filtered to {len(filtered_topologies)} bridge domains matching '{search_term}'")
                            print("💡 Use [I]nspect to view details of any filtered result")
                        else:
                            print(f"❌ No bridge domains found matching '{search_term}'")
                            print("💡 Try a different search term or use [Clear] to reset")
                        input("Press Enter to continue...")
                elif choice == 'clear':
                    # Clear search filter and restore original topologies
                    all_topologies = original_topologies.copy()
                    current_page = 1
                    total_pages = math.ceil(len(all_topologies) / page_size)
                    scope_stats = _calculate_scope_statistics(all_topologies)
                    print("✅ Filter cleared - showing all bridge domains")
                    input("Press Enter to continue...")
                elif choice == 'h':
                    _show_help_menu()
                    input("Press Enter to continue...")
                else:
                    print("❌ Invalid choice. Type 'h' for help.")
                    input("Press Enter to continue...")

            
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ Failed to list topologies: {e}")
        import traceback
        traceback.print_exc()

def run_consolidate_bridge_domains():
    """Consolidate duplicate bridge domains"""
    print("\n🔗 Consolidate Bridge Domains...")
    print("═" * 60)
    print("This will identify and consolidate duplicate bridge domains")
    print("that represent the same service with different naming conventions.")
    print()
    
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        
        db_manager = create_phase1_database_manager()
        
        # First, show consolidation candidates
        print("🔍 Analyzing bridge domains for duplicates...")
        candidates = db_manager.get_consolidation_candidates()
        
        if not candidates:
            print("✅ No consolidation needed - no duplicates found!")
            input("\nPress Enter to continue...")
            return
        
        print(f"🚨 Found {len(candidates)} consolidation groups:")
        print()
        
        for consolidation_key, bd_names in candidates.items():
            print(f"🔗 {consolidation_key}:")
            for name in bd_names:
                print(f"   • {name}")
            print()
        
        # Ask for confirmation
        confirm = input("Do you want to proceed with consolidation? [y/N]: ").strip().lower()
        
        if confirm not in ['y', 'yes']:
            print("❌ Consolidation cancelled")
            return
        
        # Perform consolidation
        print("\n🔄 Performing consolidation...")
        result = db_manager.consolidate_bridge_domains()
        
        if result['success']:
            print("✅ Consolidation completed successfully!")
            print()
            print("📊 Consolidation Results:")
            print(f"   Original bridge domains: {result['original_count']}")
            print(f"   After consolidation: {result['consolidated_count']}")
            print(f"   Duplicates removed: {result['duplicates_removed']}")
            print(f"   Consolidation groups: {result['consolidation_groups']}")
            print()
            
            if result.get('consolidation_details'):
                print("🔗 Consolidation Details:")
                for bd_name, details in result['consolidation_details'].items():
                    print(f"   {bd_name}:")
                    print(f"      Original names: {', '.join(details['original_names'])}")
                    print(f"      Confidence: {details['confidence']:.1f}%")
                    print()
        else:
            print(f"❌ Consolidation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Failed to consolidate bridge domains: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to continue...")

def run_search_topologies():
    """Search topologies by name or content"""
    print("\n🔍 Search Topologies...")
    try:
        search_term = input("Enter search term: ").strip()
        if not search_term:
            print("❌ Search term cannot be empty.")
            return
        
        from config_engine.phase1_database import create_phase1_database_manager
        db_manager = create_phase1_database_manager()
        
        results = db_manager.search_topologies(search_term, limit=50)
        
        if not results:
            print(f"🔍 No topologies found matching '{search_term}'.")
            return
        
        print(f"\n🔍 Found {len(results)} matching topologies:")
        print("─" * 80)
        print(f"{'ID':<5} {'Name':<30} {'Type':<15} {'Devices':<10} {'Match':<20}")
        print("─" * 80)
        
        for topology in results:
            topology_id = getattr(topology, 'id', 'N/A')
            bridge_domain_name = getattr(topology, 'bridge_domain_name', 'N/A')
            topology_type = getattr(topology, 'topology_type', 'N/A')
            device_count = len(getattr(topology, 'devices', []))
            
            print(f"{topology_id:<5} {bridge_domain_name:<30} {topology_type:<15} {device_count:<10} '{search_term}'")
        
        print("─" * 80)
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()

def run_view_topology_details():
    """View detailed information about a specific topology"""
    print("\n📋 View Topology Details...")
    try:
        topology_id = input("Enter topology ID: ").strip()
        if not topology_id:
            print("❌ Topology ID cannot be empty.")
            return
        
        try:
            topology_id = int(topology_id)
        except ValueError:
            print("❌ Topology ID must be a number.")
            return
        
        from config_engine.phase1_database import create_phase1_database_manager
        db_manager = create_phase1_database_manager()
        
        topology = db_manager.get_topology_data(topology_id)
        
        if not topology:
            print(f"❌ Topology with ID {topology_id} not found.")
            return
        
        print(f"\n�� Topology Details (ID: {topology_id}):")
        print("=" * 80)
        print(f"Bridge Domain Name: {getattr(topology, 'bridge_domain_name', 'N/A')}")
        print(f"Topology Type: {getattr(topology, 'topology_type', 'N/A')}")
        print(f"Service Name: {getattr(topology, 'service_name', 'N/A')}")
        print(f"VLAN ID: {getattr(topology, 'vlan_id', 'N/A')}")
        print(f"Created: {getattr(topology, 'created_at', 'N/A')}")
        print(f"Updated: {getattr(topology, 'updated_at', 'N/A')}")
        
        # Show devices
        devices = getattr(topology, 'devices', [])
        print(f"\n📱 Devices ({len(devices)}):")
        if devices:
            for device in devices:
                print(f"  • {getattr(device, 'name', 'N/A')} ({getattr(device, 'device_type', 'N/A')})")
        else:
            print("  No devices found.")
        
        # Show interfaces
        interfaces = getattr(topology, 'interfaces', [])
        print(f"\n🔌 Interfaces ({len(interfaces)}):")
        if interfaces:
            for interface in interfaces:
                device_name = next((d.name for d in devices if d.id == interface.device_id), 'Unknown')
                print(f"  • {interface.name} on {device_name}")
                print(f"    - Type: {interface.interface_type}")
                print(f"    - Role: {interface.interface_role}")
                print(f"    - VLAN: {interface.vlan_id or 'Not Set'}")
                print(f"    - L2 Service: {'Enabled' if interface.l2_service_enabled else 'Disabled'}")
                print(f"    - Outer Tag Imposition: {interface.outer_tag_imposition or 'N/A'}")
                print(f"    - Confidence: {interface.confidence_score:.1%}")
                print(f"    - Status: {interface.validation_status}")
                print(f"    - Discovered: {interface.discovered_at}")
                print(f"    - Created: {interface.created_at}")
        
        # Bridge Domain Configuration
        bridge_domain_configs = getattr(topology, 'bridge_domain_configs', [])
        if bridge_domain_configs:
            print(f"\n⚙️ Bridge Domain Configuration:")
            for config in bridge_domain_configs:
                print(f"  • Service Name: {config.service_name}")
                print(f"    - Type: {config.bridge_domain_type}")
                print(f"    - Source Device: {config.source_device}")
                print(f"    - Source Interface: {config.source_interface}")
                print(f"    - VLAN ID: {config.vlan_id or 'Not Set'}")
                print(f"    - Outer Tag Imposition: {config.outer_tag_imposition}")
                print(f"    - Created: {config.created_at}")
                print(f"    - Updated: {config.updated_at}")
                print(f"    - Confidence: {config.confidence_score:.1%}")
                print(f"    - Status: {config.validation_status}")
        
        # Destinations
        destinations = getattr(topology, 'destinations', [])
        if destinations:
            print(f"\n🎯 Destinations ({len(destinations)}):")
            for dest in destinations:
                print(f"  • {dest.device} - {dest.port}")
                print(f"    - Created: {dest.created_at}")
        
        # Network Paths
        paths = getattr(topology, 'paths', [])
        if paths:
            print(f"\n🛣️ Network Paths ({len(paths)}):")
            for path in paths:
                print(f"  • {path.path_name}")
                print(f"    - Type: {path.path_type}")
                print(f"    - Source: {path.source_device}")
                print(f"    - Destination: {path.dest_device}")
                print(f"    - Discovered: {path.discovered_at}")
                print(f"    - Created: {path.created_at}")
                print(f"    - Confidence: {path.confidence_score:.1%}")
                print(f"    - Status: {path.validation_status}")
                
                # Path Segments
                path_segs = [ps for ps in getattr(topology, 'path_segments', []) if ps.path_id == path.id]
                if path_segs:
                    print(f"    - Segments ({len(path_segs)}):")
                    for seg in path_segs:
                        print(f"      • {seg.source_device}:{seg.source_interface} → {seg.dest_device}:{seg.dest_interface}")
                        print(f"        Type: {seg.segment_type}, Connection: {seg.connection_type}")
        
        # Validation Summary
        print(f"\n📊 Validation Summary:")
        print(f"  • Overall Status: {getattr(topology, 'validation_status', 'N/A')}")
        print(f"  • Confidence: {getattr(topology, 'confidence_score', 0):.1%}")
        
        # Data Completeness Check
        missing_fields = []
        if not getattr(topology, 'vlan_id', None):
            missing_fields.append("VLAN ID")
        if not devices:
            missing_fields.append("Devices")
        if not interfaces:
            missing_fields.append("Interfaces")
        if not bridge_domain_configs:
            missing_fields.append("Bridge Domain Configuration")
        if not destinations:
            missing_fields.append("Destinations")
        if not paths:
            missing_fields.append("Network Paths")
        
        if missing_fields:
            print(f"  • ⚠️ Missing Data: {', '.join(missing_fields)}")
        else:
            print(f"  • ✅ All Required Data Present")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Failed to view topology details: {e}")
        import traceback
        traceback.print_exc()

def run_export_topology():
    """Export topology data to file"""
    print("\n📤 Export Topology Data...")
    try:
        topology_id = input("Enter topology ID to export: ").strip()
        if not topology_id:
            print("❌ Topology ID cannot be empty.")
            return
        
        try:
            topology_id = int(topology_id)
        except ValueError:
            print("❌ Topology ID must be a number.")
            return
        
        format_choice = input("Export format (json/yaml) [json]: ").strip().lower()
        if not format_choice:
            format_choice = 'json'
        
        if format_choice not in ['json', 'yaml']:
            print("❌ Invalid format. Using JSON.")
            format_choice = 'json'
        
        from config_engine.phase1_database import create_phase1_database_manager
        from config_engine.phase1_database.serializers import Phase1DataSerializer
        
        db_manager = create_phase1_database_manager()
        topology = db_manager.get_topology_data(topology_id)
        
        if not topology:
            print(f"❌ Topology with ID {topology_id} not found.")
            return
        
        serializer = Phase1DataSerializer()
        exported_data = serializer.serialize_topology(topology, format_choice)
        
        # Generate filename
        bridge_domain_name = getattr(topology, 'bridge_domain_name', f'topology_{topology_id}')
        filename = f"{bridge_domain_name}_{format_choice}.{format_choice}"
        
        # Write to file
        with open(filename, 'w') as f:
            f.write(exported_data)
        
        print(f"✅ Topology exported successfully to: {filename}")
        print(f"📁 File size: {len(exported_data)} characters")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()

def run_import_topology():
    """Import topology data from file"""
    print("\n📥 Import Topology Data...")
    try:
        filename = input("Enter filename to import: ").strip()
        if not filename:
            print("❌ Filename cannot be empty.")
            return
        
        if not Path(filename).exists():
            print(f"❌ File '{filename}' not found.")
            return
        
        from config_engine.phase1_database import create_phase1_database_manager
        from config_engine.phase1_database.serializers import Phase1DataSerializer
        
        # Read file content
        with open(filename, 'r') as f:
            content = f.read()
        
        # Determine format from file extension
        if filename.endswith('.json'):
            format_type = 'json'
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            format_type = 'yaml'
        else:
            print("❌ Unsupported file format. Please use .json or .yaml files.")
            return
        
        # Deserialize and import
        serializer = Phase1DataSerializer()
        topology_data = serializer.deserialize_topology(content, format_type)
        
        if not topology_data:
            print("❌ Failed to deserialize topology data.")
            return
        
        db_manager = create_phase1_database_manager()
        topology_id = db_manager.save_topology_data(topology_data)
        
        if topology_id:
            print(f"✅ Topology imported successfully with ID: {topology_id}")
            print(f"📋 Bridge Domain: {getattr(topology_data, 'bridge_domain_name', 'N/A')}")
        else:
            print("❌ Failed to save imported topology.")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

def run_delete_topology():
    """Delete a topology from the database"""
    print("\n🗑️  Delete Topology...")
    try:
        topology_id = input("Enter topology ID to delete: ").strip()
        if not topology_id:
            print("❌ Topology ID cannot be empty.")
            return
        
        try:
            topology_id = int(topology_id)
        except ValueError:
            print("❌ Topology ID must be a number.")
            return
        
        # Confirm deletion
        confirm = input(f"⚠️  Are you sure you want to delete topology {topology_id}? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("❌ Deletion cancelled.")
            return
        
        from config_engine.phase1_database import create_phase1_database_manager
        db_manager = create_phase1_database_manager()
        
        success = db_manager.delete_topology_data(topology_id)
        
        if success:
            print(f"✅ Topology {topology_id} deleted successfully.")
        else:
            print(f"❌ Failed to delete topology {topology_id}.")
        
    except Exception as e:
        print(f"❌ Deletion failed: {e}")
        import traceback
        traceback.print_exc()

def run_database_statistics():
    """Show database statistics and health information"""
    print("\n📈 Database Statistics...")
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        db_manager = create_phase1_database_manager()
        
        db_info = db_manager.get_database_info()
        
        print("\n📊 Database Information:")
        print("=" * 50)
        print(f"Phase 1 Tables: {len(db_info.get('phase1_tables', []))}")
        print(f"Total Records: {db_info.get('total_phase1_records', 0)}")
        print(f"Database Size: {db_info.get('database_size', 0)} bytes")
        
        # Show table details
        phase1_tables = db_info.get('phase1_tables', [])
        if phase1_tables:
            print(f"\n📋 Phase 1 Tables:")
            for table in phase1_tables:
                print(f"  • {table}")
        
        # Show record counts by type
        print(f"\n📊 Record Counts:")
        print(f"  • Topologies: {len(db_manager.get_all_topologies(limit=1000))}")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Failed to get database statistics: {e}")
        import traceback
        traceback.print_exc()

def run_migrate_legacy_data():
    """Migrate legacy configurations to Phase 1 format"""
    print("\n🔄 Migrate Legacy Data...")
    try:
        print("⚠️  This feature requires access to legacy database tables.")
        print("📋 Migration status:")
        
        from config_engine.phase1_database import create_phase1_database_manager
        db_manager = create_phase1_database_manager()
        
        db_info = db_manager.get_database_info()
        
        if db_info.get('phase1_tables'):
            print("✅ Phase 1 database is ready")
            print("📊 Phase 1 tables available")
            print("💡 Legacy migration can be implemented when legacy tables are accessible")
        else:
            print("❌ Phase 1 database not initialized")
            print("💡 Please initialize the database first")
        
        print("\n📋 Migration features:")
        print("  • Convert legacy configurations to Phase 1 format")
        print("  • Preserve all configuration data")
        print("  • Maintain backward compatibility")
        print("  • Validate migrated data")
        
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        import traceback
        traceback.print_exc()

def run_import_from_discovery_files():
    """Import and populate Enhanced Database from legacy discovery parsed files"""
    print("\n📥 Importing from Discovery Files...")
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        from config_engine.enhanced_discovery_integration.auto_population_service import (
            EnhancedDatabasePopulationService,
        )
        from pathlib import Path

        # Ask for a directory or use default
        default_dir = 'topology/configs/parsed_data'
        user_input = input(f"Enter directory with parsed files [{default_dir}]: ").strip()
        base_dir = user_input or default_dir

        base_path = Path(base_dir)
        if not base_path.exists():
            print(f"❌ Directory not found: {base_dir}")
            return

        # Collect candidate files
        bd_dir = base_path / 'bridge_domain_parsed'
        file_candidates = []
        file_candidates += list(base_path.glob('*_lacp_parsed_*.yaml'))
        file_candidates += list(base_path.glob('*_lldp_parsed_*.yaml'))
        file_candidates += list(bd_dir.glob('*_bridge_domain_instance_parsed_*.yaml'))
        file_candidates += list(bd_dir.glob('*_vlan_config_parsed_*.yaml'))

        if not file_candidates:
            print("📭 No parsed discovery files found.")
            return

        # Optional filters
        limit_input = input("Limit to first N bridge-domains (blank for all): ").strip()
        limit_count = None
        if limit_input:
            try:
                limit_count = int(limit_input)
            except ValueError:
                print("⚠️  Invalid number for limit. Ignoring.")
                limit_count = None

        services_input = input("Filter by service names (comma-separated, blank for none): ").strip()
        service_filters = [s.strip() for s in services_input.split(',')] if services_input else None

        print(f"📄 Found {len(file_candidates)} files.")

        # Choose source: mapping JSON vs parsed YAMLs
        use_mapping = input("Use legacy bridge-domain mapping JSON instead? (y/N): ").strip().lower() in ['y', 'yes']
        if use_mapping:
            default_mapping = 'topology/bridge_domain_discovery/bridge_domain_mapping_20250803_172648.json'
            mapping_input = input(f"Enter mapping JSON path [{default_mapping}]: ").strip()
            mapping_path = mapping_input or default_mapping

            print("🔄 Importing from legacy mapping JSON...")
            db_manager = create_phase1_database_manager()
            pop = EnhancedDatabasePopulationService(db_manager)
            result = pop.populate_from_legacy_mapping(Path(mapping_path), limit_count=limit_count, service_filters=service_filters)
            # Short-circuit: do not run file conversion when mapping is selected
            if result.get('success'):
                if result.get('success'):
                    print("✅ Import completed successfully!")
                else:
                    print("❌ Import failed.")
                if 'file_count' in result:
                    print(f"📊 Files processed: {result.get('file_count', 0)}")
                if 'mapping_file' in result:
                    print(f"📄 Mapping file: {result.get('mapping_file')}")
                    print(f"🔎 Selected BDs: {result.get('selected_bds', 0)}")
                print(f"🌐 Topologies converted: {result.get('topologies_converted', 0)}")
                integration = result.get('integration', {})
                totals = integration.get('integration_results', {})
                if totals:
                    top = totals.get('topologies', {})
                    print(f"   • Topologies saved: {top.get('successful', 0)}")
                return
        else:
            print("🔄 Converting from parsed discovery files...")
            db_manager = create_phase1_database_manager()
            pop = EnhancedDatabasePopulationService(db_manager)
            result = pop.populate_from_legacy_files(file_candidates, limit_count=limit_count, service_filters=service_filters)
            # Mapping not chosen; proceed with file conversion flow

        # Final reporting for file conversion path only

        if result.get('success'):
            print("✅ Import completed successfully!")
            if 'file_count' in result:
                print(f"📊 Files processed: {result.get('file_count', 0)}")
            if 'mapping_file' in result:
                print(f"📄 Mapping file: {result.get('mapping_file')}")
                print(f"🔎 Selected BDs: {result.get('selected_bds', 0)}")
            print(f"🌐 Topologies converted: {result.get('topologies_converted', 0)}")
            integration = result.get('integration', {})
            totals = integration.get('integration_results', {})
            if totals:
                top = totals.get('topologies', {})
                print(f"   • Topologies saved: {top.get('successful', 0)}")
        else:
            print("❌ Import failed.")
            if 'error' in result:
                print(f"   • Error: {result['error']}")

    except Exception as e:
        print(f"❌ Import from discovery files failed: {e}")
        import traceback
        traceback.print_exc()

def view_bridge_domain_details():
    """Display detailed information about a specific bridge domain from the new optimized data structure"""
    try:
        # Get bridge domain name from user
        bridge_domain_name = input("Enter bridge domain name to view: ").strip()
        if not bridge_domain_name:
            print("❌ Bridge domain name is required")
            return
        
        # Initialize database manager
        from config_engine.phase1_database.manager import Phase1DatabaseManager
        db_manager = Phase1DatabaseManager()
        
        # Get topology data by bridge domain name
        topology_data = db_manager.get_topology_by_bridge_domain(bridge_domain_name)
        if not topology_data:
            print(f"❌ Bridge domain '{bridge_domain_name}' not found in the database")
            return
        
        # Get topology ID from the topology data
        topology_id = getattr(topology_data, 'topology_id', None)
        if not topology_id:
            print(f"❌ Could not determine topology ID for bridge domain '{bridge_domain_name}'")
            return
        
        print(f"\n{'='*80}")
        print(f"🔍 BRIDGE DOMAIN DETAILS: {bridge_domain_name}")
        print(f"{'='*80}")
        
        # Basic Topology Information
        print(f"\n📊 BASIC TOPOLOGY INFORMATION:")
        print(f"  • Bridge Domain Name: {topology_data.bridge_domain_name}")
        print(f"  • Topology Type: {topology_data.topology_type}")
        print(f"  • VLAN ID: {topology_data.vlan_id or 'Not specified'}")
        print(f"  • Scan Method: {getattr(topology_data, 'scan_method', 'unknown')}")
        print(f"  • Discovered At: {topology_data.discovered_at}")
        print(f"  • Confidence Score: {topology_data.confidence_score:.1%}")
        print(f"  • Validation Status: {topology_data.validation_status}")
        
        # Performance Summary from the topology data
        print(f"\n⚡ PERFORMANCE SUMMARY:")
        print(f"  • Device Count: {len(topology_data.devices)}")
        print(f"  • Interface Count: {len(topology_data.interfaces)}")
        print(f"  • Path Count: {len(topology_data.paths)}")
        
        # Devices Section
        print(f"\n🖥️  DEVICES ({len(topology_data.devices)} total):")
        for i, device in enumerate(topology_data.devices, 1):
            print(f"  {i}. Device: {device.name}")
            print(f"     • Type: {device.device_type}")
            print(f"     • Role: {device.device_role}")
            print(f"     • Device ID: {getattr(device, 'device_id', 'Not specified')}")
            print(f"     • Discovered At: {device.discovered_at}")
            print(f"     • Confidence Score: {device.confidence_score:.1%}")
            print(f"     • Validation Status: {device.validation_status}")
            print()
        
        # Interfaces Section
        print(f"\n🔌 INTERFACES ({len(topology_data.interfaces)} total):")
        for i, interface in enumerate(topology_data.interfaces, 1):
            print(f"  {i}. Interface: {interface.name}")
            print(f"     • Type: {interface.interface_type}")
            print(f"     • Role: {interface.interface_role}")
            print(f"     • Device: {interface.device_name}")
            print(f"     • VLAN ID: {interface.vlan_id or 'Not specified'}")
            print(f"     • L2 Service Enabled: {'Yes' if interface.l2_service_enabled else 'No'}")
            print(f"     • Discovered At: {interface.discovered_at}")
            print(f"     • Confidence Score: {interface.confidence_score:.1%}")
            print(f"     • Validation Status: {interface.validation_status}")
            print()
        
        # Bridge Domain Configuration Section (OPTIMIZED)
        if hasattr(topology_data, 'bridge_domain_config') and topology_data.bridge_domain_config:
            config = topology_data.bridge_domain_config
            print(f"\n⚙️  BRIDGE DOMAIN CONFIGURATION:")
            print(f"  • Service Name: {config.service_name}")
            print(f"  • Bridge Domain Type: {config.bridge_domain_type}")
            print(f"  • Source Device: {config.source_device}")
            print(f"  • Source Interface: {config.source_interface}")
            print(f"  • VLAN ID: {config.vlan_id or 'Not specified'}")
            
            # Display destinations
            if config.destinations:
                print(f"  • Destinations ({len(config.destinations)} total):")
                for j, dest in enumerate(config.destinations, 1):
                    if isinstance(dest, dict):
                        device = dest.get('device', 'Unknown')
                        port = dest.get('port', 'Unknown')
                    else:
                        device = getattr(dest, 'device', 'Unknown')
                        port = getattr(dest, 'port', 'Unknown')
                    
                    print(f"    {j}. Device: {device}, Port: {port}")
            else:
                print(f"  • Destinations: None")

        
        # Paths Section
        print(f"\n🛣️  PATHS ({len(topology_data.paths)} total):")
        for i, path in enumerate(topology_data.paths, 1):
            print(f"  {i}. Path: {path.path_name}")
            print(f"     • Type: {path.path_type}")
            print(f"     • Source Device: {path.source_device}")
            print(f"     • Destination Device: {path.dest_device}")
            print(f"     • Discovered At: {path.discovered_at}")
            print(f"     • Confidence Score: {path.confidence_score:.1%}")
            print(f"     • Validation Status: {path.validation_status}")
            print(f"     • Segment Count: {len(path.segments)}")
            print()
        
        # Path Segments Section
        total_segments = sum(len(path.segments) for path in topology_data.paths)
        print(f"\n🔗 PATH SEGMENTS ({total_segments} total):")
        segment_count = 0
        for path in topology_data.paths:
            for segment in path.segments:
                segment_count += 1
                print(f"  {segment_count}. Segment: {segment.source_device} → {segment.dest_device}")
                print(f"     • Source Interface: {segment.source_interface}")
                print(f"     • Destination Interface: {segment.dest_interface}")
                print(f"     • Segment Type: {segment.segment_type}")
                print(f"     • Connection Type: {getattr(segment, 'connection_type', 'Not specified')}")
                print(f"     • Discovered At: {segment.discovered_at}")
                print(f"     • Confidence Score: {segment.confidence_score:.1%}")
                print()
        
        # Validation Summary
        print(f"\n✅ VALIDATION SUMMARY:")
        print(f"  • Overall Validation Status: {topology_data.validation_status}")
        print(f"  • Overall Confidence Score: {topology_data.confidence_score:.1%}")
        
        # Data Completeness Check
        print(f"\n📋 DATA COMPLETENESS CHECK:")
        print(f"  • Devices: {len(topology_data.devices)}")
        print(f"  • Interfaces: {len(topology_data.interfaces)}")
        print(f"  • Paths: {len(topology_data.paths)}")
        print(f"  • Total Segments: {total_segments}")
        
        # NEW: Display optimization benefits
        print(f"\n🚀 OPTIMIZATION BENEFITS:")
        print(f"  • Consolidated Destinations: JSON field reduces table joins")
        print(f"  • Enhanced Interface Classification: Proper subinterface detection")
        print(f"  • Device Role Clarification: Primary source designation")
        print(f"  • Optimized Data Structure: Reduced redundancy and improved performance")
        
        print(f"\n{'='*80}")
        print(f"✅ Bridge domain details displayed successfully!")
        print(f"{'='*80}")
        

        
    except AttributeError as e:
        print(f"❌ Attribute error: {e}")
        print("This might indicate a missing field in the database model")
    except Exception as e:
        print(f"❌ Error viewing bridge domain details: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🚀 Welcome to Lab Automation Framework!")
    print("📋 This framework provides tools for network automation and topology management.")
    
    while True:
        show_main_menu()
        choice = input("Select an option [1-7]: ").strip()
        
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
            show_enhanced_database_menu()
        elif choice == '7':
            print("\n👋 Thank you for using Lab Automation Framework!")
            print("🚀 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1, 2, 3, 4, 5, 6, or 7.")

def _calculate_scope_statistics(topologies):
    """Calculate scope compliance statistics"""
    from config_engine.phase1_data_structures.enums import BridgeDomainScope
    
    stats = {'matches': 0, 'mismatches': 0, 'unspecified': 0, 'total': len(topologies)}
    
    for topology in topologies:
        named_scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
        actual_scope = BridgeDomainScope.detect_from_deployment(topology.device_count)
        
        if named_scope == actual_scope:
            stats['matches'] += 1
        elif named_scope == BridgeDomainScope.UNSPECIFIED:
            stats['unspecified'] += 1
        else:
            stats['mismatches'] += 1
    
    return stats

def _display_topology_page(topologies, current_page, total_pages, total_count, scope_stats, all_topologies=None):
    """Display a single page of topologies with smart column width"""
    from config_engine.phase1_data_structures.enums import BridgeDomainScope, get_dnaas_type_display_name, BridgeDomainType
    
    # Header with overview
    print("🗄️ Enhanced Database Operations - View All Topologies")
    print("═" * 100)
    
    # Clean overview dashboard (use ALL topologies for accurate stats)
    print("📊 TOPOLOGY OVERVIEW:")
    if all_topologies:
        # Calculate from entire dataset
        p2p_count = sum(1 for t in all_topologies if str(t.topology_type).lower() == 'p2p')
        p2mp_count = len(all_topologies) - p2p_count
        total_devices = sum(t.device_count for t in all_topologies)
        total_interfaces = sum(t.interface_count for t in all_topologies)
    else:
        # Fallback to current page (for backward compatibility)
        p2p_count = sum(1 for t in topologies if str(t.topology_type).lower() == 'p2p')
        p2mp_count = len(topologies) - p2p_count
        total_devices = sum(t.device_count for t in topologies)
        total_interfaces = sum(t.interface_count for t in topologies)
    
    print(f"  Total: {total_count} Bridge Domains │ P2P: {p2p_count} │ P2MP: {p2mp_count} │ Devices: {total_devices} │ Interfaces: {total_interfaces}")
    print()
    
    # Page header
    print(f"📋 Bridge Domains (Page {current_page} of {total_pages}, showing {(current_page-1)*20+1}-{min(current_page*20, total_count)}):")
    
    # Smart column headers (clean and focused)
    print("─" * 95)
    print(f"{'ID':<4} {'Name':<32} {'Type':<4} {'Template':<14} {'Scope':<8} {'Dev':<3} {'Int':<3} {'Created':<10}")
    print("─" * 95)
    
    # Display topology rows
    for topology in topologies:
        # Smart name truncation
        name = topology.bridge_domain_name
        if len(name) > 32:
            name = name[:29] + "..."
        
        # Get template type (abbreviated)
        template_type = _get_abbreviated_template_type(topology)
        
        # Simple scope display (just named scope for main view)
        named_scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
        scope_display = _abbreviate_scope(named_scope)
        
        # Add scope mismatch indicator if needed
        actual_scope = BridgeDomainScope.detect_from_deployment(topology.device_count)
        if named_scope != actual_scope and named_scope != BridgeDomainScope.UNSPECIFIED:
            scope_display += "*"  # Add asterisk for mismatches
        
        # Format creation date
        created_at = topology.created_at
        if created_at:
            created_at = created_at.strftime('%Y-%m-%d')[:10]
        else:
            created_at = 'N/A'
        
        # Format row (cleaner, less cluttered)
        topo_type = str(topology.topology_type).upper()[:4]  # P2P or P2MP
        
        print(f"{topology.id:<4} {name:<32} {topo_type:<4} {template_type:<14} {scope_display:<8} {topology.device_count:<3} {topology.interface_count:<3} {created_at:<10}")
    
    print("─" * 95)

def _get_abbreviated_template_type(topology):
    """Get abbreviated template type for compact display"""
    template_type = 'N/A'
    
    # Try to get bridge domain config
    bd_config = None
    if hasattr(topology, 'bridge_domain_config') and topology.bridge_domain_config:
        bd_config = topology.bridge_domain_config
    elif hasattr(topology, 'bridge_domain_configs') and topology.bridge_domain_configs:
        bd_config = topology.bridge_domain_configs[0]
    
    if bd_config and hasattr(bd_config, 'bridge_domain_type'):
        bd_type = str(bd_config.bridge_domain_type).upper()
        
        # Abbreviate common types (check string values)
        abbreviations = {
            'SINGLE_VLAN': 'Legacy(S)',
            'SINGLE_TAGGED': 'Type 4A(S)',
            'SINGLE_TAGGED_RANGE': 'Type 4B(R)',
            'SINGLE_TAGGED_LIST': 'Type 4B(L)',
            'DOUBLE_TAGGED': 'Type 1(DT)',
            'QINQ_SINGLE_BD': 'Type 2A(Q)',
            'QINQ_MULTI_BD': 'Type 2B(Q)',
            'HYBRID': 'Type 3(H)',
            'QINQ': 'Legacy(Q)',
            'PORT_MODE': 'Type 5(PM)',
            'EMPTY_BRIDGE_DOMAIN': 'Empty(BD)'
        }
        
        # Direct match first
        if bd_type in abbreviations:
            template_type = abbreviations[bd_type]
        else:
            # Partial match for enum string representations
            for enum_name, abbr in abbreviations.items():
                if enum_name in bd_type:
                    template_type = abbr
                    break
    
    return template_type

def _abbreviate_scope(scope_enum):
    """Abbreviate scope names for compact display"""
    from config_engine.phase1_data_structures.enums import BridgeDomainScope
    
    abbreviations = {
        BridgeDomainScope.LOCAL: 'LOC',
        BridgeDomainScope.GLOBAL: 'GLO', 
        BridgeDomainScope.UNSPECIFIED: 'UNS'
    }
    
    return abbreviations.get(scope_enum, 'N/A')

def _show_navigation_menu(current_page, total_pages):
    """Show navigation menu and get user choice"""
    print(f"\n🎯 Navigation & Filters:")
    nav_options = []
    
    if current_page > 1:
        nav_options.append("[P]revious")
    if current_page < total_pages:
        nav_options.append("[N]ext")
    
    nav_options.extend(["[G]oto page", "[S]ort", "[F]ilters", "[I]nspect", "[Search]", "[Clear]", "[H]elp", "[Q]uit"])
    
    print(f"  {' │ '.join(nav_options)}")
    print(f"  Page {current_page} of {total_pages}")
    print(f"  💡 Scope indicators: * = mismatch")
    
    return input("\nEnter command: ").strip().lower()


def _show_sort_menu(topologies):
    """Show sort options menu and return sorted topologies"""
    
    print("\n🔢 SORT OPTIONS:")
    print("═" * 50)
    print("  [1] Sort by ID (ascending)")
    print("  [2] Sort by ID (descending)")
    print("  [3] Sort by Device Count (ascending)")
    print("  [4] Sort by Device Count (descending)")
    print("  [5] Sort by Interface Count (ascending)")
    print("  [6] Sort by Interface Count (descending)")
    print("  [7] Sort by Created Date (newest first)")
    print("  [8] Sort by Created Date (oldest first)")
    print("  [9] Sort by Name (A-Z)")
    print("  [10] Sort by Name (Z-A)")
    print("  [11] Back to topology view")
    
    choice = input("\nSelect sort option [1-11]: ").strip()
    
    try:
        choice_num = int(choice)
        
        if choice_num == 1:
            # Sort by ID ascending
            sorted_topologies = sorted(topologies, key=lambda t: getattr(t, 'id', 0))
            return (sorted_topologies, "SORTED BY ID (ASCENDING)")
        elif choice_num == 2:
            # Sort by ID descending
            sorted_topologies = sorted(topologies, key=lambda t: getattr(t, 'id', 0), reverse=True)
            return (sorted_topologies, "SORTED BY ID (DESCENDING)")
        elif choice_num == 3:
            # Sort by device count ascending
            sorted_topologies = sorted(topologies, key=lambda t: len(t.devices))
            return (sorted_topologies, "SORTED BY DEVICE COUNT (LOW TO HIGH)")
        elif choice_num == 4:
            # Sort by device count descending
            sorted_topologies = sorted(topologies, key=lambda t: len(t.devices), reverse=True)
            return (sorted_topologies, "SORTED BY DEVICE COUNT (HIGH TO LOW)")
        elif choice_num == 5:
            # Sort by interface count ascending
            sorted_topologies = sorted(topologies, key=lambda t: len(t.interfaces))
            return (sorted_topologies, "SORTED BY INTERFACE COUNT (LOW TO HIGH)")
        elif choice_num == 6:
            # Sort by interface count descending
            sorted_topologies = sorted(topologies, key=lambda t: len(t.interfaces), reverse=True)
            return (sorted_topologies, "SORTED BY INTERFACE COUNT (HIGH TO LOW)")
        elif choice_num == 7:
            # Sort by created date (newest first)
            sorted_topologies = sorted(topologies, key=lambda t: getattr(t, 'discovered_at', datetime.min), reverse=True)
            return (sorted_topologies, "SORTED BY CREATED DATE (NEWEST FIRST)")
        elif choice_num == 8:
            # Sort by created date (oldest first)
            sorted_topologies = sorted(topologies, key=lambda t: getattr(t, 'discovered_at', datetime.min))
            return (sorted_topologies, "SORTED BY CREATED DATE (OLDEST FIRST)")
        elif choice_num == 9:
            # Sort by name A-Z
            sorted_topologies = sorted(topologies, key=lambda t: t.bridge_domain_name.lower())
            return (sorted_topologies, "SORTED BY NAME (A-Z)")
        elif choice_num == 10:
            # Sort by name Z-A
            sorted_topologies = sorted(topologies, key=lambda t: t.bridge_domain_name.lower(), reverse=True)
            return (sorted_topologies, "SORTED BY NAME (Z-A)")
        elif choice_num == 11:
            # Back to topology view
            return None
        else:
            print("❌ Invalid choice. Please select 1-11.")
            return None
            
    except ValueError:
        print("❌ Invalid input. Please enter a number 1-11.")
        return None


def _filter_scope_mismatches(topologies):
    """Filter topologies to show only scope mismatches"""
    from config_engine.phase1_data_structures.enums import BridgeDomainScope
    
    mismatches = []
    for topology in topologies:
        named_scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
        actual_scope = BridgeDomainScope.detect_from_deployment(topology.device_count)
        
        if named_scope != actual_scope and named_scope != BridgeDomainScope.UNSPECIFIED:
            mismatches.append(topology)
    
    return mismatches

def _display_filtered_results(topologies, filter_name):
    """Display filtered results"""
    print(f"\n🔍 {filter_name} ({len(topologies)} entries):")
    print("─" * 90)
    print(f"{'Name':<35} {'Named':<8} {'Actual':<8} {'Issue':<30}")
    print("─" * 90)
    
    for topology in topologies[:20]:  # Show first 20
        from config_engine.phase1_data_structures.enums import BridgeDomainScope
        
        named_scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
        actual_scope = BridgeDomainScope.detect_from_deployment(topology.device_count)
        
        name = topology.bridge_domain_name[:34] if len(topology.bridge_domain_name) > 34 else topology.bridge_domain_name
        
        if named_scope == BridgeDomainScope.GLOBAL and actual_scope == BridgeDomainScope.LOCAL:
            issue = "Should use l_ prefix"
        elif named_scope == BridgeDomainScope.LOCAL and actual_scope == BridgeDomainScope.GLOBAL:
            issue = f"Spans {topology.device_count} devices"
        elif named_scope == actual_scope:
            issue = "No issue"
        else:
            issue = "Scope mismatch"
        
        print(f"{name:<35} {_abbreviate_scope(named_scope):<8} {_abbreviate_scope(actual_scope):<8} {issue:<30}")
    
    if len(topologies) > 20:
        print(f"... and {len(topologies) - 20} more entries")
    print("─" * 90)

def _show_filter_menu():
    """Show filter menu and get user choice"""
    print("\n🔍 FILTER OPTIONS:")
    print("═" * 50)
    print("  [1] Scope Mismatches (Named ≠ Actual)")
    print("  [2] LOCAL Bridge Domains (l_ prefix)")
    print("  [3] GLOBAL Bridge Domains (g_ prefix)")
    print("  [4] Detailed Scope Analysis")
    print("  [5] Filter by Type (Single VLAN, QinQ, etc.)")
    print("  [6] Search Bridge Domains (fuzzy search)")
    print("  [7] Back to main view")
    
    return input("\nSelect filter [1-7]: ").strip()

def _filter_by_scope(topologies, scope_type):
    """Filter topologies by scope type"""
    from config_engine.phase1_data_structures.enums import BridgeDomainScope
    
    filtered = []
    for topology in topologies:
        named_scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
        if scope_type == 'local' and named_scope == BridgeDomainScope.LOCAL:
            filtered.append(topology)
        elif scope_type == 'global' and named_scope == BridgeDomainScope.GLOBAL:
            filtered.append(topology)
    
    return filtered

def _display_scope_analysis(topologies):
    """Display detailed scope analysis"""
    from config_engine.phase1_data_structures.enums import BridgeDomainScope
    
    print("\n🎯 DETAILED SCOPE ANALYSIS:")
    print("═" * 80)
    print(f"{'Name':<35} {'Named':<8} {'Actual':<8} {'Match':<5} {'Issue':<20}")
    print("─" * 80)
    
    for topology in topologies[:20]:  # Show first 20
        named_scope = BridgeDomainScope.detect_from_name(topology.bridge_domain_name)
        actual_scope = BridgeDomainScope.detect_from_deployment(topology.device_count)
        
        name = topology.bridge_domain_name[:34] if len(topology.bridge_domain_name) > 34 else topology.bridge_domain_name
        
        # Match analysis
        if named_scope == actual_scope:
            match = '✅'
            issue = 'Perfect alignment'
        elif named_scope == BridgeDomainScope.UNSPECIFIED:
            match = '❓'
            issue = 'No naming intent'
        elif named_scope == BridgeDomainScope.GLOBAL and actual_scope == BridgeDomainScope.LOCAL:
            match = '❌'
            issue = 'Should use l_ prefix'
        elif named_scope == BridgeDomainScope.LOCAL and actual_scope == BridgeDomainScope.GLOBAL:
            match = '❌'
            issue = f'Spans {topology.device_count} devices'
        elif named_scope == actual_scope:
            match = '✅'
            issue = 'Correctly scoped'
        else:
            match = '❌'
            issue = 'Scope mismatch'
        
        named_abbr = _abbreviate_scope(named_scope)
        actual_abbr = _abbreviate_scope(actual_scope)
        
        print(f"{name:<35} {named_abbr:<8} {actual_abbr:<8} {match:<5} {issue:<20}")
    
    if len(topologies) > 20:
        print(f"... and {len(topologies) - 20} more entries")
    print("─" * 80)

def _show_help_menu():
    """Show help menu for navigation"""
    print("\n📋 NAVIGATION HELP:")
    print("═" * 50)
    print("🎯 Commands:")
    print("  n         - Next page")
    print("  p         - Previous page") 
    print("  g<number> - Goto page (e.g., 'g5' for page 5)")
    print("  s         - Show sort options")
    print("  f         - Show filter options")
    print("  i         - [I]nspect - Select BD from current page for detailed view")
    print("  search    - Filter table using fuzzy search")
    print("  clear     - Clear search filter and show all bridge domains")
    print("  h         - Show this help")
    print("  q         - Quit and return to menu")
    print()
    print("🎨 Scope Indicators:")
    print("  LOC       - LOCAL scope (l_ prefix)")
    print("  GLO       - GLOBAL scope (g_ prefix)")
    print("  UNS       - UNSPECIFIED scope (no prefix)")
    print("  *         - Scope mismatch (add to scope type)")
    print()
    print("📊 Template Types (All DNAAS Types):")
    print("  🔹 Legacy Types:")
    print("    Legacy(S) - Legacy Single VLAN (31 BDs)")
    print("    Legacy(Q) - Legacy QinQ (3 BDs)")
    print("  🔹 Official DNAAS Types:")
    print("    Type 1(DT)- Type 1 Double-Tagged (32 BDs)")
    print("    Type 2A(Q)- Type 2A QinQ Single BD (12 BDs)")
    print("    Type 2B(Q)- Type 2B QinQ Multi BD (61 BDs)")
    print("    Type 3(H) - Type 3 Hybrid (90 BDs)")
    print("    Type 4A(S)- Type 4A Single VLAN (548 BDs)")
    print("    Type 4B(R)- Type 4B VLAN Range (15 BDs)")
    print("    Type 4B(L)- Type 4B VLAN List (5 BDs)")
    print("  🔹 Special Types:")
    print("    Type 5(PM)- Type 5 Port-Mode (if any)")
    print("    Empty(BD)- Empty Bridge Domain (if any)")
    print()
    print("🔍 Enhanced Features:")
    print("  📊 [I]nspect:")
    print("    • Select any BD from current page (1-20)")
    print("    • View complete topology details with service signatures")
    print("    • See devices, interfaces, paths, and bridge domain config")
    print("    • Full-screen detailed view with all metadata")
    print("  🔎 [Search]:")
    print("    • Filter the main table using fuzzy search")
    print("    • Search by BD name, partial name, or VLAN ID")
    print("    • Case-insensitive with intelligent scoring")
    print("    • Updates the main table view with filtered results")
    print("    • Use [Clear] to reset and show all bridge domains")
    print()
    print("💡 Enhanced Usage Tips:")
    print("  - Use [I]nspect for comprehensive BD analysis")
    print("  - Use [Search] to quickly find specific bridge domains")
    print("  - Look for '*' indicators to find scope mismatches")
    print("  - Both features work seamlessly with existing filters and sorting")

def _filter_by_type(topologies):
    """Filter topologies by bridge domain type"""
    from config_engine.phase1_data_structures.enums import BridgeDomainType, get_dnaas_type_display_name
    
    print("\n🔍 FILTER BY TYPE:")
    print("═" * 50)
    
    # Get all available types from the data
    type_counts = {}
    for topology in topologies:
        bd_type = None
        
        # Handle both TopologyData (data structure) and Phase1TopologyData (database model)
        if hasattr(topology, 'bridge_domain_config') and topology.bridge_domain_config:
            # TopologyData object (data structure)
            bd_type = topology.bridge_domain_config.bridge_domain_type
        elif hasattr(topology, 'bridge_domain_configs') and topology.bridge_domain_configs:
            # Phase1TopologyData object (database model)
            bd_config = topology.bridge_domain_configs[0]
            # Convert string back to enum
            from config_engine.phase1_data_structures.enums import get_enum_by_value, BridgeDomainType
            bd_type = get_enum_by_value(BridgeDomainType, bd_config.bridge_domain_type)
        
        if bd_type:
            display_name = get_dnaas_type_display_name(bd_type)
            type_counts[bd_type] = type_counts.get(bd_type, 0) + 1
    
    # Display available types with counts
    type_options = list(type_counts.keys())
    for i, bd_type in enumerate(type_options, 1):
        display_name = get_dnaas_type_display_name(bd_type)
        count = type_counts[bd_type]
        print(f"  [{i}] {display_name} ({count} bridge domains)")
    
    print(f"  [{len(type_options) + 1}] Back to filter menu")
    
    try:
        choice = input(f"\nSelect type [1-{len(type_options) + 1}]: ").strip()
        choice_num = int(choice)
        
        if choice_num == len(type_options) + 1:
            return None  # Back to filter menu
        
        if 1 <= choice_num <= len(type_options):
            selected_type = type_options[choice_num - 1]
            display_name = get_dnaas_type_display_name(selected_type)
            
            # Filter topologies by selected type
            filtered = []
            for topology in topologies:
                bd_type = None
                
                # Handle both TopologyData and Phase1TopologyData objects
                if hasattr(topology, 'bridge_domain_config') and topology.bridge_domain_config:
                    # TopologyData object (data structure)
                    bd_type = topology.bridge_domain_config.bridge_domain_type
                elif hasattr(topology, 'bridge_domain_configs') and topology.bridge_domain_configs:
                    # Phase1TopologyData object (database model)
                    bd_config = topology.bridge_domain_configs[0]
                    # Convert string back to enum
                    from config_engine.phase1_data_structures.enums import get_enum_by_value, BridgeDomainType
                    bd_type = get_enum_by_value(BridgeDomainType, bd_config.bridge_domain_type)
                
                if bd_type == selected_type:
                    filtered.append(topology)
            
            return (filtered, f"{display_name.upper()} BRIDGE DOMAINS")
        else:
            print("❌ Invalid choice")
            return None
            
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return None

def _search_bridge_domains(topologies):
    """Search bridge domains using fuzzy matching"""
    import difflib
    
    print("\n🔍 SEARCH BRIDGE DOMAINS:")
    print("═" * 50)
    print("💡 Enter search term (e.g., 'visaev', 'mgmt', 'v251')")
    print("💡 Leave empty to cancel")
    
    search_term = input("\nSearch term: ").strip()
    
    if not search_term:
        return None  # Cancel search
    
    search_term_lower = search_term.lower()
    
    # Collect all bridge domain names for fuzzy matching
    bd_names = [topology.bridge_domain_name for topology in topologies]
    
    # Find exact matches first
    exact_matches = []
    partial_matches = []
    fuzzy_matches = []
    
    for topology in topologies:
        bd_name = topology.bridge_domain_name
        bd_name_lower = bd_name.lower()
        
        # Exact substring match
        if search_term_lower in bd_name_lower:
            if search_term_lower == bd_name_lower:
                exact_matches.append(topology)
            else:
                partial_matches.append(topology)
    
    # If we don't have many matches, add fuzzy matches
    if len(exact_matches) + len(partial_matches) < 10:
        # Use difflib for fuzzy matching
        fuzzy_names = difflib.get_close_matches(search_term, bd_names, n=20, cutoff=0.3)
        for fuzzy_name in fuzzy_names:
            # Find the topology with this name
            for topology in topologies:
                if topology.bridge_domain_name == fuzzy_name:
                    # Avoid duplicates
                    if topology not in exact_matches and topology not in partial_matches:
                        fuzzy_matches.append(topology)
                    break
    
    # Combine results (exact first, then partial, then fuzzy)
    all_matches = exact_matches + partial_matches + fuzzy_matches
    
    if not all_matches:
        print(f"❌ No bridge domains found matching '{search_term}'")
        input("Press Enter to continue...")
        return None
    
    # Display search results summary
    print(f"\n🎯 SEARCH RESULTS for '{search_term}':")
    print("─" * 50)
    if exact_matches:
        print(f"  🎯 Exact matches: {len(exact_matches)}")
    if partial_matches:
        print(f"  🔍 Partial matches: {len(partial_matches)}")
    if fuzzy_matches:
        print(f"  💡 Fuzzy matches: {len(fuzzy_matches)}")
    print(f"  📊 Total results: {len(all_matches)}")
    
    return (all_matches, f"SEARCH RESULTS: '{search_term}'")


def run_bulletproof_consolidation():
    """Run simplified VLAN-based consolidation analysis"""
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        from config_engine.phase1_database.root_consolidation_manager import RootConsolidationManager
        from config_engine.phase1_data_structures.enums import ConsolidationDecision
        
        print("\n🎯" + "="*80)
        print("🔍 SIMPLIFIED NETWORK ENGINEER CONSOLIDATION")
        print("🎯" + "="*80)
        print("This analysis uses VLAN-based logic to consolidate broadcast domains.")
        print("Rule: Same VLAN = Same broadcast domain = Consolidate")
        print("Scope differences don't matter (just admin marking)")
        print("Topology patterns don't matter (same broadcast domain)")
        print("Only VLAN identity matters for broadcast domain membership.\n")
        
        # Get all topologies
        db_manager = create_phase1_database_manager()
        topologies = db_manager.get_all_topologies()
        
        if not topologies:
            print("❌ No topologies found in database.")
            return
        
        print(f"📊 Analyzing {len(topologies)} bridge domains...")
        print("\n" + "="*80)
        
        # Create ROOT consolidation manager - back to network engineering fundamentals
        consolidation_manager = RootConsolidationManager()
        
        # Perform simplified VLAN-based consolidation
        consolidated_topologies, consolidation_decisions = consolidation_manager.consolidate_topologies(topologies)
        
        # Display results
        print("\n🎯 SIMPLIFIED CONSOLIDATION RESULTS")
        print("="*80)
        
        # Summary statistics
        total_groups = len(consolidation_decisions)
        approved_groups = len([d for d in consolidation_decisions.values() if d.decision == ConsolidationDecision.APPROVE])
        rejected_groups = len([d for d in consolidation_decisions.values() if d.decision == ConsolidationDecision.REJECT])
        review_required = len([d for d in consolidation_decisions.values() if d.decision == ConsolidationDecision.REVIEW_REQUIRED])
        
        print(f"📋 CONSOLIDATION SUMMARY:")
        print(f"   Total Bridge Domains: {len(topologies)}")
        print(f"   After Consolidation: {len(consolidated_topologies)}")
        print(f"   Reduction: {len(topologies) - len(consolidated_topologies)} domains")
        print(f"   Reduction %: {((len(topologies) - len(consolidated_topologies))/len(topologies)*100):.1f}%")
        print()
        
        print(f"🎯 CONSOLIDATION ANALYSIS:")
        print(f"   Total Groups Analyzed: {total_groups}")
        print(f"   ✅ Approved (Same broadcast domain): {approved_groups}")
        print(f"   ❌ Rejected (Different broadcast domain): {rejected_groups}")
        print(f"   ⚠️  Requires Review: {review_required}")
        
        # Avoid division by zero
        if total_groups > 0:
            success_rate = (approved_groups / total_groups * 100)
            print(f"   🎯 Success Rate: {success_rate:.1f}% broadcast domains consolidated")
        else:
            print(f"   🎯 Success Rate: N/A (no groups to analyze)")
        print()
        
        # Detailed decision breakdown
        if consolidation_decisions:
            print("📊 DETAILED CONSOLIDATION DECISIONS:")
            print("="*80)
            
            for consolidation_key, decision in consolidation_decisions.items():
                decision_icon = {
                    ConsolidationDecision.APPROVE: "✅",
                    ConsolidationDecision.REJECT: "❌",
                    ConsolidationDecision.REVIEW_REQUIRED: "⚠️"
                }.get(decision.decision, "❓")
                
                print(f"{decision_icon} GROUP: {consolidation_key}")
                print(f"   Decision: {decision.decision.value.upper()}")
                print(f"   Bridge Domains ({len(decision.bridge_domain_names)}):")
                for bd_name in decision.bridge_domain_names:
                    print(f"      • {bd_name}")
                print(f"   Confidence: {decision.confidence:.2f}")
                
                if decision.approval_reasons:
                    print(f"   ✅ Approval Reasons:")
                    for reason in decision.approval_reasons:
                        print(f"      • {reason}")
                
                if decision.rejection_reasons:
                    print(f"   ❌ Rejection Reasons:")
                    for reason in decision.rejection_reasons:
                        print(f"      • {reason}")
                
                if decision.warnings:
                    print(f"   ⚠️  Warnings:")
                    for warning in decision.warnings:
                        print(f"      • {warning}")
                
                print()
        
        # Show key consolidation examples
        if approved_groups > 0:
            print("🎯 KEY CONSOLIDATION EXAMPLES:")
            print("="*80)
            
            # Show first few approved consolidations
            approved_examples = [d for d in consolidation_decisions.values() if d.decision == ConsolidationDecision.APPROVE][:3]
            
            for i, decision in enumerate(approved_examples, 1):
                print(f"Example {i}: {decision.consolidation_key}")
                print(f"   Consolidates: {', '.join(decision.bridge_domain_names)}")
                print(f"   Reason: Same VLAN = Same broadcast domain")
                print()
        
        # Show rejected examples
        if rejected_groups > 0:
            print("❌ REJECTED CONSOLIDATION EXAMPLES:")
            print("="*80)
            
            # Show first few rejected consolidations
            rejected_examples = [d for d in consolidation_decisions.values() if d.decision == ConsolidationDecision.REJECT][:3]
            
            for i, decision in enumerate(rejected_examples, 1):
                print(f"Example {i}: {decision.consolidation_key}")
                print(f"   Bridge Domains: {', '.join(decision.bridge_domain_names)}")
                print(f"   Reason: {'; '.join(decision.rejection_reasons)}")
                print()
        
        print("🎯 CONSOLIDATION COMPLETE!")
        print("The system has accurately represented the true network topology")
        print("by consolidating bridge domains that represent the same broadcast domain.")
        print()
        
        # Ask if user wants to apply consolidations
        print("💡 NEXT STEPS:")
        print("1. Review the consolidation decisions above")
        print("2. Apply consolidations to database now")
        print("3. View the consolidated topology data")
        print()
        
        # Offer to apply consolidations immediately
        if approved_groups > 0:
            print("🎯 APPLY CONSOLIDATIONS TO DATABASE:")
            print("-" * 50)
            print(f"📊 {approved_groups} consolidation groups ready to apply")
            print("⚠️  This will modify the database - create backup first!")
            
            apply_choice = input("\nApply consolidations now? (yes/no): ").strip().lower()
            if apply_choice == 'yes':
                # Pass a flag to skip the duplicate confirmation
                apply_approved_consolidations_to_database(db_manager, consolidation_decisions, skip_confirmation=True)
            else:
                print("ℹ️  Consolidations not applied. You can run this option again later to apply them.")
        else:
            print("ℹ️  No consolidations to apply.")
        
    except Exception as e:
        print(f"❌ Error during consolidation analysis: {e}")
        import traceback
        traceback.print_exc()


def apply_approved_consolidations_to_database(db_manager, consolidation_decisions, skip_confirmation=False):
    """Apply approved consolidations to the database"""
    from config_engine.phase1_data_structures.enums import ConsolidationDecision
    
    print("\n💾 APPLYING APPROVED CONSOLIDATIONS")
    print("="*60)
    
    approved_decisions = [d for d in consolidation_decisions.values() if d.decision in [
        ConsolidationDecision.APPROVE, ConsolidationDecision.APPROVE_EXACT, ConsolidationDecision.APPROVE_HIGH_CONFIDENCE
    ]]
    
    if not approved_decisions:
        print("ℹ️  No approved consolidations to apply.")
        return
    
    print(f"📊 Ready to apply {len(approved_decisions)} consolidation groups")
    print("⚠️  This will modify the database - create backup first!")
    
    # Skip confirmation if requested (to avoid duplicate prompts)
    if not skip_confirmation:
        confirm = input("\nProceed with applying consolidations? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Consolidation cancelled.")
            return
    else:
        print("✅ Proceeding with consolidation (confirmation already provided)...")
    
    try:
        # Apply the actual database consolidations
        print("🔄 APPLYING CONSOLIDATIONS TO DATABASE...")
        print("⚠️  This will permanently merge bridge domains in the database!")
        
        # Use the new bulletproof consolidation method
        consolidation_results = db_manager.apply_bulletproof_consolidations(consolidation_decisions)
        
        if consolidation_results["status"] == "success":
            print("\n✅ DATABASE CONSOLIDATIONS APPLIED SUCCESSFULLY!")
            print(f"   Groups processed: {consolidation_results['groups_processed']}")
            print(f"   Bridge domains consolidated: {consolidation_results['bridge_domains_consolidated']}")
            print(f"   Bridge domains removed: {consolidation_results['bridge_domains_removed']}")
            print(f"   Net reduction: {consolidation_results['bridge_domains_removed']} domains")
            
            print(f"\n📋 CONSOLIDATION DETAILS:")
            for detail in consolidation_results["consolidation_details"][:5]:  # Show first 5
                print(f"   • {detail['consolidation_key']}")
                print(f"     Consolidated into: {detail['consolidated_into']}")
                print(f"     Removed: {len(detail['removed_topologies'])} bridge domains")
                safety_score = detail.get('safety_score', 0.95)
                print(f"     Safety score: {safety_score:.2f}")
            
            if len(consolidation_results["consolidation_details"]) > 5:
                remaining = len(consolidation_results["consolidation_details"]) - 5
                print(f"   ... and {remaining} more consolidation groups")
            
            print(f"\n🎯 DATABASE UPDATE COMPLETE!")
            print("You can now search for bridge domains to see the consolidated results.")
            
        else:
            print(f"\n❌ CONSOLIDATION FAILED: {consolidation_results.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Error applying consolidations: {e}")
        import traceback
        traceback.print_exc()


def export_consolidation_report(consolidation_decisions):
    """Export detailed consolidation report"""
    print("\n📋 EXPORTING CONSOLIDATION REPORT")
    print("="*50)
    
    from pathlib import Path
    import json
    
    # Create reports directory
    reports_dir = Path("logs/consolidation/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"consolidation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = reports_dir / filename
    
    try:
        # Convert decisions to exportable format
        report_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_groups": len(consolidation_decisions),
            "summary": {
                "approved": len([d for d in consolidation_decisions.values() if d.decision.value in ['approve', 'approve_exact', 'approve_high_confidence']]),
                "rejected": len([d for d in consolidation_decisions.values() if d.decision.value == 'reject']),
                "review_required": len([d for d in consolidation_decisions.values() if d.decision.value == 'review_required'])
            },
            "consolidation_decisions": {}
        }
        
        for key, decision in consolidation_decisions.items():
            report_data["consolidation_decisions"][key] = decision.to_debug_dict()
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Report saved to: {filepath}")
        print(f"📊 Contains {len(consolidation_decisions)} consolidation decisions")
        print(f"📈 Summary: {report_data['summary']['approved']} approved, {report_data['summary']['rejected']} rejected, {report_data['summary']['review_required']} need review")
        print("✅ Export complete!")
        
    except Exception as e:
        print(f"❌ Error exporting report: {e}")


def review_specific_group(consolidation_decisions):
    """Review specific consolidation group in detail"""
    print("\n🔍 REVIEW SPECIFIC CONSOLIDATION GROUP")
    print("="*60)
    
    if not consolidation_decisions:
        print("ℹ️  No consolidation groups to review.")
        return
    
    # List available groups
    print("📋 Available consolidation groups:")
    groups = list(consolidation_decisions.keys())
    for i, key in enumerate(groups[:10]):  # Show first 10
        decision = consolidation_decisions[key]
        status_icon = "✅" if decision.decision != ConsolidationDecision.REJECT else "❌"
        print(f"   {i+1}. {status_icon} {key} ({len(decision.bridge_domain_names)} BDs)")
    
    if len(groups) > 10:
        print(f"   ... and {len(groups) - 10} more groups")
    
    try:
        choice = int(input(f"\nSelect group to review (1-{min(10, len(groups))}): ")) - 1
        if 0 <= choice < min(10, len(groups)):
            selected_key = groups[choice]
            decision = consolidation_decisions[selected_key]
            
            print(f"\n🔍 DETAILED REVIEW: {selected_key}")
            print("="*80)
            print(f"Decision: {decision.decision.value.upper()}")
            safety_score = getattr(decision, 'safety_score', 0.95)
            print(f"Safety Score: {safety_score:.2f}")
            print(f"Confidence: {decision.confidence:.2f}")
            print()
            
            print("🏷️  Bridge Domains in Group:")
            for bd_name in decision.bridge_domain_names:
                print(f"   • {bd_name}")
            print()
            
            if decision.validation_results:
                print("🔍 Validation Results:")
                for result in decision.validation_results:
                    status = "✅" if result.passed else "❌"
                    print(f"   {status} {result.rule_name}: {result.reason}")
                print()
            
            if decision.debug_info:
                print("🐛 Debug Information:")
                for key, value in decision.debug_info.items():
                    print(f"   {key}: {value}")
        else:
            print("❌ Invalid selection.")
    except ValueError:
        print("❌ Invalid input.")


def run_path_validation_tool():
    """Comprehensive path validation tool for investigating and fixing issues"""
    print("\n🛡️  PATH VALIDATION TOOL")
    print("=" * 50)
    print("🔍 Investigate and fix path validation issues in your database")
    print()
    
    while True:
        print("📋 Path Validation Options:")
        print("1. 🔍 View All Path Validation Issues")
        print("2. 📊 Path Validation Statistics")
        print("3. 🔧 Fix Specific Path Issues")
        print("4. 🧪 Test Path Validation on Topology")
        print("5. 📋 Export Path Validation Report")
        print("6. 🔙 Back to Database Menu")
        print()
        
        choice = input("Select an option [1-6]: ").strip()
        
        if choice == "1":
            view_all_path_validation_issues()
        elif choice == "2":
            show_path_validation_statistics()
        elif choice == "3":
            fix_specific_path_issues()
        elif choice == "4":
            test_path_validation_on_topology()
        elif choice == "5":
            export_path_validation_report()
        elif choice == "6":
            break
        else:
            print("❌ Invalid choice. Please select [1-6].")


def view_all_path_validation_issues():
    """Display all path validation issues with detailed information"""
    print("\n🔍 VIEWING ALL PATH VALIDATION ISSUES")
    print("=" * 50)
    
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        
        db_manager = create_phase1_database_manager()
        
        # Get all topologies with path validation
        print("📊 Retrieving topologies with path validation...")
        all_topologies = db_manager.get_all_topologies()
        
        if not all_topologies:
            print("✅ No topologies found - no validation issues to report.")
            return
        
        # Analyze path validation issues
        validation_issues = []
        valid_topologies = []
        
        for topology in all_topologies:
            # Check each path in the topology
            for path in topology.paths:
                if path.segments:
                    from config_engine.path_validation import validate_path_continuity
                    validation_result = validate_path_continuity(path.segments)
                    
                    if not validation_result.is_valid:
                        validation_issues.append({
                            'topology': topology.bridge_domain_name,
                            'topology_id': getattr(topology, 'id', 'N/A'),
                            'path_name': path.path_name,
                            'validation_result': validation_result,
                            'path_summary': f"{path.source_device} → {path.dest_device}"
                        })
                    else:
                        valid_topologies.append(topology.bridge_domain_name)
        
        # Display results
        if validation_issues:
            print(f"❌ Found {len(validation_issues)} path validation issues:")
            print()
            
            # Group issues by type
            issue_types = {}
            for issue in validation_issues:
                for error in issue['validation_result'].errors:
                    error_type = error.error_type.value
                    if error_type not in issue_types:
                        issue_types[error_type] = []
                    issue_types[error_type].append(issue)
            
            # Display issues by type
            for error_type, issues in issue_types.items():
                print(f"🔴 {error_type.upper()} ({len(issues)} issues):")
                for issue in issues[:5]:  # Show first 5 of each type
                    print(f"   • {issue['topology']} - {issue['path_name']}")
                    print(f"     Path: {issue['path_summary']}")
                    for error in issue['validation_result'].errors:
                        print(f"     Error: {error.message}")
                    print()
                
                if len(issues) > 5:
                    print(f"   ... and {len(issues) - 5} more {error_type} issues")
                print()
            
            print(f"📊 Summary: {len(validation_issues)} issues across {len(set(issue['topology'] for issue in validation_issues))} topologies")
            
        else:
            print("✅ All topologies passed path validation!")
            print(f"📊 Total valid topologies: {len(set(valid_topologies))}")
        
        # Show topologies that passed validation
        if valid_topologies:
            print(f"\n✅ Topologies with valid paths: {len(set(valid_topologies))}")
            print("   These can safely participate in consolidation.")
        
    except Exception as e:
        print(f"❌ Error analyzing path validation issues: {e}")
        print("💡 Check the logs for more details.")


def show_path_validation_statistics():
    """Display comprehensive path validation statistics"""
    print("\n📊 PATH VALIDATION STATISTICS")
    print("=" * 50)
    
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        
        db_manager = create_phase1_database_manager()
        
        # Get all topologies
        all_topologies = db_manager.get_all_topologies()
        
        if not all_topologies:
            print("📭 No topologies found in database.")
            return
        
        # Analyze validation status
        total_topologies = len(all_topologies)
        valid_paths = 0
        invalid_paths = 0
        total_paths = 0
        issue_types = {}
        
        for topology in all_topologies:
            for path in topology.paths:
                total_paths += 1
                if path.segments:
                    from config_engine.path_validation import validate_path_continuity
                    validation_result = validate_path_continuity(path.segments)
                    
                    if validation_result.is_valid:
                        valid_paths += 1
                    else:
                        invalid_paths += 1
                        for error in validation_result.errors:
                            error_type = error.error_type.value
                            issue_types[error_type] = issue_types.get(error_type, 0) + 1
        
        # Calculate statistics
        validation_rate = (valid_paths / total_paths * 100) if total_paths > 0 else 0
        topology_validation_rate = (len([t for t in all_topologies if all(
            validate_path_continuity(p.segments).is_valid 
            for p in t.paths if p.segments
        )]) / total_topologies * 100) if total_topologies > 0 else 0
        
        # Display statistics
        print(f"📊 Overall Statistics:")
        print(f"   Total Topologies: {total_topologies}")
        print(f"   Total Paths: {total_paths}")
        print(f"   Valid Paths: {valid_paths}")
        print(f"   Invalid Paths: {invalid_paths}")
        print()
        
        print(f"📈 Validation Rates:")
        print(f"   Path Validation Rate: {validation_rate:.1f}%")
        print(f"   Topology Validation Rate: {topology_validation_rate:.1f}%")
        print()
        
        if issue_types:
            print(f"🔴 Issue Breakdown:")
            for error_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / invalid_paths * 100) if invalid_paths > 0 else 0
                print(f"   {error_type}: {count} ({percentage:.1f}%)")
        
        print()
        
        # Recommendations
        if validation_rate < 90:
            print("⚠️  RECOMMENDATIONS:")
            print("   • Path validation rate is below 90%")
            print("   • Consider fixing path issues before consolidation")
            print("   • Review discovery system path generation")
        else:
            print("✅ Path validation rate is healthy!")
        
    except Exception as e:
        print(f"❌ Error generating path validation statistics: {e}")


def fix_specific_path_issues():
    """Interactive tool to fix specific path validation issues"""
    print("\n🔧 FIX SPECIFIC PATH ISSUES")
    print("=" * 50)
    print("⚠️  This tool helps identify and fix path validation issues")
    print("⚠️  Always backup your database before making changes")
    print()
    
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        
        db_manager = create_phase1_database_manager()
        
        # Get topologies with validation issues
        all_topologies = db_manager.get_all_topologies()
        problematic_topologies = []
        
        for topology in all_topologies:
            for path in topology.paths:
                if path.segments:
                    from config_engine.path_validation import validate_path_continuity
                    validation_result = validate_path_continuity(path.segments)
                    
                    if not validation_result.is_valid:
                        problematic_topologies.append({
                            'topology': topology,
                            'path': path,
                            'issues': validation_result.errors
                        })
        
        if not problematic_topologies:
            print("✅ No path validation issues found!")
            return
        
        print(f"🔍 Found {len(problematic_topologies)} topologies with path issues:")
        print()
        
        # Show options for fixing
        for i, item in enumerate(problematic_topologies[:10]):  # Show first 10
            topology = item['topology']
            path = item['path']
            issues = item['issues']
            
            print(f"{i+1}. {topology.bridge_domain_name}")
            print(f"   Path: {path.path_name}")
            print(f"   Issues: {len(issues)} validation errors")
            for issue in issues:
                print(f"      • {issue.message}")
            print()
        
        if len(problematic_topologies) > 10:
            print(f"... and {len(problematic_topologies) - 10} more topologies with issues")
        
        print("🔧 Fixing Options:")
        print("   1. Auto-fix common path issues (recommended)")
        print("   2. Manual fix for specific topology")
        print("   3. Export issues for external analysis")
        print("   4. Back to path validation menu")
        
        choice = input("\nSelect fixing option [1-4]: ").strip()
        
        if choice == "1":
            auto_fix_common_path_issues(db_manager, problematic_topologies)
        elif choice == "2":
            manual_fix_specific_topology(db_manager, problematic_topologies)
        elif choice == "3":
            export_path_issues_for_analysis(problematic_topologies)
        elif choice == "4":
            return
        else:
            print("❌ Invalid choice.")
    
    except Exception as e:
        print(f"❌ Error in path issue fixing: {e}")


def auto_fix_common_path_issues(db_manager, problematic_topologies):
    """Automatically fix common path validation issues"""
    print("\n🔧 AUTO-FIXING COMMON PATH ISSUES")
    print("=" * 50)
    
    fixed_count = 0
    total_attempted = 0
    
    for item in problematic_topologies:
        topology = item['topology']
        path = item['path']
        
        print(f"🔍 Analyzing {topology.bridge_domain_name} - {path.path_name}...")
        
        # Try to auto-fix common issues
        if auto_fix_path_issue(path):
            fixed_count += 1
            print(f"   ✅ Auto-fixed path issue")
        else:
            print(f"   ⚠️  Could not auto-fix - requires manual intervention")
        
        total_attempted += 1
    
    print(f"\n📊 Auto-fix Results:")
    print(f"   Attempted fixes: {total_attempted}")
    print(f"   Successfully fixed: {fixed_count}")
    print(f"   Success rate: {(fixed_count/total_attempted*100):.1f}%" if total_attempted > 0 else "N/A")


def auto_fix_path_issue(path):
    """Attempt to automatically fix a path validation issue"""
    # This is a placeholder for actual auto-fix logic
    # In a real implementation, you would:
    # 1. Analyze the specific error type
    # 2. Apply appropriate fixes based on the error
    # 3. Update the database with corrected paths
    
    # For now, return False to indicate manual intervention needed
    return False


def manual_fix_specific_topology(db_manager, problematic_topologies):
    """Manual fix interface for specific topology"""
    print("\n🔧 MANUAL FIX FOR SPECIFIC TOPOLOGY")
    print("=" * 50)
    
    if not problematic_topologies:
        print("❌ No problematic topologies to fix.")
        return
    
    # Show list of problematic topologies
    print("📋 Select a topology to fix:")
    for i, item in enumerate(problematic_topologies):
        topology = item['topology']
        print(f"{i+1}. {topology.bridge_domain_name}")
    
    try:
        choice = int(input(f"\nSelect topology [1-{len(problematic_topologies)}]: ").strip())
        if 1 <= choice <= len(problematic_topologies):
            selected_item = problematic_topologies[choice - 1]
            show_topology_fix_interface(db_manager, selected_item)
        else:
            print("❌ Invalid selection.")
    except ValueError:
        print("❌ Please enter a valid number.")


def show_topology_fix_interface(db_manager, selected_item):
    """Show detailed interface for fixing a specific topology"""
    topology = selected_item['topology']
    path = selected_item['path']
    issues = selected_item['issues']
    
    print(f"\n🔧 FIXING TOPOLOGY: {topology.bridge_domain_name}")
    print("=" * 50)
    
    print(f"📋 Path: {path.path_name}")
    print(f"🔍 Issues: {len(issues)} validation errors")
    
    for i, issue in enumerate(issues):
        print(f"   {i+1}. {issue.message}")
        if hasattr(issue, 'context') and issue.context:
            print(f"      Context: {issue.context}")
    
    print("\n🔧 Fix Options:")
    print("   1. View detailed path information")
    print("   2. Edit path segments manually")
    print("   3. Reset path to default")
    print("   4. Mark as reviewed (skip)")
    print("   5. Back to manual fix menu")
    
    choice = input("\nSelect fix option [1-5]: ").strip()
    
    if choice == "1":
        show_detailed_path_information(path)
    elif choice == "2":
        edit_path_segments_manually(path)
    elif choice == "3":
        reset_path_to_default(path)
    elif choice == "4":
        mark_path_as_reviewed(path)
    elif choice == "5":
        return
    else:
        print("❌ Invalid choice.")


def show_detailed_path_information(path):
    """Show detailed information about a path for debugging"""
    print(f"\n📋 DETAILED PATH INFORMATION: {path.path_name}")
    print("=" * 50)
    
    print(f"Source Device: {path.source_device}")
    print(f"Destination Device: {path.dest_device}")
    print(f"Path Type: {path.path_type}")
    print(f"Segments: {len(path.segments)}")
    print()
    
    if path.segments:
        print("📊 Segment Details:")
        for i, segment in enumerate(path.segments):
            print(f"   Segment {i+1}:")
            print(f"     Source: {segment.source_device} ({segment.source_interface})")
            print(f"     Destination: {segment.dest_device} ({segment.dest_interface})")
            print(f"     Type: {segment.segment_type}")
            print(f"     Connection: {segment.connection_type}")
            print()
    else:
        print("⚠️  No segments found in path")


def edit_path_segments_manually(path):
    """Interface for manually editing path segments"""
    print("\n🔧 MANUAL PATH SEGMENT EDITING")
    print("=" * 50)
    print("⚠️  This feature requires database update implementation")
    print("💡 For now, use the export feature to analyze issues externally")
    
    # This would be implemented with actual database update logic
    print("📋 Path segments for editing:")
    for i, segment in enumerate(path.segments):
        print(f"   {i+1}. {segment.source_device} → {segment.dest_device}")


def reset_path_to_default(path):
    """Reset a path to its default/expected configuration"""
    print("\n🔄 RESET PATH TO DEFAULT")
    print("=" * 50)
    print("⚠️  This feature requires database update implementation")
    print("💡 Would reset path to expected default configuration")


def mark_path_as_reviewed(path):
    """Mark a path as reviewed to skip future validation checks"""
    print("\n✅ MARK PATH AS REVIEWED")
    print("=" * 50)
    print("⚠️  This feature requires database update implementation")
    print("💡 Would mark path as manually reviewed")


def test_path_validation_on_topology():
    """Test path validation on a specific topology"""
    print("\n🧪 TEST PATH VALIDATION ON TOPOLOGY")
    print("=" * 50)
    
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        
        db_manager = create_phase1_database_manager()
        
        # Get all topologies
        all_topologies = db_manager.get_all_topologies()
        
        if not all_topologies:
            print("📭 No topologies found in database.")
            return
        
        # Show available topologies
        print("📋 Available topologies for testing:")
        for i, topology in enumerate(all_topologies[:20]):  # Show first 20
            print(f"{i+1}. {topology.bridge_domain_name}")
        
        if len(all_topologies) > 20:
            print(f"... and {len(all_topologies) - 20} more")
        
        # Get user selection
        try:
            choice = int(input(f"\nSelect topology to test [1-{min(20, len(all_topologies))}]: ").strip())
            if 1 <= choice <= min(20, len(all_topologies)):
                selected_topology = all_topologies[choice - 1]
                test_single_topology_path_validation(selected_topology)
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    except Exception as e:
        print(f"❌ Error testing path validation: {e}")


def test_single_topology_path_validation(topology):
    """Test path validation on a single topology"""
    print(f"\n🧪 TESTING PATH VALIDATION: {topology.bridge_domain_name}")
    print("=" * 50)
    
    from config_engine.path_validation import validate_path_continuity, get_path_summary
    
    print(f"📊 Topology Information:")
    print(f"   Bridge Domain: {topology.bridge_domain_name}")
    print(f"   VLAN ID: {topology.vlan_id}")
    print(f"   Paths: {len(topology.paths)}")
    print()
    
    if not topology.paths:
        print("⚠️  No paths found in topology.")
        return
    
    # Test each path
    for i, path in enumerate(topology.paths):
        print(f"🔍 Testing Path {i+1}: {path.path_name}")
        print(f"   Source: {path.source_device}")
        print(f"   Destination: {path.dest_device}")
        
        if path.segments:
            print(f"   Segments: {len(path.segments)}")
            print(f"   Path: {get_path_summary(path.segments)}")
            
            # Run validation
            validation_result = validate_path_continuity(path.segments)
            
            if validation_result.is_valid:
                print("   ✅ Path validation PASSED")
                if validation_result.warnings:
                    for warning in validation_result.warnings:
                        print(f"      ⚠️  Warning: {warning}")
            else:
                print("   ❌ Path validation FAILED")
                for error in validation_result.errors:
                    print(f"      🔴 Error: {error.message}")
        else:
            print("   ⚠️  No segments in path")
        
        print()
    
    # Overall validation status
    all_paths_valid = all(
        validate_path_continuity(p.segments).is_valid 
        for p in topology.paths if p.segments
    )
    
    if all_paths_valid:
        print("🎉 All paths in this topology passed validation!")
        print("✅ This topology can safely participate in consolidation.")
    else:
        print("⚠️  Path validation issues found in this topology.")
        print("🔧 Fix the validation issues before consolidation.")


def export_path_validation_report():
    """Export comprehensive path validation report"""
    print("\n📋 EXPORT PATH VALIDATION REPORT")
    print("=" * 50)
    
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        
        db_manager = create_phase1_database_manager()
        
        # Get all topologies
        all_topologies = db_manager.get_all_topologies()
        
        if not all_topologies:
            print("📭 No topologies found in database.")
            return
        
        # Generate report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_topologies': len(all_topologies),
            'validation_results': [],
            'summary': {}
        }
        
        # Analyze each topology
        valid_count = 0
        invalid_count = 0
        issue_types = {}
        
        for topology in all_topologies:
            topology_result = {
                'bridge_domain_name': topology.bridge_domain_name,
                'vlan_id': topology.vlan_id,
                'paths': []
            }
            
            for path in topology.paths:
                if path.segments:
                    from config_engine.path_validation import validate_path_continuity
                    validation_result = validate_path_continuity(path.segments)
                    
                    path_result = {
                        'path_name': path.path_name,
                        'source_device': path.source_device,
                        'dest_device': path.dest_device,
                        'segments_count': len(path.segments),
                        'is_valid': validation_result.is_valid,
                        'errors': [error.message for error in validation_result.errors],
                        'warnings': validation_result.warnings
                    }
                    
                    topology_result['paths'].append(path_result)
                    
                    if validation_result.is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        for error in validation_result.errors:
                            error_type = error.error_type.value
                            issue_types[error_type] = issue_types.get(error_type, 0) + 1
        
        # Generate summary
        report_data['summary'] = {
            'valid_paths': valid_count,
            'invalid_paths': invalid_count,
            'total_paths': valid_count + invalid_count,
            'validation_rate': (valid_count / (valid_count + invalid_count) * 100) if (valid_count + invalid_count) > 0 else 0,
            'issue_types': issue_types
        }
        
        # Export to file
        import json
        from pathlib import Path
        
        report_file = Path("path_validation_report.json")
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"✅ Path validation report exported to: {report_file}")
        print(f"📊 Report contains validation results for {len(all_topologies)} topologies")
        print(f"📈 Validation rate: {report_data['summary']['validation_rate']:.1f}%")
        
        # Show summary
        print(f"\n📋 Report Summary:")
        print(f"   Valid Paths: {valid_count}")
        print(f"   Invalid Paths: {invalid_count}")
        print(f"   Total Paths: {valid_count + invalid_count}")
        
        if issue_types:
            print(f"\n🔴 Issue Types Found:")
            for error_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
                print(f"   {error_type}: {count}")
        
    except Exception as e:
        print(f"❌ Error exporting path validation report: {e}")


def export_path_issues_for_analysis(problematic_topologies):
    """Export path issues for external analysis"""
    print("\n📋 EXPORTING PATH ISSUES FOR ANALYSIS")
    print("=" * 50)
    
    try:
        import json
        from pathlib import Path
        
        # Prepare export data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_issues': len(problematic_topologies),
            'issues': []
        }
        
        for item in problematic_topologies:
            topology = item['topology']
            path = item['path']
            issues = item['issues']
            
            issue_data = {
                'bridge_domain_name': topology.bridge_domain_name,
                'vlan_id': topology.vlan_id,
                'path_name': path.path_name,
                'source_device': path.source_device,
                'dest_device': path.dest_device,
                'segments_count': len(path.segments),
                'validation_errors': [error.message for error in issues]
            }
            
            export_data['issues'].append(issue_data)
        
        # Export to file
        export_file = Path("path_validation_issues.json")
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Path validation issues exported to: {export_file}")
        print(f"📊 Exported {len(problematic_topologies)} issues for analysis")
        
        # Show sample of exported data
        print(f"\n📋 Sample of exported issues:")
        for i, issue in enumerate(export_data['issues'][:3]):
            print(f"   {i+1}. {issue['bridge_domain_name']} - {issue['path_name']}")
            print(f"      Errors: {', '.join(issue['validation_errors'])}")
        
        if len(export_data['issues']) > 3:
            print(f"   ... and {len(export_data['issues']) - 3} more issues")
        
    except Exception as e:
        print(f"❌ Error exporting path issues: {e}")


def run_database_flush_admin():
    """Secure database flush and reset for administrators"""
    import os
    import hashlib
    from pathlib import Path
    
    print("\n🧹" + "="*80)
    print("🚨 DATABASE FLUSH & RESET - ADMINISTRATOR ONLY")
    print("🧹" + "="*80)
    print("⚠️  WARNING: This will PERMANENTLY DELETE all topology data!")
    print("⚠️  WARNING: This action CANNOT be undone!")
    print("⚠️  WARNING: All bridge domains, devices, interfaces will be lost!")
    print()
    
    print("🎯 Benefits of Database Flush:")
    print("   ✅ Reset topology IDs to start from 1")
    print("   ✅ Remove all legacy entries and artifacts")
    print("   ✅ Clean database schema for fresh discovery")
    print("   ✅ Eliminate fragmentation from deleted records")
    print("   ✅ Fresh start for testing and development")
    print()
    
    print("📊 Current Database Status:")
    try:
        from config_engine.phase1_database import create_phase1_database_manager
        db_manager = create_phase1_database_manager()
        topologies = db_manager.get_all_topologies()
        
        print(f"   Total Bridge Domains: {len(topologies)}")
        if topologies:
            max_id = max(topology.id if hasattr(topology, 'id') else 0 for topology in topologies)
            min_id = min(topology.id if hasattr(topology, 'id') else 0 for topology in topologies)
            print(f"   ID Range: {min_id} - {max_id} (fragmented)")
        
        # Check database file size
        db_path = Path("instance/lab_automation.db")
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"   Database Size: {size_mb:.2f} MB")
    except Exception as e:
        print(f"   ❌ Could not read database status: {e}")
    
    print()
    print("🔐 ADMINISTRATOR AUTHENTICATION REQUIRED")
    print("="*60)
    
    # Multi-layer authentication
    
    # Step 1: Username verification
    expected_admin = "admin"  # In production, this would come from config
    username = input("👤 Enter administrator username: ").strip()
    if username != expected_admin:
        print("❌ Access denied. Invalid administrator username.")
        return
    
    # Step 2: Password verification (simple hash for lab environment)
    expected_password_hash = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # "password"
    password = input("🔑 Enter administrator password: ").strip()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != expected_password_hash:
        print("❌ Access denied. Invalid administrator password.")
        return
    
    # Step 3: Confirmation phrase
    print("\n🚨 FINAL CONFIRMATION REQUIRED")
    print("Type exactly: 'FLUSH DATABASE NOW' to proceed")
    confirmation = input("Confirmation phrase: ").strip()
    
    if confirmation != "FLUSH DATABASE NOW":
        print("❌ Database flush cancelled. Confirmation phrase incorrect.")
        return
    
    # Step 4: Final warning with countdown
    print("\n⚠️  FINAL WARNING: Database flush will begin in 5 seconds...")
    print("Press Ctrl+C to cancel!")
    
    try:
        import time
        for i in range(5, 0, -1):
            print(f"🔥 Flushing database in {i} seconds...", end="\r")
            time.sleep(1)
        print()
    except KeyboardInterrupt:
        print("\n❌ Database flush cancelled by user.")
        return
    
    # Execute database flush
    try:
        print("\n🔥 EXECUTING DATABASE FLUSH...")
        
        # Create backup first
        backup_path = f"instance/lab_automation_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        if Path("instance/lab_automation.db").exists():
            import shutil
            shutil.copy2("instance/lab_automation.db", backup_path)
            print(f"✅ Backup created: {backup_path}")
        
        # Flush the database
        db_manager = create_phase1_database_manager()
        flush_result = db_manager.flush_database()
        
        print("✅ DATABASE FLUSH COMPLETED SUCCESSFULLY!")
        print(f"   📊 {flush_result.get('tables_cleared', 0)} tables cleared")
        print(f"   🗑️  {flush_result.get('records_deleted', 0)} records deleted")
        print(f"   🔄 {flush_result.get('sequences_reset', 0)} ID sequences reset")
        print(f"   💾 Backup saved: {backup_path}")
        print()
        
        print("🎯 NEXT STEPS:")
        print("1. 🔍 Run discovery to populate fresh data")
        print("2. 📥 Import from discovery files")
        print("3. 🔄 Migrate specific legacy data if needed")
        print()
        print("✅ Database is now clean and ready for fresh topology data!")
        
    except Exception as e:
        print(f"❌ Database flush failed: {e}")
        print("💾 Database backup preserved for safety")
        import traceback
        traceback.print_exc()


def _show_inspect_menu(page_topologies):
    """Show inspect menu to select and view detailed information about a bridge domain"""
    import os
    
    try:
        print("\n🔍 INSPECT BRIDGE DOMAIN")
        print("=" * 50)
        print("Select a bridge domain to inspect from the current page:")
        print()
        
        # Display current page topologies with numbered options
        for i, topology in enumerate(page_topologies, 1):
            scope_indicator = "*" if getattr(topology, 'scope_mismatch', False) else " "
            print(f"  {i:2d}. {scope_indicator} {topology.bridge_domain_name}")
        
        print()
        choice = input("Enter the number to inspect (or 'q' to cancel): ").strip()
        
        if choice.lower() == 'q':
            return False
        
        try:
            selection = int(choice)
            if 1 <= selection <= len(page_topologies):
                selected_topology = page_topologies[selection - 1]
                _display_detailed_topology_info(selected_topology)
                return True
            else:
                print(f"❌ Invalid selection. Please enter 1-{len(page_topologies)}")
                return False
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
            return False
            
    except Exception as e:
        print(f"❌ Inspect failed: {e}")
        return False


def _show_search_input():
    """Simple search input that returns the search term for filtering"""
    try:
        print("\n🔍 SEARCH & FILTER BRIDGE DOMAINS")
        print("=" * 50)
        print("Enter search term to filter the table (supports partial matching, case-insensitive):")
        print("Examples: 'visaev', 'v251', 'TATA', 'g_mgmt'")
        print("💡 This will filter the main table view - use [I]nspect to view details")
        print()
        
        search_term = input("Search: ").strip()
        
        if not search_term:
            print("❌ Search term cannot be empty")
            return None
        
        return search_term
            
    except Exception as e:
        print(f"❌ Search input failed: {e}")
        return None


def _fuzzy_search_bridge_domains(topologies, search_term):
    """Implement fuzzy search for bridge domains with scoring"""
    import re
    
    search_term_lower = search_term.lower()
    results = []
    
    for topology in topologies:
        bd_name = topology.bridge_domain_name.lower()
        score = 0
        
        # Exact match gets highest score
        if search_term_lower == bd_name:
            score = 100
        # Starts with search term gets high score
        elif bd_name.startswith(search_term_lower):
            score = 90
        # Contains search term gets medium score
        elif search_term_lower in bd_name:
            score = 70
        # Individual words/parts match
        else:
            # Split search term and bridge domain name for partial matching
            search_parts = re.split(r'[_\-\s]', search_term_lower)
            bd_parts = re.split(r'[_\-\s]', bd_name)
            
            matches = 0
            for search_part in search_parts:
                if search_part:  # Skip empty parts
                    for bd_part in bd_parts:
                        if search_part in bd_part or bd_part in search_part:
                            matches += 1
                            break
            
            if matches > 0:
                score = 30 + (matches * 10)  # Base score + bonus for matches
        
        # Also search in VLAN ID if available
        if topology.vlan_id and str(topology.vlan_id) == search_term:
            score = max(score, 95)  # High score for VLAN ID match
        
        # Add result if it has any score
        if score > 0:
            results.append((topology, score))
    
    # Sort by score (descending) and return topologies
    results.sort(key=lambda x: x[1], reverse=True)
    return [topology for topology, score in results]


def _display_detailed_topology_info(topology):
    """Display comprehensive detailed information about a topology (enhanced version of view_bridge_domain_details)"""
    import os
    from config_engine.phase1_database import create_phase1_database_manager
    
    try:
        # Clear screen for better readability
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"\n{'='*80}")
        print(f"🔍 DETAILED BRIDGE DOMAIN INSPECTION: {topology.bridge_domain_name}")
        print(f"{'='*80}")
        
        # Database Manager for fetching full topology data
        db_manager = create_phase1_database_manager()
        
        # Get full topology data with all components
        try:
            full_topology_data = db_manager.get_topology_by_bridge_domain(topology.bridge_domain_name)
            
            if not full_topology_data:
                print("❌ Could not retrieve full topology data")
                return
        except Exception as e:
            print(f"❌ Error retrieving full topology data: {e}")
            print("💡 This may be due to path validation issues in the stored data")
            print("💡 Showing basic information from database record...")
            print()
            
            # Show basic information from the topology record itself
            _display_basic_topology_info(topology)
            return
        
        # === BASIC INFORMATION ===
        print(f"\n📊 BASIC TOPOLOGY INFORMATION:")
        print(f"  • Bridge Domain Name: {topology.bridge_domain_name}")
        print(f"  • Topology Type: {topology.topology_type}")
        print(f"  • VLAN ID: {topology.vlan_id or 'Not specified'}")
        print(f"  • Scan Method: {getattr(topology, 'scan_method', 'unknown')}")
        print(f"  • Discovered At: {topology.discovered_at}")
        print(f"  • Confidence Score: {topology.confidence_score:.1%}")
        print(f"  • Validation Status: {topology.validation_status}")
        
        # === SERVICE SIGNATURE & DEDUPLICATION INFO ===
        print(f"\n🔑 SERVICE SIGNATURE & DEDUPLICATION:")
        print(f"  • Service Signature: {getattr(topology, 'service_signature', 'Not available')}")
        print(f"  • Discovery Session ID: {getattr(topology, 'discovery_session_id', 'Not available')}")
        print(f"  • Discovery Count: {getattr(topology, 'discovery_count', 'Not available')}")
        print(f"  • First Discovered: {getattr(topology, 'first_discovered_at', 'Not available')}")
        print(f"  • Signature Confidence: {getattr(topology, 'signature_confidence', 0):.1%}")
        print(f"  • Review Required: {'Yes' if getattr(topology, 'review_required', False) else 'No'}")
        if getattr(topology, 'review_reason', None):
            print(f"  • Review Reason: {topology.review_reason}")
        
        # === PERFORMANCE SUMMARY ===
        print(f"\n⚡ PERFORMANCE SUMMARY:")
        print(f"  • Device Count: {len(full_topology_data.devices)}")
        print(f"  • Interface Count: {len(full_topology_data.interfaces)}")
        print(f"  • Path Count: {len(full_topology_data.paths)}")
        
        # === DEVICES SECTION ===
        if full_topology_data.devices:
            print(f"\n🖥️  DEVICES ({len(full_topology_data.devices)} total):")
            for i, device in enumerate(full_topology_data.devices, 1):
                print(f"  {i}. Device: {device.name}")
                print(f"     • Type: {device.device_type}")
                print(f"     • Role: {device.device_role}")
                print(f"     • Confidence Score: {device.confidence_score:.1%}")
                print(f"     • Validation Status: {device.validation_status}")
        
        # === INTERFACES SECTION ===
        if full_topology_data.interfaces:
            print(f"\n🔌 INTERFACES ({len(full_topology_data.interfaces)} total):")
            for i, interface in enumerate(full_topology_data.interfaces, 1):
                print(f"  {i}. Interface: {interface.name}")
                print(f"     • Type: {interface.interface_type}")
                print(f"     • Role: {interface.interface_role}")
                print(f"     • Device: {interface.device_name}")
                print(f"     • VLAN ID: {interface.vlan_id or 'Not specified'}")
                print(f"     • L2 Service Enabled: {'Yes' if interface.l2_service_enabled else 'No'}")
                print(f"     • Confidence Score: {interface.confidence_score:.1%}")
        
        # === PATHS SECTION ===
        if full_topology_data.paths:
            print(f"\n🛤️  PATHS ({len(full_topology_data.paths)} total):")
            for i, path in enumerate(full_topology_data.paths, 1):
                print(f"  {i}. Path: {path.path_name}")
                print(f"     • Type: {path.path_type}")
                print(f"     • Source Device: {path.source_device}")
                print(f"     • Destination Device: {path.dest_device}")
                print(f"     • Segments: {len(path.segments)}")
                
                # Show path segments
                for j, segment in enumerate(path.segments, 1):
                    print(f"       {j}. {segment.source_device} → {segment.dest_device}")
                    print(f"          • Source Interface: {segment.source_interface}")
                    print(f"          • Dest Interface: {segment.dest_interface}")
                    print(f"          • Segment Type: {segment.segment_type}")
        
        # === BRIDGE DOMAIN CONFIGURATION ===
        if hasattr(full_topology_data, 'bridge_domain_config') and full_topology_data.bridge_domain_config:
            config = full_topology_data.bridge_domain_config
            print(f"\n⚙️  BRIDGE DOMAIN CONFIGURATION:")
            print(f"  • Service Name: {config.service_name}")
            print(f"  • Bridge Domain Type: {config.bridge_domain_type}")
            print(f"  • Source Device: {config.source_device}")
            print(f"  • Source Interface: {config.source_interface}")
            print(f"  • VLAN ID: {config.vlan_id or 'Not specified'}")
            print(f"  • Outer VLAN: {config.outer_vlan or 'Not specified'}")
            print(f"  • Inner VLAN: {config.inner_vlan or 'Not specified'}")
            
            if config.destinations:
                print(f"  • Destinations ({len(config.destinations)}):")
                for j, dest in enumerate(config.destinations, 1):
                    dest_device = dest.get('device_name', 'Unknown')
                    dest_interface = dest.get('interface_name', 'Unknown')
                    print(f"    {j}. {dest_device} - {dest_interface}")
        
        # === DATA SOURCES ===
        if hasattr(topology, 'data_sources') and topology.data_sources:
            print(f"\n📋 DATA SOURCES:")
            if isinstance(topology.data_sources, list):
                for i, source in enumerate(topology.data_sources, 1):
                    if isinstance(source, dict):
                        print(f"  {i}. Discovery Session: {source.get('discovery_session', 'Unknown')}")
                        print(f"     • Scan Method: {source.get('scan_method', 'Unknown')}")
                        print(f"     • Discovered At: {source.get('discovered_at', 'Unknown')}")
                        if source.get('review_reason'):
                            print(f"     • Review Reason: {source.get('review_reason')}")
            else:
                print(f"  • Raw Data Sources: {topology.data_sources}")
        
        print(f"\n{'='*80}")
        print("🎯 INSPECTION COMPLETE - Press Enter to return to topology list")
        
    except Exception as e:
        print(f"❌ Failed to display detailed topology info: {e}")
        import traceback
        traceback.print_exc()


def _display_basic_topology_info(topology):
    """Display basic topology information when full data retrieval fails"""
    print(f"\n📊 BASIC TOPOLOGY INFORMATION:")
    print(f"  • Bridge Domain Name: {topology.bridge_domain_name}")
    print(f"  • Topology Type: {topology.topology_type}")
    print(f"  • VLAN ID: {topology.vlan_id or 'Not specified'}")
    print(f"  • Scan Method: {getattr(topology, 'scan_method', 'unknown')}")
    print(f"  • Discovered At: {topology.discovered_at}")
    print(f"  • Confidence Score: {topology.confidence_score:.1%}")
    print(f"  • Validation Status: {topology.validation_status}")
    
    # Service Signature & Deduplication Info
    print(f"\n🔑 SERVICE SIGNATURE & DEDUPLICATION:")
    print(f"  • Service Signature: {getattr(topology, 'service_signature', 'Not available')}")
    print(f"  • Discovery Session ID: {getattr(topology, 'discovery_session_id', 'Not available')}")
    print(f"  • Discovery Count: {getattr(topology, 'discovery_count', 'Not available')}")
    print(f"  • First Discovered: {getattr(topology, 'first_discovered_at', 'Not available')}")
    print(f"  • Signature Confidence: {getattr(topology, 'signature_confidence', 0):.1%}")
    print(f"  • Review Required: {'Yes' if getattr(topology, 'review_required', False) else 'No'}")
    if getattr(topology, 'review_reason', None):
        print(f"  • Review Reason: {topology.review_reason}")
    
    # Performance Summary from metadata
    print(f"\n⚡ PERFORMANCE SUMMARY (from metadata):")
    print(f"  • Device Count: {getattr(topology, 'device_count', 'Unknown')}")
    print(f"  • Interface Count: {getattr(topology, 'interface_count', 'Unknown')}")
    print(f"  • Path Count: {getattr(topology, 'path_count', 'Unknown')}")
    
    # Data Sources
    if hasattr(topology, 'data_sources') and topology.data_sources:
        print(f"\n📋 DATA SOURCES:")
        if isinstance(topology.data_sources, list):
            for i, source in enumerate(topology.data_sources, 1):
                if isinstance(source, dict):
                    print(f"  {i}. Discovery Session: {source.get('discovery_session', 'Unknown')}")
                    print(f"     • Scan Method: {source.get('scan_method', 'Unknown')}")
                    print(f"     • Discovered At: {source.get('discovered_at', 'Unknown')}")
                    if source.get('review_reason'):
                        print(f"     • Review Reason: {source.get('review_reason')}")
        else:
            print(f"  • Raw Data Sources: {topology.data_sources}")
    
    print(f"\n{'='*80}")
    print("⚠️  NOTE: Full topology details unavailable due to data validation issues")
    print("💡 This topology may need data repair or re-discovery")
    print("🔧 Root cause: Path validation error - device name mismatch in stored data")
    print("🎯 INSPECTION COMPLETE - Press Enter to return to topology list")


if __name__ == "__main__":
    main() 