"""
User and Authentication Models
Level 6: User - Individual accounts with authentication
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum
from app.db.base import Base


class SecurityType(str, enum.Enum):
    """User authentication method"""
    PASSWORD = "PASSWORD"
    GOOGLE_OAUTH = "GOOGLE_OAUTH"
    AMAZON_OAUTH = "AMAZON_OAUTH"
    SSO = "SSO"


class AccountTier(str, enum.Enum):
    """Account subscription tier"""
    FREE = "FREE"
    BASIC = "BASIC"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class UserStatus(str, enum.Enum):
    """User account status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class User(Base):
    """
    Level 6: User (Individual Account)
    Lowest level of hierarchy - actual people
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Hierarchy (User belongs to all levels)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    
    # Basic Info
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Authentication
    security_type = Column(SQLEnum(SecurityType), nullable=False, default=SecurityType.PASSWORD)
    password_hash = Column(String(255), nullable=True)  # Null for OAuth users
    
    # OAuth
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    amazon_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # MFA
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    mfa_backup_codes = Column(JSONB, default=list)  # Encrypted backup codes
    
    # Account
    account_tier = Column(SQLEnum(AccountTier), nullable=False, default=AccountTier.FREE)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    
    # Profile
    phone = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    timezone = Column(String(50), default="UTC")
    locale = Column(String(10), default="en_US")
    
    # Verification
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    verification_token = Column(String(255), nullable=True, unique=True)
    
    # Security
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Password Management
    password_changed_at = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True, unique=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Flags
    is_superuser = Column(Boolean, default=False)  # Platform administrator
    is_staff = Column(Boolean, default=False)  # Staff member
    is_active = Column(Boolean, default=True)
    
    # Metadata
    settings = Column(JSONB, default=dict)
    meta_data = Column(JSONB, default=dict)  # Renamed from 'metadata' (SQLAlchemy reserved word)
    
    # Relationships - Hierarchy
    organization = relationship("Organization", back_populates="users")
    company = relationship("Company", back_populates="users")
    department = relationship("Department", back_populates="users", foreign_keys=[department_id])
    team = relationship("Team", back_populates="users", foreign_keys=[team_id])
    
    # Relationships - Auth & RBAC
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserRole.user_id")
    user_permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserPermission.user_id")
    
    # Properties
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    @property
    def can_login(self) -> bool:
        """Check if user can login"""
        return (
            self.is_active and
            not self.is_locked and
            self.status == UserStatus.ACTIVE
        )
    
    def __repr__(self):
        try:
            return f"<User {self.id}: {self.email}>"
        except:
            # Handle detached instance
            return f"<User (detached)>"


class RefreshToken(Base):
    """
    Refresh Token Management
    Tracks JWT refresh tokens for logout/invalidation
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Token
    token = Column(String(500), unique=True, nullable=False, index=True)
    jti = Column(String(36), unique=True, nullable=False, index=True)  # JWT ID
    
    # Metadata
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Revocation
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Client Info
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")
    
    @property
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return (
            not self.revoked and
            self.expires_at > datetime.utcnow()
        )
    
    def __repr__(self):
        return f"<RefreshToken {self.jti} for User {self.user_id}>"


class MFAMethod(Base):
    """
    MFA Method Configuration
    Supports multiple MFA methods per user
    """
    __tablename__ = "mfa_methods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Method Type
    method_type = Column(String(50), nullable=False)  # TOTP, SMS, EMAIL, etc.
    
    # Configuration (encrypted)
    secret = Column(String(500), nullable=True)  # TOTP secret
    phone_number = Column(String(50), nullable=True)  # For SMS
    
    # Backup Codes
    backup_codes = Column(JSONB, default=list)  # Hashed backup codes
    
    # Status
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Metadata
    last_used_at = Column(DateTime, nullable=True)
    use_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<MFAMethod {self.method_type} for User {self.user_id}>"
