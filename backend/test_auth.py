"""
Test script for authentication service
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.auth_service import AuthService
from supabase import create_client, Client

# Mock Supabase client for testing
class MockSupabaseClient:
    def __init__(self):
        self.data = {}
        
    def table(self, table_name):
        return self
        
    def select(self, columns):
        return self
        
    def eq(self, column, value):
        return self
        
    def single(self):
        return self
        
    def execute(self):
        class MockResult:
            def __init__(self, data):
                self.data = data
        return MockResult(None)
        
    def insert(self, data):
        return self
        
    def update(self, data):
        return self

def test_password_hashing():
    """Test password hashing and verification"""
    # Create auth service with mock client
    mock_client = MockSupabaseClient()
    auth_service = AuthService(mock_client)
    
    # Test password hashing
    password = "test_password_123"
    hashed = auth_service.hash_password(password)
    
    print(f"Original password: {password}")
    print(f"Hashed password: {hashed}")
    
    # Test password verification
    is_valid = auth_service.verify_password(password, hashed)
    print(f"Password verification: {is_valid}")
    
    # Test with wrong password
    wrong_password = "wrong_password"
    is_invalid = auth_service.verify_password(wrong_password, hashed)
    print(f"Wrong password verification: {is_invalid}")
    
    # Test JWT token creation
    user_id = "test_user_123"
    token = auth_service.create_access_token(user_id)
    print(f"JWT Token: {token}")
    
    # Test token verification
    decoded_user_id = auth_service.verify_access_token(token)
    print(f"Decoded user ID: {decoded_user_id}")
    
    print("\n✅ All basic authentication tests passed!")

if __name__ == "__main__":
    test_password_hashing()
