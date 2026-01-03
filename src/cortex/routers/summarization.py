"""
Summarization API endpoints.

This module provides endpoints for document summarization including
executive summaries, key points, entity extraction, and action items.
"""

import logging
import os
import tempfile
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from cortex.services.minio import get_minio_service
from cortex.services.summarization_service import (
    SummaryResult,
    get_summarization_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/summarize", tags=["summarization"])


class SummarizeTextRequest(BaseModel):
    """Request model for text summarization."""

    text: str = Field(..., min_length=50, description="Text to summarize")
    include_entities: bool = Field(default=True, description="Extract named entities")
    include_actions: bool = Field(default=True, description="Detect action items")
    include_extractive: bool = Field(
        default=True,
        description="Include extractive summary",
    )


class SummarizeDocumentRequest(BaseModel):
    """Request model for document summarization."""

    silver_key: str = Field(..., description="Silver layer document key")
    include_entities: bool = Field(default=True, description="Extract named entities")
    include_actions: bool = Field(default=True, description="Detect action items")
    include_extractive: bool = Field(
        default=True,
        description="Include extractive summary",
    )


class QuickSummaryRequest(BaseModel):
    """Request model for quick summary."""

    text: str = Field(..., min_length=50, description="Text to summarize")
    max_words: int = Field(default=100, ge=20, le=500, description="Max summary words")


@router.post("", response_model=SummaryResult)
async def summarize_text(request: SummarizeTextRequest) -> SummaryResult:
    """
    Summarize provided text.

    Generates a comprehensive summary including:
    - Executive summary (abstractive)
    - Key bullet points
    - Named entities (optional)
    - Action items (optional)
    - Extractive summary (optional)

    Args:
        request: SummarizeTextRequest with text and options.

    Returns:
        SummaryResult with all summary components.

    Raises:
        HTTPException: If summarization fails.
    """
    try:
        service = get_summarization_service()
        result = await service.summarize(
            text=request.text,
            include_entities=request.include_entities,
            include_actions=request.include_actions,
            include_extractive=request.include_extractive,
        )
        return result
    except Exception as e:
        logger.error(f"Text summarization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document", response_model=SummaryResult)
async def summarize_document(request: SummarizeDocumentRequest) -> SummaryResult:
    """
    Summarize a document from the Silver layer.

    Fetches the document content and generates a comprehensive summary.

    Args:
        request: SummarizeDocumentRequest with silver_key and options.

    Returns:
        SummaryResult with all summary components.

    Raises:
        HTTPException: If document not found or summarization fails.
    """
    try:
        minio = get_minio_service()

        # Get document metadata
        doc = minio.get_document(request.silver_key)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Download and extract text
        text = await _extract_document_text(request.silver_key, doc.get("file_type"))

        if not text or len(text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text from document",
            )

        service = get_summarization_service()
        result = await service.summarize(
            text=text,
            include_entities=request.include_entities,
            include_actions=request.include_actions,
            include_extractive=request.include_extractive,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document summarization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick")
async def quick_summary(request: QuickSummaryRequest) -> dict[str, Any]:
    """
    Generate a quick, short summary.

    Args:
        request: QuickSummaryRequest with text and max_words.

    Returns:
        Dict with summary and word count.

    Raises:
        HTTPException: If summarization fails.
    """
    try:
        service = get_summarization_service()
        summary = await service.quick_summary(
            text=request.text,
            max_words=request.max_words,
        )
        return {
            "summary": summary,
            "word_count": len(summary.split()),
            "original_word_count": len(request.text.split()),
        }
    except Exception as e:
        logger.error(f"Quick summary failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{silver_key:path}")
async def get_cached_summary(silver_key: str) -> dict[str, Any]:
    """
    Get cached summary for a document (if available).

    Args:
        silver_key: Silver layer document key.

    Returns:
        Cached summary or message indicating none exists.

    Raises:
        HTTPException: If document not found.
    """
    try:
        minio = get_minio_service()

        doc = minio.get_document(silver_key)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Check for cached summary in metadata
        cached_summary = doc.get("summary")
        if cached_summary:
            return {
                "silver_key": silver_key,
                "cached": True,
                "summary": cached_summary,
            }

        return {
            "silver_key": silver_key,
            "cached": False,
            "message": "No cached summary. Use POST /api/summarize/document to generate.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get cached summary failed: {e}", exc_info=True)
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
            text = f"Columns: {', '.join(df.columns.astype(str))}\n"
            text += df.head(50).to_string(index=False)
        elif ext == "csv":
            df = pd.read_csv(tmp_path)
            text = f"Columns: {', '.join(df.columns.astype(str))}\n"
            text += df.head(50).to_string(index=False)
        elif ext == "txt":
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        else:
            # Try reading as text
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        return text

    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
