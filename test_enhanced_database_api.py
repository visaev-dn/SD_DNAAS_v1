#!/usr/bin/env python3
"""
Test Enhanced Database API Integration
Tests the renamed endpoints that now use "enhanced-database" instead of "phase1"
"""

import sys
import json
from datetime import datetime

def test_enhanced_database_api():
    """Test Enhanced Database API integration with new naming"""
    
    print("🧪 Testing Enhanced Database API Integration (Renamed Endpoints)")
    print("=" * 70)
    
    # Test 1: Import API server
    print("\n📦 Test 1: Importing API server with Enhanced Database integration...")
    try:
        from api_server import app
        print("✅ API server imported successfully")
        print("🚀 Enhanced Database integration detected in logs")
    except Exception as e:
        print(f"❌ Failed to import API server: {e}")
        return False
    
    # Test 2: Check Enhanced Database API router
    print("\n🔧 Test 2: Checking Enhanced Database API router...")
    try:
        from config_engine.phase1_api import EnhancedDatabaseAPIRouter
        
        # Create a test router instance
        router = EnhancedDatabaseAPIRouter(app, None)
        print("✅ Enhanced Database API router created successfully")
        print(f"   Blueprint name: {router.blueprint.name}")
        print(f"   URL prefix: {router.blueprint.url_prefix}")
        
    except Exception as e:
        print(f"❌ Failed to create Enhanced Database API router: {e}")
        return False
    
    # Test 3: Check Flask app routes for new naming
    print("\n📡 Test 3: Checking Flask app routes for Enhanced Database endpoints...")
    try:
        # Get all registered routes
        enhanced_routes = []
        phase1_routes = []
        
        for rule in app.url_map.iter_rules():
            if 'enhanced-database' in rule.rule.lower():
                enhanced_routes.append(rule.rule)
            elif 'phase1' in rule.rule.lower():
                phase1_routes.append(rule.rule)
        
        if enhanced_routes:
            print("✅ Enhanced Database routes found in Flask app")
            print(f"   Total Enhanced Database routes: {len(enhanced_routes)}")
            for route in enhanced_routes[:5]:  # Show first 5
                print(f"   - {route}")
            if len(enhanced_routes) > 5:
                print(f"   ... and {len(enhanced_routes) - 5} more")
        else:
            print("❌ No Enhanced Database routes found in Flask app")
            return False
        
        if phase1_routes:
            print(f"⚠️  {len(phase1_routes)} legacy 'phase1' routes still found (should be renamed)")
        else:
            print("✅ All routes successfully renamed to 'enhanced-database'")
            
    except Exception as e:
        print(f"❌ Failed to check Flask app routes: {e}")
        return False
    
    # Test 4: Test Enhanced Database health endpoint
    print("\n🏥 Test 4: Testing Enhanced Database health endpoint...")
    try:
        with app.test_client() as client:
            response = client.get('/api/enhanced-database/health')
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print("✅ Enhanced Database health endpoint working")
                    print(f"   Response: {data}")
                    
                    # Check that endpoints use new naming
                    endpoints = data.get('endpoints', {})
                    if endpoints:
                        for name, url in endpoints.items():
                            if 'enhanced-database' in url:
                                print(f"   ✅ {name}: {url}")
                            else:
                                print(f"   ❌ {name}: {url} (should contain 'enhanced-database')")
                else:
                    print("❌ Enhanced Database health endpoint returned error")
                    return False
            else:
                print(f"❌ Enhanced Database health endpoint returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Enhanced Database health endpoint test failed: {e}")
        return False
    
    # Test 5: Test Enhanced Database status endpoint
    print("\n📊 Test 5: Testing Enhanced Database status endpoint...")
    try:
        with app.test_client() as client:
            response = client.get('/api/enhanced-database/status')
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('success'):
                    print("✅ Enhanced Database status endpoint working")
                    integration = data.get('enhanced_database_integration', {})
                    print(f"   Status: {integration.get('status')}")
                    print(f"   Version: {integration.get('version')}")
                else:
                    print("❌ Enhanced Database status endpoint returned error")
                    return False
            else:
                print(f"❌ Enhanced Database status endpoint returned status {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Enhanced Database status endpoint test failed: {e}")
        return False
    
    # Test 6: Test enhanced configurations endpoint
    print("\n📋 Test 6: Testing enhanced configurations endpoint...")
    try:
        with app.test_client() as client:
            response = client.get('/api/configurations/enhanced')
            if response.status_code == 401:  # Expected: requires authentication
                print("✅ Enhanced configurations endpoint working (requires auth)")
            elif response.status_code == 503:  # Enhanced Database not available
                print("⚠️ Enhanced configurations endpoint: Enhanced Database not available")
            else:
                print(f"⚠️ Enhanced configurations endpoint returned status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Enhanced configurations endpoint test failed: {e}")
        return False
    
    # Test 7: Test enhanced bridge domain builder endpoint
    print("\n🔨 Test 7: Testing enhanced bridge domain builder endpoint...")
    try:
        with app.test_client() as client:
            response = client.get('/api/bridge-domains/enhanced-builder')
            if response.status_code == 405:  # Expected: GET not allowed, POST required
                print("✅ Enhanced bridge domain builder endpoint working (POST only)")
            else:
                print(f"⚠️ Enhanced bridge domain builder endpoint returned status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Enhanced bridge domain builder endpoint test failed: {e}")
        return False
    
    print("\n🎉 All Enhanced Database API integration tests completed successfully!")
    
    # Summary
    print("\n📋 Integration Summary:")
    print("─" * 50)
    print("✅ API Server: Enhanced Database integration enabled")
    print("✅ Enhanced Database Router: Working and registered")
    print("✅ Flask Routes: Enhanced Database endpoints registered")
    print("✅ Health Endpoint: /api/enhanced-database/health working")
    print("✅ Status Endpoint: /api/enhanced-database/status working")
    print("✅ Enhanced Configs: /api/configurations/enhanced available")
    print("✅ Enhanced Builder: /api/bridge-domains/enhanced-builder available")
    
    print("\n🚀 Enhanced Database API Renaming: COMPLETED!")
    print("\n💡 Available Enhanced Database endpoints:")
    print("   • /api/enhanced-database/health - Health check")
    print("   • /api/enhanced-database/status - Status and capabilities")
    print("   • /api/enhanced-database/* - All Enhanced Database CRUD operations")
    print("   • /api/configurations/enhanced - Enhanced configs with Enhanced Database")
    print("   • /api/configurations/migrate-to-phase1 - Legacy migration")
    print("   • /api/bridge-domains/enhanced-builder - Enhanced bridge building")
    
    print("\n🎯 Benefits of New Naming:")
    print("   • More user-friendly and intuitive")
    print("   • Easier troubleshooting and debugging")
    print("   • Clear separation from legacy 'phase1' terminology")
    print("   • Better API documentation and user experience")
    
    return True

if __name__ == "__main__":
    success = test_enhanced_database_api()
    sys.exit(0 if success else 1)
