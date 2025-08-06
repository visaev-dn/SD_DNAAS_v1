#!/usr/bin/env python3
"""
Database Manager for Lab Automation Framework
Provides robust database operations with multiple fallback mechanisms
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database management with robust error handling"""
    
    def __init__(self, db_path: str = 'instance/lab_automation.db'):
        self.db_path = db_path
        self.logger = logger
    
    def save_configuration(self, service_name: str, vlan_id: int, config_data: Dict, file_path: Optional[Path] = None, config_metadata: Optional[Dict] = None) -> bool:
        """Save configuration with multiple fallback mechanisms"""
        
        self.logger.info(f"Attempting to save configuration: {service_name}")
        
        # Method 1: Direct SQL (Primary method)
        if self._save_with_direct_sql(service_name, vlan_id, config_data, file_path, config_metadata):
            return True
        
        # Method 2: SQLAlchemy (Fallback)
        if self._save_with_sqlalchemy(service_name, vlan_id, config_data, file_path, config_metadata):
            return True
        
        # Method 3: Manual SQL with retry
        if self._save_with_manual_sql(service_name, vlan_id, config_data, file_path, config_metadata):
            return True
        
        self.logger.error(f"All database save methods failed for: {service_name}")
        return False
    
    def _save_with_direct_sql(self, service_name: str, vlan_id: int, config_data: Dict, file_path: Optional[Path] = None, config_metadata: Optional[Dict] = None) -> bool:
        """Save using direct SQLite connection"""
        try:
            self.logger.info("Attempting direct SQL save...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if configuration already exists
            cursor.execute("SELECT id FROM configurations WHERE service_name = ?", (service_name,))
            existing = cursor.fetchone()
            
            if existing:
                self.logger.warning(f"Configuration {service_name} already exists, skipping")
                conn.close()
                return True
            
            # Insert new configuration
            cursor.execute("""
                INSERT INTO configurations (user_id, service_name, vlan_id, config_type, status, config_data, config_metadata, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1, service_name, vlan_id, 'bridge_domain', 'pending',
                json.dumps(config_data), json.dumps(config_metadata) if config_metadata else None, 
                str(file_path) if file_path else None, datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            config_id = cursor.lastrowid
            conn.close()
            
            self.logger.info(f"✅ Direct SQL save successful: {config_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Direct SQL save failed: {e}")
            return False
    
    def _save_with_sqlalchemy(self, service_name: str, vlan_id: int, config_data: Dict, file_path: Optional[Path] = None, config_metadata: Optional[Dict] = None) -> bool:
        """Save using SQLAlchemy with proper session management"""
        try:
            self.logger.info("Attempting SQLAlchemy save...")
            
            # Import here to avoid circular imports
            import sqlite3
            from models import Configuration
            
            # Use direct SQLAlchemy approach without app context
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if configuration already exists
            cursor.execute("SELECT id FROM configurations WHERE service_name = ?", (service_name,))
            existing = cursor.fetchone()
            
            if existing:
                self.logger.warning(f"Configuration {service_name} already exists, skipping")
                conn.close()
                return True
            
            # Insert new configuration
            cursor.execute("""
                INSERT INTO configurations (user_id, service_name, vlan_id, config_type, status, config_data, config_metadata, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1, service_name, vlan_id, 'bridge_domain', 'pending',
                json.dumps(config_data), json.dumps(config_metadata) if config_metadata else None, 
                str(file_path) if file_path else None, datetime.utcnow().isoformat()
            ))
            
            conn.commit()
            config_id = cursor.lastrowid
            conn.close()
            
            self.logger.info(f"✅ SQLAlchemy-style save successful: {config_id}")
            return True
                
        except Exception as e:
            self.logger.error(f"❌ SQLAlchemy-style save failed: {e}")
            return False
    
    def _save_with_manual_sql(self, service_name: str, vlan_id: int, config_data: Dict, file_path: Optional[Path] = None, config_metadata: Optional[Dict] = None) -> bool:
        """Save using manual SQL with retry mechanism"""
        try:
            self.logger.info("Attempting manual SQL save with retry...")
            
            # Try multiple times with different approaches
            for attempt in range(3):
                conn = None
                try:
                    conn = sqlite3.connect(self.db_path, timeout=30.0)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO configurations (user_id, service_name, vlan_id, config_type, status, config_data, config_metadata, file_path, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        1, service_name, vlan_id, 'bridge_domain', 'pending',
                        json.dumps(config_data), json.dumps(config_metadata) if config_metadata else None, 
                        str(file_path) if file_path else None, datetime.utcnow().isoformat()
                    ))
                    
                    conn.commit()
                    config_id = cursor.lastrowid
                    conn.close()
                    
                    self.logger.info(f"✅ Manual SQL save successful (attempt {attempt + 1}): {config_id}")
                    return True
                    
                except Exception as attempt_error:
                    self.logger.warning(f"Manual SQL attempt {attempt + 1} failed: {attempt_error}")
                    if conn:
                        conn.close()
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Manual SQL save failed: {e}")
            return False
    
    def verify_save(self, service_name: str) -> bool:
        """Verify that a configuration was saved successfully"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM configurations WHERE service_name = ?", (service_name,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                self.logger.info(f"✅ Verification successful: {service_name} found with ID {result[0]}")
                return True
            else:
                self.logger.error(f"❌ Verification failed: {service_name} not found")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Verification error: {e}")
            return False
    
    def get_configuration_count(self) -> int:
        """Get total number of configurations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM configurations")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            self.logger.error(f"Error getting configuration count: {e}")
            return 0
    
    def get_configuration_by_service_name(self, service_name: str) -> Optional[Dict]:
        """Get configuration by service name"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, service_name, vlan_id, config_type, status, 
                       config_data, file_path, created_at, deployed_at, deployed_by
                FROM configurations 
                WHERE service_name = ?
            """, (service_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'user_id': result[1],
                    'service_name': result[2],
                    'vlan_id': result[3],
                    'config_type': result[4],
                    'status': result[5],
                    'config_data': result[6],
                    'file_path': result[7],
                    'created_at': result[8],
                    'deployed_at': result[9],
                    'deployed_by': result[10]
                }
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting configuration: {e}")
            return None
    
    def get_configurations_by_status(self, status: str) -> list:
        """Get all configurations with a specific status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, service_name, vlan_id, config_type, status, 
                       config_data, file_path, created_at, deployed_at, deployed_by
                FROM configurations 
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))
            
            rows = cursor.fetchall()
            conn.close()
            
            configs = []
            for row in rows:
                configs.append({
                    'id': row[0],
                    'user_id': row[1],
                    'service_name': row[2],
                    'vlan_id': row[3],
                    'config_type': row[4],
                    'status': row[5],
                    'config_data': row[6],
                    'file_path': row[7],
                    'created_at': row[8],
                    'deployed_at': row[9],
                    'deployed_by': row[10]
                })
            
            return configs
            
        except Exception as e:
            self.logger.error(f"Error getting configurations by status {status}: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            # Test basic connectivity
            config_count = self.get_configuration_count()
            
            # Test save operation
            test_service_name = f"health_check_{int(datetime.now().timestamp())}"
            test_config_data = {"test": "health_check"}
            test_file_path = Path("test/health_check.yaml")
            
            save_success = self.save_configuration(
                service_name=test_service_name,
                vlan_id=999,
                config_data=test_config_data,
                file_path=test_file_path
            )
            
            verify_success = self.verify_save(test_service_name)
            
            return {
                "database_healthy": True,
                "config_count": config_count,
                "save_test": save_success,
                "verify_test": verify_success,
                "test_service_name": test_service_name
            }
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "database_healthy": False,
                "error": str(e)
            } 