#!/usr/bin/env python3
"""
BD Editor Configuration Preview System

Generate comprehensive previews of BD configuration changes including
CLI commands, impact analysis, and validation results.
"""

import logging
import time
from typing import Dict, List, Optional
from .data_models import PreviewReport, ValidationResult, ImpactAnalysis
from .config_templates import ConfigTemplateEngine
from .validation_system import TypeAwareValidator

logger = logging.getLogger(__name__)


class ConfigurationPreviewSystem:
    """Complete configuration preview and validation system"""
    
    def __init__(self):
        self.template_engine = ConfigTemplateEngine()
        self.validator = TypeAwareValidator()
        
        # Import impact analyzer when available
        try:
            from .impact_analyzer import ChangeImpactAnalyzer
            self.impact_analyzer = ChangeImpactAnalyzer()
            self.impact_analysis_available = True
        except ImportError:
            self.impact_analyzer = None
            self.impact_analysis_available = False
    
    def generate_full_preview(self, bridge_domain: Dict, session: Dict) -> PreviewReport:
        """Generate comprehensive preview of all changes"""
        
        changes = session.get('changes_made', [])
        preview_report = PreviewReport()
        preview_report.changes = changes
        
        try:
            # Generate CLI commands for each change
            for change in changes:
                try:
                    commands = self._generate_change_commands(bridge_domain, change)
                    preview_report.add_change_commands(change, commands)
                except Exception as e:
                    preview_report.add_error(change, str(e))
            
            # Analyze impact if available
            if self.impact_analysis_available and self.impact_analyzer:
                impact_analysis = self.impact_analyzer.analyze_changes(bridge_domain, changes)
                preview_report.impact_analysis = impact_analysis
            
            # Validate entire changeset
            validation = self.validator.validate_changeset(bridge_domain, changes)
            preview_report.validation_result = validation
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            preview_report.add_error({}, f"Preview generation error: {e}")
        
        return preview_report
    
    def display_preview_to_user(self, preview_report: PreviewReport):
        """Display human-readable preview to user"""
        
        print(f"\n🔍 CONFIGURATION PREVIEW")
        print("="*60)
        
        # Show summary
        print(f"📊 Summary:")
        print(f"   • Changes: {len(preview_report.changes)}")
        print(f"   • Affected devices: {len(preview_report.affected_devices)}")
        print(f"   • Commands to execute: {len(preview_report.all_commands)}")
        
        # Show commands by device
        if preview_report.commands_by_device:
            print(f"\n📋 CLI COMMANDS BY DEVICE:")
            for device, commands in preview_report.commands_by_device.items():
                print(f"\n📡 {device}:")
                for i, cmd in enumerate(commands, 1):
                    print(f"   {i}. {cmd}")
        
        # Show impact analysis if available
        if preview_report.impact_analysis:
            print(f"\n🎯 IMPACT ANALYSIS:")
            impact = preview_report.impact_analysis
            print(f"   • Customer interfaces affected: {impact.customer_interfaces_affected}")
            
            if impact.services_impacted:
                print(f"   • Services impacted:")
                for service in impact.services_impacted:
                    print(f"     - {service}")
            
            print(f"   • Estimated downtime: {impact.estimated_downtime}")
            
            if impact.warnings:
                print(f"   • Impact warnings:")
                for warning in impact.warnings:
                    print(f"     - {warning}")
        
        # Show validation results
        if preview_report.validation_result:
            validation = preview_report.validation_result
            
            if validation.errors:
                print(f"\n❌ VALIDATION ERRORS:")
                for error in validation.errors:
                    print(f"   • {error}")
            
            if validation.warnings:
                print(f"\n⚠️  VALIDATION WARNINGS:")
                for warning in validation.warnings:
                    print(f"   • {warning}")
            
            if validation.is_valid:
                print(f"\n✅ VALIDATION: All changes are valid")
            else:
                print(f"\n❌ VALIDATION: Changes have errors - deployment not recommended")
        
        # Show errors if any
        if preview_report.errors:
            print(f"\n❌ PREVIEW ERRORS:")
            for error in preview_report.errors:
                print(f"   • {error}")
    
    def _generate_change_commands(self, bridge_domain: Dict, change: Dict) -> List[str]:
        """Generate CLI commands for a specific change"""
        
        bd_type = bridge_domain.get('dnaas_type', 'unknown')
        action = change.get('action', '')
        interface_info = change.get('interface', {})
        
        # Map change action to template action
        template_action = self._map_change_to_template_action(action)
        
        if not template_action:
            raise ConfigurationError(f"Unknown change action: {action}")
        
        # Prepare parameters for template
        params = self._prepare_template_parameters(bridge_domain, interface_info, action)
        
        # Generate commands using template engine
        commands = self.template_engine.generate_commands(bd_type, template_action, params)
        
        return commands
    
    def _map_change_to_template_action(self, change_action: str) -> Optional[str]:
        """Map change action to template action"""
        
        mapping = {
            'add_customer_interface': 'add_customer_interface',
            'add_qinq_customer_interface': 'add_customer_interface',
            'add_double_tagged_customer_interface': 'add_customer_interface',
            'remove_customer_interface': 'remove_customer_interface',
            'modify_customer_interface': 'modify_customer_interface',
            'modify_customer_manipulation': 'modify_customer_manipulation',
            'modify_customer_tags': 'modify_customer_tags'
        }
        
        return mapping.get(change_action)
    
    def _prepare_template_parameters(self, bridge_domain: Dict, interface_info: Dict, action: str) -> Dict:
        """Prepare parameters for template engine"""
        
        bd_type = bridge_domain.get('dnaas_type', 'unknown')
        
        # Get base interface name (remove VLAN ID if already present)
        interface_name = interface_info.get('interface', '')
        vlan_id = bridge_domain.get('vlan_id')
        
        # DEBUG: Print what we're receiving
        print(f"🔍 DEBUG - Template params preparation:")
        print(f"   interface_info: {interface_info}")
        print(f"   interface_name: {interface_name}")
        print(f"   vlan_id: {vlan_id}")
        
        # Remove VLAN ID from interface name if already present
        if f".{vlan_id}" in interface_name:
            base_interface = interface_name.replace(f".{vlan_id}", "")
            print(f"   VLAN removed: {interface_name} → {base_interface}")
        else:
            base_interface = interface_name
            print(f"   No VLAN to remove: {interface_name}")
        
        # Base parameters
        params = {
            'device': interface_info.get('device', ''),
            'interface': base_interface,  # Use base interface name
            'vlan_id': vlan_id,
            'bd_name': bridge_domain.get('name', 'unknown_bd')
        }
        
        print(f"   Final params: {params}")
        
        return params
        
        # Type-specific parameters
        if bd_type == "DNAAS_TYPE_2A_QINQ_SINGLE_BD":
            params['outer_vlan'] = bridge_domain.get('vlan_id')  # In QinQ, vlan_id is outer VLAN
        elif bd_type == "DNAAS_TYPE_1_DOUBLE_TAGGED":
            params['outer_vlan'] = bridge_domain.get('outer_vlan', 100)  # Default or extracted
            params['inner_vlan'] = bridge_domain.get('vlan_id')
        
        # Add interface-specific parameters
        params.update(interface_info)
        
        return params


# Convenience functions
def generate_configuration_preview(bridge_domain: Dict, session: Dict) -> PreviewReport:
    """Convenience function to generate configuration preview"""
    preview_system = ConfigurationPreviewSystem()
    return preview_system.generate_full_preview(bridge_domain, session)


def display_configuration_preview(bridge_domain: Dict, session: Dict):
    """Convenience function to display configuration preview"""
    preview_system = ConfigurationPreviewSystem()
    preview_report = preview_system.generate_full_preview(bridge_domain, session)
    preview_system.display_preview_to_user(preview_report)
