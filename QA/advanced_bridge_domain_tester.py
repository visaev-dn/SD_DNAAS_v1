#!/usr/bin/env python3
"""
Advanced Bridge Domain Tester - Comprehensive QA Tool
Tests specific scenarios, edge cases, and provides detailed analysis.
"""

import json
import yaml
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import logging
from collections import defaultdict, Counter

# Import the bridge domain builder
from config_engine.bridge_domain_builder import BridgeDomainBuilder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedBridgeDomainTester:
    """Advanced bridge domain tester with scenario-based testing."""
    
    def __init__(self, topology_dir: str = "topology"):
        """
        Initialize the advanced tester.
        
        Args:
            topology_dir: Directory containing topology files
        """
        self.topology_dir = Path(topology_dir)
        self.builder = BridgeDomainBuilder(topology_dir)
        
        # Load topology data
        self.topology_data = self.builder.topology_data
        self.devices = self.topology_data.get('devices', {})
        
        # Load available leaves
        self.available_leaves = self.builder.get_available_leaves()
        self.unavailable_leaves = self.builder.get_unavailable_leaves()
        
        # Test scenarios
        self.test_scenarios = {
            'random_pairs': [],
            'same_leaf': [],
            'failed_spine_affected': [],
            'edge_cases': [],
            'stress_test': []
        }
        
        logger.info(f"Loaded {len(self.available_leaves)} available leaves")
        logger.info(f"Found {len(self.unavailable_leaves)} unavailable leaves")
    
    def test_random_leaf_pairs(self, iterations: int = 10) -> List[Dict]:
        """Test random leaf pairs."""
        logger.info(f"Testing {iterations} random leaf pairs...")
        
        results = []
        for i in range(iterations):
            try:
                # Get random leaf pair
                if len(self.available_leaves) < 2:
                    raise ValueError("Need at least 2 available leaves")
                
                source_leaf, dest_leaf = random.sample(self.available_leaves, 2)
                
                result = self._run_single_test(
                    test_id=f"random_{i+1}",
                    source_leaf=source_leaf,
                    dest_leaf=dest_leaf,
                    scenario="random_pairs"
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Random pair test {i+1} failed: {e}")
                results.append({
                    'test_id': f"random_{i+1}",
                    'scenario': 'random_pairs',
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def test_same_leaf_scenarios(self, iterations: int = 5) -> List[Dict]:
        """Test scenarios where source and destination are the same leaf."""
        logger.info(f"Testing {iterations} same-leaf scenarios...")
        
        results = []
        for i in range(iterations):
            try:
                # Pick a random leaf
                leaf = random.choice(self.available_leaves)
                
                result = self._run_single_test(
                    test_id=f"same_leaf_{i+1}",
                    source_leaf=leaf,
                    dest_leaf=leaf,
                    scenario="same_leaf"
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Same leaf test {i+1} failed: {e}")
                results.append({
                    'test_id': f"same_leaf_{i+1}",
                    'scenario': 'same_leaf',
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def test_failed_spine_affected_leaves(self) -> List[Dict]:
        """Test leaves that are affected by failed spines."""
        logger.info("Testing failed spine affected leaves...")
        
        results = []
        
        # Get leaves that are unavailable due to failed spines
        affected_leaves = []
        for leaf, reason in self.unavailable_leaves.items():
            # Check if reason is a string or dict
            if isinstance(reason, str):
                if 'failed_spine' in reason.lower():
                    affected_leaves.append(leaf)
            elif isinstance(reason, dict):
                # If reason is a dict, check the description
                description = reason.get('description', '')
                if 'failed_spine' in description.lower():
                    affected_leaves.append(leaf)
        
        logger.info(f"Found {len(affected_leaves)} leaves affected by failed spines")
        
        # Test each affected leaf with a successful leaf
        for i, affected_leaf in enumerate(affected_leaves[:5]):  # Limit to 5 tests
            try:
                # Find a successful leaf to pair with
                successful_leaf = random.choice(self.available_leaves)
                
                result = self._run_single_test(
                    test_id=f"failed_spine_{i+1}",
                    source_leaf=affected_leaf,
                    dest_leaf=successful_leaf,
                    scenario="failed_spine_affected"
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed spine test {i+1} failed: {e}")
                results.append({
                    'test_id': f"failed_spine_{i+1}",
                    'scenario': 'failed_spine_affected',
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def test_edge_cases(self) -> List[Dict]:
        """Test edge cases and boundary conditions."""
        logger.info("Testing edge cases...")
        
        results = []
        
        # Edge case 1: Very high VLAN ID
        try:
            source_leaf, dest_leaf = random.sample(self.available_leaves, 2)
            result = self._run_single_test(
                test_id="edge_vlan_4094",
                source_leaf=source_leaf,
                dest_leaf=dest_leaf,
                vlan_id=4094,
                scenario="edge_cases"
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Edge case VLAN 4094 failed: {e}")
        
        # Edge case 2: Very low VLAN ID
        try:
            source_leaf, dest_leaf = random.sample(self.available_leaves, 2)
            result = self._run_single_test(
                test_id="edge_vlan_1",
                source_leaf=source_leaf,
                dest_leaf=dest_leaf,
                vlan_id=1,
                scenario="edge_cases"
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Edge case VLAN 1 failed: {e}")
        
        # Edge case 3: Very long service name
        try:
            source_leaf, dest_leaf = random.sample(self.available_leaves, 2)
            long_service_name = "a" * 100  # Very long name
            result = self._run_single_test(
                test_id="edge_long_service",
                source_leaf=source_leaf,
                dest_leaf=dest_leaf,
                service_name=long_service_name,
                scenario="edge_cases"
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Edge case long service name failed: {e}")
        
        # Edge case 4: Special characters in service name
        try:
            source_leaf, dest_leaf = random.sample(self.available_leaves, 2)
            special_service_name = "test_service_with_special_chars_!@#$%^&*()"
            result = self._run_single_test(
                test_id="edge_special_chars",
                source_leaf=source_leaf,
                dest_leaf=dest_leaf,
                service_name=special_service_name,
                scenario="edge_cases"
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Edge case special characters failed: {e}")
        
        return results
    
    def test_stress_scenarios(self, iterations: int = 20) -> List[Dict]:
        """Run stress tests with many rapid requests."""
        logger.info(f"Running stress test with {iterations} rapid requests...")
        
        results = []
        start_time = time.time()
        
        for i in range(iterations):
            try:
                # Get random leaf pair
                source_leaf, dest_leaf = random.sample(self.available_leaves, 2)
                
                result = self._run_single_test(
                    test_id=f"stress_{i+1}",
                    source_leaf=source_leaf,
                    dest_leaf=dest_leaf,
                    scenario="stress_test"
                )
                results.append(result)
                
                # Small delay to avoid overwhelming the system
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Stress test {i+1} failed: {e}")
                results.append({
                    'test_id': f"stress_{i+1}",
                    'scenario': 'stress_test',
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"Stress test completed in {total_time:.2f} seconds")
        logger.info(f"Average time per test: {total_time/iterations:.2f} seconds")
        
        return results
    
    def _run_single_test(self, test_id: str, source_leaf: str, dest_leaf: str,
                         vlan_id: Optional[int] = None, service_name: Optional[str] = None,
                         scenario: str = "unknown") -> Dict:
        """Run a single test with given parameters."""
        result = {
            'test_id': test_id,
            'scenario': scenario,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'error': None,
            'path_info': None,
            'devices_in_path': [],
            'config_commands': 0,
            'source_leaf': source_leaf,
            'dest_leaf': dest_leaf
        }
        
        try:
            # Generate random interface if not provided
            source_interface = self._get_random_interface(source_leaf)
            dest_interface = self._get_random_interface(dest_leaf)
            
            # Generate service name and VLAN if not provided
            if not service_name:
                service_name = f"test_service_{test_id}_{int(time.time())}"
            if not vlan_id:
                vlan_id = random.randint(100, 4094)
            
            result.update({
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
                result['success'] = True
                result['config_commands'] = sum(len(config) for config in configs.values())
                result['devices_in_path'] = list(configs.keys())
                
                # Get path information
                path = self.builder.calculate_path(source_leaf, dest_leaf)
                if path:
                    result['path_info'] = {
                        'is_2_tier': path.get('superspine') is None,
                        'source_spine': path.get('source_spine'),
                        'superspine': path.get('superspine'),
                        'dest_spine': path.get('dest_spine'),
                        'segments': len(path.get('segments', []))
                    }
                
                logger.info(f"{scenario} test {test_id}: SUCCESS - {source_leaf} -> {dest_leaf}")
            else:
                # Test failed
                result['success'] = False
                result['error'] = "No configuration generated"
                logger.warning(f"{scenario} test {test_id}: FAILED - {source_leaf} -> {dest_leaf}")
                
        except Exception as e:
            # Test failed with exception
            result['success'] = False
            result['error'] = str(e)
            logger.error(f"{scenario} test {test_id}: ERROR - {source_leaf} -> {dest_leaf}: {e}")
        
        return result
    
    def _get_random_interface(self, device: str) -> str:
        """Get a random interface for a device."""
        interface_patterns = [
            "ge100-0/0/1", "ge100-0/0/2", "ge100-0/0/3", "ge100-0/0/4",
            "ge100-0/0/5", "ge100-0/0/6", "ge100-0/0/7", "ge100-0/0/8",
            "ge100-0/0/9", "ge100-0/0/10", "ge100-0/0/11", "ge100-0/0/12",
            "ge100-0/0/13", "ge100-0/0/14", "ge100-0/0/15", "ge100-0/0/16",
            "ge100-0/0/17", "ge100-0/0/18", "ge100-0/0/19", "ge100-0/0/20",
            "ge100-0/0/21", "ge100-0/0/22", "ge100-0/0/23", "ge100-0/0/24",
            "ge100-0/0/25", "ge100-0/0/26", "ge100-0/0/27", "ge100-0/0/28",
            "ge100-0/0/29", "ge100-0/0/30", "ge100-0/0/31", "ge100-0/0/32",
            "ge100-0/0/33", "ge100-0/0/34", "ge100-0/0/35", "ge100-0/0/36",
            "ge100-0/0/37", "ge100-0/0/38", "ge100-0/0/39", "ge100-0/0/40"
        ]
        
        return random.choice(interface_patterns)
    
    def run_comprehensive_test_suite(self) -> Dict:
        """Run the complete comprehensive test suite."""
        logger.info("Starting comprehensive bridge domain test suite...")
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'scenarios': {},
            'summary': {
                'total_tests': 0,
                'successful_tests': 0,
                'failed_tests': 0,
                'scenario_breakdown': {}
            }
        }
        
        # Run all test scenarios
        all_results['scenarios']['random_pairs'] = self.test_random_leaf_pairs(10)
        all_results['scenarios']['same_leaf'] = self.test_same_leaf_scenarios(5)
        all_results['scenarios']['failed_spine_affected'] = self.test_failed_spine_affected_leaves()
        all_results['scenarios']['edge_cases'] = self.test_edge_cases()
        all_results['scenarios']['stress_test'] = self.test_stress_scenarios(20)
        
        # Calculate summary statistics
        for scenario_name, results in all_results['scenarios'].items():
            total = len(results)
            successful = sum(1 for r in results if r.get('success', False))
            failed = total - successful
            
            all_results['summary']['total_tests'] += total
            all_results['summary']['successful_tests'] += successful
            all_results['summary']['failed_tests'] += failed
            
            all_results['summary']['scenario_breakdown'][scenario_name] = {
                'total': total,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total * 100) if total > 0 else 0
            }
        
        # Calculate overall success rate
        overall_success_rate = (all_results['summary']['successful_tests'] / 
                              all_results['summary']['total_tests'] * 100) if all_results['summary']['total_tests'] > 0 else 0
        
        all_results['summary']['overall_success_rate'] = overall_success_rate
        
        logger.info(f"Comprehensive test suite completed!")
        logger.info(f"  Total tests: {all_results['summary']['total_tests']}")
        logger.info(f"  Successful: {all_results['summary']['successful_tests']}")
        logger.info(f"  Failed: {all_results['summary']['failed_tests']}")
        logger.info(f"  Overall success rate: {overall_success_rate:.1f}%")
        
        return all_results
    
    def generate_comprehensive_report(self, results: Dict) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("=" * 80)
        report.append("🔍 COMPREHENSIVE BRIDGE DOMAIN TEST REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {results['timestamp']}")
        report.append(f"Total Tests: {results['summary']['total_tests']}")
        report.append(f"Successful: {results['summary']['successful_tests']}")
        report.append(f"Failed: {results['summary']['failed_tests']}")
        report.append(f"Overall Success Rate: {results['summary']['overall_success_rate']:.1f}%")
        report.append("")
        
        # Scenario breakdown
        report.append("📊 SCENARIO BREAKDOWN:")
        for scenario, stats in results['summary']['scenario_breakdown'].items():
            report.append(f"  {scenario.upper()}:")
            report.append(f"    • Total: {stats['total']}")
            report.append(f"    • Successful: {stats['successful']}")
            report.append(f"    • Failed: {stats['failed']}")
            report.append(f"    • Success Rate: {stats['success_rate']:.1f}%")
            report.append("")
        
        # Detailed results by scenario
        for scenario_name, scenario_results in results['scenarios'].items():
            report.append(f"📋 {scenario_name.upper()} DETAILED RESULTS:")
            
            for result in scenario_results:
                status = "✅ SUCCESS" if result.get('success', False) else "❌ FAILED"
                report.append(f"  {result['test_id']}: {status}")
                
                if result.get('success', False):
                    devices = result.get('devices_in_path', [])
                    commands = result.get('config_commands', 0)
                    report.append(f"    • Devices in path: {len(devices)}")
                    report.append(f"    • Config commands: {commands}")
                    
                    if result.get('path_info'):
                        path_type = "2-tier" if result['path_info']['is_2_tier'] else "3-tier"
                        report.append(f"    • Path type: {path_type}")
                else:
                    report.append(f"    • Error: {result.get('error', 'Unknown')}")
                report.append("")
        
        return "\n".join(report)
    
    def save_comprehensive_results(self, results: Dict, output_file: str = "QA/comprehensive_bridge_domain_test_results.json"):
        """Save comprehensive test results to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Comprehensive test results saved to: {output_path}")
        return output_path
    
    def save_comprehensive_report(self, results: Dict, output_file: str = "QA/comprehensive_bridge_domain_test_report.txt"):
        """Save comprehensive report to text file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        report = self.generate_comprehensive_report(results)
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Comprehensive report saved to: {output_path}")
        return output_path
    
    def print_summary(self, results: Dict):
        """Print a summary of the comprehensive test results."""
        summary = results['summary']
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE BRIDGE DOMAIN TEST SUMMARY")
        print("=" * 60)
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Successful: {summary['successful_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        print(f"📈 Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        print("")
        
        print("📋 SCENARIO BREAKDOWN:")
        for scenario, stats in summary['scenario_breakdown'].items():
            print(f"  • {scenario}: {stats['successful']}/{stats['total']} ({stats['success_rate']:.1f}%)")
        
        print("\n" + "=" * 60)

def main():
    """Main function for running comprehensive bridge domain testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive bridge domain testing')
    parser.add_argument('--topology-dir', default='topology', help='Topology directory')
    parser.add_argument('--output-dir', default='QA', help='Output directory for results')
    parser.add_argument('--random-iterations', type=int, default=10, help='Number of random pair tests (default: 10)')
    parser.add_argument('--same-leaf-iterations', type=int, default=5, help='Number of same-leaf tests (default: 5)')
    parser.add_argument('--stress-iterations', type=int, default=20, help='Number of stress tests (default: 20)')
    parser.add_argument('--failed-spine-limit', type=int, default=5, help='Maximum failed spine tests (default: 5)')
    
    args = parser.parse_args()
    
    # Create tester
    tester = AdvancedBridgeDomainTester(topology_dir=args.topology_dir)
    
    # Run comprehensive test suite with custom iteration counts
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'scenarios': {},
        'summary': {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'scenario_breakdown': {}
        }
    }
    
    # Run all test scenarios with custom iteration counts
    all_results['scenarios']['random_pairs'] = tester.test_random_leaf_pairs(args.random_iterations)
    all_results['scenarios']['same_leaf'] = tester.test_same_leaf_scenarios(args.same_leaf_iterations)
    all_results['scenarios']['failed_spine_affected'] = tester.test_failed_spine_affected_leaves()
    all_results['scenarios']['edge_cases'] = tester.test_edge_cases()
    all_results['scenarios']['stress_test'] = tester.test_stress_scenarios(args.stress_iterations)
    
    # Calculate summary statistics
    for scenario_name, results in all_results['scenarios'].items():
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        failed = total - successful
        
        all_results['summary']['total_tests'] += total
        all_results['summary']['successful_tests'] += successful
        all_results['summary']['failed_tests'] += failed
        
        all_results['summary']['scenario_breakdown'][scenario_name] = {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
    
    # Calculate overall success rate
    overall_success_rate = (all_results['summary']['successful_tests'] / 
                          all_results['summary']['total_tests'] * 100) if all_results['summary']['total_tests'] > 0 else 0
    
    all_results['summary']['overall_success_rate'] = overall_success_rate
    
    logger.info(f"Comprehensive test suite completed!")
    logger.info(f"  Total tests: {all_results['summary']['total_tests']}")
    logger.info(f"  Successful: {all_results['summary']['successful_tests']}")
    logger.info(f"  Failed: {all_results['summary']['failed_tests']}")
    logger.info(f"  Overall success rate: {overall_success_rate:.1f}%")
    
    # Save results
    tester.save_comprehensive_results(all_results, f"{args.output_dir}/comprehensive_bridge_domain_test_results.json")
    tester.save_comprehensive_report(all_results, f"{args.output_dir}/comprehensive_bridge_domain_test_report.txt")
    
    # Print summary
    tester.print_summary(all_results)
    
    # Return exit code based on overall success rate
    overall_success_rate = all_results['summary']['overall_success_rate']
    if overall_success_rate >= 80:
        print("\n✅ Comprehensive testing passed! (Success rate >= 80%)")
        return 0
    else:
        print(f"\n⚠️  Comprehensive testing warning! (Success rate: {overall_success_rate:.1f}%)")
        return 1

if __name__ == "__main__":
    exit(main()) 