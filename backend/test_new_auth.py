"""
Test script for the new authentication endpoints
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

# Create test client
client = TestClient(app)

def test_signup_endpoint():
    """Test the signup endpoint"""
    signup_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    response = client.post("/auth/signup", json=signup_data)
    print(f"Signup response status: {response.status_code}")
    print(f"Signup response: {response.json()}")
    
    return response.json() if response.status_code == 200 else None

def test_login_endpoint():
    """Test the login endpoint"""
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/auth/login", json=login_data)
    print(f"Login response status: {response.status_code}")
    print(f"Login response: {response.json()}")
    
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":
    print("Testing new authentication endpoints...")
    
    # Test signup
    print("\n1. Testing signup endpoint:")
    signup_result = test_signup_endpoint()
    
    # Test login
    print("\n2. Testing login endpoint:")
    login_result = test_login_endpoint()
    
    if signup_result and login_result:
        print("\n✅ All authentication endpoints working correctly!")
    else:
        print("\n❌ Some endpoints failed. Check the responses above.")
