#!/usr/bin/env python3
"""
Comprehensive Test Runner for Lab Automation Modular API
Runs unit, integration, and performance tests
"""

import sys
import os
import unittest
import time
from pathlib import Path
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Running Unit Tests...")
    print("=" * 60)
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'tests' / 'unit'
    
    if not start_dir.exists():
        print("❌ Unit tests directory not found")
        return False
    
    suite = loader.discover(start_dir, pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    print(f"\n⏱️  Unit tests completed in {end_time - start_time:.2f} seconds")
    print(f"📊 Results: {result.testsRun} tests run, {len(result.failures)} failures, {len(result.errors)} errors")
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run all integration tests"""
    print("\n🔗 Running Integration Tests...")
    print("=" * 60)
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'tests' / 'integration'
    
    if not start_dir.exists():
        print("❌ Integration tests directory not found")
        return False
    
    suite = loader.discover(start_dir, pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    print(f"\n⏱️  Integration tests completed in {end_time - start_time:.2f} seconds")
    print(f"📊 Results: {result.testsRun} tests run, {len(result.failures)} failures, {len(result.errors)} errors")
    
    return result.wasSuccessful()


def run_performance_tests():
    """Run all performance tests"""
    print("\n⚡ Running Performance Tests...")
    print("=" * 60)
    
    # Discover and run performance tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'tests' / 'performance'
    
    if not start_dir.exists():
        print("❌ Performance tests directory not found")
        return False
    
    suite = loader.discover(start_dir, pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    print(f"\n⏱️  Performance tests completed in {end_time - start_time:.2f} seconds")
    print(f"📊 Results: {result.testsRun} tests run, {len(result.failures)} failures, {len(result.errors)} errors")
    
    return result.wasSuccessful()


def run_specific_test(test_path):
    """Run a specific test file or test case"""
    print(f"🎯 Running Specific Test: {test_path}")
    print("=" * 60)
    
    # Add the test directory to path
    test_dir = Path(test_path).parent
    sys.path.insert(0, str(test_dir))
    
    # Import and run the specific test
    try:
        # Remove .py extension if present
        module_name = Path(test_path).stem
        
        # Import the test module
        test_module = __import__(module_name)
        
        # Create test suite from the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        print(f"\n⏱️  Specific test completed in {end_time - start_time:.2f} seconds")
        print(f"📊 Results: {result.testsRun} tests run, {len(result.failures)} failures, {len(result.errors)} errors")
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"❌ Failed to import test module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running specific test: {e}")
        return False


def run_all_tests():
    """Run all test suites"""
    print("🚀 Running All Tests for Lab Automation Modular API")
    print("=" * 80)
    
    start_time = time.time()
    
    # Run all test suites
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    performance_success = run_performance_tests()
    
    end_time = time.time()
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    
    print(f"✅ Unit Tests: {'PASSED' if unit_success else 'FAILED'}")
    print(f"✅ Integration Tests: {'PASSED' if integration_success else 'FAILED'}")
    print(f"✅ Performance Tests: {'PASSED' if performance_success else 'FAILED'}")
    
    print(f"\n⏱️  Total test time: {end_time - start_time:.2f} seconds")
    
    overall_success = unit_success and integration_success and performance_success
    
    if overall_success:
        print("\n🎉 All tests passed! The modular API is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above for details.")
        return 1


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description='Run tests for Lab Automation Modular API')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--performance', action='store_true', help='Run only performance tests')
    parser.add_argument('--specific', type=str, help='Run a specific test file')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    # Default to running all tests if no specific option is chosen
    if not any([args.unit, args.integration, args.performance, args.specific]):
        args.all = True
    
    try:
        if args.specific:
            success = run_specific_test(args.specific)
            return 0 if success else 1
        elif args.unit:
            success = run_unit_tests()
            return 0 if success else 1
        elif args.integration:
            success = run_integration_tests()
            return 0 if success else 1
        elif args.performance:
            success = run_performance_tests()
            return 0 if success else 1
        elif args.all:
            return run_all_tests()
        else:
            print("❌ No test suite specified")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error during test execution: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
