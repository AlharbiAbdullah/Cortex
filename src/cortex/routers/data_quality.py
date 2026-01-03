"""
Data Quality API endpoints.

This module provides endpoints for data quality assessment,
profiling, and anomaly detection.
"""

import io
import json
import logging
import os
import tempfile
from typing import Any

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from cortex.services.data_quality_service import (
    DataQualityReport,
    get_data_quality_service,
)
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quality", tags=["data-quality"])


class AssessGoldRequest(BaseModel):
    """Request model for Gold layer assessment."""

    gold_key: str = Field(..., description="Gold layer document key")
    dataset_name: str | None = Field(
        default=None,
        description="Optional dataset name for report",
    )


class QuickCheckRequest(BaseModel):
    """Request model for quick quality check."""

    data: list[dict[str, Any]] = Field(..., description="Data as list of records")


@router.post("/assess", response_model=DataQualityReport)
async def assess_uploaded_file(
    file: UploadFile = File(...),
    dataset_name: str | None = None,
) -> DataQualityReport:
    """
    Assess data quality of an uploaded file.

    Supports CSV, Excel, and JSON files.

    Args:
        file: Uploaded file (CSV, Excel, or JSON).
        dataset_name: Optional name for the dataset.

    Returns:
        DataQualityReport with complete quality assessment.

    Raises:
        HTTPException: If file format unsupported or assessment fails.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = os.path.splitext(file.filename)[1].lower()
    name = dataset_name or file.filename

    try:
        content = await file.read()

        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(content))
        elif ext == ".json":
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise HTTPException(
                    status_code=400,
                    detail="JSON must be array or object",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {ext}. Use CSV, Excel, or JSON.",
            )

        service = get_data_quality_service()
        report = await service.assess(df, dataset_name=name)
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data quality assessment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assess/gold", response_model=DataQualityReport)
async def assess_gold_document(request: AssessGoldRequest) -> DataQualityReport:
    """
    Assess data quality of a Gold layer document.

    Args:
        request: AssessGoldRequest with gold_key.

    Returns:
        DataQualityReport with complete quality assessment.

    Raises:
        HTTPException: If document not found or assessment fails.
    """
    try:
        minio = get_minio_service()

        # Get Gold document
        data = minio.get_from_gold(request.gold_key)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"Gold document not found: {request.gold_key}",
            )

        # Convert to DataFrame
        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                df = pd.DataFrame(data["data"])
            else:
                df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            raise HTTPException(
                status_code=400,
                detail="Gold document has unexpected format",
            )

        name = request.dataset_name or request.gold_key

        service = get_data_quality_service()
        report = await service.assess(df, dataset_name=name)
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gold assessment failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-check")
async def quick_check(request: QuickCheckRequest) -> dict[str, Any]:
    """
    Perform quick quality check on provided data.

    Returns basic quality metrics without full profiling.

    Args:
        request: QuickCheckRequest with data records.

    Returns:
        Dict with basic quality metrics.

    Raises:
        HTTPException: If check fails.
    """
    if not request.data:
        raise HTTPException(status_code=400, detail="Data cannot be empty")

    try:
        df = pd.DataFrame(request.data)
        service = get_data_quality_service()
        result = service.quick_check(df)
        return result

    except Exception as e:
        logger.error(f"Quick check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-check/file")
async def quick_check_file(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Perform quick quality check on an uploaded file.

    Args:
        file: Uploaded file (CSV, Excel, or JSON).

    Returns:
        Dict with basic quality metrics.

    Raises:
        HTTPException: If file format unsupported or check fails.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = os.path.splitext(file.filename)[1].lower()

    try:
        content = await file.read()

        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(content))
        elif ext == ".json":
            data = json.loads(content.decode("utf-8"))
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {ext}",
            )

        service = get_data_quality_service()
        result = service.quick_check(df)
        result["filename"] = file.filename
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick check file failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{silver_key:path}")
async def get_quality_report(silver_key: str) -> dict[str, Any]:
    """
    Get cached quality report for a Silver document (if available).

    Args:
        silver_key: Silver layer document key.

    Returns:
        Cached quality report or message.

    Raises:
        HTTPException: If document not found.
    """
    try:
        minio = get_minio_service()

        doc = minio.get_document(silver_key)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check for cached quality report in metadata
        cached_report = doc.get("quality_report")
        if cached_report:
            return {
                "silver_key": silver_key,
                "cached": True,
                "report": cached_report,
            }

        return {
            "silver_key": silver_key,
            "cached": False,
            "message": "No cached report. Use POST /api/quality/assess to generate.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get quality report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/column")
async def profile_column(
    file: UploadFile = File(...),
    column: str = None,
) -> dict[str, Any]:
    """
    Get detailed profile for a specific column.

    Args:
        file: Uploaded file.
        column: Column name to profile (if None, profiles all columns).

    Returns:
        Column profile(s).

    Raises:
        HTTPException: If file or column invalid.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    ext = os.path.splitext(file.filename)[1].lower()

    try:
        content = await file.read()

        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(content))
        elif ext == ".json":
            data = json.loads(content.decode("utf-8"))
            df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([data])
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {ext}",
            )

        if column and column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Column not found: {column}. Available: {list(df.columns)}",
            )

        service = get_data_quality_service()
        report = await service.assess(df, dataset_name=file.filename)

        if column:
            profile = next(
                (p for p in report.column_profiles if p.column_name == column),
                None,
            )
            if profile:
                return {"column": column, "profile": profile.model_dump()}
            raise HTTPException(status_code=404, detail="Column profile not found")

        return {
            "filename": file.filename,
            "columns": [p.model_dump() for p in report.column_profiles],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Column profiling failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thresholds")
async def get_quality_thresholds() -> dict[str, Any]:
    """
    Get current quality threshold settings.

    Returns:
        Dict with threshold values.
    """
    from cortex.services.data_quality_service import get_data_quality_settings

    settings = get_data_quality_settings()
    return {
        "completeness_threshold": settings.completeness_threshold,
        "uniqueness_threshold": settings.uniqueness_threshold,
        "consistency_threshold": settings.consistency_threshold,
        "anomaly_std_threshold": settings.anomaly_std_threshold,
        "max_sample_rows": settings.max_sample_rows,
    }
