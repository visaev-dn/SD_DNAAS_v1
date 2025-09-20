#!/usr/bin/env python3
"""
Add database constraints to prevent duplicate path segments.
This script adds unique constraints to the phase1_path_segments table.
"""

import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_path_segment_constraints(db_path: str = "instance/lab_automation.db"):
    """
    Add unique constraints to prevent duplicate path segments.
    
    Args:
        db_path: Path to the SQLite database
    """
    
    if not Path(db_path).exists():
        logger.error(f"❌ Database not found: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🔧 Adding path segment constraints to prevent duplicates...")
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(phase1_path_segments)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"Current columns: {column_names}")
        
        # Check existing indexes
        cursor.execute("PRAGMA index_list(phase1_path_segments)")
        indexes = cursor.fetchall()
        index_names = [idx[1] for idx in indexes]
        
        logger.info(f"Current indexes: {index_names}")
        
        # Add unique constraint to prevent duplicates
        # This will create a unique index on the combination of fields that should be unique
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX idx_unique_path_segment 
                ON phase1_path_segments (
                    path_id, 
                    source_device, 
                    dest_device, 
                    source_interface, 
                    dest_interface
                )
            """)
            logger.info("✅ Added unique constraint: idx_unique_path_segment")
        except sqlite3.OperationalError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.warning("⚠️  Unique constraint already exists")
            else:
                logger.error(f"❌ Failed to add unique constraint: {e}")
                return False
        
        # Add additional indexes for performance
        try:
            cursor.execute("""
                CREATE INDEX idx_path_segments_path_id 
                ON phase1_path_segments (path_id)
            """)
            logger.info("✅ Added performance index: idx_path_segments_path_id")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                logger.info("ℹ️  Performance index already exists")
            else:
                logger.warning(f"⚠️  Could not add performance index: {e}")
        
        try:
            cursor.execute("""
                CREATE INDEX idx_path_segments_devices 
                ON phase1_path_segments (source_device, dest_device)
            """)
            logger.info("✅ Added performance index: idx_path_segments_devices")
        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                logger.info("ℹ️  Performance index already exists")
            else:
                logger.warning(f"⚠️  Could not add performance index: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the new constraint
        cursor.execute("PRAGMA index_list(phase1_path_segments)")
        new_indexes = cursor.fetchall()
        new_index_names = [idx[1] for idx in new_indexes]
        
        logger.info(f"Updated indexes: {new_index_names}")
        
        # Test the constraint by trying to insert a duplicate
        logger.info("🧪 Testing unique constraint...")
        
        # Get a sample path_id
        cursor.execute("SELECT id FROM phase1_path_info LIMIT 1")
        sample_path_id = cursor.fetchone()
        
        if sample_path_id:
            path_id = sample_path_id[0]
            
            # Try to insert a duplicate segment
            try:
                cursor.execute("""
                    INSERT INTO phase1_path_segments (
                        path_id, source_device, dest_device, 
                        source_interface, dest_interface, segment_type,
                        connection_type, discovered_at, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
                """, (path_id, "TEST-SOURCE", "TEST-DEST", "TEST-IF1", "TEST-IF2", 
                      "test", "direct", 0.9))
                
                # If we get here, the constraint didn't work
                logger.warning("⚠️  Unique constraint test failed - duplicate inserted")
                cursor.execute("DELETE FROM phase1_path_segments WHERE source_device = 'TEST-SOURCE'")
                conn.commit()
                
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    logger.info("✅ Unique constraint working correctly - prevented duplicate")
                else:
                    logger.warning(f"⚠️  Unexpected constraint error: {e}")
        
        logger.info("🎉 Path segment constraints added successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to add constraints: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def cleanup_duplicate_segments(db_path: str = "instance/lab_automation.db"):
    """
    Clean up existing duplicate path segments before adding constraints.
    
    Args:
        db_path: Path to the SQLite database
    """
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("🧹 Cleaning up existing duplicate path segments...")
        
        # Find duplicate segments
        cursor.execute("""
            SELECT path_id, source_device, dest_device, source_interface, dest_interface, COUNT(*) as count
            FROM phase1_path_segments
            GROUP BY path_id, source_device, dest_device, source_interface, dest_interface
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            logger.info("✅ No duplicate segments found")
            return True
        
        logger.info(f"Found {len(duplicates)} groups with duplicates")
        
        total_removed = 0
        
        for duplicate in duplicates:
            path_id, source, dest, source_if, dest_if, count = duplicate
            
            if count > 1:
                # Keep the first segment, remove the rest
                cursor.execute("""
                    DELETE FROM phase1_path_segments 
                    WHERE path_id = ? AND source_device = ? AND dest_device = ? 
                          AND source_interface = ? AND dest_interface = ?
                    AND id NOT IN (
                        SELECT MIN(id) FROM phase1_path_segments 
                        WHERE path_id = ? AND source_device = ? AND dest_device = ? 
                              AND source_interface = ? AND dest_interface = ?
                    )
                """, (path_id, source, dest, source_if, dest_if,
                      path_id, source, dest, source_if, dest_if))
                
                removed = cursor.rowcount
                total_removed += removed
                
                logger.info(f"   Removed {removed} duplicates for path {path_id}: {source} → {dest}")
        
        conn.commit()
        logger.info(f"🧹 Cleanup complete: removed {total_removed} duplicate segments")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to cleanup duplicates: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("🚀 Starting path segment constraint addition...")
    
    # First cleanup existing duplicates
    if cleanup_duplicate_segments():
        # Then add constraints
        if add_path_segment_constraints():
            logger.info("🎉 All operations completed successfully!")
        else:
            logger.error("❌ Failed to add constraints")
    else:
        logger.error("❌ Failed to cleanup duplicates")
