#!/usr/bin/env python3
"""
Service Signature Database Migration
Adds service signature support to Phase 1 database schema
"""

import logging
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, Index
from datetime import datetime

from config_engine.phase1_database.models import Base, Phase1TopologyData

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
    - review_required: Flag for manual review
    - review_reason: Reason for manual review
    """
    
    logger.info("🔄 Starting service signature schema migration...")
    
    try:
        # Add new columns to Phase1TopologyData
        with engine.connect() as connection:
            # Add service signature column (unique identifier)
            try:
                from sqlalchemy import text
                connection.execute(text("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN service_signature VARCHAR(500) NULL
                """))
                logger.info("✅ Added service_signature column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ service_signature column already exists")
                else:
                    raise
            
            # Add discovery tracking columns
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN discovery_session_id VARCHAR(100) NULL
                """)
                logger.info("✅ Added discovery_session_id column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ discovery_session_id column already exists")
                else:
                    raise
            
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN discovery_count INTEGER DEFAULT 1
                """)
                logger.info("✅ Added discovery_count column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ discovery_count column already exists")
                else:
                    raise
            
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN first_discovered_at DATETIME NULL
                """)
                logger.info("✅ Added first_discovered_at column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ first_discovered_at column already exists")
                else:
                    raise
            
            # Add signature metadata columns
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN signature_confidence FLOAT DEFAULT 0.0
                """)
                logger.info("✅ Added signature_confidence column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ signature_confidence column already exists")
                else:
                    raise
            
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN signature_classification VARCHAR(100) NULL
                """)
                logger.info("✅ Added signature_classification column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ signature_classification column already exists")
                else:
                    raise
            
            # Add review flags
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN review_required BOOLEAN DEFAULT FALSE
                """)
                logger.info("✅ Added review_required column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ review_required column already exists")
                else:
                    raise
            
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN review_reason VARCHAR(500) NULL
                """)
                logger.info("✅ Added review_reason column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ review_reason column already exists")
                else:
                    raise
            
            # Add data sources tracking
            try:
                connection.execute("""
                    ALTER TABLE phase1_topology_data 
                    ADD COLUMN data_sources JSON NULL
                """)
                logger.info("✅ Added data_sources column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("⚠️ data_sources column already exists")
                else:
                    raise
            
            # Create unique index on service_signature (for deduplication)
            try:
                connection.execute("""
                    CREATE UNIQUE INDEX idx_service_signature 
                    ON phase1_topology_data(service_signature)
                    WHERE service_signature IS NOT NULL
                """)
                logger.info("✅ Created unique index on service_signature")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("⚠️ service_signature index already exists")
                else:
                    raise
            
            # Create index on discovery_session_id
            try:
                connection.execute("""
                    CREATE INDEX idx_discovery_session 
                    ON phase1_topology_data(discovery_session_id)
                """)
                logger.info("✅ Created index on discovery_session_id")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("⚠️ discovery_session_id index already exists")
                else:
                    raise
            
            # Create index on review_required
            try:
                connection.execute("""
                    CREATE INDEX idx_review_required 
                    ON phase1_topology_data(review_required)
                    WHERE review_required = TRUE
                """)
                logger.info("✅ Created index on review_required")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info("⚠️ review_required index already exists")
                else:
                    raise
            
            connection.commit()
            
        logger.info("🎉 Service signature schema migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema migration failed: {e}")
        raise


def backfill_service_signatures(database_manager):
    """
    Backfill service signatures for existing topology data
    
    This will:
    1. Generate service signatures for existing topologies
    2. Identify potential duplicates
    3. Queue problematic topologies for review
    """
    
    logger.info("🔄 Starting service signature backfill...")
    
    from config_engine.service_signature import ServiceSignatureGenerator
    
    generator = ServiceSignatureGenerator()
    processed = 0
    signatures_generated = 0
    review_queued = 0
    
    try:
        # Get all existing topologies
        topologies = database_manager.get_all_topologies()
        total = len(topologies)
        
        logger.info(f"📊 Processing {total} existing topologies...")
        
        for topology in topologies:
            processed += 1
            
            try:
                # Generate service signature
                result = generator.generate_signature(topology)
                
                # Update topology with signature
                database_manager.update_topology_signature(
                    topology_id=topology.topology_id,
                    service_signature=result.signature,
                    signature_confidence=result.confidence,
                    signature_classification=result.classification,
                    first_discovered_at=topology.discovered_at,
                    discovery_count=1,
                    data_sources=[{
                        'discovery_run': 'backfill',
                        'scan_method': topology.scan_method,
                        'discovered_at': topology.discovered_at.isoformat()
                    }]
                )
                
                signatures_generated += 1
                
                if result.warning:
                    logger.warning(f"⚠️ {topology.bridge_domain_name}: {result.warning}")
                
            except ValueError as e:
                # Queue for review
                database_manager.mark_topology_for_review(
                    topology_id=topology.topology_id,
                    review_reason=str(e)
                )
                review_queued += 1
                logger.warning(f"🔍 Queued for review: {topology.bridge_domain_name} - {e}")
            
            # Progress reporting
            if processed % 100 == 0:
                logger.info(f"📈 Progress: {processed}/{total} ({processed/total*100:.1f}%)")
        
        # Get review queue summary
        review_items = generator.get_review_queue()
        
        logger.info("🎉 Service signature backfill completed!")
        logger.info(f"📊 Results:")
        logger.info(f"   • Processed: {processed} topologies")
        logger.info(f"   • Signatures generated: {signatures_generated}")
        logger.info(f"   • Queued for review: {review_queued}")
        logger.info(f"   • Success rate: {signatures_generated/processed*100:.1f}%")
        
        return {
            'processed': processed,
            'signatures_generated': signatures_generated,
            'review_queued': review_queued,
            'success_rate': signatures_generated/processed if processed > 0 else 0,
            'review_items': review_items
        }
        
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}")
        raise


def identify_duplicates_by_signature(database_manager):
    """
    Identify duplicate topologies using service signatures
    
    Returns statistics about duplicates found
    """
    
    logger.info("🔍 Identifying duplicates by service signature...")
    
    try:
        with database_manager.SessionLocal() as session:
            # Query for duplicate signatures
            duplicate_query = """
                SELECT service_signature, COUNT(*) as count, 
                       GROUP_CONCAT(bridge_domain_name) as names,
                       GROUP_CONCAT(id) as topology_ids
                FROM phase1_topology_data 
                WHERE service_signature IS NOT NULL 
                GROUP BY service_signature 
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            """
            
            result = session.execute(duplicate_query)
            duplicates = result.fetchall()
            
            duplicate_stats = {
                'total_duplicate_groups': len(duplicates),
                'total_duplicate_topologies': sum(d[1] for d in duplicates),
                'largest_group_size': max((d[1] for d in duplicates), default=0),
                'duplicate_groups': []
            }
            
            for signature, count, names, topology_ids in duplicates:
                duplicate_stats['duplicate_groups'].append({
                    'service_signature': signature,
                    'duplicate_count': count,
                    'bridge_domain_names': names.split(',') if names else [],
                    'topology_ids': [int(id) for id in topology_ids.split(',') if id]
                })
            
            logger.info(f"📊 Duplicate Analysis Results:")
            logger.info(f"   • Duplicate groups: {duplicate_stats['total_duplicate_groups']}")
            logger.info(f"   • Total duplicates: {duplicate_stats['total_duplicate_topologies']}")
            logger.info(f"   • Largest group: {duplicate_stats['largest_group_size']} duplicates")
            
            return duplicate_stats
            
    except Exception as e:
        logger.error(f"❌ Duplicate identification failed: {e}")
        raise


if __name__ == "__main__":
    # CLI interface for migration
    import sys
    from config_engine.phase1_database import create_phase1_database_manager
    
    if len(sys.argv) < 2:
        print("Usage: python service_signature_migration.py [migrate|backfill|duplicates]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Initialize database manager
    db_manager = create_phase1_database_manager()
    
    if command == "migrate":
        upgrade_schema_for_service_signatures(db_manager.engine)
    elif command == "backfill":
        results = backfill_service_signatures(db_manager)
        print(f"Backfill completed: {results}")
    elif command == "duplicates":
        duplicates = identify_duplicates_by_signature(db_manager)
        print(f"Duplicates found: {duplicates}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
