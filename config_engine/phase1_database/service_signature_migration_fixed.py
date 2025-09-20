#!/usr/bin/env python3
"""
Service Signature Database Migration - Fixed SQLAlchemy Version
Adds service signature support to Phase 1 database schema
"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def upgrade_schema_for_service_signatures(engine):
    """
    Add service signature columns to existing Phase1TopologyData table
    
    This migration adds:
    - service_signature: Unique identifier for deduplication
    - discovery_session_id: Track discovery runs
    - discovery_count: Number of times this service was discovered
    - first_discovered_at: When service was first seen
    - signature_confidence: Confidence in signature generation
    - signature_classification: Type of service signature
    """
    logger.info("🔧 Starting service signature schema migration...")
    
    try:
        # Add new columns to Phase1TopologyData
        with engine.connect() as connection:
            # Use transaction for safety
            with connection.begin():
                # Add service signature column (unique identifier)
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN service_signature VARCHAR(500) NULL
                    """))
                    logger.info("✅ Added service_signature column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ service_signature column already exists")
                    else:
                        raise e
                
                # Add discovery session ID column
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN discovery_session_id VARCHAR(100) NULL
                    """))
                    logger.info("✅ Added discovery_session_id column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ discovery_session_id column already exists")
                    else:
                        raise e
                
                # Add discovery count column
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN discovery_count INTEGER DEFAULT 1
                    """))
                    logger.info("✅ Added discovery_count column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ discovery_count column already exists")
                    else:
                        raise e
                
                # Add first discovered timestamp
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN first_discovered_at DATETIME NULL
                    """))
                    logger.info("✅ Added first_discovered_at column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ first_discovered_at column already exists")
                    else:
                        raise e
                
                # Add signature confidence column
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN signature_confidence REAL DEFAULT 1.0
                    """))
                    logger.info("✅ Added signature_confidence column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ signature_confidence column already exists")
                    else:
                        raise e
                
                # Add signature classification column
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN signature_classification VARCHAR(50) NULL
                    """))
                    logger.info("✅ Added signature_classification column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ signature_classification column already exists")
                    else:
                        raise e
                
                # Add data sources tracking column (as TEXT for SQLite compatibility)
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN data_sources TEXT NULL
                    """))
                    logger.info("✅ Added data_sources column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ data_sources column already exists")
                    else:
                        raise e
        
        logger.info("🎯 Service signature schema migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service signature schema migration failed: {e}")
        return False


def verify_schema_migration(engine):
    """Verify that the schema migration was successful"""
    try:
        with engine.connect() as connection:
            # Check if all new columns exist
            result = connection.execute(text("PRAGMA table_info(phase1_topology_data);"))
            columns = [row[1] for row in result.fetchall()]
            
            expected_columns = [
                'service_signature',
                'discovery_session_id', 
                'discovery_count',
                'first_discovered_at',
                'signature_confidence',
                'signature_classification',
                'data_sources'
            ]
            
            missing_columns = [col for col in expected_columns if col not in columns]
            
            if missing_columns:
                logger.error(f"❌ Schema verification failed. Missing columns: {missing_columns}")
                return False
            else:
                logger.info("✅ Schema verification passed. All service signature columns present.")
                return True
                
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from sqlalchemy import create_engine
    from pathlib import Path
    
    # Use default database path
    db_path = Path("instance/lab_automation.db")
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("🔧 Service Signature Schema Migration")
    print("=" * 45)
    
    # Apply migration
    success = upgrade_schema_for_service_signatures(engine)
    
    if success:
        # Verify migration
        verified = verify_schema_migration(engine)
        if verified:
            print("✅ Migration and verification completed successfully!")
        else:
            print("❌ Migration completed but verification failed!")
    else:
        print("❌ Migration failed!")
