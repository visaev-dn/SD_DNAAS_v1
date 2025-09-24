#!/usr/bin/env python3
"""
Simplified SSH Manager
=====================

Clean, simple SSH operations without over-engineering.
Handles configuration deployment with minimal abstraction.
"""

import os
import yaml
import json
import paramiko
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class SSHConnection:
    """Simple SSH connection wrapper"""
    client: paramiko.SSHClient
    hostname: str
    connected_at: datetime

@dataclass
class DeploymentResult:
    """Simple deployment result"""
    success: bool
    message: str
    commands_executed: List[str]
    execution_time: float
    error_details: Optional[str] = None

class SimplifiedSSHManager:
    """
    Simplified SSH manager for configuration deployment.
    
    No over-engineering, just reliable SSH operations.
    """
    
    def __init__(self):
        self.devices = self._load_devices()
        self.connection_pool = {}
        self.config_dir = Path("configurations")
    
    def _load_devices(self) -> Dict:
        """Load device information from devices.yaml"""
        try:
            with open("devices.yaml", 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Could not load devices.yaml: {e}")
            return {}
    
    def get_available_configurations(self) -> List[Dict]:
        """Get all available configurations from organized structure"""
        configs = []
        
        # Scan pending configurations
        pending_dir = self.config_dir / "active" / "pending"
        if pending_dir.exists():
            for config_file in pending_dir.glob("*.yaml"):
                configs.append(self._create_config_info(config_file, "pending"))
        
        # Scan deployed configurations
        deployed_dir = self.config_dir / "active" / "deployed"
        if deployed_dir.exists():
            for config_file in deployed_dir.glob("*.yaml"):
                configs.append(self._create_config_info(config_file, "deployed"))
        
        return configs
    
    def _create_config_info(self, config_file: Path, status: str) -> Dict:
        """Create configuration info from file"""
        service_name = config_file.stem.replace('bridge_domain_', '').replace('unified_bridge_domain_', '')
        
        # Extract VLAN ID
        vlan_id = None
        if '_v' in service_name:
            try:
                vlan_part = service_name.split('_v')[1].split('_')[0]
                vlan_id = int(vlan_part)
            except:
                pass
        
        return {
            "name": service_name,
            "path": str(config_file),
            "type": "unified" if "unified" in config_file.name else "standard",
            "status": status,
            "vlan_id": vlan_id,
            "created": datetime.fromtimestamp(config_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            "size": config_file.stat().st_size
        }
    
    def connect_to_device(self, device_name: str) -> Optional[SSHConnection]:
        """Connect to device with simple connection management"""
        if device_name in self.connection_pool:
            # Reuse existing connection
            return self.connection_pool[device_name]
        
        device_info = self.devices.get('devices', {}).get(device_name)
        if not device_info:
            print(f"❌ Device {device_name} not found in devices.yaml")
            return None
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=device_info['ip'],
                username=device_info['username'],
                password=device_info['password'],
                timeout=30
            )
            
            connection = SSHConnection(
                client=client,
                hostname=device_info['ip'],
                connected_at=datetime.now()
            )
            
            self.connection_pool[device_name] = connection
            return connection
            
        except Exception as e:
            print(f"❌ Failed to connect to {device_name}: {e}")
            return None
    
    def execute_commands(self, device_name: str, commands: List[str]) -> DeploymentResult:
        """Execute commands on device"""
        start_time = time.time()
        
        connection = self.connect_to_device(device_name)
        if not connection:
            return DeploymentResult(
                success=False,
                message=f"Failed to connect to {device_name}",
                commands_executed=[],
                execution_time=0,
                error_details="Connection failed"
            )
        
        try:
            executed_commands = []
            
            for command in commands:
                stdin, stdout, stderr = connection.client.exec_command(command)
                
                # Wait for command completion
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode()
                    return DeploymentResult(
                        success=False,
                        message=f"Command failed: {command}",
                        commands_executed=executed_commands,
                        execution_time=time.time() - start_time,
                        error_details=error_output
                    )
                
                executed_commands.append(command)
            
            return DeploymentResult(
                success=True,
                message=f"Successfully executed {len(commands)} commands",
                commands_executed=executed_commands,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return DeploymentResult(
                success=False,
                message=f"Execution failed: {str(e)}",
                commands_executed=[],
                execution_time=time.time() - start_time,
                error_details=str(e)
            )
    
    def deploy_configuration(self, config_name: str) -> Dict[str, Any]:
        """Deploy configuration to target devices"""
        print(f"🚀 Deploying configuration: {config_name}")
        
        # Find configuration file
        config_file = None
        for config in self.get_available_configurations():
            if config['name'] == config_name:
                config_file = Path(config['path'])
                break
        
        if not config_file or not config_file.exists():
            return {
                'success': False,
                'message': f"Configuration {config_name} not found",
                'deployments': []
            }
        
        # Read configuration file
        try:
            with open(config_file, 'r') as f:
                config_content = f.read()
        except Exception as e:
            return {
                'success': False,
                'message': f"Failed to read configuration: {e}",
                'deployments': []
            }
        
        # Parse configuration and extract commands by device
        device_commands = self._parse_config_content(config_content)
        
        # Deploy to each device
        deployment_results = []
        overall_success = True
        
        for device_name, commands in device_commands.items():
            result = self.execute_commands(device_name, commands)
            deployment_results.append({
                'device': device_name,
                'success': result.success,
                'message': result.message,
                'commands_count': len(result.commands_executed),
                'execution_time': result.execution_time
            })
            
            if not result.success:
                overall_success = False
        
        return {
            'success': overall_success,
            'message': f"Deployment {'completed' if overall_success else 'failed'}",
            'deployments': deployment_results,
            'config_file': str(config_file)
        }
    
    def _parse_config_content(self, content: str) -> Dict[str, List[str]]:
        """Parse configuration content and extract commands by device"""
        device_commands = {}
        current_device = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check for device section header
            if line.startswith('=== ') and line.endswith(' ==='):
                current_device = line.replace('=== ', '').replace(' ===', '')
                device_commands[current_device] = []
            elif current_device and not line.startswith('#'):
                # Add command to current device
                device_commands[current_device].append(line)
        
        return device_commands
    
    def close_connections(self):
        """Close all SSH connections"""
        for device_name, connection in self.connection_pool.items():
            try:
                connection.client.close()
            except:
                pass
        
        self.connection_pool.clear()

# Factory function for backward compatibility
def create_ssh_manager() -> SimplifiedSSHManager:
    """Create simplified SSH manager instance"""
    return SimplifiedSSHManager()
