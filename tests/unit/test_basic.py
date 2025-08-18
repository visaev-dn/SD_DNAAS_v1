#!/usr/bin/env python3
"""
Basic Test Suite
Simple tests to verify the testing framework works
"""

import unittest
import time


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality"""
    
    def test_basic_assertions(self):
        """Test basic assertions work"""
        self.assertTrue(True)
        self.assertFalse(False)
        self.assertEqual(1 + 1, 2)
        self.assertNotEqual(1 + 1, 3)
        self.assertGreater(5, 3)
        self.assertLess(3, 5)
    
    def test_string_operations(self):
        """Test string operations"""
        test_string = "Hello World"
        self.assertEqual(len(test_string), 11)
        self.assertIn("Hello", test_string)
        self.assertNotIn("Python", test_string)
        self.assertTrue(test_string.startswith("Hello"))
        self.assertTrue(test_string.endswith("World"))
    
    def test_list_operations(self):
        """Test list operations"""
        test_list = [1, 2, 3, 4, 5]
        self.assertEqual(len(test_list), 5)
        self.assertIn(3, test_list)
        self.assertNotIn(10, test_list)
        self.assertEqual(test_list[0], 1)
        self.assertEqual(test_list[-1], 5)
    
    def test_dict_operations(self):
        """Test dictionary operations"""
        test_dict = {"key1": "value1", "key2": "value2"}
        self.assertEqual(len(test_dict), 2)
        self.assertIn("key1", test_dict)
        self.assertNotIn("key3", test_dict)
        self.assertEqual(test_dict["key1"], "value1")


class TestTimeOperations(unittest.TestCase):
    """Test time-related operations"""
    
    def test_time_measurement(self):
        """Test time measurement works"""
        start_time = time.time()
        time.sleep(0.01)  # Small delay
        end_time = time.time()
        
        # Should have taken some time
        self.assertGreater(end_time, start_time)
        self.assertGreater(end_time - start_time, 0.001)
    
    def test_time_comparison(self):
        """Test time comparison logic"""
        current_time = time.time()
        future_time = current_time + 60  # 1 minute in future
        
        self.assertLess(current_time, future_time)
        self.assertGreater(future_time, current_time)
        
        time_diff = future_time - current_time
        self.assertAlmostEqual(time_diff, 60, delta=1)


class TestMathematicalOperations(unittest.TestCase):
    """Test mathematical operations"""
    
    def test_basic_math(self):
        """Test basic mathematical operations"""
        self.assertEqual(2 + 2, 4)
        self.assertEqual(5 - 3, 2)
        self.assertEqual(4 * 3, 12)
        self.assertEqual(15 / 3, 5)
        self.assertEqual(7 % 3, 1)
        self.assertEqual(2 ** 3, 8)
    
    def test_float_operations(self):
        """Test float operations"""
        self.assertAlmostEqual(0.1 + 0.2, 0.3, places=7)
        self.assertAlmostEqual(1.0 / 3.0, 0.333333, places=5)
        
        # Test percentage calculation
        total = 100
        part = 25
        percentage = (part / total) * 100
        self.assertEqual(percentage, 25.0)
    
    def test_average_calculation(self):
        """Test average calculation"""
        values = [10, 20, 30, 40, 50]
        average = sum(values) / len(values)
        self.assertEqual(average, 30)
        
        # Test with different values
        values2 = [1, 2, 3]
        average2 = sum(values2) / len(values2)
        self.assertEqual(average2, 2)


class TestErrorHandling(unittest.TestCase):
    """Test error handling patterns"""
    
    def test_exception_handling(self):
        """Test exception handling works"""
        def function_that_raises():
            raise ValueError("Test error")
        
        # Test that exception is raised
        with self.assertRaises(ValueError):
            function_that_raises()
        
        # Test exception message
        with self.assertRaisesRegex(ValueError, "Test error"):
            function_that_raises()
    
    def test_conditional_logic(self):
        """Test conditional logic"""
        value = 5
        
        if value > 3:
            result = "greater"
        else:
            result = "less_or_equal"
        
        self.assertEqual(result, "greater")
        
        # Test another condition
        if value == 5:
            result2 = "equal"
        else:
            result2 = "not_equal"
        
        self.assertEqual(result2, "equal")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestBasicFunctionality,
        TestTimeOperations,
        TestMathematicalOperations,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    import sys
    sys.exit(not result.wasSuccessful())
