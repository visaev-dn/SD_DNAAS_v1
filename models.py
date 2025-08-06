#!/usr/bin/env python3
"""
Database Models for Lab Automation Framework
Defines User and Configuration models with proper relationships
"""

from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
from typing import Optional

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user, readonly
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship to configurations (owned by user)
    configurations = db.relationship('Configuration', backref='owner', lazy=True, 
                                   foreign_keys='Configuration.user_id', cascade='all, delete-orphan')
    
    # Relationship to configurations deployed by user
    deployed_configurations = db.relationship('Configuration', backref='deployer', lazy=True,
                                            foreign_keys='Configuration.deployed_by')
    
    def __init__(self, username: str, email: str, password: str, role: str = 'user'):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        self.role = role
    
    def set_password(self, password: str):
        """Set password with hashing"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': self.id,
            'username': self.username,
            'role': self.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    @staticmethod
    def verify_token(token: str) -> Optional['User']:
        """Verify JWT token and return user"""
        try:
            secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return User.query.get(payload['user_id'])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.role == 'admin':
            return True
        elif self.role == 'user':
            return permission in ['read', 'write', 'deploy']
        elif self.role == 'readonly':
            return permission == 'read'
        return False
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Configuration(db.Model):
    """Configuration model for user configurations"""
    
    __tablename__ = 'configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_name = db.Column(db.String(255), nullable=False)
    vlan_id = db.Column(db.Integer, nullable=False)
    config_type = db.Column(db.String(50), default='bridge_domain')  # bridge_domain, etc.
    status = db.Column(db.String(20), default='pending')  # pending, deployed, failed, deleted
    config_data = db.Column(db.Text)  # JSON string of configuration
    config_metadata = db.Column(db.Text)  # JSON string of metadata (path_calculation, destinations, etc.)
    file_path = db.Column(db.String(500))  # Path to configuration file
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deployed_at = db.Column(db.DateTime)
    deployed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __init__(self, user_id: int, service_name: str, vlan_id: int, config_type: str = 'bridge_domain'):
        self.user_id = user_id
        self.service_name = service_name
        self.vlan_id = vlan_id
        self.config_type = config_type
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'service_name': self.service_name,
            'vlan_id': self.vlan_id,
            'config_type': self.config_type,
            'status': self.status,
            'config_data': self.config_data,
            'metadata': self.config_metadata,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'deployed_by': self.deployed_by
        }
    
    def update_status(self, status: str, deployed_by: Optional[int] = None):
        """Update configuration status"""
        self.status = status
        if status == 'deployed':
            self.deployed_at = datetime.utcnow()
            self.deployed_by = deployed_by
        db.session.commit()

class AuditLog(db.Model):
    """Audit log for tracking user actions"""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # create, update, delete, deploy
    resource_type = db.Column(db.String(50), nullable=False)  # configuration, user, etc.
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)  # JSON string of action details
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = db.relationship('User', backref='audit_logs')
    
    def __init__(self, user_id: int, action: str, resource_type: str, resource_id: Optional[int] = None, 
                 details: Optional[dict] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        self.user_id = user_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = str(details) if details else None
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def to_dict(self) -> dict:
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        } 