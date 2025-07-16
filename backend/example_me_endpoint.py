"""
Example usage of the /me endpoint
"""
import requests
import json

# Example of how to test the /me endpoint
def test_me_endpoint():
    """
    Test the /me endpoint with authentication
    """
    base_url = "http://localhost:8000"
    
    print("Testing /auth/me endpoint...")
    
    # First, you need to login to get a token
    print("\n1. Login to get access token:")
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    # Note: This is just an example - you'll need a real user to test
    print(f"   POST {base_url}/auth/login")
    print(f"   Data: {json.dumps(login_data, indent=2)}")
    
    # After login, you get a response like:
    example_response = {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user": {
            "id": "user_id_here",
            "email": "test@example.com",
            "name": "Test User"
        }
    }
    
    print(f"   Response: {json.dumps(example_response, indent=2)}")
    
    # Then use the token to call /me endpoint
    print("\n2. Call /me endpoint with token:")
    print(f"   GET {base_url}/auth/me")
    print("   Headers: {")
    print("     'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'")
    print("   }")
    
    # Expected response from /me endpoint:
    me_response = {
        "id": "user_id_here",
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "hashed_password_here",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }
    
    print(f"   Response: {json.dumps(me_response, indent=2)}")
    
    print("\n✅ /me endpoint is ready to use!")
    print("\nNote: Make sure to:")
    print("- Have a user registered in the database")
    print("- Use a valid JWT token in the Authorization header")
    print("- Backend server is running on http://localhost:8000")

if __name__ == "__main__":
    test_me_endpoint()
