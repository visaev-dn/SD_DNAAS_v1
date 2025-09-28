"""
Smart Interface Filtering Service

Provides intelligent interface filtering and categorization for BD-Builder and BD-Editor,
implementing business rules to guide users to optimal interface selections.
"""

import re
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .data_models import InterfaceDiscoveryData


@dataclass
class InterfaceOption:
    """Enhanced interface information with smart categorization"""
    name: str
    type: str  # physical, bundle, subinterface
    admin_status: str
    oper_status: str
    description: str
    device_name: str
    
    # Smart categorization
    category: str  # recommended, available, caution, configured, excluded
    warnings: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)
    
    # Additional context
    existing_subinterfaces: List[str] = field(default_factory=list)
    bundle_info: Optional[Dict] = None
    is_uplink: bool = False
    is_management: bool = False
    is_infrastructure: bool = False
    
    # Metadata
    discovered_at: Optional[datetime] = None
    last_seen: Optional[str] = None


class SmartInterfaceFilter:
    """
    Intelligent interface filtering service that applies business rules
    to categorize interfaces for optimal user selection.
    """
    
    def __init__(self, db_path: str = "instance/lab_automation.db"):
        self.db_path = db_path
        self.business_rules = InterfaceBusinessRules()
    
    def get_smart_interface_options(self, device_name: str) -> Dict[str, List[InterfaceOption]]:
        """
        Get intelligently filtered and categorized interfaces for a device.
        
        Returns:
            Dict with categories: safe, available, caution, configured
        """
        raw_interfaces = self._get_device_interfaces(device_name)
        
        categorized = {
            "safe": [],
            "available": [],
            "caution": [],
            "configured": []
        }
        
        for interface_data in raw_interfaces:
            interface_option = self._create_interface_option(interface_data)
            
            # Skip excluded interfaces
            if interface_option.category == "excluded":
                continue
                
            categorized[interface_option.category].append(interface_option)
        
        # Sort each category for better UX
        for category in categorized:
            categorized[category].sort(key=lambda x: (x.type, x.name))
        
        return categorized
    
    def get_device_interface_summary(self, device_name: str) -> Dict[str, int]:
        """Get summary counts for device interface categories"""
        smart_options = self.get_smart_interface_options(device_name)
        
        # Calculate total available for configuration (safe + available + caution)
        total_configurable = (len(smart_options["safe"]) + 
                            len(smart_options["available"]) + 
                            len(smart_options["caution"]))
        
        return {
            "safe": len(smart_options["safe"]),
            "available": len(smart_options["available"]),
            "caution": len(smart_options["caution"]),
            "configured": len(smart_options["configured"]),
            "total": sum(len(interfaces) for interfaces in smart_options.values()),
            "total_configurable": total_configurable
        }
    
    def get_all_devices_with_smart_preview(self) -> List[Dict]:
        """Get all devices with interface availability preview"""
        devices = []
        
        # Get all devices that have interface data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT device_name, COUNT(*) as total_interfaces
            FROM interface_discovery 
            GROUP BY device_name
            ORDER BY device_name
        """)
        
        for device_name, total_count in cursor.fetchall():
            interface_counts = self.get_device_interface_summary(device_name)
            
            devices.append({
                "name": device_name,
                "interface_counts": interface_counts,
                "status": self._get_device_status(device_name),
                "last_discovery": self._get_last_discovery_time(device_name)
            })
        
        conn.close()
        return devices
    
    def _create_interface_option(self, interface_data: InterfaceDiscoveryData) -> InterfaceOption:
        """Convert raw interface data to smart interface option"""
        
        # Create base interface option
        option = InterfaceOption(
            name=interface_data.interface_name,
            type=interface_data.interface_type,
            admin_status=interface_data.admin_status,
            oper_status=interface_data.oper_status,
            description=interface_data.description,
            device_name=interface_data.device_name,
            category="available",  # Default, will be updated
            discovered_at=interface_data.discovered_at
        )
        
        # Apply business rules to categorize and enrich
        option.category = self.business_rules.categorize_interface(interface_data, option)
        option.warnings = self.business_rules.get_interface_warnings(interface_data, option)
        option.tips = self.business_rules.get_interface_tips(interface_data, option)
        
        # Add contextual information
        if option.type == "physical":
            option.existing_subinterfaces = self._get_existing_subinterfaces(
                interface_data.device_name, interface_data.interface_name
            )
        
        # Set flags for quick filtering
        option.is_uplink = self.business_rules.is_uplink_interface(interface_data.interface_name)
        option.is_management = self.business_rules.is_management_interface(interface_data.interface_name)
        option.is_infrastructure = self.business_rules.is_infrastructure_interface(interface_data.interface_name)
        
        return option
    
    def _get_device_interfaces(self, device_name: str) -> List[InterfaceDiscoveryData]:
        """Get all interface data for a device"""
        interfaces = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT device_name, interface_name, interface_type, description,
                       admin_status, oper_status, bundle_id, is_bundle_member,
                       discovered_at, device_reachable, discovery_errors
                FROM interface_discovery 
                WHERE device_name = ?
                ORDER BY interface_name
            """, (device_name,))
            
            for row in cursor.fetchall():
                interface = InterfaceDiscoveryData(
                    device_name=row[0],
                    interface_name=row[1],
                    interface_type=row[2],
                    description=row[3],
                    admin_status=row[4],
                    oper_status=row[5],
                    bundle_id=row[6],
                    is_bundle_member=bool(row[7]),
                    discovered_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    device_reachable=bool(row[9]),
                    discovery_errors=[]  # Parse JSON if needed
                )
                interfaces.append(interface)
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error getting interfaces for {device_name}: {e}")
        
        return interfaces
    
    def _get_existing_subinterfaces(self, device_name: str, parent_interface: str) -> List[str]:
        """Get existing subinterfaces for a physical interface"""
        subinterfaces = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Look for subinterfaces that start with parent interface name
            cursor.execute("""
                SELECT interface_name
                FROM interface_discovery 
                WHERE device_name = ? 
                AND interface_name LIKE ?
                AND interface_name != ?
                AND interface_type = 'subinterface'
                ORDER BY interface_name
            """, (device_name, f"{parent_interface}.%", parent_interface))
            
            subinterfaces = [row[0] for row in cursor.fetchall()]
            conn.close()
            
        except Exception as e:
            print(f"❌ Error getting subinterfaces for {parent_interface}: {e}")
        
        return subinterfaces
    
    def _get_device_status(self, device_name: str) -> str:
        """Get device online/offline status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT device_reachable
                FROM interface_discovery 
                WHERE device_name = ?
                ORDER BY discovered_at DESC
                LIMIT 1
            """, (device_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return "online"
            else:
                return "offline"
                
        except Exception:
            return "unknown"
    
    def _get_last_discovery_time(self, device_name: str) -> Optional[str]:
        """Get last discovery time for device"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(discovered_at)
                FROM interface_discovery 
                WHERE device_name = ?
            """, (device_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else None
            
        except Exception:
            return None


class InterfaceBusinessRules:
    """
    Business rules engine for interface categorization and recommendations.
    Encapsulates network engineering best practices and organizational policies.
    """
    
    def __init__(self):
        # Uplink patterns - interfaces reserved for network infrastructure
        self.uplink_patterns = [
            r"bundle-60000",      # Primary uplink bundle
            r"bundle-6[0-9]{4}",  # Other uplink bundles (60000-69999)
        ]
        
        # Management interface patterns
        self.management_patterns = [
            r"mgmt.*",
            r"management.*",
            r"oob.*",
            r"console.*"
        ]
        
        # Infrastructure interface patterns
        self.infrastructure_patterns = [
            r"loopback.*",
            r"lo[0-9]+",
            r".*-spine-.*",
            r".*-superspine-.*"
        ]
        
        # Customer-facing interface patterns (preferred for services)
        self.customer_patterns = [
            r"ge100-0/0/.*",        # Physical customer interfaces
            r"bundle-[1-9][0-9]*",  # Customer bundles (not 60000+)
            r"bundle-[1-5][0-9]{2}" # Customer bundles (100-599)
        ]
    
    def categorize_interface(self, interface_data: InterfaceDiscoveryData, option: InterfaceOption) -> str:
        """
        Apply business rules to categorize interface.
        
        Categories:
        - excluded: Hidden from user (uplinks, management)
        - safe: Best choices for customer services (ready to configure)
        - available: Good choices with minor considerations
        - caution: Usable but with warnings (excluding admin-down)
        - configured: Already has configuration (reference only)
        """
        
        interface_name = interface_data.interface_name
        
        # EXCLUSION RULES - Hide these from user
        if self.is_uplink_interface(interface_name):
            return "excluded"
        
        if self.is_management_interface(interface_name):
            return "excluded"
        
        if self.is_infrastructure_interface(interface_name):
            return "excluded"
        
        # CONFIGURED INTERFACES - Show for reference but not selectable
        if interface_data.interface_type == "subinterface" and "(L2)" in interface_name:
            return "configured"
        
        # SAFE RULES - Best choices
        if self._is_safe_interface(interface_data, option):
            return "safe"
        
        # CAUTION RULES - Show with warnings
        if self._has_caution_conditions(interface_data, option):
            return "caution"
        
        # Default to available
        return "available"
    
    def get_interface_warnings(self, interface_data: InterfaceDiscoveryData, option: InterfaceOption) -> List[str]:
        """Generate warnings for interface"""
        warnings = []
        
        # Status warnings - NOTE: admin-down is NOT considered a warning anymore (it's safe)
        if interface_data.oper_status == "down" and interface_data.admin_status == "up":
            warnings.append("Interface is operationally down - check cable/remote end")
        
        # Existing configuration warnings
        if option.existing_subinterfaces:
            sub_list = ", ".join(option.existing_subinterfaces[:3])
            if len(option.existing_subinterfaces) > 3:
                sub_list += f" (+{len(option.existing_subinterfaces) - 3} more)"
            warnings.append(f"Has existing L2 subinterfaces: {sub_list}")
        
        # Bundle membership warnings
        if interface_data.is_bundle_member:
            warnings.append(f"Member of bundle {interface_data.bundle_id} - cannot be used independently")
        
        return warnings
    
    def get_interface_tips(self, interface_data: InterfaceDiscoveryData, option: InterfaceOption) -> List[str]:
        """Generate helpful tips for interface"""
        tips = []
        
        # Positive recommendations
        if self._is_customer_interface(interface_data.interface_name):
            if interface_data.admin_status in ["up", "admin-down"] and interface_data.oper_status == "up":
                if not option.existing_subinterfaces:
                    tips.append("✅ Safe choice - ready for service configuration")
            elif interface_data.admin_status == "admin-down":
                tips.append("💡 Safe to use - just needs admin enable")
        
        # Bundle recommendations
        if interface_data.interface_type == "bundle" and not self.is_uplink_interface(interface_data.interface_name):
            if interface_data.admin_status == "up":
                tips.append("💡 Bundle interface - good for high-bandwidth services")
        
        # Physical interface tips
        if interface_data.interface_type == "physical":
            if not option.existing_subinterfaces and interface_data.admin_status in ["up", "admin-down"]:
                tips.append("💡 Clean physical interface - no existing configuration conflicts")
        
        return tips
    
    def is_uplink_interface(self, interface_name: str) -> bool:
        """Check if interface is an uplink (should be excluded)"""
        return any(re.match(pattern, interface_name) for pattern in self.uplink_patterns)
    
    def is_management_interface(self, interface_name: str) -> bool:
        """Check if interface is for management (should be excluded)"""
        return any(re.match(pattern, interface_name) for pattern in self.management_patterns)
    
    def is_infrastructure_interface(self, interface_name: str) -> bool:
        """Check if interface is infrastructure (should be excluded)"""
        return any(re.match(pattern, interface_name) for pattern in self.infrastructure_patterns)
    
    def _is_customer_interface(self, interface_name: str) -> bool:
        """Check if interface is customer-facing (preferred for services)"""
        return any(re.match(pattern, interface_name) for pattern in self.customer_patterns)
    
    def _is_safe_interface(self, interface_data: InterfaceDiscoveryData, option: InterfaceOption) -> bool:
        """Check if interface should be in safe category"""
        
        # Must be customer-facing
        if not self._is_customer_interface(interface_data.interface_name):
            return False
        
        # Admin-down is now considered SAFE (just needs enable)
        # Must be operationally up OR admin-down with oper up
        if interface_data.oper_status != "up":
            return False
        
        # Admin status can be up or admin-down (both are safe)
        if interface_data.admin_status not in ["up", "admin-down"]:
            return False
        
        # Physical interfaces should not have existing subinterfaces
        if interface_data.interface_type == "physical" and option.existing_subinterfaces:
            return False
        
        # Should not be a bundle member
        if interface_data.is_bundle_member:
            return False
        
        return True
    
    def _has_caution_conditions(self, interface_data: InterfaceDiscoveryData, option: InterfaceOption) -> bool:
        """Check if interface should be in caution category"""
        
        # NOTE: Admin-down interfaces are NO LONGER considered caution (they're safe)
        
        # Interfaces with existing subinterfaces
        if option.existing_subinterfaces:
            return True
        
        # Bundle members
        if interface_data.is_bundle_member:
            return True
        
        # Operationally down but admin up
        if interface_data.admin_status == "up" and interface_data.oper_status == "down":
            return True
        
        return False


# Convenience functions for CLI integration
def get_smart_interface_options(device_name: str) -> Dict[str, List[InterfaceOption]]:
    """Get smart interface options for a device"""
    filter_service = SmartInterfaceFilter()
    return filter_service.get_smart_interface_options(device_name)


def get_devices_with_smart_preview() -> List[Dict]:
    """Get all devices with interface availability preview"""
    filter_service = SmartInterfaceFilter()
    return filter_service.get_all_devices_with_smart_preview()


def get_device_interface_menu(device_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Enhanced interface selection menu with smart filtering.
    
    Returns:
        Tuple of (device_name, interface_name) or (None, None) if cancelled
    """
    
    filter_service = SmartInterfaceFilter()
    interfaces = filter_service.get_smart_interface_options(device_name)
    
    print(f"\n🎯 Smart Interface Selection: {device_name}")
    print("=" * 60)
    
    # Build selection menu
    options = []
    option_num = 1
    
    # Recommended interfaces (show first)
    if interfaces["recommended"]:
        print(f"\n✅ RECOMMENDED INTERFACES ({len(interfaces['recommended'])} available):")
        for intf in interfaces["recommended"]:
            print(f"   {option_num:2d}. {intf.name} ({intf.type}) - {intf.admin_status}/{intf.oper_status}")
            if intf.tips:
                print(f"       💡 {intf.tips[0]}")
            options.append(intf)
            option_num += 1
    
    # Available interfaces
    if interfaces["available"]:
        print(f"\n🔵 AVAILABLE INTERFACES ({len(interfaces['available'])} available):")
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
            for intf in interfaces["caution"]:
                print(f"   {option_num:2d}. {intf.name} ({intf.type}) - {intf.admin_status}/{intf.oper_status}")
                for warning in intf.warnings[:2]:  # Show first 2 warnings
                    print(f"       ⚠️  {warning}")
                options.append(intf)
                option_num += 1
    
    if not options:
        print("❌ No suitable interfaces found for this device")
        return None, None
    
    # Interface selection
    try:
        choice = int(input(f"\nSelect interface [1-{len(options)}] (0 to cancel): ").strip())
        
        if choice == 0:
            print("❌ Interface selection cancelled")
            return None, None
        
        if 1 <= choice <= len(options):
            selected = options[choice - 1]
            
            # Show warnings and confirm if needed
            if selected.warnings:
                print(f"\n⚠️  WARNINGS for {selected.name}:")
                for warning in selected.warnings:
                    print(f"   • {warning}")
                
                confirm = input("\nContinue with this interface? (y/N): ").lower() == 'y'
                if not confirm:
                    print("❌ Interface selection cancelled")
                    return None, None
            
            print(f"\n✅ Selected: {device_name} - {selected.name}")
            return device_name, selected.name
        else:
            print("❌ Invalid selection")
            return None, None
            
    except (ValueError, KeyboardInterrupt):
        print("❌ Interface selection cancelled")
        return None, None
