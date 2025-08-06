#!/usr/bin/env python3
"""
Device Scanner - Discovers existing bridge domains on network devices
and converts them to configuration records for the database.
"""

import paramiko
import yaml
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceScanner:
    def __init__(self, devices_file: str = "devices.yaml"):
        self.devices_file = Path(devices_file)
        self.db_manager = DatabaseManager(str(Path(__file__).parent.parent / "instance" / "lab_automation.db"))
        self.devices = self._load_devices()
    
    def _load_devices(self) -> Dict:
        """Load device information from devices.yaml"""
        try:
            with open(self.devices_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load devices file: {e}")
            return {}
    
    def _connect_to_device(self, device_info: Dict) -> Optional[paramiko.SSHClient]:
        """Establish SSH connection to a device"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Get device connection info, merging with defaults
            defaults = self.devices.get('defaults', {})
            hostname = device_info.get('mgmt_ip') or device_info.get('hostname')
            username = device_info.get('username') or defaults.get('username')
            password = device_info.get('password') or defaults.get('password')
            port = device_info.get('ssh_port') or device_info.get('port') or defaults.get('ssh_port', 22)
            
            if not hostname:
                logger.error(f"No hostname/mgmt_ip found for device")
                return None
            
            ssh.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                key_filename=device_info.get('key_file'),
                timeout=30
            )
            return ssh
        except Exception as e:
            logger.error(f"Failed to connect to {device_info.get('mgmt_ip', 'unknown')}: {e}")
            return None
    
    def _execute_command(self, ssh: paramiko.SSHClient, command: str) -> Tuple[bool, str]:
        """Execute a command on the device and return the output"""
        try:
            # Use interactive shell like the verification function
            shell = ssh.invoke_shell()
            shell.settimeout(10)
            output = ''
            
            # Wait for initial prompt
            import time
            time.sleep(1)
            try:
                initial_output = shell.recv(4096).decode(errors='ignore')
                output += initial_output
            except Exception as e:
                logger.warning(f"Timeout getting initial output: {e}")
            
            # Send command
            shell.send(command + '\n')
            time.sleep(2)
            
            # Read response and handle pager
            while True:
                try:
                    response = shell.recv(4096).decode(errors='ignore')
                    output += response
                    
                    # Check for "More" prompt and send 'q' to quit
                    if '-- More --' in response or 'Press q to quit' in response:
                        shell.send('q\n')
                        time.sleep(1)
                        try:
                            final_response = shell.recv(4096).decode(errors='ignore')
                            output += final_response
                        except:
                            pass
                        break
                    
                    # If no more data, break
                    if not response:
                        break
                        
                except Exception as e:
                    logger.warning(f"Timeout getting response: {e}")
                    break
            
            shell.close()
            
            return True, output
        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {e}")
            return False, str(e)
    
    def _parse_bridge_domains(self, output: str) -> List[Dict]:
        """Parse bridge domain information from device output"""
        bridge_domains = []
        
        # Handle table format output from DNOS devices
        # Example output:
        # | Name                           |
        # |--------------------------------|
        # | g_visaev-Newest_v290           |
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            # Skip header lines and separators
            if line.startswith('|') and 'Name' not in line and '---' not in line:
                # Extract bridge domain name from table format
                # Format: | g_visaev-Newest_v290           |
                parts = line.split('|')
                if len(parts) >= 2:
                    service_name = parts[1].strip()
                    if service_name and service_name != 'Name':
                        bridge_domains.append({
                            'service_name': service_name,
                            'raw_output': line.strip()
                        })
        
        # Also try the old pattern as fallback
        if not bridge_domains:
            pattern = r'network-services bridge-domain instance (\S+)'
            for line in lines:
                match = re.search(pattern, line.strip())
                if match:
                    service_name = match.group(1)
                    bridge_domains.append({
                        'service_name': service_name,
                        'raw_output': line.strip()
                    })
        
        return bridge_domains
    
    def _get_bridge_domain_details(self, ssh: paramiko.SSHClient, service_name: str) -> Dict:
        """Get detailed information about a specific bridge domain"""
        details = {
            'service_name': service_name,
            'interfaces': [],
            'vlan_id': None,
            'commands': []
        }
        
        # Get the full configuration for this bridge domain
        command = f"show network-services bridge-domain {service_name}"
        success, output = self._execute_command(ssh, command)
        
        if not success:
            return details
        
        # Parse VLAN ID
        vlan_match = re.search(r'vlan-id\s+(\d+)', output)
        if vlan_match:
            details['vlan_id'] = int(vlan_match.group(1))
        
        # Parse interfaces
        interface_pattern = r'interface\s+(\S+)'
        interfaces = re.findall(interface_pattern, output)
        details['interfaces'] = interfaces
        
        # Generate CLI commands to recreate this configuration
        commands = []
        commands.append(f"network-services bridge-domain instance {service_name}")
        
        for interface in interfaces:
            commands.append(f"network-services bridge-domain instance {service_name} interface {interface}")
            commands.append(f"interfaces {interface} l2-service enabled")
            if details['vlan_id']:
                commands.append(f"interfaces {interface} vlan-id {details['vlan_id']}")
        
        details['commands'] = commands
        
        return details
    
    def scan_device(self, device_name: str, quick_scan: bool = False) -> List[Dict]:
        """Scan a single device for bridge domains"""
        if device_name not in self.devices:
            logger.error(f"Device '{device_name}' not found in devices.yaml")
            return []
        
        device_info = self.devices[device_name]
        ssh = self._connect_to_device(device_info)
        
        if not ssh:
            return []
        
        try:
            # Get all bridge domain instances
            command = "show network-services bridge-domain | no-more"
            success, output = self._execute_command(ssh, command)
            
            if not success:
                logger.error(f"Failed to get bridge domains from {device_name}")
                return []
            
            # Debug: Print the raw output
            logger.info(f"Raw output from {device_name}:")
            logger.info(f"Output length: {len(output)}")
            logger.info(f"Output: {repr(output)}")
            
            bridge_domains = self._parse_bridge_domains(output)
            logger.info(f"Parsed {len(bridge_domains)} bridge domains from {device_name}")
            
            if quick_scan:
                # Return basic info without detailed scanning
                for domain in bridge_domains:
                    domain['device'] = device_name
                return bridge_domains
            
            detailed_domains = []
            
            # Get detailed information for each bridge domain
            for domain in bridge_domains:
                details = self._get_bridge_domain_details(ssh, domain['service_name'])
                details['device'] = device_name
                detailed_domains.append(details)
            
            return detailed_domains
            
        finally:
            ssh.close()
    
    def scan_all_devices(self) -> Dict[str, List[Dict]]:
        """Scan all devices for bridge domains in parallel"""
        results = {}
        
        # Get list of devices to scan (excluding defaults)
        devices_to_scan = [name for name in self.devices.keys() if name != 'defaults']
        
        logger.info(f"Starting parallel scan of {len(devices_to_scan)} devices...")
        
        # Use ThreadPoolExecutor for parallel scanning
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all scan tasks
            future_to_device = {
                executor.submit(self.scan_device, device_name): device_name 
                for device_name in devices_to_scan
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_device):
                device_name = future_to_device[future]
                try:
                    domains = future.result()
                    if domains:
                        results[device_name] = domains
                        logger.info(f"✅ Completed scan of {device_name}: found {len(domains)} bridge domains")
                    else:
                        logger.info(f"ℹ️  Completed scan of {device_name}: no bridge domains found")
                except Exception as e:
                    logger.error(f"❌ Failed to scan {device_name}: {e}")
        
        logger.info(f"Parallel scan completed. Found bridge domains on {len(results)} devices")
        return results
    
    def consolidate_bridge_domains(self, scan_results: Dict[str, List[Dict]]) -> List[Dict]:
        """Consolidate bridge domains across devices into unique configurations"""
        domain_map = {}
        
        for device_name, domains in scan_results.items():
            for domain in domains:
                service_name = domain['service_name']
                
                if service_name not in domain_map:
                    domain_map[service_name] = {
                        'service_name': service_name,
                        'vlan_id': domain['vlan_id'],
                        'devices': [],
                        'commands': domain['commands'],
                        'config_data': {}
                    }
                
                # Add device-specific commands
                device_commands = []
                for cmd in domain['commands']:
                    if 'interface' in cmd and not cmd.startswith('network-services'):
                        device_commands.append(cmd)
                
                domain_map[service_name]['devices'].append(device_name)
                domain_map[service_name]['config_data'][device_name] = device_commands
        
        return list(domain_map.values())
    
    def create_configuration_record(self, consolidated_domain: Dict, user_id: int = 1) -> bool:
        """Create a configuration record in the database"""
        try:
            # Check if configuration already exists
            existing = self.db_manager.get_configuration_by_service_name(consolidated_domain['service_name'])
            if existing:
                logger.info(f"Configuration {consolidated_domain['service_name']} already exists in database")
                return True
            
            # Create new configuration record
            config_data = {
                'service_name': consolidated_domain['service_name'],
                'vlan_id': consolidated_domain['vlan_id'],
                'devices': consolidated_domain['devices'],
                'commands': consolidated_domain['commands'],
                'config_data': consolidated_domain['config_data']
            }
            
            # Save to database as 'deployed' status
            success = self.db_manager.save_configuration(
                user_id=user_id,
                service_name=consolidated_domain['service_name'],
                vlan_id=consolidated_domain['vlan_id'],
                config_type='bridge_domain',
                config_data=json.dumps(config_data),
                status='deployed'
            )
            
            if success:
                logger.info(f"Created configuration record for {consolidated_domain['service_name']}")
                return True
            else:
                logger.error(f"Failed to create configuration record for {consolidated_domain['service_name']}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating configuration record: {e}")
            return False
    
    def scan_and_sync(self, user_id: int = 1) -> Dict:
        """Main method to scan devices and sync configurations to database"""
        logger.info("Starting device scan and sync...")
        
        # Scan all devices
        scan_results = self.scan_all_devices()
        
        if not scan_results:
            logger.warning("No devices found or no bridge domains discovered")
            return {'success': False, 'message': 'No devices found or no bridge domains discovered'}
        
        # Consolidate results
        consolidated_domains = self.consolidate_bridge_domains(scan_results)
        
        if not consolidated_domains:
            logger.warning("No bridge domains found on any devices")
            return {'success': False, 'message': 'No bridge domains found on any devices'}
        
        # Create configuration records
        created_count = 0
        for domain in consolidated_domains:
            if self.create_configuration_record(domain, user_id):
                created_count += 1
        
        logger.info(f"Scan and sync completed. Created {created_count} configuration records.")
        
        return {
            'success': True,
            'message': f'Successfully synced {created_count} configurations from devices',
            'scanned_devices': list(scan_results.keys()),
            'found_domains': len(consolidated_domains),
            'created_configs': created_count,
            'configurations': consolidated_domains
        }

def main():
    """Command line interface for device scanning"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan network devices for bridge domains')
    parser.add_argument('--device', help='Scan specific device only')
    parser.add_argument('--user-id', type=int, default=1, help='User ID for database records')
    parser.add_argument('--sync', action='store_true', help='Sync discovered configurations to database')
    parser.add_argument('--quick-scan', action='store_true', help='Quick scan (no detailed info)')
    
    args = parser.parse_args()
    
    scanner = DeviceScanner()
    
    if args.device:
        # Scan single device
        results = scanner.scan_device(args.device, quick_scan=args.quick_scan)
        print(f"Found {len(results)} bridge domains on {args.device}:")
        for domain in results:
            print(f"  - {domain['service_name']} (VLAN {domain.get('vlan_id', 'unknown')})")
    else:
        # Scan all devices
        if args.sync:
            result = scanner.scan_and_sync(args.user_id)
            print(f"Scan and sync result: {result}")
        else:
            results = scanner.scan_all_devices()
            print(f"Scan results:")
            for device, domains in results.items():
                print(f"  {device}: {len(domains)} bridge domains")
                for domain in domains:
                    print(f"    - {domain['service_name']} (VLAN {domain.get('vlan_id', 'unknown')})")

if __name__ == "__main__":
    main() 