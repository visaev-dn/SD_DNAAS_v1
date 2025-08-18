#!/usr/bin/env python3
"""
Authentication Routes
Handles user registration, login, logout, and token management
"""

from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import logging

from api.v1 import api_v1
from models import db, User, AuditLog
from auth import create_audit_log

logger = logging.getLogger(__name__)


@api_v1.route('/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            password=hashed_password,
            email=email,
            role=role,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create audit log
        create_audit_log(
            user_id=new_user.id,
            action='user_registered',
            details=f'New user registered: {username}',
            ip_address=request.remote_addr
        )
        
        logger.info(f"New user registered: {username}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': new_user.id,
            'username': username
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@api_v1.route('/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token_payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(
            token_payload, 
            current_app.config['SECRET_KEY'], 
            algorithm='HS256'
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create audit log
        create_audit_log(
            user_id=user.id,
            action='user_login',
            details=f'User logged in from {request.remote_addr}',
            ip_address=request.remote_addr
        )
        
        logger.info(f"User logged in: {username}")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@api_v1.route('/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Decode token to get user info
        try:
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
            user_id = payload['user_id']
            username = payload['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Create audit log
        create_audit_log(
            user_id=user_id,
            action='user_logout',
            details=f'User logged out from {request.remote_addr}',
            ip_address=request.remote_addr
        )
        
        logger.info(f"User logged out: {username}")
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500


@api_v1.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """Token refresh endpoint"""
    try:
        # Get current token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        current_token = auth_header.split(' ')[1]
        
        # Decode current token
        try:
            payload = jwt.decode(
                current_token, 
                current_app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Generate new token
        new_token_payload = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        new_token = jwt.encode(
            new_token_payload, 
            current_app.config['SECRET_KEY'], 
            algorithm='HS256'
        )
        
        logger.info(f"Token refreshed for user: {payload['username']}")
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'token': new_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


@api_v1.route('/auth/me', methods=['GET'])
def get_current_user():
    """Get current user information"""
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Decode token
        try:
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get user from database
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500


@api_v1.route('/auth/change-password', methods=['POST'])
def change_password():
    """Change user password endpoint"""
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Decode token
        try:
            payload = jwt.decode(
                token, 
                current_app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new passwords are required'}), 400
        
        # Get user
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify current password
        if not check_password_hash(user.password, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        # Create audit log
        create_audit_log(
            user_id=user.id,
            action='password_changed',
            details='Password changed successfully',
            ip_address=request.remote_addr
        )
        
        logger.info(f"Password changed for user: {user.username}")
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Change password error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to change password'}), 500
