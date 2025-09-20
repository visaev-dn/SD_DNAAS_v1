#!/usr/bin/env python3
"""
Final Schema Migration for Service Signature Deduplication
Adds remaining missing columns to complete the schema
"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


def complete_schema_migration(engine):
    """
    Add remaining missing columns to complete the schema
    """
    logger.info("🔧 Starting final schema migration...")
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                # Add missing review columns
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN review_required BOOLEAN DEFAULT 0
                    """))
                    logger.info("✅ Added review_required column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ review_required column already exists")
                    else:
                        raise e
                
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN review_reason TEXT NULL
                    """))
                    logger.info("✅ Added review_reason column")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ review_reason column already exists")
                    else:
                        raise e
                
                # Add JSON columns for storing complex data structures
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN devices TEXT NULL
                    """))
                    logger.info("✅ Added devices column (JSON as TEXT)")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ devices column already exists")
                    else:
                        raise e
                
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN interfaces TEXT NULL
                    """))
                    logger.info("✅ Added interfaces column (JSON as TEXT)")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ interfaces column already exists")
                    else:
                        raise e
                
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN paths TEXT NULL
                    """))
                    logger.info("✅ Added paths column (JSON as TEXT)")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ paths column already exists")
                    else:
                        raise e
                
                try:
                    connection.execute(text("""
                        ALTER TABLE phase1_topology_data 
                        ADD COLUMN bridge_domain_configs TEXT NULL
                    """))
                    logger.info("✅ Added bridge_domain_configs column (JSON as TEXT)")
                except Exception as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info("⚠️ bridge_domain_configs column already exists")
                    else:
                        raise e
        
        logger.info("🎯 Final schema migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Final schema migration failed: {e}")
        return False


def verify_final_schema(engine):
    """Verify the final schema is complete"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("PRAGMA table_info(phase1_topology_data);"))
            columns = [row[1] for row in result.fetchall()]
            
            required_columns = [
                'service_signature',
                'discovery_session_id', 
                'discovery_count',
                'first_discovered_at',
                'signature_confidence',
                'signature_classification',
                'data_sources',
                'review_required',
                'review_reason',
                'devices',
                'interfaces', 
                'paths',
                'bridge_domain_configs'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                logger.error(f"❌ Final schema verification failed. Missing columns: {missing_columns}")
                return False
            else:
                logger.info("✅ Final schema verification passed. All required columns present.")
                return True
                
    except Exception as e:
        logger.error(f"❌ Final schema verification failed: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from sqlalchemy import create_engine
    from pathlib import Path
    
    # Use default database path
    db_path = Path("instance/lab_automation.db")
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("🔧 Final Schema Migration for Service Signature Deduplication")
    print("=" * 65)
    
    # Apply migration
    success = complete_schema_migration(engine)
    
    if success:
        # Verify migration
        verified = verify_final_schema(engine)
        if verified:
            print("✅ Final migration and verification completed successfully!")
        else:
            print("❌ Final migration completed but verification failed!")
    else:
        print("❌ Final migration failed!")
