"""
Category and Tag API Endpoints
Endpoints for categorization and tagging
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.api.v1.dependencies.auth import get_current_active_user
from app.models import User
from app.schemas.catalog import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTree,
    TagCreate, TagUpdate, TagResponse
)
from app.services.category_service import CategoryService
from app.services.tag_service import TagService


# Category Router
category_router = APIRouter()


@category_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new category
    
    Requires authentication.
    TODO: Add admin permission check
    """
    category = await CategoryService.create_category(db, category_data)
    return category


@category_router.get("/tree", response_model=List[CategoryTree])
async def get_category_tree(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get full category tree
    
    Returns hierarchical structure of all categories.
    """
    tree = await CategoryService.get_category_tree(db, active_only)
    return tree


@category_router.get("", response_model=List[CategoryResponse])
async def list_categories(
    parent_id: Optional[int] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List categories
    
    If parent_id is provided, returns children of that category.
    If parent_id is None, returns root categories.
    """
    categories = await CategoryService.list_categories(db, parent_id, active_only)
    return categories


@category_router.get("/{slug}", response_model=CategoryResponse)
async def get_category(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get category by slug"""
    from fastapi import HTTPException
    
    category = await CategoryService.get_category_by_slug(db, slug)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@category_router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a category
    
    Requires authentication.
    TODO: Add admin permission check
    """
    category = await CategoryService.update_category(db, category_id, category_data)
    return category


@category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a category
    
    Requires authentication.
    TODO: Add admin permission check
    """
    await CategoryService.delete_category(db, category_id)
    return None


# Tag Router
tag_router = APIRouter()


@tag_router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tag
    
    Requires authentication.
    TODO: Add admin permission check
    """
    tag = await TagService.create_tag(db, tag_data)
    return tag


@tag_router.get("", response_model=List[TagResponse])
async def list_tags(
    sort_by_usage: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all tags
    
    If sort_by_usage is True, sorts by usage_count (most used first).
    Otherwise, sorts alphabetically.
    """
    tags = await TagService.list_tags(db, sort_by_usage)
    return tags


@tag_router.get("/{slug}", response_model=TagResponse)
async def get_tag(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get tag by slug"""
    from fastapi import HTTPException
    
    tag = await TagService.get_tag_by_slug(db, slug)
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return tag


@tag_router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a tag
    
    Requires authentication.
    TODO: Add admin permission check
    """
    tag = await TagService.update_tag(db, tag_id, tag_data)
    return tag


@tag_router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a tag
    
    Requires authentication.
    TODO: Add admin permission check
    """
    await TagService.delete_tag(db, tag_id)
    return None
