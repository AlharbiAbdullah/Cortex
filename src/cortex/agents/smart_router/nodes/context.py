"""
Smart Router Context Node.

This module handles fetching classification contexts from the database
and computing document/category embeddings for pre-filtering.
"""

import logging
import os
import tempfile
from typing import Any

import pandas as pd
import pymupdf
from docx import Document

from cortex.agents.smart_router.embeddings import embed_texts
from cortex.agents.smart_router.state import RouterState
from cortex.agents.smart_router.utils import build_content_preview
from cortex.database.connection import DatabaseService
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)


def fetch_context_node(state: RouterState) -> dict:
    """
    Fetch contexts from database for classification.

    Enhanced to also:
    1. Create document embedding from content preview
    2. Load category embeddings from DB cache (or refresh from MinIO if stale)

    This enables embedding-based classification comparison in classify_content_node.

    Args:
        state: Current router state with content_preview.

    Returns:
        Dict with predefined_contexts, learned_contexts, context_ids_used,
        doc_embedding, category_embeddings, and updated logs.
    """
    db_service = DatabaseService()
    logs = state.get("logs", [])

    try:
        # 1. Always get predefined contexts (handles cold start)
        predefined = db_service.get_predefined_contexts()

        # 2. Get top learned contexts by usage
        learned = db_service.get_top_learned_contexts(limit=10)

        # Track context IDs for later usage update
        context_ids = [ctx["id"] for ctx in predefined + learned]

        logs.append(
            f"Fetched {len(predefined)} predefined contexts, {len(learned)} learned contexts"
        )

        # 3. Create document embedding from content preview
        content_preview = state.get("content_preview", "") or state.get(
            "raw_content", ""
        )
        doc_embedding: list[float] = []

        if content_preview and len(content_preview.strip()) > 50:
            try:
                preview_for_embedding = build_content_preview(
                    content_preview, max_chars=2000
                )
                embeddings = embed_texts([preview_for_embedding])
                if embeddings and len(embeddings) > 0:
                    doc_embedding = embeddings[0]
                    logs.append(
                        f"Created document embedding ({len(doc_embedding)} dimensions)"
                    )
            except Exception as e:
                logger.warning(f"Failed to create document embedding: {e}")
                logs.append(f"Document embedding warning: {e}")

        # 4. Load category embeddings from DB cache
        category_embeddings: dict[str, list[float]] = {}

        try:
            # Check if cache is stale
            cache_stale = db_service.is_embedding_cache_stale(max_age_hours=24)

            if cache_stale:
                logs.append(
                    "Category embedding cache is stale, refreshing from MinIO..."
                )
                minio_service = get_minio_service()
                category_embeddings = _refresh_category_embeddings_from_minio(
                    db_service, minio_service
                )

                if category_embeddings:
                    logs.append(
                        f"Refreshed embeddings for {len(category_embeddings)} categories "
                        "from MinIO"
                    )
                else:
                    # Fall back to loading from DB (may have partial data)
                    category_embeddings = db_service.get_category_embeddings()
                    logs.append(
                        f"Loaded {len(category_embeddings)} category embeddings from "
                        "cache (fallback)"
                    )
            else:
                # Load from cache
                category_embeddings = db_service.get_category_embeddings()
                logs.append(
                    f"Loaded {len(category_embeddings)} category embeddings from cache"
                )

        except Exception as e:
            logger.warning(f"Failed to load category embeddings: {e}")
            logs.append(f"Category embeddings warning: {e}, will use DB contexts only")

        return {
            "predefined_contexts": predefined,
            "learned_contexts": learned,
            "context_ids_used": context_ids,
            "doc_embedding": doc_embedding,
            "category_embeddings": category_embeddings,
            "logs": logs,
        }

    except Exception as e:
        logger.error(f"Context fetch failed: {e}")
        # Return empty but don't fail - classification can still use PIPELINE_CATEGORIES
        return {
            "predefined_contexts": [],
            "learned_contexts": [],
            "context_ids_used": [],
            "doc_embedding": [],
            "category_embeddings": {},
            "logs": logs + [f"Context fetch warning: {e}, using built-in categories"],
        }


def _refresh_category_embeddings_from_minio(
    db_service: DatabaseService,
    minio_service: Any,
) -> dict[str, list[float]]:
    """
    Refresh category embeddings from MinIO Silver documents.

    Fetches high-confidence sample documents for each category,
    extracts their text, computes embeddings, and stores the centroid.

    Args:
        db_service: Database service instance.
        minio_service: MinIO service instance.

    Returns:
        Dict mapping category names to embedding vectors.
    """
    from cortex.agents.smart_router.embeddings import compute_centroid, embed_texts

    category_embeddings: dict[str, list[float]] = {}

    try:
        # Get sample documents per category from MinIO
        category_samples = minio_service.get_distinct_categories_with_samples(
            samples_per_category=5, min_confidence=0.7
        )

        if not category_samples:
            logger.info(
                "No high-confidence documents in MinIO Silver for embedding refresh"
            )
            return category_embeddings

        for category, samples in category_samples.items():
            if not samples:
                continue

            # Collect text content from sample documents
            sample_texts: list[str] = []
            sample_keys: list[str] = []

            for sample in samples:
                silver_key = sample.get("silver_key")
                if not silver_key:
                    continue

                try:
                    # Download and extract text from each sample
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        tmp_path = tmp.name

                    minio_service.get_silver_file_to_path(silver_key, tmp_path)

                    # Extract text based on file type
                    file_type = sample.get("file_type", "").lower()
                    text_content = _extract_sample_text(tmp_path, file_type)

                    # Cleanup temp file
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass

                    if text_content and len(text_content.strip()) > 50:
                        sample_texts.append(text_content[:2000])  # Limit per sample
                        sample_keys.append(silver_key)

                except Exception as e:
                    logger.warning(f"Failed to extract text from {silver_key}: {e}")
                    continue

            if not sample_texts:
                continue

            # Compute embeddings for all samples
            try:
                embeddings = embed_texts(sample_texts)
                if not embeddings:
                    continue

                # Compute centroid (average of all sample embeddings)
                centroid = compute_centroid(embeddings)

                # Save to DB cache
                db_service.save_category_embedding(
                    category=category,
                    embedding=centroid,
                    sample_keys=sample_keys,
                    sample_count=len(sample_keys),
                )

                category_embeddings[category] = centroid
                logger.info(
                    f"Computed embedding for category '{category}' from "
                    f"{len(sample_keys)} samples"
                )

            except Exception as e:
                logger.warning(
                    f"Failed to compute embedding for category '{category}': {e}"
                )
                continue

        return category_embeddings

    except Exception as e:
        logger.error(f"Failed to refresh category embeddings from MinIO: {e}")
        return category_embeddings


def _extract_sample_text(file_path: str, file_type: str) -> str:
    """
    Extract text from a sample file for embedding.

    Args:
        file_path: Path to the file.
        file_type: File type extension.

    Returns:
        Extracted text content.
    """
    text_content = ""

    try:
        if file_type in ("xlsx", "xls"):
            df = pd.read_excel(file_path)
            text_content = f"Columns: {', '.join(df.columns.astype(str))}\n"
            text_content += df.head(10).to_string(index=False)
        elif file_type == "csv":
            df = pd.read_csv(file_path)
            text_content = f"Columns: {', '.join(df.columns.astype(str))}\n"
            text_content += df.head(10).to_string(index=False)
        elif file_type == "docx":
            doc = Document(file_path)
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            text_content = "\n".join(paragraphs[:20])
        elif file_type == "pdf":
            doc = pymupdf.open(file_path)
            pages_text = [page.get_text() for page in doc][:3]
            text_content = "\n".join(pages_text)
            doc.close()
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()[:3000]
    except Exception:
        pass

    return text_content
