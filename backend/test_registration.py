"""
Test script for user registration
Run this to test if the registration endpoint works correctly
"""
import requests
import json
import random

# Configuration
API_BASE_URL = "http://localhost:8000"

def generate_test_user():
    """Generate a unique test user"""
    random_id = random.randint(1000, 9999)
    return {
        "email": f"test{random_id}@example.com",
        "password": "testpassword123",
        "name": f"Test User {random_id}"
    }

def test_registration():
    """Test user registration endpoint"""
    test_user = generate_test_user()
    url = f"{API_BASE_URL}/auth/register"
    
    print("🧪 Testing user registration...")
    print(f"📡 URL: {url}")
    print(f"📋 Data: {test_user}")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=test_user,
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"📄 Response Data: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"📄 Raw Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Registration successful!")
            print(f"🎫 Access Token: {data.get('access_token', 'Not found')[:50]}...")
            print(f"👤 User ID: {data.get('user', {}).get('id', 'Not found')}")
            print(f"📧 User Email: {data.get('user', {}).get('email', 'Not found')}")
            print(f"👤 User Name: {data.get('user', {}).get('name', 'Not found')}")
            
            # Test login with the same credentials
            print("\n🔐 Testing login with same credentials...")
            test_login(test_user['email'], test_user['password'])
            
        else:
            print("❌ Registration failed!")
            try:
                error_data = response.json()
                print(f"💥 Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"💥 Raw error: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the backend is running on port 8000")
        print("💡 Try running: cd backend && python app.py")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_login(email: str, password: str):
    """Test login endpoint"""
    url = f"{API_BASE_URL}/auth/login"
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=10
        )
        
        print(f"📊 Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
        else:
            print("❌ Login failed!")
            try:
                error_data = response.json()
                print(f"💥 Login Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"💥 Raw login error: {response.text}")
                
    except Exception as e:
        print(f"❌ Login test error: {e}")

if __name__ == "__main__":
    print("🚀 Starting registration test...")
    test_registration()
