#!/usr/bin/env python3
"""
BD Editor Universal SSH Deployment Adapter

Adapter that connects BD Editor to the Universal SSH Deployment Framework,
providing reliable deployment using proven SSH patterns.
"""

import time
import logging
from typing import Dict, List
from services.universal_ssh import (
    UniversalDeploymentOrchestrator,
    DeploymentPlan,
    DeploymentResult,
    ExecutionMode,
    deploy_with_universal_framework
)
from .data_models import DeploymentError

logger = logging.getLogger(__name__)


class BDEditorUniversalAdapter:
    """BD Editor adapter for universal SSH framework"""
    
    def __init__(self):
        self.orchestrator = UniversalDeploymentOrchestrator()
        
        # Import existing BD Editor components
        try:
            from .config_templates import ConfigTemplateEngine
            from .config_preview import ConfigurationPreviewSystem
            self.template_engine = ConfigTemplateEngine()
            self.preview_system = ConfigurationPreviewSystem()
            self.components_available = True
        except ImportError:
            self.components_available = False
            logger.warning("BD Editor components not fully available")
    
    def deploy_bd_changes(self, bridge_domain: Dict, session: Dict) -> DeploymentResult:
        """Deploy BD changes using universal SSH framework"""
        
        try:
            if not self.components_available:
                raise DeploymentError("BD Editor components not available")
            
            print(f"\\n🔄 PREPARING DEPLOYMENT WITH UNIVERSAL SSH FRAMEWORK")
            print("="*70)
            
            # Generate deployment plan using existing BD Editor logic
            deployment_plan = self._create_deployment_plan(bridge_domain, session)
            
            if not deployment_plan.device_commands:
                return DeploymentResult(
                    deployment_id=deployment_plan.deployment_id,
                    success=True,
                    errors=["No changes to deploy"]
                )
            
            print(f"📋 Deployment plan created:")
            print(f"   • Commands: {sum(len(cmds) for cmds in deployment_plan.device_commands.values())}")
            print(f"   • Devices: {len(deployment_plan.device_commands)}")
            
            # Use universal framework for deployment
            result = self.orchestrator.deploy_with_bd_builder_pattern(deployment_plan)
            
            return result
            
        except Exception as e:
            logger.error(f"BD Editor universal deployment failed: {e}")
            return DeploymentResult(
                deployment_id=f"bd_editor_{int(time.time())}",
                success=False,
                errors=[str(e)]
            )
    
    def _create_deployment_plan(self, bridge_domain: Dict, session: Dict) -> DeploymentPlan:
        """Create deployment plan using existing BD Editor logic"""
        
        try:
            # Use existing config preview to generate commands
            preview_report = self.preview_system.generate_full_preview(bridge_domain, session)
            
            # Convert to universal framework format
            deployment_plan = DeploymentPlan(
                deployment_id=f"bd_editor_{int(time.time())}",
                device_commands=preview_report.commands_by_device,
                execution_mode=ExecutionMode.COMMIT,
                parallel_execution=True,
                validation_required=True,
                metadata={
                    'bd_name': bridge_domain.get('name'),
                    'bd_type': bridge_domain.get('dnaas_type'),
                    'changes_count': len(session.get('changes_made', []))
                }
            )
            
            return deployment_plan
            
        except Exception as e:
            logger.error(f"Error creating deployment plan: {e}")
            raise DeploymentError(f"Failed to create deployment plan: {e}")
    
    def validate_bd_changes(self, bridge_domain: Dict, session: Dict) -> Dict[str, bool]:
        """Validate BD changes using universal framework commit-check"""
        
        try:
            # Create deployment plan
            deployment_plan = self._create_deployment_plan(bridge_domain, session)
            
            # Use universal framework for validation
            validation_results = {}
            
            for device_name, commands in deployment_plan.device_commands.items():
                result = self.orchestrator.command_executor.execute_with_mode(
                    device_name, commands, ExecutionMode.COMMIT_CHECK
                )
                validation_results[device_name] = result.success
            
            return validation_results
            
        except Exception as e:
            logger.error(f"BD Editor validation failed: {e}")
            return {}
    
    def preview_bd_deployment(self, bridge_domain: Dict, session: Dict) -> Dict:
        """Preview BD deployment using existing preview system"""
        
        try:
            if not self.components_available:
                return {'error': 'Preview system not available'}
            
            # Use existing preview system
            preview_report = self.preview_system.generate_full_preview(bridge_domain, session)
            
            return {
                'success': True,
                'commands_by_device': preview_report.commands_by_device,
                'total_commands': len(preview_report.all_commands),
                'affected_devices': list(preview_report.affected_devices),
                'validation_result': preview_report.validation_result,
                'impact_analysis': preview_report.impact_analysis
            }
            
        except Exception as e:
            logger.error(f"BD Editor preview failed: {e}")
            return {'error': str(e)}


# Convenience functions for BD Editor integration
def deploy_bd_changes_with_universal_framework(bridge_domain: Dict, session: Dict) -> DeploymentResult:
    """Deploy BD changes using universal SSH framework"""
    adapter = BDEditorUniversalAdapter()
    return adapter.deploy_bd_changes(bridge_domain, session)


def validate_bd_changes_with_universal_framework(bridge_domain: Dict, session: Dict) -> Dict[str, bool]:
    """Validate BD changes using universal framework"""
    adapter = BDEditorUniversalAdapter()
    return adapter.validate_bd_changes(bridge_domain, session)


def preview_bd_deployment_with_universal_framework(bridge_domain: Dict, session: Dict) -> Dict:
    """Preview BD deployment using universal framework"""
    adapter = BDEditorUniversalAdapter()
    return adapter.preview_bd_deployment(bridge_domain, session)
