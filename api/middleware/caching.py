#!/usr/bin/env python3
"""
Caching Middleware
Provides response caching for improved API performance
"""

from functools import wraps
from flask import request, jsonify, current_app, g
import hashlib
import json
import time
import threading
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with expiration and metadata"""
    
    def __init__(self, data, ttl_seconds=300):
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = time.time()
    
    def is_expired(self):
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def access(self):
        """Mark entry as accessed"""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def get_age(self):
        """Get age of cache entry in seconds"""
        return time.time() - self.created_at


class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.RLock()
    
    def get(self, key):
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired():
                    # Remove expired entry
                    del self.cache[key]
                    return None
                
                # Mark as accessed and move to end (most recently used)
                entry.access()
                self.cache.move_to_end(key)
                return entry.data
            
            return None
    
    def set(self, key, value, ttl_seconds=300):
        """Set value in cache"""
        with self.lock:
            # Remove if key already exists
            if key in self.cache:
                del self.cache[key]
            
            # Add new entry
            self.cache[key] = CacheEntry(value, ttl_seconds)
            
            # Remove oldest entries if cache is full
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
    
    def delete(self, key):
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self):
        """Get cache statistics"""
        with self.lock:
            total_entries = len(self.cache)
            expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
            active_entries = total_entries - expired_entries
            
            return {
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': expired_entries,
                'max_size': self.max_size,
                'utilization_percent': (total_entries / self.max_size) * 100
            }


# Global cache instance
api_cache = LRUCache(max_size=1000)


def generate_cache_key(*args, **kwargs):
    """Generate cache key from function arguments and request data"""
    # Include request path and method
    key_parts = [
        request.method,
        request.path,
        str(sorted(request.args.items())),
        str(sorted(request.headers.items())),
        str(args),
        str(sorted(kwargs.items()))
    ]
    
    # Create hash of key parts
    key_string = '|'.join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_response(ttl_seconds=300, key_func=None, condition_func=None):
    """
    Cache API response decorator
    
    Args:
        ttl_seconds: Time to live for cache entry in seconds
        key_func: Custom function to generate cache key
        condition_func: Function to determine if response should be cached
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key(*args, **kwargs)
            
            # Check if response is in cache
            cached_response = api_cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_response
            
            # Execute function and cache response
            response = f(*args, **kwargs)
            
            # Check if response should be cached
            if condition_func and not condition_func(response):
                return response
            
            # Cache successful responses (status code < 400)
            if isinstance(response, tuple):
                response_obj, status_code = response
                if status_code < 400:
                    api_cache.set(cache_key, (response_obj, status_code), ttl_seconds)
                    logger.debug(f"Cached response for key: {cache_key}, TTL: {ttl_seconds}s")
            else:
                # Single response object
                api_cache.set(cache_key, response, ttl_seconds)
                logger.debug(f"Cached response for key: {cache_key}, TTL: {ttl_seconds}s")
            
            return response
        
        return decorated_function
    return decorator


def cache_by_user(ttl_seconds=300):
    """Cache response by user ID"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user ID from first argument (assuming it's current_user)
            user_id = None
            if args and hasattr(args[0], 'id'):
                user_id = args[0].id
            
            # Generate user-specific cache key
            def user_cache_key(*args, **kwargs):
                base_key = generate_cache_key(*args, **kwargs)
                return f"user_{user_id}_{base_key}"
            
            return cache_response(ttl_seconds, user_cache_key)(f)(*args, **kwargs)
        
        return decorated_function
    return decorator


def cache_by_parameters(ttl_seconds=300, param_names=None):
    """Cache response by specific request parameters"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate parameter-specific cache key
            def param_cache_key(*args, **kwargs):
                base_key = generate_cache_key(*args, **kwargs)
                if param_names:
                    # Include specific parameters in cache key
                    param_values = []
                    for param in param_names:
                        value = request.args.get(param) or request.json.get(param) if request.is_json else None
                        param_values.append(f"{param}={value}")
                    param_string = '|'.join(param_values)
                    return f"{base_key}_{param_string}"
                return base_key
            
            return cache_response(ttl_seconds, param_cache_key)(f)(*args, **kwargs)
        
        return decorated_function
    return decorator


def invalidate_cache(pattern=None, key_func=None):
    """
    Invalidate cache entries
    
    Args:
        pattern: Pattern to match cache keys for invalidation
        key_func: Function to generate cache key for invalidation
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute function first
            response = f(*args, **kwargs)
            
            # Invalidate cache
            if pattern:
                # Invalidate by pattern (e.g., all user-related cache)
                keys_to_delete = []
                for key in list(api_cache.cache.keys()):
                    if pattern in key:
                        keys_to_delete.append(key)
                
                for key in keys_to_delete:
                    api_cache.delete(key)
                
                logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")
            
            elif key_func:
                # Invalidate specific cache key
                cache_key = key_func(*args, **kwargs)
                api_cache.delete(cache_key)
                logger.info(f"Invalidated cache key: {cache_key}")
            
            return response
        
        return decorated_function
    return decorator


def cache_stats():
    """Get cache statistics endpoint"""
    return jsonify(api_cache.get_stats())


def clear_cache():
    """Clear all cache entries"""
    api_cache.clear()
    return jsonify({'message': 'Cache cleared successfully'})


def configure_caching(app):
    """Configure caching for the Flask app"""
    
    # Add cache statistics endpoint
    @app.route('/api/cache/stats', methods=['GET'])
    def get_cache_stats():
        return cache_stats()
    
    # Add cache clear endpoint (admin only)
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_all_cache():
        clear_cache()
        return jsonify({'message': 'Cache cleared successfully'})
    
    logger.info("Caching middleware configured")


# Convenience decorators for common caching patterns
def cache_dashboard_data(ttl_seconds=60):
    """Cache dashboard data (short TTL for real-time feel)"""
    return cache_response(ttl_seconds)


def cache_configuration_data(ttl_seconds=300):
    """Cache configuration data (medium TTL)"""
    return cache_response(ttl_seconds)


def cache_topology_data(ttl_seconds=600):
    """Cache topology data (longer TTL as it changes less frequently)"""
    return cache_response(ttl_seconds)


def invalidate_user_cache(user_id):
    """Invalidate all cache entries for a specific user"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Invalidate user-specific cache
            pattern = f"user_{user_id}_"
            keys_to_delete = []
            for key in list(api_cache.cache.keys()):
                if pattern in key:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                api_cache.delete(key)
            
            logger.info(f"Invalidated {len(keys_to_delete)} cache entries for user {user_id}")
            return response
        
        return decorated_function
    return decorator
