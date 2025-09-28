#!/usr/bin/env python3
"""
BD Editor Menu Adapters

Type-specific menu adapters that provide appropriate editing options
and workflows for different DNAAS bridge domain types.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from .data_models import ValidationResult, InterfaceAnalysis, BDTypeProfile

logger = logging.getLogger(__name__)


class MenuAdapter:
    """Base class for all menu adapters"""
    
    def __init__(self, bridge_domain: Dict, session: Dict, interface_analysis: InterfaceAnalysis):
        self.bd = bridge_domain
        self.session = session
        self.interface_analysis = interface_analysis
        
        # Get BD type profile
        from .interface_analyzer import BDTypeRegistry
        self.type_registry = BDTypeRegistry()
        self.profile = self.type_registry.get_profile(bridge_domain.get('dnaas_type', 'unknown'))
        
    def show_menu(self) -> str:
        """Display menu and get user choice"""
        raise NotImplementedError("Subclasses must implement show_menu")
        
    def execute_action(self, choice: str) -> bool:
        """Execute selected menu action"""
        raise NotImplementedError("Subclasses must implement execute_action")
        
    def display_bd_header(self):
        """Display BD header with type and interface info"""
        
        print(f"\n🔧 EDITING: {self.bd['name']}")
        print("="*60)
        
        if self.profile:
            print(f"Type: {self.profile.common_name} ({self.profile.dnaas_type})")
            print(f"Complexity: {self.profile.complexity.value.title()} ({self.profile.percentage}% of all BDs)")
        else:
            print(f"Type: {self.bd.get('dnaas_type', 'unknown')} (Specialized)")
        
        # BD details
        vlan_id = self.bd.get('vlan_id')
        username = self.bd.get('username')
        topology = self.bd.get('topology_type', 'unknown')
        
        print(f"VLAN ID: {vlan_id} | Username: {username} | Topology: {topology}")
        
        # Interface summary
        summary = self.interface_analysis.summary
        print(f"Customer Interfaces: {summary['customer_count']} (editable) | Infrastructure: {summary['infrastructure_count']} (read-only)")
        
        changes_count = len(self.session.get('changes_made', []))
        print(f"Changes Made: {changes_count}")
        
        # Type-specific tips
        if self.profile and self.profile.editing_tips:
            print(f"\n💡 {self.profile.common_name} BD Tips:")
            for tip in self.profile.editing_tips:
                print(f"   {tip}")
    
    def _get_customer_interface_selection(self) -> Tuple[Optional[str], Optional[str]]:
        """Get customer interface selection using smart selection"""
        
        try:
            from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
            
            print("\n🎯 Using Smart Customer Interface Selection...")
            print("💡 Only customer-facing interfaces will be shown")
            
            result = enhanced_interface_selection_for_editor()
            
            if result[0] and result[1]:
                device, interface = result
                
                # Verify this is a customer interface
                if self._is_infrastructure_interface(interface):
                    print(f"❌ Selected interface {interface} is infrastructure")
                    print("🛡️  Please select a customer-facing interface")
                    return None, None
                
                return device, interface
            else:
                return None, None
                
        except ImportError:
            print("⚠️  Smart interface selection not available")
            return self._manual_interface_input()
    
    def _manual_interface_input(self) -> Tuple[Optional[str], Optional[str]]:
        """Fallback manual interface input"""
        
        print("\n📝 Manual Interface Entry:")
        print("💡 Enter customer-facing interface only (ge100-0/0/*)")
        
        try:
            device = input("Device name: ").strip()
            if not device:
                return None, None
                
            interface = input("Interface name: ").strip()
            if not interface:
                return None, None
            
            # Verify this is not infrastructure
            if self._is_infrastructure_interface(interface):
                print(f"❌ {interface} is an infrastructure interface")
                print("🛡️  Please enter a customer-facing interface")
                return None, None
                
            return device, interface
            
        except KeyboardInterrupt:
            return None, None
    
    def _is_infrastructure_interface(self, interface_name: str) -> bool:
        """Check if interface is infrastructure"""
        from .interface_analyzer import BDInterfaceAnalyzer
        analyzer = BDInterfaceAnalyzer()
        return analyzer.is_infrastructure_interface(interface_name, '')
    
    def _add_interface_to_session(self, device: str, interface: str, config: str, interface_type: str = 'customer') -> bool:
        """Add interface to editing session"""
        
        try:
            # Create new interface record
            new_interface = {
                'device': device,
                'interface': interface,
                'vlan_id': self.bd.get('vlan_id'),
                'config_type': interface_type,
                'cli_config': config,
                'added_by_editor': True,
                'added_at': time.time()
            }
            
            # Add to working copy
            working_copy = self.session.get('working_copy', {})
            if 'interfaces' not in working_copy:
                working_copy['interfaces'] = []
            
            working_copy['interfaces'].append(new_interface)
            
            # Track change with proper structure
            change_record = {
                'id': f"change_{int(time.time())}",  # Add missing ID field
                'action': f'add_{interface_type}_interface',
                'description': f"Added {interface_type} interface {device}:{interface}",
                'interface': new_interface,
                'timestamp': time.time(),
                'reversible': True  # Interface additions are reversible
            }
            
            if 'changes_made' not in self.session:
                self.session['changes_made'] = []
            
            self.session['changes_made'].append(change_record)
            
            print(f"✅ {interface_type.title()} interface added successfully!")
            print(f"📊 Total interfaces: {len(working_copy['interfaces'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding interface to session: {e}")
            print(f"❌ Failed to add interface: {e}")
            return False


class SingleTaggedMenuAdapter(MenuAdapter):
    """Menu adapter for Type 4A: Single-Tagged BDs (73.3% of BDs)"""
    
    def show_menu(self) -> str:
        """Display simple menu for single-tagged BDs"""
        
        self.display_bd_header()
        
        print(f"\n📋 SINGLE-TAGGED EDITING OPTIONS:")
        print("1. 📍 Add Customer Interface (simple VLAN assignment)")
        print("2. 🗑️  Remove Customer Interface")
        print("3. 🔄 Move Interface to Different Device")
        print("4. 📊 View Interface Details")
        print("5. 🔍 Preview Configuration Changes")
        print("6. ↶  Undo Last Change")
        print("7. ↷  Redo Last Change")
        print("8. 📋 View Change History")
        print("9. 💾 Save Changes & Deploy")
        print("10. ❌ Cancel (discard changes)")
        
        print(f"\n💡 Single-Tagged BD: Customer interfaces use VLAN ID {self.bd.get('vlan_id')}")
        print("🛡️  Infrastructure interfaces are overlay-managed")
        print("⚠️  Note: VLAN ID cannot be changed per interface (all must use same VLAN)")
        print("⚡ Quick Actions: Press 'a' to add interface, 'r' to remove")
        
        return input("\nChoose action (1-10 or quick action): ").strip().lower()
    
    def execute_action(self, choice: str) -> bool:
        """Execute single-tagged specific actions"""
        
        if choice in ['1', 'a', 'add']:
            return self.add_customer_interface()
        elif choice in ['2', 'r', 'remove']:
            return self.remove_customer_interface()
        elif choice == '3':
            return self.move_interface()
        elif choice == '4':
            return self.view_interface_details()
        elif choice == '5':
            return self.preview_changes()
        elif choice == '6':
            return self.undo_last_change()
        elif choice == '7':
            return self.redo_last_change()
        elif choice == '8':
            return self.view_change_history()
        elif choice == '9':
            return self.save_and_deploy()
        elif choice == '10':
            return self.cancel_editing()
        else:
            print("❌ Invalid choice. Please select 1-10 or use quick actions (a/r).")
            print("💡 Note: VLAN ID change not available for single-tagged BDs")
            return True  # Continue menu loop
    
    def add_customer_interface(self) -> bool:
        """Add customer interface with single VLAN assignment"""
        
        print(f"\n📍 ADD CUSTOMER INTERFACE (Type 4A: Single-Tagged)")
        print("="*60)
        print(f"Bridge Domain: {self.bd['name']}")
        print(f"VLAN ID: {self.bd['vlan_id']} (automatic assignment)")
        print("💡 Customer interface will use BD's VLAN ID automatically")
        
        # Get customer interface selection
        device, interface = self._get_customer_interface_selection()
        if not device or not interface:
            print("❌ Interface selection cancelled")
            return True  # Continue menu
        
        # Generate single-tagged configuration
        vlan_id = self.bd['vlan_id']
        config = f"interfaces {interface}.{vlan_id} vlan-id {vlan_id}"
        
        print(f"\n📋 SINGLE-TAGGED CONFIGURATION:")
        print(f"Device: {device}")
        print(f"Interface: {interface}.{vlan_id}")
        print(f"VLAN ID: {vlan_id} (inherited from BD)")
        print(f"Configuration: {config}")
        
        # Confirm addition
        confirm = input("\nAdd this customer interface? (Y/n): ").strip().lower()
        if confirm and confirm != 'y':
            print("❌ Interface addition cancelled")
            return True
        
        # Add to session (don't append VLAN ID if already present)
        interface_name = interface if f".{vlan_id}" in interface else f"{interface}.{vlan_id}"
        return self._add_interface_to_session(device, interface_name, config, 'customer')
    
    def remove_customer_interface(self) -> bool:
        """Remove customer interface"""
        
        print(f"\n🗑️  REMOVE CUSTOMER INTERFACE")
        print("="*50)
        
        # Get customer interfaces from session
        working_copy = self.session.get('working_copy', {})
        customer_interfaces = []
        
        for interface in working_copy.get('interfaces', []):
            if not self._is_infrastructure_interface(interface.get('interface', '')):
                customer_interfaces.append(interface)
        
        if not customer_interfaces:
            print("❌ No customer interfaces to remove")
            return True
        
        print("📋 Customer interfaces available for removal:")
        for i, interface in enumerate(customer_interfaces, 1):
            device = interface.get('device')
            intf_name = interface.get('interface')
            print(f"   {i}. {device}:{intf_name}")
        
        try:
            choice = int(input(f"\nSelect interface to remove [1-{len(customer_interfaces)}] (0 to cancel): "))
            
            if choice == 0:
                print("❌ Removal cancelled")
                return True
            
            if 1 <= choice <= len(customer_interfaces):
                interface_to_remove = customer_interfaces[choice - 1]
                
                # Confirm removal
                device = interface_to_remove.get('device')
                intf_name = interface_to_remove.get('interface')
                
                confirm = input(f"\nRemove {device}:{intf_name}? (y/N): ").strip().lower()
                if confirm != 'y':
                    print("❌ Removal cancelled")
                    return True
                
                # Remove from working copy
                working_copy['interfaces'].remove(interface_to_remove)
                
                # Track change
                change_record = {
                    'action': 'remove_customer_interface',
                    'description': f"Removed customer interface {device}:{intf_name}",
                    'interface': interface_to_remove,
                    'timestamp': time.time()
                }
                
                self.session['changes_made'].append(change_record)
                
                print(f"✅ Customer interface {device}:{intf_name} removed successfully!")
                return True
            else:
                print("❌ Invalid selection")
                return True
                
        except (ValueError, KeyboardInterrupt):
            print("❌ Removal cancelled")
            return True
    
    def change_interface_vlan(self) -> bool:
        """Change VLAN ID for customer interface"""
        print("🚧 Change Interface VLAN - Coming in Phase 2")
        return True
    
    def move_interface(self) -> bool:
        """Move interface to different device"""
        print("🚧 Move Interface - Coming in Phase 2")
        return True
    
    def view_interface_details(self) -> bool:
        """View detailed interface information"""
        
        print(f"\n📊 INTERFACE DETAILS")
        print("="*50)
        
        # Display interface analysis
        self.interface_analyzer.display_interface_categorization(self.bd)
        
        input("\nPress Enter to continue...")
        return True
    
    def preview_changes(self) -> bool:
        """Preview configuration changes"""
        
        try:
            from .config_preview import ConfigurationPreviewSystem
            
            print(f"\n🔍 GENERATING CONFIGURATION PREVIEW...")
            
            preview_system = ConfigurationPreviewSystem()
            preview_report = preview_system.generate_full_preview(self.bd, self.session)
            
            if not preview_report.changes:
                print("💡 No changes to preview")
                return True
            
            preview_system.display_preview_to_user(preview_report)
            
            input("\nPress Enter to continue...")
            return True
            
        except ImportError:
            print("🚧 Configuration Preview - Phase 2 components not available")
            return True
        except Exception as e:
            print(f"❌ Preview generation failed: {e}")
            logger.error(f"Preview generation error: {e}")
            return True
    
    def save_and_deploy(self) -> bool:
        """Save changes and deploy to network devices"""
        
        try:
            from .deployment_integration import BDEditorDeploymentIntegration
            
            changes_count = len(self.session.get('changes_made', []))
            
            if changes_count == 0:
                print("💡 No changes to deploy")
                return True
            
            print(f"\n🚀 SAVE & DEPLOY CHANGES")
            print("="*50)
            print(f"Bridge Domain: {self.bd['name']}")
            print(f"Changes to deploy: {changes_count}")
            
            # Show deployment preview first
            print(f"\n🔍 DEPLOYMENT PREVIEW:")
            try:
                from .config_preview import ConfigurationPreviewSystem
                preview_system = ConfigurationPreviewSystem()
                preview_report = preview_system.generate_full_preview(self.bd, self.session)
                
                print(f"   📊 Commands: {len(preview_report.all_commands)}")
                print(f"   📡 Devices: {len(preview_report.affected_devices)}")
                
                if preview_report.validation_result and not preview_report.validation_result.is_valid:
                    print("❌ Validation errors prevent deployment:")
                    for error in preview_report.validation_result.errors:
                        print(f"   • {error}")
                    
                    print("💡 Please fix validation errors before deploying")
                    return True
                
                # Show commands that will be deployed
                for device, commands in preview_report.commands_by_device.items():
                    print(f"\\n📡 {device}:")
                    for i, cmd in enumerate(commands, 1):
                        print(f"   {i}. {cmd}")
                
            except ImportError:
                print("   ⚠️  Preview system not available")
            
            # Confirm deployment
            confirm = input("\\nProceed with deployment? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Deployment cancelled by user")
                return True
            
            # Execute deployment
            deployment_integration = BDEditorDeploymentIntegration(None)  # Will use mock for now
            deployment_result = deployment_integration.deploy_bd_changes(self.bd, self.session)
            
            # Show deployment results
            print(f"\\n📊 DEPLOYMENT RESULTS:")
            print("="*40)
            
            if deployment_result.success:
                print("✅ DEPLOYMENT SUCCESSFUL!")
                print(f"📡 Devices updated: {len(deployment_result.affected_devices)}")
                
                # Clear changes after successful deployment
                self.session['changes_made'] = []
                print("💡 Changes have been deployed and cleared from session")
                
                return False  # Exit menu after successful deployment
            else:
                print("❌ DEPLOYMENT FAILED!")
                for error in deployment_result.errors:
                    print(f"   • {error}")
                
                print("💡 Changes remain in session for retry or modification")
                return True
            
        except ImportError:
            print("🚧 Deployment system not available - Phase 4 components missing")
            print("💡 Changes saved to session for future deployment")
            return True
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            logger.error(f"Deployment error: {e}")
            return True
    
    def undo_last_change(self) -> bool:
        """Undo last change"""
        
        try:
            from .change_tracker import AdvancedChangeTracker
            
            tracker = AdvancedChangeTracker(self.session)
            success = tracker.undo_last_change()
            
            if success:
                print("💡 Change undone successfully")
            
            return True  # Continue menu
            
        except ImportError:
            print("🚧 Undo functionality - Phase 3 components not available")
            return True
        except Exception as e:
            print(f"❌ Undo failed: {e}")
            return True
    
    def redo_last_change(self) -> bool:
        """Redo last undone change"""
        
        try:
            from .change_tracker import AdvancedChangeTracker
            
            tracker = AdvancedChangeTracker(self.session)
            success = tracker.redo_last_undo()
            
            if success:
                print("💡 Change redone successfully")
            
            return True  # Continue menu
            
        except ImportError:
            print("🚧 Redo functionality - Phase 3 components not available")
            return True
        except Exception as e:
            print(f"❌ Redo failed: {e}")
            return True
    
    def view_change_history(self) -> bool:
        """View change history"""
        
        try:
            from .change_tracker import AdvancedChangeTracker
            
            tracker = AdvancedChangeTracker(self.session)
            tracker.display_change_history()
            
            input("\nPress Enter to continue...")
            return True
            
        except ImportError:
            print("🚧 Change history - Phase 3 components not available")
            return True
        except Exception as e:
            print(f"❌ Change history failed: {e}")
            return True
    
    def cancel_editing(self) -> bool:
        """Cancel editing and discard changes"""
        
        changes_count = len(self.session.get('changes_made', []))
        
        if changes_count > 0:
            print(f"\n⚠️  You have {changes_count} unsaved changes")
            confirm = input("Discard all changes and exit? (y/N): ").strip().lower()
            if confirm != 'y':
                print("💡 Continuing editing session")
                return True
        
        print("❌ Editing cancelled - changes discarded")
        return False  # Exit menu loop


class QinQSingleMenuAdapter(MenuAdapter):
    """Menu adapter for Type 2A: QinQ Single BD (21.0% of BDs)"""
    
    def show_menu(self) -> str:
        """Display advanced menu for QinQ single BDs"""
        
        self.display_bd_header()
        
        print(f"\n🎯 CUSTOMER ENDPOINT MANAGEMENT FOCUS")
        print(f"\n📋 QINQ CUSTOMER ENDPOINT OPTIONS:")
        print("1. 📍 Add Customer Interface (with VLAN manipulation)")
        print("2. 🗑️  Remove Customer Interface")
        print("3. ✏️  Modify Customer Interface Settings")
        print("4. 🔄 Move Customer Interface to Different Device")
        print("5. 📊 View All Interfaces (customer + infrastructure reference)")
        print("6. 🔍 Preview Customer Configuration Changes")
        print("7. 💾 Save Changes & Deploy")
        print("8. ❌ Cancel (discard changes)")
        
        print(f"\n💡 QinQ BD: You manage customer endpoints with manipulation (push outer-tag {self.bd.get('vlan_id')})")
        print("📊 Infrastructure: bundle-60000* interfaces shown for reference (auto-managed)")
        print("⚠️  Note: Outer VLAN is BD identity - cannot be changed in editor")
        
        return input("\nChoose action (1-8): ").strip()
    
    def execute_action(self, choice: str) -> bool:
        """Execute QinQ single BD specific actions"""
        
        if choice == '1':
            return self.add_customer_interface()
        elif choice == '2':
            return self.remove_customer_interface()
        elif choice == '3':
            return self.modify_customer_interface()
        elif choice == '4':
            return self.move_customer_interface()
        elif choice == '5':
            return self.view_all_interfaces()
        elif choice == '6':
            return self.preview_customer_changes()
        elif choice == '7':
            return self.save_and_deploy()
        elif choice == '8':
            return self.cancel_editing()
        else:
            print("❌ Invalid choice. Please select 1-8.")
            return True
    
    def add_customer_interface(self) -> bool:
        """Add customer interface with VLAN manipulation"""
        
        print(f"\n📍 ADD CUSTOMER INTERFACE (Type 2A: QinQ Single BD)")
        print("="*60)
        print(f"Bridge Domain: {self.bd['name']}")
        print(f"Outer VLAN: {self.bd['vlan_id']} (BD Identity - Fixed)")
        print("💡 Customer interface will use VLAN manipulation")
        
        # Get customer interface selection
        device, interface = self._get_customer_interface_selection()
        if not device or not interface:
            print("❌ Interface selection cancelled")
            return True
        
        # Generate QinQ customer configuration
        outer_vlan = self.bd['vlan_id']
        config = f"interfaces {interface}.{outer_vlan} vlan-manipulation ingress-mapping action push outer-tag {outer_vlan} outer-tpid 0x8100"
        
        print(f"\n📋 QINQ CUSTOMER CONFIGURATION:")
        print(f"Device: {device}")
        print(f"Interface: {interface}.{outer_vlan}")
        print(f"Outer VLAN: {outer_vlan} (BD identity)")
        print(f"Configuration Type: Customer endpoint with QinQ manipulation")
        print(f"Configuration: {config}")
        
        # Confirm addition
        confirm = input("\nAdd this QinQ customer interface? (Y/n): ").strip().lower()
        if confirm and confirm != 'y':
            print("❌ Interface addition cancelled")
            return True
        
        # Add to session
        return self._add_interface_to_session(device, f"{interface}.{outer_vlan}", config, 'qinq_customer')
    
    def remove_customer_interface(self) -> bool:
        """Remove customer interface (same as SingleTagged)"""
        return super().remove_customer_interface()
    
    def modify_customer_interface(self) -> bool:
        """Modify customer interface settings"""
        print("🚧 Modify Customer Interface - Coming in Phase 2")
        return True
    
    def move_customer_interface(self) -> bool:
        """Move customer interface to different device"""
        print("🚧 Move Customer Interface - Coming in Phase 2")
        return True
    
    def view_all_interfaces(self) -> bool:
        """View all interfaces with customer/infrastructure distinction"""
        
        print(f"\n📊 ALL INTERFACES (Customer + Infrastructure Reference)")
        print("="*60)
        
        # Display interface analysis
        from .interface_analyzer import BDInterfaceAnalyzer
        analyzer = BDInterfaceAnalyzer()
        analyzer.display_interface_categorization(self.bd)
        
        input("\nPress Enter to continue...")
        return True
    
    def preview_customer_changes(self) -> bool:
        """Preview customer configuration changes"""
        return self.preview_changes()  # Use base class implementation


class DoubleTaggedMenuAdapter(MenuAdapter):
    """Menu adapter for Type 1: Double-Tagged BDs (3.2% of BDs)"""
    
    def show_menu(self) -> str:
        """Display expert menu for double-tagged BDs"""
        
        self.display_bd_header()
        
        print(f"\n⚠️  EXPERT MODE: Double-Tagged Configuration")
        print(f"\n📋 DOUBLE-TAGGED EDITING OPTIONS:")
        print("1. 📍 Add Customer Double-Tagged Interface")
        print("2. 🗑️  Remove Customer Interface")
        print("3. ✏️  Modify Customer Interface Tags")
        print("4. 🔄 Move Customer Interface to Different Device")
        print("5. 📊 View Double-Tag Configuration Details")
        print("6. 🔍 Preview Double-Tagged Configuration")
        print("7. 💾 Save Changes & Deploy")
        print("8. ❌ Cancel (discard changes)")
        
        outer_vlan = self.bd.get('outer_vlan', 'unknown')
        inner_vlan = self.bd.get('vlan_id', 'unknown')
        
        print(f"\n💡 Double-Tagged BD: Customer interfaces use outer-tag {outer_vlan} + inner-tag {inner_vlan}")
        print("🛡️  Infrastructure double-tag configuration managed by overlay")
        print("⚠️  Expert Mode: Changes affect customer QinQ configuration only")
        
        return input("\nChoose action (1-8): ").strip()
    
    def execute_action(self, choice: str) -> bool:
        """Execute double-tagged specific actions"""
        
        if choice == '1':
            return self.add_customer_double_tagged_interface()
        elif choice == '2':
            return self.remove_customer_interface()
        elif choice == '3':
            return self.modify_customer_interface_tags()
        elif choice == '4':
            return self.move_customer_interface()
        elif choice == '5':
            return self.view_double_tag_details()
        elif choice == '6':
            return self.preview_double_tagged_changes()
        elif choice == '7':
            return self.save_and_deploy()
        elif choice == '8':
            return self.cancel_editing()
        else:
            print("❌ Invalid choice. Please select 1-8.")
            return True
    
    def add_customer_double_tagged_interface(self) -> bool:
        """Add customer interface with double-tag configuration"""
        
        print(f"\n📍 ADD CUSTOMER DOUBLE-TAGGED INTERFACE (Type 1: Expert)")
        print("="*60)
        print(f"Bridge Domain: {self.bd['name']}")
        
        outer_vlan = self.bd.get('outer_vlan', 100)
        inner_vlan = self.bd.get('vlan_id')
        
        print(f"Current Configuration: outer-tag {outer_vlan}, inner-tag {inner_vlan}")
        print("⚠️  Expert configuration - both tags will be applied to customer interface")
        
        # Get customer interface selection
        device, interface = self._get_customer_interface_selection()
        if not device or not interface:
            print("❌ Interface selection cancelled")
            return True
        
        # Generate double-tagged configuration
        config = f"interfaces {interface}.{inner_vlan} vlan-tags outer-tag {outer_vlan} inner-tag {inner_vlan}"
        
        print(f"\n📋 DOUBLE-TAGGED CUSTOMER CONFIGURATION:")
        print(f"Device: {device}")
        print(f"Interface: {interface}.{inner_vlan}")
        print(f"Outer VLAN: {outer_vlan} (inherited from BD)")
        print(f"Inner VLAN: {inner_vlan} (inherited from BD)")
        print(f"Configuration Type: Customer endpoint with double-tag")
        print(f"Configuration: {config}")
        
        # Expert confirmation
        print(f"\n⚠️  EXPERT CONFIRMATION REQUIRED:")
        print("   • This creates explicit QinQ configuration")
        print("   • Both outer and inner tags will be applied")
        print("   • Customer traffic must match this QinQ format")
        
        confirm = input("\nProceed with double-tagged configuration? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Double-tagged interface addition cancelled")
            return True
        
        # Add to session
        return self._add_interface_to_session(device, f"{interface}.{inner_vlan}", config, 'double_tagged_customer')
    
    def modify_customer_interface_tags(self) -> bool:
        """Modify customer interface tag configuration"""
        print("🚧 Modify Customer Interface Tags - Coming in Phase 2")
        return True
    
    def view_double_tag_details(self) -> bool:
        """View double-tag configuration details"""
        print("🚧 Double-Tag Configuration Details - Coming in Phase 2")
        return True
    
    def preview_double_tagged_changes(self) -> bool:
        """Preview double-tagged configuration changes"""
        return self.preview_changes()  # Use base class implementation


class GenericMenuAdapter(MenuAdapter):
    """Generic menu adapter for unknown or specialized BD types"""
    
    def show_menu(self) -> str:
        """Display generic menu for unknown BD types"""
        
        self.display_bd_header()
        
        print(f"\n⚠️  SPECIALIZED/UNKNOWN BD TYPE")
        print(f"\n📋 GENERIC EDITING OPTIONS:")
        print("1. 📍 Add Interface (manual configuration)")
        print("2. 🗑️  Remove Interface")
        print("3. 📊 View Configuration")
        print("4. ✏️  Manual Configuration Edit")
        print("5. 🔍 Preview Changes")
        print("6. 💾 Save Changes & Deploy")
        print("7. ❌ Cancel (discard changes)")
        
        print(f"\n💡 Generic BD: Manual configuration required")
        print("⚠️  Expert knowledge needed for this BD type")
        
        return input("\nChoose action (1-7): ").strip()
    
    def execute_action(self, choice: str) -> bool:
        """Execute generic actions"""
        
        if choice == '1':
            return self.add_generic_interface()
        elif choice == '2':
            return self.remove_customer_interface()
        elif choice == '3':
            return self.view_configuration()
        elif choice == '4':
            return self.manual_configuration_edit()
        elif choice == '5':
            return self.preview_changes()
        elif choice == '6':
            return self.save_and_deploy()
        elif choice == '7':
            return self.cancel_editing()
        else:
            print("❌ Invalid choice. Please select 1-7.")
            return True
    
    def add_generic_interface(self) -> bool:
        """Add interface with manual configuration"""
        print("🚧 Generic Interface Addition - Coming in Phase 2")
        return True
    
    def view_configuration(self) -> bool:
        """View current BD configuration"""
        print("🚧 Configuration View - Coming in Phase 2")
        return True
    
    def manual_configuration_edit(self) -> bool:
        """Manual configuration editing"""
        print("🚧 Manual Configuration Edit - Coming in Phase 3")
        return True
