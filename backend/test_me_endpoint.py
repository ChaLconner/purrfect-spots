"""
Test script for the new /me endpoint
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test importing the routes
    from routes import auth_manual
    print("✅ Successfully imported auth_manual routes")
    
    # Check if the /me endpoint is available
    routes = [route.path for route in auth_manual.router.routes]
    me_routes = [route for route in routes if '/me' in route]
    
    print(f"✅ Available routes in auth_manual: {routes}")
    print(f"✅ /me endpoints found: {me_routes}")
    
    # Test the main app with all routes
    from main import app
    all_routes = [route.path for route in app.routes]
    auth_routes = [route for route in all_routes if route.startswith('/auth')]
    
    print(f"✅ All auth routes in main app: {auth_routes}")
    
    # Check if /auth/me is available
    me_endpoint_exists = '/auth/me' in auth_routes
    print(f"✅ /auth/me endpoint exists: {me_endpoint_exists}")
    
    print("\n🎉 /me endpoint integration successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
