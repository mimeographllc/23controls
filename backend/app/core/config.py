"""
Application Configuration
Uses Pydantic Settings for environment variable management
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field
from typing import List
import secrets, os, logging
logging.getLogger("pydantic").setLevel(logging.WARNING)

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "SynthetIQ Signals CDP"
    APP_ENV: str = Field(default="development")
    API_PREFIX: str = Field(default="/api/v1")
    LOG_LEVEL: str = Field(default="INFO")
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Security
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32)
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # CORS
    #CORS_ORIGINS: List[str] = Field(default=["http://localhost:80,http://localhost:3000,http://localhost:5173"])
    
    # @field_validator("CORS_ORIGINS", mode="before")
    # @classmethod
    # def parse_cors_origins(cls, v):
    #     if isinstance(v, str):
    #         return [origin.strip() for origin in v.split(",")]
    #     return v
    
    # Stripe
    STRIPE_PUBLIC_KEY: str = Field(default="")
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    
    # AWS
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_REGION: str = Field(default="us-east-1")
    ECR_REPOSITORY_URL: str = Field(default="")
    
    # Email
    SENDGRID_API_KEY: str = Field(default="")
    FROM_EMAIL: str = Field(default="noreply@synthetiqsignals.com")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/2")
    
    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10 MB
    ALLOWED_IMAGE_TYPES: str = Field(
        default="image/jpeg,image/png,image/webp"
    )
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20)
    MAX_PAGE_SIZE: int = Field(default=100)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Create global settings instance
settings = Settings()
