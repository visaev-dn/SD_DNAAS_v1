#!/usr/bin/env python3
"""
BD Editor Validation System

Comprehensive validation system for BD editing that provides type-specific
validation rules and prevents invalid configurations.
"""

import logging
from typing import Dict, List
from .data_models import ValidationResult, ValidationError
from .interface_analyzer import BDInterfaceAnalyzer

logger = logging.getLogger(__name__)


class TypeAwareValidator:
    """Comprehensive validation system for BD editing"""
    
    def __init__(self):
        self.interface_analyzer = BDInterfaceAnalyzer()
        
    def validate_bd_editing_session(self, bridge_domain: Dict) -> ValidationResult:
        """Validate BD is in good state for editing"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            # Check BD type is supported
            dnaas_type = bridge_domain.get('dnaas_type', 'unknown')
            if dnaas_type == 'unknown':
                validation.add_error("BD type unknown - cannot determine editing rules")
            
            # Check BD has required fields
            required_fields = ['name', 'vlan_id', 'username']
            for field in required_fields:
                if not bridge_domain.get(field):
                    validation.add_error(f"Missing required field: {field}")
            
            # Check interface data integrity
            devices = bridge_domain.get('devices', {})
            if not devices:
                validation.add_warning("BD has no device data")
            else:
                # Check each device has interface data
                for device_name, device_data in devices.items():
                    interfaces = device_data.get('interfaces', [])
                    if not interfaces:
                        validation.add_warning(f"Device {device_name} has no interfaces")
            
            # Validate BD type specific requirements
            type_validation = self._validate_bd_type_requirements(bridge_domain)
            validation.merge(type_validation)
            
        except Exception as e:
            logger.error(f"Error validating BD editing session: {e}")
            validation.add_error(f"Validation system error: {e}")
        
        return validation
    
    def validate_interface_addition(self, bd_type: str, interface_config: Dict) -> ValidationResult:
        """Validate interface addition against BD type rules"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            device = interface_config.get('device')
            interface = interface_config.get('interface')
            config = interface_config.get('config', '')
            
            # Basic validation
            if not device or not interface:
                validation.add_error("Device and interface are required")
                return validation
            
            # Infrastructure protection
            if self.interface_analyzer.is_infrastructure_interface(interface, ''):
                validation.add_error(f"Cannot edit infrastructure interface: {interface}")
                validation.add_error("Infrastructure interfaces are managed by network overlay")
                return validation
            
            # Type-specific validation - validate the interface config, not individual CLI commands
            if bd_type == "DNAAS_TYPE_4A_SINGLE_TAGGED":
                type_validation = self._validate_single_tagged_interface(interface_config)
            elif bd_type == "DNAAS_TYPE_2A_QINQ_SINGLE_BD":
                type_validation = self._validate_qinq_single_interface(interface_config)
            elif bd_type == "DNAAS_TYPE_1_DOUBLE_TAGGED":
                type_validation = self._validate_double_tagged_interface(interface_config)
            else:
                type_validation = self._validate_generic_interface(interface_config)
            
            validation.merge(type_validation)
            
        except Exception as e:
            logger.error(f"Error validating interface addition: {e}")
            validation.add_error(f"Validation error: {e}")
        
        return validation
    
    def validate_interface_removal(self, bd_type: str, interface_config: Dict, remaining_interfaces: List[Dict]) -> ValidationResult:
        """Validate interface removal"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            interface = interface_config.get('interface', '')
            
            # Cannot remove infrastructure interfaces
            if self.interface_analyzer.is_infrastructure_interface(interface, ''):
                validation.add_error(f"Cannot remove infrastructure interface: {interface}")
                validation.add_error("Infrastructure interfaces are managed by network overlay")
                return validation
            
            # Check if this would leave BD with no customer interfaces
            customer_interfaces_remaining = [
                intf for intf in remaining_interfaces 
                if not self.interface_analyzer.is_infrastructure_interface(intf.get('interface', ''), intf.get('role', ''))
            ]
            
            if len(customer_interfaces_remaining) == 0:
                validation.add_warning("Removing last customer interface - BD will have no customer connectivity")
                validation.add_warning("Consider keeping at least one customer interface for service connectivity")
            
        except Exception as e:
            logger.error(f"Error validating interface removal: {e}")
            validation.add_error(f"Validation error: {e}")
        
        return validation
    
    def validate_changeset(self, bridge_domain: Dict, changes: List[Dict]) -> ValidationResult:
        """Validate entire changeset for consistency"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            bd_type = bridge_domain.get('dnaas_type', 'unknown')
            
            # Validate each change individually
            for change in changes:
                action = change.get('action', '')
                
                if action.startswith('add_') and 'interface' in action:
                    change_validation = self.validate_interface_addition(bd_type, change.get('interface', {}))
                elif action.startswith('remove_') and 'interface' in action:
                    # Get remaining interfaces after this removal
                    remaining = self._calculate_remaining_interfaces(bridge_domain, changes, change)
                    change_validation = self.validate_interface_removal(bd_type, change.get('interface', {}), remaining)
                else:
                    # Generic change validation
                    change_validation = ValidationResult(is_valid=True)
                
                validation.merge(change_validation)
            
            # Validate changeset consistency
            consistency_validation = self._validate_changeset_consistency(bridge_domain, changes)
            validation.merge(consistency_validation)
            
        except Exception as e:
            logger.error(f"Error validating changeset: {e}")
            validation.add_error(f"Changeset validation error: {e}")
        
        return validation
    
    def _validate_bd_type_requirements(self, bridge_domain: Dict) -> ValidationResult:
        """Validate BD meets type-specific requirements"""
        
        validation = ValidationResult(is_valid=True)
        
        bd_type = bridge_domain.get('dnaas_type', 'unknown')
        vlan_id = bridge_domain.get('vlan_id')
        
        if bd_type == "DNAAS_TYPE_4A_SINGLE_TAGGED":
            if not vlan_id:
                validation.add_error("Single-tagged BD must have VLAN ID")
        elif bd_type == "DNAAS_TYPE_2A_QINQ_SINGLE_BD":
            if not vlan_id:
                validation.add_error("QinQ single BD must have outer VLAN (stored as vlan_id)")
        elif bd_type == "DNAAS_TYPE_1_DOUBLE_TAGGED":
            if not vlan_id:
                validation.add_error("Double-tagged BD must have inner VLAN (stored as vlan_id)")
            # Note: outer_vlan should be extracted from interface configuration
        
        return validation
    
    def _validate_single_tagged_interface(self, interface_config: Dict) -> ValidationResult:
        """Validate single-tagged interface configuration"""
        
        validation = ValidationResult(is_valid=True)
        
        # Validate VLAN ID is present and valid
        vlan_id = interface_config.get('vlan_id')
        if not vlan_id:
            validation.add_error("Single-tagged interfaces must have VLAN ID")
        elif not isinstance(vlan_id, int) or not (1 <= vlan_id <= 4094):
            validation.add_error(f"Invalid VLAN ID: {vlan_id} (must be 1-4094)")
        
        # Validate device and interface are present
        device = interface_config.get('device')
        interface = interface_config.get('interface')
        
        if not device:
            validation.add_error("Device name is required")
        if not interface:
            validation.add_error("Interface name is required")
        
        # Check for proper interface naming
        if interface and not ('ge100-' in interface or 'bundle-' in interface):
            validation.add_warning(f"Unusual interface name format: {interface}")
        
        return validation
    
    def _validate_qinq_single_interface(self, interface_config: Dict) -> ValidationResult:
        """Validate QinQ single BD customer interface configuration"""
        
        validation = ValidationResult(is_valid=True)
        
        # Validate outer VLAN is present and valid
        outer_vlan = interface_config.get('outer_vlan') or interface_config.get('vlan_id')
        if not outer_vlan:
            validation.add_error("QinQ customer interfaces must have outer VLAN")
        elif not isinstance(outer_vlan, int) or not (1 <= outer_vlan <= 4094):
            validation.add_error(f"Invalid outer VLAN: {outer_vlan} (must be 1-4094)")
        
        # Validate device and interface are present
        device = interface_config.get('device')
        interface = interface_config.get('interface')
        
        if not device:
            validation.add_error("Device name is required")
        if not interface:
            validation.add_error("Interface name is required")
        
        return validation
    
    def _validate_double_tagged_interface(self, interface_config: Dict) -> ValidationResult:
        """Validate double-tagged interface configuration"""
        
        validation = ValidationResult(is_valid=True)
        
        # Validate outer and inner VLANs are present and valid
        outer_vlan = interface_config.get('outer_vlan')
        inner_vlan = interface_config.get('inner_vlan') or interface_config.get('vlan_id')
        
        if not outer_vlan:
            validation.add_error("Double-tagged interfaces must have outer VLAN")
        elif not isinstance(outer_vlan, int) or not (1 <= outer_vlan <= 4094):
            validation.add_error(f"Invalid outer VLAN: {outer_vlan} (must be 1-4094)")
        
        if not inner_vlan:
            validation.add_error("Double-tagged interfaces must have inner VLAN")
        elif not isinstance(inner_vlan, int) or not (1 <= inner_vlan <= 4094):
            validation.add_error(f"Invalid inner VLAN: {inner_vlan} (must be 1-4094)")
        
        # Validate device and interface are present
        device = interface_config.get('device')
        interface = interface_config.get('interface')
        
        if not device:
            validation.add_error("Device name is required")
        if not interface:
            validation.add_error("Interface name is required")
        
        return validation
    
    def _validate_generic_interface(self, interface_config: Dict) -> ValidationResult:
        """Validate generic interface configuration"""
        
        validation = ValidationResult(is_valid=True)
        
        # Basic validation for generic configurations
        device = interface_config.get('device')
        interface = interface_config.get('interface')
        
        if not device:
            validation.add_error("Device name is required")
        if not interface:
            validation.add_error("Interface name is required")
        
        # Warn about unknown BD type
        validation.add_warning("Unknown BD type - using generic validation")
        
        return validation
    
    def _validate_changeset_consistency(self, bridge_domain: Dict, changes: List[Dict]) -> ValidationResult:
        """Validate changeset for internal consistency"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            # Check for conflicting changes
            interface_changes = {}
            
            for change in changes:
                interface_info = change.get('interface', {})
                device = interface_info.get('device')
                interface = interface_info.get('interface')
                action = change.get('action', '')
                
                if device and interface:
                    interface_key = f"{device}:{interface}"
                    
                    if interface_key not in interface_changes:
                        interface_changes[interface_key] = []
                    
                    interface_changes[interface_key].append(action)
            
            # Check for conflicting actions on same interface
            for interface_key, actions in interface_changes.items():
                if len(actions) > 1:
                    if 'add_customer_interface' in actions and 'remove_customer_interface' in actions:
                        validation.add_warning(f"Conflicting add/remove actions for {interface_key}")
            
            # Check for VLAN conflicts
            vlan_validation = self._validate_vlan_consistency(bridge_domain, changes)
            validation.merge(vlan_validation)
            
        except Exception as e:
            logger.error(f"Error validating changeset consistency: {e}")
            validation.add_error(f"Consistency validation error: {e}")
        
        return validation
    
    def _validate_vlan_consistency(self, bridge_domain: Dict, changes: List[Dict]) -> ValidationResult:
        """Validate VLAN consistency across changes"""
        
        validation = ValidationResult(is_valid=True)
        
        bd_type = bridge_domain.get('dnaas_type', 'unknown')
        bd_vlan_id = bridge_domain.get('vlan_id')
        
        # For single-tagged BDs, all interfaces should use same VLAN
        if bd_type == "DNAAS_TYPE_4A_SINGLE_TAGGED":
            for change in changes:
                if change.get('action', '').startswith('add_'):
                    interface_vlan = change.get('interface', {}).get('vlan_id')
                    if interface_vlan and interface_vlan != bd_vlan_id:
                        validation.add_error(f"Interface VLAN {interface_vlan} doesn't match BD VLAN {bd_vlan_id}")
        
        # For QinQ BDs, outer VLAN should match BD VLAN
        elif bd_type == "DNAAS_TYPE_2A_QINQ_SINGLE_BD":
            for change in changes:
                if change.get('action', '').startswith('add_'):
                    outer_vlan = change.get('interface', {}).get('outer_vlan')
                    if outer_vlan and outer_vlan != bd_vlan_id:
                        validation.add_error(f"Interface outer VLAN {outer_vlan} doesn't match BD outer VLAN {bd_vlan_id}")
        
        return validation
    
    def _calculate_remaining_interfaces(self, bridge_domain: Dict, changes: List[Dict], current_change: Dict) -> List[Dict]:
        """Calculate interfaces that would remain after applying changes"""
        
        # This is a simplified version - full implementation would apply all changes
        # and calculate the resulting interface list
        
        working_interfaces = []
        
        try:
            # Start with current interfaces
            devices = bridge_domain.get('devices', {})
            for device_name, device_info in devices.items():
                interfaces = device_info.get('interfaces', [])
                for interface in interfaces:
                    working_interfaces.append({
                        'device': device_name,
                        'interface': interface.get('name'),
                        'role': interface.get('role')
                    })
            
            # Apply changes (simplified)
            for change in changes:
                action = change.get('action', '')
                interface_info = change.get('interface', {})
                
                if action.startswith('add_'):
                    working_interfaces.append(interface_info)
                elif action.startswith('remove_'):
                    # Remove matching interface
                    device = interface_info.get('device')
                    interface = interface_info.get('interface')
                    working_interfaces = [
                        intf for intf in working_interfaces 
                        if not (intf.get('device') == device and intf.get('interface') == interface)
                    ]
        
        except Exception as e:
            logger.error(f"Error calculating remaining interfaces: {e}")
        
        return working_interfaces


# Convenience functions
def validate_bd_for_editing(bridge_domain: Dict) -> ValidationResult:
    """Convenience function to validate BD for editing"""
    validator = TypeAwareValidator()
    return validator.validate_bd_editing_session(bridge_domain)


def validate_interface_change(bd_type: str, interface_config: Dict) -> ValidationResult:
    """Convenience function to validate interface change"""
    validator = TypeAwareValidator()
    return validator.validate_interface_addition(bd_type, interface_config)
