#!/usr/bin/env python3
"""
Enhanced CLI Display for Device and Interface Selection

Provides improved, organized display for device and interface selection
with tree-style categorization and comprehensive single-list interface display.
"""

import re
from typing import Dict, List, Tuple, Optional


class EnhancedDeviceDisplay:
    """Enhanced device display with tree-style categorization"""
    
    def display_devices_tree_style(self, devices: List[Dict]) -> str:
        """Display devices in organized tree structure"""
        
        # Categorize devices
        categorized = self._categorize_devices(devices)
        
        print(f"🎯 Smart Device Selection ({len(devices)} devices available)")
        print("💡 Enter device number OR shorthand (e.g., 'b-15' for DNAAS-LEAF-B15)")
        print()
        
        device_counter = 1
        device_map = {}
        
        # LEAF devices by series
        if categorized['leaf']:
            print("📊 LEAF DEVICES:")
            
            for series, series_devices in categorized['leaf'].items():
                print(f"┌─ {series}-Series ({len(series_devices)} devices)")
                
                # Show first 5 devices in series
                for i, device in enumerate(series_devices[:5]):
                    counts = device['interface_counts']
                    shorthand = self._get_device_shorthand(device['name'])
                    
                    print(f"│  {device_counter:2d}. {shorthand:<8} {device['name']:<22} ✅{counts['safe']:<3} 🔵{counts['available']:<3} 🎯{counts['total_configurable']}")
                    
                    # Map both number and shorthand
                    device_map[str(device_counter)] = device
                    device_map[shorthand.lower()] = device
                    device_counter += 1
                
                # Handle remaining devices in series
                for i, device in enumerate(series_devices[5:], 6):
                    shorthand = self._get_device_shorthand(device['name'])
                    device_map[str(device_counter)] = device
                    device_map[shorthand.lower()] = device
                    device_counter += 1
                
                # Show remaining count
                if len(series_devices) > 5:
                    remaining = len(series_devices) - 5
                    print(f"│  ... and {remaining} more {series}-series devices")
                
                print("│")
        
        # SPINE devices
        if categorized['spine']:
            print("🔗 SPINE DEVICES:")
            for device in categorized['spine']:
                counts = device['interface_counts']
                shorthand = self._get_device_shorthand(device['name'])
                
                print(f"   {device_counter:2d}. {shorthand:<8} {device['name']:<22} ✅{counts['safe']:<3} 🔵{counts['available']:<3} 🎯{counts['total_configurable']}")
                
                device_map[str(device_counter)] = device
                device_map[shorthand.lower()] = device
                device_counter += 1
        
        # SuperSpine devices
        if categorized['superspine']:
            print("🌐 SUPERSPINE DEVICES:")
            for device in categorized['superspine']:
                counts = device['interface_counts']
                shorthand = self._get_device_shorthand(device['name'])
                
                print(f"   {device_counter:2d}. {shorthand:<8} {device['name']:<22} ✅{counts['safe']:<3} 🔵{counts['available']:<3} 🎯{counts['total_configurable']}")
                
                device_map[str(device_counter)] = device
                device_map[shorthand.lower()] = device
                device_counter += 1
        
        # Selection
        while True:
            choice = input(f"\nSelect device [1-{len(devices)}] or shorthand (0 to cancel): ").strip().lower()
            
            if choice == '0':
                print("❌ Device selection cancelled")
                return None
            elif choice in device_map:
                selected_device = device_map[choice]
                print(f"✅ Selected: {selected_device['name']}")
                return selected_device['name']
            else:
                print(f"❌ Invalid selection: {choice}")
                print("💡 Try device number (1-52) or shorthand (e.g., 'b-15')")
                # Continue loop for retry
    
    def _categorize_devices(self, devices: List[Dict]) -> Dict:
        """Categorize devices by type and series"""
        
        categorized = {
            'leaf': {},
            'spine': [],
            'superspine': []
        }
        
        for device in devices:
            name = device['name']
            
            if 'LEAF-A' in name:
                if 'A' not in categorized['leaf']:
                    categorized['leaf']['A'] = []
                categorized['leaf']['A'].append(device)
            elif 'LEAF-B' in name:
                if 'B' not in categorized['leaf']:
                    categorized['leaf']['B'] = []
                categorized['leaf']['B'].append(device)
            elif 'LEAF-C' in name:
                if 'C' not in categorized['leaf']:
                    categorized['leaf']['C'] = []
                categorized['leaf']['C'].append(device)
            elif 'LEAF-D' in name or 'LEAF-F' in name:
                if 'Other' not in categorized['leaf']:
                    categorized['leaf']['Other'] = []
                categorized['leaf']['Other'].append(device)
            elif 'SPINE-' in name and 'SuperSpine' not in name:
                categorized['spine'].append(device)
            elif 'SuperSpine' in name:
                categorized['superspine'].append(device)
        
        return categorized
    
    def _get_device_shorthand(self, device_name: str) -> str:
        """Generate shorthand for device name"""
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
            return device_name[:8].lower()


class EnhancedInterfaceDisplay:
    """Enhanced interface display with single comprehensive list"""
    
    def display_interfaces_comprehensive_list(self, device_name: str, interfaces: Dict) -> Tuple[Optional[str], Optional[str]]:
        """Display all interfaces in single organized list"""
        
        print(f"🎯 Smart Interface Selection: {device_name}")
        print("💡 All interfaces shown in priority order - select any number")
        print()
        
        option_counter = 1
        interface_map = {}
        
        # 1. ALREADY CONFIGURED (Reference - least important, show first)
        configured = interfaces.get('configured', [])
        if configured:
            print(f"📊 ALREADY CONFIGURED (Reference - {len(configured)} interfaces):")
            
            # Show first 5 configured interfaces
            for i, intf in enumerate(configured[:5]):
                ref_id = f"R{i+1}"
                status = f"{intf.admin_status}/{intf.oper_status}"
                vlan_info = self._extract_vlan_from_interface(intf.name)
                
                print(f" {ref_id:>3}. {intf.name:<20} ({self._get_type_short(intf.type)}) {status:<13} 🔒 {vlan_info}")
                interface_map[ref_id.lower()] = intf
            
            # Show remaining count
            if len(configured) > 5:
                remaining = len(configured) - 5
                print(f" ... and {remaining} more configured interfaces (R6-R{len(configured)})")
                
                # Map remaining references
                for i, intf in enumerate(configured[5:], 6):
                    interface_map[f"r{i}"] = intf
            
            print()
        
        # 2. SAFE INTERFACES (Most important - ready to use)
        safe = interfaces.get('safe', [])
        if safe:
            print(f"✅ SAFE INTERFACES (Ready to use - {len(safe)} interfaces):")
            
            for intf in safe:
                status = f"{intf.admin_status}/{intf.oper_status}"
                tip = "✅ Ready for BD config"
                
                print(f"  {option_counter:2d}. {intf.name:<20} ({self._get_type_short(intf.type)}) {status:<13} {tip}")
                interface_map[str(option_counter)] = intf
                option_counter += 1
            
            print()
        
        # 3. AVAILABLE INTERFACES (Good options with minor considerations)
        available = interfaces.get('available', [])
        if available:
            print(f"🔵 AVAILABLE INTERFACES (Minor considerations - {len(available)} interfaces):")
            
            for intf in available:
                status = f"{intf.admin_status}/{intf.oper_status}"
                
                if intf.admin_status == 'admin-down':
                    tip = "💡 Needs admin enable"
                else:
                    tip = "🔵 Good option"
                
                print(f"  {option_counter:2d}. {intf.name:<20} ({self._get_type_short(intf.type)}) {status:<13} {tip}")
                interface_map[str(option_counter)] = intf
                option_counter += 1
            
            print()
        
        # 4. CAUTION INTERFACES (Issues - show last)
        caution = interfaces.get('caution', [])
        if caution:
            print(f"⚠️  CAUTION INTERFACES (Issues - {len(caution)} interfaces):")
            
            for intf in caution:
                status = f"{intf.admin_status}/{intf.oper_status}"
                
                if intf.oper_status == 'down':
                    tip = "⚠️  Check cable/remote"
                elif hasattr(intf, 'existing_subinterfaces') and intf.existing_subinterfaces:
                    tip = f"⚠️  Has {len(intf.existing_subinterfaces)} subinterfaces"
                else:
                    tip = "⚠️  Has warnings"
                
                print(f"  {option_counter:2d}. {intf.name:<20} ({self._get_type_short(intf.type)}) {status:<13} {tip}")
                interface_map[str(option_counter)] = intf
                option_counter += 1
        
        # Selection prompt
        total_selectable = option_counter - 1
        ref_count = len(configured)
        
        if ref_count > 0:
            prompt = f"Select interface [1-{total_selectable}] or [R1-R{ref_count}] for reference (0 to cancel): "
        else:
            prompt = f"Select interface [1-{total_selectable}] (0 to cancel): "
        
        while True:
            choice = input(f"\n{prompt}").strip().lower()
            
            # Return selected interface
            if choice == '0':
                print("❌ Interface selection cancelled")
                return None, None
            elif choice in interface_map:
                selected_intf = interface_map[choice]
                
                if choice.startswith('r'):
                    print(f"💡 Selected configured interface for reference: {selected_intf.name}")
                    print("⚠️  This interface is already configured - showing for reference only")
                    return None, None
                else:
                    device_name = getattr(selected_intf, 'device_name', device_name)
                    print(f"✅ Selected: {device_name} - {selected_intf.name}")
                    return device_name, selected_intf.name
            else:
                print(f"❌ Invalid selection: {choice}")
                if ref_count > 0:
                    print(f"💡 Try interface number (1-{total_selectable}) or reference (R1-R{ref_count})")
                else:
                    print(f"💡 Try interface number (1-{total_selectable})")
                # Continue loop for retry
    
    def _extract_vlan_from_interface(self, interface_name: str) -> str:
        """Extract VLAN info from interface name"""
        if '.' in interface_name:
            vlan = interface_name.split('.')[-1]
            # Handle L2 subinterfaces
            if '(L2)' in interface_name:
                return f"VLAN {vlan} (L2)"
            return f"VLAN {vlan}"
        return "No VLAN"
    
    def _get_type_short(self, interface_type: str) -> str:
        """Get short type indicator"""
        type_map = {
            'physical': 'phy',
            'bundle': 'bun', 
            'subinterface': 'sub',
            'L2': 'L2s'
        }
        
        # Handle L2 subinterfaces
        if '(L2)' in interface_type:
            return 'L2s'
        
        return type_map.get(interface_type, interface_type[:3])


class EnhancedSmartSelection:
    """Enhanced smart selection with improved CLI presentation"""
    
    def __init__(self):
        self.device_display = EnhancedDeviceDisplay()
        self.interface_display = EnhancedInterfaceDisplay()
    
    def enhanced_device_selection_with_shorthand(self) -> Optional[str]:
        """Enhanced device selection with tree-style display"""
        
        try:
            from .smart_filter import get_devices_with_smart_preview
            
            devices = get_devices_with_smart_preview()
            
            if not devices:
                print("❌ No devices with interface data found")
                return None
            
            # Use enhanced tree-style display
            selected_device = self.device_display.display_devices_tree_style(devices)
            
            return selected_device
            
        except Exception as e:
            print(f"❌ Enhanced device selection failed: {e}")
            return None
    
    def enhanced_interface_selection_for_device(self, device_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Enhanced interface selection with comprehensive list"""
        
        try:
            from .smart_filter import get_smart_interface_options
            
            interfaces = get_smart_interface_options(device_name)
            
            if not any(interfaces.values()):
                print(f"❌ No interfaces found for {device_name}")
                return None, None
            
            # Use enhanced comprehensive list display
            return self.interface_display.display_interfaces_comprehensive_list(device_name, interfaces)
            
        except Exception as e:
            print(f"❌ Enhanced interface selection failed: {e}")
            return None, None
    
    def enhanced_interface_selection_complete(self) -> Tuple[Optional[str], Optional[str]]:
        """Complete enhanced interface selection workflow"""
        
        # Step 1: Enhanced device selection
        selected_device = self.enhanced_device_selection_with_shorthand()
        
        if not selected_device:
            return None, None
        
        # Step 2: Enhanced interface selection
        device_name, interface_name = self.enhanced_interface_selection_for_device(selected_device)
        
        return device_name, interface_name


# Convenience functions for integration
def enhanced_device_selection() -> Optional[str]:
    """Convenience function for enhanced device selection"""
    display = EnhancedDeviceDisplay()
    
    try:
        from .smart_filter import get_devices_with_smart_preview
        devices = get_devices_with_smart_preview()
        return display.display_devices_tree_style(devices)
    except Exception as e:
        print(f"❌ Enhanced device selection failed: {e}")
        return None


def enhanced_interface_selection(device_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Convenience function for enhanced interface selection"""
    display = EnhancedInterfaceDisplay()
    
    try:
        from .smart_filter import get_smart_interface_options
        interfaces = get_smart_interface_options(device_name)
        return display.display_interfaces_comprehensive_list(device_name, interfaces)
    except Exception as e:
        print(f"❌ Enhanced interface selection failed: {e}")
        return None, None


def enhanced_smart_selection_complete() -> Tuple[Optional[str], Optional[str]]:
    """Complete enhanced smart selection workflow"""
    selector = EnhancedSmartSelection()
    return selector.enhanced_interface_selection_complete()
