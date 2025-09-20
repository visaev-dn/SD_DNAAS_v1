#!/usr/bin/env python3
"""
Database Constraints Migration for Service Signature Deduplication
Adds proper constraints, indexes, and data integrity rules
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ConstraintsMigration:
    """
    Handles database constraints migration for service signature-based deduplication
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def apply_constraints_migration(self) -> bool:
        """
        Apply database constraints migration
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            self.logger.info("🔧 Starting database constraints migration...")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Step 1: Create indexes for performance
                self._create_indexes(cursor)
                
                # Step 2: Add data integrity checks
                self._add_integrity_checks(cursor)
                
                # Step 3: Verify constraints
                verification_result = self._verify_constraints(cursor)
                
                if verification_result:
                    conn.commit()
                    self.logger.info("✅ Database constraints migration completed successfully")
                    return True
                else:
                    conn.rollback()
                    self.logger.error("❌ Database constraints migration verification failed")
                    return False
                    
        except Exception as e:
            self.logger.error(f"❌ Database constraints migration failed: {e}")
            return False
    
    def _create_indexes(self, cursor: sqlite3.Cursor):
        """Create performance indexes"""
        self.logger.info("📊 Creating performance indexes...")
        
        # Index on service_signature for deduplication queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_service_signature 
            ON phase1_topology_data(service_signature);
        """)
        
        # Index on discovery_session_id for session queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_discovery_session_id 
            ON phase1_topology_data(discovery_session_id);
        """)
        
        # Index on first_discovered_at for temporal queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_first_discovered_at 
            ON phase1_topology_data(first_discovered_at);
        """)
        
        # Composite index for service signature + session tracking
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signature_session 
            ON phase1_topology_data(service_signature, discovery_session_id);
        """)
        
        # Index on signature_classification for type-based queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_signature_classification 
            ON phase1_topology_data(signature_classification);
        """)
        
        self.logger.info("✅ Performance indexes created")
    
    def _add_integrity_checks(self, cursor: sqlite3.Cursor):
        """Add data integrity constraints"""
        self.logger.info("🔒 Adding data integrity constraints...")
        
        # Note: SQLite doesn't support adding constraints to existing tables
        # We'll implement integrity through triggers and validation functions
        
        # Trigger to ensure service_signature uniqueness
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS ensure_service_signature_unique 
            BEFORE INSERT ON phase1_topology_data
            WHEN NEW.service_signature IS NOT NULL
            BEGIN
                SELECT CASE
                    WHEN (SELECT COUNT(*) FROM phase1_topology_data 
                          WHERE service_signature = NEW.service_signature) > 0
                    THEN RAISE(FAIL, 'Service signature must be unique')
                END;
            END;
        """)
        
        # Trigger to validate service signature format
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS validate_service_signature_format 
            BEFORE INSERT ON phase1_topology_data
            WHEN NEW.service_signature IS NOT NULL
            BEGIN
                SELECT CASE
                    WHEN LENGTH(NEW.service_signature) < 5 
                    THEN RAISE(FAIL, 'Service signature too short')
                    WHEN NEW.service_signature NOT LIKE '%_%'
                    THEN RAISE(FAIL, 'Service signature invalid format')
                END;
            END;
        """)
        
        # Trigger to auto-set first_discovered_at
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS auto_set_first_discovered 
            BEFORE INSERT ON phase1_topology_data
            WHEN NEW.first_discovered_at IS NULL
            BEGIN
                UPDATE phase1_topology_data SET first_discovered_at = datetime('now')
                WHERE rowid = NEW.rowid;
            END;
        """)
        
        self.logger.info("✅ Data integrity constraints added")
    
    def _verify_constraints(self, cursor: sqlite3.Cursor) -> bool:
        """Verify that constraints are working"""
        self.logger.info("🔍 Verifying database constraints...")
        
        try:
            # Check indexes exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%';
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_service_signature',
                'idx_discovery_session_id', 
                'idx_first_discovered_at',
                'idx_signature_session',
                'idx_signature_classification'
            ]
            
            missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
            if missing_indexes:
                self.logger.error(f"❌ Missing indexes: {missing_indexes}")
                return False
            
            # Check triggers exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='trigger' AND name LIKE '%service_signature%';
            """)
            triggers = [row[0] for row in cursor.fetchall()]
            
            if len(triggers) < 2:  # Should have at least uniqueness and format triggers
                self.logger.error(f"❌ Missing triggers. Found: {triggers}")
                return False
            
            self.logger.info("✅ Database constraints verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Constraint verification failed: {e}")
            return False
    
    def get_constraint_status(self) -> dict:
        """Get current constraint and index status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get indexes
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name LIKE 'idx_%';
                """)
                indexes = [row[0] for row in cursor.fetchall()]
                
                # Get triggers
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='trigger';
                """)
                triggers = [row[0] for row in cursor.fetchall()]
                
                # Get table info
                cursor.execute("PRAGMA table_info(phase1_topology_data);")
                columns = [row[1] for row in cursor.fetchall()]
                
                return {
                    'indexes': indexes,
                    'triggers': triggers,
                    'columns': columns,
                    'service_signature_supported': 'service_signature' in columns
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get constraint status: {e}")
            return {}


def apply_database_constraints_migration(db_path: str = None) -> bool:
    """
    Apply database constraints migration
    
    Args:
        db_path: Path to database file. If None, uses default Phase 1 database
        
    Returns:
        True if migration successful
    """
    if db_path is None:
        # Use default Phase 1 database path
        db_path = Path("instance/lab_automation.db")
    else:
        db_path = Path(db_path)
    
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    migration = ConstraintsMigration(db_path)
    return migration.apply_constraints_migration()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🔧 Database Constraints Migration")
    print("=" * 40)
    
    # Apply migration
    success = apply_database_constraints_migration()
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
