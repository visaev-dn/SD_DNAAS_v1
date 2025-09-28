#!/usr/bin/env python3
"""
BD Interface Analyzer

Analyzes and categorizes interfaces in bridge domains to separate
customer-editable interfaces from infrastructure (read-only) interfaces.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from .data_models import InterfaceAnalysis, BDTypeProfile, BDEditingComplexity

logger = logging.getLogger(__name__)


class BDInterfaceAnalyzer:
    """Analyze and categorize interfaces in bridge domains"""
    
    def __init__(self):
        # Infrastructure interface patterns (overlay managed)
        self.infrastructure_patterns = [
            r"bundle-60000.*",   # Leaf uplinks to spine
            r"bundle-6000[1-9].*", # Spine downlinks to leaf  
            r"bundle-6001[0-9].*", # Additional spine interfaces
        ]
        
        # Customer interface patterns (user managed)
        self.customer_patterns = [
            r"ge100-0/0/.*",     # Physical customer interfaces
            r"bundle-[1-9].*",   # Customer bundles (not 60000+)
            r"bundle-[1-5][0-9].*" # Customer bundles (1-599)
        ]
        
        # Infrastructure roles (overlay managed)
        self.infrastructure_roles = ['uplink', 'downlink', 'transport']
        
        # Customer roles (user managed)
        self.customer_roles = ['access', 'customer']
    
    def analyze_bd_interfaces(self, bridge_domain: Dict) -> InterfaceAnalysis:
        """
        Analyze all interfaces in BD and categorize them
        
        Returns:
            InterfaceAnalysis with customer_editable and infrastructure_readonly lists
        """
        
        customer_editable = []
        infrastructure_readonly = []
        
        try:
            devices = bridge_domain.get('devices', {})
            
            for device_name, device_info in devices.items():
                interfaces = device_info.get('interfaces', [])
                
                for interface in interfaces:
                    interface_name = interface.get('name', '')
                    interface_role = interface.get('role', '')
                    
                    # Enrich interface with device context
                    enriched_interface = {
                        **interface,
                        'device_name': device_name,
                        'device_type': device_info.get('device_type', 'unknown'),
                        'editability_reason': ''
                    }
                    
                    # Categorize interface
                    if self.is_infrastructure_interface(interface_name, interface_role):
                        enriched_interface['editability_reason'] = 'Infrastructure interface - managed by network overlay'
                        infrastructure_readonly.append(enriched_interface)
                    elif self.is_customer_interface(interface_name, interface_role):
                        enriched_interface['editability_reason'] = 'Customer interface - user editable'
                        customer_editable.append(enriched_interface)
                    else:
                        # Unknown interface type - default to customer for safety
                        enriched_interface['editability_reason'] = 'Unknown interface type - defaulting to customer editable'
                        customer_editable.append(enriched_interface)
                        logger.warning(f"Unknown interface type: {interface_name} with role {interface_role}")
            
            return InterfaceAnalysis(
                customer_editable=customer_editable,
                infrastructure_readonly=infrastructure_readonly
            )
            
        except Exception as e:
            logger.error(f"Error analyzing BD interfaces: {e}")
            # Return empty analysis on error
            return InterfaceAnalysis()
    
    def is_customer_interface(self, interface_name: str, interface_role: str) -> bool:
        """Check if interface is customer-editable"""
        
        # Check by role first (most reliable)
        if interface_role in self.customer_roles:
            return True
        
        # Check by name pattern
        for pattern in self.customer_patterns:
            if re.match(pattern, interface_name):
                return True
        
        # If role is infrastructure, it's not customer
        if interface_role in self.infrastructure_roles:
            return False
            
        # Default: if not clearly infrastructure, assume customer
        return not self.is_infrastructure_interface(interface_name, interface_role)
    
    def is_infrastructure_interface(self, interface_name: str, interface_role: str) -> bool:
        """Check if interface is infrastructure (read-only)"""
        
        # Check by role first (most reliable)
        if interface_role in self.infrastructure_roles:
            return True
        
        # Check by name pattern
        for pattern in self.infrastructure_patterns:
            if re.match(pattern, interface_name):
                return True
                
        return False
    
    def get_interface_editability_summary(self, bridge_domain: Dict) -> str:
        """Generate human-readable summary of interface editability"""
        
        analysis = self.analyze_bd_interfaces(bridge_domain)
        
        customer_count = analysis.summary['customer_count']
        infrastructure_count = analysis.summary['infrastructure_count']
        total_count = analysis.summary['total_interfaces']
        
        if total_count == 0:
            return "No interfaces found in bridge domain"
        
        summary = f"{customer_count} customer interfaces (editable), {infrastructure_count} infrastructure interfaces (read-only)"
        
        if customer_count == 0:
            summary += " - ⚠️  No customer interfaces available for editing"
        elif infrastructure_count == 0:
            summary += " - 💡 All interfaces are customer-editable"
        
        return summary
    
    def display_interface_categorization(self, bridge_domain: Dict):
        """Display detailed interface categorization for user"""
        
        analysis = self.analyze_bd_interfaces(bridge_domain)
        
        print(f"\n📊 INTERFACE ANALYSIS: {bridge_domain.get('name', 'Unknown BD')}")
        print("="*60)
        
        # Summary
        summary = analysis.summary
        print(f"📈 Total interfaces: {summary['total_interfaces']}")
        print(f"✅ Customer interfaces: {summary['customer_count']} (editable)")
        print(f"🔒 Infrastructure interfaces: {summary['infrastructure_count']} (read-only)")
        print(f"📊 Editability: {summary['editability_percentage']:.1f}%")
        
        # Customer interfaces
        if analysis.customer_editable:
            print(f"\n✅ CUSTOMER INTERFACES (User Editable):")
            for i, interface in enumerate(analysis.customer_editable, 1):
                device = interface['device_name']
                name = interface['name']
                role = interface.get('role', 'unknown')
                print(f"   {i:2d}. {device}:{name} ({role})")
        
        # Infrastructure interfaces  
        if analysis.infrastructure_readonly:
            print(f"\n🔒 INFRASTRUCTURE INTERFACES (Read-Only Reference):")
            for i, interface in enumerate(analysis.infrastructure_readonly, 1):
                device = interface['device_name']
                name = interface['name']
                role = interface.get('role', 'unknown')
                print(f"   {i:2d}. {device}:{name} ({role}) - Overlay managed")
        
        if not analysis.customer_editable and not analysis.infrastructure_readonly:
            print("\n⚠️  No interfaces found in bridge domain")


# BD Type Registry
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
                    "💡 All customer interfaces use the same VLAN ID",
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
                    "🔒 Infrastructure interfaces are overlay-managed",
                    "⚠️  Outer VLAN is BD identity - cannot be changed"
                ],
                validation_rules=[
                    "Must have outer VLAN",
                    "Customer interfaces need manipulation",
                    "Infrastructure interfaces are read-only"
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
                    "💡 Customer interfaces use explicit outer-tag and inner-tag",
                    "⚠️  Expert mode - changes affect customer QinQ configuration",
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
    
    def display_bd_type_info(self, bridge_domain: Dict):
        """Display BD type information and editing guidance"""
        
        dnaas_type = bridge_domain.get('dnaas_type', 'unknown')
        profile = self.get_profile(dnaas_type)
        
        print(f"\n🧠 BD TYPE ANALYSIS")
        print("="*50)
        
        if profile:
            print(f"🎯 Type: {profile.common_name} ({profile.dnaas_type})")
            print(f"📊 Usage: {profile.percentage}% of all bridge domains")
            print(f"🔧 Complexity: {profile.complexity.value.title()}")
            print(f"📋 Description: {profile.description}")
            print(f"⚙️  Config Pattern: {profile.interface_config_pattern}")
            
            if profile.editing_tips:
                print(f"\n💡 {profile.common_name} BD Tips:")
                for tip in profile.editing_tips:
                    print(f"   {tip}")
        else:
            print(f"🎯 Type: {dnaas_type} (Specialized/Unknown)")
            print("🔧 Complexity: Specialized configuration")
            print("💡 Using generic editing options")


# Convenience functions
def analyze_bridge_domain_interfaces(bridge_domain: Dict) -> InterfaceAnalysis:
    """Convenience function to analyze BD interfaces"""
    analyzer = BDInterfaceAnalyzer()
    return analyzer.analyze_bd_interfaces(bridge_domain)


def get_bd_type_profile(dnaas_type: str) -> Optional[BDTypeProfile]:
    """Convenience function to get BD type profile"""
    registry = BDTypeRegistry()
    return registry.get_profile(dnaas_type)


def display_bd_type_information(bridge_domain: Dict):
    """Convenience function to display BD type info"""
    registry = BDTypeRegistry()
    registry.display_bd_type_info(bridge_domain)
