#!/usr/bin/env python3
"""
Simple Interface Discovery Engine

Simplified interface discovery using only 'show interface' command.
Focused on CLI integration with main.py BD editor.
"""

import sqlite3
import yaml
import json
import logging
import time
import concurrent.futures
import threading
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .data_models import InterfaceDiscoveryData, DeviceDiscoveryResult

logger = logging.getLogger(__name__)


class SimpleInterfaceDiscovery:
    """Simplified interface discovery for CLI integration"""
    
    def __init__(self, db_path: str = 'instance/lab_automation.db'):
        self.db_path = db_path
        self.devices_yaml_path = Path('devices.yaml')
    
    def get_available_interfaces_for_device(self, device_name: str) -> List[str]:
        """Get cached interface list for CLI integration"""
        try:
            interfaces = self._get_cached_interfaces(device_name)
            available = [
                intf.interface_name 
                for intf in interfaces 
                if intf.is_available_for_use()
            ]
            return available
        except Exception as e:
            logger.error(f"Error getting interfaces for {device_name}: {e}")
            return []
    
    def get_devices_with_interface_counts(self) -> Dict[str, int]:
        """Get devices with their interface counts for CLI display"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT device_name, COUNT(*) as count
                FROM interface_discovery 
                WHERE admin_status != 'admin-down'
                GROUP BY device_name
                ORDER BY device_name
            """)
            
            results = dict(cursor.fetchall())
            conn.close()
            
            return results
        except Exception as e:
            logger.error(f"Error getting device interface counts: {e}")
            return {}
    
    def _get_cached_interfaces(self, device_name: str) -> List[InterfaceDiscoveryData]:
        """Get cached interfaces for a device"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM interface_discovery 
                WHERE device_name = ? 
                ORDER BY interface_name
            """, (device_name,))
            
            rows = cursor.fetchall()
            conn.close()
            
            interfaces = []
            for row in rows:
                interface_data = InterfaceDiscoveryData.from_dict(dict(row))
                interfaces.append(interface_data)
            
            return interfaces
        except Exception as e:
            logger.error(f"Error getting cached interfaces for {device_name}: {e}")
            return []
    
    def discover_device_interfaces(self, device_name: str, store_raw_data: bool = True):
        """Discover interfaces for a single device using 'show interface' command"""
        logger.info(f"🔍 Starting interface discovery for {device_name}")
        
        try:
            # Execute 'show interface | no-more' command via SSH to prevent truncation
            raw_output = self._execute_ssh_command(device_name, "show interface | no-more")
            
            if not raw_output or not raw_output.strip():
                return DeviceDiscoveryResult(
                    device_name=device_name,
                    interfaces=[],
                    success=False,
                    error_message="No output received from device"
                )
            
            # Parse output using DRIVENETS parser
            from .description_parser import InterfaceDescriptionParser
            parser = InterfaceDescriptionParser()
            interfaces = parser.parse_interface_descriptions(raw_output, device_name)
            
            # Store in database with debug information
            if interfaces:
                self._store_interfaces_with_debug(interfaces, raw_output, "drivenets")
                logger.info(f"✅ Discovered {len(interfaces)} interfaces on {device_name}")
                
                # Also store in raw data table for debugging
                if store_raw_data:
                    self._store_raw_discovery_data(
                        device_name, "show interface | no-more", raw_output, 
                        True, 0, []
                    )
            else:
                logger.warning(f"No interfaces parsed from output for {device_name}")
                
                # Store failed parsing for debugging
                if store_raw_data:
                    self._store_raw_discovery_data(
                        device_name, "show interface | no-more", raw_output, 
                        False, 0, ["No interfaces parsed"]
                    )
            
            return DeviceDiscoveryResult(
                device_name=device_name,
                interfaces=interfaces,
                success=True if interfaces else False,
                error_message="No interfaces parsed" if not interfaces else None
            )
            
        except Exception as e:
            logger.error(f"❌ Discovery failed for {device_name}: {e}")
            return DeviceDiscoveryResult(
                device_name=device_name,
                interfaces=[],
                success=False,
                error_message=str(e)
            )
    
    def _execute_ssh_command(self, device_name: str, command: str) -> str:
        """Execute SSH command using interactive shell"""
        try:
            import yaml
            import paramiko
            import time
            
            # Load device info
            with open('devices.yaml', 'r') as f:
                devices_data = yaml.safe_load(f)
            
            device_info = devices_data.get(device_name)
            if not device_info:
                raise Exception(f"Device {device_name} not found in devices.yaml")
            
            defaults = devices_data.get('defaults', {})
            hostname = device_info.get('mgmt_ip')
            username = device_info.get('username', defaults.get('username'))
            password = device_info.get('password', defaults.get('password'))
            
            if not all([hostname, username, password]):
                raise Exception(f"Incomplete connection info for {device_name}")
            
            # Connect using interactive shell
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=hostname, username=username, password=password, timeout=30)
            
            shell = client.invoke_shell()
            time.sleep(2)  # Wait for prompt
            
            # Send command
            shell.send(command + '\n')
            time.sleep(3)  # Wait for command execution
            
            # Read output with multiple attempts to get complete data
            output = ""
            attempts = 0
            max_attempts = 5
            
            while attempts < max_attempts:
                if shell.recv_ready():
                    chunk = shell.recv(8192).decode('utf-8')
                    output += chunk
                    
                    # If we got data, wait a bit more for additional data
                    if chunk:
                        time.sleep(1)
                        attempts = 0  # Reset attempts if we're still getting data
                    else:
                        attempts += 1
                else:
                    attempts += 1
                    time.sleep(0.5)  # Wait before next attempt
            
            shell.close()
            client.close()
            
            return output
            
        except Exception as e:
            logger.error(f"SSH execution failed for {device_name}: {e}")
            raise
    
    def _store_interfaces(self, interfaces: List[InterfaceDiscoveryData]):
        """Store interface data in database"""
        if not interfaces:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for interface in interfaces:
                cursor.execute("""
                    INSERT OR REPLACE INTO interface_discovery (
                        device_name, interface_name, interface_type, description,
                        admin_status, oper_status, bundle_id, is_bundle_member,
                        discovered_at, device_reachable, discovery_errors
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    interface.device_name,
                    interface.interface_name,
                    interface.interface_type,
                    interface.description,
                    interface.admin_status,
                    interface.oper_status,
                    interface.bundle_id,
                    interface.is_bundle_member,
                    interface.discovered_at.isoformat(),
                    interface.device_reachable,
                    '[]'
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing interfaces: {e}")
    
    def _store_interfaces_with_debug(self, interfaces: List[InterfaceDiscoveryData], raw_output: str, parsing_method: str):
        """Store interface data with debug information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for interface in interfaces:
                cursor.execute("""
                    INSERT OR REPLACE INTO interface_discovery (
                        device_name, interface_name, interface_type, description,
                        admin_status, oper_status, bundle_id, is_bundle_member,
                        discovered_at, device_reachable, discovery_errors,
                        raw_command_output, parsing_method, parsing_errors
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    interface.device_name,
                    interface.interface_name,
                    interface.interface_type,
                    interface.description,
                    interface.admin_status,
                    interface.oper_status,
                    interface.bundle_id,
                    interface.is_bundle_member,
                    interface.discovered_at.isoformat(),
                    interface.device_reachable,
                    '[]',
                    raw_output,  # Store raw output for debugging
                    parsing_method,
                    '[]'
                ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Stored {len(interfaces)} interfaces with debug data")
            
        except Exception as e:
            logger.error(f"Error storing interfaces with debug: {e}")
    
    def _store_raw_discovery_data(self, device_name: str, command: str, raw_output: str, 
                                 success: bool, execution_time: int, errors: List[str]):
        """Store raw discovery data for debugging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO discovery_raw_data (
                    device_name, command_executed, raw_output, command_success,
                    execution_time_ms, ssh_errors, discovered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                device_name,
                command,
                raw_output,
                success,
                execution_time,
                json.dumps(errors),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Stored raw discovery data for {device_name}")
            
        except Exception as e:
            logger.error(f"Error storing raw discovery data: {e}")
    
    def discover_all_devices_parallel(self, max_workers: int = 10) -> Dict[str, DeviceDiscoveryResult]:
        """
        Discover interfaces on all devices in parallel for speed.
        
        Args:
            max_workers: Maximum number of parallel SSH connections
            
        Returns:
            Dictionary mapping device names to discovery results
        """
        logger.info("🔄 Starting parallel discovery for all devices")
        
        devices = self._load_devices_from_yaml()
        if not devices:
            logger.warning("No valid devices found in devices.yaml")
            return {}
        
        print(f"🚀 Starting PARALLEL discovery on {len(devices)} devices...")
        print(f"💡 Using {max_workers} parallel connections for speed")
        print("🔍 This will be much faster than sequential discovery")
        
        results = {}
        successful_devices = 0
        total_interfaces = 0
        
        # Use ThreadPoolExecutor for parallel discovery
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all discovery tasks
            future_to_device = {
                executor.submit(self.discover_device_interfaces, device): device 
                for device in devices
            }
            
            # Process results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(future_to_device), 1):
                device_name = future_to_device[future]
                
                try:
                    result = future.result()
                    results[device_name] = result
                    
                    if result.success:
                        successful_devices += 1
                        total_interfaces += len(result.interfaces)
                        status = f"✅ {len(result.interfaces)} interfaces"
                    else:
                        status = f"❌ {result.error_message[:50]}..."
                    
                    print(f"  📡 [{i:2d}/{len(devices)}] {device_name}: {status}")
                    
                except Exception as e:
                    print(f"  📡 [{i:2d}/{len(devices)}] {device_name}: ❌ Exception: {str(e)[:50]}...")
                    results[device_name] = DeviceDiscoveryResult(
                        device_name=device_name,
                        interfaces=[],
                        success=False,
                        error_message=str(e)
                    )
        
        print(f"\n🎉 Parallel discovery complete:")
        print(f"   • {successful_devices}/{len(devices)} devices successful")
        print(f"   • {total_interfaces} total interfaces discovered")
        print(f"   • Completed in parallel using {max_workers} workers")
        
        return results
    
    def _load_devices_from_yaml(self) -> List[str]:
        """Load device names from devices.yaml"""
        try:
            if not self.devices_yaml_path.exists():
                return []
            
            with open(self.devices_yaml_path, 'r') as f:
                devices_data = yaml.safe_load(f)
            
            # Return devices with complete connection info
            valid_devices = []
            defaults = devices_data.get('defaults', {})
            
            for name, device_info in devices_data.items():
                if name == 'defaults' or not isinstance(device_info, dict):
                    continue
                
                hostname = device_info.get('mgmt_ip')
                username = device_info.get('username', defaults.get('username'))
                password = device_info.get('password', defaults.get('password'))
                
                if all([hostname, username, password]):
                    valid_devices.append(name)
            
            return valid_devices  # Return ALL devices with complete connection info
            
        except Exception as e:
            logger.error(f"Error loading devices.yaml: {e}")
            return []
