#!/usr/bin/env python3
"""
Rate Limiting Middleware
Provides rate limiting functionality for API endpoints
"""

from functools import wraps
from flask import request, jsonify, current_app
import time
import threading
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, key):
        """Check if request is allowed"""
        now = time.time()
        
        with self.lock:
            # Clean old requests
            while self.requests[key] and self.requests[key][0] < now - self.window_seconds:
                self.requests[key].popleft()
            
            # Check if under limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                return True, self.max_requests - len(self.requests[key])
            
            return False, 0
    
    def get_remaining(self, key):
        """Get remaining requests for a key"""
        now = time.time()
        
        with self.lock:
            # Clean old requests
            while self.requests[key] and self.requests[key][0] < now - self.window_seconds:
                self.requests[key].popleft()
            
            return self.max_requests - len(self.requests[key])


# Global rate limiters
rate_limiters = {
    'default': RateLimiter(max_requests=100, window_seconds=60),
    'auth': RateLimiter(max_requests=10, window_seconds=60),  # Stricter for auth
    'deployment': RateLimiter(max_requests=20, window_seconds=60),  # Moderate for deployments
    'admin': RateLimiter(max_requests=50, window_seconds=60),  # Higher for admin operations
}


def rate_limit(limiter_name='default', key_func=None):
    """
    Rate limiting decorator
    
    Args:
        limiter_name: Name of the rate limiter to use
        key_func: Function to generate rate limit key (defaults to IP address)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get the appropriate rate limiter
            limiter = rate_limiters.get(limiter_name, rate_limiters['default'])
            
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                # Default to IP address
                key = request.remote_addr or 'unknown'
            
            # Check rate limit
            allowed, remaining = limiter.is_allowed(key)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {key} on {limiter_name}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limiter.max_requests} per {limiter.window_seconds} seconds',
                    'retry_after': limiter.window_seconds
                }), 429
            
            # Add rate limit headers
            response = f(*args, **kwargs)
            if isinstance(response, tuple):
                response_obj, status_code = response
                if hasattr(response_obj, 'headers'):
                    response_obj.headers['X-RateLimit-Limit'] = limiter.max_requests
                    response_obj.headers['X-RateLimit-Remaining'] = remaining
                    response_obj.headers['X-RateLimit-Reset'] = int(time.time() + limiter.window_seconds)
                return response_obj, status_code
            else:
                # If it's just a response object, we can't add headers easily
                # In a real implementation, you might want to use Flask's response object
                return response
        
        return decorated_function
    return decorator


def rate_limit_by_user(limiter_name='default'):
    """Rate limit by user ID (requires authenticated user)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This assumes the first argument is the current_user
            # You might need to adjust based on your route signature
            if args and hasattr(args[0], 'id'):
                user_id = args[0].id
                key = f"user_{user_id}"
            else:
                # Fallback to IP if no user
                key = request.remote_addr or 'unknown'
            
            limiter = rate_limiters.get(limiter_name, rate_limiters['default'])
            allowed, remaining = limiter.is_allowed(key)
            
            if not allowed:
                logger.warning(f"User rate limit exceeded for {key} on {limiter_name}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limiter.max_requests} per {limiter.window_seconds} seconds',
                    'retry_after': limiter.window_seconds
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def rate_limit_by_ip(limiter_name='default'):
    """Rate limit by IP address"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = request.remote_addr or 'unknown'
            limiter = rate_limiters.get(limiter_name, rate_limiters['default'])
            allowed, remaining = limiter.is_allowed(key)
            
            if not allowed:
                logger.warning(f"IP rate limit exceeded for {key} on {limiter_name}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limiter.max_requests} per {limiter.window_seconds} seconds',
                    'retry_after': limiter.window_seconds
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def get_rate_limit_info(limiter_name='default', key=None):
    """Get rate limit information for a key"""
    if key is None:
        key = request.remote_addr or 'unknown'
    
    limiter = rate_limiters.get(limiter_name, rate_limiters['default'])
    remaining = limiter.get_remaining(key)
    
    return {
        'limit': limiter.max_requests,
        'remaining': remaining,
        'reset_time': int(time.time() + limiter.window_seconds),
        'window_seconds': limiter.window_seconds
    }


def configure_rate_limits(config):
    """Configure rate limits from application config"""
    global rate_limiters
    
    # Update existing limiters or create new ones based on config
    for name, settings in config.get('RATE_LIMITS', {}).items():
        max_requests = settings.get('max_requests', 100)
        window_seconds = settings.get('window_seconds', 60)
        
        if name in rate_limiters:
            # Update existing limiter
            rate_limiters[name].max_requests = max_requests
            rate_limiters[name].window_seconds = window_seconds
        else:
            # Create new limiter
            rate_limiters[name] = RateLimiter(max_requests, window_seconds)
    
    logger.info(f"Configured {len(rate_limiters)} rate limiters")


# Convenience decorators for common use cases
def auth_rate_limit(f):
    """Rate limit authentication endpoints"""
    return rate_limit('auth')(f)


def deployment_rate_limit(f):
    """Rate limit deployment endpoints"""
    return rate_limit('deployment')(f)


def admin_rate_limit(f):
    """Rate limit admin endpoints"""
    return rate_limit('admin')(f)


def user_rate_limit(f):
    """Rate limit by user ID"""
    return rate_limit_by_user('default')(f)
