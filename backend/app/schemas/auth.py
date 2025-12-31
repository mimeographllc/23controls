

"""
Authentication Schemas
Request/Response models for authentication endpoints
Matches the SecureAuth Postman collection structure
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserSignup(BaseModel):
    """Sign up request schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    organization: str = Field(..., min_length=1, max_length=200, description="Organization name")
    division: Optional[str] = Field(None, max_length=200, description="Company/Division name")
    security_type: str = Field("PASSWORD", description="PASSWORD, GOOGLE_OAUTH, or AMAZON_OAUTH")
    password: Optional[str] = Field(None, min_length=8, max_length=72)  # bcrypt limit
    
    @validator("password")
    def validate_password(cls, v, values):
        """Validate password strength for PASSWORD security type"""
        if values.get("security_type") == "PASSWORD":
            if not v:
                raise ValueError("Password is required for PASSWORD security type")
            
            # Check length (bcrypt has 72-byte limit)
            if len(v) < 8:
                raise ValueError("Password must be at least 8 characters")
            if len(v.encode('utf-8')) > 72:
                raise ValueError("Password is too long (max 72 bytes)")
            
            # Check for uppercase
            if not re.search(r"[A-Z]", v):
                raise ValueError("Password must contain at least one uppercase letter")
            
            # Check for lowercase
            if not re.search(r"[a-z]", v):
                raise ValueError("Password must contain at least one lowercase letter")
            
            # Check for digit
            if not re.search(r"\d", v):
                raise ValueError("Password must contain at least one digit")
            
            # Check for special character
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
                raise ValueError("Password must contain at least one special character")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "organization": "Acme Corp",
                "division": "Engineering",
                "security_type": "PASSWORD",
                "password": "SecurePass123!"
            }
        }


class UserLogin(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str
    mfa_token: Optional[str] = Field(None, description="6-digit MFA token if MFA is enabled")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@example.com",
                "password": "Admin123!"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiry in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=72)  # bcrypt limit
    
    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength"""
        # Check length (bcrypt has 72-byte limit)
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password is too long (max 72 bytes)")
        
        # Check for uppercase
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for lowercase
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        
        # Check for special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldPass123!",
                "new_password": "NewSecurePass123!"
            }
        }


class MFASetupResponse(BaseModel):
    """MFA setup response with QR code"""
    secret: str = Field(..., description="Base32 encoded TOTP secret")
    qr_code: str = Field(..., description="Data URL for QR code image")
    backup_codes: list[str] = Field(..., description="Backup codes for account recovery")
    
    class Config:
        json_schema_extra = {
            "example": {
                "secret": "JBSWY3DPEHPK3PXP",
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUh...",
                "backup_codes": [
                    "12345678",
                    "87654321",
                    "13579246",
                    "24681357",
                    "98765432"
                ]
            }
        }


class MFAVerifyRequest(BaseModel):
    """MFA token verification request"""
    token: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "123456"
            }
        }


class MFAVerifyResponse(BaseModel):
    """MFA verification response"""
    verified: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "verified": True,
                "message": "MFA successfully enabled"
            }
        }


class UserResponse(BaseModel):
    """Current user response"""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    security_type: str
    account_tier: str
    status: str
    mfa_enabled: bool
    email_verified: bool
    is_active: bool
    is_staff: bool
    is_superuser: bool
    
    # Hierarchy
    organization_id: int
    company_id: Optional[int]
    department_id: Optional[int]
    team_id: Optional[int]
    
    # Profile
    phone: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    locale: str
    
    # Dates
    #created_at: datetime
    #updated_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "full_name": "Admin User",
                "security_type": "PASSWORD",
                "account_tier": "FREE",
                "status": "ACTIVE",
                "mfa_enabled": False,
                "email_verified": True,
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "organization_id": 1,
                "company_id": 1,
                "department_id": None,
                "team_id": None,
                "phone": None,
                "avatar_url": None,
                "timezone": "UTC",
                "locale": "en_US",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-20T12:00:00Z"
            }
        }


class UserProfileUpdate(BaseModel):
    """Update user profile request"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=1000)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1-555-0123",
                "timezone": "America/New_York",
                "locale": "en_US"
            }
        }


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }
