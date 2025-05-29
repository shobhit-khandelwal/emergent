from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="RV & Boat Storage Management System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

class UnitType(str, Enum):
    ENCLOSED_PARKING = "enclosed_parking"
    SELF_STORAGE = "self_storage"
    OUTDOOR_PARKING = "outdoor_parking"
    COVERED_PARKING = "covered_parking"

class BookingStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"
    WAITLIST = "waitlist"

class PaymentOption(str, Enum):
    PAY_NOW_MOVE_NOW = "pay_now_move_now"
    PAY_NOW_MOVE_LATER = "pay_now_move_later"
    PAY_LATER_MOVE_LATER = "pay_later_move_later"

class PricingPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

# Models
class ImageAsset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    category: str  # hero, unit, feature, gallery
    tags: List[str] = []  # rv, boat, storage, outdoor, enclosed, etc.
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PhysicalUnit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    unit_number: str
    actual_size: str  # e.g., "12x30"
    location: str
    amenities: List[str] = []  # e.g., ["security", "climate_control", "covered"]
    base_price: float
    status: BookingStatus = BookingStatus.AVAILABLE
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VirtualUnit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    physical_unit_id: str
    unit_type: UnitType
    display_size: str  # e.g., "12x25"
    display_name: str  # e.g., "Enclosed Parking 12x25"
    daily_price: float
    weekly_price: float
    monthly_price: float
    amenities: List[str] = []
    image_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    virtual_unit_id: str
    physical_unit_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    payment_option: PaymentOption
    pricing_period: PricingPeriod
    start_date: datetime
    end_date: Optional[datetime] = None
    total_price: float
    status: BookingStatus = BookingStatus.BOOKED
    move_in_date: Optional[datetime] = None
    special_requests: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FilterOptions(BaseModel):
    unit_type: Optional[UnitType] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    pricing_period: PricingPeriod = PricingPeriod.MONTHLY
    amenities: Optional[List[str]] = None
    size_category: Optional[str] = None  # small, medium, large
    availability_date: Optional[datetime] = None

class BookingRequest(BaseModel):
    virtual_unit_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    payment_option: PaymentOption
    pricing_period: PricingPeriod
    start_date: datetime
    end_date: Optional[datetime] = None
    move_in_date: Optional[datetime] = None
    special_requests: Optional[str] = None

# Helper functions
def get_size_category(size: str) -> str:
    """Categorize unit size as small, medium, or large"""
    try:
        dimensions = size.lower().replace('x', '').replace(' ', '')
        # Extract numbers from size string
        numbers = [int(s) for s in dimensions.split() if s.isdigit()]
        if len(numbers) >= 2:
            area = numbers[0] * numbers[1]
            if area <= 200:
                return "small"
            elif area <= 400:
                return "medium"
            else:
                return "large"
    except:
        pass
    return "medium"

def get_price_for_period(virtual_unit: VirtualUnit, period: PricingPeriod) -> float:
    """Get price for specified period"""
    if period == PricingPeriod.DAILY:
        return virtual_unit.daily_price
    elif period == PricingPeriod.WEEKLY:
        return virtual_unit.weekly_price
    else:
        return virtual_unit.monthly_price

# API Routes

@api_router.get("/")
async def root():
    return {"message": "RV & Boat Storage Management API"}

@api_router.post("/physical-units", response_model=PhysicalUnit)
async def create_physical_unit(unit: PhysicalUnit):
    """Create a new physical storage unit"""
    unit_dict = unit.dict()
    await db.physical_units.insert_one(unit_dict)
    return unit

@api_router.get("/physical-units", response_model=List[PhysicalUnit])
async def get_physical_units():
    """Get all physical units"""
    units = await db.physical_units.find().to_list(1000)
    return [PhysicalUnit(**unit) for unit in units]

@api_router.post("/virtual-units", response_model=VirtualUnit)
async def create_virtual_unit(unit: VirtualUnit):
    """Create a new virtual unit mapping"""
    # Verify physical unit exists
    physical_unit = await db.physical_units.find_one({"id": unit.physical_unit_id})
    if not physical_unit:
        raise HTTPException(status_code=404, detail="Physical unit not found")
    
    unit_dict = unit.dict()
    await db.virtual_units.insert_one(unit_dict)
    return unit

@api_router.get("/virtual-units", response_model=List[VirtualUnit])
async def get_virtual_units(
    unit_type: Optional[UnitType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    pricing_period: PricingPeriod = PricingPeriod.MONTHLY,
    amenities: Optional[str] = None,
    size_category: Optional[str] = None,
    available_only: bool = True
):
    """Get virtual units with filtering options"""
    
    # Build filter query
    query = {}
    
    if unit_type:
        query["unit_type"] = unit_type
    
    # Get all virtual units first
    virtual_units = await db.virtual_units.find(query).to_list(1000)
    
    # Filter by availability if requested
    if available_only:
        # Get all booked physical unit IDs
        booked_bookings = await db.bookings.find({
            "status": {"$in": [BookingStatus.BOOKED, BookingStatus.MAINTENANCE]}
        }).to_list(1000)
        booked_physical_unit_ids = {booking["physical_unit_id"] for booking in booked_bookings}
        
        # Filter out virtual units whose physical units are booked
        virtual_units = [unit for unit in virtual_units if unit["physical_unit_id"] not in booked_physical_unit_ids]
    
    # Convert to VirtualUnit objects
    result = [VirtualUnit(**unit) for unit in virtual_units]
    
    # Apply additional filters
    if min_price is not None or max_price is not None:
        filtered_result = []
        for unit in result:
            price = get_price_for_period(unit, pricing_period)
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            filtered_result.append(unit)
        result = filtered_result
    
    if amenities:
        amenity_list = [a.strip() for a in amenities.split(",")]
        result = [unit for unit in result if any(amenity in unit.amenities for amenity in amenity_list)]
    
    if size_category:
        result = [unit for unit in result if get_size_category(unit.display_size) == size_category]
    
    return result

@api_router.get("/virtual-units/{unit_id}", response_model=VirtualUnit)
async def get_virtual_unit(unit_id: str):
    """Get a specific virtual unit"""
    unit = await db.virtual_units.find_one({"id": unit_id})
    if not unit:
        raise HTTPException(status_code=404, detail="Virtual unit not found")
    return VirtualUnit(**unit)

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking_request: BookingRequest):
    """Create a new booking"""
    
    # Verify virtual unit exists
    virtual_unit = await db.virtual_units.find_one({"id": booking_request.virtual_unit_id})
    if not virtual_unit:
        raise HTTPException(status_code=404, detail="Virtual unit not found")
    
    # Check if physical unit is available
    existing_booking = await db.bookings.find_one({
        "physical_unit_id": virtual_unit["physical_unit_id"],
        "status": {"$in": [BookingStatus.BOOKED, BookingStatus.MAINTENANCE]}
    })
    
    if existing_booking:
        raise HTTPException(status_code=409, detail="Unit is not available")
    
    # Calculate total price
    virtual_unit_obj = VirtualUnit(**virtual_unit)
    daily_rate = get_price_for_period(virtual_unit_obj, booking_request.pricing_period)
    
    # For now, calculate for 30 days if monthly, 7 days if weekly, 1 day if daily
    if booking_request.pricing_period == PricingPeriod.MONTHLY:
        total_price = daily_rate
    elif booking_request.pricing_period == PricingPeriod.WEEKLY:
        total_price = daily_rate
    else:
        total_price = daily_rate
    
    # Create booking
    booking = Booking(
        virtual_unit_id=booking_request.virtual_unit_id,
        physical_unit_id=virtual_unit["physical_unit_id"],
        customer_name=booking_request.customer_name,
        customer_email=booking_request.customer_email,
        customer_phone=booking_request.customer_phone,
        payment_option=booking_request.payment_option,
        pricing_period=booking_request.pricing_period,
        start_date=booking_request.start_date,
        end_date=booking_request.end_date,
        total_price=total_price,
        move_in_date=booking_request.move_in_date,
        special_requests=booking_request.special_requests
    )
    
    booking_dict = booking.dict()
    await db.bookings.insert_one(booking_dict)
    
    return booking

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings():
    """Get all bookings"""
    bookings = await db.bookings.find().to_list(1000)
    return [Booking(**booking) for booking in bookings]

@api_router.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(booking_id: str):
    """Get a specific booking"""
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return Booking(**booking)

@api_router.get("/filter-options")
async def get_filter_options():
    """Get available filter options"""
    
    # Get unique amenities
    virtual_units = await db.virtual_units.find().to_list(1000)
    all_amenities = set()
    for unit in virtual_units:
        all_amenities.update(unit.get("amenities", []))
    
    # Get price ranges
    prices = []
    for unit in virtual_units:
        unit_obj = VirtualUnit(**unit)
        prices.extend([unit_obj.daily_price, unit_obj.weekly_price, unit_obj.monthly_price])
    
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 1000
    
    return {
        "unit_types": [ut.value for ut in UnitType],
        "amenities": sorted(list(all_amenities)),
        "size_categories": ["small", "medium", "large"],
        "pricing_periods": [pp.value for pp in PricingPeriod],
        "payment_options": [po.value for po in PaymentOption],
        "price_range": {"min": min_price, "max": max_price}
    }

# Image Management Routes

@api_router.get("/images", response_model=List[ImageAsset])
async def get_images(category: Optional[str] = None, tags: Optional[str] = None):
    """Get all images, optionally filtered by category and tags"""
    query = {}
    if category:
        query["category"] = category
    
    images = await db.image_assets.find(query).to_list(1000)
    result = [ImageAsset(**img) for img in images]
    
    # Filter by tags if provided
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        result = [img for img in result if any(tag in img.tags for tag in tag_list)]
    
    return result

@api_router.post("/images", response_model=ImageAsset)
async def create_image(image: ImageAsset):
    """Add a new image asset"""
    image_dict = image.dict()
    await db.image_assets.insert_one(image_dict)
    return image

@api_router.put("/images/{image_id}", response_model=ImageAsset)
async def update_image(image_id: str, image: ImageAsset):
    """Update an existing image asset"""
    result = await db.image_assets.replace_one({"id": image_id}, image.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@api_router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """Delete an image asset"""
    result = await db.image_assets.delete_one({"id": image_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image deleted successfully"}

@api_router.put("/virtual-units/{unit_id}/image")
async def update_unit_image(unit_id: str, image_url: str):
    """Update the image for a virtual unit"""
    result = await db.virtual_units.update_one(
        {"id": unit_id}, 
        {"$set": {"image_url": image_url}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Virtual unit not found")
    return {"message": "Unit image updated successfully"}

@api_router.post("/initialize-sample-data")
async def initialize_sample_data():
    """Initialize the system with sample data"""
    
    # Clear existing data
    await db.physical_units.delete_many({})
    await db.virtual_units.delete_many({})
    await db.bookings.delete_many({})
    await db.image_assets.delete_many({})
    
    # Create sample image assets
    image_assets = [
        # Hero Images
        ImageAsset(
            name="RV Storage Facility Hero",
            url="https://images.pexels.com/photos/13016664/pexels-photo-13016664.png",
            category="hero",
            tags=["rv", "storage", "facility", "outdoor"],
            description="Main hero image showing RV storage facility"
        ),
        ImageAsset(
            name="Boat Storage Hero",
            url="https://images.unsplash.com/photo-1711130361680-a3beb1369ef5",
            category="hero", 
            tags=["boat", "storage", "outdoor", "facility"],
            description="Hero image showing boat storage area"
        ),
        
        # Unit Images - Enclosed Parking
        ImageAsset(
            name="Enclosed RV Parking",
            url="https://images.pexels.com/photos/2797828/pexels-photo-2797828.jpeg",
            category="unit",
            tags=["enclosed", "parking", "rv", "covered"],
            description="Enclosed parking space for RVs"
        ),
        ImageAsset(
            name="Premium Enclosed Storage",
            url="https://images.pexels.com/photos/13016664/pexels-photo-13016664.png",
            category="unit",
            tags=["enclosed", "premium", "storage", "climate"],
            description="Premium enclosed storage with climate control"
        ),
        
        # Unit Images - Self Storage
        ImageAsset(
            name="Climate Controlled Storage",
            url="https://images.unsplash.com/photo-1551313158-73d016a829ae",
            category="unit",
            tags=["self_storage", "climate", "indoor", "boats"],
            description="Climate controlled self storage for boats"
        ),
        ImageAsset(
            name="Large Self Storage Unit",
            url="https://images.unsplash.com/photo-1618438502398-195e47778d6c",
            category="unit",
            tags=["self_storage", "large", "boats", "equipment"],
            description="Large self storage unit for boats and equipment"
        ),
        
        # Unit Images - Covered Parking
        ImageAsset(
            name="Covered Parking Structure",
            url="https://images.pexels.com/photos/13388790/pexels-photo-13388790.jpeg",
            category="unit",
            tags=["covered", "parking", "structure", "protection"],
            description="Covered parking structure for weather protection"
        ),
        
        # Unit Images - Outdoor Parking
        ImageAsset(
            name="Secure Outdoor Parking",
            url="https://images.unsplash.com/photo-1600181914037-b14638c1137d",
            category="unit",
            tags=["outdoor", "parking", "secure", "open"],
            description="Secure outdoor parking area"
        ),
        ImageAsset(
            name="Large Outdoor Storage",
            url="https://images.unsplash.com/photo-1711130361680-a3beb1369ef5",
            category="unit",
            tags=["outdoor", "large", "storage", "boats", "rvs"],
            description="Large outdoor storage area for boats and RVs"
        ),
        
        # Feature Images
        ImageAsset(
            name="Security Features",
            url="https://images.unsplash.com/photo-1551313158-73d016a829ae",
            category="feature",
            tags=["security", "safe", "monitoring"],
            description="Security and safety features"
        ),
        ImageAsset(
            name="Flexible Storage Options",
            url="https://images.pexels.com/photos/13388790/pexels-photo-13388790.jpeg",
            category="feature",
            tags=["flexible", "options", "variety"],
            description="Various flexible storage options"
        ),
        ImageAsset(
            name="Size Variety",
            url="https://images.unsplash.com/photo-1711130361680-a3beb1369ef5",
            category="feature",
            tags=["sizes", "variety", "multiple"],
            description="Multiple storage sizes available"
        ),
        
        # Additional Gallery Images
        ImageAsset(
            name="RV Storage Row",
            url="https://images.unsplash.com/photo-1664802915802-0ded0ff61e43",
            category="gallery",
            tags=["rv", "row", "multiple", "storage"],
            description="Row of RV storage units"
        ),
        ImageAsset(
            name="Boat Marina Storage",
            url="https://images.unsplash.com/photo-1540946485063-a40da27545f8",
            category="gallery", 
            tags=["boat", "marina", "water", "storage"],
            description="Boat storage at marina"
        ),
        ImageAsset(
            name="Indoor Storage Facility",
            url="https://images.unsplash.com/photo-1586023492125-27b2c045efd7",
            category="gallery",
            tags=["indoor", "facility", "warehouse", "storage"],
            description="Indoor storage facility warehouse"
        )
    ]
    
    for image in image_assets:
        await db.image_assets.insert_one(image.dict())
    
    # Create sample physical units
    physical_units = [
        PhysicalUnit(
            unit_number="A-001",
            actual_size="12x30",
            location="Building A - Row 1",
            amenities=["security", "covered", "electric"],
            base_price=200.0
        ),
        PhysicalUnit(
            unit_number="A-002", 
            actual_size="14x35",
            location="Building A - Row 1",
            amenities=["security", "covered", "electric", "climate_control"],
            base_price=280.0
        ),
        PhysicalUnit(
            unit_number="B-001",
            actual_size="10x25",
            location="Building B - Row 1", 
            amenities=["security"],
            base_price=150.0
        ),
        PhysicalUnit(
            unit_number="C-001",
            actual_size="16x40",
            location="Outdoor Lot C",
            amenities=["security", "24hr_access"],
            base_price=320.0
        )
    ]
    
    for unit in physical_units:
        await db.physical_units.insert_one(unit.dict())
    
    # Create sample virtual units (multiple virtual units per physical unit)
    virtual_units = []
    
    # For Physical Unit A-001 (12x30)
    physical_id = physical_units[0].id
    virtual_units.extend([
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.ENCLOSED_PARKING,
            display_size="12x30",
            display_name="Enclosed Parking 12x30",
            daily_price=8.0,
            weekly_price=50.0,
            monthly_price=200.0,
            amenities=["security", "covered", "electric"],
            image_url="https://images.pexels.com/photos/2797828/pexels-photo-2797828.jpeg",
            description="Perfect for RVs up to 30 feet. Fully enclosed with electric hookup."
        ),
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.ENCLOSED_PARKING,
            display_size="12x25",
            display_name="Enclosed Parking 12x25",
            daily_price=7.0,
            weekly_price=45.0,
            monthly_price=180.0,
            amenities=["security", "covered", "electric"],
            image_url="https://images.pexels.com/photos/2797828/pexels-photo-2797828.jpeg",
            description="Ideal for smaller RVs and boats up to 25 feet."
        ),
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.SELF_STORAGE,
            display_size="12x30",
            display_name="Self Storage 12x30",
            daily_price=10.0,
            weekly_price=65.0,
            monthly_price=250.0,
            amenities=["security", "covered", "electric", "climate_control"],
            image_url="https://images.unsplash.com/photo-1551313158-73d016a829ae",
            description="Climate-controlled storage for boats and recreational equipment."
        )
    ])
    
    # For Physical Unit A-002 (14x35)
    physical_id = physical_units[1].id
    virtual_units.extend([
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.ENCLOSED_PARKING,
            display_size="14x35",
            display_name="Enclosed Parking 14x35",
            daily_price=12.0,
            weekly_price=75.0,
            monthly_price=280.0,
            amenities=["security", "covered", "electric", "climate_control"],
            image_url="https://images.pexels.com/photos/13016664/pexels-photo-13016664.png",
            description="Premium enclosed parking for large RVs up to 35 feet."
        ),
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.SELF_STORAGE,
            display_size="14x35",
            display_name="Self Storage 14x35",
            daily_price=15.0,
            weekly_price=95.0,
            monthly_price=350.0,
            amenities=["security", "covered", "electric", "climate_control"],
            image_url="https://images.unsplash.com/photo-1618438502398-195e47778d6c",
            description="Large climate-controlled storage for boats and multiple vehicles."
        )
    ])
    
    # For Physical Unit B-001 (10x25)
    physical_id = physical_units[2].id
    virtual_units.extend([
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.COVERED_PARKING,
            display_size="10x25",
            display_name="Covered Parking 10x25",
            daily_price=6.0,
            weekly_price=35.0,
            monthly_price=150.0,
            amenities=["security"],
            image_url="https://images.pexels.com/photos/13388790/pexels-photo-13388790.jpeg",
            description="Covered parking for small to medium boats and RVs."
        ),
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.OUTDOOR_PARKING,
            display_size="10x25",
            display_name="Outdoor Parking 10x25",
            daily_price=4.0,
            weekly_price=25.0,
            monthly_price=120.0,
            amenities=["security"],
            image_url="https://images.unsplash.com/photo-1600181914037-b14638c1137d",
            description="Secure outdoor parking for boats and small RVs."
        )
    ])
    
    # For Physical Unit C-001 (16x40)
    physical_id = physical_units[3].id
    virtual_units.extend([
        VirtualUnit(
            physical_unit_id=physical_id,
            unit_type=UnitType.OUTDOOR_PARKING,
            display_size="16x40",
            display_name="Outdoor Parking 16x40",
            daily_price=10.0,
            weekly_price=60.0,
            monthly_price=320.0,
            amenities=["security", "24hr_access"],
            image_url="https://images.unsplash.com/photo-1711130361680-a3beb1369ef5",
            description="Large outdoor space perfect for big boats and large RVs."
        )
    ])
    
    for unit in virtual_units:
        await db.virtual_units.insert_one(unit.dict())
    
    return {
        "message": "Sample data initialized successfully",
        "physical_units": len(physical_units),
        "virtual_units": len(virtual_units),
        "image_assets": len(image_assets)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
