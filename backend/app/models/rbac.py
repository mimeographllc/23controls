"""
RBAC (Role-Based Access Control) Models
Handles roles, permissions, and their assignments with hierarchy scoping
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.db.base import Base


class Role(Base):
    """
    Role Definition
    Groups permissions together for easy assignment
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy Scoping (Optional - limits where role can be assigned)
    scoped_to_org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    scoped_to_company_id = Column(Integer, ForeignKey("companies.id"), nullable=True, index=True)
    scoped_to_dept_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    
    # Configuration
    is_system = Column(Boolean, default=False)  # System roles can't be deleted
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority = more powerful
    
    # Settings
    settings = Column(JSONB, default=dict)
    
    # Relationships
    scoped_organization = relationship("Organization", foreign_keys=[scoped_to_org_id])
    scoped_company = relationship("Company", foreign_keys=[scoped_to_company_id])
    scoped_department = relationship("Department", foreign_keys=[scoped_to_dept_id])
    
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role {self.slug}: {self.name}>"


class Permission(Base):
    """
    Permission Definition
    Represents a specific action or capability
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Categorization
    resource = Column(String(100), nullable=False, index=True)  # e.g., "users", "models", "orders"
    action = Column(String(50), nullable=False, index=True)     # e.g., "create", "read", "update", "delete"
    
    # Configuration
    is_system = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Settings
    settings = Column(JSONB, default=dict)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    user_permissions = relationship("UserPermission", back_populates="permission", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Permission {self.slug}: {self.resource}.{self.action}>"


class UserRole(Base):
    """
    User-Role Assignment
    Links users to roles with optional hierarchy scoping
    """
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', 'scope_type', 'scope_id', name='uq_user_role_scope'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    
    # Scope (where this role applies)
    scope_type = Column(String(50), nullable=True, index=True)  # "organization", "company", "department", "team"
    scope_id = Column(Integer, nullable=True, index=True)        # ID of the scoped entity
    
    # Assignment Info
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Expiration (optional)
    expires_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
    
    @property
    def is_valid(self) -> bool:
        """Check if role assignment is still valid"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def __repr__(self):
        scope = f" ({self.scope_type}:{self.scope_id})" if self.scope_type else ""
        return f"<UserRole User:{self.user_id} → Role:{self.role_id}{scope}>"


class RolePermission(Base):
    """
    Role-Permission Assignment
    Links permissions to roles
    """
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, index=True)
    
    # Assignment Info
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Grant/Deny
    is_grant = Column(Boolean, default=True)  # False = explicit deny
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
    
    def __repr__(self):
        action = "GRANT" if self.is_grant else "DENY"
        return f"<RolePermission {action} Permission:{self.permission_id} → Role:{self.role_id}>"


class UserPermission(Base):
    """
    User-Permission Assignment
    Direct permissions assigned to users (overrides roles)
    """
    __tablename__ = "user_permissions"
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id', 'scope_type', 'scope_id', name='uq_user_permission_scope'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False, index=True)
    
    # Scope (where this permission applies)
    scope_type = Column(String(50), nullable=True, index=True)
    scope_id = Column(Integer, nullable=True, index=True)
    
    # Assignment Info
    assigned_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Expiration (optional)
    expires_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Grant/Deny
    is_grant = Column(Boolean, default=True)  # False = explicit deny
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_permissions")
    permission = relationship("Permission", back_populates="user_permissions")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])
    
    @property
    def is_valid(self) -> bool:
        """Check if permission assignment is still valid"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def __repr__(self):
        action = "GRANT" if self.is_grant else "DENY"
        scope = f" ({self.scope_type}:{self.scope_id})" if self.scope_type else ""
        return f"<UserPermission {action} Permission:{self.permission_id} → User:{self.user_id}{scope}>"


class AuditLog(Base):
    """
    Audit Log for Permissions and Roles
    Tracks all changes to RBAC configuration
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event Info
    event_type = Column(String(100), nullable=False, index=True)  # "role_assigned", "permission_granted", etc.
    resource_type = Column(String(50), nullable=False, index=True)  # "role", "permission", "user_role", etc.
    resource_id = Column(Integer, nullable=True, index=True)
    
    # Actor
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Details
    changes = Column(JSONB, default=dict)  # Before/after state
    meta_data = Column(JSONB, default=dict)  # Renamed from 'metadata' (SQLAlchemy reserved word)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog {self.event_type} on {self.resource_type}:{self.resource_id}>"
