#!/usr/bin/env python3
"""
BD Editing Session Manager

Manages BD editing sessions with persistence, recovery, and change tracking.
Handles session interruptions and provides recovery capabilities.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, List
from .data_models import SessionError, BDDataRetrievalError

logger = logging.getLogger(__name__)


class BDEditingSessionManager:
    """Manage BD editing sessions with persistence and recovery"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.session_storage_path = "instance/bd_editing_sessions/"
        
        # Ensure session storage directory exists
        os.makedirs(self.session_storage_path, exist_ok=True)
    
    def create_editing_session(self, bd_name: str) -> Dict:
        """Create new BD editing session"""
        
        try:
            session_id = self._generate_session_id()
            
            # Get BD data for editing
            bd_data = self._get_bd_data_for_editing(bd_name)
            
            session = {
                'session_id': session_id,
                'bd_name': bd_name,
                'created_at': datetime.now().isoformat(),
                'working_copy': bd_data,
                'changes_made': [],
                'last_activity': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Persist session
            self._save_session(session)
            
            logger.info(f"Created editing session {session_id} for BD {bd_name}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating editing session for {bd_name}: {e}")
            raise SessionError(f"Failed to create editing session: {e}")
    
    def save_session_state(self, session: Dict):
        """Save current session state"""
        
        try:
            session['last_activity'] = datetime.now().isoformat()
            self._save_session(session)
            
        except Exception as e:
            logger.error(f"Error saving session state: {e}")
            raise SessionError(f"Failed to save session state: {e}")
    
    def recover_session(self, session_id: str) -> Optional[Dict]:
        """Recover interrupted session"""
        
        try:
            session = self._load_session(session_id)
            
            if session:
                # Update last activity
                session['last_activity'] = datetime.now().isoformat()
                session['status'] = 'recovered'
                self._save_session(session)
                
                logger.info(f"Recovered session {session_id}")
                
            return session
            
        except Exception as e:
            logger.error(f"Error recovering session {session_id}: {e}")
            return None
    
    def list_active_sessions(self) -> List[Dict]:
        """List all active editing sessions"""
        
        active_sessions = []
        
        try:
            if not os.path.exists(self.session_storage_path):
                return active_sessions
            
            for filename in os.listdir(self.session_storage_path):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json extension
                    session = self._load_session(session_id)
                    
                    if session and session.get('status') == 'active':
                        active_sessions.append({
                            'session_id': session_id,
                            'bd_name': session.get('bd_name'),
                            'created_at': session.get('created_at'),
                            'changes_count': len(session.get('changes_made', []))
                        })
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Error listing active sessions: {e}")
            return []
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session files"""
        
        try:
            if not os.path.exists(self.session_storage_path):
                return
            
            current_time = datetime.now()
            cleaned_count = 0
            
            for filename in os.listdir(self.session_storage_path):
                if filename.endswith('.json'):
                    session_file = os.path.join(self.session_storage_path, filename)
                    
                    # Check file age
                    file_time = datetime.fromtimestamp(os.path.getmtime(session_file))
                    age_hours = (current_time - file_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        os.remove(session_file)
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old session files")
                
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return str(uuid.uuid4())[:8]
    
    def _get_bd_data_for_editing(self, bd_name: str) -> Dict:
        """Get BD data optimized for editing"""
        
        try:
            # Use database manager to get BD data
            bd_data = self.db_manager.get_bridge_domain_by_name(bd_name)
            
            if not bd_data:
                raise ValueError(f"BD {bd_name} not found in database")
            
            # Parse discovery data if available
            discovery_data = bd_data.get('discovery_data', '{}')
            if isinstance(discovery_data, str):
                discovery_data = json.loads(discovery_data)
            
            # Create working copy structure
            working_copy = {
                'id': bd_data.get('id'),
                'name': bd_data['name'],
                'username': bd_data.get('username'),
                'vlan_id': bd_data.get('vlan_id'),
                'dnaas_type': bd_data.get('dnaas_type'),
                'topology_type': bd_data.get('topology_type'),
                'source': bd_data.get('source'),
                'devices': discovery_data.get('devices', {}),
                'interfaces': self._extract_interfaces_from_discovery_data(discovery_data)
            }
            
            return working_copy
            
        except Exception as e:
            logger.error(f"Error getting BD data for editing: {e}")
            raise BDDataRetrievalError(f"Failed to retrieve BD {bd_name}: {e}")
    
    def _extract_interfaces_from_discovery_data(self, discovery_data: Dict) -> List[Dict]:
        """Extract interface list from discovery data"""
        
        interfaces = []
        
        try:
            devices = discovery_data.get('devices', {})
            
            for device_name, device_info in devices.items():
                device_interfaces = device_info.get('interfaces', [])
                
                for interface in device_interfaces:
                    interfaces.append({
                        'device': device_name,
                        'interface': interface.get('name'),
                        'vlan_id': interface.get('vlan_id'),
                        'role': interface.get('role'),
                        'type': interface.get('type'),
                        'original_config': interface.get('raw_cli_config', []),
                        'added_by_editor': False  # Original interface
                    })
            
        except Exception as e:
            logger.warning(f"Error extracting interfaces from discovery data: {e}")
        
        return interfaces
    
    def _save_session(self, session: Dict):
        """Persist session to storage"""
        
        try:
            session_file = os.path.join(self.session_storage_path, f"{session['session_id']}.json")
            
            with open(session_file, 'w') as f:
                json.dump(session, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            raise SessionError(f"Failed to save session: {e}")
    
    def _load_session(self, session_id: str) -> Optional[Dict]:
        """Load session from storage"""
        
        try:
            session_file = os.path.join(self.session_storage_path, f"{session_id}.json")
            
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None


# Convenience functions
def create_bd_editing_session(bd_name: str, db_manager) -> Dict:
    """Convenience function to create BD editing session"""
    session_manager = BDEditingSessionManager(db_manager)
    return session_manager.create_editing_session(bd_name)


def save_bd_session(session: Dict, db_manager):
    """Convenience function to save BD session"""
    session_manager = BDEditingSessionManager(db_manager)
    session_manager.save_session_state(session)
