"""Nexus Workbench - FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, models, chat, cache


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Nexus Workbench",
        description="Run frontier MoE models on hardware you already own — pure C, zero deps, experts streamed from disk.",
        version="1.0.0",
    )

    # CORS for frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(cache.router, prefix="/api/v1/cache", tags=["cache"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
