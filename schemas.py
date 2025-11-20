"""
Database Schemas for the Unified Product Lifecycle & Service Management Platform

Each Pydantic model represents a MongoDB collection. The collection name is the
lowercase of the class name (e.g., User -> "user").

These schemas validate incoming data and help structure the database.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date


class User(BaseModel):
    """
    End users who store products and book services.
    Collection: "user"
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    city: Optional[str] = Field(None, description="City for geo features")
    is_active: bool = Field(True, description="Active status")


class Product(BaseModel):
    """
    A consumer-owned product stored in their digital vault.
    Collection: "product"
    """
    user_id: str = Field(..., description="Owner user _id as string")
    brand: str = Field(..., description="Brand, e.g., Samsung")
    model: str = Field(..., description="Model name/number")
    serial_number: str = Field(..., description="Unique serial number")
    category: Optional[str] = Field(None, description="Category, e.g., TV, Washer")
    purchase_date: Optional[date] = Field(None, description="Date of purchase")
    warranty_months: Optional[int] = Field(12, ge=0, le=120, description="Warranty duration in months")
    invoice_url: Optional[str] = Field(None, description="Link to stored invoice (if uploaded elsewhere)")


class ServiceCenter(BaseModel):
    """
    Authorized service centers registered by OEMs/partners.
    Collection: "servicecenter"
    """
    name: str = Field(..., description="Center name")
    brands: List[str] = Field(..., description="Brands supported")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    phone: Optional[str] = Field(None, description="Contact number")
    rating: Optional[float] = Field(4.5, ge=0, le=5, description="Average rating")


class ServiceRequest(BaseModel):
    """
    A service request created by a user for a product.
    Collection: "servicerequest"
    """
    user_id: str = Field(..., description="User _id as string")
    product_id: str = Field(..., description="Product _id as string")
    issue_description: str = Field(..., description="Problem description")
    preferred_date: Optional[date] = Field(None, description="Preferred appointment date")
    city: Optional[str] = Field(None, description="City for assignment")
    media_urls: Optional[List[str]] = Field(None, description="Optional evidence: photo/video links")
    status: str = Field("pending", description="pending, assigned, in_progress, completed, cancelled")
    assigned_center_id: Optional[str] = Field(None, description="ServiceCenter _id if assigned")


# Optional: Explicit Warranty records (computed for MVP via Product fields)
class Warranty(BaseModel):
    """
    Warranty info linked to a product. Kept for extensibility.
    Collection: "warranty"
    """
    product_id: str = Field(..., description="Product _id as string")
    start_date: date = Field(...)
    end_date: date = Field(...)
    extended: bool = Field(False)
