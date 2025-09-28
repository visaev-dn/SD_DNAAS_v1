#!/usr/bin/env python3
"""
BD Editor CLI Template Validator

Validates generated CLI commands for syntax correctness and safety
before deployment to network devices.
"""

import re
import logging
from typing import Dict, List
from .data_models import ValidationResult

logger = logging.getLogger(__name__)


class CLITemplateValidator:
    """Validate generated CLI commands before deployment"""
    
    def __init__(self):
        self.device_command_patterns = self._load_device_patterns()
        self.dangerous_commands = self._load_dangerous_commands()
        
    def validate_generated_commands(self, device_name: str, commands: List[str]) -> ValidationResult:
        """Validate CLI commands for specific device type"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            # Detect device type
            device_type = self._detect_device_type(device_name)
            patterns = self.device_command_patterns.get(device_type, {})
            
            for command in commands:
                # Validate command syntax
                syntax_validation = self._validate_command_syntax(command, patterns)
                validation.merge(syntax_validation)
                
                # Check for dangerous commands
                danger_validation = self._check_dangerous_commands(command)
                validation.merge(danger_validation)
                
                # Validate VLAN ranges
                vlan_validation = self._validate_vlan_ranges(command)
                validation.merge(vlan_validation)
                
                # Validate interface names
                interface_validation = self._validate_interface_names(command)
                validation.merge(interface_validation)
            
        except Exception as e:
            logger.error(f"Error validating commands for {device_name}: {e}")
            validation.add_error(f"Command validation error: {e}")
        
        return validation
    
    def dry_run_commands(self, device_name: str, commands: List[str]) -> ValidationResult:
        """Perform dry-run validation of commands (syntax only)"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            # This is a placeholder for actual dry-run validation
            # In a full implementation, this would:
            # 1. Connect to device
            # 2. Run commands in configuration mode without commit
            # 3. Check for syntax errors
            # 4. Validate configuration consistency
            
            # For now, perform static validation
            static_validation = self.validate_generated_commands(device_name, commands)
            validation.merge(static_validation)
            
            # Add dry-run specific checks
            for command in commands:
                if self._is_configuration_command(command):
                    validation.add_warning(f"Configuration command requires commit: {command}")
            
        except Exception as e:
            logger.error(f"Error in dry-run validation: {e}")
            validation.add_error(f"Dry-run validation failed: {e}")
        
        return validation
    
    def _load_device_patterns(self) -> Dict:
        """Load command patterns for different device types"""
        return {
            "DRIVENETS": {
                "interface_pattern": r"^interfaces\s+[\w\-\.\/]+(\.\d+)?$",
                "vlan_id_pattern": r"^interfaces\s+[\w\-\.\/]+(\.\d+)?\s+vlan-id\s+\d+$",
                "manipulation_pattern": r"^interfaces\s+[\w\-\.\/]+(\.\d+)?\s+vlan-manipulation.*$",
                "l2_service_pattern": r"^interfaces\s+[\w\-\.\/]+(\.\d+)?\s+l2-service\s+enable$",
                "no_interface_pattern": r"^no\s+interfaces\s+[\w\-\.\/]+(\.\d+)?$"
            },
            "CISCO": {
                "interface_pattern": r"^interface\s+[\w\-\.\/]+(\.\d+)?$",
                "vlan_pattern": r"^encapsulation\s+dot1q\s+\d+$",
                "no_interface_pattern": r"^no\s+interface\s+[\w\-\.\/]+(\.\d+)?$"
            },
            "JUNIPER": {
                "interface_pattern": r"^set\s+interfaces\s+[\w\-\.\/]+(\.\d+)?.*$",
                "vlan_pattern": r"^set\s+interfaces\s+[\w\-\.\/]+(\.\d+)?\s+vlan-id\s+\d+$"
            }
        }
    
    def _load_dangerous_commands(self) -> List[str]:
        """Load patterns for potentially dangerous commands"""
        return [
            r".*shutdown.*",           # Interface shutdown commands
            r".*no\s+ip\s+address.*", # IP address removal
            r".*clear.*",              # Clear commands
            r".*reload.*",             # Device reload
            r".*reboot.*",             # Device reboot
            r".*delete.*",             # Delete commands
            r".*erase.*"               # Erase commands
        ]
    
    def _detect_device_type(self, device_name: str) -> str:
        """Detect device type from device name"""
        
        device_name_lower = device_name.lower()
        
        if 'dnaas' in device_name_lower:
            return "DRIVENETS"
        elif 'cisco' in device_name_lower or 'csr' in device_name_lower:
            return "CISCO"
        elif 'juniper' in device_name_lower or 'mx' in device_name_lower:
            return "JUNIPER"
        else:
            # Default to DRIVENETS for DNAAS environment
            return "DRIVENETS"
    
    def _validate_command_syntax(self, command: str, patterns: Dict) -> ValidationResult:
        """Validate command syntax against device patterns"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            command_lower = command.lower().strip()
            
            # Check if command matches any known pattern
            pattern_matched = False
            
            for pattern_name, pattern in patterns.items():
                if re.match(pattern, command):
                    pattern_matched = True
                    logger.debug(f"Command matched pattern {pattern_name}: {command}")
                    break
            
            if not pattern_matched and patterns:
                validation.add_warning(f"Command doesn't match known patterns: {command}")
            
        except Exception as e:
            validation.add_error(f"Syntax validation error: {e}")
        
        return validation
    
    def _check_dangerous_commands(self, command: str) -> ValidationResult:
        """Check for potentially dangerous commands"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            command_lower = command.lower()
            
            for dangerous_pattern in self.dangerous_commands:
                if re.search(dangerous_pattern, command_lower):
                    validation.add_warning(f"Potentially dangerous command: {command}")
                    break
        
        except Exception as e:
            validation.add_error(f"Danger check error: {e}")
        
        return validation
    
    def _validate_vlan_ranges(self, command: str) -> ValidationResult:
        """Validate VLAN IDs are in valid range"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            # Extract VLAN IDs from command
            vlan_matches = re.findall(r'vlan-id\s+(\d+)', command)
            vlan_matches.extend(re.findall(r'outer-tag\s+(\d+)', command))
            vlan_matches.extend(re.findall(r'inner-tag\s+(\d+)', command))
            vlan_matches.extend(re.findall(r'\.(\d+)', command))  # Subinterface VLANs
            
            for vlan_str in vlan_matches:
                try:
                    vlan_id = int(vlan_str)
                    if not (1 <= vlan_id <= 4094):
                        validation.add_error(f"Invalid VLAN ID: {vlan_id} (must be 1-4094)")
                except ValueError:
                    validation.add_error(f"Invalid VLAN ID format: {vlan_str}")
        
        except Exception as e:
            validation.add_error(f"VLAN validation error: {e}")
        
        return validation
    
    def _validate_interface_names(self, command: str) -> ValidationResult:
        """Validate interface names in commands"""
        
        validation = ValidationResult(is_valid=True)
        
        try:
            # Extract interface names from commands
            interface_matches = re.findall(r'interfaces\s+([\w\-\.\/]+)', command)
            
            for interface_name in interface_matches:
                # Check for valid interface name format
                if not self._is_valid_interface_name(interface_name):
                    validation.add_warning(f"Unusual interface name format: {interface_name}")
                
                # Check if it's an infrastructure interface (shouldn't be in customer commands)
                from .interface_analyzer import BDInterfaceAnalyzer
                analyzer = BDInterfaceAnalyzer()
                
                if analyzer.is_infrastructure_interface(interface_name, ''):
                    validation.add_error(f"Command affects infrastructure interface: {interface_name}")
        
        except Exception as e:
            validation.add_error(f"Interface name validation error: {e}")
        
        return validation
    
    def _is_valid_interface_name(self, interface_name: str) -> bool:
        """Check if interface name has valid format"""
        
        valid_patterns = [
            r"^ge\d+-\d+/\d+/\d+(\.\d+)?$",      # GigabitEthernet format
            r"^bundle-\d+(\.\d+)?$",              # Bundle interface format
            r"^ethernet\d+/\d+(\.\d+)?$",         # Ethernet format
            r"^eth\d+/\d+(\.\d+)?$"               # Short ethernet format
        ]
        
        return any(re.match(pattern, interface_name) for pattern in valid_patterns)
    
    def _is_configuration_command(self, command: str) -> bool:
        """Check if command is a configuration command"""
        
        config_patterns = [
            r"^interfaces\s+",
            r"^vlan\s+",
            r"^bridge-domain\s+"
        ]
        
        return any(re.match(pattern, command) for pattern in config_patterns)


# Convenience functions
def validate_cli_commands(device_name: str, commands: List[str]) -> ValidationResult:
    """Convenience function to validate CLI commands"""
    validator = CLITemplateValidator()
    return validator.validate_generated_commands(device_name, commands)


def dry_run_cli_commands(device_name: str, commands: List[str]) -> ValidationResult:
    """Convenience function to perform dry-run validation"""
    validator = CLITemplateValidator()
    return validator.dry_run_commands(device_name, commands)
