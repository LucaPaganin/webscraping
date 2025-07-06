#!/usr/bin/env python3
"""
Real Estate Data Models
======================

Pydantic models for standardized real estate data representation.

Author: Lucas P
Date: July 6, 2025
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class RealEstateAd(BaseModel):
    """
    Standardized data model for real estate advertisements.
    
    This model provides a unified structure for real estate data from any source,
    ensuring consistency across different websites and APIs.
    """
    
    # Core identification
    id: str = Field(..., description="Unique identifier for the ad")
    source_url: str = Field(..., description="Original URL of the advertisement")
    source_website: str = Field(..., description="Source website (e.g., 'immobiliare.it')")
    
    # Basic property information
    title: str = Field(..., description="Property title/headline")
    description: Optional[str] = Field(None, description="Detailed property description")
    property_type: Optional[str] = Field(None, description="Type of property (apartment, house, etc.)")
    contract_type: str = Field(..., description="Contract type (rent/sale)")
    
    # Pricing information
    price: Optional[float] = Field(None, description="Property price")
    price_formatted: Optional[str] = Field(None, description="Formatted price string")
    price_per_sqm: Optional[float] = Field(None, description="Price per square meter")
    currency: str = Field(default="EUR", description="Currency code")
    
    # Property characteristics
    surface: Optional[int] = Field(None, description="Surface area in square meters")
    rooms: Optional[int] = Field(None, description="Number of rooms")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    floor: Optional[str] = Field(None, description="Floor level")
    
    # Location information
    address: Optional[str] = Field(None, description="Property address")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    city: Optional[str] = Field(None, description="City name")
    comune: Optional[str] = Field(None, description="Municipality/comune name")
    province: Optional[str] = Field(None, description="Province code")
    region: Optional[str] = Field(None, description="Region name")
    zone: Optional[str] = Field(None, description="Zone/neighborhood name")
    zone_id: Optional[str] = Field(None, description="Zone identifier")
    
    # Property features (boolean flags)
    elevator: Optional[bool] = Field(None, description="Elevator availability")
    balcony: Optional[bool] = Field(None, description="Balcony presence")
    terrace: Optional[bool] = Field(None, description="Terrace presence")
    garden: Optional[bool] = Field(None, description="Garden presence")
    air_conditioning: Optional[bool] = Field(None, description="Air conditioning availability")
    parking: Optional[bool] = Field(None, description="Parking availability")
    
    # Additional information
    energy_class: Optional[str] = Field(None, description="Energy efficiency class")
    condition: Optional[str] = Field(None, description="Property condition")
    heating: Optional[str] = Field(None, description="Heating system type")
    furnished: Optional[bool] = Field(None, description="Furnished status")
    
    # Media and features
    images: List[str] = Field(default_factory=list, description="List of image URLs")
    features: List[str] = Field(default_factory=list, description="List of property features")
    
    # Metadata
    date_created: Optional[datetime] = Field(None, description="Ad creation date")
    date_scraped: datetime = Field(default_factory=datetime.now, description="Date when scraped")
    
    @validator('price', 'price_per_sqm')
    def validate_price(cls, v):
        """Ensure prices are non-negative."""
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v
    
    @validator('surface', 'rooms', 'bedrooms', 'bathrooms')
    def validate_positive_integers(cls, v):
        """Ensure integer fields are positive."""
        if v is not None and v <= 0:
            raise ValueError('Value must be positive')
        return v
    
    @validator('latitude')
    def validate_latitude(cls, v):
        """Validate latitude range."""
        if v is not None and not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v):
        """Validate longitude range."""
        if v is not None and not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database storage."""
        return self.dict(exclude_none=False, by_alias=True)
    
    def calculate_price_per_sqm(self) -> Optional[float]:
        """Calculate price per square meter if possible."""
        if self.price and self.surface and self.surface > 0:
            return round(self.price / self.surface, 2)
        return None
