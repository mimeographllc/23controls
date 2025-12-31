"""
Model API Endpoints
RESTful endpoints for software model CRUD operations
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.api.v1.dependencies.auth import get_current_user, get_current_active_user, get_optional_current_user
from app.models import User
from app.schemas.catalog import (
    ModelCreate, ModelUpdate, ModelResponse, ModelDetail, ModelListResponse,
    ModelListItem, ModelFilter, ModelSort
)
from app.services.model_service import ModelService
from fastapi import HTTPException


router = APIRouter()


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new software model
    
    Requires authentication. Model is initially private.
    """
    model = await ModelService.create_model(
        db=db,
        model_data=model_data,
        creator_id=current_user.id,
        organization_id=current_user.organization_id
    )
    
    return model


@router.get("", response_model=ModelListResponse)
async def list_models(
    # Pagination
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    
    # Filtering
    category_id: Optional[int] = Query(None),
    model_type: Optional[str] = Query(None),
    framework: Optional[str] = Query(None),
    license_type: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    is_verified: Optional[bool] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    search: Optional[str] = Query(None),
    tags: Optional[List[int]] = Query(None),
    
    # Sorting
    sort_by: ModelSort = Query(ModelSort.POPULAR),
    
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List models with filtering, sorting, and pagination
    
    Public endpoint - shows public models to unauthenticated users.
    Authenticated users also see their own private models.
    """
    # Build filters
    filters = ModelFilter(
        category_id=category_id,
        model_type=model_type,
        framework=framework,
        license_type=license_type,
        is_featured=is_featured,
        is_verified=is_verified,
        min_rating=min_rating,
        search=search,
        tags=tags
    )
    
    # Get models
    models, total = await ModelService.list_models(
        db=db,
        filters=filters,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        user_id=current_user.id if current_user else None
    )
    
    # Convert to list items
    items = [
        ModelListItem(
            id=model.id,
            slug=model.slug,
            name=model.name,
            description=model.description,
            model_type=model.model_type,
            framework=model.framework,
            category_id=model.category_id,
            download_count=model.download_count,
            rating_avg=model.rating_avg,
            rating_count=model.rating_count,
            is_featured=model.is_featured,
            is_verified=model.is_verified,
            published_at=model.published_at,
            thumbnail_url=None  # TODO: Get from media
        )
        for model in models
    ]
    
    # Calculate pagination
    total_pages = (total + page_size - 1) // page_size
    
    return ModelListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/featured", response_model=List[ModelListItem])
async def get_featured_models(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get featured models"""
    filters = ModelFilter(is_featured=True)
    
    models, _ = await ModelService.list_models(
        db=db,
        filters=filters,
        sort_by=ModelSort.POPULAR,
        page=1,
        page_size=limit
    )
    
    return [
        ModelListItem(
            id=model.id,
            slug=model.slug,
            name=model.name,
            description=model.description,
            model_type=model.model_type,
            framework=model.framework,
            category_id=model.category_id,
            download_count=model.download_count,
            rating_avg=model.rating_avg,
            rating_count=model.rating_count,
            is_featured=model.is_featured,
            is_verified=model.is_verified,
            published_at=model.published_at,
            thumbnail_url=None
        )
        for model in models
    ]


@router.get("/{slug}", response_model=ModelDetail)
async def get_model(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get model details by slug
    
    Increments view count.
    """
    model = await ModelService.get_model_by_slug(db, slug, load_details=True)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Check if model is public
    if not model.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # Build response with all details
    from app.services.eav_service import EAVService
    attributes = await EAVService.get_model_attributes(db, model.id)
    
    # Convert attributes to dict
    attributes_dict = {attr.attribute_slug: attr.value for attr in attributes}
    
    return ModelDetail(
        id=model.id,
        slug=model.slug,
        name=model.name,
        description=model.description,
        long_description=model.long_description,
        creator_user_id=model.creator_user_id,
        organization_id=model.organization_id,
        category_id=model.category_id,
        model_type=model.model_type,
        framework=model.framework,
        license_type=model.license_type,
        repository_url=model.repository_url,
        documentation_url=model.documentation_url,
        demo_url=model.demo_url,
        version_current=model.version_current,
        download_count=model.download_count,
        view_count=model.view_count,
        rating_avg=model.rating_avg,
        rating_count=model.rating_count,
        is_public=model.is_public,
        is_featured=model.is_featured,
        is_verified=model.is_verified,
        published_at=model.published_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
        metadata=model.meta_data,
        tags=[],  # TODO: Load tags
        category=None,  # TODO: Load category
        attributes=attributes_dict,
        versions=[],  # TODO: Load versions
        media=[],  # TODO: Load media
        pricing_tiers=[]  # TODO: Load pricing
    )


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    model_data: ModelUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a model
    
    Only the model creator can update it.
    """
    model = await ModelService.update_model(
        db=db,
        model_id=model_id,
        model_data=model_data,
        user_id=current_user.id
    )
    
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a model
    
    Only the model creator can delete it.
    """
    await ModelService.delete_model(
        db=db,
        model_id=model_id,
        user_id=current_user.id
    )
    
    return None


@router.post("/{model_id}/publish", response_model=ModelResponse)
async def publish_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish a model (make it public)
    
    Only the model creator can publish it.
    """
    model = await ModelService.publish_model(
        db=db,
        model_id=model_id,
        user_id=current_user.id
    )
    
    return model


@router.post("/{model_id}/unpublish", response_model=ModelResponse)
async def unpublish_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unpublish a model (make it private)
    
    Only the model creator can unpublish it.
    """
    model = await ModelService.unpublish_model(
        db=db,
        model_id=model_id,
        user_id=current_user.id
    )
    
    return model


@router.get("/{model_id}/attributes")
async def get_model_attributes(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all attributes for a model"""
    from app.services.eav_service import EAVService
    
    attributes = await EAVService.get_model_attributes(db, model_id)
    
    return {"model_id": model_id, "attributes": attributes}


@router.put("/{model_id}/attributes")
async def set_model_attributes(
    model_id: int,
    attributes: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Set attributes for a model"""
    from app.services.eav_service import EAVService
    
    # Verify user owns the model
    model = await ModelService.get_model_by_id(db, model_id, load_details=False)
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    if model.creator_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Set attributes
    await EAVService.set_model_attributes(db, model_id, attributes)
    
    # Return updated attributes
    updated_attributes = await EAVService.get_model_attributes(db, model_id)
    
    return {"model_id": model_id, "attributes": updated_attributes}
