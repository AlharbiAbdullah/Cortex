"""
Smart Router Extraction Nodes.

This module contains nodes for initializing document state
and extracting text content from various file formats.
"""

import logging
import os
import uuid

import pandas as pd
import pymupdf
from docx import Document

from cortex.agents.smart_router.state import RouterState
from cortex.agents.smart_router.utils import get_file_extension
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)


def init_node(state: RouterState) -> dict:
    """
    Initialize state and detect file type from extension.

    This is the entry point node that sets up document metadata.

    Args:
        state: Current router state.

    Returns:
        Dict with file_type, filename, document_id, and updated logs.
    """
    file_path = state["file_path"]
    filename = state.get("filename") or os.path.basename(file_path)
    document_id = state.get("document_id") or uuid.uuid4().hex

    # File type is always the raw extension: csv, md, xlsx, docx, pdf, txt, etc.
    file_type = get_file_extension(filename)

    return {
        "file_type": file_type,
        "filename": filename,
        "document_id": document_id,
        "logs": state.get("logs", [])
        + [f"Initialized: {filename} (type: {file_type}, id: {document_id})"],
    }


def extract_text_node(state: RouterState) -> dict:
    """
    Extract text content from Bronze layer file for classification.

    Downloads from MinIO Bronze to temp file, extracts text, then cleans up.
    Supports: PDF, DOCX, XLSX, XLS, CSV, TXT, MD, JSON.

    Args:
        state: Current router state with bronze_key and file_type.

    Returns:
        Dict with raw_content, content_preview, and updated logs.
    """
    bronze_key = state.get("bronze_key", "")
    file_type = state["file_type"]
    text_content = ""

    # Create temp file path using bronze_key
    temp_path = f"/tmp/extract_{os.path.basename(bronze_key) if bronze_key else 'unknown'}"

    try:
        # Download from Bronze to temp file
        if bronze_key:
            minio_service = get_minio_service()
            minio_service.get_bronze_file_to_path(bronze_key, temp_path)
            file_path = temp_path
        else:
            # Fallback to direct file_path if no bronze_key (backward compat)
            file_path = state.get("file_path", "")
            if not file_path:
                raise ValueError("No bronze_key or file_path available")

        ext = (file_type or "").lower()

        # Excel formats (xlsx, xls)
        if ext in ("xlsx", "xls"):
            text_content = _extract_excel(file_path)

        # CSV
        elif ext == "csv":
            text_content = _extract_csv(file_path)

        # Word documents
        elif ext == "docx":
            text_content = _extract_docx(file_path)

        # PDF
        elif ext == "pdf":
            text_content = _extract_pdf(file_path)

        # Plain text and markdown
        elif ext in ("txt", "md"):
            text_content = _extract_text_file(file_path)

        # JSON (read as text for classification)
        elif ext == "json":
            text_content = _extract_text_file(file_path)

        else:
            # Try reading as text (best-effort)
            text_content = _extract_text_file(file_path)

        # Create preview for classification (first 4000 chars)
        content_preview = text_content[:4000] if text_content else ""

        return {
            "raw_content": text_content,
            "content_preview": content_preview,
            "logs": state.get("logs", [])
            + [f"Extracted {len(text_content)} characters of text from Bronze"],
        }

    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return {
            "status": "error",
            "error": f"Text extraction failed: {str(e)}",
            "logs": state.get("logs", []) + [f"Text extraction error: {e}"],
        }

    finally:
        # Cleanup temp file
        if bronze_key and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def _extract_excel(file_path: str) -> str:
    """Extract text from Excel files."""
    try:
        df = pd.read_excel(file_path)
        text_content = f"Columns: {', '.join(df.columns.astype(str))}\n\n"
        text_content += df.head(20).to_string(index=False)
        return text_content
    except Exception as e:
        logger.warning(f"Excel text extraction failed: {e}")
        return ""


def _extract_csv(file_path: str) -> str:
    """Extract text from CSV files."""
    try:
        try:
            df = pd.read_csv(file_path)
        except Exception:
            df = pd.read_csv(file_path, encoding="utf-8-sig")
        text_content = f"Columns: {', '.join(df.columns.astype(str))}\n\n"
        text_content += df.head(20).to_string(index=False)
        return text_content
    except Exception as e:
        logger.warning(f"CSV text extraction failed: {e}")
        return ""


def _extract_docx(file_path: str) -> str:
    """Extract text from Word documents."""
    doc = Document(file_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF files."""
    try:
        doc = pymupdf.open(file_path)
        pages_text = [page.get_text() for page in doc]
        text_content = "\n\n".join(pages_text)
        doc.close()

        # Check if text extraction yielded meaningful content
        cleaned_text = text_content.strip()
        if len(cleaned_text) < 100:
            logger.info(
                f"PDF has minimal text ({len(cleaned_text)} chars), may be scanned"
            )

        return text_content
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise


def _extract_text_file(file_path: str) -> str:
    """Extract text from plain text files."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""
