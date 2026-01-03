"""
Upload endpoints for file upload and processing.

This module handles file uploads to the Bronze layer and queues
background processing jobs for document classification and indexing.
"""

import asyncio
import logging
import os
import uuid
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from cortex.jobs.manager import get_job_manager
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """
    Smart Routing Upload Endpoint with MinIO Data Lake.

    Flow:
    1. Stream upload to MinIO Bronze (landing zone)
    2. Return immediately with job_id
    3. Background processing: Extract text, classify, copy to Silver, index in ChromaDB

    Args:
        file: Uploaded file from request.

    Returns:
        JSON with job_id, document_id, bronze_key for tracking.
        Use GET /api/upload/jobs/{job_id} to check processing status.

    Raises:
        HTTPException: If filename is missing or upload fails.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")

        minio = get_minio_service()

        # Determine length without reading into memory
        try:
            file.file.seek(0, os.SEEK_END)
            length = file.file.tell()
            file.file.seek(0)
        except Exception:
            # Fallback: read into memory (should be rare)
            content = await file.read()
            length = len(content)
            file.file = BytesIO(content)  # type: ignore
            file.file.seek(0)

        document_id = uuid.uuid4().hex
        bronze_key = minio.upload_stream_to_bronze(
            data_stream=file.file,
            length=length,
            filename=file.filename,
            document_id=document_id,
            content_type=file.content_type,
        )

        logger.info(f"Received file: {file.filename}, uploaded to Bronze: {bronze_key}")

        # Queue background job for processing
        job_manager = get_job_manager()
        job_id = uuid.uuid4().hex
        job_manager.create_job(job_id, file.filename, document_id, bronze_key)

        loop = asyncio.get_running_loop()
        job_manager.submit_job(job_id, bronze_key, file.filename, document_id, loop)

        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": "queued",
                "document_id": document_id,
                "bronze_key": bronze_key,
                "filename": file.filename,
                "message": (
                    "Upload received and stored in Bronze. "
                    "Processing will continue in background."
                ),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart routing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_upload_jobs(limit: int = 100) -> dict:
    """
    List recent upload background jobs.

    Args:
        limit: Maximum number of jobs to return.

    Returns:
        Dict with list of recent jobs (in-memory, best-effort).
    """
    job_manager = get_job_manager()
    return {"jobs": job_manager.list_jobs(limit=limit)}


@router.get("/jobs/{job_id}")
async def get_upload_job(job_id: str) -> dict:
    """
    Get status/result for a background upload job.

    Args:
        job_id: The job identifier.

    Returns:
        Job status and result data.

    Raises:
        HTTPException: If job not found.
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
