"""
Catalog Models
Software model catalog with categories and tags
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Enum as SQLEnum, BigInteger, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum
from app.db.base import Base


class ModelType(str, enum.Enum):
    """Type of AI model"""
    IMAGE = "IMAGE"
    TEXT = "TEXT"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    MULTIMODAL = "MULTIMODAL"
    OTHER = "OTHER"


class Framework(str, enum.Enum):
    """ML/AI Framework"""
    PYTORCH = "PYTORCH"
    TENSORFLOW = "TENSORFLOW"
    KERAS = "KERAS"
    ONNX = "ONNX"
    SCIKIT_LEARN = "SCIKIT_LEARN"
    HUGGINGFACE = "HUGGINGFACE"
    JAX = "JAX"
    MXNET = "MXNET"
    OTHER = "OTHER"


class LicenseType(str, enum.Enum):
    """Software license type"""
    MIT = "MIT"
    APACHE_2 = "APACHE_2"
    GPL_3 = "GPL_3"
    BSD = "BSD"
    PROPRIETARY = "PROPRIETARY"
    CREATIVE_COMMONS = "CREATIVE_COMMONS"
    OTHER = "OTHER"


class Category(Base):
    """
    Hierarchical Category System
    Organizes models into tree structure
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Display
    icon_url = Column(String(500), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color like #FF5733
    sort_order = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    meta_data = Column(JSONB, default=dict)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    models = relationship("SoftwareModel", back_populates="category")
    
    def __repr__(self):
        try:
            return f"<Category {self.slug}: {self.name}>"
        except:
            return f"<Category (detached)>"


class Tag(Base):
    """
    Flexible Tag System
    Labels for models (frameworks, features, etc.)
    """
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Display
    color = Column(String(7), nullable=True)  # Hex color
    
    # Stats
    usage_count = Column(Integer, default=0)  # Number of models with this tag
    
    # Relationships
    model_tags = relationship("ModelTag", back_populates="tag", cascade="all, delete-orphan")
    
    def __repr__(self):
        try:
            return f"<Tag {self.slug}: {self.name}>"
        except:
            return f"<Tag (detached)>"


class SoftwareModel(Base):
    """
    Core Software Model Entity
    Represents an AI/ML model in the catalog
    """
    __tablename__ = "software_models"

    id = Column(Integer, primary_key=True, index=True)
    
    # Ownership
    creator_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Categorization
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    long_description = Column(Text, nullable=True)  # Markdown
    
    # Technical Info
    model_type = Column(SQLEnum(ModelType), nullable=False, index=True)
    framework = Column(SQLEnum(Framework), nullable=True, index=True)
    license_type = Column(SQLEnum(LicenseType), nullable=False, default=LicenseType.MIT)
    
    # Links
    repository_url = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    demo_url = Column(String(500), nullable=True)
    
    # Versioning
    version_current = Column(String(50), nullable=True)  # Current version like "1.0.0"
    
    # Stats
    download_count = Column(BigInteger, default=0, index=True)
    view_count = Column(BigInteger, default=0, index=True)
    rating_avg = Column(Float, default=0.0, index=True)
    rating_count = Column(Integer, default=0)
    
    # Status Flags
    is_public = Column(Boolean, default=False, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    is_verified = Column(Boolean, default=False, index=True)  # Staff verified
    
    # Dates
    published_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow(), nullable=False)
    
    # Metadata
    meta_data = Column(JSONB, default=dict)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    category = relationship("Category", back_populates="models")
    
    # Related entities
    model_tags = relationship("ModelTag", back_populates="model", cascade="all, delete-orphan")
    attribute_values = relationship("ModelAttributeValue", back_populates="model", cascade="all, delete-orphan")
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    media = relationship("ModelMedia", back_populates="model", cascade="all, delete-orphan")
    pricing_tiers = relationship("PricingTier", back_populates="model", cascade="all, delete-orphan")
    licenses = relationship("License", back_populates="model")
    reviews = relationship("ModelReview", back_populates="model", cascade="all, delete-orphan")
    
    def __repr__(self):
        try:
            return f"<SoftwareModel {self.slug}: {self.name}>"
        except:
            return f"<SoftwareModel (detached)>"


class ModelTag(Base):
    """
    Model-Tag Join Table
    Many-to-many relationship
    """
    __tablename__ = "model_tags"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("software_models.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False, index=True)
    
    # Relationships
    model = relationship("SoftwareModel", back_populates="model_tags")
    tag = relationship("Tag", back_populates="model_tags")
    
    def __repr__(self):
        return f"<ModelTag Model:{self.model_id} → Tag:{self.tag_id}>"
