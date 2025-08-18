#!/usr/bin/env python3
"""
Logging Middleware
Provides comprehensive logging for API requests and responses
"""

from functools import wraps
from flask import request, jsonify, current_app, g
import time
import json
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class RequestLogger:
    """Request logging utility"""
    
    def __init__(self):
        self.request_id = None
        self.start_time = None
        self.user_id = None
        self.ip_address = None
        self.user_agent = None
    
    def start_request(self, request_id=None):
        """Start logging a request"""
        self.request_id = request_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.ip_address = request.remote_addr
        self.user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Log request start
        logger.info(f"Request started", extra={
            'request_id': self.request_id,
            'method': request.method,
            'path': request.path,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def end_request(self, response, status_code):
        """End logging a request"""
        if self.start_time is None:
            return
        
        duration = time.time() - self.start_time
        
        # Log request completion
        logger.info(f"Request completed", extra={
            'request_id': self.request_id,
            'method': request.method,
            'path': request.path,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def log_error(self, error, status_code=500):
        """Log request error"""
        if self.start_time is None:
            return
        
        duration = time.time() - self.start_time
        
        logger.error(f"Request failed", extra={
            'request_id': self.request_id,
            'method': request.method,
            'path': request.path,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2),
            'error': str(error),
            'error_type': type(error).__name__,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': datetime.utcnow().isoformat()
        })


def log_request(f):
    """Decorator to log API requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create request logger
        request_logger = RequestLogger()
        request_logger.start_request()
        
        # Store in Flask g for access in error handlers
        g.request_logger = request_logger
        
        try:
            # Execute the route function
            response = f(*args, **kwargs)
            
            # Handle different response types
            if isinstance(response, tuple):
                response_obj, status_code = response
                request_logger.end_request(response_obj, status_code)
                return response_obj, status_code
            else:
                request_logger.end_request(response, 200)
                return response
                
        except Exception as e:
            # Log error and re-raise
            request_logger.log_error(e)
            raise
    
    return decorated_function


def log_request_with_body(f):
    """Decorator to log API requests with request/response body"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create request logger
        request_logger = RequestLogger()
        request_logger.start_request()
        
        # Store in Flask g for access in error handlers
        g.request_logger = request_logger
        
        # Log request body if present
        if request.is_json:
            try:
                request_body = request.get_json()
                logger.debug(f"Request body", extra={
                    'request_id': request_logger.request_id,
                    'body': request_body
                })
            except Exception as e:
                logger.warning(f"Failed to parse request body: {e}")
        
        try:
            # Execute the route function
            response = f(*args, **kwargs)
            
            # Handle different response types
            if isinstance(response, tuple):
                response_obj, status_code = response
                
                # Log response body if it's JSON
                if hasattr(response_obj, 'json'):
                    try:
                        response_body = response_obj.json
                        logger.debug(f"Response body", extra={
                            'request_id': request_logger.request_id,
                            'status_code': status_code,
                            'body': response_body
                        })
                    except Exception as e:
                        logger.warning(f"Failed to log response body: {e}")
                
                request_logger.end_request(response_obj, status_code)
                return response_obj, status_code
            else:
                request_logger.end_request(response, 200)
                return response
                
        except Exception as e:
            # Log error and re-raise
            request_logger.log_error(e)
            raise
    
    return decorated_function


def log_sensitive_operation(operation_name):
    """Decorator to log sensitive operations with additional context"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create request logger
            request_logger = RequestLogger()
            request_logger.start_request()
            
            # Store in Flask g for access in error handlers
            g.request_logger = request_logger
            
            # Log sensitive operation start
            logger.warning(f"Sensitive operation started", extra={
                'request_id': request_logger.request_id,
                'operation': operation_name,
                'method': request.method,
                'path': request.path,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            try:
                # Execute the route function
                response = f(*args, **kwargs)
                
                # Log sensitive operation completion
                logger.warning(f"Sensitive operation completed", extra={
                    'request_id': request_logger.request_id,
                    'operation': operation_name,
                    'method': request.method,
                    'path': request.path,
                    'status': 'success',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                # Handle different response types
                if isinstance(response, tuple):
                    response_obj, status_code = response
                    request_logger.end_request(response_obj, status_code)
                    return response_obj, status_code
                else:
                    request_logger.end_request(response, 200)
                    return response
                    
            except Exception as e:
                # Log sensitive operation failure
                logger.error(f"Sensitive operation failed", extra={
                    'request_id': request_logger.request_id,
                    'operation': operation_name,
                    'method': request.method,
                    'path': request.path,
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                request_logger.log_error(e)
                raise
        
        return decorated_function
    return decorator


def log_performance(threshold_ms=1000):
    """Decorator to log slow requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Execute the route function
            response = f(*args, **kwargs)
            
            duration = time.time() - start_time
            duration_ms = round(duration * 1000, 2)
            
            # Log slow requests
            if duration_ms > threshold_ms:
                logger.warning(f"Slow request detected", extra={
                    'method': request.method,
                    'path': request.path,
                    'duration_ms': duration_ms,
                    'threshold_ms': threshold_ms,
                    'ip_address': request.remote_addr,
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            return response
        
        return decorated_function
    return decorator


def log_user_activity(activity_type):
    """Decorator to log user activity"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user ID from first argument (assuming it's current_user)
            user_id = None
            if args and hasattr(args[0], 'id'):
                user_id = args[0].id
            
            # Log user activity
            logger.info(f"User activity", extra={
                'user_id': user_id,
                'activity_type': activity_type,
                'method': request.method,
                'path': request.path,
                'ip_address': request.remote_addr,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Execute the route function
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def configure_request_logging(app):
    """Configure request logging for the Flask app"""
    
    # Add before_request handler to set up logging
    @app.before_request
    def before_request():
        # Generate request ID
        g.request_id = str(uuid.uuid4())
        
        # Set up basic request logging
        logger.info(f"Request received", extra={
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # Add after_request handler to log response
    @app.after_request
    def after_request(response):
        # Log response
        logger.info(f"Response sent", extra={
            'request_id': g.get('request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'content_length': len(response.get_data()),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
        
        return response
    
    # Add error handler to log errors
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log error
        logger.error(f"Unhandled exception", extra={
            'request_id': g.get('request_id', 'unknown'),
            'method': request.method,
            'path': request.path,
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Return error response
        return jsonify({
            'error': 'Internal server error',
            'request_id': g.get('request_id', 'unknown')
        }), 500


# Convenience decorators for common logging patterns
def log_auth_operation(f):
    """Log authentication operations"""
    return log_sensitive_operation('authentication')(f)


def log_admin_operation(f):
    """Log admin operations"""
    return log_sensitive_operation('admin_operation')(f)


def log_deployment_operation(f):
    """Log deployment operations"""
    return log_sensitive_operation('deployment')(f)


def log_configuration_change(f):
    """Log configuration changes"""
    return log_sensitive_operation('configuration_change')(f)
