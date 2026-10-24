"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "nexus-workbench"}