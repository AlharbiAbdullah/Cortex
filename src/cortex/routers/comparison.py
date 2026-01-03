"""
Document Comparison API endpoints.

This module provides endpoints for comparing documents including
semantic similarity, text diff, and change tracking.
"""

import logging
import os
import tempfile
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from cortex.services.comparison_service import (
    ComparisonResult,
    get_comparison_service,
)
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compare", tags=["comparison"])


class CompareTextsRequest(BaseModel):
    """Request model for text comparison."""

    text1: str = Field(..., min_length=10, description="Original/baseline text")
    text2: str = Field(..., min_length=10, description="Modified/new text")
    generate_summary: bool = Field(
        default=True,
        description="Generate LLM summary of differences",
    )


class CompareDocumentsRequest(BaseModel):
    """Request model for document comparison."""

    silver_key1: str = Field(..., description="First document silver key")
    silver_key2: str = Field(..., description="Second document silver key")
    generate_summary: bool = Field(
        default=True,
        description="Generate LLM summary of differences",
    )


class QuickDiffRequest(BaseModel):
    """Request model for quick diff."""

    text1: str = Field(..., min_length=10, description="Original text")
    text2: str = Field(..., min_length=10, description="Modified text")


@router.post("", response_model=ComparisonResult)
async def compare_texts(request: CompareTextsRequest) -> ComparisonResult:
    """
    Compare two texts.

    Calculates semantic similarity and generates a detailed diff.

    Args:
        request: CompareTextsRequest with two texts to compare.

    Returns:
        ComparisonResult with similarity score and differences.

    Raises:
        HTTPException: If comparison fails.
    """
    try:
        service = get_comparison_service()
        result = await service.compare(
            text1=request.text1,
            text2=request.text2,
            generate_summary=request.generate_summary,
        )
        return result
    except Exception as e:
        logger.error(f"Text comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents", response_model=ComparisonResult)
async def compare_documents(request: CompareDocumentsRequest) -> ComparisonResult:
    """
    Compare two documents from the Silver layer.

    Fetches both documents and performs semantic comparison.

    Args:
        request: CompareDocumentsRequest with two silver keys.

    Returns:
        ComparisonResult with similarity score and differences.

    Raises:
        HTTPException: If documents not found or comparison fails.
    """
    try:
        minio = get_minio_service()

        # Get document metadata
        doc1 = minio.get_document(request.silver_key1)
        doc2 = minio.get_document(request.silver_key2)

        if not doc1:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {request.silver_key1}",
            )
        if not doc2:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {request.silver_key2}",
            )

        # Extract text from both documents
        text1 = await _extract_document_text(
            request.silver_key1,
            doc1.get("file_type"),
        )
        text2 = await _extract_document_text(
            request.silver_key2,
            doc2.get("file_type"),
        )

        if not text1 or len(text1.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Could not extract text from {request.silver_key1}",
            )
        if not text2 or len(text2.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Could not extract text from {request.silver_key2}",
            )

        service = get_comparison_service()
        result = await service.compare(
            text1=text1,
            text2=text2,
            generate_summary=request.generate_summary,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick")
async def quick_diff(request: QuickDiffRequest) -> dict[str, Any]:
    """
    Generate a quick diff without LLM processing.

    Provides basic statistics about changes between texts.

    Args:
        request: QuickDiffRequest with two texts.

    Returns:
        Dict with diff statistics.

    Raises:
        HTTPException: If diff generation fails.
    """
    try:
        service = get_comparison_service()
        result = service.quick_diff(
            text1=request.text1,
            text2=request.text2,
        )
        return result
    except Exception as e:
        logger.error(f"Quick diff failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions")
async def compare_versions(
    silver_keys: list[str],
) -> dict[str, Any]:
    """
    Compare multiple versions of a document.

    Compares consecutive versions and returns all comparison results.

    Args:
        silver_keys: List of silver keys representing document versions.

    Returns:
        Dict with version comparisons.

    Raises:
        HTTPException: If fewer than 2 versions or comparison fails.
    """
    if len(silver_keys) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 versions required for comparison",
        )

    try:
        minio = get_minio_service()

        # Extract text from all versions
        versions = []
        for i, key in enumerate(silver_keys):
            doc = minio.get_document(key)
            if not doc:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document not found: {key}",
                )

            text = await _extract_document_text(key, doc.get("file_type"))
            versions.append({
                "version_id": f"v{i + 1}",
                "silver_key": key,
                "text": text,
                "filename": doc.get("filename"),
            })

        service = get_comparison_service()
        results = await service.compare_versions(versions)

        return {
            "version_count": len(versions),
            "comparisons": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Version comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similarity")
async def check_similarity(
    silver_key1: str,
    silver_key2: str,
) -> dict[str, Any]:
    """
    Quick similarity check between two documents.

    Returns only the similarity score without full diff.

    Args:
        silver_key1: First document silver key.
        silver_key2: Second document silver key.

    Returns:
        Dict with similarity score and similar flag.

    Raises:
        HTTPException: If documents not found or calculation fails.
    """
    try:
        minio = get_minio_service()

        doc1 = minio.get_document(silver_key1)
        doc2 = minio.get_document(silver_key2)

        if not doc1:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {silver_key1}",
            )
        if not doc2:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {silver_key2}",
            )

        text1 = await _extract_document_text(silver_key1, doc1.get("file_type"))
        text2 = await _extract_document_text(silver_key2, doc2.get("file_type"))

        service = get_comparison_service()
        result = await service.compare(
            text1=text1,
            text2=text2,
            generate_summary=False,
        )

        return {
            "silver_key1": silver_key1,
            "silver_key2": silver_key2,
            "similarity_score": result.similarity_score,
            "is_similar": result.is_similar,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similarity check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _extract_document_text(silver_key: str, file_type: str | None) -> str:
    """
    Extract text content from a document.

    Args:
        silver_key: Silver layer document key.
        file_type: Document file type.

    Returns:
        Extracted text content.
    """
    import pandas as pd
    import pymupdf
    from docx import Document

    minio = get_minio_service()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        minio.get_silver_file_to_path(silver_key, tmp_path)

        ext = (file_type or "").lower()
        text = ""

        if ext == "pdf":
            doc = pymupdf.open(tmp_path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        elif ext == "docx":
            doc = Document(tmp_path)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        elif ext in ("xlsx", "xls"):
            df = pd.read_excel(tmp_path)
            text = df.to_string(index=False)
        elif ext == "csv":
            df = pd.read_csv(tmp_path)
            text = df.to_string(index=False)
        else:
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        return text

    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
