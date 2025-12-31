"""
Hierarchical Organization Models
6-level structure: Regionality → Organization → Company → Department → Team → User
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum
from app.db.base import Base


class RegionType(str, enum.Enum):
    """Geographic/Regulatory regions"""
    GDPR_EU = "GDPR_EU"  # European Union
    GDPR_UK = "GDPR_UK"  # United Kingdom
    CCPA_US = "CCPA_US"  # California/US
    APAC = "APAC"        # Asia Pacific
    LATAM = "LATAM"      # Latin America
    MEA = "MEA"          # Middle East & Africa


class Regionality(Base):
    """
    Level 1: Geographic/Regulatory Region
    Highest level of organizational hierarchy
    """
    __tablename__ = "regionalities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    region_type = Column(SQLEnum(RegionType), nullable=False)
    
    # Data sovereignty settings
    data_residency_required = Column(Boolean, default=True)
    compliance_frameworks = Column(JSONB, default=list)  # ["GDPR", "CCPA", etc.]
    
    # Configuration
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default=dict)
    
    # Relationships
    organizations = relationship("Organization", back_populates="regionality", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Regionality {self.code}: {self.name}>"


class Organization(Base):
    """
    Level 2: Organization (Top-tier Customer)
    Enterprise-level customer entity
    """
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    regionality_id = Column(Integer, ForeignKey("regionalities.id"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    legal_name = Column(String(200), nullable=True)
    
    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Business Info
    tax_id = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    employee_count = Column(Integer, nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    mfa_required = Column(Boolean, default=False)
    password_policy = Column(JSONB, default=dict)
    settings = Column(JSONB, default=dict)
    
    # Relationships
    regionality = relationship("Regionality", back_populates="organizations")
    companies = relationship("Company", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")

    def __repr__(self):
        return f"<Organization {self.slug}: {self.name}>"


class Company(Base):
    """
    Level 3: Company (Mid-tier Customer)
    Division or subsidiary within an Organization
    """
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default=dict)
    
    # Relationships
    organization = relationship("Organization", back_populates="companies")
    departments = relationship("Department", back_populates="company", cascade="all, delete-orphan")
    users = relationship("User", back_populates="company")

    def __repr__(self):
        return f"<Company {self.slug}: {self.name}>"


class Department(Base):
    """
    Level 4: Department
    Functional unit within a Company
    """
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Management
    manager_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default=dict)
    
    # Relationships
    company = relationship("Company", back_populates="departments")
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
    manager = relationship("User", foreign_keys=[manager_user_id], post_update=True)

    def __repr__(self):
        return f"<Department {self.slug}: {self.name}>"


class Team(Base):
    """
    Level 5: Team
    Working group within a Department
    """
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Management
    lead_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True)
    settings = Column(JSONB, default=dict)
    
    # Relationships
    department = relationship("Department", back_populates="teams")
    users = relationship("User", back_populates="team", foreign_keys="User.team_id")
    team_lead = relationship("User", foreign_keys=[lead_user_id], post_update=True)

    def __repr__(self):
        return f"<Team {self.slug}: {self.name}>"
