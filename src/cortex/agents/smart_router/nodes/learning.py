"""
Smart Router Learning Node.

This module handles learning from high-confidence classifications
to improve future classification accuracy.
"""

import logging
import re

from cortex.agents.smart_router.config import HIGH_CONFIDENCE_THRESHOLD
from cortex.agents.smart_router.state import RouterState
from cortex.database.connection import DatabaseService

logger = logging.getLogger(__name__)


async def learning_node(state: RouterState) -> dict:
    """
    Learn from high-confidence classifications.

    When confidence exceeds threshold, saves the document's content as a
    learned context for future classifications and updates category embeddings.

    Args:
        state: Current router state with classification results.

    Returns:
        Dict with updated logs.
    """
    db_service = DatabaseService()
    logs = state.get("logs", [])

    classification = state.get("classification", "")
    confidence = state.get("confidence", 0.0)
    content_preview = state.get("content_preview", "")
    silver_key = state.get("silver_key", "")
    doc_embedding = state.get("doc_embedding", [])

    # Only learn from high-confidence classifications
    if confidence >= HIGH_CONFIDENCE_THRESHOLD and classification != "unclassified":
        logs.append(
            f"Learning from high-confidence ({confidence:.0%}) classification: "
            f"'{classification}'"
        )

        # 1. Save learned context to database
        if content_preview and len(content_preview.strip()) > 100:
            try:
                # Build context text from document preview
                context_text = _build_context_text(content_preview, classification)

                db_service.save_learned_context(
                    category=classification,
                    context_text=context_text,
                    sample_content=content_preview[:500],  # First 500 chars as sample
                    source_document_key=silver_key,
                    confidence_when_learned=confidence,
                )
                logs.append(f"Saved learned context for category '{classification}'")

            except Exception as e:
                logger.error(f"Learned context save error: {e}")
                logs.append(f"Learned context warning: {e}")

        # 2. Incrementally update category embedding cache
        if doc_embedding and len(doc_embedding) > 0 and silver_key:
            try:
                db_service.update_category_embedding_incremental(
                    category=classification,
                    new_embedding=doc_embedding,
                    new_sample_key=silver_key,
                    weight=0.1,  # 10% influence from each new high-confidence doc
                )
                logs.append(
                    f"Updated category embedding for '{classification}' with new document"
                )

            except Exception as e:
                logger.error(f"Category embedding update error: {e}")
                logs.append(f"Category embedding update warning: {e}")
    else:
        logs.append(
            f"Skipped learning - confidence {confidence:.0%} below threshold "
            f"{HIGH_CONFIDENCE_THRESHOLD:.0%}"
        )

    return {"logs": logs}


def _build_context_text(content_preview: str, category: str) -> str:
    """
    Build context text from document content for learning.

    Extracts key phrases and summarizes the content for use as context
    in future classifications.

    Args:
        content_preview: Document content preview.
        category: The classification category.

    Returns:
        Context text string.
    """
    # Take first 300 chars and clean up
    sample = content_preview[:300].strip()

    # Remove excessive whitespace
    sample = re.sub(r"\s+", " ", sample)

    # Build context description
    context_text = (
        f"Document classified as {category}. "
        f"Content excerpt: {sample}"
    )

    return context_text[:500]  # Limit total length
