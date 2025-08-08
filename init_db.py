#!/usr/bin/env python3
"""
Database initialization script for Lab Automation Framework
Creates SQLite database and initial admin user
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, User, Configuration, AuditLog, UserVlanAllocation, UserPermission, PersonalBridgeDomain, TopologyScan, DeviceInterface, TopologyPath
from auth import ensure_user_directories

def create_app():
    """Create Flask app for database initialization"""
    app = Flask(__name__)
    
    # Configure SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_automation.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    
    # Initialize database
    db.init_app(app)
    
    return app

def init_database():
    """Initialize database and create tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@lab-automation.local',
                password='Admin123!',
                role='admin',
                created_by=None  # Admin is self-created
            )
            admin_user.is_admin = True
            db.session.add(admin_user)
            db.session.commit()
            
            # Create admin VLAN allocations (full range for admin)
            admin_vlan_allocation = UserVlanAllocation(
                user_id=admin_user.id,
                start_vlan=1,
                end_vlan=4094,
                description='Admin full VLAN range'
            )
            db.session.add(admin_vlan_allocation)
            
            # Create admin permissions (full access)
            admin_permissions = UserPermission(
                user_id=admin_user.id,
                can_edit_topology=True,
                can_deploy_changes=True,
                can_view_global=True,
                can_edit_others=True,
                max_bridge_domains=1000,
                require_approval=False
            )
            db.session.add(admin_permissions)
            
            db.session.commit()
            print("✅ Admin user created successfully")
            print("   Username: admin")
            print("   Password: Admin123!")
            print("   Email: admin@lab-automation.local")
            print("   VLAN Range: 1-4094 (Full access)")
            print("   Permissions: Full admin access")
        else:
            print("ℹ️  Admin user already exists")
        
        # Create user directories
        ensure_user_directories(admin_user.id)
        print("✅ User directories created")
        
        # Create additional test users with VLAN ranges
        test_users = [
            {
                'username': 'user1',
                'email': 'user1@lab-automation.local',
                'password': 'User123!',
                'role': 'user',
                'vlan_ranges': [
                    {'start': 100, 'end': 199, 'description': 'User1 VLAN Range 1'},
                    {'start': 200, 'end': 299, 'description': 'User1 VLAN Range 2'}
                ],
                'permissions': {
                    'can_edit_topology': True,
                    'can_deploy_changes': True,
                    'can_view_global': False,
                    'can_edit_others': False,
                    'max_bridge_domains': 50,
                    'require_approval': False
                }
            },
            {
                'username': 'user2',
                'email': 'user2@lab-automation.local',
                'password': 'User123!',
                'role': 'user',
                'vlan_ranges': [
                    {'start': 300, 'end': 399, 'description': 'User2 VLAN Range'}
                ],
                'permissions': {
                    'can_edit_topology': True,
                    'can_deploy_changes': True,
                    'can_view_global': False,
                    'can_edit_others': False,
                    'max_bridge_domains': 30,
                    'require_approval': True
                }
            },
            {
                'username': 'readonly1',
                'email': 'readonly1@lab-automation.local',
                'password': 'Read123!',
                'role': 'readonly',
                'vlan_ranges': [
                    {'start': 400, 'end': 499, 'description': 'ReadOnly VLAN Range'}
                ],
                'permissions': {
                    'can_edit_topology': False,
                    'can_deploy_changes': False,
                    'can_view_global': True,
                    'can_edit_others': False,
                    'max_bridge_domains': 10,
                    'require_approval': True
                }
            }
        ]
        
        for user_data in test_users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                # Create user
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    role=user_data['role'],
                    created_by=admin_user.id
                )
                db.session.add(user)
                db.session.flush()  # Get user ID
                
                # Create VLAN allocations
                for vlan_range in user_data['vlan_ranges']:
                    vlan_allocation = UserVlanAllocation(
                        user_id=user.id,
                        start_vlan=vlan_range['start'],
                        end_vlan=vlan_range['end'],
                        description=vlan_range['description']
                    )
                    db.session.add(vlan_allocation)
                
                # Create permissions
                permissions = UserPermission(
                    user_id=user.id,
                    **user_data['permissions']
                )
                db.session.add(permissions)
                
                # Create user directories
                ensure_user_directories(user.id)
                
                print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
                vlan_ranges_str = ', '.join([f"{r['start']}-{r['end']}" for r in user_data['vlan_ranges']])
                print(f"   VLAN Ranges: {vlan_ranges_str}")
        
        db.session.commit()
        print("\n🎉 Database initialization completed!")
        print("\n📋 Available users:")
        print("   Admin: admin / Admin123! (VLAN: 1-4094, Full access)")
        print("   User1: user1 / User123! (VLAN: 100-199, 200-299)")
        print("   User2: user2 / User123! (VLAN: 300-399)")
        print("   ReadOnly: readonly1 / Read123! (VLAN: 400-499, Read-only)")

def migrate_existing_configs():
    """Migrate existing configurations to user ownership"""
    app = create_app()
    
    with app.app_context():
        # Get admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found. Please run init_database() first.")
            return
        
        # Find configurations without user_id and assign to admin
        orphaned_configs = Configuration.query.filter_by(user_id=None).all()
        
        if orphaned_configs:
            print(f"🔄 Migrating {len(orphaned_configs)} orphaned configurations to admin user...")
            
            for config in orphaned_configs:
                config.user_id = admin_user.id
                print(f"   Migrated: {config.service_name}")
            
            db.session.commit()
            print("✅ Migration completed successfully")
        else:
            print("ℹ️  No orphaned configurations found")

def create_user_with_vlan_ranges(username: str, email: str, password: str, vlan_ranges: list, 
                                permissions: dict = None, created_by: int = None):
    """Create a new user with VLAN ranges and permissions"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ User {username} already exists")
            return None
        
        # Create user
        user = User(
            username=username,
            email=email,
            password=password,
            role='user',
            created_by=created_by
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create VLAN allocations
        for vlan_range in vlan_ranges:
            vlan_allocation = UserVlanAllocation(
                user_id=user.id,
                start_vlan=vlan_range['start'],
                end_vlan=vlan_range['end'],
                description=vlan_range.get('description', '')
            )
            db.session.add(vlan_allocation)
        
        # Create permissions (use defaults if not provided)
        if permissions is None:
            permissions = {
                'can_edit_topology': True,
                'can_deploy_changes': True,
                'can_view_global': False,
                'can_edit_others': False,
                'max_bridge_domains': 50,
                'require_approval': False
            }
        
        user_permissions = UserPermission(
            user_id=user.id,
            **permissions
        )
        db.session.add(user_permissions)
        
        # Create user directories
        ensure_user_directories(user.id)
        
        db.session.commit()
        
        print(f"✅ Created user: {username}")
        print(f"   Email: {email}")
        vlan_ranges_str = ', '.join([f"{r['start']}-{r['end']}" for r in vlan_ranges])
        print(f"   VLAN Ranges: {vlan_ranges_str}")
        
        return user

if __name__ == '__main__':
    print("🚀 Initializing Lab Automation Database...")
    
    # Initialize database
    init_database()
    
    # Migrate existing configurations
    migrate_existing_configs()
    
    print("\n✨ Database setup complete!")
    print("\n📝 Next steps:")
    print("   1. Start the API server: python api_server.py")
    print("   2. Access the web interface")
    print("   3. Login with admin credentials")
    print("   4. Create additional users through the admin interface") 