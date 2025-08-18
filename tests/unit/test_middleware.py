#!/usr/bin/env python3
"""
Unit Tests for Middleware Components
Tests authentication, error handling, rate limiting, logging, caching, and monitoring
"""

import unittest
import sys
import os
from pathlib import Path
import time
import json
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.middleware.auth_middleware import token_required, admin_required, create_audit_log
from api.middleware.error_middleware import (
    APIError, ValidationError, NotFoundError, format_error_response, format_success_response
)
from api.middleware.rate_limiting import RateLimiter, rate_limit
from api.middleware.caching import LRUCache, CacheEntry, cache_response
from api.middleware.monitoring import MetricsCollector, monitor_request


class TestAuthMiddleware(unittest.TestCase):
    """Test authentication middleware components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_user = Mock()
        self.mock_user.id = 123
        self.mock_user.username = "testuser"
        self.mock_user.is_admin = False
        
        self.mock_admin_user = Mock()
        self.mock_admin_user.id = 456
        self.mock_admin_user.username = "adminuser"
        self.mock_admin_user.is_admin = True
    
    def test_token_required_decorator(self):
        """Test token_required decorator"""
        @token_required
        def test_function(current_user):
            return f"Hello {current_user.username}"
        
        # Test with valid user
        result = test_function(self.mock_user)
        self.assertEqual(result, "Hello testuser")
    
    def test_admin_required_decorator(self):
        """Test admin_required decorator"""
        @admin_required
        def admin_function(current_user):
            return f"Admin: {current_user.username}"
        
        # Test with admin user
        result = admin_function(self.mock_admin_user)
        self.assertEqual(result, "Admin: adminuser")
    
    def test_create_audit_log(self):
        """Test audit log creation"""
        # Mock the database session
        with patch('api.middleware.auth_middleware.db') as mock_db:
            with patch('api.middleware.auth_middleware.AuditLog') as mock_audit_log:
                mock_audit_instance = Mock()
                mock_audit_log.return_value = mock_audit_instance
                
                create_audit_log(
                    user_id=123,
                    action="test_action",
                    details={"test": "data"},
                    ip_address="127.0.0.1"
                )
                
                # Verify audit log was created
                mock_audit_log.assert_called_once()
                mock_db.session.add.assert_called_once_with(mock_audit_instance)
                mock_db.session.commit.assert_called_once()


class TestErrorMiddleware(unittest.TestCase):
    """Test error handling middleware"""
    
    def test_api_error_hierarchy(self):
        """Test API error class hierarchy"""
        # Test base API error
        error = APIError("Test error", 400)
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.status_code, 400)
        self.assertIsInstance(error, Exception)
        
        # Test validation error
        val_error = ValidationError("Validation failed", {"field": "value"})
        self.assertEqual(val_error.message, "Validation failed")
        self.assertEqual(val_error.status_code, 400)
        self.assertEqual(val_error.details, {"field": "value"})
        
        # Test not found error
        not_found = NotFoundError("Resource not found", {"resource_id": 123})
        self.assertEqual(not_found.message, "Resource not found")
        self.assertEqual(not_found.status_code, 404)
    
    def test_format_error_response(self):
        """Test error response formatting"""
        response = format_error_response("Test error", 400, {"field": "value"})
        
        self.assertIsInstance(response, dict)
        self.assertEqual(response['error'], True)
        self.assertEqual(response['message'], "Test error")
        self.assertEqual(response['status_code'], 400)
        self.assertEqual(response['details'], {"field": "value"})
    
    def test_format_success_response(self):
        """Test success response formatting"""
        response = format_success_response({"data": "test"}, "Success message")
        
        self.assertIsInstance(response, dict)
        self.assertEqual(response['error'], False)
        self.assertEqual(response['message'], "Success message")
        self.assertEqual(response['data'], {"data": "test"})


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting middleware"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.limiter = RateLimiter(max_requests=3, window_seconds=1)
    
    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiter functionality"""
        key = "test_key"
        
        # First three requests should be allowed
        self.assertTrue(self.limiter.is_allowed(key)[0])
        self.assertTrue(self.limiter.is_allowed(key)[0])
        self.assertTrue(self.limiter.is_allowed(key)[0])
        
        # Fourth request should be blocked
        self.assertFalse(self.limiter.is_allowed(key)[0])
    
    def test_rate_limiter_window_expiry(self):
        """Test rate limiter window expiry"""
        key = "test_key"
        
        # Make requests
        self.limiter.is_allowed(key)
        self.limiter.is_allowed(key)
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        self.assertTrue(self.limiter.is_allowed(key)[0])
    
    def test_rate_limiter_remaining_requests(self):
        """Test remaining requests calculation"""
        key = "test_key"
        
        # First request
        allowed, remaining = self.limiter.is_allowed(key)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 2)
        
        # Second request
        allowed, remaining = self.limiter.is_allowed(key)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 1)
        
        # Third request
        allowed, remaining = self.limiter.is_allowed(key)
        self.assertTrue(allowed)
        self.assertEqual(remaining, 0)
    
    def test_rate_limit_decorator(self):
        """Test rate limit decorator"""
        @rate_limit('default')
        def test_function():
            return "success"
        
        # Function should be callable
        self.assertTrue(callable(test_function))
        
        # Should return the original function result
        result = test_function()
        self.assertEqual(result, "success")


class TestCaching(unittest.TestCase):
    """Test caching middleware"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cache = LRUCache(max_size=3)
    
    def test_cache_entry_creation(self):
        """Test cache entry creation"""
        entry = CacheEntry("test_data", ttl_seconds=300)
        
        self.assertEqual(entry.data, "test_data")
        self.assertEqual(entry.ttl_seconds, 300)
        self.assertEqual(entry.access_count, 0)
        self.assertFalse(entry.is_expired())
    
    def test_cache_entry_expiry(self):
        """Test cache entry expiry"""
        entry = CacheEntry("test_data", ttl_seconds=0.1)
        
        # Should not be expired initially
        self.assertFalse(entry.is_expired())
        
        # Wait for expiry
        time.sleep(0.2)
        
        # Should be expired now
        self.assertTrue(entry.is_expired())
    
    def test_lru_cache_basic_operations(self):
        """Test LRU cache basic operations"""
        # Test set and get
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Test get non-existent key
        self.assertIsNone(self.cache.get("nonexistent"))
        
        # Test delete
        self.cache.delete("key1")
        self.assertIsNone(self.cache.get("key1"))
    
    def test_lru_cache_size_limit(self):
        """Test LRU cache size limit enforcement"""
        # Fill cache to capacity
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # All should be present
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertEqual(self.cache.get("key3"), "value3")
        
        # Add one more - should evict oldest (key1)
        self.cache.set("key4", "value4")
        
        # key1 should be evicted
        self.assertIsNone(self.cache.get("key1"))
        # key4 should be present
        self.assertEqual(self.cache.get("key4"), "value4")
    
    def test_lru_cache_access_order(self):
        """Test LRU cache access order maintenance"""
        # Add items
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")
        
        # Access key1 to make it most recently used
        self.cache.get("key1")
        
        # Add new item - should evict key2 (least recently used)
        self.cache.set("key4", "value4")
        
        # key2 should be evicted
        self.assertIsNone(self.cache.get("key2"))
        # key1 should still be present
        self.assertEqual(self.cache.get("key1"), "value1")
    
    def test_cache_response_decorator(self):
        """Test cache response decorator"""
        @cache_response(ttl_seconds=300)
        def test_function():
            return "cached_result"
        
        # Function should be callable
        self.assertTrue(callable(test_function))
        
        # Should return the original function result
        result = test_function()
        self.assertEqual(result, "cached_result")


class TestMonitoring(unittest.TestCase):
    """Test monitoring middleware"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.metrics = MetricsCollector(max_history=100)
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization"""
        self.assertEqual(self.metrics.max_history, 100)
        self.assertIsInstance(self.metrics.request_counts, dict)
        self.assertIsInstance(self.metrics.endpoint_metrics, dict)
        self.assertIsInstance(self.metrics.user_metrics, dict)
    
    def test_record_request_metrics(self):
        """Test request metrics recording"""
        # Record a request
        self.metrics.record_request(
            endpoint="test_endpoint",
            method="GET",
            user_id=123,
            response_time=0.5,
            status_code=200
        )
        
        # Check that metrics were recorded
        self.assertEqual(self.metrics.request_counts["GET test_endpoint"], 1)
        self.assertEqual(self.metrics.status_codes[200], 1)
        self.assertEqual(len(self.metrics.response_times["GET test_endpoint"]), 1)
        
        # Check endpoint metrics
        endpoint_key = "GET test_endpoint"
        self.assertEqual(self.metrics.endpoint_metrics[endpoint_key]['total_requests'], 1)
        self.assertEqual(self.metrics.endpoint_metrics[endpoint_key]['avg_response_time'], 0.5)
        
        # Check user metrics
        self.assertEqual(self.metrics.user_metrics[123]['total_requests'], 1)
    
    def test_record_error_metrics(self):
        """Test error metrics recording"""
        # Record an error request
        self.metrics.record_request(
            endpoint="test_endpoint",
            method="POST",
            user_id=123,
            response_time=0.1,
            status_code=500,
            error="Test error"
        )
        
        # Check error counts
        self.assertEqual(self.metrics.error_counts["POST test_endpoint"], 1)
        self.assertEqual(self.metrics.status_codes[500], 1)
        
        # Check endpoint error metrics
        endpoint_key = "POST test_endpoint"
        self.assertEqual(self.metrics.endpoint_metrics[endpoint_key]['total_errors'], 1)
        
        # Check user error metrics
        self.assertEqual(self.metrics.user_metrics[123]['total_errors'], 1)
    
    def test_get_summary_stats(self):
        """Test summary statistics generation"""
        # Record some requests
        self.metrics.record_request("endpoint1", "GET", user_id=123, response_time=0.5, status_code=200)
        self.metrics.record_request("endpoint2", "POST", user_id=456, response_time=0.3, status_code=200)
        self.metrics.record_request("endpoint1", "GET", user_id=123, response_time=0.7, status_code=500, error="Error")
        
        stats = self.metrics.get_summary_stats()
        
        self.assertEqual(stats['total_requests'], 3)
        self.assertEqual(stats['total_errors'], 1)
        self.assertAlmostEqual(stats['error_rate_percent'], 33.33, places=1)
        self.assertEqual(stats['unique_endpoints'], 2)
        self.assertEqual(stats['unique_users'], 2)
    
    def test_monitor_request_decorator(self):
        """Test monitor request decorator"""
        @monitor_request
        def test_function():
            return "monitored_result"
        
        # Function should be callable
        self.assertTrue(callable(test_function))
        
        # Should return the original function result
        result = test_function()
        self.assertEqual(result, "monitored_result")


class TestMiddlewareIntegration(unittest.TestCase):
    """Test middleware integration and combination"""
    
    def test_multiple_decorators_combination(self):
        """Test combining multiple middleware decorators"""
        # Create a function with multiple decorators
        @token_required
        @rate_limit('default')
        @monitor_request
        def test_function(current_user):
            return f"Hello {current_user.username}"
        
        # Function should be callable
        self.assertTrue(callable(test_function))
        
        # Mock user for testing
        mock_user = Mock()
        mock_user.username = "testuser"
        
        # Should execute without errors
        result = test_function(mock_user)
        self.assertEqual(result, "Hello testuser")
    
    def test_middleware_error_handling(self):
        """Test middleware error handling integration"""
        @token_required
        @monitor_request
        def error_function(current_user):
            raise ValidationError("Test validation error")
        
        # Mock user for testing
        mock_user = Mock()
        mock_user.username = "testuser"
        
        # Should raise the error (middleware should not suppress it)
        with self.assertRaises(ValidationError):
            error_function(mock_user)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAuthMiddleware,
        TestErrorMiddleware,
        TestRateLimiting,
        TestCaching,
        TestMonitoring,
        TestMiddlewareIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())
