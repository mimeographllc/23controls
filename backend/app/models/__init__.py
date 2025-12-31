"""
Models Package
Exports all database models for use throughout the application
"""
from app.models.hierarchy import (
    Regionality,
    RegionType,
    Organization,
    Company,
    Department,
    Team,
)
from app.models.user import (
    User,
    SecurityType,
    AccountTier,
    UserStatus,
    RefreshToken,
    MFAMethod,
)
from app.models.rbac import (
    Role,
    Permission,
    UserRole,
    RolePermission,
    UserPermission,
    AuditLog,
)
from app.models.catalog import (
    Category,
    Tag,
    SoftwareModel,
    ModelTag,
    ModelType,
    Framework,
    LicenseType,
)
from app.models.eav import (
    ModelAttribute,
    ModelAttributeValue,
    AttributeDataType,
)
from app.models.media import (
    ModelVersion,
    ModelMedia,
    MediaType,
)
from app.models.licensing import (
    PricingTier,
    License,
    ModelReview,
    PricingInterval,
    LicenseStatus,
    SupportLevel,
)

__all__ = [
    # Hierarchy Models
    "Regionality",
    "RegionType",
    "Organization",
    "Company",
    "Department",
    "Team",
    
    # User Models
    "User",
    "SecurityType",
    "AccountTier",
    "UserStatus",
    "RefreshToken",
    "MFAMethod",
    
    # RBAC Models
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "UserPermission",
    "AuditLog",
    
    # Catalog Models (Phase 3)
    "Category",
    "Tag",
    "SoftwareModel",
    "ModelTag",
    "ModelType",
    "Framework",
    "LicenseType",
    
    # EAV Models (Phase 3)
    "ModelAttribute",
    "ModelAttributeValue",
    "AttributeDataType",
    
    # Media Models (Phase 3)
    "ModelVersion",
    "ModelMedia",
    "MediaType",
    
    # Licensing Models (Phase 3)
    "PricingTier",
    "License",
    "ModelReview",
    "PricingInterval",
    "LicenseStatus",
    "SupportLevel",
]
