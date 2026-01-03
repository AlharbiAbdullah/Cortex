"""
FastAPI routers module.

This module exports all API routers for the Cortex application.
"""

from cortex.routers.chat import router as chat_router
from cortex.routers.comparison import router as comparison_router
from cortex.routers.data_quality import router as data_quality_router
from cortex.routers.documents import router as documents_router
from cortex.routers.health import router as health_router
from cortex.routers.reports import router as reports_router
from cortex.routers.summarization import router as summarization_router
from cortex.routers.upload import router as upload_router

__all__ = [
    # Core routers
    "chat_router",
    "documents_router",
    "health_router",
    "upload_router",
    # Phase 2 routers
    "summarization_router",
    "comparison_router",
    "reports_router",
    "data_quality_router",
]
