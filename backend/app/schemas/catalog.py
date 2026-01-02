"""
Catalog Schemas
Pydantic schemas for model catalog operations
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from app.models.catalog import ModelType, Framework, LicenseType


# ============ Category Schemas ============

class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    sort_order: int = 0
    is_active: bool = True


# class CategoryCreate(CategoryBase):
#     """Create category request"""
#     parent_id: Optional[int] = None
class CategoryCreate(CategoryBase):
    """Create category request"""
    parent_id: Optional[int] = None
    
    @validator('parent_id', pre=True)
    @classmethod
    def convert_zero_to_null(cls, v):
        """Convert 0 to None for root categories"""
        if v == 0:
            return None
        return v

class CategoryUpdate(BaseModel):
    """Update category request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon_url: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

    #fix: 0 to none validation on categrories.
    @validator('parent_id', pre=True)
    @classmethod
    def convert_zero_to_null(cls, v):
        """Convert 0 to None for root categories"""
        if v == 0:
            return None
        return v


class CategoryResponse(CategoryBase):
    """Category response"""
    id: int
    slug: str
    parent_id: Optional[int]
    meta_data: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class CategoryTree(CategoryResponse):
    """Category with children (tree structure)"""
    children: List['CategoryTree'] = []
    
    class Config:
        from_attributes = True


# ============ Tag Schemas ============

class TagBase(BaseModel):
    """Base tag schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    """Create tag request"""
    pass


class TagUpdate(BaseModel):
    """Update tag request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TagResponse(TagBase):
    """Tag response"""
    id: int
    slug: str
    usage_count: int = 0
    
    class Config:
        from_attributes = True


# ============ Software Model Schemas ============

class ModelBase(BaseModel):
    """Base model schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    long_description: Optional[str] = None
    category_id: Optional[int] = None
    model_type: ModelType
    framework: Optional[Framework] = None
    license_type: LicenseType = LicenseType.MIT
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    demo_url: Optional[str] = None


class ModelCreate(ModelBase):
    """Create model request"""
    tags: List[int] = []  # Tag IDs
    attributes: Dict[str, Any] = {}  # Attribute slug → value


class ModelUpdate(BaseModel):
    """Update model request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    long_description: Optional[str] = None
    category_id: Optional[int] = None
    model_type: Optional[ModelType] = None
    framework: Optional[Framework] = None
    license_type: Optional[LicenseType] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    demo_url: Optional[str] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None


class ModelResponse(ModelBase):
    """Model response"""
    id: int
    slug: str
    creator_user_id: int
    organization_id: int
    version_current: Optional[str]
    download_count: int = 0
    view_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    is_public: bool
    is_featured: bool
    is_verified: bool
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    meta_data: Dict[str, Any] = {}
    
    # Related data
    tags: List[TagResponse] = []
    category: Optional[CategoryResponse] = None
    
    class Config:
        from_attributes = True


class ModelDetail(ModelResponse):
    """Detailed model response with all relations"""
    attributes: Dict[str, Any] = {}  # Attribute slug → value
    versions: List['ModelVersionResponse'] = []
    media: List['ModelMediaResponse'] = []
    pricing_tiers: List['PricingTierResponse'] = []
    
    class Config:
        from_attributes = True


class ModelListItem(BaseModel):
    """Simplified model for list views"""
    id: int
    slug: str
    name: str
    description: str
    model_type: ModelType
    framework: Optional[Framework]
    category_id: Optional[int]
    download_count: int
    rating_avg: float
    rating_count: int
    is_featured: bool
    is_verified: bool
    published_at: Optional[datetime]
    
    # Thumbnail
    thumbnail_url: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============ Model Version Schemas ============

class ModelVersionBase(BaseModel):
    """Base version schema"""
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")  # Semver: 1.0.0
    release_notes: Optional[str] = None
    file_url: Optional[str] = None
    file_size_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$")


class ModelVersionCreate(ModelVersionBase):
    """Create version request"""
    pass


class ModelVersionResponse(ModelVersionBase):
    """Version response"""
    id: int
    model_id: int
    is_active: bool
    released_at: datetime
    download_count: int = 0
    meta_data: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


# ============ Model Media Schemas ============

class ModelMediaBase(BaseModel):
    """Base media schema"""
    media_type: str  # Will be MediaType enum
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    sort_order: int = 0


class ModelMediaCreate(ModelMediaBase):
    """Create media request (after upload)"""
    file_url: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ModelMediaResponse(ModelMediaBase):
    """Media response"""
    id: int
    model_id: int
    file_url: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# ============ Search & Filter Schemas ============

class ModelFilter(BaseModel):
    """Model filtering parameters"""
    category_id: Optional[int] = None
    tags: Optional[List[int]] = None  # Tag IDs
    model_type: Optional[ModelType] = None
    framework: Optional[Framework] = None
    license_type: Optional[LicenseType] = None
    is_featured: Optional[bool] = None
    is_verified: Optional[bool] = None
    min_rating: Optional[float] = Field(None, ge=0, le=5)
    search: Optional[str] = None  # Full-text search


class ModelSort(Enum):
    """Sort options"""
    POPULAR = "popular"  # download_count DESC
    RECENT = "recent"    # published_at DESC
    RATING = "rating"    # rating_avg DESC
    NAME = "name"        # name ASC


class ModelListQuery(BaseModel):
    
    """Model list query parameters"""
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    
    # Filtering
    filters: Optional[ModelFilter] = Field(None)
    
    # Sorting
    sort_by: ModelSort = ModelSort.POPULAR
    
    
class ModelListResponse(BaseModel):
    """Paginated model list response"""
    items: List[ModelListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============ Pricing Tier Schemas ============

class PricingTierBase(BaseModel):
    """Base pricing tier schema"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    price_monthly_cents: Optional[int] = Field(None, ge=0)
    price_yearly_cents: Optional[int] = Field(None, ge=0)
    price_one_time_cents: Optional[int] = Field(None, ge=0)
    features: List[str] = []
    api_calls_limit: Optional[int] = None
    download_limit: Optional[int] = None
    support_level: str = "NONE"
    sort_order: int = 0
    is_popular: bool = False


class PricingTierCreate(PricingTierBase):
    """Create pricing tier request"""
    pass


class PricingTierResponse(PricingTierBase):
    """Pricing tier response"""
    id: int
    model_id: int
    slug: str
    is_active: bool
    meta_data: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


# ============ License Schemas ============

class LicenseCreate(BaseModel):
    """Create license (purchase) request"""
    model_id: int
    pricing_tier_id: int
    payment_method_id: Optional[str] = None  # Stripe payment method


class LicenseResponse(BaseModel):
    """License response"""
    id: int
    user_id: int
    model_id: int
    pricing_tier_id: Optional[int]
    license_key: str
    status: str
    starts_at: datetime
    expires_at: Optional[datetime]
    auto_renew: bool
    purchased_at: datetime
    
    # Usage
    api_calls_used: int
    downloads_used: int
    last_used_at: Optional[datetime]
    
    # Computed
    is_active: bool
    is_expired: bool
    
    class Config:
        from_attributes = True


# ============ Review Schemas ============

class ReviewCreate(BaseModel):
    """Create review request"""
    model_id: int
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None


class ReviewUpdate(BaseModel):
    """Update review request"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None


class ReviewResponse(BaseModel):
    """Review response"""
    id: int
    user_id: int
    model_id: int
    rating: int
    title: Optional[str]
    content: Optional[str]
    helpful_count: int
    is_verified_purchase: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Forward references for nested models
CategoryTree.model_rebuild()
ModelDetail.model_rebuild()
