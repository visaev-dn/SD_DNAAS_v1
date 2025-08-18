#!/usr/bin/env python3
"""
Data Validators
Common validation functions for the Lab Automation Framework
"""

import re
import ipaddress
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass

from ..exceptions.base_exceptions import ValidationError


@dataclass
class ValidationRule:
    """Represents a validation rule"""
    field_name: str
    rule_type: str
    rule_value: Any
    error_message: str
    required: bool = True


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    field_errors: Dict[str, List[str]]
    warnings: List[str]


class BaseValidator:
    """Base class for all validators"""
    
    def __init__(self):
        self.errors = []
        self.field_errors = {}
        self.warnings = []
    
    def add_error(self, field: str, message: str) -> None:
        """Add a validation error"""
        self.errors.append(message)
        if field not in self.field_errors:
            self.field_errors[field] = []
        self.field_errors[field].append(message)
    
    def add_warning(self, message: str) -> None:
        """Add a validation warning"""
        self.warnings.append(message)
    
    def get_result(self) -> ValidationResult:
        """Get the validation result"""
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            field_errors=self.field_errors,
            warnings=self.warnings
        )


class StringValidator(BaseValidator):
    """Validator for string fields"""
    
    def validate_required(self, value: Any, field_name: str) -> bool:
        """Validate that a required field is present"""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            self.add_error(field_name, f"{field_name} is required")
            return False
        return True
    
    def validate_length(self, value: str, field_name: str, min_length: int = 0, max_length: int = None) -> bool:
        """Validate string length"""
        if not isinstance(value, str):
            return True  # Let other validators handle type validation
        
        if len(value) < min_length:
            self.add_error(field_name, f"{field_name} must be at least {min_length} characters long")
            return False
        
        if max_length and len(value) > max_length:
            self.add_error(field_name, f"{field_name} must be no more than {max_length} characters long")
            return False
        
        return True
    
    def validate_pattern(self, value: str, field_name: str, pattern: str, description: str = None) -> bool:
        """Validate string against regex pattern"""
        if not isinstance(value, str):
            return True
        
        if not re.match(pattern, value):
            desc = description or f"pattern {pattern}"
            self.add_error(field_name, f"{field_name} does not match required format: {desc}")
            return False
        
        return True
    
    def validate_enum(self, value: str, field_name: str, allowed_values: List[str]) -> bool:
        """Validate string is one of allowed values"""
        if not isinstance(value, str):
            return True
        
        if value not in allowed_values:
            allowed_str = ", ".join(allowed_values)
            self.add_error(field_name, f"{field_name} must be one of: {allowed_str}")
            return False
        
        return True


class NetworkValidator(BaseValidator):
    """Validator for network-related fields"""
    
    def validate_ip_address(self, value: str, field_name: str, allow_private: bool = True) -> bool:
        """Validate IP address format"""
        if not isinstance(value, str):
            return True
        
        try:
            ip = ipaddress.ip_address(value)
            
            if not allow_private and ip.is_private:
                self.add_error(field_name, f"{field_name} cannot be a private IP address")
                return False
            
            return True
            
        except ValueError:
            self.add_error(field_name, f"{field_name} is not a valid IP address")
            return False
    
    def validate_ip_network(self, value: str, field_name: str) -> bool:
        """Validate IP network format (CIDR)"""
        if not isinstance(value, str):
            return True
        
        try:
            ipaddress.ip_network(value, strict=False)
            return True
        except ValueError:
            self.add_error(field_name, f"{field_name} is not a valid IP network (CIDR)")
            return False
    
    def validate_mac_address(self, value: str, field_name: str) -> bool:
        """Validate MAC address format"""
        if not isinstance(value, str):
            return True
        
        # Common MAC address patterns
        patterns = [
            r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$',  # XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
            r'^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$',    # XXXX.XXXX.XXXX
        ]
        
        for pattern in patterns:
            if re.match(pattern, value):
                return True
        
        self.add_error(field_name, f"{field_name} is not a valid MAC address")
        return False
    
    def validate_vlan_id(self, value: int, field_name: str) -> bool:
        """Validate VLAN ID (1-4094)"""
        if not isinstance(value, int):
            return True
        
        if value < 1 or value > 4094:
            self.add_error(field_name, f"{field_name} must be between 1 and 4094")
            return False
        
        return True
    
    def validate_port_number(self, value: int, field_name: str) -> bool:
        """Validate port number (1-65535)"""
        if not isinstance(value, int):
            return True
        
        if value < 1 or value > 65535:
            self.add_error(field_name, f"{field_name} must be between 1 and 65535")
            return False
        
        return True


class DeviceValidator(BaseValidator):
    """Validator for device-related fields"""
    
    def validate_device_name(self, value: str, field_name: str) -> bool:
        """Validate device name format"""
        if not isinstance(value, str):
            return True
        
        # Device names should be alphanumeric with hyphens and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            self.add_error(field_name, f"{field_name} can only contain letters, numbers, hyphens, and underscores")
            return False
        
        # Check length
        if len(value) < 1 or len(value) > 63:
            self.add_error(field_name, f"{field_name} must be between 1 and 63 characters")
            return False
        
        return True
    
    def validate_interface_name(self, value: str, field_name: str) -> bool:
        """Validate interface name format"""
        if not isinstance(value, str):
            return True
        
        # Common interface patterns (ge, xe, et, etc.)
        patterns = [
            r'^[a-zA-Z]+[0-9]+(-[0-9]+)?(/[0-9]+)?(/[0-9]+)?$',  # ge100-0/0/1
            r'^[a-zA-Z]+[0-9]+$',                                  # ge100
        ]
        
        for pattern in patterns:
            if re.match(pattern, value):
                return True
        
        self.add_error(field_name, f"{field_name} is not a valid interface name")
        return False
    
    def validate_device_type(self, value: str, field_name: str) -> bool:
        """Validate device type"""
        if not isinstance(value, str):
            return True
        
        allowed_types = ['leaf', 'spine', 'superspine', 'access', 'core', 'edge']
        if value.lower() not in allowed_types:
            allowed_str = ", ".join(allowed_types)
            self.add_error(field_name, f"{field_name} must be one of: {allowed_str}")
            return False
        
        return True


class ConfigurationValidator(BaseValidator):
    """Validator for configuration-related fields"""
    
    def validate_service_name(self, value: str, field_name: str) -> bool:
        """Validate service name format"""
        if not isinstance(value, str):
            return True
        
        # Service names should follow pattern: g_username_vlan
        if not re.match(r'^g_[a-zA-Z0-9_]+_v[0-9]+$', value):
            self.add_error(field_name, f"{field_name} must follow pattern: g_username_vlan (e.g., g_visaev_v253)")
            return False
        
        return True
    
    def validate_json_schema(self, value: Dict[str, Any], field_name: str, schema: Dict[str, Any]) -> bool:
        """Validate JSON against schema (basic implementation)"""
        if not isinstance(value, dict):
            self.add_error(field_name, f"{field_name} must be a dictionary")
            return False
        
        # Basic schema validation - can be extended with jsonschema library
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in value:
                self.add_error(field_name, f"Required field '{field}' missing in {field_name}")
        
        return len(self.errors) == 0


class CompositeValidator(BaseValidator):
    """Composite validator that combines multiple validators"""
    
    def __init__(self):
        super().__init__()
        self.validators = []
    
    def add_validator(self, validator: BaseValidator) -> None:
        """Add a validator to the composite"""
        self.validators.append(validator)
    
    def validate(self, data: Dict[str, Any], rules: List[ValidationRule]) -> ValidationResult:
        """Validate data against rules using all validators"""
        for rule in rules:
            value = data.get(rule.field_name)
            
            # Check if required field is present
            if rule.required and not self._validate_required(value, rule):
                continue
            
            # Skip validation for None values if not required
            if value is None and not rule.required:
                continue
            
            # Apply validation based on rule type
            self._apply_validation_rule(value, rule)
        
        # Collect errors from all validators
        for validator in self.validators:
            self.errors.extend(validator.errors)
            for field, errors in validator.field_errors.items():
                if field not in self.field_errors:
                    self.field_errors[field] = []
                self.field_errors[field].extend(errors)
            self.warnings.extend(validator.warnings)
        
        return self.get_result()
    
    def _validate_required(self, value: Any, rule: ValidationRule) -> bool:
        """Validate required field"""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            self.add_error(rule.field_name, rule.error_message)
            return False
        return True
    
    def _apply_validation_rule(self, value: Any, rule: ValidationRule) -> None:
        """Apply a specific validation rule"""
        # This would be implemented based on the rule type
        # For now, we'll use a simple approach
        pass


# Convenience functions for common validations
def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """Validate that required fields are present"""
    errors = []
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and data[field].strip() == ""):
            errors.append(f"{field} is required")
    
    return len(errors) == 0, errors


def validate_device_configuration(config: Dict[str, Any]) -> ValidationResult:
    """Validate device configuration"""
    validator = CompositeValidator()
    validator.add_validator(DeviceValidator())
    validator.add_validator(NetworkValidator())
    
    rules = [
        ValidationRule("hostname", "required", True, "Hostname is required"),
        ValidationRule("ip_address", "ip_address", True, "Valid IP address is required"),
        ValidationRule("device_type", "enum", ["leaf", "spine", "superspine"], "Valid device type is required"),
    ]
    
    return validator.validate(config, rules)


def validate_bridge_domain_config(config: Dict[str, Any]) -> ValidationResult:
    """Validate bridge domain configuration"""
    validator = CompositeValidator()
    validator.add_validator(ConfigurationValidator())
    validator.add_validator(DeviceValidator())
    validator.add_validator(NetworkValidator())
    
    rules = [
        ValidationRule("service_name", "service_name", True, "Valid service name is required"),
        ValidationRule("vlan_id", "vlan_id", True, "Valid VLAN ID is required"),
        ValidationRule("source_device", "device_name", True, "Valid source device name is required"),
        ValidationRule("destination_device", "device_name", True, "Valid destination device name is required"),
    ]
    
    return validator.validate(config, rules)
