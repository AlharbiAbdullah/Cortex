"""
Smart Router Storage Nodes.

This module handles copying files to Silver layer and saving routing decisions.
"""

import logging
import os
import uuid

from cortex.agents.smart_router.config import LOW_CONFIDENCE_THRESHOLD, get_domain_for_category
from cortex.agents.smart_router.state import RouterState
from cortex.database.connection import DatabaseService
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)


def copy_to_silver_node(state: RouterState) -> dict:
    """
    Copy file from Bronze to Silver with category tags.

    This is the FINAL DESTINATION - file location never changes.
    Silver layer IS the source of truth - all metadata stored as tags.
    Categories are mutable via re-learning (just update tags, no file move).

    Now includes per-category confidence scores from ensemble classification.

    Args:
        state: Current router state with bronze_key and classification results.

    Returns:
        Dict with document_id, silver_key, status, and updated logs.
    """
    bronze_key = state.get("bronze_key", "")
    document_id = state.get("document_id", "")
    filename = state.get("filename", "unknown")
    file_type = state.get("file_type", "unknown")
    primary_category = state.get("primary_category", "unclassified")
    all_categories = state.get("all_categories", [primary_category])
    confidence = state.get("confidence", 0.0)
    category_scores = state.get("category_scores", {})
    reasoning = state.get("reasoning", "")

    # Reflect low-confidence routing as metadata
    # Treat the threshold as inclusive to avoid confusion around rounding
    status_tag = "pending_review" if confidence <= LOW_CONFIDENCE_THRESHOLD else "processed"

    # Auto-set tableur=1 for tabular file types (CSV, JSON), otherwise 0
    normalized_type = (file_type or "").lower()
    tableur = 1 if normalized_type in ("csv", "json") else 0

    if not bronze_key:
        return {
            "status": "error",
            "error": "No bronze_key available for Silver copy",
            "logs": state.get("logs", []) + ["Error: Missing bronze_key"],
        }

    if not document_id:
        # Backward/defensive fallback: derive a stable-ish ID from the bronze key basename
        document_id = (
            os.path.splitext(os.path.basename(bronze_key))[0] or uuid.uuid4().hex
        )

    try:
        minio_service = get_minio_service()
        silver_key = minio_service.copy_to_silver(
            bronze_key=bronze_key,
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            primary_category=primary_category,
            categories=all_categories,
            confidence=confidence,
            reasoning=reasoning,
            status=status_tag,
            tableur=tableur,
            category_scores=category_scores,
        )

        # Build score summary for logging
        score_summary = (
            ", ".join(
                [
                    f"{cat}:{category_scores.get(cat, 0.0):.0%}"
                    for cat in all_categories[:3]  # Top 3 for brevity
                ]
            )
            if category_scores
            else str(all_categories)
        )

        return {
            "document_id": document_id,
            "silver_key": silver_key,
            "status": status_tag,
            "tableur": tableur,
            "logs": state.get("logs", [])
            + [
                f"Copied to Silver: {silver_key} "
                f"(status: {status_tag}, categories: {score_summary}, tableur: {tableur})"
            ],
        }

    except Exception as e:
        logger.error(f"Silver copy failed: {e}")
        return {
            "status": "error",
            "error": f"Silver copy failed: {str(e)}",
            "logs": state.get("logs", []) + [f"Silver copy error: {e}"],
        }


async def save_results_node(state: RouterState) -> dict:
    """
    Save routing decision to database.

    Records the classification decision for audit trail and analytics.

    Args:
        state: Current router state with classification results.

    Returns:
        Dict with routing_decision_id and updated logs.
    """
    db_service = DatabaseService()
    logs = state.get("logs", [])

    # Extract values from state
    silver_key = state.get("silver_key", "")
    primary_category = state.get("primary_category", "unclassified")
    confidence = state.get("confidence", 0.0)
    reasoning = state.get("reasoning", "")
    context_ids = state.get("context_ids_used", [])
    all_categories = state.get("all_categories", [primary_category])
    category_scores = state.get("category_scores", {})

    if not silver_key:
        logs.append("Warning: No silver_key to save routing decision")
        return {"logs": logs}

    try:
        # Save routing decision
        decision_id = db_service.save_routing_decision(
            document_key=silver_key,
            classification=primary_category,
            confidence_score=confidence,
            reasoning=reasoning,
            context_ids_used=context_ids,
            pipeline_routed_to=_get_pipeline_name(primary_category),
            additional_categories=all_categories[1:] if len(all_categories) > 1 else [],
            category_scores=category_scores,
        )

        logs.append(f"Saved routing decision (ID: {decision_id})")

        # Update context usage counts
        if context_ids:
            db_service.update_context_usage(context_ids)
            logs.append(f"Updated usage for {len(context_ids)} contexts")

        return {
            "routing_decision_id": decision_id,
            "logs": logs,
        }

    except Exception as e:
        logger.error(f"Failed to save routing decision: {e}")
        logs.append(f"Routing decision save warning: {e}")
        return {"logs": logs}


def _get_pipeline_name(category: str) -> str:
    """
    Determine the pipeline name for a category.

    Args:
        category: The classification category.

    Returns:
        Pipeline name string.
    """
    domain = get_domain_for_category(category)

    if domain:
        return f"{domain}_pipeline"
    elif category == "unclassified":
        return "human_review_pipeline"
    else:
        return "generic_pipeline"
