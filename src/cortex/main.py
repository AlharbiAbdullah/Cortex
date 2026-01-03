"""
FastAPI Backend for Cortex Document Intelligence Platform.

Main application entry point with modular router architecture.
"""

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from cortex.routers import (
    chat_router,
    comparison_router,
    data_quality_router,
    documents_router,
    health_router,
    reports_router,
    summarization_router,
    upload_router,
)
from cortex.startup import seed_contexts_on_startup

logger = logging.getLogger(__name__)


class AppSettings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Cortex"
    app_version: str = "1.0.0"
    debug: bool = False
    cors_origins: str = "http://localhost:3000,http://localhost:8080"


@lru_cache()
def get_app_settings() -> AppSettings:
    """Get cached application settings instance."""
    return AppSettings()


# Cache for SmartRouterGraph categories (avoid recreating on every request)
_cached_categories: dict[str, Any] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Handles:
    - Database context seeding on startup
    - Category pre-caching for Smart Router
    - Graceful shutdown logging
    """
    global _cached_categories

    # Startup
    logger.info("Starting Cortex Document Intelligence Platform...")
    await seed_contexts_on_startup()

    # Pre-cache categories
    try:
        from cortex.agents.smart_router import SmartRouterGraph

        smart_router = SmartRouterGraph()
        _cached_categories = smart_router.get_available_categories()
        logger.info(f"Cached {len(_cached_categories)} routing categories")
    except Exception as e:
        logger.warning(f"Could not pre-cache categories: {e}")
        _cached_categories = {}

    yield

    # Shutdown
    logger.info("Shutting down Cortex Document Intelligence Platform...")


# ==================== Application Setup ====================
settings = get_app_settings()

app = FastAPI(
    title="Cortex API",
    description=(
        "Cortex Document Intelligence Platform - "
        "RAG, Smart Routing, and Agentic Workflows"
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
# Note: allow_credentials=True requires specific origins, not wildcard
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Include Routers ====================
# Core routers
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(health_router)

# Phase 2 routers
app.include_router(summarization_router)
app.include_router(comparison_router)
app.include_router(reports_router)
app.include_router(data_quality_router)


# ==================== Root Endpoint ====================
@app.get("/")
async def root() -> dict:
    """
    Root endpoint with API information.

    Returns:
        Dict with API info, version, available services, and categories.
    """
    return {
        "message": "Cortex Document Intelligence Platform",
        "version": settings.app_version,
        "services": [
            # Core services
            "upload (smart-routing)",
            "qa/chat",
            "documents",
            "health",
            # Phase 2 services
            "summarization",
            "comparison",
            "reports",
            "data-quality",
        ],
        "routing_categories": (
            list(_cached_categories.keys()) if _cached_categories else []
        ),
        "status": "running",
    }


# ==================== Main Entry Point ====================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
