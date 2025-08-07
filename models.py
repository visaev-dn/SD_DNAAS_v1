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
import json

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
    is_admin = db.Column(db.Boolean, default=False)  # Additional admin flag
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin who created this user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship to configurations (owned by user)
    configurations = db.relationship('Configuration', backref='owner', lazy=True, 
                                   foreign_keys='Configuration.user_id', cascade='all, delete-orphan')
    
    # Relationship to configurations deployed by user
    deployed_configurations = db.relationship('Configuration', backref='deployer', lazy=True,
                                            foreign_keys='Configuration.deployed_by')
    
    # Relationship to VLAN allocations
    vlan_allocations = db.relationship('UserVlanAllocation', backref='user', lazy=True,
                                     cascade='all, delete-orphan')
    
    # Relationship to user permissions
    permissions = db.relationship('UserPermission', backref='user', lazy=True,
                                uselist=False, cascade='all, delete-orphan')
    
    # Relationship to personal bridge domains
    personal_bridge_domains = db.relationship('PersonalBridgeDomain', backref='user', lazy=True,
                                            cascade='all, delete-orphan')
    
    def __init__(self, username: str, email: str, password: str, role: str = 'user', created_by: Optional[int] = None):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        self.role = role
        self.is_admin = (role == 'admin')
        self.created_by = created_by
    
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
            'is_admin': self.is_admin,
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
        if self.role == 'admin' or self.is_admin:
            return True
        elif self.role == 'user':
            return permission in ['read', 'write', 'deploy']
        elif self.role == 'readonly':
            return permission == 'read'
        return False
    
    def get_vlan_ranges(self) -> list:
        """Get user's VLAN ranges"""
        ranges = []
        for allocation in self.vlan_allocations:
            if allocation.is_active:
                ranges.append({
                    'id': allocation.id,
                    'startVlan': allocation.start_vlan,
                    'endVlan': allocation.end_vlan,
                    'description': allocation.description
                })
        return ranges
    
    def has_access_to_vlan(self, vlan_id: int) -> bool:
        """Check if user has access to a specific VLAN"""
        for allocation in self.vlan_allocations:
            if allocation.is_active and allocation.start_vlan <= vlan_id <= allocation.end_vlan:
                return True
        return False
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'vlanRanges': self.get_vlan_ranges(),
            'permissions': self.permissions.to_dict() if self.permissions else None
        }

class UserVlanAllocation(db.Model):
    """User VLAN allocation model"""
    
    __tablename__ = 'user_vlan_allocations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_vlan = db.Column(db.Integer, nullable=False)
    end_vlan = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id: int, start_vlan: int, end_vlan: int, description: str = ''):
        self.user_id = user_id
        self.start_vlan = start_vlan
        self.end_vlan = end_vlan
        self.description = description
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'startVlan': self.start_vlan,
            'endVlan': self.end_vlan,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserPermission(db.Model):
    """User permissions model"""
    
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    can_edit_topology = db.Column(db.Boolean, default=True)
    can_deploy_changes = db.Column(db.Boolean, default=True)
    can_view_global = db.Column(db.Boolean, default=False)
    can_edit_others = db.Column(db.Boolean, default=False)
    max_bridge_domains = db.Column(db.Integer, default=50)
    require_approval = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id: int, **kwargs):
        self.user_id = user_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'canEditTopology': self.can_edit_topology,
            'canDeployChanges': self.can_deploy_changes,
            'canViewGlobal': self.can_view_global,
            'canEditOthers': self.can_edit_others,
            'maxBridgeDomains': self.max_bridge_domains,
            'requireApproval': self.require_approval,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PersonalBridgeDomain(db.Model):
    """Personal workspace bridge domains"""
    
    __tablename__ = 'personal_bridge_domains'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bridge_domain_name = db.Column(db.String(100), nullable=False)
    imported_from_topology = db.Column(db.Boolean, default=False)
    topology_scanned = db.Column(db.Boolean, default=False)
    last_scan_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id: int, bridge_domain_name: str, imported_from_topology: bool = False):
        self.user_id = user_id
        self.bridge_domain_name = bridge_domain_name
        self.imported_from_topology = imported_from_topology
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bridge_domain_name': self.bridge_domain_name,
            'imported_from_topology': self.imported_from_topology,
            'topology_scanned': self.topology_scanned,
            'last_scan_at': self.last_scan_at.isoformat() if self.last_scan_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
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
            'config_metadata': self.config_metadata,
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
        elif status == 'deleted':
            self.deployed_at = None
            self.deployed_by = None

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
        self.details = json.dumps(details) if details else None
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