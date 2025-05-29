
import requests
import sys
import json
import time
import uuid
from datetime import datetime

class ImageManagementTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_image_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
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
                if response.text:
                    try:
                        return success, response.json()
                    except json.JSONDecodeError:
                        return success, response.text
                return success, None
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_get_all_images(self):
        """Test getting all images"""
        success, response = self.run_test(
            "Get All Images",
            "GET",
            "api/images",
            200
        )
        if success:
            print(f"Found {len(response)} images")
        return success, response

    def test_get_images_by_category(self, category):
        """Test getting images filtered by category"""
        success, response = self.run_test(
            f"Get Images by Category: {category}",
            "GET",
            "api/images",
            200,
            params={"category": category}
        )
        if success:
            print(f"Found {len(response)} images in category '{category}'")
            # Verify all returned images have the correct category
            all_correct = all(img["category"] == category for img in response)
            if not all_correct:
                print("❌ Some images have incorrect category")
                return False, response
        return success, response

    def test_create_image(self, image_data):
        """Test creating a new image"""
        success, response = self.run_test(
            "Create Image",
            "POST",
            "api/images",
            200,
            data=image_data
        )
        if success and response and "id" in response:
            self.created_image_ids.append(response["id"])
            print(f"Created image with ID: {response['id']}")
        return success, response

    def test_update_image(self, image_id, updated_data):
        """Test updating an image"""
        success, response = self.run_test(
            f"Update Image {image_id}",
            "PUT",
            f"api/images/{image_id}",
            200,
            data=updated_data
        )
        return success, response

    def test_delete_image(self, image_id):
        """Test deleting an image"""
        success, response = self.run_test(
            f"Delete Image {image_id}",
            "DELETE",
            f"api/images/{image_id}",
            200
        )
        if success:
            if image_id in self.created_image_ids:
                self.created_image_ids.remove(image_id)
        return success, response

    def test_update_unit_image(self, unit_id, image_url):
        """Test updating a unit's image"""
        success, response = self.run_test(
            f"Update Unit Image for {unit_id}",
            "PUT",
            f"api/virtual-units/{unit_id}/image",
            200,
            params={"image_url": image_url}
        )
        return success, response

    def test_get_virtual_units(self):
        """Get all virtual units to use for testing"""
        success, response = self.run_test(
            "Get Virtual Units",
            "GET",
            "api/virtual-units",
            200
        )
        return success, response

    def cleanup(self):
        """Clean up any created test images"""
        print("\n🧹 Cleaning up test data...")
        for image_id in self.created_image_ids:
            self.test_delete_image(image_id)

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://0a1f512a-b503-4e07-b1bf-b8806b67f6b0.preview.emergentagent.com"
    
    # Setup tester
    tester = ImageManagementTester(backend_url)
    
    # Initialize test data
    test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    test_image_data = {
        "name": f"Test Image {test_timestamp}",
        "url": "https://images.unsplash.com/photo-1711130361680-a3beb1369ef5",
        "category": "unit",
        "tags": ["test", "automated", "rv"],
        "description": "This is a test image created by automated testing"
    }
    
    # Run tests
    print("\n🚀 Starting Image Management API Tests")
    print(f"Using backend URL: {backend_url}")
    
    # Test 1: Get all images
    get_all_success, all_images = tester.test_get_all_images()
    if not get_all_success:
        print("❌ Failed to get images, stopping tests")
        return 1
    
    # Test 2: Get images by category
    categories = ["hero", "unit", "feature", "gallery"]
    for category in categories:
        tester.test_get_images_by_category(category)
    
    # Test 3: Create a new image
    create_success, created_image = tester.test_create_image(test_image_data)
    if not create_success or not created_image:
        print("❌ Failed to create image, stopping tests")
        return 1
    
    # Test 4: Update the created image
    image_id = created_image["id"]
    updated_data = {**created_image, "description": "Updated description from automated test"}
    tester.test_update_image(image_id, updated_data)
    
    # Test 5: Get virtual units to use for image assignment
    units_success, units = tester.test_get_virtual_units()
    if units_success and units and len(units) > 0:
        # Test 6: Update a unit's image
        unit_id = units[0]["id"]
        tester.test_update_unit_image(unit_id, created_image["url"])
    
    # Test 7: Delete the created image
    tester.test_delete_image(image_id)
    
    # Clean up any remaining test data
    tester.cleanup()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("✅ Image Management API Testing Complete")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
