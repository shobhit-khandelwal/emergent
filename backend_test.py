
import requests
import sys
import os
from datetime import datetime

class StorageAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return success, response.json() if response.content else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_get_content(self):
        """Test getting content blocks"""
        return self.run_test(
            "Get Content Blocks",
            "GET",
            "content",
            200
        )

    def test_get_banners(self):
        """Test getting promotional banners"""
        return self.run_test(
            "Get Promotional Banners",
            "GET",
            "banners",
            200
        )

    def test_get_images(self):
        """Test getting image assets"""
        return self.run_test(
            "Get Image Assets",
            "GET",
            "images",
            200
        )

    def test_get_virtual_units(self):
        """Test getting virtual units"""
        return self.run_test(
            "Get Virtual Units",
            "GET",
            "virtual-units",
            200
        )

    def test_get_filter_options(self):
        """Test getting filter options"""
        return self.run_test(
            "Get Filter Options",
            "GET",
            "filter-options",
            200
        )

    def test_get_admin_analytics(self):
        """Test getting admin analytics"""
        return self.run_test(
            "Get Admin Analytics",
            "GET",
            "admin/analytics",
            200
        )

def main():
    # Get backend URL from environment or use default
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=')[1]
                break
    
    # Ensure the URL has the /api prefix
    if not backend_url.endswith('/api'):
        backend_url = f"{backend_url}/api"
    
    print(f"Testing backend API at: {backend_url}")
    
    # Setup tester
    tester = StorageAPITester(backend_url)
    
    # Run tests
    tester.test_root_endpoint()
    tester.test_get_content()
    tester.test_get_banners()
    tester.test_get_images()
    tester.test_get_virtual_units()
    tester.test_get_filter_options()
    tester.test_get_admin_analytics()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
