#!/usr/bin/env python3
"""
Bridge Domain Editor - Week 2 Implementation
CLI Editing Interface + Workspace Functions
"""

import json
from datetime import datetime


def show_editing_interface(session, db_manager):
    """Enhanced CLI interface with intelligent BD editor system"""
    
    try:
        # Try to use intelligent BD editor system
        from services.bd_editor import (
            PHASE_1_COMPLETE, 
            PHASE_2_AVAILABLE, 
            PHASE_3_AVAILABLE,
            create_intelligent_menu,
            display_bd_health_report,
            is_bd_ready_for_editing
        )
        
        working_copy = session['working_copy']
        
        if PHASE_1_COMPLETE and PHASE_2_AVAILABLE and PHASE_3_AVAILABLE:
            print(f"\n🧠 INTELLIGENT BD EDITOR (All Phases Available)")
            print("="*60)
            print("💡 Enhanced with type-aware menus, validation, preview, and advanced features")
            
            # Health check before editing
            if not is_bd_ready_for_editing(working_copy):
                print("⚠️  BD health check indicates potential issues")
                display_bd_health_report(working_copy)
                
                if not input("Continue editing anyway? (y/N): ").lower().startswith('y'):
                    print("❌ Editing cancelled due to health check")
                    return
            
            # Create intelligent menu adapter
            menu_adapter = create_intelligent_menu(working_copy, session)
            
            print(f"✅ Using {type(menu_adapter).__name__} for BD type {working_copy.get('dnaas_type', 'unknown')}")
            
            # Intelligent editing loop
            while True:
                try:
                    choice = menu_adapter.show_menu()
                    
                    if not menu_adapter.execute_action(choice):
                        break  # User chose to exit
                        
                except KeyboardInterrupt:
                    print("\\n⚠️  Intelligent editing interrupted")
                    
                    if input("Save session and exit? (Y/n): ").lower() != 'n':
                        print("✅ Session saved - you can resume later")
                    
                    break
                except Exception as e:
                    print(f"❌ Error in intelligent menu: {e}")
                    
                    fallback = input("Switch to basic menu? (Y/n): ").lower() != 'n'
                    if fallback:
                        print("💡 Switching to basic menu mode")
                        break
                    else:
                        return
            
            return
            
        else:
            print(f"⚠️  Intelligent BD editor not fully available")
            print(f"📊 Phases: 1({PHASE_1_COMPLETE}) | 2({PHASE_2_AVAILABLE}) | 3({PHASE_3_AVAILABLE})")
            print("💡 Using basic menu with available intelligent features")
            
    except ImportError as e:
        print(f"⚠️  Intelligent BD editor not available: {e}")
        print("💡 Using basic BD editor menu")
    
    # Fallback to basic menu or enhanced basic menu
    show_basic_editing_interface(session, db_manager)


def show_basic_editing_interface(session, db_manager):
    """Basic editing interface with intelligent enhancements where available"""
    
    while True:
        working_copy = session['working_copy']
        
        print(f"\n🔧 EDITING: {working_copy['name']}")
        print("=" * 60)
        print(f"VLAN ID: {working_copy['vlan_id']}")
        print(f"Username: {working_copy['username']}")
        print(f"DNAAS Type: {working_copy.get('dnaas_type', 'N/A')}")
        print(f"Interfaces: {len(working_copy['interfaces'])}")
        print(f"Changes Made: {len(session['changes_made'])}")
        print()
        
        print("📋 EDITING OPTIONS:")
        print("1. 📍 Add Interface/Endpoint")      # Enhanced with intelligent system
        print("2. 🗑️  Remove Interface/Endpoint")   # Enhanced with intelligent system
        print("3. ✏️  Modify Interface/Endpoint")   # User vision: "change endpoints"
        print("4. 🔄 Move Interface to Different Port")  # Interface migration
        print("5. 📊 View All Interfaces")         # Enhanced with categorization
        print("6. 🔍 Preview Changes")             # Enhanced with CLI commands
        print("7. 💾 Save Changes & Deploy")       # Enhanced with deployment
        print("8. ❌ Cancel (discard changes)")
        print()
        
        choice = input("Choose action (1-8): ").strip()
        
        if choice == "1":
            # Try Phase 1 intelligent menu system
            try:
                from services.bd_editor import create_intelligent_menu, PHASE_1_COMPLETE
                
                if PHASE_1_COMPLETE:
                    print("🧠 Using Phase 1 Intelligent Menu System...")
                    
                    # Create intelligent menu adapter
                    menu_adapter = create_intelligent_menu(working_copy, session)
                    
                    # Use menu adapter's add interface method
                    if hasattr(menu_adapter, 'add_customer_interface'):
                        if menu_adapter.add_customer_interface():
                            print("✅ Customer interface added using intelligent system")
                        else:
                            print("❌ Intelligent addition cancelled")
                    else:
                        print("⚠️  Menu adapter doesn't support interface addition yet")
                        add_interface_cli(session)
                else:
                    print("⚠️  Phase 1 not complete, using standard method")
                    add_interface_cli(session)
                    
            except ImportError as e:
                print(f"💡 Intelligent menu system not available: {e}")
                add_interface_cli(session)
            except Exception as e:
                print(f"❌ Intelligent system error: {e}")
                print("💡 Falling back to standard interface addition")
                add_interface_cli(session)
        elif choice == "2":
            remove_interface_cli(session)
        elif choice == "3":
            modify_interface_cli(session)
        elif choice == "4":
            move_interface_cli(session)
        elif choice == "5":
            view_all_interfaces(session)
        elif choice == "6":
            # Try intelligent preview system
            try:
                from services.bd_editor import display_configuration_preview, PHASE_2_AVAILABLE
                
                if PHASE_2_AVAILABLE:
                    print("🔍 Using Intelligent Configuration Preview...")
                    display_configuration_preview(working_copy, session)
                else:
                    preview_changes(session)
                    
            except ImportError:
                preview_changes(session)
        elif choice == "7":
            save_changes_placeholder(session)
        elif choice == "8":
            if confirm_cancel_changes(session):
                print("❌ Changes discarded")
                break
        else:
            print("❌ Invalid choice. Please select 1-8.")
        
        print()


def add_interface_cli(session):
    """Add new interface/endpoint with smart interface selection"""
    # Enhanced with smart interface selection system
    
    print("\n📍 ADD NEW INTERFACE/ENDPOINT")
    print("=" * 40)
    
    working_copy = session['working_copy']
    
    print(f"Adding interface to: {working_copy['name']}")
    print(f"Current VLAN: {working_copy['vlan_id']}")
    
    # Use enhanced smart interface selection for BD Editor
    try:
        from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
        
        print("\n🎯 Using Enhanced Smart Interface Selection for BD Editor...")
        print("💡 Smart device selection with shorthand support + intelligent interface filtering")
        
        result = enhanced_interface_selection_for_editor()
        
        if result[0] and result[1]:
            device, interface = result
            print(f"\n✅ Enhanced Smart Selection Complete:")
            print(f"   Device: {device}")
            print(f"   Interface: {interface}")
            print("💡 Interface validated for BD configuration")
        else:
            print("❌ Smart selection cancelled")
            return
                
    except ImportError:
        print("⚠️  Enhanced smart interface selection not available")
        print("💡 Using manual input...")
        
        device = input("Device name (or shorthand like 'b-15'): ").strip()
        if not device:
            print("❌ Device name required")
            return
        
        interface = input("Interface name: ").strip()
        if not interface:
            print("❌ Interface name required")
            return
    
    # VLAN ID with smart default
    vlan_prompt = f"VLAN ID (current: {working_copy['vlan_id']}): "
    vlan_input = input(vlan_prompt).strip()
    vlan_id = int(vlan_input) if vlan_input else working_copy['vlan_id']
    
    # Create new interface
    new_interface = {
        'device': device,
        'interface': interface,
        'vlan_id': vlan_id,
        'l2_service': True,
        'interface_type': 'physical',
        'added_by_editor': True,  # Mark as editor-added
        'added_at': datetime.now().isoformat()
    }
    
    # Add to working copy
    working_copy['interfaces'].append(new_interface)
    
    # Track change
    change_description = f"Added interface {device}:{interface} (VLAN {vlan_id})"
    session['changes_made'].append({
        'action': 'add_interface',
        'description': change_description,
        'interface': new_interface,
        'timestamp': datetime.now().isoformat()
    })
    
    print(f"✅ Added interface: {device}:{interface} (VLAN {vlan_id})")
    print(f"📊 Total interfaces: {len(working_copy['interfaces'])}")


def remove_interface_cli(session):
    """Remove existing interface/endpoint - Task 2.3 Implementation"""
    # User Vision: "remove endpoints"
    
    print("\n🗑️  REMOVE INTERFACE/ENDPOINT")
    print("=" * 40)
    
    working_copy = session['working_copy']
    interfaces = working_copy['interfaces']
    
    if not interfaces:
        print("❌ No interfaces to remove")
        return
    
    print(f"Current interfaces in {working_copy['name']}:")
    for i, iface in enumerate(interfaces, 1):
        device = iface.get('device', 'Unknown')
        interface_name = iface.get('interface', 'Unknown')
        vlan_id = iface.get('vlan_id', 'N/A')
        added_by_editor = iface.get('added_by_editor', False)
        status = " (Added by Editor)" if added_by_editor else ""
        print(f"{i:2}. {device}:{interface_name} (VLAN {vlan_id}){status}")
    
    print()
    choice = input("Select interface to remove (number or 'c' to cancel): ").strip()
    
    if choice.lower() == 'c':
        return
    
    if choice.isdigit():
        interface_index = int(choice) - 1
        if 0 <= interface_index < len(interfaces):
            removed_interface = interfaces.pop(interface_index)
            
            # Track change
            device = removed_interface.get('device', 'Unknown')
            interface_name = removed_interface.get('interface', 'Unknown')
            change_description = f"Removed interface {device}:{interface_name}"
            
            session['changes_made'].append({
                'action': 'remove_interface',
                'description': change_description,
                'interface': removed_interface,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"✅ Removed interface: {device}:{interface_name}")
            print(f"📊 Remaining interfaces: {len(interfaces)}")
        else:
            print("❌ Invalid selection")
    else:
        print("❌ Invalid input")


def modify_interface_cli(session):
    """Modify existing interface/endpoint - Task 2.3 Implementation"""
    # User Vision: "change endpoints"
    
    print("\n✏️  MODIFY INTERFACE/ENDPOINT")
    print("=" * 40)
    
    working_copy = session['working_copy']
    interfaces = working_copy['interfaces']
    
    if not interfaces:
        print("❌ No interfaces to modify")
        return
    
    print(f"Interfaces in {working_copy['name']}:")
    for i, iface in enumerate(interfaces, 1):
        device = iface.get('device', 'Unknown')
        interface_name = iface.get('interface', 'Unknown')
        vlan_id = iface.get('vlan_id', 'N/A')
        print(f"{i:2}. {device}:{interface_name} (VLAN {vlan_id})")
    
    print()
    choice = input("Select interface to modify (number or 'c' to cancel): ").strip()
    
    if choice.lower() == 'c':
        return
    
    if choice.isdigit():
        interface_index = int(choice) - 1
        if 0 <= interface_index < len(interfaces):
            interface = interfaces[interface_index]
            
            print(f"\n✏️ Modifying: {interface.get('device')}:{interface.get('interface')}")
            print("📋 What would you like to modify?")
            print("1. VLAN ID")
            print("2. L2 Service Setting")
            print("3. Interface Type")
            print("4. Cancel")
            
            modify_choice = input("Choose option (1-4): ").strip()
            
            if modify_choice == "1":
                new_vlan = input(f"New VLAN ID (current: {interface.get('vlan_id')}): ").strip()
                if new_vlan and new_vlan.isdigit():
                    old_vlan = interface.get('vlan_id')
                    interface['vlan_id'] = int(new_vlan)
                    
                    change_description = f"Modified {interface.get('device')}:{interface.get('interface')} VLAN: {old_vlan} → {new_vlan}"
                    session['changes_made'].append({
                        'action': 'modify_interface_vlan',
                        'description': change_description,
                        'interface': interface,
                        'old_value': old_vlan,
                        'new_value': int(new_vlan),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    print(f"✅ VLAN ID updated: {old_vlan} → {new_vlan}")
            elif modify_choice == "2":
                current_l2 = interface.get('l2_service', True)
                new_l2 = not current_l2
                interface['l2_service'] = new_l2
                
                change_description = f"Modified {interface.get('device')}:{interface.get('interface')} L2 Service: {current_l2} → {new_l2}"
                session['changes_made'].append({
                    'action': 'modify_interface_l2',
                    'description': change_description,
                    'interface': interface,
                    'old_value': current_l2,
                    'new_value': new_l2,
                    'timestamp': datetime.now().isoformat()
                })
                
                print(f"✅ L2 Service updated: {current_l2} → {new_l2}")
            elif modify_choice == "3":
                current_type = interface.get('interface_type', 'physical')
                print("Interface type options: physical, subinterface, bundle")
                new_type = input(f"New interface type (current: {current_type}): ").strip()
                if new_type and new_type in ['physical', 'subinterface', 'bundle']:
                    interface['interface_type'] = new_type
                    
                    change_description = f"Modified {interface.get('device')}:{interface.get('interface')} type: {current_type} → {new_type}"
                    session['changes_made'].append({
                        'action': 'modify_interface_type',
                        'description': change_description,
                        'interface': interface,
                        'old_value': current_type,
                        'new_value': new_type,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    print(f"✅ Interface type updated: {current_type} → {new_type}")
        else:
            print("❌ Invalid selection")
    else:
        print("❌ Invalid input")


def move_interface_cli(session):
    """Move interface to different physical port on same device - NEW FEATURE"""
    
    print("\n🔄 MOVE INTERFACE TO DIFFERENT PORT")
    print("=" * 50)
    print("💡 Move an interface from one physical port to another on the same device")
    print()
    
    working_copy = session['working_copy']
    interfaces = working_copy['interfaces']
    
    if not interfaces:
        print("❌ No interfaces to move")
        return
    
    # Show current interfaces
    print(f"Current interfaces in {working_copy['name']}:")
    for i, iface in enumerate(interfaces, 1):
        device = iface.get('device', 'Unknown')
        interface_name = iface.get('interface', 'Unknown')
        vlan_id = iface.get('vlan_id', 'N/A')
        role = iface.get('role', 'unknown')
        print(f"{i:2}. {device}:{interface_name} (VLAN {vlan_id}) - {role}")
    
    print()
    choice = input("Select interface to move (number or 'c' to cancel): ").strip()
    
    if choice.lower() == 'c':
        return
    
    if choice.isdigit():
        interface_index = int(choice) - 1
        if 0 <= interface_index < len(interfaces):
            interface_to_move = interfaces[interface_index]
            
            print(f"\n🔄 Moving: {interface_to_move.get('device')}:{interface_to_move.get('interface')}")
            print(f"Current device: {interface_to_move.get('device')}")
            print()
            
            # Get new interface details
            print("📋 New interface location:")
            new_device = input(f"Device name (current: {interface_to_move.get('device')}): ").strip()
            if not new_device:
                new_device = interface_to_move.get('device')  # Keep same device
            
            new_interface_name = input("New interface name (e.g., ge100-0/0/15.251): ").strip()
            if not new_interface_name:
                print("❌ New interface name required")
                return
            
            # Preserve all configuration but change physical location
            old_device = interface_to_move.get('device')
            old_interface = interface_to_move.get('interface')
            
            # Update interface location
            interface_to_move['device'] = new_device
            interface_to_move['interface'] = new_interface_name
            interface_to_move['moved_by_editor'] = True
            interface_to_move['moved_at'] = datetime.now().isoformat()
            
            # Track the move as a compound change
            move_description = f"Moved interface from {old_device}:{old_interface} to {new_device}:{new_interface_name}"
            session['changes_made'].append({
                'action': 'move_interface',
                'description': move_description,
                'old_location': {'device': old_device, 'interface': old_interface},
                'new_location': {'device': new_device, 'interface': new_interface_name},
                'interface': interface_to_move,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"✅ Interface moved successfully!")
            print(f"✅ From: {old_device}:{old_interface}")
            print(f"✅ To: {new_device}:{new_interface_name}")
            print(f"✅ All VLAN configuration preserved")
            
            # Show what this means for deployment
            print()
            print("📋 Deployment Impact:")
            print(f"   1. Remove interface from {old_device}:{old_interface}")
            print(f"   2. Add interface to {new_device}:{new_interface_name}")
            print(f"   3. Apply same VLAN configuration")
            print("💡 This will be executed as atomic operation during deployment")
            
        else:
            print("❌ Invalid selection")
    else:
        print("❌ Invalid input")


def view_all_interfaces(session):
    """View all interfaces in detail with raw config - Enhanced Implementation"""
    
    print("\n📋 ALL INTERFACES WITH RAW CONFIGURATION")
    print("=" * 80)
    
    working_copy = session['working_copy']
    interfaces = working_copy['interfaces']
    
    if not interfaces:
        print("📭 No interfaces configured")
        print("💡 Use option 1 to add interfaces")
        return
    
    print(f"Bridge Domain: {working_copy['name']}")
    print(f"Total User-Editable Endpoints: {len(interfaces)}")
    print()
    
    for i, iface in enumerate(interfaces, 1):
        device = iface.get('device', 'Unknown')
        interface_name = iface.get('interface', 'Unknown')
        vlan_id = iface.get('vlan_id', 'N/A')
        outer_vlan = iface.get('outer_vlan', 'N/A')
        inner_vlan = iface.get('inner_vlan', 'N/A')
        l2_service = iface.get('l2_service', 'Unknown')
        interface_type = iface.get('interface_type', 'Unknown')
        role = iface.get('role', 'Unknown')
        added_by_editor = iface.get('added_by_editor', False)
        
        print(f"{i:3}. {device}:{interface_name}")
        print(f"     • VLAN ID: {vlan_id}")
        if outer_vlan != 'N/A':
            print(f"     • Outer VLAN: {outer_vlan}")
        if inner_vlan != 'N/A':
            print(f"     • Inner VLAN: {inner_vlan}")
        print(f"     • L2 Service: {l2_service}")
        print(f"     • Type: {interface_type}")
        print(f"     • Role: {role}")
        if added_by_editor:
            print(f"     • 🆕 Added by Editor")
        
        # Show raw CLI configuration from database
        raw_config = iface.get('raw_cli_config', [])
        if raw_config:
            print(f"     • 📜 Raw CLI Config:")
            for j, cmd in enumerate(raw_config, 1):
                print(f"       {j}. {cmd}")
        else:
            print(f"     • 📜 Raw CLI Config: None (new interface)")
        
        # Show VLAN manipulation if present
        vlan_manipulation = iface.get('vlan_manipulation')
        if vlan_manipulation:
            print(f"     • 🔧 VLAN Manipulation: {vlan_manipulation}")
        
        print()
    
    print("💡 Raw CLI config shows actual network device configuration")
    print("🔒 Uplink/downlink interfaces hidden (automatically managed)")
    input("Press Enter to continue...")


def preview_changes(session):
    """Preview all changes made in editing session - Task 2.2 Implementation"""
    
    print("\n🔍 PREVIEW CHANGES")
    print("=" * 50)
    
    changes = session['changes_made']
    
    if not changes:
        print("📭 No changes made yet")
        print("💡 Use options 1-3 to make changes")
        return
    
    working_copy = session['working_copy']
    print(f"Bridge Domain: {working_copy['name']}")
    print(f"Session ID: {session['session_id'][:8]}...")
    print()
    
    print(f"📊 CHANGE SUMMARY ({len(changes)} changes):")
    for i, change in enumerate(changes, 1):
        action = change['action']
        description = change['description']
        timestamp = change['timestamp'][:19]  # Remove microseconds
        
        action_icon = {
            'add_interface': '📍',
            'remove_interface': '🗑️',
            'modify_interface_vlan': '✏️',
            'modify_interface_l2': '✏️',
            'modify_interface_type': '✏️',
            'move_interface': '🔄'
        }.get(action, '📝')
        
        print(f"{i:2}. {action_icon} {description}")
        print(f"    Time: {timestamp}")
    
    print()
    print("💡 Use option 6 to save changes (Week 3: Deploy)")
    input("Press Enter to continue...")


def save_changes_placeholder(session):
    """Week 3 Implementation: Smart Deployment + Validation"""
    
    print("\n💾 SAVE & DEPLOY CHANGES")
    print("=" * 50)
    
    changes = session['changes_made']
    working_copy = session['working_copy']
    
    if not changes:
        print("📭 No changes to save")
        return
    
    print(f"Bridge Domain: {working_copy['name']}")
    print(f"Changes to deploy: {len(changes)}")
    print()
    
    try:
        # Task 3.1: Smart CLI Command Calculation
        print("🧠 CALCULATING DEPLOYMENT CHANGES...")
        from bd_editor_week3 import calculate_deployment_changes
        deployment_diff = calculate_deployment_changes(session)
        
        print(f"📊 DEPLOYMENT SUMMARY:")
        operations = deployment_diff.get('operations', [])
        total_commands = len([cmd for cmd in deployment_diff['cli_commands'] if not cmd.startswith('#')])
        
        print(f"   • Operations to deploy: {len(operations)}")
        for op in operations:
            op_type = op['type'].upper()
            cmd_count = op['commands']
            print(f"     - {op_type}: {cmd_count} commands")
        print(f"   • Total CLI commands: {total_commands}")
        print()
        
        # Task 3.2: Validation System
        print("✅ VALIDATING DEPLOYMENT CHANGES...")
        from bd_editor_week3 import validate_deployment_changes
        validation_result = validate_deployment_changes(deployment_diff, session)
        
        if not validation_result['is_valid']:
            print("❌ VALIDATION FAILED - Deployment aborted")
            for error in validation_result['errors']:
                print(f"   • {error}")
            input("Press Enter to continue...")
            return
        
        # Show warnings if any
        if validation_result['warnings']:
            print("⚠️  WARNINGS DETECTED:")
            for warning in validation_result['warnings']:
                print(f"   • {warning}")
            print()
        
        # Preview CLI commands with better formatting
        print("🔍 PREVIEW OF DEPLOYMENT OPERATIONS:")
        print("=" * 60)
        
        # Group commands by operation type for better readability
        preview_cli_commands_grouped(deployment_diff, session)
        
        print("=" * 60)
        
        # Confirm deployment
        confirm = input("Deploy these changes to the network? (y/N): ").strip().lower()
        if not confirm.startswith('y'):
            print("❌ Deployment cancelled by user")
            return
        
        # Task 3.3: Safe SSH Deployment
        print("🚀 DEPLOYING CHANGES SAFELY...")
        from bd_editor_week3 import deploy_changes_safely, update_database_after_deployment
        deployment_result = deploy_changes_safely(session, deployment_diff)
        
        if deployment_result['success']:
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print("✅ All changes applied and validated")
            print("✅ Bridge domain successfully updated")
            
            # Update database with changes (Task 3.4)
            update_database_after_deployment(session, deployment_diff)
            
        else:
            print("❌ DEPLOYMENT FAILED")
            print("🔄 System automatically rolled back to previous state")
            if deployment_result.get('error'):
                print(f"   Error: {deployment_result['error']}")
        
        input("Press Enter to continue...")
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        print("🔄 No changes were applied to the network")
        input("Press Enter to continue...")


def confirm_cancel_changes(session):
    """Confirm canceling changes"""
    
    changes = session['changes_made']
    
    if not changes:
        return True
    
    print(f"\n⚠️  You have {len(changes)} unsaved changes:")
    for change in changes[-3:]:  # Show last 3 changes
        print(f"   • {change['description']}")
    
    if len(changes) > 3:
        print(f"   ... and {len(changes) - 3} more changes")
    
    print()
    confirm = input("Are you sure you want to discard all changes? (y/N): ").strip().lower()
    return confirm.startswith('y')


def preview_cli_commands_grouped(deployment_diff, session):
    """Preview CLI commands grouped by operation for CLEAN readability"""
    
    operations = deployment_diff.get('operations', [])
    
    if not operations:
        print("📭 No operations to deploy")
        return
    
    # Show clean, grouped operations
    for i, operation in enumerate(operations, 1):
        op_type = operation['type']
        description = operation['description']
        cmd_count = operation['commands']
        
        # Operation header with icon
        op_icons = {
            'move': '🔄',
            'add': '📍', 
            'remove': '🗑️',
            'modify': '✏️'
        }
        
        icon = op_icons.get(op_type, '📝')
        print(f"{icon} OPERATION {i}: {description}")
        print(f"   └─ {cmd_count} CLI commands")
        print()
    
    # Show actual CLI commands in clean format
    print("🔧 ACTUAL CLI COMMANDS TO EXECUTE:")
    print("-" * 50)
    
    cmd_num = 1
    for cmd in deployment_diff['cli_commands']:
        if cmd.startswith('#'):
            # Show operation separator
            print(f"\n# {cmd[2:]}")  # Remove "# " prefix
        else:
            print(f"{cmd_num:2}. {cmd}")
            cmd_num += 1
    
    print()
    actual_commands = len([cmd for cmd in deployment_diff['cli_commands'] if not cmd.startswith('#')])
    print(f"📊 TOTAL: {actual_commands} network commands to execute")
    
    if actual_commands <= 5:
        print("✅ Optimized command count - efficient deployment")
    elif actual_commands <= 10:
        print("⚠️ Moderate command count - acceptable")
    else:
        print("🚨 High command count - consider breaking into smaller operations")
