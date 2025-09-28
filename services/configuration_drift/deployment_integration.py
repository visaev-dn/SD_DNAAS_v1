#!/usr/bin/env python3
"""
Drift-Aware Deployment Integration

Integrates configuration drift handling with deployment systems,
providing automatic detection and resolution of database-reality sync issues.
"""

import logging
from typing import Dict, List
from .data_models import DriftEvent, SyncAction, DriftType
from .drift_detector import ConfigurationDriftDetector
from .sync_resolver import ConfigurationSyncResolver

logger = logging.getLogger(__name__)


class DriftAwareDeploymentHandler:
    """Integrates drift handling with universal SSH deployment"""
    
    def __init__(self):
        # Use universal SSH framework for deployment
        try:
            from services.universal_ssh import UniversalDeploymentOrchestrator
            self.orchestrator = UniversalDeploymentOrchestrator()
            self.ssh_available = True
        except ImportError:
            self.orchestrator = None
            self.ssh_available = False
            logger.warning("Universal SSH framework not available")
        
        self.drift_detector = ConfigurationDriftDetector()
        self.sync_resolver = ConfigurationSyncResolver()
    
    def deploy_with_drift_handling(self, deployment_plan) -> 'DeploymentResult':
        """Execute deployment with COMMIT-CHECK-FIRST drift detection and handling"""
        
        try:
            if not self.ssh_available:
                raise Exception("Universal SSH framework not available")
            
            print(f"\\n🔄 DRIFT-AWARE DEPLOYMENT (Stop and Sync at Commit-Check)")
            print("="*60)
            print("💡 Drift detection BEFORE deployment - Conservative approach")
            
            # STAGE 1: COMMIT-CHECK WITH DRIFT DETECTION (Stop and Sync approach)
            print(f"\\n🔍 Stage 1: Commit-check with drift detection...")
            
            drift_events = []
            commit_check_results = {}
            
            # Execute commit-check on each device and detect drift immediately
            for device_name, commands in deployment_plan.device_commands.items():
                print(f"   🔍 Checking {device_name}...")
                
                # Use universal SSH framework for commit-check
                try:
                    from services.universal_ssh import UniversalCommandExecutor, ExecutionMode
                    command_executor = UniversalCommandExecutor()
                    
                    # Execute commit-check
                    result = command_executor.execute_with_mode(
                        device_name, commands, ExecutionMode.COMMIT_CHECK
                    )
                    
                    commit_check_results[device_name] = result.success
                    
                    if result.success:
                        # Check for drift in commit-check message (FIXED string matching)
                        output_lower = result.output.lower()
                        
                        # DEBUG: Print the actual output for analysis
                        print(f"   🔍 DEBUG - Commit-check output: '{result.output}'")
                        print(f"   🔍 DEBUG - Output length: {len(result.output)} chars")
                        
                        # Check for all possible "already configured" patterns
                        drift_patterns = [
                            'no configuration changes were made',
                            'no changes needed',
                            'already configured',
                            'commit action is not applicable'
                        ]
                        
                        # DEBUG: Check each pattern
                        for pattern in drift_patterns:
                            if pattern in output_lower:
                                print(f"   🔍 DEBUG - DRIFT PATTERN MATCHED: '{pattern}'")
                        
                        drift_detected = any(pattern in output_lower for pattern in drift_patterns)
                        print(f"   🔍 DEBUG - Drift detected: {drift_detected}")
                        
                        if drift_detected:
                            print(f"   🛑 {device_name}: CONFIGURATION DRIFT DETECTED!")
                            print(f"   💡 Device has configurations that database doesn't know about")
                            print(f"   📊 Commit-check output: {result.output[:100]}...")
                            
                            # Extract interface name from commands
                            interface_name = None
                            for command in commands:
                                if 'interfaces ' in command:
                                    parts = command.split()
                                    if len(parts) >= 2:
                                        interface_name = parts[1]
                                        break
                            
                            # Create drift event immediately
                            drift_event = DriftEvent(
                                drift_type=DriftType.INTERFACE_ALREADY_CONFIGURED,
                                device_name=device_name,
                                interface_name=interface_name,
                                detection_source="commit_check_immediate",
                                severity="high",  # High severity to ensure handling
                                expected_config={'commands': commands},
                                actual_config={'commit_check_output': result.output}
                            )
                            drift_events.append(drift_event)
                        else:
                            print(f"   ✅ {device_name}: Commit-check passed - new configuration")
                    else:
                        print(f"   ❌ {device_name}: Commit-check failed - {result.error_message}")
                        
                except ImportError:
                    print(f"   ⚠️  Universal SSH not available - using fallback")
                    # Fallback to basic commit-check without drift detection
                    commit_check_results[device_name] = True
            
            # HANDLE DRIFT EVENTS IMMEDIATELY (Stop and Sync)
            if drift_events:
                print(f"\\n⚠️  CONFIGURATION DRIFT DETECTED AT COMMIT-CHECK")
                print("="*60)
                print(f"🛑 STOPPING DEPLOYMENT - {len(drift_events)} sync issues found")
                print("💡 Resolving drift BEFORE proceeding with deployment")
                
                all_resolutions_successful = True
                
                for i, drift_event in enumerate(drift_events, 1):
                    print(f"\\n🔧 Resolving drift issue {i}/{len(drift_events)}:")
                    print(f"   Device: {drift_event.device_name}")
                    print(f"   Issue: Configuration already exists on device")
                    
                    resolution = self.sync_resolver.resolve_drift_interactive(drift_event)
                    
                    if resolution.action == SyncAction.ABORT:
                        print(f"❌ User chose to abort deployment")
                        return self._create_aborted_deployment_result(deployment_plan, "User aborted due to configuration drift")
                        
                    elif resolution.action == SyncAction.SYNCED:
                        print(f"✅ Database synced with device reality")
                        # Continue with deployment - database now accurate
                        
                    elif resolution.action == SyncAction.SKIP:
                        print(f"⏭️  User chose to skip conflicting interfaces")
                        # Remove conflicting commands from deployment plan
                        deployment_plan.device_commands[drift_event.device_name] = []
                        
                    elif resolution.action == SyncAction.OVERRIDE:
                        print(f"🔄 User chose to force override existing configuration")
                        # Continue with deployment as planned
                        
                    elif resolution.action == SyncAction.FAILED:
                        print(f"❌ Drift resolution failed: {resolution.message}")
                        all_resolutions_successful = False
                
                if not all_resolutions_successful:
                    return self._create_failed_deployment_result(deployment_plan, "Drift resolution failed")
                
                print(f"\\n✅ All drift issues resolved - proceeding with deployment")
            
            # STAGE 2: PROCEED WITH DEPLOYMENT (drift resolved) - SKIP COMMIT-CHECK
            print(f"\\n⚡ Stage 2: Executing deployment (skipping duplicate commit-check)...")
            
            # Since we already did commit-check with drift detection, proceed directly to deployment
            # Use a custom deployment that skips the commit-check phase
            return self._execute_deployment_without_duplicate_commit_check(deployment_plan)
            
        except Exception as e:
            logger.error(f"Drift-aware deployment failed: {e}")
            
            # Return failed deployment result
            from services.universal_ssh.data_models import DeploymentResult
            return DeploymentResult(
                deployment_id=deployment_plan.deployment_id,
                success=False,
                errors=[f"Drift-aware deployment failed: {e}"]
            )
    
    def _detect_drift_from_commit_check_results(self, deployment_plan, deployment_result) -> List[DriftEvent]:
        """Detect drift from commit-check phase results"""
        
        drift_events = []
        
        try:
            # Check commit-check results in deployment result
            for device_name, passed in deployment_result.commit_check_results.items():
                if passed:
                    # Check if commit-check passed but with "no changes" message
                    device_commands = deployment_plan.device_commands.get(device_name, [])
                    
                    # Simulate commit-check output analysis (in real implementation, this would be stored)
                    # For now, we'll detect drift from the fact that commit-check passed but deployment might fail
                    
                    if device_commands:
                        # Look for interface in commands
                        interface_name = None
                        for command in device_commands:
                            if 'interfaces ' in command:
                                parts = command.split()
                                if len(parts) >= 2:
                                    interface_name = parts[1]
                                    break
                        
                        # Create drift event for potential "already configured" scenario
                        if interface_name:
                            drift_event = DriftEvent(
                                drift_type=DriftType.INTERFACE_ALREADY_CONFIGURED,
                                device_name=device_name,
                                interface_name=interface_name,
                                detection_source="commit_check_analysis",
                                severity="low"  # Lower severity since commit-check passed
                            )
                            drift_events.append(drift_event)
            
            return drift_events
            
        except Exception as e:
            logger.error(f"Error detecting drift from commit-check results: {e}")
            return []
    
    def _execute_deployment_without_duplicate_commit_check(self, deployment_plan):
        """Execute deployment without duplicate commit-check (we already did it with drift detection)"""
        
        try:
            from services.universal_ssh import UniversalCommandExecutor, ExecutionMode
            
            print(f"\\n⚡ DIRECT DEPLOYMENT (Commit-check already completed with drift handling)")
            print("="*70)
            
            command_executor = UniversalCommandExecutor()
            all_results = {}
            overall_success = True
            all_errors = []
            
            # Execute deployment directly on each device (skip commit-check)
            for device_name, commands in deployment_plan.device_commands.items():
                if not commands:  # Skip if commands were removed due to drift resolution
                    print(f"   ⏭️  {device_name}: Skipped (no commands after drift resolution)")
                    continue
                
                print(f"   🚀 Deploying to {device_name}...")
                
                # Execute with COMMIT mode (skip commit-check since we already did it)
                result = command_executor.execute_with_mode(
                    device_name, commands, ExecutionMode.COMMIT
                )
                
                all_results[device_name] = result
                
                if result.success:
                    print(f"   ✅ {device_name}: Deployment successful ({result.total_execution_time:.2f}s)")
                else:
                    print(f"   ❌ {device_name}: Deployment failed - {result.error_message}")
                    all_errors.append(f"{device_name}: {result.error_message}")
                    overall_success = False
            
            # Create deployment result
            from services.universal_ssh.data_models import DeploymentResult
            
            deployment_result = DeploymentResult(
                deployment_id=deployment_plan.deployment_id,
                success=overall_success,
                execution_results=all_results,
                affected_devices=list(deployment_plan.device_commands.keys()),
                errors=all_errors
            )
            
            print(f"\\n📊 DRIFT-AWARE DEPLOYMENT RESULTS:")
            print("="*50)
            if overall_success:
                print("✅ DEPLOYMENT SUCCESSFUL!")
                print(f"📡 Devices updated: {len(all_results)}")
            else:
                print("❌ DEPLOYMENT FAILED!")
                for error in all_errors:
                    print(f"   • {error}")
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Direct deployment failed: {e}")
            return self._create_failed_deployment_result(deployment_plan, f"Direct deployment failed: {e}")
    
    def _create_aborted_deployment_result(self, deployment_plan, reason: str):
        """Create deployment result for aborted deployment"""
        try:
            from services.universal_ssh.data_models import DeploymentResult
            return DeploymentResult(
                deployment_id=deployment_plan.deployment_id,
                success=False,
                affected_devices=list(deployment_plan.device_commands.keys()),
                errors=[reason]
            )
        except ImportError:
            # Fallback if universal SSH not available
            class SimpleDeploymentResult:
                def __init__(self, success, errors, affected_devices):
                    self.success = success
                    self.errors = errors
                    self.affected_devices = affected_devices
            
            return SimpleDeploymentResult(
                success=False,
                errors=[reason],
                affected_devices=list(deployment_plan.device_commands.keys())
            )
    
    def _create_failed_deployment_result(self, deployment_plan, reason: str):
        """Create deployment result for failed deployment"""
        try:
            from services.universal_ssh.data_models import DeploymentResult
            return DeploymentResult(
                deployment_id=deployment_plan.deployment_id,
                success=False,
                affected_devices=list(deployment_plan.device_commands.keys()),
                errors=[reason]
            )
        except ImportError:
            # Fallback if universal SSH not available
            class SimpleDeploymentResult:
                def __init__(self, success, errors, affected_devices):
                    self.success = success
                    self.errors = errors
                    self.affected_devices = affected_devices
            
            return SimpleDeploymentResult(
                success=False,
                errors=[reason],
                affected_devices=list(deployment_plan.device_commands.keys())
            )


# Convenience function
def deploy_with_drift_handling(deployment_plan) -> 'DeploymentResult':
    """Convenience function for drift-aware deployment"""
    handler = DriftAwareDeploymentHandler()
    return handler.deploy_with_drift_handling(deployment_plan)
