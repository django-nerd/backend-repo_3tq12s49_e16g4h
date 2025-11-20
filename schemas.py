"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    hashed_password: str = Field(..., description="Password hash (never store raw password)")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    is_active: bool = Field(True, description="Whether user is active")

class Course(BaseModel):
    """
    Courses collection schema
    Collection name: "course"
    """
    title: str = Field(..., description="Course title")
    description: str = Field(..., description="Short description")
    price: float = Field(..., ge=0, description="Price in USD")
    level: str = Field("Beginner", description="Difficulty level")
    duration: str = Field("", description="Total duration, e.g., '6h 30m'")
    lessons_count: int = Field(0, ge=0, description="Number of lessons")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    preview_video_url: Optional[str] = Field(None, description="Preview video URL")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product"
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field("material", description="Product category, e.g., material, book")
    in_stock: bool = Field(True, description="Whether product is in stock")
    image_url: Optional[str] = Field(None, description="Image URL")

class ContactMessage(BaseModel):
    """
    Contact messages from the website
    Collection name: "contactmessage"
    """
    name: str = Field(..., description="Sender name")
    email: str = Field(..., description="Sender email")
    message: str = Field(..., description="Message body")
