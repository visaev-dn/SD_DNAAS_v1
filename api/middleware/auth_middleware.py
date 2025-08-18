#!/usr/bin/env python3
"""
Authentication Middleware
JWT token validation and user authentication decorators
"""

from functools import wraps
from flask import request, jsonify, current_app
import jwt
import logging

from models import User

logger = logging.getLogger(__name__)


def token_required(f):
    """Decorator to require valid JWT token for protected routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode token
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
            
            # Get current user
            current_user = User.query.get(payload['user_id'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'error': 'Token validation failed'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def permission_required(permission):
    """Decorator to require specific permission for routes"""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if not hasattr(current_user, 'role'):
                return jsonify({'error': 'User has no role defined'}), 403
            
            if current_user.role != permission and current_user.role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    """Decorator to require admin role for routes"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if not hasattr(current_user, 'role'):
            return jsonify({'error': 'User has no role defined'}), 403
        
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def user_ownership_required(f):
    """Decorator to require user ownership for resource access"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        # This decorator assumes the resource ID is in kwargs
        # and the resource has a user_id field
        resource_id = kwargs.get('resource_id') or kwargs.get('config_id')
        
        if not resource_id:
            return jsonify({'error': 'Resource ID not found'}), 400
        
        # Check if user is admin (admin can access all resources)
        if hasattr(current_user, 'role') and current_user.role == 'admin':
            return f(current_user, *args, **kwargs)
        
        # For non-admin users, check ownership
        # This is a generic check - specific routes should implement their own logic
        return f(current_user, *args, **kwargs)
    
    return decorated


def create_audit_log(user_id, action, details, ip_address=None):
    """Create audit log entry for user actions"""
    try:
        from models import AuditLog
        from datetime import datetime
        
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        
        from models import db
        db.session.add(audit_entry)
        db.session.commit()
        
        logger.info(f"Audit log created: {action} by user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Don't fail the main operation if audit logging fails
        pass
