"""
Media and Versioning Models
Handle model versions and associated media assets
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Enum as SQLEnum, BigInteger, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum
from app.db.base import Base


class MediaType(str, enum.Enum):
    """Type of media asset"""
    SCREENSHOT = "SCREENSHOT"
    DEMO = "DEMO"
    THUMBNAIL = "THUMBNAIL"
    LOGO = "LOGO"
    BANNER = "BANNER"
    VIDEO = "VIDEO"


class ModelVersion(Base):
    """
    Model Version Tracking
    Maintains version history for models
    """
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("software_models.id"), nullable=False, index=True)
    
    # Version Info
    version = Column(String(50), nullable=False, index=True)  # "1.0.0", "2.1.3", etc.
    release_notes = Column(Text, nullable=True)  # Markdown
    
    # File Info
    file_url = Column(String(500), nullable=True)  # S3 URL
    file_size_bytes = Column(BigInteger, nullable=True)
    checksum_sha256 = Column(String(64), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Dates
    released_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metadata
    meta_data = Column(JSONB, default=dict)
    
    # Stats
    download_count = Column(BigInteger, default=0)
    
    # Relationships
    model = relationship("SoftwareModel", back_populates="versions")
    
    def __repr__(self):
        try:
            return f"<ModelVersion {self.version} for Model:{self.model_id}>"
        except:
            return f"<ModelVersion (detached)>"


class ModelMedia(Base):
    """
    Model Media Assets
    Images, videos, demos, etc.
    """
    __tablename__ = "model_media"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("software_models.id"), nullable=False, index=True)
    
    # Media Type
    media_type = Column(SQLEnum(MediaType), nullable=False, index=True)
    
    # File Info
    file_url = Column(String(500), nullable=False)  # S3 URL
    file_size_bytes = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)  # "image/png", "video/mp4"
    
    # Image Dimensions (for images/videos)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Display Info
    alt_text = Column(String(500), nullable=True)
    caption = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    
    # Dates
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    model = relationship("SoftwareModel", back_populates="media")
    
    def __repr__(self):
        try:
            return f"<ModelMedia {self.media_type} for Model:{self.model_id}>"
        except:
            return f"<ModelMedia (detached)>"
