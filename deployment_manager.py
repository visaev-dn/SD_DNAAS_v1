#!/usr/bin/env python3
"""
Enhanced Deployment Manager
Provides real-time deployment progress and detailed feedback to users
"""

import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

class DeploymentManager:
    """Manages deployment operations with real-time progress reporting"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_deployments = {}  # deployment_id -> deployment_info
        self.logger = logger
    
    def start_deployment(self, deployment_id: str, config_id: int, config_data: Dict, 
                        user_id: int, progress_callback: Optional[Callable] = None) -> bool:
        """Start a new deployment"""
        try:
            # Initialize deployment info
            deployment_info = {
                'deployment_id': deployment_id,
                'config_id': config_id,
                'user_id': user_id,
                'status': 'starting',
                'stage': 'initializing',
                'progress': 0,
                'logs': [],
                'errors': [],
                'device_results': {},
                'start_time': datetime.utcnow().isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.active_deployments[deployment_id] = deployment_info
            
            # Start deployment in background thread
            import threading
            deployment_thread = threading.Thread(
                target=self._deploy_worker,
                args=(deployment_id, config_data, progress_callback)
            )
            deployment_thread.daemon = True
            deployment_thread.start()
            
            self.logger.info(f"Started deployment {deployment_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start deployment {deployment_id}: {e}")
            return False

    def start_removal(self, removal_id: str, config_id: int, config_data: Dict, 
                     user_id: int, progress_callback: Optional[Callable] = None) -> bool:
        """Start a new removal operation"""
        try:
            # Initialize removal info
            removal_info = {
                'removal_id': removal_id,
                'config_id': config_id,
                'user_id': user_id,
                'status': 'starting',
                'stage': 'initializing',
                'progress': 0,
                'logs': [],
                'errors': [],
                'device_results': {},
                'start_time': datetime.utcnow().isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.active_deployments[removal_id] = removal_info
            
            # Debug logging
            self.logger.info(f"🔍 Added removal {removal_id} to active_deployments")
            self.logger.info(f"🔍 Active deployments after adding: {list(self.active_deployments.keys())}")
            
            # Start removal in background thread
            import threading
            removal_thread = threading.Thread(
                target=self._removal_worker,
                args=(removal_id, config_data, progress_callback)
            )
            removal_thread.daemon = True
            removal_thread.start()
            
            self.logger.info(f"Started removal {removal_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start removal {removal_id}: {e}")
            return False

    def _deploy_worker(self, deployment_id: str, config_data: Dict, 
                      progress_callback: Optional[Callable] = None):
        """Background worker for deployment execution"""
        try:
            deployment_info = self.active_deployments[deployment_id]
            config_id = deployment_info['config_id']
            user_id = deployment_info['user_id']
            
            # Update status to running
            deployment_info['status'] = 'running'
            deployment_info['stage'] = 'initializing'
            deployment_info['progress'] = 10
            self._emit_progress(deployment_id, deployment_info)
            
            self._log_deployment(deployment_id, "🚀 Starting configuration deployment...")
            
            # Import SSH push manager
            from config_engine.ssh_push_manager import SSHPushManager
            ssh_push = SSHPushManager()
            
            # Get service name from config_data
            service_name = None
            if '_metadata' in config_data and 'service_name' in config_data['_metadata']:
                service_name = config_data['_metadata']['service_name']
            else:
                # Try to extract from device commands
                for device, commands in config_data.items():
                    if device != '_metadata' and commands:
                        # Look for service name in commands
                        for cmd in commands:
                            if 'bridge-domain instance' in cmd:
                                parts = cmd.split()
                                for i, part in enumerate(parts):
                                    if part == 'instance' and i + 1 < len(parts):
                                        service_name = parts[i + 1]
                                        break
                                if service_name:
                                    break
                        if service_name:
                            break
            
            if not service_name:
                self._log_deployment(deployment_id, "❌ Could not determine service name from configuration")
                deployment_info['status'] = 'failed'
                deployment_info['errors'] = ['Could not determine service name from configuration']
                self._emit_progress(deployment_id, deployment_info)
                return
            
            # Prepare device commands (exclude _metadata)
            device_commands = {k: v for k, v in config_data.items() if k != '_metadata'}
            
            if not device_commands:
                self._log_deployment(deployment_id, "❌ No device commands found in configuration")
                deployment_info['status'] = 'failed'
                deployment_info['errors'] = ['No device commands found in configuration']
                self._emit_progress(deployment_id, deployment_info)
                return
            
            # Update status to validating
            deployment_info['status'] = 'running'
            deployment_info['stage'] = 'validating'
            deployment_info['progress'] = 20
            self._emit_progress(deployment_id, deployment_info)
            
            # Execute deployment with progress
            all_devices_already_exist = self._execute_deployment_with_progress(
                deployment_id, ssh_push, device_commands
            )
            
            # Stage 2: Commit (skip if all devices already existed)
            if all_devices_already_exist:
                deployment_info['stage'] = 'committing'
                deployment_info['progress'] = 70
                self._log_deployment(deployment_id, "✅ All devices already have configuration - skipping commit stage")
                self._emit_progress(deployment_id, deployment_info)
            else:
                deployment_info['stage'] = 'committing'
                deployment_info['progress'] = 70
                self._log_deployment(deployment_id, "🔄 Stage 2: Committing configuration on all devices...")
                self._emit_progress(deployment_id, deployment_info)
                
                commit_results = {}
                commit_errors = []
                
                # Filter out _metadata key - only process actual devices
                actual_devices = [d for d in device_commands.keys() if d != '_metadata']
                for i, device in enumerate(actual_devices):
                    device_progress = 70 + (i / len(actual_devices)) * 20  # 70-90%
                    deployment_info['progress'] = int(device_progress)
                    deployment_info['stage'] = f'committing_device_{device}'
                    self._log_deployment(deployment_id, f"🚀 Committing {device}...")
                    self._emit_progress(deployment_id, deployment_info)
                    
                    # Execute commit on device
                    device_info = ssh_push._load_device_info(device)
                    if not device_info:
                        error_msg = f"Missing SSH info for {device}"
                        commit_errors.append(error_msg)
                        self._log_deployment(deployment_id, f"❌ {error_msg}")
                        continue
                    
                    cli_commands = device_commands.get(device, [])
                    device_name, success, already_exists, error_message = ssh_push._execute_on_device_parallel(
                        device, device_info, cli_commands, None, "commit"
                    )
                    
                    commit_results[device] = (success, already_exists, error_message)
                    
                    if success:
                        self._log_deployment(deployment_id, f"✅ {device}: Configuration committed successfully")
                    else:
                        error_msg = f"Commit failed on {device}: {error_message}"
                        commit_errors.append(error_msg)
                        self._log_deployment(deployment_id, f"❌ {error_msg}")
                
                if commit_errors:
                    deployment_info['status'] = 'failed'
                    deployment_info['stage'] = 'commit_failed'
                    deployment_info['progress'] = 0
                    deployment_info['errors'] = commit_errors
                    self._log_deployment(deployment_id, f"❌ Commit failed: {commit_errors}")
                    self._emit_progress(deployment_id, deployment_info)
                    return
                
                self._log_deployment(deployment_id, "✅ All devices committed successfully")
            
            # Stage 3: Verification (skip if all devices already existed)
            if all_devices_already_exist:
                deployment_info['stage'] = 'verifying'
                deployment_info['progress'] = 90
                self._log_deployment(deployment_id, "🔍 Skipping verification - all configurations already existed")
                self._emit_progress(deployment_id, deployment_info)
                
                # Update database status to deployed since all devices already had the configuration
                self._update_configuration_status(config_id, 'deployed', user_id, deployment_id)
                
                # Skip verification since all devices already had the configuration
                deployment_info['progress'] = 100
                self._log_deployment(deployment_id, "✅ All devices already had configuration - verification skipped")
            else:
                deployment_info['stage'] = 'verifying'
                deployment_info['progress'] = 90
                self._log_deployment(deployment_id, "🔍 Verifying deployment...")
                self._emit_progress(deployment_id, deployment_info)
                
                # Verify deployment using the existing config_data
                verification_success = self._verify_deployment_with_config(
                    deployment_id, ssh_push, config_data
                )
                
                if not verification_success:
                    deployment_info['status'] = 'failed'
                    deployment_info['stage'] = 'verification_failed'
                    deployment_info['progress'] = 0
                    self._log_deployment(deployment_id, "❌ Deployment verification failed")
                    self._emit_progress(deployment_id, deployment_info)
                    return
            
            # Success
            deployment_info['status'] = 'completed'
            deployment_info['stage'] = 'completed'
            deployment_info['progress'] = 100
            deployment_info['end_time'] = datetime.utcnow().isoformat()
            
            # Update database status to deployed
            self._update_configuration_status(config_id, 'deployed', user_id, deployment_id)
            
            self._log_deployment(deployment_id, "🎉 Deployment completed successfully!")
            self._emit_progress(deployment_id, deployment_info)
            
        except Exception as e:
            self.logger.error(f"Deployment worker error: {e}")
            deployment_info = self.active_deployments.get(deployment_id)
            if deployment_info:
                deployment_info['status'] = 'failed'
                deployment_info['stage'] = 'failed'
                deployment_info['progress'] = 0
                deployment_info['errors'] = [f"Deployment error: {str(e)}"]
                self._log_deployment(deployment_id, f"❌ Deployment error: {e}")
                self._emit_progress(deployment_id, deployment_info)

    def _removal_worker(self, removal_id: str, config_data: Dict, 
                       progress_callback: Optional[Callable] = None):
        """Background worker for removal execution"""
        try:
            removal_info = self.active_deployments[removal_id]
            config_id = removal_info['config_id']
            user_id = removal_info['user_id']
            
            # Debug logging
            self.logger.info(f"🔍 Removal worker started for {removal_id}")
            self.logger.info(f"🔍 Active deployments in worker: {list(self.active_deployments.keys())}")
            
            # Update status to running
            removal_info['status'] = 'running'
            removal_info['stage'] = 'initializing'
            removal_info['progress'] = 10
            self._emit_progress(removal_id, removal_info)
            
            self._log_deployment(removal_id, "🗑️ Starting configuration removal...")
            
            # Import SSH push manager
            from config_engine.ssh_push_manager import SSHPushManager
            ssh_push = SSHPushManager()
            
            # Handle config_data - it might be a string that needs to be parsed
            if isinstance(config_data, str):
                try:
                    import json
                    config_data = json.loads(config_data)
                    self._log_deployment(removal_id, "📋 Parsed config_data from JSON string")
                except json.JSONDecodeError as e:
                    self._log_deployment(removal_id, f"❌ Failed to parse config_data: {e}")
                    removal_info['status'] = 'failed'
                    removal_info['errors'] = ['Invalid configuration data format']
                    self._emit_progress(removal_id, removal_info)
                    return
            
            # Update status to removing
            removal_info['status'] = 'running'
            removal_info['stage'] = 'removing'
            removal_info['progress'] = 30
            self._emit_progress(removal_id, removal_info)
            
            # Extract service name from config_data
            service_name = None
            if '_metadata' in config_data and 'service_name' in config_data['_metadata']:
                service_name = config_data['_metadata']['service_name']
            else:
                # Try to extract from device commands
                for device, commands in config_data.items():
                    if device != '_metadata' and commands:
                        # Look for service name in commands
                        for cmd in commands:
                            if 'bridge-domain instance' in cmd:
                                parts = cmd.split()
                                for i, part in enumerate(parts):
                                    if part == 'instance' and i + 1 < len(parts):
                                        service_name = parts[i + 1]
                                        break
                                if service_name:
                                    break
                        if service_name:
                            break
            
            if not service_name:
                self._log_deployment(removal_id, "❌ Could not determine service name from configuration")
                removal_info['status'] = 'failed'
                removal_info['errors'] = ['Could not determine service name from configuration']
                self._emit_progress(removal_id, removal_info)
                return
            
            # Create a progress callback that logs to our deployment system
            def progress_callback(message):
                self._log_deployment(removal_id, message)
                # Update progress based on message content
                if "Progress:" in message:
                    # Extract progress percentage from message
                    if "devices completed" in message:
                        try:
                            # Parse "Progress: X/Y devices completed"
                            parts = message.split("Progress: ")[1].split("/")
                            completed = int(parts[0])
                            total = int(parts[1].split(" ")[0])
                            progress = int((completed / total) * 100)
                            removal_info['progress'] = progress
                            self._emit_progress(removal_id, removal_info)
                        except:
                            pass
                elif "✅" in message or "❌" in message:
                    # Update progress for completion messages
                    removal_info['progress'] = min(removal_info['progress'] + 10, 100)
                    self._emit_progress(removal_id, removal_info)
            
            # Use the working removal logic from SSHPushManager
            success, errors = ssh_push.remove_config(service_name, dry_run=False, progress_callback=progress_callback)
            
            if not success:
                removal_info['status'] = 'failed'
                removal_info['stage'] = 'removal_failed'
                removal_info['progress'] = 0
                removal_info['errors'] = errors
                self._log_deployment(removal_id, "❌ Removal failed")
                self._emit_progress(removal_id, removal_info)
                return
            
            # Success
            removal_info['status'] = 'completed'
            removal_info['stage'] = 'completed'
            removal_info['progress'] = 100
            removal_info['end_time'] = datetime.utcnow().isoformat()
            
            # Update database status to deleted
            self._update_configuration_status(config_id, 'deleted', user_id, removal_id)
            
            self._log_deployment(removal_id, "🎉 Removal completed successfully!")
            self._emit_progress(removal_id, removal_info)
            
        except Exception as e:
            self.logger.error(f"Removal worker error: {e}")
            removal_info = self.active_deployments.get(removal_id)
            if removal_info:
                removal_info['status'] = 'failed'
                removal_info['stage'] = 'failed'
                removal_info['progress'] = 0
                removal_info['errors'] = [f"Removal error: {str(e)}"]
                self._log_deployment(removal_id, f"❌ Removal error: {e}")
                self._emit_progress(removal_id, removal_info)

    def _update_configuration_status(self, config_id: int, status: str, user_id: int, deployment_id: str):
        """Update configuration status in database"""
        try:
            import sqlite3
            import os
            
            # Get the database path
            db_path = os.path.join(os.path.dirname(__file__), 'instance', 'lab_automation.db')
            
            # Use direct SQLite connection to avoid Flask context issues
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Update the configuration status
            cursor.execute("""
                UPDATE configurations 
                SET status = ?, deployed_at = ?, deployed_by = ?
                WHERE id = ?
            """, (status, datetime.utcnow().isoformat(), user_id, config_id))
            
            conn.commit()
            conn.close()
            
            self._log_deployment(deployment_id, f"✅ Database status updated to '{status}'")
            
        except Exception as e:
            self._log_deployment(deployment_id, f"⚠️ Failed to update database status: {e}")
    
    def _execute_deployment_with_progress(self, deployment_id: str, ssh_push, 
                                        device_commands: Dict) -> tuple:
        """Execute deployment with detailed progress reporting"""
        try:
            deployment_info = self.active_deployments[deployment_id]
            # Filter out _metadata key - only process actual devices
            devices = [device for device in device_commands.keys() if device != '_metadata']
            total_devices = len(devices)
            
            self._log_deployment(deployment_id, f"📱 Deploying to {total_devices} devices...")
            
            # Stage 1: Commit-check (validation)
            deployment_info['stage'] = 'validating_devices'
            deployment_info['progress'] = 30
            self._log_deployment(deployment_id, "🔄 Stage 1: Running commit-check on all devices...")
            self._emit_progress(deployment_id, deployment_info)
            
            check_results = {}
            check_errors = []
            devices_already_exist = []
            
            for i, device in enumerate(devices):
                device_progress = 30 + (i / total_devices) * 20  # 30-50%
                deployment_info['progress'] = int(device_progress)
                deployment_info['stage'] = f'validating_device_{device}'
                self._log_deployment(deployment_id, f"🔍 Validating {device}...")
                self._emit_progress(deployment_id, deployment_info)
                
                # Execute commit-check on device
                device_info = ssh_push._load_device_info(device)
                if not device_info:
                    error_msg = f"Missing SSH info for {device}"
                    check_errors.append(error_msg)
                    self._log_deployment(deployment_id, f"❌ {error_msg}")
                    continue
                
                cli_commands = device_commands.get(device, [])
                if not cli_commands:
                    error_msg = f"No CLI commands for {device}"
                    check_errors.append(error_msg)
                    self._log_deployment(deployment_id, f"❌ {error_msg}")
                    continue
                
                # Execute commit-check
                device_name, success, already_exists, error_message = ssh_push._execute_on_device_parallel(
                    device, device_info, cli_commands, None, "check"
                )
                
                check_results[device] = (success, already_exists, error_message)
                
                # Debug logging for already_exists flag
                self._log_deployment(deployment_id, f"🔍 Debug: {device} - success={success}, already_exists={already_exists}")
                
                if success:
                    if already_exists:
                        devices_already_exist.append(device)
                        self._log_deployment(deployment_id, f"✅ {device}: Configuration already exists")
                    else:
                        self._log_deployment(deployment_id, f"✅ {device}: Commit-check passed")
                else:
                    error_msg = f"Commit-check failed on {device}: {error_message}"
                    check_errors.append(error_msg)
                    self._log_deployment(deployment_id, f"❌ {error_msg}")
            
            if check_errors:
                return False, check_errors, False
            
            # Check if all devices already exist
            all_devices_already_exist = len(devices_already_exist) == len(devices)
            
            # Debug logging
            self._log_deployment(deployment_id, f"🔍 Debug: {len(devices_already_exist)} devices already exist out of {len(devices)} total devices")
            self._log_deployment(deployment_id, f"🔍 Debug: Devices that already exist: {devices_already_exist}")
            self._log_deployment(deployment_id, f"🔍 Debug: all_devices_already_exist = {all_devices_already_exist}")
            
            # Stage 2: Commit (actual deployment) - only if not all devices already exist
            if all_devices_already_exist:
                self._log_deployment(deployment_id, "✅ All devices already have configuration - skipping commit stage")
                return True, [], True
            
            deployment_info['stage'] = 'committing_devices'
            deployment_info['progress'] = 50
            self._log_deployment(deployment_id, "🔄 Stage 2: Committing configuration on all devices...")
            self._emit_progress(deployment_id, deployment_info)
            
            commit_results = {}
            commit_errors = []
            
            for i, device in enumerate(devices):
                device_progress = 50 + (i / total_devices) * 30  # 50-80%
                deployment_info['progress'] = int(device_progress)
                deployment_info['stage'] = f'committing_device_{device}'
                self._log_deployment(deployment_id, f"🚀 Committing {device}...")
                self._emit_progress(deployment_id, deployment_info)
                
                # Execute commit on device
                device_info = ssh_push._load_device_info(device)
                cli_commands = device_commands.get(device, [])
                
                device_name, success, already_exists, error_message = ssh_push._execute_on_device_parallel(
                    device, device_info, cli_commands, None, "commit"
                )
                
                commit_results[device] = (success, already_exists, error_message)
                
                if success:
                    self._log_deployment(deployment_id, f"✅ {device}: Configuration committed successfully")
                else:
                    error_msg = f"Commit failed on {device}: {error_message}"
                    commit_errors.append(error_msg)
                    self._log_deployment(deployment_id, f"❌ {error_msg}")
            
            if commit_errors:
                return False, commit_errors, False
            
            deployment_info['progress'] = 80
            self._log_deployment(deployment_id, "✅ All devices committed successfully")
            self._emit_progress(deployment_id, deployment_info)
            
            return True, [], False
            
        except Exception as e:
            self.logger.error(f"Deployment execution error: {e}")
            return False, [str(e)], False
    
    def _execute_removal_with_progress(self, removal_id: str, ssh_push, 
                                     device_commands: Dict, service_name: str) -> bool:
        """Execute removal with detailed progress reporting"""
        try:
            removal_info = self.active_deployments[removal_id]
            devices = list(device_commands.keys())
            # Filter out _metadata key - only process actual devices
            devices = [device for device in device_commands.keys() if device != '_metadata']
            total_devices = len(devices)
            
            self._log_deployment(removal_id, f"🗑️ Removing from {total_devices} devices...")
            
            # Stage 1: Removal
            removal_info['stage'] = 'removing_devices'
            removal_info['progress'] = 30
            self._log_deployment(removal_id, "🔄 Stage 1: Removing configuration from all devices...")
            self._emit_progress(removal_id, removal_info)
            
            removal_results = {}
            removal_errors = []
            
            for i, device in enumerate(devices):
                device_progress = 30 + (i / total_devices) * 40  # 30-70%
                removal_info['progress'] = int(device_progress)
                removal_info['stage'] = f'removing_device_{device}'
                self._log_deployment(removal_id, f"🗑️ Removing from {device}...")
                self._emit_progress(removal_id, removal_info)
                
                # Execute removal on device
                device_info = ssh_push._load_device_info(device)
                if not device_info:
                    error_msg = f"Missing SSH info for {device}"
                    removal_errors.append(error_msg)
                    self._log_deployment(removal_id, f"❌ {error_msg}")
                    continue
                
                cli_commands = device_commands.get(device, [])
                if not cli_commands:
                    error_msg = f"No CLI commands for {device}"
                    removal_errors.append(error_msg)
                    self._log_deployment(removal_id, f"❌ {error_msg}")
                    continue
                
                # Execute removal
                device_name, success, already_exists, error_message = ssh_push._execute_on_device_parallel(
                    device, device_info, cli_commands, None, "remove"
                )
                
                removal_results[device] = (success, already_exists, error_message)
                
                if success:
                    self._log_deployment(removal_id, f"✅ {device}: Configuration removed successfully")
                else:
                    error_msg = f"Removal failed on {device}: {error_message}"
                    removal_errors.append(error_msg)
                    self._log_deployment(removal_id, f"❌ {error_msg}")
            
            if removal_errors:
                return False
            
            # Stage 2: Verification
            removal_info['stage'] = 'verifying_removal'
            removal_info['progress'] = 70
            self._log_deployment(removal_id, "🔍 Stage 2: Verifying removal...")
            self._emit_progress(removal_id, removal_info)
            
            verification_errors = []
            
            for i, device in enumerate(devices):
                device_progress = 70 + (i / total_devices) * 30  # 70-100%
                removal_info['progress'] = int(device_progress)
                removal_info['stage'] = f'verifying_device_{device}'
                self._log_deployment(removal_id, f"🔍 Verifying {device}...")
                self._emit_progress(removal_id, removal_info)
                
                # Verify removal on device
                device_info = ssh_push._load_device_info(device)
                if not device_info:
                    verification_errors.append(f"Missing SSH info for {device}")
                    self._log_deployment(removal_id, f"❌ Missing SSH info for {device}")
                    continue
                
                device_name, success = ssh_push._verify_config_deployment_parallel(
                    device, device_info, service_name, None
                )
                
                # For removal, we expect the verification to fail (config not found)
                if not success:
                    self._log_deployment(removal_id, f"✅ {device}: Removal verified (config not found)")
                else:
                    verification_errors.append(f"Verification failed for {device} - config still exists")
                    self._log_deployment(removal_id, f"❌ {device}: Verification failed - config still exists")
            
            if verification_errors:
                self._log_deployment(removal_id, f"❌ Verification errors: {verification_errors}")
                return False
            
            self._log_deployment(removal_id, "✅ All devices verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Removal execution error: {e}")
            return False
    
    def _verify_deployment_with_config(self, deployment_id: str, ssh_push, config_data: Dict) -> bool:
        """Verify deployment on all devices using existing config_data"""
        try:
            deployment_info = self.active_deployments[deployment_id]
            
            devices = list(config_data.keys())
            # Filter out _metadata key - only process actual devices
            devices = [device for device in config_data.keys() if device != '_metadata']
            total_devices = len(devices)
            
            self._log_deployment(deployment_id, f"🔍 Verifying deployment on {total_devices} devices...")
            
            verification_errors = []
            
            for i, device in enumerate(devices):
                device_progress = 90 + (i / total_devices) * 10  # 90-100%
                deployment_info['progress'] = int(device_progress)
                deployment_info['stage'] = f'verifying_device_{device}'
                self._log_deployment(deployment_id, f"🔍 Verifying {device}...")
                self._emit_progress(deployment_id, deployment_info)
                
                # Verify deployment on device
                device_info = ssh_push._load_device_info(device)
                if not device_info:
                    verification_errors.append(f"Missing SSH info for {device}")
                    self._log_deployment(deployment_id, f"❌ Missing SSH info for {device}")
                    continue
                
                # Extract service name for verification from the first command
                service_name = None
                device_commands = config_data.get(device, [])
                for command in device_commands:
                    if "network-services bridge-domain instance" in command:
                        parts = command.split()
                        if len(parts) >= 4:
                            service_name = parts[3]  # Extract the service name
                            break
                
                if not service_name:
                    verification_errors.append(f"Could not extract service name for {device}")
                    self._log_deployment(deployment_id, f"❌ Could not extract service name for {device}")
                    continue
                
                device_name, success = ssh_push._verify_config_deployment_parallel(
                    device, device_info, service_name, None
                )
                
                if success:
                    self._log_deployment(deployment_id, f"✅ {device}: Verification passed")
                else:
                    verification_errors.append(f"Verification failed for {device}")
                    self._log_deployment(deployment_id, f"❌ {device}: Verification failed")
            
            if verification_errors:
                self._log_deployment(deployment_id, f"❌ Verification errors: {verification_errors}")
                return False
            
            self._log_deployment(deployment_id, "✅ All devices verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Verification error: {e}")
            return False

    def _verify_deployment(self, deployment_id: str, ssh_push, config_name: str) -> bool:
        """Verify deployment on all devices (DEPRECATED - use _verify_deployment_with_config instead)"""
        try:
            deployment_info = self.active_deployments[deployment_id]
            
            # Load config to get devices
            config = ssh_push.push_manager.load_config(config_name)
            if not config:
                self._log_deployment(deployment_id, "❌ Failed to load configuration for verification")
                return False
            
            devices = list(config.keys())
            # Filter out _metadata key - only process actual devices
            devices = [device for device in config.keys() if device != '_metadata']
            total_devices = len(devices)
            
            self._log_deployment(deployment_id, f"🔍 Verifying deployment on {total_devices} devices...")
            
            verification_errors = []
            
            for i, device in enumerate(devices):
                device_progress = 90 + (i / total_devices) * 10  # 90-100%
                deployment_info['progress'] = int(device_progress)
                deployment_info['stage'] = f'verifying_device_{device}'
                self._log_deployment(deployment_id, f"🔍 Verifying {device}...")
                self._emit_progress(deployment_id, deployment_info)
                
                # Verify deployment on device
                device_info = ssh_push.push_manager._load_device_info(device)
                if not device_info:
                    verification_errors.append(f"Missing SSH info for {device}")
                    self._log_deployment(deployment_id, f"❌ Missing SSH info for {device}")
                    continue
                
                # Extract service name for verification
                service_name = config_name.replace('bridge_domain_', '')
                
                device_name, success = ssh_push.push_manager._verify_config_deployment_parallel(
                    device, device_info, service_name, None
                )
                
                if success:
                    self._log_deployment(deployment_id, f"✅ {device}: Verification passed")
                else:
                    verification_errors.append(f"Verification failed for {device}")
                    self._log_deployment(deployment_id, f"❌ {device}: Verification failed")
            
            if verification_errors:
                self._log_deployment(deployment_id, f"❌ Verification errors: {verification_errors}")
                return False
            
            self._log_deployment(deployment_id, "✅ All devices verified successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Verification error: {e}")
            return False
    
    def _log_deployment(self, deployment_id: str, message: str):
        """Add log message to deployment"""
        if deployment_id in self.active_deployments:
            deployment_info = self.active_deployments[deployment_id]
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_entry = f"[{timestamp}] {message}"
            deployment_info['logs'].append(log_entry)
            self.logger.info(f"Deployment {deployment_id}: {message}")
    
    def _emit_progress(self, deployment_id: str, deployment_info: Dict):
        """Emit progress update via WebSocket"""
        try:
            self.socketio.emit('deployment_update', {
                'deployment_id': deployment_id,
                'status': deployment_info['status'],
                'progress': deployment_info['progress'],
                'stage': deployment_info['stage'],
                'logs': deployment_info['logs'][-10:],  # Last 10 log entries
                'errors': deployment_info.get('errors', []),
                'device_results': deployment_info.get('device_results', {}),
                'timestamp': datetime.utcnow().isoformat()
            }, room=deployment_id)
        except Exception as e:
            self.logger.error(f"Failed to emit progress for {deployment_id}: {e}")
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Dict]:
        """Get current deployment status"""
        # Add debug logging
        self.logger.info(f"🔍 Looking for deployment/removal status: {deployment_id}")
        self.logger.info(f"🔍 Active deployments: {list(self.active_deployments.keys())}")
        
        status = self.active_deployments.get(deployment_id)
        if status:
            self.logger.info(f"✅ Found status for {deployment_id}: {status['status']}")
        else:
            self.logger.info(f"❌ No status found for {deployment_id}")
        
        return status
    
    def cleanup_deployment(self, deployment_id: str):
        """Clean up deployment data"""
        if deployment_id in self.active_deployments:
            del self.active_deployments[deployment_id] 