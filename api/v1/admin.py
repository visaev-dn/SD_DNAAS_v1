#!/usr/bin/env python3
"""
Admin Routes
User management endpoints
"""

from flask import request, jsonify
from datetime import datetime
import logging

from api.v1 import api_v1
from api.middleware.auth_middleware import token_required, admin_required
from models import db, User

logger = logging.getLogger(__name__)


@api_v1.route('/admin/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    try:
        users = User.query.all()
        items = [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_login': u.last_login.isoformat() if u.last_login else None
        } for u in users]
        return jsonify({'users': items, 'total': len(items)})
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({'error': 'Failed to list users'}), 500


@api_v1.route('/admin/users', methods=['POST'])
@token_required
@admin_required
def create_user(current_user):
    try:
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'user')
        
        if not username or not password:
            return jsonify({'error': 'username and password are required'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        user = User(username=username, email=email, role=role, created_at=datetime.utcnow())
        # NOTE: In original code, password hashing is handled elsewhere; add hashing if needed
        user.password = password
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'user_id': user.id}), 201
    except Exception as e:
        logger.error(f"Create user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create user'}), 500


@api_v1.route('/admin/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(current_user, user_id: int):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json() or {}
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Update user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update user'}), 500


@api_v1.route('/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id: int):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500
