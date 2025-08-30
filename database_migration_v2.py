#!/usr/bin/env python3
"""
Database Migration Script v2 - Optimized Structure
This script migrates the existing Phase 1 database to the new optimized structure.

Changes:
1. Add new tables: path_groups, vlan_configs, confidence_metrics
2. Add new fields to existing tables
3. Consolidate destinations into JSON field
4. Migrate existing data to new structure
5. Update confidence scores
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseMigrationV2:
    """Database migration to optimized Phase 1 structure"""
    
    def __init__(self, db_path: str = 'instance/lab_automation.db'):
        """Initialize migration with database path"""
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Verify database exists
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
        logger.info(f"🚀 Starting database migration to optimized structure")
        logger.info(f"Database: {db_path}")
        logger.info(f"Backup: {self.backup_path}")
    
    def create_backup(self) -> bool:
        """Create backup of current database"""
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            logger.info(f"✅ Database backup created: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def add_new_tables(self) -> bool:
        """Add new optimized tables to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Add new fields to existing tables
            logger.info("📝 Adding new fields to existing tables...")
            
            # Add new fields to phase1_topology_data
            try:
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN scan_method TEXT DEFAULT 'unknown'
                """)
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN legacy_bridge_domain_id INTEGER
                """)
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN device_count INTEGER DEFAULT 0
                """)
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN interface_count INTEGER DEFAULT 0
                """)
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN path_count INTEGER DEFAULT 0
                """)
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN total_bandwidth TEXT
                """)
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                """)
                cursor.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN change_count INTEGER DEFAULT 0
                """)
                logger.info("✅ Added new fields to phase1_topology_data")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
                logger.info("ℹ️  Some fields already exist in phase1_topology_data")
            
            # Add new fields to phase1_device_info
            try:
                cursor.execute("""
                    ALTER TABLE phase1_device_info 
                    ADD COLUMN is_primary_source BOOLEAN DEFAULT 0
                """)
                cursor.execute("""
                    ALTER TABLE phase1_device_info 
                    ADD COLUMN redundancy_group_id INTEGER
                """)
                logger.info("✅ Added new fields to phase1_device_info")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
                logger.info("ℹ️  Some fields already exist in phase1_device_info")
            
            # Add new fields to phase1_interface_info
            try:
                cursor.execute("""
                    ALTER TABLE phase1_interface_info 
                    ADD COLUMN parent_interface TEXT
                """)
                cursor.execute("""
                    ALTER TABLE phase1_interface_info 
                    ADD COLUMN subinterface_id TEXT
                """)
                logger.info("✅ Added new fields to phase1_interface_info")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
                logger.info("ℹ️  Some fields already exist in phase1_interface_info")
            
            # Add destinations JSON field to phase1_bridge_domain_config
            try:
                cursor.execute("""
                    ALTER TABLE phase1_bridge_domain_config 
                    ADD COLUMN destinations TEXT DEFAULT '[]'
                """)
                logger.info("✅ Added destinations field to phase1_bridge_domain_config")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    raise
                logger.info("ℹ️  Destinations field already exists in phase1_bridge_domain_config")
            
            # 2. Create new optimized tables
            logger.info("📝 Creating new optimized tables...")
            
            # Create phase1_path_groups table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phase1_path_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER NOT NULL,
                    source_device TEXT NOT NULL,
                    destination_device TEXT NOT NULL,
                    path_count INTEGER DEFAULT 1,
                    primary_path_id INTEGER,
                    backup_paths TEXT DEFAULT '[]',
                    load_balancing_type TEXT DEFAULT 'active-active',
                    redundancy_level TEXT DEFAULT 'none',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (config_id) REFERENCES phase1_bridge_domain_config (id)
                )
            """)
            logger.info("✅ Created phase1_path_groups table")
            
            # Create phase1_vlan_configs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phase1_vlan_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER NOT NULL,
                    vlan_id INTEGER NOT NULL,
                    vlan_type TEXT NOT NULL DEFAULT 'single',
                    outer_vlan INTEGER,
                    inner_vlan INTEGER,
                    vlan_range_start INTEGER,
                    vlan_range_end INTEGER,
                    vlan_list TEXT DEFAULT '[]',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (config_id) REFERENCES phase1_bridge_domain_config (id)
                )
            """)
            logger.info("✅ Created phase1_vlan_configs table")
            
            # Create phase1_confidence_metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phase1_confidence_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_id INTEGER NOT NULL,
                    device_confidence REAL DEFAULT 0.0,
                    interface_confidence REAL DEFAULT 0.0,
                    path_confidence REAL DEFAULT 0.0,
                    vlan_confidence REAL DEFAULT 0.0,
                    overall_confidence REAL DEFAULT 0.0,
                    confidence_factors TEXT DEFAULT '[]',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (config_id) REFERENCES phase1_bridge_domain_config (id)
                )
            """)
            logger.info("✅ Created phase1_confidence_metrics table")
            
            # 3. Create indexes for performance
            logger.info("📝 Creating performance indexes...")
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_groups_config_id ON phase1_path_groups (config_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_groups_source_dest ON phase1_path_groups (source_device, destination_device)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vlan_configs_config_id ON phase1_vlan_configs (config_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vlan_configs_vlan_id ON phase1_vlan_configs (vlan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_confidence_metrics_config_id ON phase1_confidence_metrics (config_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_info_primary_source ON phase1_device_info (is_primary_source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_interface_info_parent ON phase1_interface_info (parent_interface)")
            
            logger.info("✅ Created performance indexes")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ New tables and fields added successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add new tables: {e}")
            return False
    
    def migrate_existing_data(self) -> bool:
        """Migrate existing data to the new optimized structure"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.info("🔄 Migrating existing data to optimized structure...")
            
            # 1. First ensure all new fields exist by checking and adding them if needed
            logger.info("🔍 Ensuring all required fields exist...")
            
            # Check if device_count field exists, add if not
            try:
                cursor.execute("SELECT device_count FROM phase1_topology_data LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("📝 Adding missing device_count field...")
                cursor.execute("ALTER TABLE phase1_topology_data ADD COLUMN device_count INTEGER DEFAULT 0")
            
            # Check if interface_count field exists, add if not
            try:
                cursor.execute("SELECT interface_count FROM phase1_topology_data LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("📝 Adding missing interface_count field...")
                cursor.execute("ALTER TABLE phase1_topology_data ADD COLUMN interface_count INTEGER DEFAULT 0")
            
            # Check if path_count field exists, add if not
            try:
                cursor.execute("SELECT path_count FROM phase1_topology_data LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("📝 Adding missing path_count field...")
                cursor.execute("ALTER TABLE phase1_topology_data ADD COLUMN path_count INTEGER DEFAULT 0")
            
            # Check if total_bandwidth field exists, add if not
            try:
                cursor.execute("SELECT total_bandwidth FROM phase1_topology_data LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("📝 Adding missing total_bandwidth field...")
                cursor.execute("ALTER TABLE phase1_topology_data ADD COLUMN total_bandwidth TEXT")
            
            # Check if last_updated field exists, add if not
            try:
                cursor.execute("SELECT last_updated FROM phase1_topology_data LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("📝 Adding missing last_updated field...")
                cursor.execute("ALTER TABLE phase1_topology_data ADD COLUMN last_updated DATETIME")
            
            # Check if change_count field exists, add if not
            try:
                cursor.execute("SELECT change_count FROM phase1_topology_data LIMIT 1")
            except sqlite3.OperationalError:
                logger.info("📝 Adding missing change_count field...")
                cursor.execute("ALTER TABLE phase1_topology_data ADD COLUMN change_count INTEGER DEFAULT 0")
            
            # 2. Update topology summary fields
            logger.info("📊 Updating topology summary fields...")
            cursor.execute("""
                UPDATE phase1_topology_data 
                SET device_count = (
                    SELECT COUNT(*) FROM phase1_device_info 
                    WHERE phase1_device_info.topology_id = phase1_topology_data.id
                )
            """)
            
            cursor.execute("""
                UPDATE phase1_topology_data 
                SET interface_count = (
                    SELECT COUNT(*) FROM phase1_interface_info 
                    WHERE phase1_interface_info.topology_id = phase1_topology_data.id
                )
            """)
            
            cursor.execute("""
                UPDATE phase1_topology_data 
                SET path_count = (
                    SELECT COUNT(*) FROM phase1_path_info 
                    WHERE phase1_path_info.topology_id = phase1_topology_data.id
                )
            """)
            
            cursor.execute("""
                UPDATE phase1_topology_data 
                SET last_updated = CURRENT_TIMESTAMP
            """)
            
            logger.info("✅ Updated topology summary fields")
            
            # 3. Consolidate destinations into JSON field
            logger.info("🎯 Consolidating destinations into JSON field...")
            
            # Get all bridge domain configs
            cursor.execute("SELECT id FROM phase1_bridge_domain_config")
            config_ids = [row[0] for row in cursor.fetchall()]
            
            for config_id in config_ids:
                # Get destinations for this config
                cursor.execute("""
                    SELECT device, port FROM phase1_destinations 
                    WHERE bridge_domain_config_id = ?
                """, (config_id,))
                
                destinations = []
                for row in cursor.fetchall():
                    destination = {
                        'device': row[0],
                        'interface': row[1],
                        'created_at': datetime.now().isoformat()
                    }
                    destinations.append(destination)
                
                # Update the destinations JSON field
                destinations_json = json.dumps(destinations)
                cursor.execute("""
                    UPDATE phase1_bridge_domain_config 
                    SET destinations = ? 
                    WHERE id = ?
                """, (destinations_json, config_id))
                
                logger.info(f"✅ Consolidated {len(destinations)} destinations for config {config_id}")
            
            # 4. Create path groups from existing paths
            logger.info("🛣️  Creating path groups from existing paths...")
            
            for config_id in config_ids:
                # Get paths for this topology
                cursor.execute("""
                    SELECT p.id, p.source_device, p.dest_device 
                    FROM phase1_path_info p
                    JOIN phase1_bridge_domain_config c ON p.topology_id = c.topology_id
                    WHERE c.id = ?
                """, (config_id,))
                
                path_groups = {}
                for row in cursor.fetchall():
                    path_id, source, dest = row
                    key = (source, dest)
                    if key not in path_groups:
                        path_groups[key] = []
                    path_groups[key].append(path_id)
                
                # Create path group records
                for (source, dest), path_ids in path_groups.items():
                    primary_path_id = path_ids[0] if path_ids else None
                    backup_paths = path_ids[1:] if len(path_ids) > 1 else []
                    
                    cursor.execute("""
                        INSERT INTO phase1_path_groups 
                        (config_id, source_device, destination_device, path_count, 
                         primary_path_id, backup_paths, load_balancing_type, redundancy_level)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        config_id, source, dest, len(path_ids),
                        primary_path_id, json.dumps(backup_paths),
                        'active-active' if len(path_ids) > 1 else 'none',
                        'n+1' if len(path_ids) > 1 else 'none'
                    ))
                
                logger.info(f"✅ Created {len(path_groups)} path groups for config {config_id}")
            
            # 5. Create VLAN configurations
            logger.info("🏷️  Creating VLAN configurations...")
            
            for config_id in config_ids:
                # Get VLAN ID from bridge domain config
                cursor.execute("""
                    SELECT vlan_id FROM phase1_bridge_domain_config 
                    WHERE id = ?
                """, (config_id,))
                
                vlan_result = cursor.fetchone()
                if vlan_result and vlan_result[0]:
                    vlan_id = vlan_result[0]
                    
                    cursor.execute("""
                        INSERT INTO phase1_vlan_configs 
                        (config_id, vlan_id, vlan_type)
                        VALUES (?, ?, 'single')
                    """, (config_id, vlan_id))
                    
                    logger.info(f"✅ Created VLAN config for config {config_id}: VLAN {vlan_id}")
            
            # 6. Create confidence metrics
            logger.info("📈 Creating confidence metrics...")
            
            for config_id in config_ids:
                # Get confidence scores from related data
                cursor.execute("""
                    SELECT 
                        AVG(d.confidence_score) as device_confidence,
                        AVG(i.confidence_score) as interface_confidence,
                        AVG(p.confidence_score) as path_confidence
                    FROM phase1_bridge_domain_config c
                    JOIN phase1_topology_data t ON c.topology_id = t.id
                    LEFT JOIN phase1_device_info d ON d.topology_id = t.id
                    LEFT JOIN phase1_interface_info i ON i.topology_id = t.id
                    LEFT JOIN phase1_path_info p ON p.topology_id = t.id
                    WHERE c.id = ?
                """, (config_id,))
                
                result = cursor.fetchone()
                if result:
                    device_conf, interface_conf, path_conf = result
                    
                    # Calculate weighted overall confidence
                    weights = {'device': 0.30, 'interface': 0.30, 'path': 0.25, 'vlan': 0.15}
                    vlan_conf = 1.0  # Assume VLAN is known if config exists
                    
                    overall_conf = (
                        (device_conf or 0) * weights['device'] +
                        (interface_conf or 0) * weights['interface'] +
                        (path_conf or 0) * weights['path'] +
                        vlan_conf * weights['vlan']
                    )
                    
                    # Create confidence factors
                    confidence_factors = []
                    if device_conf:
                        confidence_factors.append({
                            'type': 'devices',
                            'score': device_conf,
                            'reason': 'Average device confidence',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    if interface_conf:
                        confidence_factors.append({
                            'type': 'interfaces',
                            'score': interface_conf,
                            'reason': 'Average interface confidence',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    if path_conf:
                        confidence_factors.append({
                            'type': 'paths',
                            'score': path_conf,
                            'reason': 'Average path confidence',
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    confidence_factors.append({
                        'type': 'vlan',
                        'score': vlan_conf,
                        'reason': 'VLAN configuration present',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    cursor.execute("""
                        INSERT INTO phase1_confidence_metrics 
                        (config_id, device_confidence, interface_confidence, 
                         path_confidence, vlan_confidence, overall_confidence, confidence_factors)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        config_id, device_conf or 0, interface_conf or 0,
                        path_conf or 0, vlan_conf, overall_conf, json.dumps(confidence_factors)
                    ))
                    
                    logger.info(f"✅ Created confidence metrics for config {config_id}: {overall_conf:.1%}")
            
            # 7. Update interface classifications
            logger.info("🔌 Updating interface classifications...")
            
            cursor.execute("""
                UPDATE phase1_interface_info 
                SET interface_type = 'subinterface',
                    parent_interface = SUBSTR(name, 1, INSTR(name, '.') - 1),
                    subinterface_id = SUBSTR(name, INSTR(name, '.') + 1)
                WHERE name LIKE '%.%'
            """)
            
            cursor.execute("""
                UPDATE phase1_interface_info 
                SET interface_type = 'bundle'
                WHERE name LIKE 'bundle-%' OR name LIKE 'port-channel%'
            """)
            
            logger.info("✅ Updated interface classifications")
            
            # 8. Update device roles
            logger.info("🖥️  Updating device roles...")
            
            cursor.execute("""
                UPDATE phase1_device_info 
                SET is_primary_source = 1
                WHERE device_role = 'source' AND device_type = 'leaf'
            """)
            
            logger.info("✅ Updated device roles")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Data migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate data: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify that the migration was successful"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            logger.info("🔍 Verifying migration...")
            
            # Check table existence
            tables = [
                'phase1_path_groups',
                'phase1_vlan_configs', 
                'phase1_confidence_metrics'
            ]
            
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    logger.error(f"❌ Table {table} not found")
                    return False
                logger.info(f"✅ Table {table} exists")
            
            # Check data counts
            cursor.execute("SELECT COUNT(*) FROM phase1_path_groups")
            path_groups_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM phase1_vlan_configs")
            vlan_configs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM phase1_confidence_metrics")
            confidence_metrics_count = cursor.fetchone()[0]
            
            logger.info(f"✅ Migration verification:")
            logger.info(f"  • Path Groups: {path_groups_count}")
            logger.info(f"  • VLAN Configs: {vlan_configs_count}")
            logger.info(f"  • Confidence Metrics: {confidence_metrics_count}")
            
            # Check that destinations are properly consolidated
            cursor.execute("SELECT COUNT(*) FROM phase1_bridge_domain_config WHERE destinations != '[]'")
            configs_with_destinations = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM phase1_destinations")
            legacy_destinations = cursor.fetchone()[0]
            
            logger.info(f"  • Configs with consolidated destinations: {configs_with_destinations}")
            logger.info(f"  • Legacy destination records: {legacy_destinations}")
            
            conn.close()
            
            logger.info("✅ Migration verification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        try:
            logger.info("🚀 Starting database migration to optimized structure...")
            
            # Step 1: Create backup
            if not self.create_backup():
                logger.error("❌ Backup creation failed. Aborting migration.")
                return False
            
            # Step 2: Add new tables and fields
            if not self.add_new_tables():
                logger.error("❌ Failed to add new tables. Migration aborted.")
                return False
            
            # Step 3: Migrate existing data
            if not self.migrate_existing_data():
                logger.error("❌ Failed to migrate data. Migration aborted.")
                return False
            
            # Step 4: Verify migration
            if not self.verify_migration():
                logger.error("❌ Migration verification failed.")
                return False
            
            logger.info("🎉 Database migration completed successfully!")
            logger.info(f"📁 Backup saved at: {self.backup_path}")
            logger.info("💡 You can now use the optimized database structure")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            logger.error("🔄 You may need to restore from backup and try again")
            return False
    
    def rollback(self) -> bool:
        """Rollback migration by restoring from backup"""
        try:
            if not Path(self.backup_path).exists():
                logger.error(f"❌ Backup not found: {self.backup_path}")
                return False
            
            import shutil
            shutil.copy2(self.backup_path, self.db_path)
            logger.info(f"✅ Database restored from backup: {self.backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False


def main():
    """Main migration function"""
    try:
        # Check if database exists
        db_path = 'instance/lab_automation.db'
        if not Path(db_path).exists():
            print(f"❌ Database not found: {db_path}")
            print("Please run this script from the lab_automation directory")
            return
        
        # Create migration instance
        migration = DatabaseMigrationV2(db_path)
        
        # Run migration
        success = migration.run_migration()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("The database now has the optimized structure with:")
            print("  • Consolidated destinations (JSON)")
            print("  • Path groups for logical path management")
            print("  • Centralized VLAN configuration")
            print("  • Detailed confidence metrics")
            print("  • Enhanced interface classification")
            print("  • Device role clarification")
        else:
            print("\n❌ Migration failed!")
            print("You can restore from backup using:")
            print(f"  migration.rollback()")
        
    except Exception as e:
        print(f"❌ Migration script failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
