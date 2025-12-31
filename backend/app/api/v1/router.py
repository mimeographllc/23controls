"""
API v1 Router
Aggregates all API endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, models, catalog

# Create main API router
api_router = APIRouter()


# Phase 2 - Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Phase 3 - Software Models
api_router.include_router(
    models.router,
    prefix="/models",
    tags=["Models"]
)

# Phase 3 - Categories
api_router.include_router(
    catalog.category_router,
    prefix="/categories",
    tags=["Categories"]
)

# Phase 3 - Tags
api_router.include_router(
    catalog.tag_router,
    prefix="/tags",
    tags=["Tags"]
)


# Health check endpoint
@api_router.get("/health", tags=["Health"])
async def api_health():
    """API health check"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "features": {
            "auth": True,
            "catalog": True,
            "models": True
        }
    }

