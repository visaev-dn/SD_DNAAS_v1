#!/usr/bin/env python3
"""
Universal Deployment Orchestrator

Unified deployment orchestration with all proven safety patterns
extracted from BD-Builder and deployment manager systems.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List
from .data_models import DeploymentPlan, DeploymentResult, ExecutionMode, DeploymentError
from .device_manager import UniversalDeviceManager
from .command_executor import UniversalCommandExecutor

logger = logging.getLogger(__name__)


class UniversalDeploymentOrchestrator:
    """Unified deployment orchestration with all proven safety patterns"""
    
    def __init__(self):
        self.device_manager = UniversalDeviceManager()
        self.command_executor = UniversalCommandExecutor()
    
    def deploy_with_bd_builder_pattern(self, deployment_plan: DeploymentPlan) -> DeploymentResult:
        """Use proven BD-Builder deployment pattern: commit-check → parallel deploy → validate"""
        
        start_time = time.time()
        
        result = DeploymentResult(
            deployment_id=deployment_plan.deployment_id,
            success=False,
            deployment_time=datetime.now()
        )
        
        try:
            print(f"\\n🛡️  EXECUTING SAFE DEPLOYMENT (Universal Framework - BD-Builder Pattern)")
            print("="*70)
            
            # Stage 1: Commit-check validation on all devices (proven BD-Builder pattern)
            print(f"🔍 Stage 1: Commit-check validation on all devices...")
            
            commit_check_results = {}
            commit_check_errors = []
            
            for device_name, commands in deployment_plan.device_commands.items():
                print(f"   🔍 Checking {device_name}...")
                
                check_result = self.command_executor.execute_with_mode(
                    device_name, commands, ExecutionMode.COMMIT_CHECK
                )
                
                commit_check_results[device_name] = check_result.success
                result.commit_check_results[device_name] = check_result.success
                
                if check_result.success:
                    print(f"   ✅ {device_name}: Commit-check passed")
                else:
                    print(f"   ❌ {device_name}: Commit-check failed - {check_result.error_message}")
                    commit_check_errors.append(f"{device_name}: {check_result.error_message}")
            
            # Check if all commit-checks passed (proven BD-Builder safety)
            if commit_check_errors:
                print(f"\\n❌ COMMIT-CHECK FAILURES - Deployment aborted")
                for error in commit_check_errors:
                    print(f"   • {error}")
                
                result.errors = commit_check_errors
                result.total_execution_time = time.time() - start_time
                return result
            
            print(f"\\n✅ All commit-checks passed - proceeding with deployment")
            
            # Stage 2: Parallel deployment (proven BD-Builder pattern)
            print(f"\\n⚡ Stage 2: Parallel deployment to all devices...")
            
            deployment_results = self.command_executor.execute_parallel(
                deployment_plan.device_commands,
                ExecutionMode.COMMIT
            )
            
            # Analyze deployment results
            successful_deployments = []
            failed_deployments = []
            
            for device_name, exec_result in deployment_results.items():
                result.execution_results[device_name] = exec_result
                result.affected_devices.append(device_name)
                
                if exec_result.success:
                    print(f"   ✅ {device_name}: Deployment successful ({exec_result.total_execution_time:.2f}s)")
                    successful_deployments.append(device_name)
                else:
                    print(f"   ❌ {device_name}: Deployment failed - {exec_result.error_message}")
                    failed_deployments.append(device_name)
                    result.errors.append(f"{device_name}: {exec_result.error_message}")
            
            # Stage 3: Post-deployment validation (proven pattern)
            if successful_deployments:
                print(f"\\n🔍 Stage 3: Post-deployment validation...")
                
                for device_name in successful_deployments:
                    validation_success = self._validate_deployment_on_device(
                        device_name, 
                        deployment_plan.device_commands[device_name]
                    )
                    
                    result.validation_results[device_name] = validation_success
                    
                    if validation_success:
                        print(f"   ✅ {device_name}: Configuration validated")
                    else:
                        print(f"   ⚠️  {device_name}: Post-deployment validation failed")
                        result.warnings.append(f"{device_name}: Post-deployment validation failed")
            
            # Determine overall success
            result.success = len(failed_deployments) == 0
            result.total_execution_time = time.time() - start_time
            
            # Show final results
            print(f"\\n📊 DEPLOYMENT RESULTS:")
            print("="*50)
            
            if result.success:
                print("✅ DEPLOYMENT SUCCESSFUL!")
                print(f"📡 Devices updated: {len(successful_deployments)}")
                print(f"⏱️  Total execution time: {result.total_execution_time:.2f}s")
            else:
                print("❌ DEPLOYMENT FAILED!")
                print(f"📡 Successful: {len(successful_deployments)}")
                print(f"❌ Failed: {len(failed_deployments)}")
                for error in result.errors:
                    print(f"   • {error}")
            
            return result
            
        except Exception as e:
            logger.error(f"Deployment orchestration failed: {e}")
            result.error_message = str(e)
            result.errors = [str(e)]
            result.total_execution_time = time.time() - start_time
            return result
    
    def deploy_immediate(self, device_commands: Dict[str, List[str]]) -> DeploymentResult:
        """Immediate deployment without commit-check (for simple operations)"""
        
        deployment_plan = DeploymentPlan(
            deployment_id=f"immediate_{int(time.time())}",
            device_commands=device_commands,
            execution_mode=ExecutionMode.COMMIT,
            parallel_execution=True
        )
        
        # Skip commit-check, go straight to deployment
        print(f"\\n⚡ IMMEDIATE DEPLOYMENT (Universal Framework)")
        print("="*60)
        
        deployment_results = self.command_executor.execute_parallel(
            device_commands,
            ExecutionMode.COMMIT
        )
        
        # Analyze results
        result = DeploymentResult(
            deployment_id=deployment_plan.deployment_id,
            success=all(res.success for res in deployment_results.values()),
            execution_results=deployment_results,
            affected_devices=list(device_commands.keys()),
            deployment_time=datetime.now()
        )
        
        return result
    
    def _validate_deployment_on_device(self, device_name: str, deployed_commands: List[str]) -> bool:
        """Validate deployment on device using proven patterns"""
        
        try:
            # Extract interfaces to validate
            interfaces_to_validate = []
            for command in deployed_commands:
                if command.startswith('interfaces ') and 'vlan-id' in command:
                    parts = command.split()
                    if len(parts) >= 4:
                        interface_name = parts[1]
                        vlan_id = parts[3]
                        interfaces_to_validate.append((interface_name, vlan_id))
            
            if not interfaces_to_validate:
                return True  # No interfaces to validate
            
            # Use optimized validation with filtering (your suggestion)
            validation_commands = []
            for interface, vlan in interfaces_to_validate:
                # Use efficient filtering to avoid parsing through useless information
                validation_commands.append(f"show interfaces | no-more | i {interface}")
            
            validation_result = self.command_executor.execute_with_mode(
                device_name, validation_commands, ExecutionMode.QUERY
            )
            
            if validation_result.success:
                print(f"     🔍 Validating with optimized filtering...")
                
                # Check if interfaces are actually configured with expected VLAN
                validation_output = validation_result.output
                
                for interface, expected_vlan in interfaces_to_validate:
                    print(f"     🔍 Checking {interface} for VLAN {expected_vlan}...")
                    
                    # Look for interface in filtered output
                    if interface not in validation_output:
                        print(f"     ❌ Interface {interface} not found in output")
                        return False
                    
                    # Look for VLAN configuration in the interface line
                    interface_lines = [line for line in validation_output.split('\\n') if interface in line]
                    
                    if not interface_lines:
                        print(f"     ❌ No interface lines found for {interface}")
                        return False
                    
                    # Check for VLAN in interface information
                    vlan_found = False
                    for line in interface_lines:
                        if f"Vlan-Id: {expected_vlan}" in line or f"vlan-id {expected_vlan}" in line or f".{expected_vlan}" in line:
                            print(f"     ✅ {interface} VLAN {expected_vlan} confirmed")
                            vlan_found = True
                            break
                    
                    if not vlan_found:
                        print(f"     ❌ VLAN {expected_vlan} not configured on {interface}")
                        return False
                
                return True
            else:
                print(f"     ❌ Validation query failed: {validation_result.error_message}")
                return False
                
        except Exception as e:
            logger.error(f"Validation failed for {device_name}: {e}")
            return False


# Convenience functions
def deploy_with_universal_framework(device_commands: Dict[str, List[str]], 
                                   use_commit_check: bool = True) -> DeploymentResult:
    """Deploy using universal framework with BD-Builder pattern"""
    
    orchestrator = UniversalDeploymentOrchestrator()
    
    deployment_plan = DeploymentPlan(
        deployment_id=f"universal_{int(time.time())}",
        device_commands=device_commands,
        execution_mode=ExecutionMode.COMMIT
    )
    
    if use_commit_check:
        return orchestrator.deploy_with_bd_builder_pattern(deployment_plan)
    else:
        return orchestrator.deploy_immediate(device_commands)


def validate_commands_on_devices(device_commands: Dict[str, List[str]]) -> Dict[str, bool]:
    """Validate commands on devices using commit-check"""
    
    orchestrator = UniversalDeploymentOrchestrator()
    
    validation_results = {}
    
    for device_name, commands in device_commands.items():
        result = orchestrator.command_executor.execute_with_mode(
            device_name, commands, ExecutionMode.COMMIT_CHECK
        )
        validation_results[device_name] = result.success
    
    return validation_results
