"""
Authentication API Endpoints
Matches the SecureAuth Postman collection structure
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional

from app.db.session import get_db
from app.schemas.auth import (
    UserSignup,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
    UserResponse,
    UserProfileUpdate,
    MessageResponse,
)
from app.services.auth import AuthService
from app.models import User, Organization, Company, SecurityType, UserStatus, AccountTier, RegionType
from app.api.v1.dependencies.auth import get_current_user, get_current_active_user


router = APIRouter(tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserSignup,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    Creates a new user with organization and optional company/division assignment.
    Sends welcome email and email verification.
    """
    from sqlalchemy.orm import selectinload
    
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Find or create organization
    org_slug = user_data.organization.lower().replace(" ", "-")
    result = await db.execute(
        select(Organization).where(Organization.slug == org_slug)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        # Create default regionality if it doesn't exist
        from app.models import Regionality
        result = await db.execute(
            select(Regionality).where(Regionality.code == "GLOBAL")
        )
        regionality = result.scalar_one_or_none()
        
        if not regionality:
            regionality = Regionality(
                name="Global",
                code="GLOBAL",
                region_type=RegionType.CCPA_US,
                data_residency_required=False
            )
            db.add(regionality)
            await db.flush()
        
        # Create organization
        organization = Organization(
            regionality_id=regionality.id,
            name=user_data.organization,
            slug=org_slug,
            is_active=True
        )
        db.add(organization)
        await db.flush()
    
    # Find or create company/division if provided
    company = None
    if user_data.division:
        company_slug = user_data.division.lower().replace(" ", "-")
        result = await db.execute(
            select(Company).where(
                Company.organization_id == organization.id,
                Company.slug == company_slug
            )
        )
        company = result.scalar_one_or_none()
        
        if not company:
            company = Company(
                organization_id=organization.id,
                name=user_data.division,
                slug=company_slug,
                is_active=True
            )
            db.add(company)
            await db.flush()
    
    # Create user
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        organization_id=organization.id,
        company_id=company.id if company else None,
        security_type=SecurityType(user_data.security_type),
        status=UserStatus.ACTIVE,
        account_tier=AccountTier.FREE,
        is_active=True,
        email_verified=False,  # Should be verified via email
    )
    
    # Hash password for PASSWORD security type
    if user_data.security_type == "PASSWORD" and user_data.password:
        user.password_hash = AuthService.hash_password(user_data.password)
    
    db.add(user)
    await db.commit()
    
    # Eagerly load relationships before returning
    await db.refresh(user)
    result = await db.execute(
        select(User)
        .where(User.id == user.id)
        .options(
            selectinload(User.organization),
            selectinload(User.company),
            selectinload(User.department),
            selectinload(User.team),
        )
    )
    user = result.scalar_one()
    
    # TODO: Send welcome email
    # TODO: Send email verification
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens
    
    Returns access and refresh tokens for API authentication.
    Validates MFA token if MFA is enabled for the user.
    """
    # Authenticate user
    user = await AuthService.authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password,
        mfa_token=login_data.mfa_token
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    
    # Create refresh token
    refresh_token, jti = AuthService.create_refresh_token(
        data={"sub": user.id}
    )
    
    # Save refresh token to database
    expires_at = datetime.utcnow() + timedelta(days=7)
    await AuthService.save_refresh_token(
        db=db,
        user_id=user.id,
        token=refresh_token,
        jti=jti,
        expires_at=expires_at,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = request.client.host if request.client else None
    await db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60  # 30 minutes in seconds
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Returns full user profile including hierarchy information.
    """
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    Validates refresh token and returns new access token.
    Refresh token remains valid until expiration.
    """
    # Verify refresh token exists and is valid
    token_obj = await AuthService.verify_refresh_token(db, refresh_data.refresh_token)
    
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token to get user ID
    try:
        payload = AuthService.decode_token(refresh_data.refresh_token)
        user_id = payload.get("sub")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token = AuthService.create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_data.refresh_token,  # Same refresh token
        token_type="bearer",
        expires_in=30 * 60
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    refresh_data: RefreshTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by revoking refresh token
    
    Revokes the provided refresh token. Access tokens cannot be revoked
    but will expire after 30 minutes.
    """
    # Revoke refresh token
    revoked = await AuthService.revoke_refresh_token(db, refresh_data.refresh_token)
    
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found"
        )
    
    return MessageResponse(message="Successfully logged out")


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Setup MFA for user account
    
    Generates TOTP secret, QR code, and backup codes.
    User must verify with /mfa/verify before MFA is enabled.
    """
    # Generate MFA secret
    secret = AuthService.generate_mfa_secret()
    
    # Generate QR code
    qr_code = AuthService.generate_qr_code(
        secret=secret,
        user_email=current_user.email
    )
    
    # Generate backup codes
    backup_codes = AuthService.generate_backup_codes()
    
    # Store secret temporarily (not enabled yet)
    current_user.mfa_secret = secret  # In production, encrypt this!
    current_user.mfa_backup_codes = [
        AuthService.hash_password(code) for code in backup_codes
    ]
    
    await db.commit()
    
    return MFASetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )


@router.post("/mfa/verify", response_model=MFAVerifyResponse)
async def verify_mfa(
    verify_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify MFA token and enable MFA
    
    Validates TOTP token from authenticator app.
    Enables MFA for user account on successful verification.
    """
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up. Call /mfa/setup first."
        )
    
    # Verify TOTP token
    is_valid = AuthService.verify_totp(
        secret=current_user.mfa_secret,
        token=verify_data.token
    )
    
    if not is_valid:
        return MFAVerifyResponse(
            verified=False,
            message="Invalid MFA token"
        )
    
    # Enable MFA
    current_user.mfa_enabled = True
    await db.commit()
    
    return MFAVerifyResponse(
        verified=True,
        message="MFA successfully enabled"
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile
    
    Updates user profile information.
    Cannot change email or password (use specific endpoints for those).
    """
    from sqlalchemy.orm import selectinload
    
    # Update fields
    if profile_data.first_name is not None:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        current_user.last_name = profile_data.last_name
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
    if profile_data.bio is not None:
        current_user.bio = profile_data.bio
    if profile_data.timezone is not None:
        current_user.timezone = profile_data.timezone
    if profile_data.locale is not None:
        current_user.locale = profile_data.locale
    
    await db.commit()
    
    # Reload with relationships
    result = await db.execute(
        select(User)
        .where(User.id == current_user.id)
        .options(
            selectinload(User.organization),
            selectinload(User.company),
            selectinload(User.department),
            selectinload(User.team),
        )
    )
    user = result.scalar_one()
    
    return user


@router.post("/me/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password
    
    Requires current password for verification.
    Revokes all existing refresh tokens for security.
    """
    # Verify old password
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesn't have a password (OAuth user)"
        )
    
    if not AuthService.verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Set new password
    current_user.password_hash = AuthService.hash_password(password_data.new_password)
    current_user.password_changed_at = datetime.utcnow()
    
    # Revoke all existing refresh tokens
    await AuthService.revoke_all_user_tokens(db, current_user.id)
    
    await db.commit()
    
    return MessageResponse(
        message="Password changed successfully. Please login again with your new password."
    )
