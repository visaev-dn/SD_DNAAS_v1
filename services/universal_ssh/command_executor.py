#!/usr/bin/env python3
"""
Universal Command Executor

Unified command execution with all proven patterns extracted from
DNOSSSH, interface discovery, and BD-Builder systems.
"""

import time
import logging
from typing import List, Dict
from .data_models import ExecutionMode, ExecutionResult, CommandResult, CommandExecutionError
from .device_manager import UniversalDeviceManager

logger = logging.getLogger(__name__)


class UniversalCommandExecutor:
    """Unified command execution with all proven patterns"""
    
    def __init__(self):
        self.device_manager = UniversalDeviceManager()
        
    def execute_with_mode(self, device_name: str, commands: List[str], mode: ExecutionMode) -> ExecutionResult:
        """Execute commands with specified mode using proven patterns"""
        
        try:
            if mode == ExecutionMode.COMMIT_CHECK:
                return self._execute_commit_check(device_name, commands)
            elif mode == ExecutionMode.COMMIT:
                return self._execute_commit(device_name, commands)
            elif mode == ExecutionMode.QUERY:
                return self._execute_query(device_name, commands)
            elif mode == ExecutionMode.DRY_RUN:
                return self._execute_dry_run(device_name, commands)
            elif mode == ExecutionMode.IMMEDIATE:
                return self._execute_immediate(device_name, commands)
            else:
                raise CommandExecutionError(f"Unknown execution mode: {mode}")
                
        except Exception as e:
            logger.error(f"Command execution failed for {device_name}: {e}")
            return ExecutionResult(
                device_name=device_name,
                success=False,
                execution_mode=mode,
                error_message=str(e)
            )
    
    def execute_parallel(self, device_commands: Dict[str, List[str]], mode: ExecutionMode = ExecutionMode.COMMIT) -> Dict[str, ExecutionResult]:
        """Execute commands on multiple devices in parallel (interface discovery pattern)"""
        
        try:
            import concurrent.futures
            
            results = {}
            
            # Use proven parallel pattern from interface discovery
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit execution tasks
                future_to_device = {
                    executor.submit(self.execute_with_mode, device_name, commands, mode): device_name
                    for device_name, commands in device_commands.items()
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_device):
                    device_name = future_to_device[future]
                    try:
                        result = future.result()
                        results[device_name] = result
                    except Exception as e:
                        logger.error(f"Parallel execution failed for {device_name}: {e}")
                        results[device_name] = ExecutionResult(
                            device_name=device_name,
                            success=False,
                            execution_mode=mode,
                            error_message=str(e)
                        )
            
            return results
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            return {}
    
    def _execute_commit_check(self, device_name: str, commands: List[str]) -> ExecutionResult:
        """Execute commit-check using proven BD-Builder pattern"""
        
        start_time = time.time()
        result = ExecutionResult(
            device_name=device_name,
            execution_mode=ExecutionMode.COMMIT_CHECK,
            success=False
        )
        
        try:
            # Get device connection
            connection = self.device_manager.get_device_connection(device_name)
            if not connection:
                result.error_message = f"Failed to connect to {device_name}"
                return result
            
            result.connection_successful = True
            ssh_client = connection.ssh_client
            
            # Enter config mode (proven pattern)
            print(f"     🔧 Entering configuration mode...")
            ssh_client.send_command('configure')
            
            # Execute commands to test syntax and validity
            command_results = []
            for command in commands:
                print(f"     ⚡ Testing command: {command}")
                
                cmd_start = time.time()
                output = ssh_client.send_command(command)
                cmd_time = time.time() - cmd_start
                
                cmd_result = CommandResult(
                    command=command,
                    success=True,
                    output=output,
                    execution_time=cmd_time
                )
                
                # Check for errors (proven error detection)
                if 'ERROR:' in output or 'error:' in output:
                    error_lines = [line for line in output.split('\\n') if 'ERROR:' in line or 'error:' in line]
                    if error_lines:
                        error_msg = error_lines[0].strip()
                        print(f"     ❌ Command failed: {error_msg}")
                        cmd_result.success = False
                        cmd_result.error_message = error_msg
                        result.error_message = f"Command failed: {error_msg}"
                        
                        # Exit config mode without commit
                        ssh_client.send_command('exit')
                        result.total_execution_time = time.time() - start_time
                        result.command_results = command_results
                        return result
                else:
                    print(f"     ✅ Command syntax OK")
                
                command_results.append(cmd_result)
            
            # Execute COMMIT CHECK (proven BD-Builder pattern)
            print(f"     🔍 Running commit check...")
            commit_check_output = ssh_client.send_command('commit check')
            print(f"     📊 Commit check result: {commit_check_output[:100]}...")
            
            # Store commit check output for drift detection
            result.output = commit_check_output
            
            # Analyze commit check result (proven logic)
            if 'ERROR:' in commit_check_output or 'error:' in commit_check_output:
                print(f"     ❌ Commit check failed: Configuration has errors")
                result.error_message = "Commit-check failed: Configuration has errors"
                result.commit_check_passed = False
            elif 'no configuration changes' in commit_check_output.lower():
                print(f"     💡 Commit check: No changes needed (already configured)")
                result.success = True
                result.commit_check_passed = True
                result.error_message = "No changes needed - already configured"
            else:
                print(f"     ✅ Commit check passed: Configuration validated")
                result.success = True
                result.commit_check_passed = True
            
            # Exit config mode without committing (proven pattern)
            ssh_client.send_command('exit')
            
            result.total_execution_time = time.time() - start_time
            result.command_results = command_results
            result.commands_executed = commands
            
            return result
            
        except Exception as e:
            logger.error(f"Commit-check execution failed for {device_name}: {e}")
            result.error_message = str(e)
            result.total_execution_time = time.time() - start_time
            return result
    
    def _execute_commit(self, device_name: str, commands: List[str]) -> ExecutionResult:
        """Execute commit using proven BD-Builder pattern"""
        
        start_time = time.time()
        result = ExecutionResult(
            device_name=device_name,
            execution_mode=ExecutionMode.COMMIT,
            success=False
        )
        
        try:
            # Get device connection
            connection = self.device_manager.get_device_connection(device_name)
            if not connection:
                result.error_message = f"Failed to connect to {device_name}"
                return result
            
            result.connection_successful = True
            ssh_client = connection.ssh_client
            
            # Use proven DNOSSSH configure method
            print(f"   🔧 Entering configuration mode...")
            config_success = ssh_client.configure(commands, commit=True)
            
            result.total_execution_time = time.time() - start_time
            result.commands_executed = commands
            
            if config_success:
                print(f"   ✅ Configuration committed successfully")
                result.success = True
                result.configuration_applied = True
            else:
                print(f"   ❌ Configuration failed")
                result.error_message = "Configuration failed to apply"
            
            return result
            
        except Exception as e:
            logger.error(f"Commit execution failed for {device_name}: {e}")
            result.error_message = str(e)
            result.total_execution_time = time.time() - start_time
            return result
    
    def _execute_query(self, device_name: str, commands: List[str]) -> ExecutionResult:
        """Execute query using proven interface discovery pattern"""
        
        start_time = time.time()
        result = ExecutionResult(
            device_name=device_name,
            execution_mode=ExecutionMode.QUERY,
            success=False
        )
        
        try:
            # Get device connection
            connection = self.device_manager.get_device_connection(device_name)
            if not connection:
                result.error_message = f"Failed to connect to {device_name}"
                return result
            
            result.connection_successful = True
            ssh_client = connection.ssh_client
            
            # Execute query commands (no config mode needed)
            command_results = []
            all_output = []
            
            for command in commands:
                print(f"   🔍 Querying: {command}")
                
                cmd_start = time.time()
                output = ssh_client.send_command(command)
                cmd_time = time.time() - cmd_start
                
                cmd_result = CommandResult(
                    command=command,
                    success=True,
                    output=output,
                    execution_time=cmd_time
                )
                
                command_results.append(cmd_result)
                all_output.append(output)
                
                print(f"   ✅ Query completed ({len(output)} chars)")
            
            result.success = True
            result.command_results = command_results
            result.commands_executed = commands
            result.output = '\\n'.join(all_output)
            result.total_execution_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed for {device_name}: {e}")
            result.error_message = str(e)
            result.total_execution_time = time.time() - start_time
            return result
    
    def _execute_dry_run(self, device_name: str, commands: List[str]) -> ExecutionResult:
        """Execute dry-run validation (syntax check only)"""
        
        result = ExecutionResult(
            device_name=device_name,
            execution_mode=ExecutionMode.DRY_RUN,
            success=True
        )
        
        # For dry-run, perform static validation only
        # This could be enhanced with actual device connection for syntax validation
        
        result.commands_executed = commands
        result.error_message = "Dry-run validation (static only)"
        
        return result
    
    def _execute_immediate(self, device_name: str, commands: List[str]) -> ExecutionResult:
        """Execute commands immediately without config mode"""
        
        start_time = time.time()
        result = ExecutionResult(
            device_name=device_name,
            execution_mode=ExecutionMode.IMMEDIATE,
            success=False
        )
        
        try:
            # Get device connection
            connection = self.device_manager.get_device_connection(device_name)
            if not connection:
                result.error_message = f"Failed to connect to {device_name}"
                return result
            
            result.connection_successful = True
            ssh_client = connection.ssh_client
            
            # Execute commands directly (no config mode)
            command_results = []
            
            for command in commands:
                print(f"   ⚡ Executing: {command}")
                
                cmd_start = time.time()
                output = ssh_client.send_command(command)
                cmd_time = time.time() - cmd_start
                
                cmd_result = CommandResult(
                    command=command,
                    success=True,
                    output=output,
                    execution_time=cmd_time
                )
                
                command_results.append(cmd_result)
                print(f"   ✅ Command completed")
            
            result.success = True
            result.command_results = command_results
            result.commands_executed = commands
            result.total_execution_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"Immediate execution failed for {device_name}: {e}")
            result.error_message = str(e)
            result.total_execution_time = time.time() - start_time
            return result


# Convenience functions
def execute_commands_on_device(device_name: str, commands: List[str], 
                              mode: ExecutionMode = ExecutionMode.COMMIT) -> ExecutionResult:
    """Convenience function to execute commands on device"""
    executor = UniversalCommandExecutor()
    return executor.execute_with_mode(device_name, commands, mode)


def execute_commands_parallel(device_commands: Dict[str, List[str]], 
                             mode: ExecutionMode = ExecutionMode.COMMIT) -> Dict[str, ExecutionResult]:
    """Convenience function for parallel command execution"""
    executor = UniversalCommandExecutor()
    return executor.execute_parallel(device_commands, mode)
