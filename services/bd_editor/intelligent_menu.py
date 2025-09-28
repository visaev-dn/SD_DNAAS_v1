#!/usr/bin/env python3
"""
Intelligent Bridge Domain Editor Menu System

Provides type-aware editing menus that adapt to different DNAAS bridge domain types,
offering appropriate options and validation for each configuration pattern.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class BDEditingComplexity(Enum):
    """BD editing complexity levels"""
    SIMPLE = "simple"      # Type 4A: Single-Tagged (73.3% of BDs)
    ADVANCED = "advanced"  # Type 2A: QinQ Single BD (21.0% of BDs)
    EXPERT = "expert"      # Type 1: Double-Tagged (3.2% of BDs)
    SPECIALIZED = "specialized"  # Other types (2.5% of BDs)


@dataclass
class BDTypeProfile:
    """Profile for a specific BD type with editing characteristics"""
    dnaas_type: str
    complexity: BDEditingComplexity
    common_name: str
    description: str
    percentage: float
    interface_config_pattern: str
    editing_tips: List[str]
    validation_rules: List[str]


class BDTypeRegistry:
    """Registry of BD types with their editing profiles"""
    
    def __init__(self):
        self.profiles = {
            "DNAAS_TYPE_4A_SINGLE_TAGGED": BDTypeProfile(
                dnaas_type="DNAAS_TYPE_4A_SINGLE_TAGGED",
                complexity=BDEditingComplexity.SIMPLE,
                common_name="Single-Tagged",
                description="Simple VLAN ID configuration - most common type",
                percentage=73.3,
                interface_config_pattern="interfaces {interface}.{vlan_id} vlan-id {vlan_id}",
                editing_tips=[
                    "💡 All interfaces use the same VLAN ID",
                    "⚡ Simplest configuration - VLAN ID is automatic",
                    "🎯 Best for basic L2 services and connectivity"
                ],
                validation_rules=[
                    "Must have VLAN ID",
                    "No VLAN manipulation allowed",
                    "No outer/inner tags allowed"
                ]
            ),
            
            "DNAAS_TYPE_2A_QINQ_SINGLE_BD": BDTypeProfile(
                dnaas_type="DNAAS_TYPE_2A_QINQ_SINGLE_BD",
                complexity=BDEditingComplexity.ADVANCED,
                common_name="QinQ Single BD",
                description="VLAN manipulation with outer tag - service provider type",
                percentage=21.0,
                interface_config_pattern="interfaces {interface}.{outer_vlan} vlan-manipulation ingress-mapping action push outer-tag {outer_vlan} outer-tpid 0x8100",
                editing_tips=[
                    "💡 Customer interfaces use VLAN manipulation",
                    "🔗 Uplink interfaces use simple VLAN assignment",
                    "⚠️  Changing outer VLAN affects all manipulation commands"
                ],
                validation_rules=[
                    "Must have outer VLAN",
                    "Customer interfaces need manipulation",
                    "Uplink interfaces use simple VLAN"
                ]
            ),
            
            "DNAAS_TYPE_1_DOUBLE_TAGGED": BDTypeProfile(
                dnaas_type="DNAAS_TYPE_1_DOUBLE_TAGGED",
                complexity=BDEditingComplexity.EXPERT,
                common_name="Double-Tagged",
                description="Explicit outer and inner VLAN tags - expert configuration",
                percentage=3.2,
                interface_config_pattern="interfaces {interface}.{inner_vlan} vlan-tags outer-tag {outer_vlan} inner-tag {inner_vlan}",
                editing_tips=[
                    "💡 All interfaces use explicit outer-tag and inner-tag",
                    "⚠️  Expert mode - changes affect QinQ across all interfaces",
                    "🎯 Most complex type - requires QinQ expertise"
                ],
                validation_rules=[
                    "Must have both outer and inner VLANs",
                    "No manipulation commands",
                    "Consistent QinQ configuration required"
                ]
            )
        }
    
    def get_profile(self, dnaas_type: str) -> Optional[BDTypeProfile]:
        """Get BD type profile"""
        return self.profiles.get(dnaas_type)
    
    def get_complexity(self, dnaas_type: str) -> BDEditingComplexity:
        """Get editing complexity for BD type"""
        profile = self.get_profile(dnaas_type)
        return profile.complexity if profile else BDEditingComplexity.SPECIALIZED


class IntelligentBDEditorMenu:
    """Intelligent menu system that adapts to BD type and complexity"""
    
    def __init__(self):
        self.type_registry = BDTypeRegistry()
    
    def get_editing_menu(self, bridge_domain: Dict) -> List[Dict]:
        """Get type-appropriate editing menu"""
        
        dnaas_type = bridge_domain.get('dnaas_type', 'unknown')
        profile = self.type_registry.get_profile(dnaas_type)
        complexity = self.type_registry.get_complexity(dnaas_type)
        
        if complexity == BDEditingComplexity.SIMPLE:
            return self._get_simple_menu(bridge_domain, profile)
        elif complexity == BDEditingComplexity.ADVANCED:
            return self._get_advanced_menu(bridge_domain, profile)
        elif complexity == BDEditingComplexity.EXPERT:
            return self._get_expert_menu(bridge_domain, profile)
        else:
            return self._get_generic_menu(bridge_domain)
    
    def _get_simple_menu(self, bd: Dict, profile: BDTypeProfile) -> List[Dict]:
        """Simple menu for Type 4A: Single-Tagged (73.3% of BDs)"""
        return [
            {
                "option": "1",
                "icon": "📍",
                "title": "Add Access Interface",
                "description": "Add interface with automatic VLAN assignment",
                "action": "add_simple_interface",
                "complexity": "simple",
                "tip": "💡 Interface will automatically use VLAN ID " + str(bd.get('vlan_id', 'N/A'))
            },
            {
                "option": "2", 
                "icon": "🗑️",
                "title": "Remove Interface",
                "description": "Remove existing interface from BD",
                "action": "remove_interface",
                "complexity": "simple"
            },
            {
                "option": "3",
                "icon": "✏️",
                "title": "Change Interface VLAN",
                "description": "Modify VLAN ID for specific interface",
                "action": "change_interface_vlan",
                "complexity": "simple"
            },
            {
                "option": "4",
                "icon": "🔄",
                "title": "Move Interface",
                "description": "Move interface to different device/port",
                "action": "move_interface",
                "complexity": "simple"
            },
            {
                "option": "5",
                "icon": "🎯",
                "title": "Change BD VLAN ID",
                "description": "Change VLAN ID for entire bridge domain",
                "action": "change_bd_vlan",
                "complexity": "advanced",
                "warning": "⚠️  This affects ALL interfaces in the BD"
            },
            {
                "option": "6",
                "icon": "📊",
                "title": "View Interface Details",
                "description": "Show detailed interface configuration",
                "action": "view_details",
                "complexity": "simple"
            },
            {
                "option": "7",
                "icon": "🔍",
                "title": "Preview Changes",
                "description": "Show CLI commands that will be generated",
                "action": "preview_changes",
                "complexity": "simple"
            },
            {
                "option": "8",
                "icon": "💾",
                "title": "Save & Deploy",
                "description": "Save changes and deploy to network",
                "action": "save_deploy",
                "complexity": "advanced"
            },
            {
                "option": "9",
                "icon": "❌",
                "title": "Cancel",
                "description": "Discard all changes and exit",
                "action": "cancel",
                "complexity": "simple"
            }
        ]
    
    def _get_advanced_menu(self, bd: Dict, profile: BDTypeProfile) -> List[Dict]:
        """Advanced menu for Type 2A: QinQ Single BD (21.0% of BDs)"""
        return [
            {
                "option": "1",
                "icon": "📍",
                "title": "Add Customer Interface",
                "description": "Add customer interface with VLAN manipulation",
                "action": "add_customer_interface",
                "complexity": "advanced",
                "tip": "💡 Will use VLAN manipulation with outer-tag " + str(bd.get('vlan_id', 'N/A'))
            },
            {
                "option": "2",
                "icon": "📍",
                "title": "Add Uplink Interface", 
                "description": "Add uplink interface with simple VLAN assignment",
                "action": "add_uplink_interface",
                "complexity": "simple",
                "tip": "💡 Will use simple vlan-id " + str(bd.get('vlan_id', 'N/A'))
            },
            {
                "option": "3",
                "icon": "🗑️",
                "title": "Remove Interface",
                "description": "Remove existing interface from BD",
                "action": "remove_interface",
                "complexity": "simple"
            },
            {
                "option": "4",
                "icon": "✏️",
                "title": "Modify VLAN Manipulation",
                "description": "Change manipulation settings for interface",
                "action": "modify_manipulation",
                "complexity": "expert",
                "warning": "⚠️  Expert feature - affects QinQ behavior"
            },
            {
                "option": "5",
                "icon": "🔄",
                "title": "Convert Interface Type",
                "description": "Convert between manipulation and simple VLAN",
                "action": "convert_interface_type",
                "complexity": "expert"
            },
            {
                "option": "6",
                "icon": "🎯",
                "title": "Change Outer VLAN",
                "description": "Change outer VLAN for entire BD",
                "action": "change_outer_vlan",
                "complexity": "expert",
                "warning": "⚠️  This affects ALL manipulation commands"
            },
            {
                "option": "7",
                "icon": "📊",
                "title": "View QinQ Configuration",
                "description": "Show detailed QinQ interface configuration",
                "action": "view_qinq_config",
                "complexity": "advanced"
            },
            {
                "option": "8",
                "icon": "🔍",
                "title": "Preview QinQ Changes",
                "description": "Show QinQ CLI commands that will be generated",
                "action": "preview_qinq_changes",
                "complexity": "advanced"
            },
            {
                "option": "9",
                "icon": "💾",
                "title": "Save & Deploy",
                "description": "Save changes and deploy QinQ configuration",
                "action": "save_deploy",
                "complexity": "expert"
            },
            {
                "option": "10",
                "icon": "❌",
                "title": "Cancel",
                "description": "Discard all changes and exit",
                "action": "cancel",
                "complexity": "simple"
            }
        ]
    
    def _get_expert_menu(self, bd: Dict, profile: BDTypeProfile) -> List[Dict]:
        """Expert menu for Type 1: Double-Tagged (3.2% of BDs)"""
        return [
            {
                "option": "1",
                "icon": "📍",
                "title": "Add Double-Tagged Interface",
                "description": "Add interface with explicit outer and inner tags",
                "action": "add_double_tagged_interface",
                "complexity": "expert",
                "warning": "⚠️  Expert configuration required"
            },
            {
                "option": "2",
                "icon": "🗑️",
                "title": "Remove Interface",
                "description": "Remove existing interface from BD",
                "action": "remove_interface",
                "complexity": "simple"
            },
            {
                "option": "3",
                "icon": "✏️",
                "title": "Modify Outer VLAN",
                "description": "Change outer VLAN tag for all interfaces",
                "action": "modify_outer_vlan",
                "complexity": "expert",
                "warning": "⚠️  Affects ALL interfaces in BD"
            },
            {
                "option": "4",
                "icon": "✏️",
                "title": "Modify Inner VLAN",
                "description": "Change inner VLAN tag for all interfaces",
                "action": "modify_inner_vlan",
                "complexity": "expert",
                "warning": "⚠️  Affects ALL interfaces in BD"
            },
            {
                "option": "5",
                "icon": "🔄",
                "title": "Move Interface",
                "description": "Move interface to different device/port",
                "action": "move_interface",
                "complexity": "advanced"
            },
            {
                "option": "6",
                "icon": "📊",
                "title": "View Double-Tag Details",
                "description": "Show detailed double-tagged configuration",
                "action": "view_double_tag_config",
                "complexity": "expert"
            },
            {
                "option": "7",
                "icon": "⚠️",
                "title": "Convert to QinQ Single",
                "description": "Convert to simpler QinQ Single BD type",
                "action": "convert_to_qinq_single",
                "complexity": "expert",
                "warning": "⚠️  Major configuration change - backup recommended"
            },
            {
                "option": "8",
                "icon": "🔍",
                "title": "Preview Double-Tag Changes",
                "description": "Show double-tagged CLI commands",
                "action": "preview_double_tag_changes",
                "complexity": "expert"
            },
            {
                "option": "9",
                "icon": "💾",
                "title": "Save & Deploy",
                "description": "Save and deploy double-tagged configuration",
                "action": "save_deploy",
                "complexity": "expert"
            },
            {
                "option": "10",
                "icon": "❌",
                "title": "Cancel",
                "description": "Discard all changes and exit",
                "action": "cancel",
                "complexity": "simple"
            }
        ]
    
    def _get_generic_menu(self, bd: Dict) -> List[Dict]:
        """Generic menu for unknown or specialized BD types"""
        return [
            {
                "option": "1",
                "icon": "📍",
                "title": "Add Interface (Generic)",
                "description": "Add interface with manual configuration",
                "action": "add_generic_interface",
                "complexity": "expert",
                "warning": "⚠️  Manual configuration required"
            },
            {
                "option": "2",
                "icon": "🗑️",
                "title": "Remove Interface",
                "description": "Remove existing interface",
                "action": "remove_interface",
                "complexity": "simple"
            },
            {
                "option": "3",
                "icon": "📊",
                "title": "View Configuration",
                "description": "Show current configuration details",
                "action": "view_config",
                "complexity": "simple"
            },
            {
                "option": "4",
                "icon": "✏️",
                "title": "Manual Configuration Edit",
                "description": "Expert manual configuration editing",
                "action": "manual_config_edit",
                "complexity": "expert",
                "warning": "⚠️  Expert mode - advanced knowledge required"
            },
            {
                "option": "5",
                "icon": "🔍",
                "title": "Preview Changes",
                "description": "Show configuration changes",
                "action": "preview_changes",
                "complexity": "simple"
            },
            {
                "option": "6",
                "icon": "💾",
                "title": "Save & Deploy",
                "description": "Save changes and deploy",
                "action": "save_deploy",
                "complexity": "expert"
            },
            {
                "option": "7",
                "icon": "❌",
                "title": "Cancel",
                "description": "Discard changes and exit",
                "action": "cancel",
                "complexity": "simple"
            }
        ]
    
    def display_intelligent_menu(self, bridge_domain: Dict, session: Dict) -> None:
        """Display intelligent, type-aware editing menu"""
        
        dnaas_type = bridge_domain.get('dnaas_type', 'unknown')
        profile = self.type_registry.get_profile(dnaas_type)
        menu_options = self.get_editing_menu(bridge_domain)
        
        # Header with BD type information
        print(f"\n🔧 EDITING: {bridge_domain['name']}")
        print("="*60)
        
        if profile:
            print(f"Type: {profile.common_name} ({profile.dnaas_type})")
            print(f"Complexity: {profile.complexity.value.title()} ({profile.percentage}% of all BDs)")
            print(f"Description: {profile.description}")
        else:
            print(f"Type: {dnaas_type} (Specialized/Unknown)")
            print("Complexity: Specialized configuration")
        
        # BD details
        vlan_id = bridge_domain.get('vlan_id')
        username = bridge_domain.get('username')
        topology = bridge_domain.get('topology_type', 'unknown')
        interface_count = len(session.get('working_copy', {}).get('interfaces', []))
        changes_count = len(session.get('changes_made', []))
        
        print(f"VLAN ID: {vlan_id} | Username: {username} | Topology: {topology}")
        print(f"Interfaces: {interface_count} | Changes Made: {changes_count}")
        
        # Type-specific tips
        if profile and profile.editing_tips:
            print(f"\n💡 {profile.common_name} BD Tips:")
            for tip in profile.editing_tips:
                print(f"   {tip}")
        
        # Menu options
        print(f"\n📋 {profile.common_name.upper()} EDITING OPTIONS:" if profile else "\n📋 EDITING OPTIONS:")
        
        for option in menu_options:
            icon = option['icon']
            title = option['title']
            description = option['description']
            complexity = option.get('complexity', 'simple')
            
            # Complexity indicator
            complexity_icon = {
                'simple': '🔵',
                'advanced': '🟡', 
                'expert': '🔴'
            }.get(complexity, '⚪')
            
            print(f"{option['option']:2s}. {icon} {title}")
            print(f"     {description}")
            
            # Show tips and warnings
            if option.get('tip'):
                print(f"     {option['tip']}")
            if option.get('warning'):
                print(f"     {option['warning']}")
        
        # Quick actions for simple types
        if profile and profile.complexity == BDEditingComplexity.SIMPLE:
            print(f"\n⚡ Quick Actions: Press 'a' to add interface, 'r' to remove")


class TypeAwareInterfaceAdder:
    """Add interfaces with type-appropriate configuration"""
    
    def __init__(self):
        self.type_registry = BDTypeRegistry()
    
    def add_interface_by_type(self, bridge_domain: Dict, session: Dict) -> bool:
        """Add interface using type-appropriate workflow"""
        
        dnaas_type = bridge_domain.get('dnaas_type', 'unknown')
        profile = self.type_registry.get_profile(dnaas_type)
        
        if not profile:
            return self._add_generic_interface(bridge_domain, session)
        
        if profile.complexity == BDEditingComplexity.SIMPLE:
            return self._add_simple_interface(bridge_domain, session, profile)
        elif profile.complexity == BDEditingComplexity.ADVANCED:
            return self._add_qinq_interface(bridge_domain, session, profile)
        elif profile.complexity == BDEditingComplexity.EXPERT:
            return self._add_double_tagged_interface(bridge_domain, session, profile)
        else:
            return self._add_generic_interface(bridge_domain, session)
    
    def _add_simple_interface(self, bd: Dict, session: Dict, profile: BDTypeProfile) -> bool:
        """Add simple single-tagged interface"""
        
        print(f"\n📍 ADD ACCESS INTERFACE ({profile.common_name})")
        print("="*50)
        print(f"Bridge Domain: {bd['name']}")
        print(f"Current VLAN: {bd['vlan_id']}")
        print(f"💡 Interface will automatically use VLAN ID {bd['vlan_id']}")
        
        # Use smart interface selection
        try:
            from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
            
            result = enhanced_interface_selection_for_editor()
            if not result[0] or not result[1]:
                print("❌ Interface selection cancelled")
                return False
            
            device, interface = result
            vlan_id = bd['vlan_id']
            
            # Generate single-tagged configuration
            config = f"interfaces {interface}.{vlan_id} vlan-id {vlan_id}"
            
            print(f"\n📋 SINGLE-TAGGED CONFIGURATION:")
            print(f"Device: {device}")
            print(f"Interface: {interface}.{vlan_id}")
            print(f"VLAN ID: {vlan_id} (inherited from BD)")
            print(f"Configuration: {config}")
            
            # Add to session
            new_interface = {
                'device': device,
                'interface': f"{interface}.{vlan_id}",
                'vlan_id': vlan_id,
                'config_type': 'single_tagged',
                'cli_config': config,
                'added_by_editor': True
            }
            
            session['working_copy']['interfaces'].append(new_interface)
            session['changes_made'].append({
                'action': 'add_simple_interface',
                'description': f"Added single-tagged interface {device}:{interface}.{vlan_id}",
                'interface': new_interface
            })
            
            print(f"✅ Single-tagged interface added successfully!")
            return True
            
        except ImportError:
            print("⚠️  Smart interface selection not available")
            return False
    
    def _add_qinq_interface(self, bd: Dict, session: Dict, profile: BDTypeProfile) -> bool:
        """Add QinQ interface with type selection"""
        
        print(f"\n📍 ADD INTERFACE ({profile.common_name})")
        print("="*50)
        print(f"Bridge Domain: {bd['name']}")
        print(f"Outer VLAN: {bd['vlan_id']}")
        
        # Interface type selection for QinQ
        print(f"\n🎯 Interface Type Selection:")
        print("1. 🏠 Customer Interface (with VLAN manipulation)")
        print("2. 🔗 Uplink Interface (simple VLAN assignment)")
        
        try:
            type_choice = input("Select interface type [1-2]: ").strip()
            
            if type_choice == "1":
                return self._add_customer_interface_qinq(bd, session)
            elif type_choice == "2":
                return self._add_uplink_interface_qinq(bd, session)
            else:
                print("❌ Invalid selection")
                return False
                
        except KeyboardInterrupt:
            print("❌ Interface addition cancelled")
            return False
    
    def _add_customer_interface_qinq(self, bd: Dict, session: Dict) -> bool:
        """Add customer interface with VLAN manipulation"""
        
        try:
            from services.interface_discovery.cli_integration import enhanced_interface_selection_for_editor
            
            result = enhanced_interface_selection_for_editor()
            if not result[0] or not result[1]:
                return False
            
            device, interface = result
            outer_vlan = bd['vlan_id']
            
            # Generate QinQ manipulation configuration
            config = f"interfaces {interface}.{outer_vlan} vlan-manipulation ingress-mapping action push outer-tag {outer_vlan} outer-tpid 0x8100"
            
            print(f"\n📋 QINQ MANIPULATION CONFIGURATION:")
            print(f"Device: {device}")
            print(f"Interface: {interface}.{outer_vlan}")
            print(f"Outer VLAN: {outer_vlan}")
            print(f"Configuration: {config}")
            
            # Add to session
            new_interface = {
                'device': device,
                'interface': f"{interface}.{outer_vlan}",
                'vlan_id': outer_vlan,
                'config_type': 'qinq_customer',
                'cli_config': config,
                'interface_role': 'customer',
                'added_by_editor': True
            }
            
            session['working_copy']['interfaces'].append(new_interface)
            session['changes_made'].append({
                'action': 'add_qinq_customer_interface',
                'description': f"Added QinQ customer interface {device}:{interface}.{outer_vlan}",
                'interface': new_interface
            })
            
            print(f"✅ QinQ customer interface added successfully!")
            return True
            
        except ImportError:
            print("⚠️  Smart interface selection not available")
            return False


# Convenience functions for CLI integration
def get_intelligent_bd_menu(bridge_domain: Dict) -> List[Dict]:
    """Get intelligent menu for bridge domain"""
    menu = IntelligentBDEditorMenu()
    return menu.get_editing_menu(bridge_domain)


def add_interface_intelligently(bridge_domain: Dict, session: Dict) -> bool:
    """Add interface using intelligent type-aware workflow"""
    adder = TypeAwareInterfaceAdder()
    return adder.add_interface_by_type(bridge_domain, session)


def display_bd_type_info(bridge_domain: Dict) -> None:
    """Display BD type information and editing guidance"""
    
    dnaas_type = bridge_domain.get('dnaas_type', 'unknown')
    registry = BDTypeRegistry()
    profile = registry.get_profile(dnaas_type)
    
    if profile:
        print(f"🎯 BD Type: {profile.common_name} ({profile.dnaas_type})")
        print(f"📊 Usage: {profile.percentage}% of all bridge domains")
        print(f"🔧 Complexity: {profile.complexity.value.title()}")
        print(f"📋 Description: {profile.description}")
        print(f"⚙️  Config Pattern: {profile.interface_config_pattern}")
    else:
        print(f"🎯 BD Type: {dnaas_type} (Specialized/Unknown)")
        print("🔧 Complexity: Specialized configuration")
        print("💡 Using generic editing options")
