#!/usr/bin/env python3
"""
BD Editor Deployment Integration

Integration with SSH deployment system for deploying BD configuration
changes directly to network devices with validation and rollback support.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from .data_models import DeploymentResult, DeviceDeploymentResult, DeploymentError

logger = logging.getLogger(__name__)


class BDEditorDeploymentIntegration:
    """Integration with SSH deployment system"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.ssh_manager = None
        
        # Use the same proven device connection logic as interface discovery
        try:
            # Import the working SSH approach from interface discovery
            self.ssh_deployment_available = True
            logger.info("Using proven device connection logic from interface discovery")
        except Exception as e:
            self.ssh_deployment_available = False
            logger.warning(f"SSH deployment setup failed: {e}")
    
    def deploy_bd_changes(self, bridge_domain: Dict, session: Dict) -> DeploymentResult:
        """Deploy BD changes to network devices"""
        
        try:
            # Generate deployment plan
            deployment_plan = self._create_deployment_plan(bridge_domain, session)
            
            if not deployment_plan['commands_by_device']:
                return DeploymentResult(
                    success=True,
                    affected_devices=[],
                    commands_executed={},
                    errors=["No changes to deploy"]
                )
            
            # Validate deployment plan
            validation = self._validate_deployment_plan(deployment_plan)
            if not validation['is_valid']:
                return DeploymentResult(
                    success=False,
                    errors=validation['errors']
                )
            
            # Try to use drift-aware deployment with Stop and Sync approach
            try:
                from services.configuration_drift import DriftAwareDeploymentHandler
                
                print(f"\n🔄 EXECUTING DRIFT-AWARE DEPLOYMENT (Stop and Sync)")
                print("="*60)
                print("💡 Automatic detection and handling of configuration drift")
                
                # Convert deployment plan to universal format
                universal_plan = self._convert_to_universal_deployment_plan(deployment_plan)
                
                # Use drift-aware deployment
                drift_handler = DriftAwareDeploymentHandler()
                return self._convert_from_universal_result(
                    drift_handler.deploy_with_drift_handling(universal_plan)
                )
                
            except ImportError:
                print("⚠️  Configuration drift handling not available - using standard BD-Builder pattern")
                
                # Fallback to standard BD-Builder deployment pattern
                print(f"\n🛡️  EXECUTING SAFE DEPLOYMENT (BD-Builder Pattern)")
                print("="*60)
                
                # Stage 1: Commit-check on all devices
                print(f"🔍 Stage 1: Commit-check validation on all devices...")
                commit_check_results = {}
                commit_check_errors = []
                
                for device_name, commands in deployment_plan['commands_by_device'].items():
                    print(f"   🔍 Checking {device_name}...")
                    
                    check_success, check_message = self._execute_commit_check(device_name, commands)
                    commit_check_results[device_name] = (check_success, check_message)
                    
                    if check_success:
                        print(f"   ✅ {device_name}: Commit-check passed")
                        
                        # Check for "already configured" in commit-check message
                        if 'already configured' in check_message.lower() or 'no changes needed' in check_message.lower():
                            print(f"   💡 {device_name}: Configuration already exists on device")
                            print(f"   ⚠️  DATABASE-REALITY SYNC ISSUE DETECTED!")
                            print(f"   💡 Device has configurations that database doesn't know about")
                            print(f"   🔧 Consider running targeted discovery to sync database")
                    else:
                        print(f"   ❌ {device_name}: Commit-check failed - {check_message}")
                        commit_check_errors.append(f"{device_name}: {check_message}")
                
                # Check if all commit-checks passed
                if commit_check_errors:
                    print(f"\n❌ COMMIT-CHECK FAILURES - Deployment aborted")
                    for error in commit_check_errors:
                        print(f"   • {error}")
                    
                    return DeploymentResult(
                        success=False,
                        errors=commit_check_errors
                    )
                
                print(f"\n✅ All commit-checks passed - proceeding with deployment")
            
            # Stage 2: Parallel deployment to all devices
            print(f"\n⚡ Stage 2: Parallel deployment to all devices...")
            deployment_results = []
            
            for device_name, commands in deployment_plan['commands_by_device'].items():
                print(f"   🚀 Deploying to {device_name}...")
                device_result = self._execute_real_deployment(device_name, commands)
                deployment_results.append(device_result)
            
            # Analyze overall deployment result
            return self._analyze_deployment_results(deployment_results)
            
        except Exception as e:
            logger.error(f"Error deploying BD changes: {e}")
            return DeploymentResult(
                success=False,
                errors=[f"Deployment failed: {e}"]
            )
    
    def _create_deployment_plan(self, bridge_domain: Dict, session: Dict) -> Dict:
        """Create deployment plan from session changes"""
        
        try:
            from .config_preview import ConfigurationPreviewSystem
            
            # Generate configuration preview
            preview_system = ConfigurationPreviewSystem()
            preview_report = preview_system.generate_full_preview(bridge_domain, session)
            
            deployment_plan = {
                'bd_name': bridge_domain.get('name'),
                'commands_by_device': preview_report.commands_by_device,
                'affected_devices': list(preview_report.affected_devices),
                'total_commands': len(preview_report.all_commands),
                'validation_result': preview_report.validation_result,
                'impact_analysis': preview_report.impact_analysis,
                'created_at': datetime.now().isoformat()
            }
            
            return deployment_plan
            
        except Exception as e:
            logger.error(f"Error creating deployment plan: {e}")
            raise DeploymentError(f"Failed to create deployment plan: {e}")
    
    def _validate_deployment_plan(self, deployment_plan: Dict) -> Dict:
        """Validate deployment plan before execution"""
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check if there are commands to deploy
            if not deployment_plan.get('commands_by_device'):
                validation_result['errors'].append("No commands to deploy")
                validation_result['is_valid'] = False
                return validation_result
            
            # Check validation result from preview
            preview_validation = deployment_plan.get('validation_result')
            if preview_validation and not preview_validation.is_valid:
                validation_result['errors'].extend(preview_validation.errors)
                validation_result['warnings'].extend(preview_validation.warnings)
                validation_result['is_valid'] = False
            
            # Check SSH deployment availability
            if not self.ssh_deployment_available:
                validation_result['errors'].append("SSH deployment system not available")
                validation_result['is_valid'] = False
            
            # Validate each device is reachable (placeholder)
            for device_name in deployment_plan.get('affected_devices', []):
                if not self._is_device_reachable(device_name):
                    validation_result['warnings'].append(f"Device {device_name} may not be reachable")
            
        except Exception as e:
            logger.error(f"Error validating deployment plan: {e}")
            validation_result['errors'].append(f"Deployment plan validation failed: {e}")
            validation_result['is_valid'] = False
        
        return validation_result
    
    def _deploy_to_device(self, device_name: str, commands: List[str]) -> DeviceDeploymentResult:
        """Deploy commands to specific device using proven SSH logic from interface discovery"""
        
        try:
            if not self.ssh_deployment_available:
                return DeviceDeploymentResult(
                    device=device_name,
                    success=False,
                    errors=["SSH deployment system not available"]
                )
            
            print(f"🚀 Deploying to {device_name}...")
            print(f"📋 Commands to execute: {len(commands)}")
            
            # Show commands that will be executed
            for i, command in enumerate(commands, 1):
                print(f"   {i}. {command}")
            
            print(f"🔌 Connecting to {device_name}...")
            
            # Use the same proven SSH logic as interface discovery
            success, execution_time, output, errors = self._execute_ssh_commands_on_device(device_name, commands)
            
            # Create result
            result = DeviceDeploymentResult(
                device=device_name,
                success=success,
                commands_executed=commands if success else [],
                output=output
            )
            
            # Show progress and results
            if success:
                print(f"✅ Successfully deployed to {device_name}")
                print(f"⏱️  Execution time: {execution_time:.2f}s")
                
                # Post-deployment validation
                print(f"🔍 Validating configuration on {device_name}...")
                validation_success = self._validate_deployed_configuration(device_name, commands)
                
                if validation_success:
                    print(f"✅ Configuration validated on {device_name}")
                    logger.info(f"Real deployment to {device_name}: {len(commands)} commands executed and validated")
                else:
                    print(f"⚠️  Configuration validation failed on {device_name}")
                    result.errors = ["Configuration deployed but validation failed"]
                    result.success = False
            else:
                print(f"❌ Deployment failed on {device_name}")
                if errors:
                    print(f"🔍 Error details: {'; '.join(errors)}")
                result.errors = errors
            
            return result
            
        except Exception as e:
            logger.error(f"Error deploying to {device_name}: {e}")
            print(f"❌ Deployment error on {device_name}: {e}")
            return DeviceDeploymentResult(
                device=device_name,
                success=False,
                commands_executed=[],
                errors=[str(e)]
            )
    
    def _execute_ssh_commands_on_device(self, device_name: str, commands: List[str]) -> tuple:
        """Execute SSH commands using proper DRIVENETS configuration mode"""
        
        try:
            import yaml
            from utils.dnos_ssh import DNOSSSH
            import time
            
            # Load device info
            with open('devices.yaml', 'r') as f:
                devices_data = yaml.safe_load(f)
            
            device_info = devices_data.get(device_name)
            if not device_info:
                return False, 0, "", [f"Device {device_name} not found in devices.yaml"]
            
            defaults = devices_data.get('defaults', {})
            hostname = device_info.get('mgmt_ip')
            username = device_info.get('username', defaults.get('username'))
            password = device_info.get('password', defaults.get('password'))
            
            if not all([hostname, username, password]):
                return False, 0, "", [f"Incomplete connection info for {device_name}"]
            
            start_time = time.time()
            
            # Use proper DNOSSSH class for configuration
            ssh_client = DNOSSSH(
                hostname=hostname,
                username=username,
                password=password,
                debug=True
            )
            
            # Connect to device
            if not ssh_client.connect():
                return False, 0, "", [f"Failed to connect to {device_name}"]
            
            try:
                print(f"   🔧 Entering configuration mode...")
                
                # Execute commands one by one to detect errors
                ssh_client.send_command('configure')
                time.sleep(1)
                
                config_success = True
                error_messages = []
                
                for command in commands:
                    print(f"   ⚡ Executing: {command}")
                    output = ssh_client.send_command(command)
                    
                    # Check for errors in command output
                    if 'ERROR:' in output or 'error:' in output:
                        error_line = [line for line in output.split('\\n') if 'ERROR:' in line or 'error:' in line]
                        if error_line:
                            error_msg = error_line[0].strip()
                            print(f"   ❌ Command failed: {error_msg}")
                            error_messages.append(error_msg)
                            config_success = False
                    else:
                        print(f"   ✅ Command executed successfully")
                
                execution_time = time.time() - start_time
                
                if config_success:
                    # Commit configuration
                    print(f"   💾 Committing configuration...")
                    commit_output = ssh_client.send_command('commit and-exit')
                    
                    if 'no configuration changes were made' in commit_output:
                        print(f"   ⚠️  No configuration changes to commit")
                        return False, execution_time, commit_output, ["No configuration changes were made"]
                    elif 'ERROR:' in commit_output:
                        print(f"   ❌ Commit failed")
                        return False, execution_time, commit_output, ["Commit failed"]
                    else:
                        print(f"   ✅ Configuration committed successfully")
                        return True, execution_time, "Configuration applied and committed", []
                else:
                    print(f"   ❌ Configuration failed due to command errors")
                    ssh_client.send_command('exit')  # Exit config mode without commit
                    return False, execution_time, "Configuration failed", error_messages
                
            finally:
                ssh_client.disconnect()
            
        except Exception as e:
            logger.error(f"SSH execution failed for {device_name}: {e}")
            return False, 0, "", [str(e)]
    
    def _execute_commit_check(self, device_name: str, commands: List[str]) -> tuple:
        """Execute commit-check validation (BD-Builder pattern: test config without commit)"""
        
        try:
            import yaml
            from utils.dnos_ssh import DNOSSSH
            
            # Load device info
            with open('devices.yaml', 'r') as f:
                devices_data = yaml.safe_load(f)
            
            device_info = devices_data.get(device_name)
            if not device_info:
                return False, f"Device {device_name} not found in devices.yaml"
            
            defaults = devices_data.get('defaults', {})
            hostname = device_info.get('mgmt_ip')
            username = device_info.get('username', defaults.get('username'))
            password = device_info.get('password', defaults.get('password'))
            
            if not all([hostname, username, password]):
                return False, f"Incomplete connection info for {device_name}"
            
            # Use DNOSSSH for commit-check (enable debug to see logs)
            ssh_client = DNOSSSH(
                hostname=hostname,
                username=username,
                password=password,
                debug=True  # Enable debug to see SSH logs like real deployment
            )
            
            if not ssh_client.connect():
                return False, f"Failed to connect to {device_name} for commit-check"
            
            try:
                print(f"     🔌 Connecting to {device_name} for commit-check...")
                
                # Enter config mode
                print(f"     🔧 Entering configuration mode...")
                ssh_client.send_command('configure')
                
                # Execute commands to test syntax and validity
                for command in commands:
                    print(f"     ⚡ Testing command: {command}")
                    output = ssh_client.send_command(command)
                    
                    # Check for errors in command execution
                    if 'ERROR:' in output or 'error:' in output:
                        error_line = [line for line in output.split('\\n') if 'ERROR:' in line or 'error:' in line]
                        if error_line:
                            error_msg = error_line[0].strip()
                            print(f"     ❌ Command failed: {error_msg}")
                            # Exit config mode without commit
                            ssh_client.send_command('exit')
                            return False, f"Commit-check failed: {error_msg}"
                    else:
                        print(f"     ✅ Command syntax OK")
                
                # Execute COMMIT CHECK (BD-Builder pattern)
                print(f"     🔍 Running commit check...")
                commit_check_output = ssh_client.send_command('commit check')
                print(f"     📊 Commit check result: {commit_check_output[:100]}...")
                
                # Analyze commit check result
                if 'ERROR:' in commit_check_output or 'error:' in commit_check_output:
                    # Commit check failed - configuration has issues
                    print(f"     ❌ Commit check failed: Configuration has errors")
                    ssh_client.send_command('exit')
                    return False, f"Commit-check failed: Configuration has errors"
                elif 'no configuration changes' in commit_check_output.lower():
                    # No changes to commit - might be already configured
                    print(f"     💡 Commit check: No changes needed (already configured)")
                    ssh_client.send_command('exit')
                    return True, "Commit-check passed (no changes needed - already configured)"
                else:
                    # Commit check passed - configuration is valid
                    print(f"     ✅ Commit check passed: Configuration validated")
                    ssh_client.send_command('exit')  # Exit without committing
                    return True, "Commit-check passed (configuration validated)"
                
            finally:
                ssh_client.disconnect()
            
        except Exception as e:
            logger.error(f"Commit-check failed for {device_name}: {e}")
            return False, str(e)
    
    def _execute_real_deployment(self, device_name: str, commands: List[str]) -> DeviceDeploymentResult:
        """Execute real deployment after commit-check passed"""
        
        try:
            # Use the proven SSH execution logic
            success, execution_time, output, errors = self._execute_ssh_commands_on_device(device_name, commands)
            
            result = DeviceDeploymentResult(
                device=device_name,
                success=success,
                commands_executed=commands if success else [],
                output=output
            )
            
            if success:
                print(f"   ✅ {device_name}: Deployment successful ({execution_time:.2f}s)")
                
                # Post-deployment validation
                validation_success = self._validate_deployed_configuration(device_name, commands)
                if not validation_success:
                    print(f"   ⚠️  {device_name}: Post-deployment validation failed")
                    result.success = False
                    result.errors = ["Post-deployment validation failed"]
                else:
                    print(f"   ✅ {device_name}: Configuration validated")
            else:
                print(f"   ❌ {device_name}: Deployment failed")
                result.errors = errors
            
            return result
            
        except Exception as e:
            logger.error(f"Real deployment failed for {device_name}: {e}")
            return DeviceDeploymentResult(
                device=device_name,
                success=False,
                commands_executed=[],
                errors=[str(e)]
            )
    
    def _analyze_deployment_results(self, device_results: List[DeviceDeploymentResult]) -> DeploymentResult:
        """Analyze overall deployment results"""
        
        overall_success = all(result.success for result in device_results)
        affected_devices = [result.device for result in device_results]
        commands_executed = {result.device: result.commands_executed for result in device_results}
        
        # Collect all errors and warnings
        all_errors = []
        all_warnings = []
        
        for result in device_results:
            all_errors.extend(result.errors)
            
            if not result.success:
                all_warnings.append(f"Deployment failed on {result.device}")
        
        return DeploymentResult(
            success=overall_success,
            affected_devices=affected_devices,
            commands_executed=commands_executed,
            errors=all_errors,
            warnings=all_warnings,
            deployment_time=datetime.now()
        )
    
    def _validate_deployed_configuration(self, device_name: str, deployed_commands: List[str]) -> bool:
        """Validate that configuration was actually applied to device with proper verification"""
        
        try:
            import yaml
            from utils.dnos_ssh import DNOSSSH
            
            # Load device info
            with open('devices.yaml', 'r') as f:
                devices_data = yaml.safe_load(f)
            
            device_info = devices_data.get(device_name)
            if not device_info:
                logger.warning(f"Device {device_name} not found for validation")
                return False
            
            defaults = devices_data.get('defaults', {})
            hostname = device_info.get('mgmt_ip')
            username = device_info.get('username', defaults.get('username'))
            password = device_info.get('password', defaults.get('password'))
            
            # Extract interface and VLAN info from deployed commands
            interfaces_to_validate = []
            for command in deployed_commands:
                if command.startswith('interfaces ') and 'vlan-id' in command:
                    # Extract interface name and VLAN ID
                    parts = command.split()
                    if len(parts) >= 4:  # interfaces ge100-0/0/30.251 vlan-id 251
                        interface_name = parts[1]
                        vlan_id = parts[3]
                        interfaces_to_validate.append((interface_name, vlan_id))
            
            if not interfaces_to_validate:
                logger.warning("No interfaces with VLAN configuration to validate")
                return True
            
            # Use proper DNOSSSH for validation
            ssh_client = DNOSSSH(
                hostname=hostname,
                username=username,
                password=password,
                debug=False  # Disable debug for validation
            )
            
            if not ssh_client.connect():
                logger.error(f"Failed to connect to {device_name} for validation")
                return False
            
            try:
                validation_success = True
                
                for interface_name, expected_vlan in interfaces_to_validate:
                    print(f"     🔍 Validating {interface_name} VLAN {expected_vlan}...")
                    
                    # Check if interface exists and has correct VLAN
                    validation_command = f"show interfaces {interface_name}"
                    output = ssh_client.send_command(validation_command)
                    
                    # Check for interface existence and VLAN configuration
                    if not output or 'not found' in output.lower():
                        print(f"     ❌ Interface {interface_name} not found")
                        validation_success = False
                        break
                    
                    # Check for VLAN configuration
                    if f"vlan-id {expected_vlan}" not in output and f"VLAN {expected_vlan}" not in output:
                        print(f"     ❌ VLAN {expected_vlan} not configured on {interface_name}")
                        validation_success = False
                        break
                    
                    print(f"     ✅ {interface_name} VLAN {expected_vlan} validated")
                
                return validation_success
                
            finally:
                ssh_client.disconnect()
            
        except Exception as e:
            logger.error(f"Error validating configuration on {device_name}: {e}")
            return False
    
    def _analyze_deployment_results(self, device_results: List[DeviceDeploymentResult]) -> DeploymentResult:
        """Analyze overall deployment results"""
        
        overall_success = all(result.success for result in device_results)
        affected_devices = [result.device for result in device_results]
        commands_executed = {result.device: result.commands_executed for result in device_results}
        
        # Collect all errors and warnings
        all_errors = []
        all_warnings = []
        
        for result in device_results:
            all_errors.extend(result.errors)
            
            if not result.success:
                all_warnings.append(f"Deployment failed on {result.device}")
        
        return DeploymentResult(
            success=overall_success,
            affected_devices=affected_devices,
            commands_executed=commands_executed,
            errors=all_errors,
            warnings=all_warnings,
            deployment_time=datetime.now()
        )
    
    def _is_device_reachable(self, device_name: str) -> bool:
        """Check if device is reachable using same logic as interface discovery"""
        
        try:
            import yaml
            import paramiko
            
            # Load device info using the same logic as interface discovery
            with open('devices.yaml', 'r') as f:
                devices_data = yaml.safe_load(f)
            
            device_info = devices_data.get(device_name)
            if not device_info:
                logger.warning(f"Device {device_name} not found in devices.yaml")
                return False
            
            defaults = devices_data.get('defaults', {})
            hostname = device_info.get('mgmt_ip')
            username = device_info.get('username', defaults.get('username'))
            password = device_info.get('password', defaults.get('password'))
            
            if not all([hostname, username, password]):
                logger.warning(f"Incomplete connection info for {device_name}")
                return False
            
            # Quick connection test
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=hostname, username=username, password=password, timeout=10)
                client.close()
                
                logger.debug(f"Device {device_name} is reachable at {hostname}")
                return True
                
            except Exception as conn_e:
                logger.debug(f"Device {device_name} not reachable: {conn_e}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking reachability for {device_name}: {e}")
            return False
    
    def create_rollback_plan(self, deployment_result: DeploymentResult, original_session: Dict) -> Dict:
        """Create rollback plan for failed deployment"""
        
        rollback_plan = {
            'rollback_needed': not deployment_result.success,
            'affected_devices': deployment_result.affected_devices,
            'rollback_commands': {},
            'created_at': datetime.now().isoformat()
        }
        
        if deployment_result.success:
            return rollback_plan
        
        try:
            # Generate rollback commands for each device
            for device_name in deployment_result.affected_devices:
                device_commands = deployment_result.commands_executed.get(device_name, [])
                rollback_commands = self._generate_rollback_commands(device_commands)
                rollback_plan['rollback_commands'][device_name] = rollback_commands
            
        except Exception as e:
            logger.error(f"Error creating rollback plan: {e}")
            rollback_plan['errors'] = [f"Rollback plan creation failed: {e}"]
        
        return rollback_plan
    
    def _generate_rollback_commands(self, original_commands: List[str]) -> List[str]:
        """Generate rollback commands for original commands"""
        
        rollback_commands = []
        
        try:
            for command in original_commands:
                # Generate reverse command
                if command.startswith('interfaces ') and not command.startswith('no '):
                    # Add 'no' prefix to reverse interface commands
                    rollback_command = f"no {command}"
                    rollback_commands.append(rollback_command)
                # Add more rollback logic as needed
            
        except Exception as e:
            logger.error(f"Error generating rollback commands: {e}")
        
        return rollback_commands
    
    def _convert_to_universal_deployment_plan(self, deployment_plan: Dict):
        """Convert BD Editor deployment plan to universal SSH framework format"""
        
        try:
            from services.universal_ssh import DeploymentPlan
            import time
            
            deployment_id = f"bd_deployment_{int(time.time())}"
            
            return DeploymentPlan(
                deployment_id=deployment_id,
                device_commands=deployment_plan['commands_by_device'],
                metadata={
                    'bd_name': deployment_plan.get('bd_name'),
                    'total_commands': deployment_plan.get('total_commands', 0),
                    'source': 'bd_editor'
                }
            )
            
        except ImportError:
            # Create simple object if universal SSH not available
            class SimpleDeploymentPlan:
                def __init__(self, deployment_id, device_commands, metadata):
                    self.deployment_id = deployment_id
                    self.device_commands = device_commands
                    self.metadata = metadata
            
            return SimpleDeploymentPlan(
                deployment_id=f"bd_deployment_{int(time.time())}",
                device_commands=deployment_plan['commands_by_device'],
                metadata={'bd_name': deployment_plan.get('bd_name')}
            )
    
    def _convert_from_universal_result(self, universal_result) -> DeploymentResult:
        """Convert universal SSH deployment result to BD Editor format"""
        
        try:
            # Convert execution_results to commands_executed format
            commands_executed = {}
            for device_name, exec_result in universal_result.execution_results.items():
                commands_executed[device_name] = exec_result.commands_executed
            
            return DeploymentResult(
                success=universal_result.success,
                affected_devices=universal_result.affected_devices,
                commands_executed=commands_executed,
                errors=universal_result.errors,
                warnings=getattr(universal_result, 'warnings', []),
                deployment_time=getattr(universal_result, 'deployment_time', datetime.now())
            )
            
        except Exception as e:
            logger.error(f"Error converting universal deployment result: {e}")
            return DeploymentResult(
                success=False,
                errors=[f"Result conversion failed: {e}"]
            )


class ProductionBDEditor:
    """Production-ready BD editor with complete intelligent menu system"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Initialize all systems
        from .menu_system import IntelligentBDEditorMenu
        from .health_checker import BDHealthChecker
        from .error_handler import BDEditorErrorHandler
        from .session_manager import BDEditingSessionManager
        
        self.menu_system = IntelligentBDEditorMenu()
        self.health_checker = BDHealthChecker()
        self.error_handler = BDEditorErrorHandler()
        self.session_manager = BDEditingSessionManager(db_manager)
        self.deployment_integration = BDEditorDeploymentIntegration(db_manager)
    
    def start_bd_editing_session(self, bd_name: str) -> bool:
        """Start complete BD editing session with intelligent menu"""
        
        try:
            print(f"\n🧠 STARTING INTELLIGENT BD EDITING SESSION")
            print("="*60)
            print(f"Bridge Domain: {bd_name}")
            
            # Create editing session
            session = self.session_manager.create_editing_session(bd_name)
            working_copy = session['working_copy']
            
            # Health check before editing
            print(f"\n📊 Performing BD health check...")
            health_report = self.health_checker.check_bd_health(working_copy)
            
            if health_report.has_errors():
                print("❌ BD Health Check Failed:")
                for error in health_report.errors:
                    print(f"   • {error}")
                
                if not input("Continue anyway? (y/N): ").lower().startswith('y'):
                    print("❌ Editing cancelled due to health check failures")
                    return False
            elif health_report.warnings:
                print("⚠️  BD Health Check Warnings:")
                for warning in health_report.warnings:
                    print(f"   • {warning}")
            else:
                print("✅ BD health check passed")
            
            # Display BD type information
            self.menu_system.display_bd_editing_header(working_copy, session)
            
            # Create intelligent menu adapter
            menu_adapter = self.menu_system.create_menu_for_bd(working_copy, session)
            
            print(f"\n🎯 Using {type(menu_adapter).__name__} for this BD type")
            
            # Main editing loop
            while True:
                try:
                    # Save session state
                    self.session_manager.save_session_state(session)
                    
                    # Show menu and get choice
                    choice = menu_adapter.show_menu()
                    
                    # Execute action
                    continue_editing = menu_adapter.execute_action(choice)
                    
                    if not continue_editing:
                        break  # User chose to exit
                        
                except KeyboardInterrupt:
                    print("\\n⚠️  Editing interrupted")
                    
                    if input("Save session and exit? (Y/n): ").lower() != 'n':
                        self.session_manager.save_session_state(session)
                        print("✅ Session saved - you can resume later")
                    
                    break
                    
                except Exception as e:
                    # Use error handler for unexpected errors
                    try:
                        self.error_handler.handle_error('generic_error', e, {
                            'bridge_domain': working_copy,
                            'session': session
                        })
                    except BDEditorExitException:
                        break
            
            print(f"\\n📊 EDITING SESSION SUMMARY")
            print("="*50)
            
            changes_count = len(session.get('changes_made', []))
            print(f"Changes made: {changes_count}")
            
            if changes_count > 0:
                print("💡 Use 'Preview Changes' to see CLI commands before deployment")
                print("💡 Use 'Save & Deploy' to apply changes to network")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in BD editing session: {e}")
            print(f"❌ BD editing session failed: {e}")
            return False
    
    def deploy_session_changes(self, session: Dict) -> DeploymentResult:
        """Deploy all changes from editing session"""
        
        try:
            working_copy = session.get('working_copy', {})
            changes = session.get('changes_made', [])
            
            if not changes:
                return DeploymentResult(
                    success=True,
                    errors=["No changes to deploy"]
                )
            
            print(f"\\n🚀 DEPLOYING BD CHANGES")
            print("="*50)
            print(f"Bridge Domain: {working_copy.get('name')}")
            print(f"Changes to deploy: {len(changes)}")
            
            # Show deployment preview
            from .config_preview import ConfigurationPreviewSystem
            preview_system = ConfigurationPreviewSystem()
            preview_report = preview_system.generate_full_preview(working_copy, session)
            
            print(f"\\n📋 DEPLOYMENT PREVIEW:")
            print(f"   • Commands: {len(preview_report.all_commands)}")
            print(f"   • Devices: {len(preview_report.affected_devices)}")
            
            if preview_report.validation_result and not preview_report.validation_result.is_valid:
                print("❌ Validation errors prevent deployment:")
                for error in preview_report.validation_result.errors:
                    print(f"   • {error}")
                return DeploymentResult(
                    success=False,
                    errors=preview_report.validation_result.errors
                )
            
            # Confirm deployment
            confirm = input("\\nProceed with deployment? (y/N): ").strip().lower()
            if confirm != 'y':
                print("❌ Deployment cancelled by user")
                return DeploymentResult(
                    success=False,
                    errors=["Deployment cancelled by user"]
                )
            
            # Execute deployment
            deployment_result = self.deployment_integration.deploy_bd_changes(working_copy, session)
            
            # Update session with deployment result
            session['deployment_result'] = {
                'success': deployment_result.success,
                'deployed_at': datetime.now().isoformat(),
                'affected_devices': deployment_result.affected_devices,
                'errors': deployment_result.errors
            }
            
            # Save session
            self.session_manager.save_session_state(session)
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"Error deploying session changes: {e}")
            return DeploymentResult(
                success=False,
                errors=[f"Deployment error: {e}"]
            )


# Enhanced BD Editor CLI Integration
def enhanced_bd_editor_with_intelligent_menu(db_manager, bd_name: str) -> bool:
    """Enhanced BD editor with complete intelligent menu system"""
    
    try:
        # Initialize production BD editor
        production_editor = ProductionBDEditor(db_manager)
        
        # Start intelligent editing session
        success = production_editor.start_bd_editing_session(bd_name)
        
        return success
        
    except Exception as e:
        logger.error(f"Error in enhanced BD editor: {e}")
        print(f"❌ Enhanced BD editor failed: {e}")
        return False


# Integration with existing BD editor
def replace_bd_editor_with_intelligent_system(session, db_manager):
    """Replace basic BD editor with intelligent system"""
    
    try:
        working_copy = session.get('working_copy', {})
        bd_name = working_copy.get('name', 'unknown')
        
        print(f"\\n🧠 SWITCHING TO INTELLIGENT BD EDITOR")
        print("="*60)
        print("💡 Enhanced with type-aware menus, validation, and preview")
        
        # Initialize production editor
        production_editor = ProductionBDEditor(db_manager)
        
        # Use existing session or create new one
        if 'session_id' not in session:
            # Create new intelligent session
            intelligent_session = production_editor.session_manager.create_editing_session(bd_name)
            
            # Migrate existing changes
            if 'changes_made' in session:
                intelligent_session['changes_made'] = session['changes_made']
            
            session.update(intelligent_session)
        
        # Create intelligent menu
        menu_adapter = production_editor.menu_system.create_menu_for_bd(working_copy, session)
        
        print(f"✅ Intelligent menu activated: {type(menu_adapter).__name__}")
        
        # Main intelligent editing loop
        while True:
            try:
                choice = menu_adapter.show_menu()
                
                if not menu_adapter.execute_action(choice):
                    break  # User chose to exit
                    
            except KeyboardInterrupt:
                print("\\n⚠️  Intelligent editing interrupted")
                break
            except Exception as e:
                print(f"❌ Error in intelligent menu: {e}")
                break
        
        return True
        
    except Exception as e:
        logger.error(f"Error replacing BD editor with intelligent system: {e}")
        print(f"❌ Failed to switch to intelligent system: {e}")
        return False


# Convenience functions
def deploy_bd_changes(bridge_domain: Dict, session: Dict, db_manager) -> DeploymentResult:
    """Convenience function to deploy BD changes"""
    deployment_integration = BDEditorDeploymentIntegration(db_manager)
    return deployment_integration.deploy_bd_changes(bridge_domain, session)


def start_intelligent_bd_editor(bd_name: str, db_manager) -> bool:
    """Convenience function to start intelligent BD editor"""
    return enhanced_bd_editor_with_intelligent_menu(db_manager, bd_name)
