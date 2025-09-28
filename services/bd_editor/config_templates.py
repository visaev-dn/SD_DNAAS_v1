#!/usr/bin/env python3
"""
BD Editor Configuration Templates

Generate CLI commands based on BD type and interface configuration.
Provides type-specific templates for different DNAAS bridge domain types.
"""

import logging
from typing import Dict, List, Optional
from .data_models import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigTemplateEngine:
    """Generate CLI commands based on BD type and interface configuration"""
    
    def __init__(self):
        self.templates = self._load_config_templates()
        
    def _load_config_templates(self) -> Dict:
        """Load CLI command templates for each BD type"""
        return {
            "DNAAS_TYPE_4A_SINGLE_TAGGED": {
                "add_customer_interface": [
                    "interfaces {interface}.{vlan_id} vlan-id {vlan_id}",
                    "interfaces {interface}.{vlan_id} l2-service enabled"
                ],
                "remove_customer_interface": [
                    "no interfaces {interface}.{vlan_id}"
                ],
                "modify_customer_vlan": [
                    "interfaces {interface}.{old_vlan_id} vlan-id {new_vlan_id}"
                ]
            },
            "DNAAS_TYPE_2A_QINQ_SINGLE_BD": {
                "add_customer_interface": [
                    "interfaces {interface}.{outer_vlan} vlan-manipulation ingress-mapping action push outer-tag {outer_vlan} outer-tpid 0x8100",
                    "interfaces {interface}.{outer_vlan} l2-service enabled"
                ],
                "remove_customer_interface": [
                    "no interfaces {interface}.{outer_vlan}"
                ],
                "modify_customer_manipulation": [
                    "interfaces {interface}.{outer_vlan} vlan-manipulation ingress-mapping action push outer-tag {new_outer_vlan} outer-tpid 0x8100"
                ]
            },
            "DNAAS_TYPE_1_DOUBLE_TAGGED": {
                "add_customer_interface": [
                    "interfaces {interface}.{inner_vlan}",
                    "vlan-tags outer-tag {outer_vlan} inner-tag {inner_vlan}",
                    "l2-service enable",
                    "exit"
                ],
                "remove_customer_interface": [
                    "no interfaces {interface}.{inner_vlan}"
                ],
                "modify_customer_tags": [
                    "interfaces {interface}.{inner_vlan} vlan-tags outer-tag {new_outer_vlan} inner-tag {new_inner_vlan}"
                ]
            },
            "GENERIC": {
                "add_interface": [
                    "interfaces {interface}",
                    "interfaces {interface} {manual_config}"
                ],
                "remove_interface": [
                    "no interfaces {interface}"
                ]
            }
        }
    
    def generate_commands(self, bd_type: str, action: str, params: Dict) -> List[str]:
        """Generate CLI commands for specific action"""
        
        try:
            # Get template for BD type and action
            bd_templates = self.templates.get(bd_type, self.templates.get("GENERIC", {}))
            template = bd_templates.get(action, [])
            
            if not template:
                raise ConfigurationError(f"No template found for {bd_type} action {action}")
            
            # Fill template with parameters
            commands = []
            for cmd_template in template:
                try:
                    command = cmd_template.format(**params)
                    commands.append(command)
                except KeyError as e:
                    raise ConfigurationError(f"Missing parameter for template: {e}")
            
            logger.debug(f"Generated {len(commands)} commands for {bd_type} {action}")
            return commands
            
        except Exception as e:
            logger.error(f"Error generating commands for {bd_type} {action}: {e}")
            raise ConfigurationError(f"Failed to generate commands: {e}")
    
    def get_available_actions(self, bd_type: str) -> List[str]:
        """Get available actions for BD type"""
        
        bd_templates = self.templates.get(bd_type, self.templates.get("GENERIC", {}))
        return list(bd_templates.keys())
    
    def validate_template_parameters(self, bd_type: str, action: str, params: Dict) -> List[str]:
        """Validate that all required parameters are provided"""
        
        errors = []
        
        try:
            # Get template
            bd_templates = self.templates.get(bd_type, self.templates.get("GENERIC", {}))
            template = bd_templates.get(action, [])
            
            if not template:
                errors.append(f"No template found for {bd_type} action {action}")
                return errors
            
            # Check each template command for required parameters
            for cmd_template in template:
                # Extract parameter names from template
                import re
                param_names = re.findall(r'\{(\w+)\}', cmd_template)
                
                for param_name in param_names:
                    if param_name not in params:
                        errors.append(f"Missing required parameter: {param_name}")
            
        except Exception as e:
            errors.append(f"Template validation error: {e}")
        
        return errors
    
    def preview_commands(self, bd_type: str, action: str, params: Dict) -> Dict:
        """Preview commands that would be generated"""
        
        try:
            # Validate parameters first
            param_errors = self.validate_template_parameters(bd_type, action, params)
            if param_errors:
                return {
                    'success': False,
                    'errors': param_errors,
                    'commands': []
                }
            
            # Generate commands
            commands = self.generate_commands(bd_type, action, params)
            
            return {
                'success': True,
                'errors': [],
                'commands': commands,
                'action': action,
                'bd_type': bd_type,
                'parameters': params
            }
            
        except Exception as e:
            return {
                'success': False,
                'errors': [str(e)],
                'commands': []
            }


# Convenience functions
def generate_cli_commands(bd_type: str, action: str, params: Dict) -> List[str]:
    """Convenience function to generate CLI commands"""
    engine = ConfigTemplateEngine()
    return engine.generate_commands(bd_type, action, params)


def preview_cli_commands(bd_type: str, action: str, params: Dict) -> Dict:
    """Convenience function to preview CLI commands"""
    engine = ConfigTemplateEngine()
    return engine.preview_commands(bd_type, action, params)
