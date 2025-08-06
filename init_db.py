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
from models import db, User, Configuration, AuditLog
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
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created successfully")
            print("   Username: admin")
            print("   Password: Admin123!")
            print("   Email: admin@lab-automation.local")
        else:
            print("ℹ️  Admin user already exists")
        
        # Create user directories
        ensure_user_directories(admin_user.id)
        print("✅ User directories created")
        
        # Create additional test users
        test_users = [
            {
                'username': 'user1',
                'email': 'user1@lab-automation.local',
                'password': 'User123!',
                'role': 'user'
            },
            {
                'username': 'readonly1',
                'email': 'readonly1@lab-automation.local',
                'password': 'Read123!',
                'role': 'readonly'
            }
        ]
        
        for user_data in test_users:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(**user_data)
                db.session.add(user)
                ensure_user_directories(user.id)
                print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
        
        db.session.commit()
        print("\n🎉 Database initialization completed!")
        print("\n📋 Available users:")
        print("   Admin: admin / Admin123!")
        print("   User: user1 / User123!")
        print("   Read-only: readonly1 / Read123!")

def migrate_existing_configs():
    """Migrate existing configurations to user ownership"""
    app = create_app()
    
    with app.app_context():
        from pathlib import Path
        import yaml
        import json
        
        # Get admin user
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ Admin user not found. Run init_database() first.")
            return
        
        # Migrate configs from configs/pending to admin user
        pending_dir = Path("configs/pending")
        if pending_dir.exists():
            migrated_count = 0
            for config_file in pending_dir.glob("*.yaml"):
                try:
                    # Read existing config
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    # Extract service name from filename
                    service_name = config_file.stem.replace('unified_bridge_domain_', '')
                    
                    # Create configuration record
                    config = Configuration(
                        user_id=admin_user.id,
                        service_name=service_name,
                        vlan_id=0,  # Will be extracted from config data
                        config_type='bridge_domain'
                    )
                    
                    # Set config data
                    config.config_data = json.dumps(config_data)
                    config.file_path = str(config_file)
                    
                    # Extract VLAN ID if available
                    if config_data and '_metadata' in config_data:
                        metadata = config_data['_metadata']
                        if 'vlan_id' in metadata:
                            config.vlan_id = metadata['vlan_id']
                    
                    db.session.add(config)
                    migrated_count += 1
                    
                    # Move file to admin user directory
                    admin_pending_dir = Path(f"configs/users/{admin_user.id}/pending")
                    admin_pending_dir.mkdir(parents=True, exist_ok=True)
                    
                    new_path = admin_pending_dir / config_file.name
                    config_file.rename(new_path)
                    config.file_path = str(new_path)
                    
                except Exception as e:
                    print(f"⚠️  Failed to migrate {config_file}: {e}")
            
            db.session.commit()
            print(f"✅ Migrated {migrated_count} configurations to admin user")
        
        # Migrate deployed configs
        deployed_dir = Path("configs/deployed")
        if deployed_dir.exists():
            migrated_count = 0
            for config_file in deployed_dir.glob("*.yaml"):
                try:
                    # Read existing config
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    # Extract service name from filename
                    service_name = config_file.stem.replace('unified_bridge_domain_', '')
                    
                    # Create configuration record
                    config = Configuration(
                        user_id=admin_user.id,
                        service_name=service_name,
                        vlan_id=0,
                        config_type='bridge_domain',
                        status='deployed'
                    )
                    
                    # Set config data
                    config.config_data = json.dumps(config_data)
                    config.file_path = str(config_file)
                    
                    # Extract VLAN ID if available
                    if config_data and '_metadata' in config_data:
                        metadata = config_data['_metadata']
                        if 'vlan_id' in metadata:
                            config.vlan_id = metadata['vlan_id']
                    
                    db.session.add(config)
                    migrated_count += 1
                    
                    # Move file to admin user directory
                    admin_deployed_dir = Path(f"configs/users/{admin_user.id}/deployed")
                    admin_deployed_dir.mkdir(parents=True, exist_ok=True)
                    
                    new_path = admin_deployed_dir / config_file.name
                    config_file.rename(new_path)
                    config.file_path = str(new_path)
                    
                except Exception as e:
                    print(f"⚠️  Failed to migrate {config_file}: {e}")
            
            db.session.commit()
            print(f"✅ Migrated {migrated_count} deployed configurations to admin user")

if __name__ == "__main__":
    print("🚀 Initializing Lab Automation Database...")
    
    # Initialize database
    init_database()
    
    # Migrate existing configurations
    print("\n📦 Migrating existing configurations...")
    migrate_existing_configs()
    
    print("\n✅ Database setup completed successfully!") 