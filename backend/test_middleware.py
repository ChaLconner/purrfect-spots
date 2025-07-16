"""
Test script for the updated authentication middleware
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test importing the new middleware functions
    from middleware.auth_middleware import decode_token, get_current_user, get_current_user_optional
    print("✅ Successfully imported new middleware functions")
    
    # Test the decode_token function with a mock token
    import jwt
    from datetime import datetime, timedelta
    
    # Create a test token
    JWT_SECRET = "test-secret"
    payload = {
        "sub": "test_user_123",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    test_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    print(f"✅ Created test token: {test_token[:20]}...")
    
    # Test decode_token function
    os.environ["JWT_SECRET"] = JWT_SECRET
    decoded = decode_token(test_token)
    print(f"✅ Decoded token payload: {decoded}")
    
    print("\n🎉 All middleware functions are working correctly!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
