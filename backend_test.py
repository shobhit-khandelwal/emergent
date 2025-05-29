
import requests
import sys
import os
import json
import uuid
from datetime import datetime

class StorageAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_customer_id = None
        self.created_location_id = None

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
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
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
        
    # Integration-related tests
    
    def test_get_integration_status(self):
        """Test getting integration status"""
        return self.run_test(
            "Get Integration Status",
            "GET",
            "integration-status",
            200
        )
    
    def test_get_api_keys(self):
        """Test getting API keys"""
        return self.run_test(
            "Get API Keys",
            "GET",
            "api-keys",
            200
        )
    
    def test_create_api_key(self):
        """Test creating an API key"""
        data = {
            "service": "stripe",
            "key_name": "secret_key",
            "key_value": "sk_test_example123456789",
            "is_active": True,
            "environment": "test"
        }
        success, response = self.run_test(
            "Create API Key",
            "POST",
            "api-keys",
            200,
            data=data
        )
        if success:
            print(f"Created API key with ID: {response.get('id')}")
            return success, response
        return success, {}
    
    def test_create_twilio_api_keys(self):
        """Test creating Twilio API keys"""
        # Create Account SID
        data1 = {
            "service": "twilio",
            "key_name": "account_sid",
            "key_value": "AC123456789example",
            "is_active": True,
            "environment": "test"
        }
        success1, _ = self.run_test(
            "Create Twilio Account SID",
            "POST",
            "api-keys",
            200,
            data=data1
        )
        
        # Create Auth Token
        data2 = {
            "service": "twilio",
            "key_name": "auth_token",
            "key_value": "auth_token_example123456789",
            "is_active": True,
            "environment": "test"
        }
        success2, _ = self.run_test(
            "Create Twilio Auth Token",
            "POST",
            "api-keys",
            200,
            data=data2
        )
        
        # Create From Number
        data3 = {
            "service": "twilio",
            "key_name": "from_number",
            "key_value": "+15551234567",
            "is_active": True,
            "environment": "test"
        }
        success3, _ = self.run_test(
            "Create Twilio From Number",
            "POST",
            "api-keys",
            200,
            data=data3
        )
        
        return success1 and success2 and success3, {}
    
    def test_create_sendgrid_api_keys(self):
        """Test creating SendGrid API keys"""
        # Create API Key
        data1 = {
            "service": "sendgrid",
            "key_name": "api_key",
            "key_value": "SG.example123456789",
            "is_active": True,
            "environment": "test"
        }
        success1, _ = self.run_test(
            "Create SendGrid API Key",
            "POST",
            "api-keys",
            200,
            data=data1
        )
        
        # Create From Email
        data2 = {
            "service": "sendgrid",
            "key_name": "from_email",
            "key_value": "test@example.com",
            "is_active": True,
            "environment": "test"
        }
        success2, _ = self.run_test(
            "Create SendGrid From Email",
            "POST",
            "api-keys",
            200,
            data=data2
        )
        
        return success1 and success2, {}
    
    def test_create_checkout_session(self):
        """Test creating a checkout session"""
        data = {
            "booking_id": "test_booking_123",
            "amount": 199.99,
            "origin_url": "https://example.com"
        }
        return self.run_test(
            "Create Checkout Session",
            "POST",
            "payments/create-checkout",
            200,
            data=data
        )
    
    def test_send_booking_confirmation(self):
        """Test sending booking confirmation"""
        data = {
            "booking_id": "test_booking_123"
        }
        return self.run_test(
            "Send Booking Confirmation",
            "POST",
            "notifications/send-booking-confirmation",
            200,
            data=data
        )
    
    def test_send_payment_confirmation(self):
        """Test sending payment confirmation"""
        data = {
            "transaction_id": "test_transaction_123"
        }
        return self.run_test(
            "Send Payment Confirmation",
            "POST",
            "notifications/send-payment-confirmation",
            200,
            data=data
        )
    
    def test_delete_api_key(self, key_id):
        """Test deleting an API key"""
        return self.run_test(
            f"Delete API Key {key_id}",
            "DELETE",
            f"api-keys/{key_id}",
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
