"""
Test script for the new separated authentication routes
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test importing the new route modules
    from routes import auth_manual, auth_google
    print("✅ Successfully imported auth_manual and auth_google modules")
    
    # Test that both routers are available
    print(f"✅ auth_manual router: {auth_manual.router}")
    print(f"✅ auth_google router: {auth_google.router}")
    
    # Test the main app imports
    from main import app, get_supabase_client
    print("✅ Successfully imported main app and get_supabase_client")
    
    # Check that routes are properly included
    routes = [route.path for route in app.routes]
    auth_routes = [route for route in routes if route.startswith('/auth')]
    print(f"✅ Available auth routes: {auth_routes}")
    
    print("\n🎉 All imports and route integrations working correctly!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
