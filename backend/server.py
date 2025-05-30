from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks
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

# Integration services
import stripe
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Template

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Integration Services
class StripeService:
    def __init__(self, api_key: str = None):
        if api_key:
            stripe.api_key = api_key
    
    def create_checkout_session(self, amount: float, currency: str = "usd", 
                              success_url: str = "", cancel_url: str = "", 
                              metadata: dict = None):
        try:
            if not stripe.api_key:
                return {"success": False, "error": "Stripe API key not configured"}
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': 'Storage Unit Booking',
                        },
                        'unit_amount': int(amount * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata=metadata or {}
            )
            return {
                "success": True,
                "session_id": session.id,
                "url": session.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_payment_status(self, session_id: str):
        try:
            if not stripe.api_key:
                return {"success": False, "error": "Stripe API key not configured"}
                
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "success": True,
                "status": session.status,
                "payment_status": session.payment_status,
                "amount_total": session.amount_total,
                "currency": session.currency,
                "metadata": session.metadata
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class TwilioService:
    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        if account_sid and auth_token:
            self.client = TwilioClient(account_sid, auth_token)
            self.from_number = from_number
        else:
            self.client = None
    
    def send_sms(self, to_number: str, message: str):
        try:
            if not self.client:
                return {"success": False, "error": "Twilio not configured"}
            
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

class EmailService:
    def __init__(self, api_key: str = None, from_email: str = None):
        if api_key:
            self.sg = SendGridAPIClient(api_key=api_key)
            self.from_email = from_email
        else:
            self.sg = None
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        try:
            if not self.sg:
                return {"success": False, "error": "SendGrid not configured"}
            
            mail = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if text_content:
                mail.add_content(Content("text/plain", text_content))
            
            response = self.sg.send(mail)
            return {
                "success": True,
                "status_code": response.status_code
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Email Templates
class EmailTemplates:
    BOOKING_CONFIRMATION = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Booking Confirmation</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
            .content { background: #f9f9f9; padding: 20px; }
            .booking-details { background: white; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #667eea; }
            .footer { text-align: center; padding: 20px; color: #666; }
            .button { background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Booking Confirmed!</h1>
            </div>
            <div class="content">
                <p>Dear {{ customer_name }},</p>
                <p>Your RV/Boat storage booking has been confirmed! We're excited to provide you with secure storage.</p>
                
                <div class="booking-details">
                    <h3>📋 Booking Details</h3>
                    <p><strong>Unit:</strong> {{ unit_name }}</p>
                    <p><strong>Size:</strong> {{ unit_size }}</p>
                    <p><strong>Monthly Rate:</strong> ${{ amount }}</p>
                    <p><strong>Move-in Date:</strong> {{ move_in_date }}</p>
                    <p><strong>Booking ID:</strong> {{ booking_id }}</p>
                </div>
                
                <h3>📝 What's Next:</h3>
                <ul>
                    <li>📧 You'll receive gate access codes 24 hours before move-in</li>
                    <li>💳 Payment is due on the 1st of each month</li>
                    <li>📞 Contact us anytime with questions</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{ manage_booking_url }}" class="button">Manage Booking</a>
                </div>
            </div>
            <div class="footer">
                <p>Thank you for choosing our premium storage facility!</p>
                <p>Questions? Email us or call (555) 123-4567</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    PAYMENT_CONFIRMATION = """
    <!DOCTYPE html>
    <html>
    <head><title>Payment Received</title></head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #28a745; color: white; padding: 20px; text-align: center;">
                <h1>✅ Payment Received</h1>
            </div>
            <div style="background: #f9f9f9; padding: 20px;">
                <p>Dear {{ customer_name }},</p>
                <p>We've successfully received your payment! Thank you for keeping your account current.</p>
                
                <div style="background: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 8px;">
                    <h3>💳 Payment Details</h3>
                    <p><strong>Amount:</strong> ${{ amount }}</p>
                    <p><strong>Date:</strong> {{ payment_date }}</p>
                    <p><strong>Unit:</strong> {{ unit_name }}</p>
                    <p><strong>Transaction ID:</strong> {{ transaction_id }}</p>
                </div>
                
                <p>Your storage unit remains secure and accessible. Next payment due: {{ next_due_date }}</p>
            </div>
        </div>
    </body>
    </html>
    """

# SMS Templates
class SMSTemplates:
    @staticmethod
    def booking_confirmation(customer_name: str, unit_name: str, move_in_date: str, amount: float):
        return f"""
🎉 Hi {customer_name}! Your storage booking is CONFIRMED!

📦 Unit: {unit_name}
📅 Move-in: {move_in_date}
💰 Rate: ${amount:.2f}/month

Gate codes coming 24hrs before move-in. Questions? Reply HELP
        """.strip()
    
    @staticmethod
    def payment_confirmation(customer_name: str, amount: float, unit_name: str):
        return f"""
✅ Payment received! Thanks {customer_name}!

💳 Amount: ${amount:.2f}
📦 Unit: {unit_name}

Your storage is secure. Next payment due 1st of next month.
        """.strip()
    
    @staticmethod
    def move_in_reminder(customer_name: str, unit_name: str, gate_code: str = "TBD"):
        return f"""
🚚 Hi {customer_name}! Tomorrow is your move-in day!

📦 Unit: {unit_name}
🔑 Gate Code: {gate_code}

Facility hours: 6AM-10PM daily. Need help? Call (555) 123-4567
        """.strip()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize services (will be configured via API keys)
stripe_service = StripeService()
twilio_service = TwilioService()
email_service = EmailService()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Helper function to get configured services
async def get_api_key(service: str, key_name: str) -> Optional[str]:
    """Get API key from database"""
    try:
        api_key = await db.api_keys.find_one({
            "service": service,
            "key_name": key_name,
            "is_active": True
        })
        return api_key["key_value"] if api_key else None
    except:
        return None

async def configure_services():
    """Configure services with API keys from database"""
    global stripe_service, twilio_service, email_service
    
    # Configure Stripe
    stripe_key = await get_api_key("stripe", "secret_key")
    if stripe_key:
        stripe_service = StripeService(stripe_key)
    
    # Configure Twilio
    twilio_sid = await get_api_key("twilio", "account_sid")
    twilio_token = await get_api_key("twilio", "auth_token")
    twilio_number = await get_api_key("twilio", "from_number")
    if twilio_sid and twilio_token and twilio_number:
        twilio_service = TwilioService(twilio_sid, twilio_token, twilio_number)
    
    # Configure Email
    email_key = await get_api_key("sendgrid", "api_key")
    from_email = await get_api_key("sendgrid", "from_email")
    if email_key and from_email:
        email_service = EmailService(email_key, from_email)

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

class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    phone: Optional[str] = None
    first_name: str
    last_name: str
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    customer_type: str = "individual"  # individual, business, vip
    acquisition_source: Optional[str] = None  # web, referral, ads, etc.
    lifetime_value: float = 0.0
    total_bookings: int = 0
    loyalty_points: int = 0
    loyalty_tier: str = "bronze"  # bronze, silver, gold, platinum
    referral_code: Optional[str] = None
    referred_by: Optional[str] = None
    marketing_consent: bool = True
    tags: List[str] = []
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

class Location(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    email: str
    manager_name: Optional[str] = None
    hours_of_operation: Dict[str, str] = {}  # {"monday": "6AM-10PM", etc.}
    amenities: List[str] = []
    description: Optional[str] = None
    images: List[str] = []
    is_active: bool = True
    gate_access_code: Optional[str] = None
    special_instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LoyaltyTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    transaction_type: str  # earned, redeemed, expired, bonus
    points: int
    description: str
    booking_id: Optional[str] = None
    referral_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Referral(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referrer_id: str
    referred_email: str
    referred_customer_id: Optional[str] = None
    status: str = "pending"  # pending, completed, expired
    referrer_reward: int = 0  # points awarded to referrer
    referred_reward: int = 0  # points awarded to referred customer
    booking_id: Optional[str] = None  # booking that completed the referral
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class BrandSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    location_id: Optional[str] = None  # None for global settings
    company_name: str = "Premium Storage"
    logo_url: Optional[str] = None
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    accent_color: str = "#28a745"
    font_family: str = "Inter, sans-serif"
    hero_title: str = "Premium RV & Boat Storage"
    hero_subtitle: str = "Secure, flexible storage solutions"
    contact_phone: str = "(555) 123-4567"
    contact_email: str = "info@example.com"
    social_media: Dict[str, str] = {}  # {"facebook": "url", "instagram": "url"}
    custom_css: Optional[str] = None
    terms_url: Optional[str] = None
    privacy_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PushSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: Optional[str] = None
    endpoint: str
    p256dh_key: str
    auth_key: str
    user_agent: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    template_type: str  # email, sms, push
    subject: Optional[str] = None
    content: str
    variables: List[str] = []  # list of template variables like {customer_name}
    trigger: str  # booking_confirmed, payment_received, etc.
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service: str  # stripe, twilio, sendgrid
    key_name: str  # secret_key, account_sid, auth_token, etc.
    key_value: str
    is_active: bool = True
    environment: str = "test"  # test, production
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sms_enabled: bool = False
    email_enabled: bool = False
    payment_reminders_enabled: bool = True
    promotional_campaigns_enabled: bool = True
    booking_confirmations_enabled: bool = True
    move_in_reminders_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    stripe_session_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    amount: float
    currency: str = "usd"
    status: str = "pending"  # pending, completed, failed, refunded
    payment_method: str = "stripe"
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContentBlock(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str  # e.g., "hero_title", "hero_subtitle", "feature_1_title"
    content: str
    content_type: str = "text"  # text, html, markdown
    section: str  # hero, features, units, general
    editable: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PromoBanner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    message: str
    cta_text: str
    cta_url: Optional[str] = None
    banner_type: str  # success, warning, info, promotional
    funnel_stages: List[str] = []  # visitor, viewing_units, filtering, booking_started, booking_abandoned, returning_visitor
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    background_color: str = "#667eea"
    text_color: str = "#ffffff"
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FunnelEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    event_type: str  # page_view, unit_viewed, filter_used, booking_started, booking_completed, booking_abandoned
    unit_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

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

# Content Management Routes

@api_router.get("/content", response_model=List[ContentBlock])
async def get_content(section: Optional[str] = None):
    """Get all content blocks, optionally filtered by section"""
    query = {}
    if section:
        query["section"] = section
    
    content_blocks = await db.content_blocks.find(query).to_list(1000)
    return [ContentBlock(**block) for block in content_blocks]

@api_router.get("/content/{key}", response_model=ContentBlock)
async def get_content_by_key(key: str):
    """Get specific content block by key"""
    content = await db.content_blocks.find_one({"key": key})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return ContentBlock(**content)

@api_router.post("/content", response_model=ContentBlock)
async def create_content(content: ContentBlock):
    """Create a new content block"""
    content_dict = content.dict()
    await db.content_blocks.insert_one(content_dict)
    return content

@api_router.put("/content/{content_id}", response_model=ContentBlock)
async def update_content(content_id: str, content: ContentBlock):
    """Update existing content block"""
    content.updated_at = datetime.utcnow()
    result = await db.content_blocks.replace_one({"id": content_id}, content.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

@api_router.put("/content/key/{key}")
async def update_content_by_key(key: str, content_data: dict):
    """Update content block by key (simplified endpoint)"""
    update_data = {
        "content": content_data.get("content"),
        "updated_at": datetime.utcnow()
    }
    result = await db.content_blocks.update_one(
        {"key": key}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": "Content updated successfully"}

# Banner Management Routes

@api_router.get("/banners", response_model=List[PromoBanner])
async def get_banners(active_only: bool = False, funnel_stage: Optional[str] = None):
    """Get banners, optionally filtered by active status and funnel stage"""
    query = {}
    if active_only:
        query["is_active"] = True
        # Check date constraints
        now = datetime.utcnow()
        query["$or"] = [
            {"start_date": None, "end_date": None},
            {"start_date": {"$lte": now}, "end_date": None},
            {"start_date": None, "end_date": {"$gte": now}},
            {"start_date": {"$lte": now}, "end_date": {"$gte": now}}
        ]
    
    banners = await db.promo_banners.find(query).to_list(1000)
    result = [PromoBanner(**banner) for banner in banners]
    
    # Filter by funnel stage if provided
    if funnel_stage:
        result = [banner for banner in result if funnel_stage in banner.funnel_stages or not banner.funnel_stages]
    
    return result

@api_router.post("/banners", response_model=PromoBanner)
async def create_banner(banner: PromoBanner):
    """Create a new promotional banner"""
    banner_dict = banner.dict()
    await db.promo_banners.insert_one(banner_dict)
    return banner

@api_router.put("/banners/{banner_id}", response_model=PromoBanner)
async def update_banner(banner_id: str, banner: PromoBanner):
    """Update existing banner"""
    result = await db.promo_banners.replace_one({"id": banner_id}, banner.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Banner not found")
    return banner

@api_router.delete("/banners/{banner_id}")
async def delete_banner(banner_id: str):
    """Delete a banner"""
    result = await db.promo_banners.delete_one({"id": banner_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Banner not found")
    return {"message": "Banner deleted successfully"}

# Funnel Tracking Routes

@api_router.post("/funnel/track")
async def track_funnel_event(event: FunnelEvent):
    """Track a funnel event"""
    event_dict = event.dict()
    await db.funnel_events.insert_one(event_dict)
    return {"message": "Event tracked successfully"}

@api_router.get("/funnel/user/{session_id}")
async def get_user_funnel_stage(session_id: str):
    """Get current funnel stage for a user session"""
    # Get recent events for this session (last 24 hours)
    since = datetime.utcnow() - timedelta(days=1)
    events = await db.funnel_events.find({
        "session_id": session_id,
        "timestamp": {"$gte": since}
    }).sort("timestamp", -1).to_list(100)
    
    if not events:
        return {"funnel_stage": "visitor", "events_count": 0}
    
    # Determine funnel stage based on events
    event_types = [event["event_type"] for event in events]
    
    if "booking_completed" in event_types:
        stage = "booking_completed"
    elif "booking_abandoned" in event_types:
        stage = "booking_abandoned"
    elif "booking_started" in event_types:
        stage = "booking_started"
    elif "filter_used" in event_types:
        stage = "filtering"
    elif "unit_viewed" in event_types:
        stage = "viewing_units"
    elif len(events) > 5:  # Multiple page views
        stage = "returning_visitor"
    else:
        stage = "visitor"
    
    return {
        "funnel_stage": stage,
        "events_count": len(events),
        "last_activity": events[0]["timestamp"] if events else None
    }

@api_router.get("/admin/analytics")
async def get_admin_analytics():
    """Get analytics data for admin dashboard"""
    # Get total counts
    total_units = await db.virtual_units.count_documents({})
    total_bookings = await db.bookings.count_documents({})
    total_images = await db.image_assets.count_documents({})
    
    # Get recent funnel events (last 7 days)
    since = datetime.utcnow() - timedelta(days=7)
    recent_events = await db.funnel_events.find({
        "timestamp": {"$gte": since}
    }).to_list(1000)
    
    # Count events by type
    event_counts = {}
    for event in recent_events:
        event_type = event["event_type"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    # Get unique sessions
    unique_sessions = len(set(event["session_id"] for event in recent_events))
    
    return {
        "total_units": total_units,
        "total_bookings": total_bookings,
        "total_images": total_images,
        "last_7_days": {
            "unique_visitors": unique_sessions,
            "event_counts": event_counts,
            "total_events": len(recent_events)
        }
    }

# API Key Management Routes

@api_router.get("/api-keys", response_model=List[Dict[str, Any]])
async def get_api_keys():
    """Get all API keys (values masked for security)"""
    api_keys = await db.api_keys.find().to_list(1000)
    # Mask sensitive values
    for key in api_keys:
        if len(key["key_value"]) > 8:
            key["key_value"] = key["key_value"][:4] + "****" + key["key_value"][-4:]
        else:
            key["key_value"] = "****"
    return api_keys

@api_router.post("/api-keys", response_model=APIKey)
async def create_api_key(api_key: APIKey):
    """Create or update an API key"""
    # Check if key already exists
    existing = await db.api_keys.find_one({
        "service": api_key.service,
        "key_name": api_key.key_name
    })
    
    if existing:
        # Update existing key
        api_key.id = existing["id"]
        api_key.updated_at = datetime.utcnow()
        await db.api_keys.replace_one({"id": existing["id"]}, api_key.dict())
    else:
        # Create new key
        await db.api_keys.insert_one(api_key.dict())
    
    # Reconfigure services
    await configure_services()
    
    return api_key

@api_router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """Delete an API key"""
    result = await db.api_keys.delete_one({"id": key_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Reconfigure services
    await configure_services()
    
    return {"message": "API key deleted successfully"}

@api_router.get("/integration-status")
async def get_integration_status():
    """Get status of all integrations"""
    await configure_services()
    
    status = {
        "stripe": {
            "configured": stripe_service and hasattr(stripe, 'api_key') and stripe.api_key is not None,
            "test_mode": True if stripe.api_key and stripe.api_key.startswith('sk_test_') else False
        },
        "twilio": {
            "configured": twilio_service and twilio_service.client is not None,
            "from_number": twilio_service.from_number if twilio_service and twilio_service.client else None
        },
        "sendgrid": {
            "configured": email_service and email_service.sg is not None,
            "from_email": email_service.from_email if email_service and email_service.sg else None
        }
    }
    
    return status

# Payment Routes

@api_router.post("/payments/create-checkout")
async def create_payment_checkout(
    booking_id: str,
    amount: float,
    origin_url: str
):
    """Create a Stripe checkout session for booking payment"""
    await configure_services()
    
    if not stripe_service or not hasattr(stripe, 'api_key') or not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payment processing not configured")
    
    # Create payment transaction record
    transaction = PaymentTransaction(
        booking_id=booking_id,
        amount=amount,
        status="pending"
    )
    await db.payment_transactions.insert_one(transaction.dict())
    
    # Create Stripe checkout session
    success_url = f"{origin_url}/payment/success"
    cancel_url = f"{origin_url}/payment/cancel"
    
    result = stripe_service.create_checkout_session(
        amount=amount,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"booking_id": booking_id, "transaction_id": transaction.id}
    )
    
    if result["success"]:
        # Update transaction with session ID
        await db.payment_transactions.update_one(
            {"id": transaction.id},
            {"$set": {"stripe_session_id": result["session_id"]}}
        )
        return {
            "checkout_url": result["url"],
            "session_id": result["session_id"],
            "transaction_id": transaction.id
        }
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    """Check payment status"""
    await configure_services()
    
    if not stripe_service:
        raise HTTPException(status_code=503, detail="Payment processing not configured")
    
    result = stripe_service.get_payment_status(session_id)
    
    if result["success"]:
        # Update transaction status if paid
        if result["payment_status"] == "paid":
            await db.payment_transactions.update_one(
                {"stripe_session_id": session_id},
                {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
            )
        
        return result
    else:
        raise HTTPException(status_code=500, detail=result["error"])

# Notification Routes

@api_router.post("/notifications/send-booking-confirmation")
async def send_booking_confirmation(
    booking_id: str,
    background_tasks: BackgroundTasks
):
    """Send booking confirmation via SMS and Email"""
    await configure_services()
    
    # Get booking details
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Get virtual unit details
    virtual_unit = await db.virtual_units.find_one({"id": booking["virtual_unit_id"]})
    if not virtual_unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    
    customer_data = {
        "name": booking["customer_name"],
        "email": booking["customer_email"],
        "phone": booking["customer_phone"]
    }
    
    booking_data = {
        "unit_name": virtual_unit["display_name"],
        "unit_size": virtual_unit["display_size"],
        "amount": booking["total_price"],
        "move_in_date": booking["move_in_date"].strftime("%B %d, %Y") if booking.get("move_in_date") else "TBD",
        "booking_id": booking["id"]
    }
    
    # Send SMS if configured and phone provided
    if twilio_service and twilio_service.client and customer_data["phone"]:
        background_tasks.add_task(
            send_sms_notification,
            customer_data["phone"],
            SMSTemplates.booking_confirmation(
                customer_data["name"],
                booking_data["unit_name"],
                booking_data["move_in_date"],
                booking_data["amount"]
            )
        )
    
    # Send Email if configured and email provided
    if email_service and email_service.sg and customer_data["email"]:
        background_tasks.add_task(
            send_email_notification,
            customer_data["email"],
            "🎉 Booking Confirmed - RV & Boat Storage",
            EmailTemplates.BOOKING_CONFIRMATION,
            {**customer_data, **booking_data, "manage_booking_url": "#"}
        )
    
    return {"message": "Notifications queued for sending"}

@api_router.post("/notifications/send-payment-confirmation")
async def send_payment_confirmation(
    transaction_id: str,
    background_tasks: BackgroundTasks
):
    """Send payment confirmation via SMS and Email"""
    await configure_services()
    
    # Get transaction and booking details
    transaction = await db.payment_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    booking = await db.bookings.find_one({"id": transaction["booking_id"]})
    virtual_unit = await db.virtual_units.find_one({"id": booking["virtual_unit_id"]})
    
    customer_data = {
        "name": booking["customer_name"],
        "email": booking["customer_email"],
        "phone": booking["customer_phone"]
    }
    
    payment_data = {
        "amount": transaction["amount"],
        "payment_date": transaction["updated_at"].strftime("%B %d, %Y"),
        "unit_name": virtual_unit["display_name"],
        "transaction_id": transaction["id"][:8],
        "next_due_date": "1st of next month"
    }
    
    # Send SMS
    if twilio_service and twilio_service.client and customer_data["phone"]:
        background_tasks.add_task(
            send_sms_notification,
            customer_data["phone"],
            SMSTemplates.payment_confirmation(
                customer_data["name"],
                payment_data["amount"],
                payment_data["unit_name"]
            )
        )
    
    # Send Email
    if email_service and email_service.sg and customer_data["email"]:
        background_tasks.add_task(
            send_email_notification,
            customer_data["email"],
            "✅ Payment Received - Thank You!",
            EmailTemplates.PAYMENT_CONFIRMATION,
            {**customer_data, **payment_data}
        )
    
    return {"message": "Payment confirmation notifications sent"}

# Helper functions for background tasks
async def send_sms_notification(phone: str, message: str):
    """Background task to send SMS"""
    if twilio_service and twilio_service.client:
        result = twilio_service.send_sms(phone, message)
        if not result["success"]:
            logger.error(f"SMS sending failed: {result['error']}")

async def send_email_notification(email: str, subject: str, template: str, data: dict):
    """Background task to send email"""
    if email_service and email_service.sg:
        html_content = Template(template).render(**data)
        result = email_service.send_email(email, subject, html_content)
        if not result["success"]:
            logger.error(f"Email sending failed: {result['error']}")

# Advanced CRM Routes

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(
    search: Optional[str] = None,
    customer_type: Optional[str] = None,
    loyalty_tier: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get customers with filtering and search"""
    query = {}
    if customer_type:
        query["customer_type"] = customer_type
    if loyalty_tier:
        query["loyalty_tier"] = loyalty_tier
    
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
    
    customers = await db.customers.find(query).skip(offset).limit(limit).to_list(limit)
    return [Customer(**customer) for customer in customers]

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: Customer):
    """Create a new customer"""
    # Generate referral code
    if not customer.referral_code:
        customer.referral_code = f"REF{customer.first_name[:2].upper()}{customer.last_name[:2].upper()}{str(uuid.uuid4())[:6].upper()}"
    
    customer_dict = customer.dict()
    await db.customers.insert_one(customer_dict)
    return customer

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get customer details"""
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(**customer)

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer: Customer):
    """Update customer information"""
    customer.last_activity = datetime.utcnow()
    result = await db.customers.replace_one({"id": customer_id}, customer.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@api_router.get("/customers/{customer_id}/bookings")
async def get_customer_bookings(customer_id: str):
    """Get all bookings for a customer"""
    bookings = await db.bookings.find({"customer_email": {"$exists": True}}).to_list(1000)
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer_bookings = [booking for booking in bookings if booking.get("customer_email") == customer["email"]]
    return customer_bookings

# Loyalty Program Routes

@api_router.get("/loyalty/customer/{customer_id}")
async def get_customer_loyalty(customer_id: str):
    """Get customer loyalty information"""
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get loyalty transactions
    transactions = await db.loyalty_transactions.find({"customer_id": customer_id}).sort("created_at", -1).to_list(100)
    
    return {
        "customer_id": customer_id,
        "points": customer.get("loyalty_points", 0),
        "tier": customer.get("loyalty_tier", "bronze"),
        "lifetime_value": customer.get("lifetime_value", 0.0),
        "transactions": transactions
    }

@api_router.post("/loyalty/award-points")
async def award_loyalty_points(
    customer_id: str,
    points: int,
    description: str,
    booking_id: Optional[str] = None
):
    """Award loyalty points to a customer"""
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Create loyalty transaction
    transaction = LoyaltyTransaction(
        customer_id=customer_id,
        transaction_type="earned",
        points=points,
        description=description,
        booking_id=booking_id
    )
    await db.loyalty_transactions.insert_one(transaction.dict())
    
    # Update customer points and tier
    new_points = customer.get("loyalty_points", 0) + points
    new_tier = calculate_loyalty_tier(new_points)
    
    await db.customers.update_one(
        {"id": customer_id},
        {"$set": {
            "loyalty_points": new_points,
            "loyalty_tier": new_tier,
            "last_activity": datetime.utcnow()
        }}
    )
    
    return {"message": "Points awarded successfully", "new_points": new_points, "new_tier": new_tier}

@api_router.post("/loyalty/redeem-points")
async def redeem_loyalty_points(
    customer_id: str,
    points: int,
    description: str
):
    """Redeem loyalty points"""
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    current_points = customer.get("loyalty_points", 0)
    if current_points < points:
        raise HTTPException(status_code=400, detail="Insufficient points")
    
    # Create redemption transaction
    transaction = LoyaltyTransaction(
        customer_id=customer_id,
        transaction_type="redeemed",
        points=-points,
        description=description
    )
    await db.loyalty_transactions.insert_one(transaction.dict())
    
    # Update customer points
    new_points = current_points - points
    await db.customers.update_one(
        {"id": customer_id},
        {"$set": {
            "loyalty_points": new_points,
            "last_activity": datetime.utcnow()
        }}
    )
    
    return {"message": "Points redeemed successfully", "new_points": new_points}

# Referral System Routes

@api_router.post("/referrals/create")
async def create_referral(referrer_id: str, referred_email: str):
    """Create a new referral"""
    referrer = await db.customers.find_one({"id": referrer_id})
    if not referrer:
        raise HTTPException(status_code=404, detail="Referrer not found")
    
    # Check if email already referred
    existing = await db.referrals.find_one({"referred_email": referred_email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already referred")
    
    referral = Referral(
        referrer_id=referrer_id,
        referred_email=referred_email,
        referrer_reward=500,  # 500 points for successful referral
        referred_reward=250   # 250 points for new customer
    )
    
    await db.referrals.insert_one(referral.dict())
    return referral

@api_router.get("/referrals/{referrer_id}")
async def get_referrals(referrer_id: str):
    """Get all referrals by a customer"""
    referrals = await db.referrals.find({"referrer_id": referrer_id}).to_list(100)
    return referrals

# Location Management Routes

@api_router.get("/locations", response_model=List[Location])
async def get_locations(active_only: bool = True):
    """Get all locations"""
    query = {"is_active": True} if active_only else {}
    locations = await db.locations.find(query).to_list(100)
    return [Location(**location) for location in locations]

@api_router.post("/locations", response_model=Location)
async def create_location(location: Location):
    """Create a new location"""
    location_dict = location.dict()
    await db.locations.insert_one(location_dict)
    return location

@api_router.put("/locations/{location_id}", response_model=Location)
async def update_location(location_id: str, location: Location):
    """Update location information"""
    result = await db.locations.replace_one({"id": location_id}, location.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

# Brand Settings Routes

@api_router.get("/brand-settings")
async def get_brand_settings(location_id: Optional[str] = None):
    """Get brand settings for location or global"""
    query = {"location_id": location_id} if location_id else {"location_id": None}
    settings = await db.brand_settings.find_one(query)
    if not settings:
        # Return default settings
        return BrandSettings().dict()
    return settings

@api_router.post("/brand-settings", response_model=BrandSettings)
async def create_brand_settings(settings: BrandSettings):
    """Create or update brand settings"""
    settings.updated_at = datetime.utcnow()
    
    # Check if settings already exist for this location
    existing = await db.brand_settings.find_one({
        "location_id": settings.location_id
    })
    
    if existing:
        # Update existing
        settings.id = existing["id"]
        await db.brand_settings.replace_one({"id": existing["id"]}, settings.dict())
    else:
        # Create new
        await db.brand_settings.insert_one(settings.dict())
    
    return settings

# Push Notification Routes

@api_router.post("/push/subscribe")
async def subscribe_push(subscription: PushSubscription):
    """Subscribe to push notifications"""
    # Check if subscription already exists
    existing = await db.push_subscriptions.find_one({"endpoint": subscription.endpoint})
    if existing:
        # Update existing subscription
        await db.push_subscriptions.replace_one({"endpoint": subscription.endpoint}, subscription.dict())
    else:
        # Create new subscription
        await db.push_subscriptions.insert_one(subscription.dict())
    
    return {"message": "Subscription saved successfully"}

@api_router.post("/push/send")
async def send_push_notification(
    title: str,
    body: str,
    customer_id: Optional[str] = None,
    url: Optional[str] = None
):
    """Send push notification"""
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    
    subscriptions = await db.push_subscriptions.find(query).to_list(1000)
    
    # Here you would integrate with a push service like Firebase
    # For now, we'll just log the attempt
    logger.info(f"Would send push notification to {len(subscriptions)} subscribers: {title}")
    
    return {"message": f"Push notification queued for {len(subscriptions)} subscribers"}

# Helper functions
def calculate_loyalty_tier(points: int) -> str:
    """Calculate loyalty tier based on points"""
    if points >= 5000:
        return "platinum"
    elif points >= 2500:
        return "gold"
    elif points >= 1000:
        return "silver"
    else:
        return "bronze"

@api_router.post("/initialize-sample-data")
async def initialize_sample_data():
    """Initialize the system with sample data"""
    
    # Clear existing data
    await db.physical_units.delete_many({})
    await db.virtual_units.delete_many({})
    await db.bookings.delete_many({})
    await db.image_assets.delete_many({})
    await db.content_blocks.delete_many({})
    await db.promo_banners.delete_many({})
    await db.funnel_events.delete_many({})
    await db.api_keys.delete_many({})
    await db.payment_transactions.delete_many({})
    await db.customers.delete_many({})
    await db.locations.delete_many({})
    await db.loyalty_transactions.delete_many({})
    await db.referrals.delete_many({})
    await db.brand_settings.delete_many({})
    await db.push_subscriptions.delete_many({})
    
    # Create sample locations
    locations = [
        Location(
            name="Downtown Storage Center",
            address="123 Main Street",
            city="Springfield",
            state="IL",
            zip_code="62701",
            phone="(555) 123-4567",
            email="downtown@premiumstorage.com",
            manager_name="Sarah Johnson",
            hours_of_operation={
                "monday": "6AM-10PM",
                "tuesday": "6AM-10PM", 
                "wednesday": "6AM-10PM",
                "thursday": "6AM-10PM",
                "friday": "6AM-10PM",
                "saturday": "7AM-9PM",
                "sunday": "8AM-8PM"
            },
            amenities=["24/7_access", "security_cameras", "gated", "climate_control"],
            description="Our flagship downtown location with premium amenities",
            gate_access_code="1234#"
        ),
        Location(
            name="Riverside Marina Storage",
            address="456 Waterfront Drive", 
            city="Springfield",
            state="IL",
            zip_code="62702",
            phone="(555) 234-5678",
            email="riverside@premiumstorage.com",
            manager_name="Mike Thompson",
            hours_of_operation={
                "monday": "7AM-9PM",
                "tuesday": "7AM-9PM",
                "wednesday": "7AM-9PM", 
                "thursday": "7AM-9PM",
                "friday": "7AM-10PM",
                "saturday": "6AM-10PM",
                "sunday": "7AM-9PM"
            },
            amenities=["boat_launch", "power_washing", "security", "covered_parking"],
            description="Waterfront location perfect for boat storage with launch access"
        )
    ]
    
    for location in locations:
        await db.locations.insert_one(location.dict())
    
    # Create sample customers
    customers = [
        Customer(
            email="john.doe@email.com",
            phone="(555) 123-0001",
            first_name="John",
            last_name="Doe",
            customer_type="individual",
            acquisition_source="web",
            loyalty_points=750,
            loyalty_tier="silver",
            total_bookings=2,
            lifetime_value=450.0,
            referral_code="REFJOHO892E4A"
        ),
        Customer(
            email="sarah.wilson@email.com", 
            phone="(555) 123-0002",
            first_name="Sarah",
            last_name="Wilson",
            company="Wilson Boat Rentals",
            customer_type="business",
            acquisition_source="referral",
            loyalty_points=2100,
            loyalty_tier="gold",
            total_bookings=5,
            lifetime_value=1250.0,
            referral_code="REFSAWI7F8B2C"
        ),
        Customer(
            email="mike.brown@email.com",
            phone="(555) 123-0003", 
            first_name="Mike",
            last_name="Brown",
            customer_type="individual",
            acquisition_source="ads",
            loyalty_points=150,
            loyalty_tier="bronze",
            total_bookings=1,
            lifetime_value=200.0,
            referral_code="REFMIBR3D9E1F"
        )
    ]
    
    for customer in customers:
        await db.customers.insert_one(customer.dict())
    
    # Create sample loyalty transactions
    loyalty_transactions = [
        LoyaltyTransaction(
            customer_id=customers[0].id,
            transaction_type="earned",
            points=250,
            description="New customer bonus"
        ),
        LoyaltyTransaction(
            customer_id=customers[0].id,
            transaction_type="earned", 
            points=500,
            description="Booking completed - Premium RV Storage"
        ),
        LoyaltyTransaction(
            customer_id=customers[1].id,
            transaction_type="earned",
            points=1000,
            description="Business customer bonus"
        ),
        LoyaltyTransaction(
            customer_id=customers[1].id,
            transaction_type="earned",
            points=1100,
            description="Multiple bookings bonus"
        )
    ]
    
    for transaction in loyalty_transactions:
        await db.loyalty_transactions.insert_one(transaction.dict())
    
    # Create sample referrals
    referrals = [
        Referral(
            referrer_id=customers[0].id,
            referred_email="friend1@email.com",
            status="pending",
            referrer_reward=500,
            referred_reward=250
        ),
        Referral(
            referrer_id=customers[1].id,
            referred_email="business.partner@email.com", 
            status="completed",
            referrer_reward=500,
            referred_reward=250,
            completed_at=datetime.utcnow()
        )
    ]
    
    for referral in referrals:
        await db.referrals.insert_one(referral.dict())
    
    # Create default brand settings
    brand_settings = BrandSettings(
        location_id=None,  # Global settings
        company_name="Premium RV & Boat Storage",
        primary_color="#667eea",
        secondary_color="#764ba2", 
        accent_color="#28a745",
        hero_title="Premium RV & Boat Storage",
        hero_subtitle="Secure, flexible storage solutions with loyalty rewards",
        contact_phone="(555) 123-4567",
        contact_email="info@premiumstorage.com",
        social_media={
            "facebook": "https://facebook.com/premiumstorage",
            "instagram": "https://instagram.com/premiumstorage"
        }
    )
    
    await db.brand_settings.insert_one(brand_settings.dict())
    
    # Create sample content blocks
    content_blocks = [
        ContentBlock(
            key="hero_title",
            content="Premium RV & Boat Storage",
            section="hero",
            content_type="text"
        ),
        ContentBlock(
            key="hero_subtitle", 
            content="Secure, flexible storage solutions with multiple booking options",
            section="hero",
            content_type="text"
        ),
        ContentBlock(
            key="feature_1_title",
            content="Secure & Safe",
            section="features",
            content_type="text"
        ),
        ContentBlock(
            key="feature_1_description",
            content="24/7 security monitoring and controlled access",
            section="features",
            content_type="text"
        ),
        ContentBlock(
            key="feature_2_title",
            content="Flexible Booking",
            section="features", 
            content_type="text"
        ),
        ContentBlock(
            key="feature_2_description",
            content="Pay now or later, move in when convenient",
            section="features",
            content_type="text"
        ),
        ContentBlock(
            key="feature_3_title",
            content="Multiple Sizes",
            section="features",
            content_type="text"
        ),
        ContentBlock(
            key="feature_3_description",
            content="From small boats to large RVs, we have space for everything",
            section="features",
            content_type="text"
        ),
        ContentBlock(
            key="results_header_title",
            content="Available Storage Units",
            section="units",
            content_type="text"
        )
    ]
    
    for content in content_blocks:
        await db.content_blocks.insert_one(content.dict())
    
    # Create sample promotional banners
    promo_banners = [
        PromoBanner(
            title="Welcome to Premium Storage!",
            message="Browse our secure storage options and find the perfect space for your RV or boat.",
            cta_text="Explore Units",
            cta_url="#units",
            banner_type="info",
            funnel_stages=["visitor"],
            background_color="#e3f2fd",
            text_color="#1565c0"
        ),
        PromoBanner(
            title="🔍 Great Choice!",
            message="You're looking at quality storage options. Need help choosing? Our team is here to assist!",
            cta_text="Contact Us",
            cta_url="#contact",
            banner_type="promotional",
            funnel_stages=["viewing_units", "filtering"],
            background_color="#f3e5f5",
            text_color="#7b1fa2"
        ),
        PromoBanner(
            title="⚡ Almost There!",
            message="Complete your booking now and secure your storage space. Limited availability!",
            cta_text="Finish Booking",
            cta_url="#",
            banner_type="warning",
            funnel_stages=["booking_started"],
            background_color="#fff3e0",
            text_color="#ef6c00"
        ),
        PromoBanner(
            title="💔 Don't Miss Out!",
            message="You were so close! Come back and complete your booking. Your space is still available.",
            cta_text="Complete Booking",
            cta_url="#",
            banner_type="warning",
            funnel_stages=["booking_abandoned"],
            background_color="#ffebee",
            text_color="#c62828"
        ),
        PromoBanner(
            title="🎉 Thank You!",
            message="Your booking is confirmed! Check your email for details. Need to modify your booking?",
            cta_text="Manage Booking",
            cta_url="#bookings",
            banner_type="success",
            funnel_stages=["booking_completed"],
            background_color="#e8f5e8",
            text_color="#2e7d32"
        ),
        PromoBanner(
            title="👋 Welcome Back!",
            message="Ready to book another space? We have new units available with special discounts for returning customers.",
            cta_text="View New Units",
            cta_url="#units",
            banner_type="promotional",
            funnel_stages=["returning_visitor"],
            background_color="#e1f5fe",
            text_color="#0277bd"
        )
    ]
    
    for banner in promo_banners:
        await db.promo_banners.insert_one(banner.dict())
    
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
        "image_assets": len(image_assets),
        "content_blocks": len(content_blocks),
        "promo_banners": len(promo_banners),
        "locations": len(locations),
        "customers": len(customers),
        "loyalty_transactions": len(loyalty_transactions),
        "referrals": len(referrals),
        "brand_settings": 1
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
