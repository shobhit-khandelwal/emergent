
import requests
import sys
import json
from datetime import datetime

class StorageAPITester:
    def __init__(self, base_url="https://0a1f512a-b503-4e07-b1bf-b8806b67f6b0.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

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

    def test_get_filter_options(self):
        """Test getting filter options"""
        return self.run_test(
            "Get Filter Options",
            "GET",
            "filter-options",
            200
        )

    def test_get_virtual_units(self, params=None):
        """Test getting virtual units with optional filters"""
        return self.run_test(
            "Get Virtual Units",
            "GET",
            "virtual-units",
            200,
            params=params
        )

    def test_get_virtual_units_with_filters(self):
        """Test getting virtual units with various filters"""
        # Test unit type filter
        print("\n--- Testing unit type filter ---")
        success, data = self.run_test(
            "Get Virtual Units - Filter by Unit Type",
            "GET",
            "virtual-units",
            200,
            params={"unit_type": "enclosed_parking"}
        )
        if success:
            print(f"Found {len(data)} enclosed parking units")
            for unit in data:
                if unit["unit_type"] != "enclosed_parking":
                    print(f"❌ Unit has incorrect type: {unit['unit_type']}")
                    success = False
        
        # Test price range filter
        print("\n--- Testing price range filter ---")
        success2, data2 = self.run_test(
            "Get Virtual Units - Filter by Price Range",
            "GET",
            "virtual-units",
            200,
            params={"min_price": 200, "max_price": 300, "pricing_period": "monthly"}
        )
        if success2:
            print(f"Found {len(data2)} units in price range $200-$300/month")
            for unit in data2:
                if unit["monthly_price"] < 200 or unit["monthly_price"] > 300:
                    print(f"❌ Unit has price outside range: ${unit['monthly_price']}")
                    success2 = False
        
        # Test amenities filter
        print("\n--- Testing amenities filter ---")
        success3, data3 = self.run_test(
            "Get Virtual Units - Filter by Amenities",
            "GET",
            "virtual-units",
            200,
            params={"amenities": "electric"}
        )
        if success3:
            print(f"Found {len(data3)} units with electric amenity")
            for unit in data3:
                if "electric" not in unit["amenities"]:
                    print(f"❌ Unit missing electric amenity: {unit['amenities']}")
                    success3 = False
        
        return success and success2 and success3

    def test_create_booking(self, virtual_unit_id):
        """Test creating a booking"""
        booking_data = {
            "virtual_unit_id": virtual_unit_id,
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "555-123-4567",
            "payment_option": "pay_now_move_now",
            "pricing_period": "monthly",
            "start_date": datetime.now().isoformat(),
            "move_in_date": datetime.now().isoformat()
        }
        
        return self.run_test(
            "Create Booking",
            "POST",
            "bookings",
            200,
            data=booking_data
        )

    def test_unit_availability_after_booking(self, booked_physical_unit_id):
        """Test that all virtual units with the same physical unit are unavailable after booking"""
        success, all_units = self.run_test(
            "Get All Virtual Units (Including Unavailable)",
            "GET",
            "virtual-units",
            200,
            params={"available_only": False}
        )
        
        if not success:
            return False
        
        # Get all virtual units with the same physical unit ID
        related_units = [unit for unit in all_units if unit["physical_unit_id"] == booked_physical_unit_id]
        
        print(f"\nFound {len(related_units)} virtual units with the same physical unit ID")
        
        # Now check if these units are available
        success, available_units = self.run_test(
            "Get Available Virtual Units",
            "GET",
            "virtual-units",
            200,
            params={"available_only": True}
        )
        
        if not success:
            return False
        
        # Check if any of the related units are still available
        available_unit_ids = [unit["id"] for unit in available_units]
        for unit in related_units:
            if unit["id"] in available_unit_ids:
                print(f"❌ Unit {unit['id']} should be unavailable but is still available")
                return False
        
        print("✅ All virtual units with the same physical unit are correctly marked as unavailable")
        return True

def main():
    # Setup
    tester = StorageAPITester()
    
    # Run tests
    print("\n=== Testing RV & Boat Storage Management API ===\n")
    
    # Test basic endpoints
    tester.test_root_endpoint()
    success, filter_options = tester.test_get_filter_options()
    
    if success:
        print("\nAvailable filter options:")
        print(f"Unit Types: {filter_options.get('unit_types', [])}")
        print(f"Amenities: {filter_options.get('amenities', [])}")
        print(f"Size Categories: {filter_options.get('size_categories', [])}")
        print(f"Price Range: {filter_options.get('price_range', {})}")
    
    # Test getting virtual units
    success, units = tester.test_get_virtual_units()
    
    if success:
        print(f"\nFound {len(units)} virtual units")
        if len(units) > 0:
            print("\nSample unit details:")
            sample_unit = units[0]
            print(f"ID: {sample_unit['id']}")
            print(f"Name: {sample_unit['display_name']}")
            print(f"Type: {sample_unit['unit_type']}")
            print(f"Size: {sample_unit['display_size']}")
            print(f"Prices: ${sample_unit['daily_price']}/day, ${sample_unit['weekly_price']}/week, ${sample_unit['monthly_price']}/month")
            print(f"Amenities: {', '.join(sample_unit['amenities'])}")
            print(f"Physical Unit ID: {sample_unit['physical_unit_id']}")
    
    # Test filtering
    tester.test_get_virtual_units_with_filters()
    
    # Test booking flow
    if success and len(units) > 0:
        print("\n=== Testing Booking Flow ===")
        
        # Select a unit to book
        unit_to_book = units[0]
        print(f"\nBooking unit: {unit_to_book['display_name']} (ID: {unit_to_book['id']})")
        
        # Create a booking
        booking_success, booking = tester.test_create_booking(unit_to_book['id'])
        
        if booking_success:
            print("\nBooking created successfully:")
            print(f"Booking ID: {booking['id']}")
            print(f"Customer: {booking['customer_name']}")
            print(f"Unit: {booking['virtual_unit_id']}")
            print(f"Physical Unit: {booking['physical_unit_id']}")
            print(f"Status: {booking['status']}")
            
            # Test that all virtual units with the same physical unit are unavailable
            tester.test_unit_availability_after_booking(booking['physical_unit_id'])
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
