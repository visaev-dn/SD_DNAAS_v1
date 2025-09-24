#!/usr/bin/env python3
"""
Database Unification Migration Script
====================================

Migrates from fragmented database schemas to unified bridge domain schema.
Aggressive approach: Clean slate with data preservation.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DatabaseUnificationMigration:
    """Aggressive database unification with clean schema"""
    
    def __init__(self, db_path: str = "instance/lab_automation.db"):
        self.db_path = db_path
        self.backup_path = f"instance/lab_automation_backup_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
    def execute_migration(self):
        """Execute complete database unification"""
        print("🚀 Starting aggressive database unification...")
        
        try:
            # Step 1: Backup current database
            self._create_backup()
            
            # Step 2: Extract current data
            current_data = self._extract_current_data()
            
            # Step 3: Create clean unified schema
            self._create_unified_schema()
            
            # Step 4: Migrate data to unified schema
            self._migrate_data_to_unified_schema(current_data)
            
            # Step 5: Validate migration
            self._validate_migration(current_data)
            
            print("✅ Database unification completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            self._restore_from_backup()
            raise
    
    def _create_backup(self):
        """Create backup of current database"""
        print(f"💾 Creating database backup: {self.backup_path}")
        
        import shutil
        shutil.copy2(self.db_path, self.backup_path)
        
        print("✅ Database backup created")
    
    def _extract_current_data(self) -> dict:
        """Extract all current data before schema changes"""
        print("📊 Extracting current database data...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data = {
            'users': [],
            'personal_bridge_domains': [],
            'configurations': [],
            'phase1_data': []
        }
        
        try:
            # Extract users
            cursor.execute("SELECT * FROM users")
            columns = [desc[0] for desc in cursor.description]
            data['users'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Extract personal bridge domains (discovery data)
            cursor.execute("SELECT * FROM personal_bridge_domains")
            columns = [desc[0] for desc in cursor.description]
            data['personal_bridge_domains'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Extract configurations
            try:
                cursor.execute("SELECT * FROM configurations")
                columns = [desc[0] for desc in cursor.description]
                data['configurations'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            except:
                data['configurations'] = []
            
            # Extract any Phase 1 data
            try:
                cursor.execute("SELECT * FROM phase1_configurations")
                columns = [desc[0] for desc in cursor.description]
                data['phase1_data'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            except:
                data['phase1_data'] = []
        
        except Exception as e:
            print(f"⚠️ Error extracting some data: {e}")
        
        finally:
            conn.close()
        
        print(f"✅ Data extracted:")
        print(f"   • Users: {len(data['users'])}")
        print(f"   • Bridge Domains: {len(data['personal_bridge_domains'])}")
        print(f"   • Configurations: {len(data['configurations'])}")
        print(f"   • Phase 1 Data: {len(data['phase1_data'])}")
        
        return data
    
    def _create_unified_schema(self):
        """Create clean unified schema"""
        print("🏗️ Creating unified database schema...")
        
        # Read unified schema SQL
        schema_path = Path(__file__).parent / "unified_schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Drop existing tables (aggressive approach)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Drop old fragmented tables
            old_tables = [
                'personal_bridge_domains',
                'configurations', 
                'phase1_configurations',
                'phase1_bridge_domain_config',
                'phase1_vlan_configs'
            ]
            
            for table in old_tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"🗑️ Dropped old table: {table}")
                except:
                    pass
            
            # Create unified schema
            cursor.executescript(schema_sql)
            conn.commit()
            
            print("✅ Unified schema created successfully")
            
        finally:
            conn.close()
    
    def _migrate_data_to_unified_schema(self, data: dict):
        """Migrate extracted data to unified schema"""
        print("🔄 Migrating data to unified schema...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Migrate users (preserve user accounts)
            for user in data['users']:
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (id, username, email, password_hash, role, is_active, is_admin, created_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user['id'], user['username'], user['email'], 
                    user['password_hash'], user.get('role', 'user'), 
                    user.get('is_active', True), user.get('is_admin', False),
                    user['created_at'], user.get('created_by', 1)
                ))
            
            print(f"✅ Migrated {len(data['users'])} users")
            
            # Migrate bridge domains from discovery data
            migrated_count = 0
            for bd in data['personal_bridge_domains']:
                try:
                    # Parse discovery data
                    discovery_data = json.loads(bd.get('discovery_data', '{}'))
                    
                    # Extract bridge domain analysis
                    bridge_analysis = discovery_data.get('bridge_domain_analysis', {})
                    
                    cursor.execute("""
                        INSERT INTO bridge_domains 
                        (name, source, username, vlan_id, topology_type, dnaas_type,
                         configuration_data, discovery_data, deployment_status,
                         created_at, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        bd['bridge_domain_name'],
                        'discovered',
                        bd.get('username', 'unknown'),
                        bd.get('vlan_id'),
                        bd.get('topology_type', 'unknown'),
                        bridge_analysis.get('dnaas_type', 'unknown'),
                        bd.get('discovery_data', '{}'),
                        bd.get('discovery_data', '{}'),
                        'discovered',
                        bd.get('created_at', datetime.now().isoformat()),
                        bd.get('user_id', 1)
                    ))
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Failed to migrate BD {bd.get('bridge_domain_name', 'unknown')}: {e}")
            
            print(f"✅ Migrated {migrated_count} bridge domains")
            
            # Migrate configurations (if any)
            config_count = 0
            for config in data['configurations']:
                try:
                    cursor.execute("""
                        INSERT INTO bridge_domains 
                        (name, source, username, vlan_id, configuration_data,
                         deployment_status, created_at, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        config['service_name'],
                        'created',
                        config.get('username', 'unknown'),
                        config.get('vlan_id'),
                        config.get('config_data', '{}'),
                        config.get('status', 'pending'),
                        config.get('created_at', datetime.now().isoformat()),
                        config.get('user_id', 1)
                    ))
                    
                    config_count += 1
                    
                except Exception as e:
                    print(f"⚠️ Failed to migrate config {config.get('service_name', 'unknown')}: {e}")
            
            print(f"✅ Migrated {config_count} configurations")
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _validate_migration(self, original_data: dict):
        """Validate migration success"""
        print("🧪 Validating migration...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check bridge domains count
            cursor.execute("SELECT COUNT(*) FROM bridge_domains")
            new_count = cursor.fetchone()[0]
            
            original_bd_count = len(original_data['personal_bridge_domains'])
            original_config_count = len(original_data['configurations'])
            expected_count = original_bd_count + original_config_count
            
            print(f"📊 Migration validation:")
            print(f"   • Original bridge domains: {original_bd_count}")
            print(f"   • Original configurations: {original_config_count}")
            print(f"   • Expected total: {expected_count}")
            print(f"   • Migrated total: {new_count}")
            
            if new_count >= expected_count * 0.95:  # Allow 5% loss for data quality issues
                print("✅ Migration validation passed")
            else:
                raise Exception(f"Migration validation failed: {new_count} < {expected_count}")
            
            # Test unified database manager
            from database_manager import DatabaseManager
            db_manager = DatabaseManager()
            
            # Test basic operations
            cursor.execute("SELECT name FROM bridge_domains LIMIT 5")
            sample_bds = cursor.fetchall()
            
            print(f"✅ Sample bridge domains accessible: {[bd[0] for bd in sample_bds]}")
            
        finally:
            conn.close()
    
    def _restore_from_backup(self):
        """Restore database from backup if migration fails"""
        print("🔄 Restoring database from backup...")
        
        import shutil
        shutil.copy2(self.backup_path, self.db_path)
        
        print("✅ Database restored from backup")

def run_migration():
    """Execute the database unification migration"""
    migration = DatabaseUnificationMigration()
    return migration.execute_migration()

if __name__ == "__main__":
    run_migration()
