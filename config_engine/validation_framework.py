#!/usr/bin/env python3
"""
Validation Framework
Provides comprehensive validation for smart deployments, including pre-deployment, during-deployment, and post-deployment checks.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .smart_deployment_types import ValidationStep, ValidationResult, DeploymentResult, DeploymentDiff, RiskLevel

logger = logging.getLogger(__name__)

@dataclass
class ValidationRule:
    """Represents a validation rule"""
    rule_id: str
    name: str
    description: str
    validation_type: str  # 'pre', 'during', 'post'
    severity: str  # 'critical', 'warning', 'info'
    required: bool
    validation_function: str  # Name of the validation method

@dataclass
class ValidationContext:
    """Context for validation operations"""
    deployment_id: str
    deployment_diff: DeploymentDiff
    current_config: Dict
    new_config: Dict
    user_preferences: Dict

class ValidationFramework:
    """
    Framework for comprehensive deployment validation.
    
    Features:
    - Pre-deployment validation
    - During-deployment validation
    - Post-deployment validation
    - Customizable validation rules
    - Risk-based validation
    """
    
    def __init__(self):
        """Initialize validation framework."""
        self.logger = logger
        
        # Define validation rules
        self.validation_rules = self._define_validation_rules()
        
        # Validation history
        self.validation_history: Dict[str, List[Dict]] = {}
    
    def define_validation_steps(self, diff: DeploymentDiff) -> List[ValidationStep]:
        """
        Define validation steps based on deployment diff.
        
        Args:
            diff: DeploymentDiff to analyze for validation requirements
            
        Returns:
            List of ValidationStep objects
        """
        try:
            validation_steps = []
            
            # Pre-deployment validation steps
            pre_steps = self._define_pre_deployment_steps(diff)
            validation_steps.extend(pre_steps)
            
            # During-deployment validation steps
            during_steps = self._define_during_deployment_steps(diff)
            validation_steps.extend(during_steps)
            
            # Post-deployment validation steps
            post_steps = self._define_post_deployment_steps(diff)
            validation_steps.extend(post_steps)
            
            self.logger.info(f"Defined {len(validation_steps)} validation steps")
            return validation_steps
            
        except Exception as e:
            self.logger.error(f"Error defining validation steps: {e}")
            raise
    
    def validate_deployment_result(self, result: DeploymentResult) -> ValidationResult:
        """
        Validate deployment result.
        
        Args:
            result: DeploymentResult to validate
            
        Returns:
            ValidationResult with validation findings
        """
        try:
            self.logger.info("Validating deployment result")
            
            issues = []
            warnings = []
            recommendations = []
            
            # Check for failed devices
            if result.failed_devices:
                issues.append(f"Deployment failed on {len(result.failed_devices)} device(s): {', '.join(result.failed_devices)}")
            
            # Check for errors
            if result.errors:
                issues.extend(result.errors)
            
            # Check deployment duration
            if result.duration > 300:  # 5 minutes
                warnings.append(f"Deployment took {result.duration}s - consider optimizing for faster deployments")
            
            # Check rollback availability
            if not result.rollback_available:
                warnings.append("Rollback configuration not available - recovery may be difficult")
            
            # Generate recommendations
            if result.failed_devices:
                recommendations.append("Review failed device logs and consider manual intervention")
                recommendations.append("Verify network connectivity to failed devices")
            
            if result.duration > 300:
                recommendations.append("Consider using parallel deployment strategy for faster execution")
            
            # Determine overall validity
            valid = len(issues) == 0
            
            validation_result = ValidationResult(
                valid=valid,
                issues=issues,
                warnings=warnings,
                recommendations=recommendations
            )
            
            self.logger.info(f"Deployment validation complete: {len(issues)} issues, {len(warnings)} warnings")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating deployment result: {e}")
            return ValidationResult(
                valid=False,
                issues=[f"Validation error: {str(e)}"],
                warnings=[],
                recommendations=["Check validation logs for details"]
            )
    
    def execute_validation_step(self, step: ValidationStep, context: ValidationContext) -> bool:
        """
        Execute a single validation step.
        
        Args:
            step: ValidationStep to execute
            context: ValidationContext for the validation
            
        Returns:
            True if validation passed, False otherwise
        """
        try:
            self.logger.info(f"Executing validation step: {step.name}")
            
            # Find the validation rule
            rule = self._find_validation_rule(step.step_id)
            if not rule:
                self.logger.warning(f"Validation rule not found for step: {step.step_id}")
                return False
            
            # Execute the validation
            validation_method = getattr(self, rule.validation_function, None)
            if not validation_method:
                self.logger.error(f"Validation method not found: {rule.validation_function}")
                return False
            
            # Execute validation with context
            validation_result = validation_method(context)
            
            # Log validation result
            self._log_validation_result(step.step_id, validation_result, context.deployment_id)
            
            # Update validation history
            self._update_validation_history(context.deployment_id, step, validation_result)
            
            self.logger.info(f"Validation step {step.name} completed: {'PASS' if validation_result else 'FAIL'}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error executing validation step {step.step_id}: {e}")
            self._log_validation_result(step.step_id, False, context.deployment_id, error=str(e))
            return False
    
    def _define_validation_rules(self) -> List[ValidationRule]:
        """Define available validation rules."""
        rules = [
            # Pre-deployment validation rules
            ValidationRule(
                rule_id="config_syntax_check",
                name="Configuration Syntax Check",
                description="Validate configuration syntax for all devices",
                validation_type="pre",
                severity="critical",
                required=True,
                validation_function="_validate_config_syntax"
            ),
            ValidationRule(
                rule_id="device_connectivity",
                name="Device Connectivity Check",
                description="Verify connectivity to all target devices",
                validation_type="pre",
                severity="critical",
                required=True,
                validation_function="_validate_device_connectivity"
            ),
            ValidationRule(
                rule_id="vlan_conflicts",
                name="VLAN Conflict Check",
                description="Check for VLAN ID conflicts across devices",
                validation_type="pre",
                severity="warning",
                required=False,
                validation_function="_validate_vlan_conflicts"
            ),
            ValidationRule(
                rule_id="interface_availability",
                name="Interface Availability Check",
                description="Verify required interfaces are available",
                validation_type="pre",
                severity="warning",
                required=False,
                validation_function="_validate_interface_availability"
            ),
            ValidationRule(
                rule_id="resource_availability",
                name="Resource Availability Check",
                description="Check device resource availability",
                validation_type="pre",
                severity="info",
                required=False,
                validation_function="_validate_resource_availability"
            ),
            
            # During-deployment validation rules
            ValidationRule(
                rule_id="deployment_progress",
                name="Deployment Progress Check",
                description="Monitor deployment progress and detect stalls",
                validation_type="during",
                severity="warning",
                required=False,
                validation_function="_validate_deployment_progress"
            ),
            ValidationRule(
                rule_id="device_response",
                name="Device Response Check",
                description="Verify devices are responding during deployment",
                validation_type="during",
                severity="critical",
                required=True,
                validation_function="_validate_device_response"
            ),
            
            # Post-deployment validation rules
            ValidationRule(
                rule_id="config_verification",
                name="Configuration Verification",
                description="Verify new configuration is properly applied",
                validation_type="post",
                severity="critical",
                required=True,
                validation_function="_validate_config_verification"
            ),
            ValidationRule(
                rule_id="connectivity_test",
                name="Connectivity Test",
                description="Test network connectivity after deployment",
                validation_type="post",
                severity="critical",
                required=True,
                validation_function="_validate_connectivity_test"
            ),
            ValidationRule(
                rule_id="performance_check",
                name="Performance Check",
                description="Verify network performance after changes",
                validation_type="post",
                severity="warning",
                required=False,
                validation_function="_validate_performance_check"
            ),
            ValidationRule(
                rule_id="cleanup_verification",
                name="Cleanup Verification",
                description="Verify no obsolete configuration remains",
                validation_type="post",
                severity="warning",
                required=False,
                validation_function="_validate_cleanup_verification"
            )
        ]
        
        return rules
    
    def _define_pre_deployment_steps(self, diff: DeploymentDiff) -> List[ValidationStep]:
        """Define pre-deployment validation steps."""
        steps = []
        
        # Always include critical pre-deployment validations
        critical_rules = [r for r in self.validation_rules if r.validation_type == "pre" and r.required]
        
        for rule in critical_rules:
            step = ValidationStep(
                step_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                validation_type="pre",
                required=rule.required
            )
            steps.append(step)
        
        # Add conditional steps based on deployment diff
        if diff.vlan_changes:
            # Add VLAN-specific validations
            vlan_rules = [r for r in self.validation_rules if r.validation_type == "pre" and "vlan" in r.rule_id.lower()]
            for rule in vlan_rules:
                if rule not in [s.step_id for s in steps]:
                    step = ValidationStep(
                        step_id=rule.rule_id,
                        name=rule.name,
                        description=rule.description,
                        validation_type="pre",
                        required=rule.required
                    )
                    steps.append(step)
        
        if diff.estimated_impact.risk_level == RiskLevel.HIGH:
            # Add additional validations for high-risk deployments
            high_risk_rules = [r for r in self.validation_rules if r.validation_type == "pre" and r.severity == "warning"]
            for rule in high_risk_rules:
                if rule not in [s.step_id for s in steps]:
                    step = ValidationStep(
                        step_id=rule.rule_id,
                        name=rule.name,
                        description=rule.description,
                        validation_type="pre",
                        required=rule.required
                    )
                    steps.append(step)
        
        return steps
    
    def _define_during_deployment_steps(self, diff: DeploymentDiff) -> List[ValidationStep]:
        """Define during-deployment validation steps."""
        steps = []
        
        # Always include critical during-deployment validations
        during_rules = [r for r in self.validation_rules if r.validation_type == "during"]
        
        for rule in during_rules:
            step = ValidationStep(
                step_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                validation_type="during",
                required=rule.required
            )
            steps.append(step)
        
        return steps
    
    def _define_post_deployment_steps(self, diff: DeploymentDiff) -> List[ValidationStep]:
        """Define post-deployment validation steps."""
        steps = []
        
        # Always include critical post-deployment validations
        critical_rules = [r for r in self.validation_rules if r.validation_type == "post" and r.required]
        
        for rule in critical_rules:
            step = ValidationStep(
                step_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                validation_type="post",
                required=rule.required
            )
            steps.append(step)
        
        # Add conditional post-deployment validations
        if diff.devices_to_remove:
            # Add cleanup verification for removed devices
            cleanup_rules = [r for r in self.validation_rules if r.validation_type == "post" and "cleanup" in r.rule_id.lower()]
            for rule in cleanup_rules:
                step = ValidationStep(
                    step_id=rule.rule_id,
                    name=rule.name,
                    description=rule.description,
                    validation_type="post",
                    required=rule.required
                )
                steps.append(step)
        
        return steps
    
    def _find_validation_rule(self, step_id: str) -> Optional[ValidationRule]:
        """Find validation rule by step ID."""
        for rule in self.validation_rules:
            if rule.rule_id == step_id:
                return rule
        return None
    
    # Pre-deployment validation methods
    
    def _validate_config_syntax(self, context: ValidationContext) -> bool:
        """Validate configuration syntax for all devices."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Parse configuration commands
            # 2. Validate syntax against device-specific parsers
            # 3. Check for common syntax errors
            
            # Simulate validation
            time.sleep(0.1)
            
            # For now, assume syntax is valid
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating config syntax: {e}")
            return False
    
    def _validate_device_connectivity(self, context: ValidationContext) -> bool:
        """Verify connectivity to all target devices."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Test SSH connectivity to each device
            # 2. Verify authentication credentials
            # 3. Check device responsiveness
            
            # Simulate connectivity check
            time.sleep(0.2)
            
            # For now, assume connectivity is good
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating device connectivity: {e}")
            return False
    
    def _validate_vlan_conflicts(self, context: ValidationContext) -> bool:
        """Check for VLAN ID conflicts across devices."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Extract VLAN IDs from new configuration
            # 2. Check for conflicts with existing VLANs
            # 3. Validate VLAN ID ranges
            
            # Simulate VLAN conflict check
            time.sleep(0.1)
            
            # For now, assume no conflicts
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating VLAN conflicts: {e}")
            return False
    
    def _validate_interface_availability(self, context: ValidationContext) -> bool:
        """Verify required interfaces are available."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Check if required interfaces exist on devices
            # 2. Verify interface status
            # 3. Check for interface conflicts
            
            # Simulate interface availability check
            time.sleep(0.1)
            
            # For now, assume interfaces are available
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating interface availability: {e}")
            return False
    
    def _validate_resource_availability(self, context: ValidationContext) -> bool:
        """Check device resource availability."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Check device memory usage
            # 2. Verify flash storage availability
            # 3. Check CPU utilization
            
            # Simulate resource check
            time.sleep(0.1)
            
            # For now, assume resources are available
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating resource availability: {e}")
            return False
    
    # During-deployment validation methods
    
    def _validate_deployment_progress(self, context: ValidationContext) -> bool:
        """Monitor deployment progress and detect stalls."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Monitor deployment timestamps
            # 2. Detect stalled operations
            # 3. Check for timeout conditions
            
            # Simulate progress check
            time.sleep(0.1)
            
            # For now, assume progress is good
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating deployment progress: {e}")
            return False
    
    def _validate_device_response(self, context: ValidationContext) -> bool:
        """Verify devices are responding during deployment."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Send test commands to devices
            # 2. Verify command execution
            # 3. Check for device responsiveness
            
            # Simulate device response check
            time.sleep(0.1)
            
            # For now, assume devices are responding
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating device response: {e}")
            return False
    
    # Post-deployment validation methods
    
    def _validate_config_verification(self, context: ValidationContext) -> bool:
        """Verify new configuration is properly applied."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Retrieve current device configuration
            # 2. Compare with expected configuration
            # 3. Verify all changes are applied
            
            # Simulate config verification
            time.sleep(0.2)
            
            # For now, assume configuration is correct
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating config verification: {e}")
            return False
    
    def _validate_connectivity_test(self, context: ValidationContext) -> bool:
        """Test network connectivity after deployment."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Test connectivity between devices
            # 2. Verify VLAN connectivity
            # 3. Check routing tables
            
            # Simulate connectivity test
            time.sleep(0.3)
            
            # For now, assume connectivity is good
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating connectivity test: {e}")
            return False
    
    def _validate_performance_check(self, context: ValidationContext) -> bool:
        """Verify network performance after changes."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Measure latency between devices
            # 2. Check bandwidth utilization
            # 3. Verify QoS settings
            
            # Simulate performance check
            time.sleep(0.2)
            
            # For now, assume performance is acceptable
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating performance check: {e}")
            return False
    
    def _validate_cleanup_verification(self, context: ValidationContext) -> bool:
        """Verify no obsolete configuration remains."""
        try:
            # This is a placeholder - in practice, you would:
            # 1. Check for orphaned VLANs
            # 2. Verify unused interfaces are cleaned up
            # 3. Check for obsolete routing entries
            
            # Simulate cleanup verification
            time.sleep(0.1)
            
            # For now, assume cleanup is complete
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating cleanup verification: {e}")
            return False
    
    def _log_validation_result(self, step_id: str, result: bool, deployment_id: str, error: Optional[str] = None):
        """Log validation result."""
        status = "PASS" if result else "FAIL"
        log_message = f"Validation step {step_id}: {status}"
        
        if error:
            log_message += f" - Error: {error}"
        
        if result:
            self.logger.info(log_message)
        else:
            self.logger.warning(log_message)
    
    def _update_validation_history(self, deployment_id: str, step: ValidationStep, result: bool):
        """Update validation history."""
        if deployment_id not in self.validation_history:
            self.validation_history[deployment_id] = []
        
        history_entry = {
            'timestamp': time.time(),
            'step_id': step.step_id,
            'step_name': step.name,
            'result': result,
            'validation_type': step.validation_type
        }
        
        self.validation_history[deployment_id].append(history_entry)
    
    def get_validation_history(self, deployment_id: str) -> List[Dict]:
        """Get validation history for a deployment."""
        return self.validation_history.get(deployment_id, [])
    
    def get_validation_summary(self, deployment_id: str) -> Dict[str, Any]:
        """Get validation summary for a deployment."""
        history = self.get_validation_history(deployment_id)
        
        if not history:
            return {
                'total_steps': 0,
                'passed_steps': 0,
                'failed_steps': 0,
                'success_rate': 0.0
            }
        
        total_steps = len(history)
        passed_steps = len([h for h in history if h['result']])
        failed_steps = total_steps - passed_steps
        success_rate = (passed_steps / total_steps) * 100 if total_steps > 0 else 0.0
        
        return {
            'total_steps': total_steps,
            'passed_steps': passed_steps,
            'failed_steps': failed_steps,
            'success_rate': success_rate,
            'history': history
        } 