#!/usr/bin/env python3
"""
Bridge Domain Validator - QA Tool
Automatically tests bridge domain builder with random leaf pairs and generates reports.
"""

import json
import yaml
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from collections import defaultdict, Counter

# Import the bridge domain builder
from config_engine.bridge_domain_builder import BridgeDomainBuilder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BridgeDomainValidator:
    """Validates bridge domain builder with automated testing."""
    
    def __init__(self, topology_dir: str = "topology", iterations: int = 20):
        """
        Initialize the validator.
        
        Args:
            topology_dir: Directory containing topology files
            iterations: Number of test iterations to run
        """
        self.topology_dir = Path(topology_dir)
        self.iterations = iterations
        self.builder = BridgeDomainBuilder(topology_dir)
        
        # Test results
        self.test_results = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'tests': [],
            'failure_reasons': Counter(),
            'device_success_rates': defaultdict(lambda: {'success': 0, 'total': 0}),
            'interface_success_rates': defaultdict(lambda: {'success': 0, 'total': 0}),
            'timestamp': datetime.now().isoformat()
        }
        
        # Load available leaves
        self.available_leaves = self.builder.get_available_leaves()
        self.unavailable_leaves = self.builder.get_unavailable_leaves()
        
        logger.info(f"Loaded {len(self.available_leaves)} available leaves")
        logger.info(f"Found {len(self.unavailable_leaves)} unavailable leaves")
    
    def get_random_leaf_pair(self) -> Tuple[str, str]:
        """Get a random pair of available leaves."""
        if len(self.available_leaves) < 2:
            raise ValueError("Need at least 2 available leaves for testing")
        
        # Get two different leaves
        leaf1, leaf2 = random.sample(self.available_leaves, 2)
        return leaf1, leaf2
    
    def get_random_interface(self, device: str) -> str:
        """Get a random interface for a device."""
        # Common interface patterns
        interface_patterns = [
            "ge100-0/0/1",
            "ge100-0/0/2", 
            "ge100-0/0/3",
            "ge100-0/0/4",
            "ge100-0/0/5",
            "ge100-0/0/6",
            "ge100-0/0/7",
            "ge100-0/0/8",
            "ge100-0/0/9",
            "ge100-0/0/10",
            "ge100-0/0/11",
            "ge100-0/0/12",
            "ge100-0/0/13",
            "ge100-0/0/14",
            "ge100-0/0/15",
            "ge100-0/0/16",
            "ge100-0/0/17",
            "ge100-0/0/18",
            "ge100-0/0/19",
            "ge100-0/0/20",
            "ge100-0/0/21",
            "ge100-0/0/22",
            "ge100-0/0/23",
            "ge100-0/0/24",
            "ge100-0/0/25",
            "ge100-0/0/26",
            "ge100-0/0/27",
            "ge100-0/0/28",
            "ge100-0/0/29",
            "ge100-0/0/30",
            "ge100-0/0/31",
            "ge100-0/0/32",
            "ge100-0/0/33",
            "ge100-0/0/34",
            "ge100-0/0/35",
            "ge100-0/0/36",
            "ge100-0/0/37",
            "ge100-0/0/38",
            "ge100-0/0/39",
            "ge100-0/0/40"
        ]
        
        return random.choice(interface_patterns)
    
    def run_single_test(self, test_id: int) -> Dict:
        """Run a single bridge domain test."""
        test_result = {
            'test_id': test_id,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'path_info': None,
            'devices_in_path': [],
            'config_commands': 0
        }
        
        try:
            # Get random leaf pair
            source_leaf, dest_leaf = self.get_random_leaf_pair()
            
            # Get random interfaces
            source_interface = self.get_random_interface(source_leaf)
            dest_interface = self.get_random_interface(dest_leaf)
            
            # Generate service name and VLAN
            service_name = f"test_service_{test_id}_{int(time.time())}"
            vlan_id = random.randint(100, 4094)
            
            test_result.update({
                'source_leaf': source_leaf,
                'dest_leaf': dest_leaf,
                'source_interface': source_interface,
                'dest_interface': dest_interface,
                'service_name': service_name,
                'vlan_id': vlan_id
            })
            
            # Build bridge domain configuration
            configs = self.builder.build_bridge_domain_config(
                service_name=service_name,
                vlan_id=vlan_id,
                source_leaf=source_leaf,
                source_port=source_interface,
                dest_leaf=dest_leaf,
                dest_port=dest_interface
            )
            
            if configs:
                # Test successful
                test_result['success'] = True
                test_result['config_commands'] = sum(len(config) for config in configs.values())
                test_result['devices_in_path'] = list(configs.keys())
                
                # Get path information
                path = self.builder.calculate_path(source_leaf, dest_leaf)
                if path:
                    test_result['path_info'] = {
                        'is_2_tier': path.get('superspine') is None,
                        'source_spine': path.get('source_spine'),
                        'superspine': path.get('superspine'),
                        'dest_spine': path.get('dest_spine'),
                        'segments': len(path.get('segments', []))
                    }
                
                logger.info(f"Test {test_id}: SUCCESS - {source_leaf} -> {dest_leaf} ({len(configs)} devices)")
            else:
                # Test failed
                test_result['success'] = False
                test_result['error'] = "No configuration generated"
                logger.warning(f"Test {test_id}: FAILED - {source_leaf} -> {dest_leaf} (no config)")
                
        except Exception as e:
            # Test failed with exception
            test_result['success'] = False
            test_result['error'] = str(e)
            logger.error(f"Test {test_id}: ERROR - {source_leaf} -> {dest_leaf}: {e}")
        
        return test_result
    
    def run_validation_tests(self) -> Dict:
        """Run the complete validation test suite."""
        logger.info(f"Starting bridge domain validation with {self.iterations} iterations...")
        
        self.test_results['total_tests'] = self.iterations
        
        for i in range(self.iterations):
            logger.info(f"Running test {i+1}/{self.iterations}...")
            
            test_result = self.run_single_test(i + 1)
            self.test_results['tests'].append(test_result)
            
            # Update statistics
            if test_result['success']:
                self.test_results['successful_tests'] += 1
                
                # Update device success rates
                for device in test_result.get('devices_in_path', []):
                    self.test_results['device_success_rates'][device]['success'] += 1
                    self.test_results['device_success_rates'][device]['total'] += 1
                
                # Update interface success rates
                source_interface = test_result.get('source_interface', '')
                dest_interface = test_result.get('dest_interface', '')
                self.test_results['interface_success_rates'][source_interface]['success'] += 1
                self.test_results['interface_success_rates'][source_interface]['total'] += 1
                self.test_results['interface_success_rates'][dest_interface]['success'] += 1
                self.test_results['interface_success_rates'][dest_interface]['total'] += 1
            else:
                self.test_results['failed_tests'] += 1
                
                # Track failure reasons
                error = test_result.get('error', 'Unknown error')
                self.test_results['failure_reasons'][error] += 1
                
                # Update device failure rates
                source_leaf = test_result.get('source_leaf', '')
                dest_leaf = test_result.get('dest_leaf', '')
                if source_leaf:
                    self.test_results['device_success_rates'][source_leaf]['total'] += 1
                if dest_leaf:
                    self.test_results['device_success_rates'][dest_leaf]['total'] += 1
        
        # Calculate success rate
        success_rate = (self.test_results['successful_tests'] / self.test_results['total_tests']) * 100
        
        logger.info(f"Validation complete!")
        logger.info(f"  Total tests: {self.test_results['total_tests']}")
        logger.info(f"  Successful: {self.test_results['successful_tests']}")
        logger.info(f"  Failed: {self.test_results['failed_tests']}")
        logger.info(f"  Success rate: {success_rate:.1f}%")
        
        return self.test_results
    
    def generate_detailed_report(self) -> str:
        """Generate a detailed validation report."""
        report = []
        report.append("=" * 80)
        report.append("🔍 BRIDGE DOMAIN VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {self.test_results['timestamp']}")
        report.append(f"Total Tests: {self.test_results['total_tests']}")
        report.append(f"Successful: {self.test_results['successful_tests']}")
        report.append(f"Failed: {self.test_results['failed_tests']}")
        
        success_rate = (self.test_results['successful_tests'] / self.test_results['total_tests']) * 100
        report.append(f"Success Rate: {success_rate:.1f}%")
        report.append("")
        
        # Failure analysis
        if self.test_results['failure_reasons']:
            report.append("❌ FAILURE ANALYSIS:")
            for reason, count in self.test_results['failure_reasons'].most_common():
                percentage = (count / self.test_results['total_tests']) * 100
                report.append(f"  • {reason}: {count} times ({percentage:.1f}%)")
            report.append("")
        
        # Device success rates
        report.append("📊 DEVICE SUCCESS RATES:")
        for device, stats in sorted(self.test_results['device_success_rates'].items()):
            if stats['total'] > 0:
                rate = (stats['success'] / stats['total']) * 100
                report.append(f"  • {device}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
        report.append("")
        
        # Path analysis
        path_stats = {
            '2_tier': 0,
            '3_tier': 0,
            'failed': 0
        }
        
        for test in self.test_results['tests']:
            if test['success'] and test.get('path_info'):
                if test['path_info']['is_2_tier']:
                    path_stats['2_tier'] += 1
                else:
                    path_stats['3_tier'] += 1
            else:
                path_stats['failed'] += 1
        
        report.append("🛣️  PATH ANALYSIS:")
        report.append(f"  • 2-tier paths: {path_stats['2_tier']}")
        report.append(f"  • 3-tier paths: {path_stats['3_tier']}")
        report.append(f"  • Failed paths: {path_stats['failed']}")
        report.append("")
        
        # Detailed test results
        report.append("📋 DETAILED TEST RESULTS:")
        for test in self.test_results['tests']:
            status = "✅ SUCCESS" if test['success'] else "❌ FAILED"
            report.append(f"  Test {test['test_id']}: {status}")
            report.append(f"    {test.get('source_leaf', 'N/A')} -> {test.get('dest_leaf', 'N/A')}")
            
            if test['success']:
                devices = test.get('devices_in_path', [])
                report.append(f"    Devices in path: {len(devices)}")
                report.append(f"    Config commands: {test.get('config_commands', 0)}")
                
                if test.get('path_info'):
                    path_type = "2-tier" if test['path_info']['is_2_tier'] else "3-tier"
                    report.append(f"    Path type: {path_type}")
            else:
                report.append(f"    Error: {test.get('error', 'Unknown')}")
            report.append("")
        
        return "\n".join(report)
    
    def save_test_results(self, output_file: str = "QA/bridge_domain_validation_results.json"):
        """Save test results to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Test results saved to: {output_path}")
        return output_path
    
    def save_detailed_report(self, output_file: str = "QA/bridge_domain_validation_report.txt"):
        """Save detailed report to text file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        report = self.generate_detailed_report()
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Detailed report saved to: {output_path}")
        return output_path
    
    def print_summary(self):
        """Print a summary of the validation results."""
        success_rate = (self.test_results['successful_tests'] / self.test_results['total_tests']) * 100
        
        print("\n" + "=" * 60)
        print("🎯 BRIDGE DOMAIN VALIDATION SUMMARY")
        print("=" * 60)
        print(f"📊 Total Tests: {self.test_results['total_tests']}")
        print(f"✅ Successful: {self.test_results['successful_tests']}")
        print(f"❌ Failed: {self.test_results['failed_tests']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['failure_reasons']:
            print(f"\n🔍 Top Failure Reasons:")
            for reason, count in self.test_results['failure_reasons'].most_common(3):
                percentage = (count / self.test_results['total_tests']) * 100
                print(f"   • {reason}: {count} times ({percentage:.1f}%)")
        
        # Path analysis
        path_stats = {'2_tier': 0, '3_tier': 0, 'failed': 0}
        for test in self.test_results['tests']:
            if test['success'] and test.get('path_info'):
                if test['path_info']['is_2_tier']:
                    path_stats['2_tier'] += 1
                else:
                    path_stats['3_tier'] += 1
            else:
                path_stats['failed'] += 1
        
        print(f"\n🛣️  Path Analysis:")
        print(f"   • 2-tier paths: {path_stats['2_tier']}")
        print(f"   • 3-tier paths: {path_stats['3_tier']}")
        print(f"   • Failed paths: {path_stats['failed']}")
        
        print("\n" + "=" * 60)

def main():
    """Main function for running bridge domain validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate bridge domain builder with automated testing')
    parser.add_argument('--iterations', type=int, default=20, help='Number of test iterations')
    parser.add_argument('--topology-dir', default='topology', help='Topology directory')
    parser.add_argument('--output-dir', default='QA', help='Output directory for results')
    
    args = parser.parse_args()
    
    # Create validator
    validator = BridgeDomainValidator(
        topology_dir=args.topology_dir,
        iterations=args.iterations
    )
    
    # Run validation
    results = validator.run_validation_tests()
    
    # Save results
    validator.save_test_results(f"{args.output_dir}/bridge_domain_validation_results.json")
    validator.save_detailed_report(f"{args.output_dir}/bridge_domain_validation_report.txt")
    
    # Print summary
    validator.print_summary()
    
    # Return exit code based on success rate
    success_rate = (results['successful_tests'] / results['total_tests']) * 100
    if success_rate >= 80:
        print("\n✅ Validation passed! (Success rate >= 80%)")
        return 0
    else:
        print(f"\n⚠️  Validation warning! (Success rate: {success_rate:.1f}%)")
        return 1

if __name__ == "__main__":
    exit(main()) 