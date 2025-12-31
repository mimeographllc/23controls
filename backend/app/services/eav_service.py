"""
EAV Service  
Business logic for Entity-Attribute-Value operations
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import ModelAttribute, ModelAttributeValue, SoftwareModel
from app.models.eav import AttributeDataType
from app.schemas.eav import AttributeCreate, AttributeUpdate, AttributeValueResponse
from fastapi import HTTPException, status


class EAVService:
    """Service for EAV operations"""
    
    @staticmethod
    async def create_attribute(
        db: AsyncSession,
        attribute_data: AttributeCreate
    ) -> ModelAttribute:
        """Create a new attribute definition"""
        # Generate slug
        slug = attribute_data.name.lower().replace(" ", "_")
        
        # Check if slug exists
        result = await db.execute(
            select(ModelAttribute).where(ModelAttribute.slug == slug)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attribute with this name already exists"
            )
        
        # Create attribute
        attribute = ModelAttribute(
            name=attribute_data.name,
            slug=slug,
            description=attribute_data.description,
            data_type=attribute_data.data_type,
            is_required=attribute_data.is_required,
            validation_rules=attribute_data.validation_rules,
            display_name=attribute_data.display_name,
            help_text=attribute_data.help_text,
            unit=attribute_data.unit,
            group=attribute_data.group,
            sort_order=attribute_data.sort_order
        )
        
        db.add(attribute)
        await db.commit()
        await db.refresh(attribute)
        
        return attribute
    
    @staticmethod
    async def get_attribute_by_slug(
        db: AsyncSession,
        slug: str
    ) -> Optional[ModelAttribute]:
        """Get attribute by slug"""
        result = await db.execute(
            select(ModelAttribute).where(ModelAttribute.slug == slug)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_attributes(
        db: AsyncSession,
        active_only: bool = True,
        group: Optional[str] = None
    ) -> List[ModelAttribute]:
        """List all attribute definitions"""
        query = select(ModelAttribute)
        
        if active_only:
            query = query.where(ModelAttribute.is_active == True)
        
        if group:
            query = query.where(ModelAttribute.group == group)
        
        query = query.order_by(ModelAttribute.sort_order, ModelAttribute.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def set_model_attributes(
        db: AsyncSession,
        model_id: int,
        attributes: Dict[str, Any]
    ) -> List[ModelAttributeValue]:
        """
        Set multiple attribute values for a model
        
        Args:
            db: Database session
            model_id: Model ID
            attributes: Dict of attribute_slug → value
            
        Returns:
            List of created/updated attribute values
        """
        # Verify model exists
        result = await db.execute(
            select(SoftwareModel).where(SoftwareModel.id == model_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        values = []
        
        for attr_slug, value in attributes.items():
            # Get attribute definition
            attribute = await EAVService.get_attribute_by_slug(db, attr_slug)
            
            if not attribute:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attribute '{attr_slug}' not found"
                )
            
            # Check if value already exists
            result = await db.execute(
                select(ModelAttributeValue).where(
                    ModelAttributeValue.model_id == model_id,
                    ModelAttributeValue.attribute_id == attribute.id
                )
            )
            attr_value = result.scalar_one_or_none()
            
            if not attr_value:
                # Create new value
                attr_value = ModelAttributeValue(
                    model_id=model_id,
                    attribute_id=attribute.id
                )
                db.add(attr_value)
            
            # Set value based on data type
            try:
                attr_value.set_value(value)
                values.append(attr_value)
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid value for attribute '{attr_slug}': {str(e)}"
                )
        
        await db.commit()
        
        # Reload with relationships
        for attr_value in values:
            await db.refresh(attr_value)
        
        return values
    
    @staticmethod
    async def get_model_attributes(
        db: AsyncSession,
        model_id: int
    ) -> List[AttributeValueResponse]:
        """
        Get all attribute values for a model
        
        Returns list of AttributeValueResponse objects
        """
        result = await db.execute(
            select(ModelAttributeValue)
            .where(ModelAttributeValue.model_id == model_id)
            .options(selectinload(ModelAttributeValue.attribute))
        )
        values = result.scalars().all()
        
        return [
            AttributeValueResponse(
                attribute_id=val.attribute_id,
                attribute_slug=val.attribute.slug,
                attribute_name=val.attribute.name,
                data_type=val.attribute.data_type,
                value=val.get_value(),
                unit=val.attribute.unit
            )
            for val in values
        ]
    
    @staticmethod
    async def delete_model_attribute(
        db: AsyncSession,
        model_id: int,
        attribute_slug: str
    ) -> bool:
        """Delete a specific attribute value from a model"""
        # Get attribute
        attribute = await EAVService.get_attribute_by_slug(db, attribute_slug)
        
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute not found"
            )
        
        # Get value
        result = await db.execute(
            select(ModelAttributeValue).where(
                ModelAttributeValue.model_id == model_id,
                ModelAttributeValue.attribute_id == attribute.id
            )
        )
        attr_value = result.scalar_one_or_none()
        
        if not attr_value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute value not found"
            )
        
        await db.delete(attr_value)
        await db.commit()
        
        return True
    
    @staticmethod
    def validate_attribute_value(
        attribute: ModelAttribute,
        value: Any
    ) -> bool:
        """
        Validate a value against attribute validation rules
        
        Returns True if valid, raises HTTPException if invalid
        """
        rules = attribute.validation_rules or {}
        
        # Type checking
        if attribute.data_type == AttributeDataType.INTEGER:
            if not isinstance(value, int):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be an integer"
                )
            if "min" in rules and value < rules["min"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be >= {rules['min']}"
                )
            if "max" in rules and value > rules["max"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be <= {rules['max']}"
                )
        
        elif attribute.data_type == AttributeDataType.FLOAT:
            if not isinstance(value, (int, float)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be a number"
                )
            if "min" in rules and value < rules["min"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be >= {rules['min']}"
                )
            if "max" in rules and value > rules["max"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be <= {rules['max']}"
                )
        
        elif attribute.data_type == AttributeDataType.STRING:
            if not isinstance(value, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be a string"
                )
            if "minLength" in rules and len(value) < rules["minLength"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be at least {rules['minLength']} characters"
                )
            if "maxLength" in rules and len(value) > rules["maxLength"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be at most {rules['maxLength']} characters"
                )
        
        elif attribute.data_type == AttributeDataType.BOOLEAN:
            if not isinstance(value, bool):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be a boolean"
                )
        
        elif attribute.data_type == AttributeDataType.JSON:
            if not isinstance(value, (dict, list)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Value must be a JSON object or array"
                )
        
        return True
