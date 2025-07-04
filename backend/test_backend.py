#!/usr/bin/env python3
"""
Test script to verify backend functionality
"""
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{API_URL}/health")
        print("=== Health Check Test ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_config():
    """Test the configuration endpoint"""
    try:
        response = requests.get(f"{API_URL}/config")
        print("=== Configuration Test ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"Config test failed: {e}")
        return False

def test_list_images():
    """Test the list images endpoint"""
    try:
        response = requests.get(f"{API_URL}/images")
        print("=== List Images Test ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"List images test failed: {e}")
        return False

def test_upload_dummy():
    """Test upload with a dummy request (should fail without file)"""
    try:
        response = requests.post(f"{API_URL}/upload")
        print("=== Upload Test (No File) ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        return response.status_code == 400  # Should fail with 400
    except Exception as e:
        print(f"Upload test failed: {e}")
        return False

def main():
    print("Testing Purrfect Spots Backend API")
    print("=" * 40)
    
    # Check environment variables
    print("=== Environment Check ===")
    aws_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket = os.getenv('S3_BUCKET_NAME')
    region = os.getenv('AWS_REGION')
    
    print(f"AWS_ACCESS_KEY_ID: {'✓' if aws_key else '✗'}")
    print(f"AWS_SECRET_ACCESS_KEY: {'✓' if aws_secret else '✗'}")
    print(f"S3_BUCKET_NAME: {bucket if bucket else '✗'}")
    print(f"AWS_REGION: {region if region else '✗'}")
    print()
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Configuration", test_config),
        ("List Images", test_list_images),
        ("Upload (No File)", test_upload_dummy)
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("=== Test Results ===")
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
    else:
        print("❌ Some tests failed. Please check the backend configuration.")

if __name__ == "__main__":
    main()
