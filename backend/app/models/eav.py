"""
EAV (Entity-Attribute-Value) Pattern Models
Allows flexible attributes for different model types
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Enum as SQLEnum, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum
from app.db.base import Base


class AttributeDataType(str, enum.Enum):
    """Data type for attribute values"""
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    URL = "URL"
    EMAIL = "EMAIL"


class ModelAttribute(Base):
    """
    Attribute Definition (EAV - Attribute)
    Defines what attributes are available for models
    
    Examples:
    - input_shape: [224, 224, 3]
    - output_classes: 1000
    - accuracy: 0.95
    - inference_time_ms: 50
    - supported_languages: ["en", "es", "fr"]
    """
    __tablename__ = "model_attributes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, unique=True, index=True)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Data Type
    data_type = Column(SQLEnum(AttributeDataType), nullable=False)
    
    # Validation
    is_required = Column(Boolean, default=False)
    validation_rules = Column(JSONB, default=dict)  # Min, max, regex, etc.
    
    # Display
    display_name = Column(String(200), nullable=True)  # User-friendly name
    help_text = Column(Text, nullable=True)
    unit = Column(String(50), nullable=True)  # e.g., "ms", "MB", "%"
    sort_order = Column(Integer, default=0)
    
    # Categorization
    group = Column(String(100), nullable=True)  # Group attributes: "Performance", "Input", "Output"
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    values = relationship("ModelAttributeValue", back_populates="attribute", cascade="all, delete-orphan")
    
    def __repr__(self):
        try:
            return f"<ModelAttribute {self.slug}: {self.name} ({self.data_type})>"
        except:
            return f"<ModelAttribute (detached)>"


class ModelAttributeValue(Base):
    """
    Attribute Value (EAV - Value)
    Stores actual values for model attributes
    
    Only ONE value column is populated based on data_type
    """
    __tablename__ = "model_attribute_values"
    __table_args__ = (
        UniqueConstraint('model_id', 'attribute_id', name='uq_model_attribute'),
    )

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("software_models.id"), nullable=False, index=True)
    attribute_id = Column(Integer, ForeignKey("model_attributes.id"), nullable=False, index=True)
    
    # Value columns (only one populated based on data_type)
    value_string = Column(Text, nullable=True, index=True)
    value_integer = Column(Integer, nullable=True, index=True)
    value_float = Column(Float, nullable=True, index=True)
    value_boolean = Column(Boolean, nullable=True, index=True)
    value_json = Column(JSONB, nullable=True)
    
    # Relationships
    model = relationship("SoftwareModel", back_populates="attribute_values")
    attribute = relationship("ModelAttribute", back_populates="values")
    
    def get_value(self):
        """Get the actual value based on data type"""
        if self.attribute.data_type == AttributeDataType.STRING:
            return self.value_string
        elif self.attribute.data_type == AttributeDataType.INTEGER:
            return self.value_integer
        elif self.attribute.data_type == AttributeDataType.FLOAT:
            return self.value_float
        elif self.attribute.data_type == AttributeDataType.BOOLEAN:
            return self.value_boolean
        elif self.attribute.data_type in (AttributeDataType.JSON, AttributeDataType.URL, AttributeDataType.EMAIL):
            return self.value_json if self.attribute.data_type == AttributeDataType.JSON else self.value_string
        return None
    
    def set_value(self, value):
        """Set the appropriate value column based on data type"""
        # Clear all value columns first
        self.value_string = None
        self.value_integer = None
        self.value_float = None
        self.value_boolean = None
        self.value_json = None
        
        # Set the appropriate column
        if self.attribute.data_type == AttributeDataType.STRING:
            self.value_string = str(value)
        elif self.attribute.data_type == AttributeDataType.INTEGER:
            self.value_integer = int(value)
        elif self.attribute.data_type == AttributeDataType.FLOAT:
            self.value_float = float(value)
        elif self.attribute.data_type == AttributeDataType.BOOLEAN:
            self.value_boolean = bool(value)
        elif self.attribute.data_type == AttributeDataType.JSON:
            self.value_json = value  # Should be dict or list
        elif self.attribute.data_type in (AttributeDataType.URL, AttributeDataType.EMAIL):
            self.value_string = str(value)
    
    def __repr__(self):
        try:
            value = self.get_value()
            return f"<ModelAttributeValue Model:{self.model_id} {self.attribute.slug}={value}>"
        except:
            return f"<ModelAttributeValue (detached)>"
