"""
Authentication Dependencies
FastAPI dependencies for user authentication and authorization
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_db
from app.services.auth import AuthService
from app.models import User


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials with bearer token
        db: Database session
    
    Returns:
        Current User object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Decode token
        payload = AuthService.decode_token(token)
        
        # Check token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        # BEFORE (Broken)
        # user_id: int = payload.get("sub")  # ❌ Assumes int

        # AFTER (Fixed)
        user_id_str: str = payload.get("sub")
        user_id = int(user_id_str)  # ✅ Convert string to int
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database with eager loading
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.organization),
                selectinload(User.company),
                selectinload(User.department),
                selectinload(User.team),
            )
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        # Refresh to ensure all attributes are loaded
        await db.refresh(user)
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are active
    
    Args:
        current_user: User from get_current_user dependency
    
    Returns:
        Current active User
    
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are a superuser
    
    Args:
        current_user: User from get_current_user dependency
    
    Returns:
        Current superuser
    
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_staff_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are staff
    
    Args:
        current_user: User from get_current_user dependency
    
    Returns:
        Current staff user
    
    Raises:
        HTTPException: If user is not staff
    """
    if not current_user.is_staff and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    Useful for endpoints that optionally require authentication
    
    Args:
        credentials: Optional HTTP Authorization credentials
        db: Database session
    
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
