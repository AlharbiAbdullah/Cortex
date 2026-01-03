"""
Health check endpoints with comprehensive dependency verification.

This module provides health check endpoints for monitoring application
status and dependency connectivity.
"""

import logging
import time
from typing import Any

import httpx
from fastapi import APIRouter, Response

from cortex.database.connection import DatabaseService, get_db_settings
from cortex.services.document_service import DocumentService
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


async def check_database() -> dict[str, Any]:
    """
    Check PostgreSQL database connectivity.

    Returns:
        Dict with status and latency.
    """
    start = time.time()
    try:
        db = DatabaseService()
        if db.SessionLocal:
            session = db.SessionLocal()
            try:
                session.execute("SELECT 1")
                latency = (time.time() - start) * 1000
                return {"status": "healthy", "latency_ms": round(latency, 2)}
            finally:
                session.close()
        return {"status": "unhealthy", "error": "No session available"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_minio() -> dict[str, Any]:
    """
    Check MinIO connectivity.

    Returns:
        Dict with status, latency, and bucket count.
    """
    start = time.time()
    try:
        minio = get_minio_service()
        if minio.client:
            # List buckets as connectivity test
            buckets = list(minio.client.list_buckets())
            latency = (time.time() - start) * 1000
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "buckets": len(buckets),
            }
        return {"status": "unhealthy", "error": "No client available"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_ollama() -> dict[str, Any]:
    """
    Check Ollama LLM service connectivity.

    Returns:
        Dict with status, latency, and available models.
    """
    start = time.time()
    try:
        from cortex.agents.llm import get_llm_settings

        settings = get_llm_settings()
        ollama_url = settings.ollama_url

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                    "models": models[:5],  # Show first 5 models
                }
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_chromadb() -> dict[str, Any]:
    """
    Check ChromaDB vector database connectivity.

    Returns:
        Dict with status, latency, and document count.
    """
    start = time.time()
    try:
        doc_service = DocumentService()
        if doc_service.collection:
            count = doc_service.collection.count()
            latency = (time.time() - start) * 1000
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "documents": count,
            }
        return {"status": "unhealthy", "error": "No collection available"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_neo4j() -> dict[str, Any]:
    """
    Check Neo4j graph database connectivity.

    Returns:
        Dict with status and latency.
    """
    start = time.time()
    try:
        from cortex.services.knowledge_graph_service import get_knowledge_graph_service

        kg_service = get_knowledge_graph_service()
        health = kg_service.health_check()
        latency = (time.time() - start) * 1000
        health["latency_ms"] = round(latency, 2)
        return health
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health")
async def health_basic() -> dict:
    """
    Basic health check - returns quickly.

    Returns:
        Dict with healthy status.
    """
    return {"status": "healthy"}


@router.get("/health/detailed")
async def health_detailed() -> dict:
    """
    Comprehensive health check with all dependency status.

    Checks:
    - PostgreSQL database
    - MinIO object storage
    - Ollama LLM service
    - ChromaDB vector database
    - Neo4j graph database (if available)

    Returns:
        Structured health report with component statuses and latencies.
    """
    components = {}

    # Check all components
    components["database"] = await check_database()
    components["minio"] = await check_minio()
    components["ollama"] = await check_ollama()
    components["chromadb"] = await check_chromadb()
    components["neo4j"] = await check_neo4j()

    # Determine overall status
    all_healthy = all(c.get("status") == "healthy" for c in components.values())

    # Critical services (must be healthy for system to work)
    critical_services = ["database", "minio", "ollama"]
    critical_healthy = all(
        components.get(s, {}).get("status") == "healthy" for s in critical_services
    )

    if all_healthy:
        overall_status = "healthy"
    elif critical_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "components": components,
        "critical_services": critical_services,
    }


@router.get("/health/ready")
async def health_ready() -> dict | Response:
    """
    Readiness probe for Kubernetes/Docker.

    Returns 200 if critical services are available.

    Returns:
        Dict with ready status or 503 response if not ready.
    """
    db_health = await check_database()
    minio_health = await check_minio()

    ready = (
        db_health.get("status") == "healthy"
        and minio_health.get("status") == "healthy"
    )

    if ready:
        return {"ready": True}
    else:
        return Response(
            content='{"ready": false}',
            status_code=503,
            media_type="application/json",
        )


@router.get("/health/live")
async def health_live() -> dict:
    """
    Liveness probe for Kubernetes/Docker.

    Returns 200 if the service is alive.

    Returns:
        Dict with alive status.
    """
    return {"alive": True}
