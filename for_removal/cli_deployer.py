#!/usr/bin/env python3
"""
CLI-based configuration deployer for DNOS devices
Uses SSH and CLI commands instead of NETCONF for configuration deployment
"""

import logging
from typing import Dict, List, Optional, Any
import sys
import os

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from utils.dnos_ssh import DNOSSSH

class CLIConfigDeployer:
    """CLI-based configuration deployer using SSH"""
    
    def __init__(self, devices_file: str = "devices.yaml", debug: bool = False):
        """
        Initialize CLI configuration deployer
        
        Args:
            devices_file: Path to devices configuration file
            debug: Enable debug logging
        """
        self.devices_file = devices_file
        self.logger = logging.getLogger('CLIConfigDeployer')
        
        if debug:
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        
        self.devices = self._load_devices()
    
    def _load_devices(self) -> Dict[str, Any]:
        """Load device configuration from YAML file"""
        try:
            import yaml
            with open(self.devices_file, 'r') as f:
                devices = yaml.safe_load(f)
            self.logger.info(f"Loaded {len(devices.get('devices', {}))} devices from {self.devices_file}")
            return devices.get('devices', {})
        except Exception as e:
            self.logger.error(f"Failed to load devices from {self.devices_file}: {e}")
            return {}
    
    def deploy_configuration(self, device_name: str, config_commands: List[str], 
                           dry_run: bool = False) -> Dict[str, Any]:
        """
        Deploy configuration to a single device
        
        Args:
            device_name: Name of the device
            config_commands: List of configuration commands to deploy
            dry_run: If True, don't actually deploy, just validate
            
        Returns:
            Dict containing deployment results
        """
        if device_name not in self.devices:
            return {
                'success': False,
                'error': f'Device {device_name} not found in devices configuration'
            }
        
        device_config = self.devices[device_name]
        self.logger.info(f"Deploying configuration to {device_name} ({device_config['mgmt_ip']})")
        
        if dry_run:
            self.logger.info(f"DRY RUN: Would deploy {len(config_commands)} commands to {device_name}")
            return {
                'success': True,
                'device': device_name,
                'commands_count': len(config_commands),
                'dry_run': True
            }
        
        # Create SSH connection
        ssh = DNOSSSH(
            hostname=device_config['mgmt_ip'],
            username=device_config['username'],
            password=device_config['password'],
            port=device_config.get('ssh_port', 22),
            debug=False
        )
        
        result = {
            'success': False,
            'device': device_name,
            'commands_count': len(config_commands),
            'error': None
        }
        
        try:
            if not ssh.connect():
                result['error'] = f"Failed to connect to {device_name}"
                return result
            
            # Deploy configuration using the DNOS SSH module
            success = ssh.configure(config_commands, commit=True)
            
            if success:
                result['success'] = True
                self.logger.info(f"Successfully deployed configuration to {device_name}")
            else:
                result['error'] = f"Configuration deployment failed for {device_name}"
                self.logger.error(f"Configuration deployment failed for {device_name}")
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Exception during configuration deployment to {device_name}: {e}")
        
        finally:
            ssh.disconnect()
        
        return result
    
    def deploy_service_configuration(self, service_config: Dict[str, Any], 
                                   dry_run: bool = False) -> Dict[str, Any]:
        """
        Deploy service configuration across multiple devices
        
        Args:
            service_config: Service configuration dictionary
            dry_run: If True, don't actually deploy, just validate
            
        Returns:
            Dict containing deployment results for all devices
        """
        self.logger.info(f"Deploying service configuration (dry_run={dry_run})")
        
        results = {
            'success': True,
            'devices': {},
            'summary': {
                'total_devices': 0,
                'successful': 0,
                'failed': 0
            }
        }
        
        # Extract device-specific configurations
        device_configs = service_config.get('devices', {})
        
        for device_name, device_commands in device_configs.items():
            results['summary']['total_devices'] += 1
            
            try:
                device_result = self.deploy_configuration(
                    device_name, 
                    device_commands, 
                    dry_run=dry_run
                )
                results['devices'][device_name] = device_result
                
                if device_result['success']:
                    results['summary']['successful'] += 1
                else:
                    results['summary']['failed'] += 1
                    results['success'] = False
                    
            except Exception as e:
                results['devices'][device_name] = {
                    'success': False,
                    'error': str(e)
                }
                results['summary']['failed'] += 1
                results['success'] = False
        
        self.logger.info(f"Service deployment completed: {results['summary']['successful']} successful, {results['summary']['failed']} failed")
        return results
    
    def validate_configuration(self, device_name: str, expected_config: List[str]) -> Dict[str, Any]:
        """
        Validate configuration on a device
        
        Args:
            device_name: Name of the device
            expected_config: List of expected configuration commands
            
        Returns:
            Dict containing validation results
        """
        if device_name not in self.devices:
            return {
                'success': False,
                'error': f'Device {device_name} not found in devices configuration'
            }
        
        device_config = self.devices[device_name]
        self.logger.info(f"Validating configuration on {device_name}")
        
        # Create SSH connection
        ssh = DNOSSSH(
            hostname=device_config['mgmt_ip'],
            username=device_config['username'],
            password=device_config['password'],
            port=device_config.get('ssh_port', 22),
            debug=False
        )
        
        result = {
            'success': False,
            'device': device_name,
            'validation_results': [],
            'error': None
        }
        
        try:
            if not ssh.connect():
                result['error'] = f"Failed to connect to {device_name}"
                return result
            
            # Get current configuration
            current_config = ssh.get_configuration()
            
            if current_config:
                # Simple validation - check if expected commands are present
                validation_results = []
                for expected_cmd in expected_config:
                    is_present = expected_cmd in current_config
                    validation_results.append({
                        'command': expected_cmd,
                        'present': is_present
                    })
                
                result['validation_results'] = validation_results
                result['success'] = all(r['present'] for r in validation_results)
                
                if result['success']:
                    self.logger.info(f"Configuration validation passed for {device_name}")
                else:
                    self.logger.warning(f"Configuration validation failed for {device_name}")
            else:
                result['error'] = f"Failed to retrieve configuration from {device_name}"
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Exception during configuration validation on {device_name}: {e}")
        
        finally:
            ssh.disconnect()
        
        return result

# Example usage
if __name__ == "__main__":
    # Example configuration deployment
    deployer = CLIConfigDeployer(debug=True)
    
    # Example service configuration
    service_config = {
        'devices': {
            'leaf_b15': [
                'set interfaces ge100-0/0/1 description "Test Interface"',
                'set vlans test-vlan vlan-id 100'
            ],
            'leaf_b14': [
                'set interfaces ge100-0/0/1 description "Test Interface"',
                'set vlans test-vlan vlan-id 100'
            ]
        }
    }
    
    # Deploy configuration
    results = deployer.deploy_service_configuration(service_config, dry_run=True)
    print(f"Deployment results: {results}") 