"""
Model Service
Business logic for software model operations
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime

from app.models import (
    SoftwareModel, Category, Tag, ModelTag, User, Organization,
    ModelAttributeValue, ModelAttribute, ModelVersion, ModelMedia
)
from app.models.catalog import ModelType, Framework, LicenseType
from app.schemas.catalog import (
    ModelCreate, ModelUpdate, ModelFilter, ModelSort, 
    ModelListItem, ModelDetail, ModelResponse
)
from fastapi import HTTPException, status


class ModelService:
    """Service for software model operations"""
    
    @staticmethod
    async def create_model(
        db: AsyncSession,
        model_data: ModelCreate,
        creator_id: int,
        organization_id: int
    ) -> SoftwareModel:
        """
        Create a new software model
        
        Args:
            db: Database session
            model_data: Model creation data
            creator_id: ID of the creating user
            organization_id: ID of the user's organization
            
        Returns:
            Created SoftwareModel
        """
        # Generate slug from name
        slug = model_data.name.lower().replace(" ", "-").replace("_", "-")
        
        # Check if slug exists
        result = await db.execute(
            select(SoftwareModel).where(SoftwareModel.slug == slug)
        )
        if result.scalar_one_or_none():
            # Append random suffix if slug exists
            import uuid
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
        # Verify category exists if provided
        if model_data.category_id:
            result = await db.execute(
                select(Category).where(Category.id == model_data.category_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found"
                )
        
        # Create model
        model = SoftwareModel(
            name=model_data.name,
            slug=slug,
            description=model_data.description,
            long_description=model_data.long_description,
            creator_user_id=creator_id,
            organization_id=organization_id,
            category_id=model_data.category_id,
            model_type=model_data.model_type,
            framework=model_data.framework,
            license_type=model_data.license_type,
            repository_url=model_data.repository_url,
            documentation_url=model_data.documentation_url,
            demo_url=model_data.demo_url,
            is_public=False,  # Default to private
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(model)
        await db.flush()  # Get the ID
        
        # Add tags
        if model_data.tags:
            for tag_id in model_data.tags:
                # Verify tag exists
                result = await db.execute(
                    select(Tag).where(Tag.id == tag_id)
                )
                tag = result.scalar_one_or_none()
                if tag:
                    model_tag = ModelTag(model_id=model.id, tag_id=tag_id)
                    db.add(model_tag)
                    
                    # Increment tag usage count
                    tag.usage_count += 1
        
        # Set attributes (EAV)
        if model_data.attributes:
            from app.services.eav_service import EAVService
            await EAVService.set_model_attributes(
                db, model.id, model_data.attributes
            )
        
        await db.commit()
        
        # Reload with relationships
        return await ModelService.get_model_by_id(db, model.id)
    
    @staticmethod
    async def get_model_by_id(
        db: AsyncSession,
        model_id: int,
        load_details: bool = True
    ) -> Optional[SoftwareModel]:
        """
        Get model by ID with eager loading
        
        Args:
            db: Database session
            model_id: Model ID
            load_details: Whether to load all relationships
            
        Returns:
            SoftwareModel or None
        """
        query = select(SoftwareModel).where(SoftwareModel.id == model_id)
        
        if load_details:
            query = query.options(
                selectinload(SoftwareModel.category),
                selectinload(SoftwareModel.model_tags).selectinload(ModelTag.tag),
                selectinload(SoftwareModel.creator),
                selectinload(SoftwareModel.organization),
                selectinload(SoftwareModel.attribute_values).selectinload(ModelAttributeValue.attribute),
                selectinload(SoftwareModel.versions),
                selectinload(SoftwareModel.media),
                selectinload(SoftwareModel.pricing_tiers)
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_model_by_slug(
        db: AsyncSession,
        slug: str,
        load_details: bool = True
    ) -> Optional[SoftwareModel]:
        """Get model by slug"""
        query = select(SoftwareModel).where(SoftwareModel.slug == slug)
        
        if load_details:
            query = query.options(
                selectinload(SoftwareModel.category),
                selectinload(SoftwareModel.model_tags).selectinload(ModelTag.tag),
                selectinload(SoftwareModel.creator),
                selectinload(SoftwareModel.organization),
                selectinload(SoftwareModel.attribute_values).selectinload(ModelAttributeValue.attribute),
                selectinload(SoftwareModel.versions),
                selectinload(SoftwareModel.media),
                selectinload(SoftwareModel.pricing_tiers)
            )
        
        result = await db.execute(query)
        model = result.scalar_one_or_none()
        
        # Increment view count
        if model:
            model.view_count += 1
            await db.commit()
        
        return model
    
    @staticmethod
    async def update_model(
        db: AsyncSession,
        model_id: int,
        model_data: ModelUpdate,
        user_id: int
    ) -> SoftwareModel:
        """
        Update a model
        
        Args:
            db: Database session
            model_id: Model ID
            model_data: Update data
            user_id: User performing the update
            
        Returns:
            Updated model
        """
        model = await ModelService.get_model_by_id(db, model_id, load_details=False)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # Check permissions (user must be creator or admin)
        if model.creator_user_id != user_id:
            # TODO: Check if user has admin permission
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this model"
            )
        
        # Update fields
        update_data = model_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(model, field, value)
        
        model.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return await ModelService.get_model_by_id(db, model_id)
    
    @staticmethod
    async def delete_model(
        db: AsyncSession,
        model_id: int,
        user_id: int
    ) -> bool:
        """Delete a model"""
        model = await ModelService.get_model_by_id(db, model_id, load_details=False)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # Check permissions
        if model.creator_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this model"
            )
        
        await db.delete(model)
        await db.commit()
        
        return True
    
    @staticmethod
    async def list_models(
        db: AsyncSession,
        filters: Optional[ModelFilter] = None,
        sort_by: ModelSort = ModelSort.POPULAR,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[int] = None
    ) -> Tuple[List[SoftwareModel], int]:
        """
        List models with filtering, sorting, and pagination
        
        Args:
            db: Database session
            filters: Filter criteria
            sort_by: Sort option
            page: Page number (1-indexed)
            page_size: Items per page
            user_id: Current user ID (for permission checking)
            
        Returns:
            Tuple of (models list, total count)
        """
        # Base query
        query = select(SoftwareModel)
        count_query = select(func.count(SoftwareModel.id))
        
        # Apply filters
        conditions = []
        
        # Only show public models unless user is authenticated
        if not user_id:
            conditions.append(SoftwareModel.is_public == True)
        else:
            # Show public models + user's own models
            conditions.append(
                or_(
                    SoftwareModel.is_public == True,
                    SoftwareModel.creator_user_id == user_id
                )
            )
        
        if filters:
            if filters.category_id:
                conditions.append(SoftwareModel.category_id == filters.category_id)
            
            if filters.model_type:
                conditions.append(SoftwareModel.model_type == filters.model_type)
            
            if filters.framework:
                conditions.append(SoftwareModel.framework == filters.framework)
            
            if filters.license_type:
                conditions.append(SoftwareModel.license_type == filters.license_type)
            
            if filters.is_featured is not None:
                conditions.append(SoftwareModel.is_featured == filters.is_featured)
            
            if filters.is_verified is not None:
                conditions.append(SoftwareModel.is_verified == filters.is_verified)
            
            if filters.min_rating:
                conditions.append(SoftwareModel.rating_avg >= filters.min_rating)
            
            if filters.search:
                # Simple text search on name and description
                search_term = f"%{filters.search}%"
                conditions.append(
                    or_(
                        SoftwareModel.name.ilike(search_term),
                        SoftwareModel.description.ilike(search_term)
                    )
                )
            
            if filters.tags:
                # Filter by tags (models must have ALL specified tags)
                query = query.join(ModelTag).where(
                    ModelTag.tag_id.in_(filters.tags)
                )
                # Group by and count to ensure ALL tags match
                query = query.group_by(SoftwareModel.id).having(
                    func.count(ModelTag.tag_id) == len(filters.tags)
                )
        
        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Apply sorting
        if sort_by == ModelSort.POPULAR:
            query = query.order_by(desc(SoftwareModel.download_count))
        elif sort_by == ModelSort.RECENT:
            query = query.order_by(desc(SoftwareModel.published_at))
        elif sort_by == ModelSort.RATING:
            query = query.order_by(desc(SoftwareModel.rating_avg))
        elif sort_by == ModelSort.NAME:
            query = query.order_by(asc(SoftwareModel.name))
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Eager load relationships for list view
        query = query.options(
            selectinload(SoftwareModel.category),
            selectinload(SoftwareModel.model_tags).selectinload(ModelTag.tag)
        )
        
        # Execute
        result = await db.execute(query)
        models = result.scalars().unique().all()
        
        return models, total
    
    @staticmethod
    async def publish_model(
        db: AsyncSession,
        model_id: int,
        user_id: int
    ) -> SoftwareModel:
        """Publish a model (make it public)"""
        model = await ModelService.get_model_by_id(db, model_id, load_details=False)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # Check permissions
        if model.creator_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to publish this model"
            )
        
        model.is_public = True
        model.published_at = datetime.utcnow()
        
        await db.commit()
        
        return await ModelService.get_model_by_id(db, model_id)
    
    @staticmethod
    async def unpublish_model(
        db: AsyncSession,
        model_id: int,
        user_id: int
    ) -> SoftwareModel:
        """Unpublish a model (make it private)"""
        model = await ModelService.get_model_by_id(db, model_id, load_details=False)
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model not found"
            )
        
        # Check permissions
        if model.creator_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to unpublish this model"
            )
        
        model.is_public = False
        
        await db.commit()
        
        return await ModelService.get_model_by_id(db, model_id)
    
    @staticmethod
    async def increment_download_count(
        db: AsyncSession,
        model_id: int
    ) -> None:
        """Increment model download count"""
        model = await ModelService.get_model_by_id(db, model_id, load_details=False)
        
        if model:
            model.download_count += 1
            await db.commit()
