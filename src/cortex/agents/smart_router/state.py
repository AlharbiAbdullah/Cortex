"""
Smart Router State Definition.

This module defines the RouterState TypedDict that flows through
the LangGraph nodes during document classification and routing.
"""

import os
from typing import Any, TypedDict


class RouterState(TypedDict):
    """
    State object that flows through the Smart Router Graph.

    This TypedDict defines all the data that is passed between nodes
    during document processing, classification, and routing.
    """

    # ==========================================================================
    # Input Fields
    # ==========================================================================
    file_path: str  # Local file path (used for backward compat, prefer bronze_key)
    file_type: str  # File extension: csv, md, xlsx, docx, pdf, txt, etc.
    filename: str  # Original filename
    document_id: str  # Stable ID used for Bronze/Silver keys (UUID recommended)

    # ==========================================================================
    # Document Content
    # ==========================================================================
    raw_content: str  # Full extracted text content
    content_preview: str  # First N chars for classification

    # ==========================================================================
    # MinIO Data Lake Keys (Silver = source of truth)
    # ==========================================================================
    bronze_key: str  # Temporary key in Bronze bucket
    silver_key: str  # Permanent key in Silver bucket (unique identifier)

    # ==========================================================================
    # Context from Database (for classification learning)
    # ==========================================================================
    predefined_contexts: list[dict]  # Built-in category contexts
    learned_contexts: list[dict]  # Contexts learned from high-confidence docs
    context_ids_used: list[int]  # IDs of contexts used in classification

    # ==========================================================================
    # Embeddings (computed in fetch_context, used in classify)
    # ==========================================================================
    doc_embedding: list[float]  # Document embedding vector
    category_embeddings: dict[str, list[float]]  # {category: centroid_embedding}

    # ==========================================================================
    # Classification Result (multi-category support with per-category confidence)
    # ==========================================================================
    primary_category: str  # Main category
    additional_categories: list[str]  # Additional categories (can be empty)
    all_categories: list[str]  # Combined: primary + additional
    classification: str  # Legacy: same as primary_category for backward compat
    confidence: float  # Primary category confidence
    category_scores: dict[str, float]  # Per-category confidence scores from ensemble
    ensemble_variance: dict[str, float]  # Variance per category (high = LLM disagreement)
    ensemble_count: int  # Number of LLMs that contributed to ensemble
    reasoning: str  # Explanation for classification decision

    # ==========================================================================
    # Pipeline Results
    # ==========================================================================
    extracted_data: list[dict[str, Any]]  # Extracted structured data
    pipeline_logs: list[str]  # Logs from pipeline processing

    # ==========================================================================
    # Status and Metadata
    # ==========================================================================
    status: str  # pending, processed, error, pending_review
    error: str | None  # Error message if status is error
    logs: list[str]  # Processing logs


def create_initial_state(
    bronze_key: str,
    filename: str,
    document_id: str | None = None,
) -> RouterState:
    """
    Create an initial RouterState for processing a document.

    Args:
        bronze_key: MinIO Bronze key where the raw file was uploaded.
        filename: Original filename.
        document_id: Stable document identifier (if omitted, derived from bronze_key).

    Returns:
        Initialized RouterState ready for graph processing.
    """
    if not document_id:
        # Derive from Bronze key: uploads/<document_id>.<ext>
        document_id = os.path.splitext(os.path.basename(bronze_key))[0]

    return RouterState(
        # Input
        file_path="",  # No persistent local file; extraction downloads from Bronze to temp
        file_type="unknown",
        filename=filename,
        document_id=document_id,
        # Content
        raw_content="",
        content_preview="",
        # MinIO keys
        bronze_key=bronze_key,
        silver_key="",
        # Context
        predefined_contexts=[],
        learned_contexts=[],
        context_ids_used=[],
        # Embeddings
        doc_embedding=[],
        category_embeddings={},
        # Classification
        primary_category="",
        additional_categories=[],
        all_categories=[],
        classification="",  # Legacy compat
        confidence=0.0,
        category_scores={},
        ensemble_variance={},
        ensemble_count=0,
        reasoning="",
        # Pipeline results
        extracted_data=[],
        pipeline_logs=[],
        # Status
        status="pending",
        error=None,
        logs=[f"Uploaded to Bronze: {bronze_key}"],
    )
