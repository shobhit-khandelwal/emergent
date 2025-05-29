
import requests
import sys
import json
import time
import uuid
from datetime import datetime

class RVStorageAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_ids = {
            "banners": [],
            "images": [],
            "content": []
        }
        self.session_id = f"test_session_{uuid.uuid4()}"

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

    # Content Management Tests
    def test_get_all_content(self):
        """Test getting all content blocks"""
        success, response = self.run_test(
            "Get All Content Blocks",
            "GET",
            "api/content",
            200
        )
        if success:
            print(f"Found {len(response)} content blocks")
        return success, response

    def test_get_content_by_section(self, section):
        """Test getting content filtered by section"""
        success, response = self.run_test(
            f"Get Content by Section: {section}",
            "GET",
            "api/content",
            200,
            params={"section": section}
        )
        if success:
            print(f"Found {len(response)} content blocks in section '{section}'")
        return success, response

    def test_get_content_by_key(self, key):
        """Test getting content by key"""
        success, response = self.run_test(
            f"Get Content by Key: {key}",
            "GET",
            f"api/content/{key}",
            200
        )
        if success:
            print(f"Successfully retrieved content for key '{key}'")
        return success, response

    def test_update_content_by_key(self, key, new_content):
        """Test updating content by key"""
        success, response = self.run_test(
            f"Update Content by Key: {key}",
            "PUT",
            f"api/content/key/{key}",
            200,
            data={"content": new_content}
        )
        if success:
            print(f"Successfully updated content for key '{key}'")
        return success, response

    def test_create_content(self, content_data):
        """Test creating a new content block"""
        success, response = self.run_test(
            "Create Content Block",
            "POST",
            "api/content",
            200,
            data=content_data
        )
        if success and response and "id" in response:
            self.created_ids["content"].append(response["id"])
            print(f"Created content block with ID: {response['id']}")
        return success, response

    # Banner Management Tests
    def test_get_all_banners(self):
        """Test getting all banners"""
        success, response = self.run_test(
            "Get All Banners",
            "GET",
            "api/banners",
            200
        )
        if success:
            print(f"Found {len(response)} banners")
        return success, response

    def test_get_active_banners(self, funnel_stage=None):
        """Test getting active banners, optionally filtered by funnel stage"""
        params = {"active_only": True}
        if funnel_stage:
            params["funnel_stage"] = funnel_stage
        
        test_name = "Get Active Banners"
        if funnel_stage:
            test_name += f" for stage '{funnel_stage}'"
            
        success, response = self.run_test(
            test_name,
            "GET",
            "api/banners",
            200,
            params=params
        )
        if success:
            print(f"Found {len(response)} active banners")
            if funnel_stage:
                valid_banners = [b for b in response if funnel_stage in b.get("funnel_stages", [])]
                print(f"Of which {len(valid_banners)} are targeted for stage '{funnel_stage}'")
        return success, response

    def test_create_banner(self, banner_data):
        """Test creating a new banner"""
        success, response = self.run_test(
            "Create Banner",
            "POST",
            "api/banners",
            200,
            data=banner_data
        )
        if success and response and "id" in response:
            self.created_ids["banners"].append(response["id"])
            print(f"Created banner with ID: {response['id']}")
        return success, response

    def test_update_banner(self, banner_id, updated_data):
        """Test updating a banner"""
        success, response = self.run_test(
            f"Update Banner {banner_id}",
            "PUT",
            f"api/banners/{banner_id}",
            200,
            data=updated_data
        )
        return success, response

    def test_delete_banner(self, banner_id):
        """Test deleting a banner"""
        success, response = self.run_test(
            f"Delete Banner {banner_id}",
            "DELETE",
            f"api/banners/{banner_id}",
            200
        )
        if success:
            if banner_id in self.created_ids["banners"]:
                self.created_ids["banners"].remove(banner_id)
        return success, response

    # Funnel Tracking Tests
    def test_track_funnel_event(self, event_type, metadata=None):
        """Test tracking a funnel event"""
        data = {
            "session_id": self.session_id,
            "event_type": event_type,
            "metadata": metadata or {}
        }
        success, response = self.run_test(
            f"Track Funnel Event: {event_type}",
            "POST",
            "api/funnel/track",
            200,
            data=data
        )
        return success, response

    def test_get_user_funnel_stage(self):
        """Test getting a user's funnel stage"""
        success, response = self.run_test(
            "Get User Funnel Stage",
            "GET",
            f"api/funnel/user/{self.session_id}",
            200
        )
        if success:
            print(f"User funnel stage: {response.get('funnel_stage')}")
        return success, response

    def test_get_admin_analytics(self):
        """Test getting admin analytics data"""
        success, response = self.run_test(
            "Get Admin Analytics",
            "GET",
            "api/admin/analytics",
            200
        )
        if success:
            print("Successfully retrieved admin analytics")
            print(f"Total units: {response.get('total_units')}")
            print(f"Total bookings: {response.get('total_bookings')}")
            print(f"Unique visitors (7d): {response.get('last_7_days', {}).get('unique_visitors')}")
        return success, response

    # Image Management Tests
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
            self.created_ids["images"].append(response["id"])
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
            if image_id in self.created_ids["images"]:
                self.created_ids["images"].remove(image_id)
        return success, response

    def test_update_unit_image(self, unit_id, image_url):
        """Test updating a unit's image"""
        # The API expects image_url in the query string, not as a JSON body
        url = f"{self.base_url}/api/virtual-units/{unit_id}/image?image_url={image_url}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing Update Unit Image for {unit_id}...")
        
        try:
            response = requests.put(url)
            success = response.status_code == 200
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
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, None
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    # Virtual Units Tests
    def test_get_virtual_units(self, filters=None):
        """Test getting virtual units with optional filters"""
        success, response = self.run_test(
            "Get Virtual Units",
            "GET",
            "api/virtual-units",
            200,
            params=filters
        )
        if success:
            print(f"Found {len(response)} virtual units")
        return success, response

    def cleanup(self):
        """Clean up any created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created banners
        for banner_id in self.created_ids["banners"]:
            self.test_delete_banner(banner_id)
            
        # Delete created images
        for image_id in self.created_ids["images"]:
            self.test_delete_image(image_id)
            
        # We don't delete content blocks as they're essential for the site

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://0a1f512a-b503-4e07-b1bf-b8806b67f6b0.preview.emergentagent.com"
    
    # Setup tester
    tester = RVStorageAPITester(backend_url)
    
    # Initialize test data
    test_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Run tests
    print("\n🚀 Starting RV & Boat Storage API Tests")
    print(f"Using backend URL: {backend_url}")
    
    # Initialize sample data if needed
    print("\n📦 Initializing sample data...")
    tester.run_test(
        "Initialize Sample Data",
        "POST",
        "api/initialize-sample-data",
        200
    )
    
    # Test Content Management APIs
    print("\n📝 Testing Content Management APIs...")
    
    # Test 1: Get all content blocks
    content_success, content_blocks = tester.test_get_all_content()
    if not content_success:
        print("❌ Failed to get content blocks, stopping tests")
        return 1
    
    # Verify we have at least 9 content blocks as specified
    if len(content_blocks) < 9:
        print(f"❌ Expected at least 9 content blocks, but found {len(content_blocks)}")
    else:
        print("✅ Found expected number of content blocks")
    
    # Test 2: Get content by section
    sections = ["hero", "features", "units"]
    for section in sections:
        tester.test_get_content_by_section(section)
    
    # Test 3: Get content by key
    if content_blocks:
        test_key = content_blocks[0]["key"]
        key_success, key_content = tester.test_get_content_by_key(test_key)
        
        # Test 4: Update content by key
        if key_success:
            original_content = key_content["content"]
            new_content = f"Updated content {test_timestamp}"
            update_success, _ = tester.test_update_content_by_key(test_key, new_content)
            
            # Verify the update worked
            if update_success:
                verify_success, updated_content = tester.test_get_content_by_key(test_key)
                if verify_success and updated_content["content"] == new_content:
                    print("✅ Content update verified")
                else:
                    print("❌ Content update verification failed")
                
                # Restore original content
                tester.test_update_content_by_key(test_key, original_content)
    
    # Test Banner Management APIs
    print("\n🎯 Testing Banner Management APIs...")
    
    # Test 1: Get all banners
    banners_success, banners = tester.test_get_all_banners()
    if not banners_success:
        print("❌ Failed to get banners, stopping tests")
        return 1
    
    # Verify we have at least 6 banners as specified
    if len(banners) < 6:
        print(f"❌ Expected at least 6 banners, but found {len(banners)}")
    else:
        print("✅ Found expected number of banners")
    
    # Test 2: Get active banners for different funnel stages
    funnel_stages = ["visitor", "viewing_units", "filtering", "booking_started", "booking_abandoned", "returning_visitor"]
    for stage in funnel_stages:
        tester.test_get_active_banners(stage)
    
    # Test 3: Create a new banner
    test_banner = {
        "title": f"Test Banner {test_timestamp}",
        "message": "This is a test banner created by automated testing",
        "cta_text": "Click Me",
        "cta_url": "#test",
        "banner_type": "info",
        "funnel_stages": ["visitor", "returning_visitor"],
        "background_color": "#e0f7fa",
        "text_color": "#006064"
    }
    create_success, created_banner = tester.test_create_banner(test_banner)
    
    # Test 4: Update the created banner
    if create_success and created_banner:
        banner_id = created_banner["id"]
        updated_banner = {**created_banner, "message": "Updated message from automated test"}
        tester.test_update_banner(banner_id, updated_banner)
        
        # Test 5: Delete the created banner
        tester.test_delete_banner(banner_id)
    
    # Test Funnel Tracking APIs
    print("\n📊 Testing Funnel Tracking APIs...")
    
    # Test 1: Track various funnel events
    events = [
        ("page_view", {"page": "home"}),
        ("unit_viewed", {"unit_id": "test_unit_1"}),
        ("filter_used", {"filter_key": "unit_type", "filter_value": "enclosed_parking"}),
        ("booking_started", {"unit_id": "test_unit_1"}),
        ("booking_abandoned", {"unit_id": "test_unit_1"})
    ]
    
    for event_type, metadata in events:
        tester.test_track_funnel_event(event_type, metadata)
        # Small delay to ensure events are processed in order
        time.sleep(0.5)
    
    # Test 2: Get user funnel stage
    tester.test_get_user_funnel_stage()
    
    # Test 3: Get admin analytics
    tester.test_get_admin_analytics()
    
    # Test Image Management APIs
    print("\n🖼️ Testing Image Management APIs...")
    
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
    test_image_data = {
        "name": f"Test Image {test_timestamp}",
        "url": "https://images.unsplash.com/photo-1711130361680-a3beb1369ef5",
        "category": "unit",
        "tags": ["test", "automated", "rv"],
        "description": "This is a test image created by automated testing"
    }
    create_success, created_image = tester.test_create_image(test_image_data)
    
    # Test 4: Update the created image
    if create_success and created_image:
        image_id = created_image["id"]
        updated_data = {**created_image, "description": "Updated description from automated test"}
        tester.test_update_image(image_id, updated_data)
        
        # Test 5: Get virtual units to use for image assignment
        units_success, units = tester.test_get_virtual_units()
        if units_success and units and len(units) > 0:
            # Test 6: Update a unit's image
            unit_id = units[0]["id"]
            tester.test_update_unit_image(unit_id, created_image["url"])
    
    # Clean up any remaining test data
    tester.cleanup()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print("✅ RV & Boat Storage API Testing Complete")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
