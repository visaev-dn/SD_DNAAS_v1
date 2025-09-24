#!/usr/bin/env python3
"""
Data Synchronization Manager for Simplified Discovery
===================================================

Manages synchronization between JSON files and database to ensure
data consistency and provide a single source of truth.

Architecture: Database-First with JSON Backup Strategy
"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataSyncManager:
    """
    Manages data synchronization between JSON files and database.
    
    Strategy: Database-First with JSON Backup
    - Database is the primary source of truth
    - JSON files serve as backup and export format
    - Automatic synchronization on discovery runs
    """
    
    def __init__(self, db_path: str = "instance/lab_automation.db"):
        """Initialize sync manager"""
        self.db_path = db_path
        self.json_dir = Path("topology/simplified_discovery_results")
        self.json_dir.mkdir(exist_ok=True)
    
    def sync_discovery_data(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronize discovery results between database and JSON files.
        
        This is the main sync method called after each discovery run.
        """
        try:
            print("🔄 Starting data synchronization...")
            
            # Step 1: Save to database (primary source)
            db_result = self._save_to_database(discovery_results)
            
            # Step 2: Save to JSON (backup/export)
            json_result = self._save_to_json(discovery_results)
            
            # Step 3: Verify synchronization
            sync_status = self._verify_sync_status()
            
            return {
                "database_saved": db_result.get("saved_successfully", db_result.get("saved_count", 0)),
                "json_saved": json_result.get("saved_count", 0),
                "sync_status": sync_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}")
            return {"error": str(e)}
    
    def _save_to_database(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Save discovery results to database"""
        try:
            from database_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Check if discovery_results already has the correct structure
            if 'bridge_domains' in discovery_results:
                # Full JSON structure - pass as is
                result = db_manager.save_simplified_discovery_results(discovery_results)
            else:
                # Just bridge domains - wrap in expected structure
                wrapped_data = {'bridge_domains': discovery_results}
                result = db_manager.save_simplified_discovery_results(wrapped_data)
            
            print(f"✅ Database sync: {result['saved_successfully']}/{result['total_bridge_domains']} bridge domains")
            return result
            
        except Exception as e:
            logger.error(f"❌ Database save failed: {e}")
            return {"saved_count": 0, "error": str(e)}
    
    def _save_to_json(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Save discovery results to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bridge_domain_mapping_{timestamp}.json"
            filepath = self.json_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(discovery_results, f, indent=2)
            
            print(f"✅ JSON sync: Saved to {filename}")
            return {"saved_count": len(discovery_results), "filepath": str(filepath)}
            
        except Exception as e:
            logger.error(f"❌ JSON save failed: {e}")
            return {"saved_count": 0, "error": str(e)}
    
    def _verify_sync_status(self) -> Dict[str, Any]:
        """Verify that database and JSON files are in sync"""
        try:
            # Get database count
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM personal_bridge_domains 
                WHERE detection_method = 'simplified_workflow'
            ''')
            db_count = cursor.fetchone()[0]
            conn.close()
            
            # Get latest JSON count
            json_files = list(self.json_dir.glob("bridge_domain_mapping_*.json"))
            if json_files:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file, 'r') as f:
                    json_data = json.load(f)
                json_count = len(json_data)
            else:
                json_count = 0
            
            # Calculate sync status
            is_synced = (db_count == json_count)
            sync_percentage = (min(db_count, json_count) / max(db_count, json_count) * 100) if max(db_count, json_count) > 0 else 100
            
            return {
                "is_synced": is_synced,
                "database_count": db_count,
                "json_count": json_count,
                "sync_percentage": sync_percentage,
                "status": "✅ SYNCED" if is_synced else "⚠️ OUT OF SYNC"
            }
            
        except Exception as e:
            logger.error(f"❌ Sync verification failed: {e}")
            return {"is_synced": False, "error": str(e)}
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return self._verify_sync_status()
    
    def force_resync_from_database(self) -> Dict[str, Any]:
        """Force resync by exporting all database data to JSON"""
        try:
            print("🔄 Force resync from database...")
            
            # Get all data from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT bridge_domain_name, discovery_data, devices, topology_analysis
                FROM personal_bridge_domains 
                WHERE detection_method = 'simplified_workflow'
            ''')
            
            db_data = cursor.fetchall()
            conn.close()
            
            # Convert to JSON format
            json_data = {}
            for bd_name, discovery_data, devices, topology_analysis in db_data:
                try:
                    discovery_json = json.loads(discovery_data)
                    json_data[bd_name] = discovery_json
                except:
                    logger.warning(f"⚠️ Failed to parse data for {bd_name}")
            
            # Save to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bridge_domain_mapping_resync_{timestamp}.json"
            filepath = self.json_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            print(f"✅ Resync complete: {len(json_data)} bridge domains exported to {filename}")
            return {"exported_count": len(json_data), "filepath": str(filepath)}
            
        except Exception as e:
            logger.error(f"❌ Force resync failed: {e}")
            return {"error": str(e)}
    
    def clean_old_json_files(self, keep_latest: int = 5) -> Dict[str, Any]:
        """Clean old JSON files, keeping only the latest N files"""
        try:
            json_files = list(self.json_dir.glob("bridge_domain_mapping_*.json"))
            json_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            files_to_delete = json_files[keep_latest:]
            deleted_count = 0
            
            for file_path in files_to_delete:
                file_path.unlink()
                deleted_count += 1
            
            print(f"✅ Cleaned {deleted_count} old JSON files, kept {keep_latest} latest")
            return {"deleted_count": deleted_count, "kept_count": keep_latest}
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {"error": str(e)}
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get comprehensive data summary"""
        try:
            # Database summary
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM personal_bridge_domains 
                WHERE detection_method = 'simplified_workflow'
            ''')
            db_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT MAX(created_at) FROM personal_bridge_domains 
                WHERE detection_method = 'simplified_workflow'
            ''')
            last_db_update = cursor.fetchone()[0]
            
            conn.close()
            
            # JSON summary
            json_files = list(self.json_dir.glob("bridge_domain_mapping_*.json"))
            latest_json = max(json_files, key=lambda f: f.stat().st_mtime) if json_files else None
            json_size = sum(f.stat().st_size for f in json_files) / (1024 * 1024)  # MB
            
            return {
                "database": {
                    "count": db_count,
                    "last_update": last_db_update,
                    "path": self.db_path
                },
                "json_files": {
                    "count": len(json_files),
                    "latest_file": latest_json.name if latest_json else None,
                    "total_size_mb": round(json_size, 2),
                    "directory": str(self.json_dir)
                },
                "sync_status": self._verify_sync_status()
            }
            
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}")
            return {"error": str(e)}


def run_data_sync_lesson():
    """Interactive lesson on database management"""
    print("\n" + "📚" + "=" * 68)
    print("📚 DATABASE MANAGEMENT LESSON")
    print("📚" + "=" * 68)
    
    print("\n🎯 UNDERSTANDING YOUR DATA FLOW:")
    print("   1. YAML Config Files (Source)")
    print("      ↓")
    print("   2. Discovery System (Processing)")
    print("      ↓")
    print("   3. Database (Primary Storage) ← MAIN SOURCE")
    print("      ↓")
    print("   4. JSON Files (Backup/Export)")
    
    print("\n💡 KEY CONCEPTS:")
    print("   • Database = Your main filing cabinet")
    print("   • JSON Files = Backup copies")
    print("   • Sync = Keep them identical")
    print("   • Primary Source = Database (fastest for queries)")
    
    print("\n🔧 BEST PRACTICES:")
    print("   1. Always use database for queries and searches")
    print("   2. JSON files are for backup and sharing")
    print("   3. Run discovery → auto-sync to both")
    print("   4. Check sync status regularly")
    print("   5. Clean old JSON files periodically")
    
    print("\n✅ YOUR CURRENT SETUP:")
    sync_manager = DataSyncManager()
    summary = sync_manager.get_data_summary()
    
    if "error" not in summary:
        print(f"   • Database: {summary['database']['count']} bridge domains")
        print(f"   • JSON Files: {summary['json_files']['count']} files")
        print(f"   • Sync Status: {summary['sync_status']['status']}")
        print(f"   • Total Size: {summary['json_files']['total_size_mb']} MB")
    else:
        print(f"   ❌ Error getting summary: {summary['error']}")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Use the Enhanced Database (Option 7) for all queries")
    print("   2. JSON files are automatically created as backup")
    print("   3. Check sync status in Database Statistics")
    print("   4. Clean old files when needed")


if __name__ == "__main__":
    run_data_sync_lesson()
