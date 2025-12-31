"""
Licensing and Pricing Models
Handle monetization, pricing tiers, and user licenses
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Enum as SQLEnum, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum
from app.db.base import Base


class PricingInterval(str, enum.Enum):
    """Billing interval"""
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    ONE_TIME = "ONE_TIME"


class LicenseStatus(str, enum.Enum):
    """License status"""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class SupportLevel(str, enum.Enum):
    """Support level"""
    NONE = "NONE"
    COMMUNITY = "COMMUNITY"
    EMAIL = "EMAIL"
    PRIORITY = "PRIORITY"
    ENTERPRISE = "ENTERPRISE"


class PricingTier(Base):
    """
    Pricing Tier Definition
    Different pricing options for a model
    """
    __tablename__ = "pricing_tiers"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("software_models.id"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False)  # "Free", "Pro", "Enterprise"
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Pricing (in cents to avoid floating point issues)
    price_monthly_cents = Column(Integer, nullable=True)  # e.g., 999 = $9.99
    price_yearly_cents = Column(Integer, nullable=True)   # e.g., 9990 = $99.90
    price_one_time_cents = Column(Integer, nullable=True)  # One-time purchase
    
    # Features
    features = Column(JSONB, default=list)  # ["Feature 1", "Feature 2"]
    
    # Limits
    api_calls_limit = Column(Integer, nullable=True)  # Monthly API call limit
    download_limit = Column(Integer, nullable=True)   # Download limit
    support_level = Column(SQLEnum(SupportLevel), default=SupportLevel.NONE)
    
    # Display
    sort_order = Column(Integer, default=0)
    is_popular = Column(Boolean, default=False)  # Highlight as popular choice
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    meta_data = Column(JSONB, default=dict)
    
    # Relationships
    model = relationship("SoftwareModel", back_populates="pricing_tiers")
    licenses = relationship("License", back_populates="pricing_tier")
    
    def __repr__(self):
        try:
            return f"<PricingTier {self.name} for Model:{self.model_id}>"
        except:
            return f"<PricingTier (detached)>"


class License(Base):
    """
    User License
    Represents a user's purchase/access to a model
    """
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("software_models.id"), nullable=False, index=True)
    pricing_tier_id = Column(Integer, ForeignKey("pricing_tiers.id"), nullable=True, index=True)
    
    # License Key
    license_key = Column(String(255), unique=True, nullable=False, index=True)  # UUID or generated key
    
    # Status
    status = Column(SQLEnum(LicenseStatus), nullable=False, default=LicenseStatus.PENDING, index=True)
    
    # Validity Period
    starts_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, index=True)  # Null = lifetime
    
    # Renewal
    auto_renew = Column(Boolean, default=False)
    
    # Payment Integration
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    
    # Usage Tracking
    api_calls_used = Column(Integer, default=0)
    downloads_used = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Dates
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Metadata
    meta_data = Column(JSONB, default=dict)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    model = relationship("SoftwareModel", back_populates="licenses")
    pricing_tier = relationship("PricingTier", back_populates="licenses")
    
    @property
    def is_active(self) -> bool:
        """Check if license is currently active"""
        if self.status != LicenseStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    @property
    def is_expired(self) -> bool:
        """Check if license is expired"""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        return False
    
    def __repr__(self):
        try:
            return f"<License {self.license_key} User:{self.user_id} Model:{self.model_id}>"
        except:
            return f"<License (detached)>"


class ModelReview(Base):
    """
    User Review and Rating
    Users can review and rate models
    """
    __tablename__ = "model_reviews"

    id = Column(Integer, primary_key=True, index=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("software_models.id"), nullable=False, index=True)
    
    # Rating (1-5 stars)
    rating = Column(Integer, nullable=False, index=True)
    
    # Review Content
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    
    # Social
    helpful_count = Column(Integer, default=0)  # How many found this helpful
    
    # Verification
    is_verified_purchase = Column(Boolean, default=False)  # User has license
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    model = relationship("SoftwareModel", back_populates="reviews")
    
    def __repr__(self):
        try:
            return f"<ModelReview {self.rating}★ by User:{self.user_id} for Model:{self.model_id}>"
        except:
            return f"<ModelReview (detached)>"
