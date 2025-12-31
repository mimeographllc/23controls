"""
EAV (Entity-Attribute-Value) Schemas
Schemas for dynamic model attributes
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from app.models.eav import AttributeDataType


# ============ Attribute Definition Schemas ============

class AttributeBase(BaseModel):
    """Base attribute schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    data_type: AttributeDataType
    is_required: bool = False
    display_name: Optional[str] = None
    help_text: Optional[str] = None
    unit: Optional[str] = None
    group: Optional[str] = None
    sort_order: int = 0


class AttributeCreate(AttributeBase):
    """Create attribute request"""
    validation_rules: Dict[str, Any] = {}


class AttributeUpdate(BaseModel):
    """Update attribute request"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    display_name: Optional[str] = None
    help_text: Optional[str] = None
    unit: Optional[str] = None
    group: Optional[str] = None
    sort_order: Optional[int] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None
    validation_rules: Optional[Dict[str, Any]] = None


class AttributeResponse(AttributeBase):
    """Attribute response"""
    id: int
    slug: str
    validation_rules: Dict[str, Any] = {}
    is_active: bool
    
    class Config:
        from_attributes = True


# ============ Attribute Value Schemas ============

class AttributeValueSet(BaseModel):
    """Set attribute value for a model"""
    attribute_slug: str
    value: Union[str, int, float, bool, Dict, List]
    
    @validator('value')
    def validate_value_type(cls, v, values):
        """Validate value matches attribute data type"""
        # This is a basic check - full validation happens in service layer
        if v is None:
            return v
        return v


class AttributeValuesSet(BaseModel):
    """Set multiple attribute values"""
    attributes: List[AttributeValueSet]


class AttributeValueResponse(BaseModel):
    """Attribute value response"""
    attribute_id: int
    attribute_slug: str
    attribute_name: str
    data_type: AttributeDataType
    value: Union[str, int, float, bool, Dict, List, None]
    unit: Optional[str]
    
    class Config:
        from_attributes = True


class ModelAttributesResponse(BaseModel):
    """All attributes for a model"""
    model_id: int
    attributes: List[AttributeValueResponse]


# ============ Attribute Query Schemas ============

class AttributeFilter(BaseModel):
    """Filter models by attributes"""
    attribute_slug: str
    operator: str = Field(..., pattern="^(eq|ne|gt|gte|lt|lte|contains|in)$")
    value: Union[str, int, float, bool, List]


class AttributeSearch(BaseModel):
    """Search models by multiple attributes"""
    filters: List[AttributeFilter]
    match_all: bool = True  # AND vs OR logic


# ============ Common Attribute Definitions ============

class CommonAttributes:
    """
    Common attribute definitions for different model types
    These can be seeded into the database
    """
    
    IMAGE_ATTRIBUTES = [
        {
            "name": "Input Shape",
            "slug": "input_shape",
            "data_type": AttributeDataType.JSON,
            "description": "Expected input dimensions [height, width, channels]",
            "group": "Input/Output",
            "is_required": True,
            "validation_rules": {"type": "array", "items": {"type": "integer"}}
        },
        {
            "name": "Output Classes",
            "slug": "output_classes",
            "data_type": AttributeDataType.INTEGER,
            "description": "Number of output classes",
            "group": "Input/Output",
            "validation_rules": {"min": 1}
        },
        {
            "name": "Accuracy",
            "slug": "accuracy",
            "data_type": AttributeDataType.FLOAT,
            "description": "Model accuracy on test set",
            "unit": "%",
            "group": "Performance",
            "validation_rules": {"min": 0, "max": 100}
        },
        {
            "name": "Inference Time",
            "slug": "inference_time_ms",
            "data_type": AttributeDataType.FLOAT,
            "description": "Average inference time per image",
            "unit": "ms",
            "group": "Performance",
            "validation_rules": {"min": 0}
        },
        {
            "name": "Model Size",
            "slug": "model_size_mb",
            "data_type": AttributeDataType.FLOAT,
            "description": "Model file size",
            "unit": "MB",
            "group": "Technical",
            "validation_rules": {"min": 0}
        },
        {
            "name": "Requires GPU",
            "slug": "requires_gpu",
            "data_type": AttributeDataType.BOOLEAN,
            "description": "Whether model requires GPU for inference",
            "group": "Technical",
            "is_required": True
        }
    ]
    
    TEXT_ATTRIBUTES = [
        {
            "name": "Max Tokens",
            "slug": "max_tokens",
            "data_type": AttributeDataType.INTEGER,
            "description": "Maximum token length",
            "group": "Input/Output",
            "validation_rules": {"min": 1}
        },
        {
            "name": "Languages",
            "slug": "languages",
            "data_type": AttributeDataType.JSON,
            "description": "Supported languages",
            "group": "Capabilities",
            "validation_rules": {"type": "array"}
        },
        {
            "name": "Embedding Size",
            "slug": "embedding_size",
            "data_type": AttributeDataType.INTEGER,
            "description": "Embedding dimension size",
            "group": "Technical",
            "validation_rules": {"min": 1}
        },
        {
            "name": "Perplexity",
            "slug": "perplexity",
            "data_type": AttributeDataType.FLOAT,
            "description": "Model perplexity score",
            "group": "Performance",
            "validation_rules": {"min": 0}
        }
    ]
    
    AUDIO_ATTRIBUTES = [
        {
            "name": "Sample Rate",
            "slug": "sample_rate_hz",
            "data_type": AttributeDataType.INTEGER,
            "description": "Audio sample rate",
            "unit": "Hz",
            "group": "Input",
            "validation_rules": {"min": 8000, "max": 192000}
        },
        {
            "name": "Channels",
            "slug": "channels",
            "data_type": AttributeDataType.INTEGER,
            "description": "Number of audio channels (1=mono, 2=stereo)",
            "group": "Input",
            "validation_rules": {"min": 1, "max": 8}
        },
        {
            "name": "Max Duration",
            "slug": "max_duration_seconds",
            "data_type": AttributeDataType.FLOAT,
            "description": "Maximum audio duration",
            "unit": "seconds",
            "group": "Input",
            "validation_rules": {"min": 0}
        }
    ]
