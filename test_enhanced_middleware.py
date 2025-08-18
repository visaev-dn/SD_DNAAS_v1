#!/usr/bin/env python3
"""
Test Enhanced Middleware Components
Tests rate limiting, logging, and other middleware functionality
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


def test_rate_limiting():
    """Test rate limiting middleware"""
    print("Testing Rate Limiting Middleware...")
    
    try:
        from api.middleware.rate_limiting import (
            RateLimiter, rate_limit, auth_rate_limit, deployment_rate_limit
        )
        
        # Test basic rate limiter
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        
        # Test basic functionality
        key = "test_key"
        assert limiter.is_allowed(key)[0] == True, "First request should be allowed"
        assert limiter.is_allowed(key)[0] == True, "Second request should be allowed"
        assert limiter.is_allowed(key)[0] == True, "Third request should be allowed"
        assert limiter.is_allowed(key)[0] == False, "Fourth request should be blocked"
        
        print("   ✅ Basic rate limiter functionality works")
        
        # Test decorators exist
        assert callable(auth_rate_limit), "auth_rate_limit decorator should exist"
        assert callable(deployment_rate_limit), "deployment_rate_limit decorator should exist"
        
        print("   ✅ Rate limiting decorators available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Rate limiting test failed: {e}")
        return False


def test_logging_middleware():
    """Test logging middleware"""
    print("Testing Logging Middleware...")
    
    try:
        from api.middleware.logging_middleware import (
            RequestLogger, log_request, log_sensitive_operation, log_performance
        )
        
        # Test RequestLogger class
        logger = RequestLogger()
        assert logger.request_id is None, "Request ID should start as None"
        assert logger.start_time is None, "Start time should start as None"
        
        print("   ✅ RequestLogger class works")
        
        # Test decorators exist
        assert callable(log_request), "log_request decorator should exist"
        assert callable(log_sensitive_operation), "log_sensitive_operation decorator should exist"
        assert callable(log_performance), "log_performance decorator should exist"
        
        print("   ✅ Logging decorators available")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Logging middleware test failed: {e}")
        return False


def test_middleware_integration():
    """Test middleware integration"""
    print("Testing Middleware Integration...")
    
    try:
        from api.middleware import (
            token_required, admin_required, ValidationError, NotFoundError,
            auth_rate_limit, log_auth_operation, log_admin_operation
        )
        
        # Test that all middleware components are available
        assert callable(token_required), "token_required should be available"
        assert callable(admin_required), "admin_required should be available"
        assert callable(auth_rate_limit), "auth_rate_limit should be available"
        assert callable(log_auth_operation), "log_auth_operation should be available"
        assert callable(log_admin_operation), "log_admin_operation should be available"
        
        # Test error classes
        assert issubclass(ValidationError, Exception), "ValidationError should be a subclass of Exception"
        assert issubclass(NotFoundError, Exception), "NotFoundError should be a subclass of Exception"
        
        print("   ✅ All middleware components integrated correctly")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Middleware integration test failed: {e}")
        return False


def test_decorator_combinations():
    """Test combining multiple decorators"""
    print("Testing Decorator Combinations...")
    
    try:
        from api.middleware import (
            token_required, admin_required, auth_rate_limit, log_admin_operation
        )
        
        # Test that we can combine decorators
        @token_required
        @admin_required
        @auth_rate_limit
        @log_admin_operation
        def test_function(current_user):
            return "success"
        
        print("   ✅ Multiple decorators can be combined")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Decorator combination test failed: {e}")
        return False


def main():
    """Run all middleware tests"""
    print("🧪 Testing Enhanced Middleware Components")
    print("=" * 60)
    
    tests = [
        test_rate_limiting,
        test_logging_middleware,
        test_middleware_integration,
        test_decorator_combinations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All middleware tests passed! Enhanced middleware is working correctly.")
        return 0
    else:
        print("❌ Some middleware tests failed. Check the output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
