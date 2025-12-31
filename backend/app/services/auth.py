"""
Authentication Service
Handles JWT tokens, password hashing, MFA, and user authentication
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from passlib.context import CryptContext
from jose import JWTError, jwt
import pyotp
import qrcode
import io
import base64
import secrets
import uuid

from app.core.config import settings
from app.models import User, RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


# Password hashing context with bcrypt
# Note: bcrypt has a 72-byte password limit, so we truncate longer passwords
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Cost factor
)


class AuthService:
    """Authentication service for user auth, JWT, and MFA"""
    
    @staticmethod
    def truncate_password(password: str) -> bytes:
        """
        Truncate password to 72 bytes for bcrypt compatibility
        
        Bcrypt has a maximum password length of 72 bytes.
        We truncate to ensure compatibility.
        
        Args:
            password: Plain text password
            
        Returns:
            Password truncated to 72 bytes
        """
        password_bytes = password.encode('utf-8')
        return password_bytes[:72]
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hash of the password
        """
        # Truncate to 72 bytes for bcrypt
        truncated = AuthService.truncate_password(password)
        return pwd_context.hash(truncated)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        # Truncate to 72 bytes for bcrypt
        truncated = AuthService.truncate_password(plain_password)
        return pwd_context.verify(truncated, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            data: Payload data to encode
            expires_delta: Token expiration time (default: from settings)
        
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
        """
        Create a JWT refresh token
        
        Args:
            data: Payload data to encode
            expires_delta: Token expiration time (default: from settings)
        
        Returns:
            Tuple of (encoded token, jti)
        """
        to_encode = data.copy()
        jti = str(uuid.uuid4())
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": jti,
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt, jti
    
    @staticmethod
    def decode_token(token: str) -> Dict:
        """
        Decode and validate a JWT token
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload
        
        Raises:
            JWTError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    async def save_refresh_token(
        db: AsyncSession,
        user_id: int,
        token: str,
        jti: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RefreshToken:
        """
        Save a refresh token to the database
        
        Args:
            db: Database session
            user_id: User ID
            token: Encoded refresh token
            jti: JWT ID
            expires_at: Token expiration datetime
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Created RefreshToken object
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            jti=jti,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(refresh_token)
        await db.commit()
        await db.refresh(refresh_token)
        
        return refresh_token
    
    @staticmethod
    async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
        """
        Verify a refresh token exists and is valid
        
        Args:
            db: Database session
            token: Refresh token string
        
        Returns:
            RefreshToken object if valid, None otherwise
        """
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
        """
        Revoke a refresh token
        
        Args:
            db: Database session
            token: Refresh token to revoke
        
        Returns:
            True if token was revoked, False if not found
        """
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        refresh_token = result.scalar_one_or_none()
        
        if refresh_token:
            refresh_token.revoked = True
            refresh_token.revoked_at = datetime.utcnow()
            await db.commit()
            return True
        
        return False
    
    @staticmethod
    async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> int:
        """
        Revoke all refresh tokens for a user (e.g., on password change)
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Number of tokens revoked
        """
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            )
        )
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            token.revoked = True
            token.revoked_at = datetime.utcnow()
            count += 1
        
        await db.commit()
        return count
    
    @staticmethod
    def generate_mfa_secret() -> str:
        """
        Generate a random TOTP secret
        
        Returns:
            Base32 encoded secret
        """
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(secret: str, user_email: str, issuer: str = "SynthetIQ Signals") -> str:
        """
        Generate a QR code for MFA setup
        
        Args:
            secret: TOTP secret
            user_email: User's email address
            issuer: Issuer name for the authenticator app
        
        Returns:
            Base64 encoded PNG image data URL
        """
        # Create provisioning URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """
        Generate backup codes for MFA recovery
        
        Args:
            count: Number of backup codes to generate
        
        Returns:
            List of backup codes
        """
        return [
            "".join([str(secrets.randbelow(10)) for _ in range(8)])
            for _ in range(count)
        ]
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """
        Verify a TOTP token
        
        Args:
            secret: TOTP secret
            token: 6-digit token to verify
        
        Returns:
            True if token is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 30s window
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        email: str,
        password: str,
        mfa_token: Optional[str] = None
    ) -> Optional[User]:
        """
        Authenticate a user with email and password
        
        Args:
            db: Database session
            email: User email
            password: User password
            mfa_token: Optional MFA token if MFA is enabled
        
        Returns:
            User object if authentication successful, None otherwise
        """
        # Get user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Check if user can login
        if not user.can_login:
            return None
        
        # Verify password (only for PASSWORD security type)
        if user.security_type.value == "PASSWORD":
            if not user.password_hash:
                return None
            
            if not AuthService.verify_password(password, user.password_hash):
                # Increment failed login attempts
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                
                await db.commit()
                return None
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_token:
                return None
            
            if not user.mfa_secret:
                return None
            
            # Verify TOTP token
            if not AuthService.verify_totp(user.mfa_secret, mfa_token):
                return None
        
        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        await db.commit()
        
        return user
