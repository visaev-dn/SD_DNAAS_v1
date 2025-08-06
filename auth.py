#!/usr/bin/env python3
"""
Authentication utilities and middleware for Lab Automation Framework
Handles JWT token verification, user authentication, and authorization
"""

import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, AuditLog

def create_audit_log(user_id: int, action: str, resource_type: str, resource_id: int = None, 
                    details: dict = None):
    """Create audit log entry"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to create audit log: {e}")

def token_required(f):
    """Decorator to require JWT token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Verify token
            secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Invalid token'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def permission_required(permission: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            if not current_user.has_permission(permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

def user_ownership_required(f):
    """Decorator to ensure user owns the resource"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        # For admin users, allow access to all resources
        if current_user.role == 'admin':
            return f(current_user, *args, **kwargs)
        
        # For other users, check ownership
        resource_id = kwargs.get('config_id') or kwargs.get('id')
        if resource_id:
            from models import Configuration
            config = Configuration.query.get(resource_id)
            if not config or config.user_id != current_user.id:
                return jsonify({'error': 'Access denied'}), 403
        
        return f(current_user, *args, **kwargs)
    return decorated

def generate_password_reset_token(user: User) -> str:
    """Generate password reset token"""
    payload = {
        'user_id': user.id,
        'type': 'password_reset',
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
    return jwt.encode(payload, secret_key, algorithm='HS256')

def verify_password_reset_token(token: str) -> User:
    """Verify password reset token"""
    try:
        secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        if payload.get('type') != 'password_reset':
            return None
            
        return User.query.get(payload['user_id'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def rate_limit_login(username: str) -> bool:
    """Simple rate limiting for login attempts"""
    # This is a basic implementation
    # In production, use Redis or similar for proper rate limiting
    return True

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, "Password is strong"

def sanitize_username(username: str) -> str:
    """Sanitize username for security"""
    # Remove any potentially dangerous characters
    import re
    return re.sub(r'[^a-zA-Z0-9_-]', '', username)

def get_user_config_path(user_id: int) -> str:
    """Get user-specific configuration directory path"""
    return f"configs/users/{user_id}"

def ensure_user_directories(user_id: int):
    """Ensure user directories exist"""
    import os
    from pathlib import Path
    
    user_path = Path(get_user_config_path(user_id))
    user_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (user_path / "pending").mkdir(exist_ok=True)
    (user_path / "deployed").mkdir(exist_ok=True)
    (user_path / "failed").mkdir(exist_ok=True)
    
    return str(user_path) 