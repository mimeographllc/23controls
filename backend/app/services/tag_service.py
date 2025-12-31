"""
Tag Service
Business logic for tag operations
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models import Tag
from app.schemas.catalog import TagCreate, TagUpdate
from fastapi import HTTPException, status


class TagService:
    """Service for tag operations"""
    
    @staticmethod
    async def create_tag(
        db: AsyncSession,
        tag_data: TagCreate
    ) -> Tag:
        """Create a new tag"""
        # Generate slug
        slug = tag_data.name.lower().replace(" ", "-")
        
        # Check if slug exists
        result = await db.execute(
            select(Tag).where(Tag.slug == slug)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists"
            )
        
        # Create tag
        tag = Tag(
            name=tag_data.name,
            slug=slug,
            description=tag_data.description,
            color=tag_data.color
        )
        
        db.add(tag)
        await db.commit()
        await db.refresh(tag)
        
        return tag
    
    @staticmethod
    async def get_tag_by_id(
        db: AsyncSession,
        tag_id: int
    ) -> Optional[Tag]:
        """Get tag by ID"""
        result = await db.execute(
            select(Tag).where(Tag.id == tag_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_tag_by_slug(
        db: AsyncSession,
        slug: str
    ) -> Optional[Tag]:
        """Get tag by slug"""
        result = await db.execute(
            select(Tag).where(Tag.slug == slug)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_tags(
        db: AsyncSession,
        sort_by_usage: bool = False
    ) -> List[Tag]:
        """List all tags"""
        query = select(Tag)
        
        if sort_by_usage:
            query = query.order_by(desc(Tag.usage_count))
        else:
            query = query.order_by(Tag.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_tag(
        db: AsyncSession,
        tag_id: int,
        tag_data: TagUpdate
    ) -> Tag:
        """Update a tag"""
        tag = await TagService.get_tag_by_id(db, tag_id)
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        # Update fields
        update_data = tag_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "name":
                # Update slug if name changes
                tag.slug = value.lower().replace(" ", "-")
            setattr(tag, field, value)
        
        await db.commit()
        await db.refresh(tag)
        
        return tag
    
    @staticmethod
    async def delete_tag(
        db: AsyncSession,
        tag_id: int
    ) -> bool:
        """Delete a tag"""
        tag = await TagService.get_tag_by_id(db, tag_id)
        
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )
        
        # Check if tag is in use
        if tag.usage_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete tag that is in use"
            )
        
        await db.delete(tag)
        await db.commit()
        
        return True
