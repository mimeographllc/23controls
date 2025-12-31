"""
Category Service
Business logic for category operations
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Category
from app.schemas.catalog import CategoryCreate, CategoryUpdate, CategoryTree
from fastapi import HTTPException, status


class CategoryService:
    """Service for category operations"""
    
    @staticmethod
    async def create_category(
        db: AsyncSession,
        category_data: CategoryCreate
    ) -> Category:
        """Create a new category"""
        # Generate slug
        slug = category_data.name.lower().replace(" ", "-")
        
        # Check if slug exists
        result = await db.execute(
            select(Category).where(Category.slug == slug)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )
        
        # Verify parent exists if provided
        if category_data.parent_id:
            result = await db.execute(
                select(Category).where(Category.id == category_data.parent_id)
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found"
                )
        
        # Create category
        category = Category(
            name=category_data.name,
            slug=slug,
            description=category_data.description,
            parent_id=category_data.parent_id,
            icon_url=category_data.icon_url,
            color=category_data.color,
            sort_order=category_data.sort_order,
            is_active=category_data.is_active
        )
        
        db.add(category)
        await db.commit()
        await db.refresh(category)
        
        return category
    
    @staticmethod
    async def get_category_by_id(
        db: AsyncSession,
        category_id: int
    ) -> Optional[Category]:
        """Get category by ID"""
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_category_by_slug(
        db: AsyncSession,
        slug: str
    ) -> Optional[Category]:
        """Get category by slug"""
        result = await db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_categories(
        db: AsyncSession,
        parent_id: Optional[int] = None,
        active_only: bool = True
    ) -> List[Category]:
        """List categories"""
        query = select(Category)
        
        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        else:
            # Only root categories (no parent)
            query = query.where(Category.parent_id.is_(None))
        
        if active_only:
            query = query.where(Category.is_active == True)
        
        query = query.order_by(Category.sort_order, Category.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_category_tree(
        db: AsyncSession,
        active_only: bool = True
    ) -> List[CategoryTree]:
        """
        Get full category tree
        
        Returns list of root categories with nested children
        """
        # Get all categories
        query = select(Category)
        if active_only:
            query = query.where(Category.is_active == True)
        query = query.order_by(Category.sort_order, Category.name)
        
        result = await db.execute(query)
        all_categories = result.scalars().all()
        
        # Build tree structure
        category_map = {cat.id: cat for cat in all_categories}
        roots = []
        
        for category in all_categories:
            if category.parent_id is None:
                roots.append(category)
        
        def build_tree(cat: Category) -> CategoryTree:
            """Recursively build tree"""
            children = [
                build_tree(category_map[child.id])
                for child in all_categories
                if child.parent_id == cat.id
            ]
            
            return CategoryTree(
                id=cat.id,
                slug=cat.slug,
                name=cat.name,
                description=cat.description,
                icon_url=cat.icon_url,
                color=cat.color,
                sort_order=cat.sort_order,
                is_active=cat.is_active,
                parent_id=cat.parent_id,
                metadata=cat.metadata,
                children=children
            )
        
        return [build_tree(root) for root in roots]
    
    @staticmethod
    async def update_category(
        db: AsyncSession,
        category_id: int,
        category_data: CategoryUpdate
    ) -> Category:
        """Update a category"""
        category = await CategoryService.get_category_by_id(db, category_id)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Update fields
        update_data = category_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        await db.commit()
        await db.refresh(category)
        
        return category
    
    @staticmethod
    async def delete_category(
        db: AsyncSession,
        category_id: int
    ) -> bool:
        """Delete a category"""
        category = await CategoryService.get_category_by_id(db, category_id)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if category has children
        result = await db.execute(
            select(Category).where(Category.parent_id == category_id)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with children"
            )
        
        # Check if category has models
        from app.models import SoftwareModel
        result = await db.execute(
            select(SoftwareModel).where(SoftwareModel.category_id == category_id)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category with models"
            )
        
        await db.delete(category)
        await db.commit()
        
        return True
