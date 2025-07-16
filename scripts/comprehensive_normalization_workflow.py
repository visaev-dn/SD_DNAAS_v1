#!/usr/bin/env python3
"""
Comprehensive Normalization Workflow
Re-runs all discovery and mapping with normalization properly integrated.
This script ensures the bridge domain builder uses normalized topology data.
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_engine.device_name_normalizer import normalizer
from config_engine.enhanced_topology_discovery import enhanced_discovery

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveNormalizationWorkflow:
    """Comprehensive workflow to re-run all discovery with normalization."""
    
    def __init__(self):
        self.topology_dir = Path("topology")
        self.qa_dir = Path("QA")
        self.backup_dir = Path("backups")
        
        # Create directories
        self.topology_dir.mkdir(exist_ok=True)
        self.qa_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def backup_existing_data(self):
        """Backup existing topology and QA data."""
        logger.info("📦 Backing up existing data...")
        
        backup_name = f"backup_{self.timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        # Backup topology files
        topology_files = [
            "complete_topology_v2.json",
            "device_summary_v2.yaml", 
            "bundle_mapping_v2.yaml",
            "device_status.json",
            "collection_summary.txt"
        ]
        
        for file_name in topology_files:
            file_path = self.topology_dir / file_name
            if file_path.exists():
                backup_file = backup_path / file_name
                with open(file_path, 'r') as src, open(backup_file, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"  ✓ Backed up {file_name}")
        
        # Backup QA files
        qa_files = [
            "comprehensive_bridge_domain_test_report.txt",
            "comprehensive_bridge_domain_test_results.json"
        ]
        
        for file_name in qa_files:
            file_path = self.qa_dir / file_name
            if file_path.exists():
                backup_file = backup_path / file_name
                with open(file_path, 'r') as src, open(backup_file, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"  ✓ Backed up {file_name}")
        
        logger.info(f"📦 Backup completed: {backup_path}")
        return backup_path
    
    def run_probe_and_parse(self):
        """Run probe+parse to collect fresh data."""
        logger.info("🔍 Running probe+parse LACP+LLDP...")
        
        try:
            # Run the collect_lacp_xml.py script with --phase both
            result = subprocess.run([
                sys.executable, "scripts/collect_lacp_xml.py", "--phase", "both"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ Probe+parse completed successfully")
                return True
            else:
                logger.error(f"❌ Probe+parse failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("❌ Probe+parse timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Probe+parse failed with exception: {e}")
            return False
    
    def run_enhanced_topology_discovery(self):
        """Run enhanced topology discovery with normalization."""
        logger.info("🔧 Running enhanced topology discovery...")
        
        try:
            # Run enhanced topology discovery
            enhanced_topology = enhanced_discovery.discover_topology_with_normalization()
            
            if enhanced_topology:
                logger.info("✅ Enhanced topology discovery completed")
                
                # Show normalization statistics
                stats = enhanced_discovery.export_normalization_data()
                logger.info(f"📊 Normalization Statistics:")
                logger.info(f"  • Device mappings: {len(stats['device_mappings'])}")
                logger.info(f"  • Spine mappings: {len(stats['spine_mappings'])}")
                logger.info(f"  • Issues found: {len(stats['issues_found'].get('missing_spine_connections', []))}")
                logger.info(f"  • Fixes applied: {len(stats['fixes_applied'].get('spine_mappings', []))}")
                
                return True
            else:
                logger.error("❌ Enhanced topology discovery failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Enhanced topology discovery failed with exception: {e}")
            return False
    
    def update_bridge_domain_builder(self):
        """Update bridge domain builder to use enhanced topology."""
        logger.info("🔧 Updating bridge domain builder...")
        
        # The bridge domain builder should automatically use enhanced topology
        # if it exists. Let's verify the enhanced topology file exists.
        enhanced_topology_file = self.topology_dir / "enhanced_topology.json"
        
        if enhanced_topology_file.exists():
            logger.info("✅ Enhanced topology file found")
            
            # Load and validate enhanced topology
            with open(enhanced_topology_file, 'r') as f:
                enhanced_topology = json.load(f)
            
            devices = enhanced_topology.get('devices', {})
            logger.info(f"📊 Enhanced topology contains {len(devices)} devices")
            
            # Show some normalization examples
            normalized_count = 0
            for device_name, device_info in devices.items():
                if device_name != device_info.get('original_name', device_name):
                    normalized_count += 1
                    if normalized_count <= 5:  # Show first 5 examples
                        original = device_info.get('original_name', device_name)
                        logger.info(f"  • {original} -> {device_name}")
            
            if normalized_count > 5:
                logger.info(f"  • ... and {normalized_count - 5} more devices normalized")
            
            return True
        else:
            logger.error("❌ Enhanced topology file not found")
            return False
    
    def run_qa_tests(self):
        """Run QA tests to validate the normalization."""
        logger.info("🧪 Running QA tests...")
        
        try:
            # Set PYTHONPATH for QA tests
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            result = subprocess.run([
                sys.executable, "QA/advanced_bridge_domain_tester.py",
                "--random-iterations", "20",
                "--stress-iterations", "10"
            ], env=env, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info("✅ QA tests completed successfully")
                
                # Parse and display results
                self._display_qa_results()
                return True
            else:
                logger.error(f"❌ QA tests failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ QA tests timed out")
            return False
        except Exception as e:
            logger.error(f"❌ QA tests failed with exception: {e}")
            return False
    
    def _display_qa_results(self):
        """Display QA test results."""
        qa_report_file = self.qa_dir / "comprehensive_bridge_domain_test_report.txt"
        
        if qa_report_file.exists():
            with open(qa_report_file, 'r') as f:
                content = f.read()
            
            # Extract success rate
            if "Overall Success Rate:" in content:
                lines = content.split('\n')
                for line in lines:
                    if "Overall Success Rate:" in line:
                        success_rate = line.split(":")[-1].strip()
                        logger.info(f"📊 QA Test Results: {success_rate}")
                        break
    
    def generate_workflow_report(self):
        """Generate comprehensive workflow report."""
        logger.info("📋 Generating workflow report...")
        
        report = {
            "workflow_timestamp": self.timestamp,
            "workflow_status": "completed",
            "steps_completed": [],
            "normalization_stats": {},
            "qa_results": {},
            "files_generated": []
        }
        
        # Check generated files
        expected_files = [
            "topology/enhanced_topology.json",
            "topology/enhanced_topology_summary.json", 
            "topology/device_mappings.json",
            "QA/comprehensive_bridge_domain_test_report.txt",
            "QA/comprehensive_bridge_domain_test_results.json"
        ]
        
        for file_path in expected_files:
            if Path(file_path).exists():
                report["files_generated"].append(file_path)
        
        # Load normalization stats
        enhanced_summary_file = self.topology_dir / "enhanced_topology_summary.json"
        if enhanced_summary_file.exists():
            with open(enhanced_summary_file, 'r') as f:
                report["normalization_stats"] = json.load(f)
        
        # Save report
        report_file = f"workflow_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Workflow report saved: {report_file}")
        return report
    
    def run_complete_workflow(self):
        """Run the complete normalization workflow."""
        logger.info("🚀 Starting Comprehensive Normalization Workflow")
        logger.info("=" * 60)
        
        steps = [
            ("Backup existing data", self.backup_existing_data),
            ("Run probe+parse", self.run_probe_and_parse),
            ("Run enhanced topology discovery", self.run_enhanced_topology_discovery),
            ("Update bridge domain builder", self.update_bridge_domain_builder),
            ("Run QA tests", self.run_qa_tests),
            ("Generate workflow report", self.generate_workflow_report)
        ]
        
        completed_steps = []
        
        for step_name, step_func in steps:
            logger.info(f"\n🔄 Step: {step_name}")
            logger.info("-" * 40)
            
            try:
                success = step_func()
                if success:
                    completed_steps.append(step_name)
                    logger.info(f"✅ {step_name} completed successfully")
                else:
                    logger.error(f"❌ {step_name} failed")
                    logger.error("Workflow stopped due to failure")
                    return False
            except Exception as e:
                logger.error(f"❌ {step_name} failed with exception: {e}")
                logger.error("Workflow stopped due to exception")
                return False
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Comprehensive Normalization Workflow Completed!")
        logger.info("=" * 60)
        logger.info(f"✅ Completed steps: {len(completed_steps)}/{len(steps)}")
        
        for step in completed_steps:
            logger.info(f"  ✓ {step}")
        
        return True

def main():
    """Main function."""
    workflow = ComprehensiveNormalizationWorkflow()
    
    try:
        success = workflow.run_complete_workflow()
        
        if success:
            print("\n🎉 Workflow completed successfully!")
            print("📁 Check generated files in topology/ and QA/ directories")
            print("📋 Check workflow report for detailed statistics")
        else:
            print("\n❌ Workflow failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Workflow failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 