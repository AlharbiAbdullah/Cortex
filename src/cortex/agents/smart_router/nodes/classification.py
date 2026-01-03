"""
Smart Router Classification Node.

This module contains the main classification logic including:
- Embedding-based pre-filtering
- LLM ensemble classification
- Multi-category scoring and aggregation
"""

import asyncio
import json
import logging
import os
from typing import Any

from cortex.agents.llm import get_llm
from cortex.agents.smart_router.config import (
    ENSEMBLE_ADDITIONAL_THRESHOLD,
    ENSEMBLE_MODELS,
    ENSEMBLE_TOP_CANDIDATES,
    LOW_CONFIDENCE_THRESHOLD,
    PIPELINE_CATEGORIES,
)
from cortex.agents.smart_router.embeddings import compute_embedding_confidence
from cortex.agents.smart_router.state import RouterState
from cortex.agents.smart_router.utils import build_content_preview, canonicalize_category

logger = logging.getLogger(__name__)


async def classify_content_node(state: RouterState) -> dict:
    """
    Hybrid classification using embeddings pre-filter + LLM ensemble.

    Flow:
    1. Use embedding similarity scores to pre-filter to top N candidate categories
    2. Run LLMs in parallel on those candidates
    3. Aggregate per-category scores to determine primary + additional categories

    This approach:
    - Reduces LLM cost by only scoring top candidates (not all 100 categories)
    - Provides robust classification via ensemble averaging
    - Returns per-category confidence scores for additional_categories

    Args:
        state: Current router state with content_preview and embeddings.

    Returns:
        Dict with classification results including primary_category, confidence,
        category_scores, and updated logs.
    """
    logs = state.get("logs", [])

    try:
        preview_chars = int(os.getenv("ROUTER_CONTENT_PREVIEW_CHARS", "3000") or "3000")
    except Exception:
        preview_chars = 3000

    raw_text = state.get("raw_content", "") or ""
    content_preview = build_content_preview(raw_text, max_chars=preview_chars)
    predefined_contexts = state.get("predefined_contexts", [])
    learned_contexts = state.get("learned_contexts", [])

    # Get pre-computed embeddings from state (computed in fetch_context_node)
    doc_embedding = state.get("doc_embedding", [])
    category_embeddings = state.get("category_embeddings", {})

    # ==================== STEP 1: Embedding Pre-Filter ====================
    embedding_meta: dict[str, Any] = {}
    category_scores_ranked: list[dict[str, Any]] = []

    try:
        if doc_embedding and len(doc_embedding) > 0:
            embedding_meta = compute_embedding_confidence(
                doc_embedding=doc_embedding,
                category_embeddings=category_embeddings,
                predefined_contexts=predefined_contexts,
                learned_contexts=learned_contexts,
            )
            # Convert to list of dicts for compatibility
            category_scores_ranked = [
                {"category": cat, "score": score}
                for cat, score in embedding_meta.get("category_scores_ranked", [])
            ]
    except Exception as emb_err:
        logger.warning(f"Embedding pre-filter failed: {emb_err}")
        logs.append(f"Embedding pre-filter warning: {emb_err}")

    # Select top N candidates from embedding scores
    top_n = ENSEMBLE_TOP_CANDIDATES
    if category_scores_ranked:
        top_candidates = [item["category"] for item in category_scores_ranked[:top_n]]
        logs.append(f"Embedding pre-filter: top {top_n} candidates = {top_candidates}")
    else:
        # Fallback: use all categories if embeddings failed
        top_candidates = list(PIPELINE_CATEGORIES.keys())[:top_n]
        logs.append(f"Embedding pre-filter failed, using first {top_n} categories")

    # Build candidate categories dict for ensemble
    candidate_categories = {
        cat: PIPELINE_CATEGORIES.get(cat, "")
        for cat in top_candidates
        if cat in PIPELINE_CATEGORIES
    }

    # ==================== STEP 2: Build Context for LLM ====================
    context_sections = []

    if predefined_contexts or learned_contexts:
        context_sections.append("=== EXAMPLES FROM DATABASE ===")

        for ctx in predefined_contexts:
            if ctx.get("sample_content") and ctx.get("category") in candidate_categories:
                context_sections.append(
                    f"* {ctx['category'].upper()} example: {ctx['sample_content'][:200]}..."
                )

        for ctx in learned_contexts[:5]:
            if ctx.get("sample_content") and ctx.get("category") in candidate_categories:
                context_sections.append(
                    f"* {ctx['category'].upper()} (learned, used {ctx['usage_count']}x): "
                    f"{ctx['sample_content'][:150]}..."
                )

    context_text = "\n".join(context_sections) if context_sections else ""

    # ==================== STEP 3: Run LLM Ensemble ====================
    try:
        ensemble_result = await _ensemble_classify(
            content_preview=content_preview,
            candidate_categories=candidate_categories,
            context_text=context_text,
            models=ENSEMBLE_MODELS,
            additional_threshold=ENSEMBLE_ADDITIONAL_THRESHOLD,
        )

        # Extract and normalize results
        primary_category = canonicalize_category(
            ensemble_result.get("primary_category", "unclassified")
        )
        primary_confidence = float(ensemble_result.get("primary_confidence", 0.0))

        # Get additional categories (already filtered by threshold in ensemble)
        additional_categories = [
            canonicalize_category(cat)
            for cat in ensemble_result.get("additional_categories", [])
        ]
        # Remove duplicates and primary
        additional_categories = [
            cat
            for cat in additional_categories
            if cat != primary_category and cat != "unclassified"
        ]

        # Combine all categories
        all_categories = [primary_category] + additional_categories

        # Get per-category scores
        category_scores = ensemble_result.get("category_scores", {})
        ensemble_variance = ensemble_result.get("ensemble_variance", {})
        ensemble_count = ensemble_result.get("ensemble_count", 0)
        reasoning = ensemble_result.get("reasoning", "")

        # CRITICAL: If no category reaches threshold, mark as "unclassified"
        if primary_confidence < LOW_CONFIDENCE_THRESHOLD:
            original_best = ensemble_result.get("primary_category", "unknown")
            logs.append(
                f"No category reached {LOW_CONFIDENCE_THRESHOLD:.0%} threshold. "
                f"Best was '{original_best}' at {primary_confidence:.0%}. "
                "Marking as 'unclassified' for human review."
            )
            primary_category = "unclassified"
            additional_categories = []
            all_categories = ["unclassified"]
            reasoning = (
                f"No confident classification - best score was {primary_confidence:.0%} "
                f"(below {LOW_CONFIDENCE_THRESHOLD:.0%} threshold). "
                f"Original best: {original_best}. {reasoning}"
            )

        # Check for high variance (LLMs disagree)
        max_variance = max(ensemble_variance.values()) if ensemble_variance else 0.0
        if max_variance > 0.1:
            logs.append(
                f"High ensemble variance ({max_variance:.2f}), "
                "LLMs disagree - consider human review"
            )

        logs.append(
            f"Final classification: '{primary_category}' ({primary_confidence:.0%}) "
            f"with {len(additional_categories)} additional categories: {additional_categories}"
        )

        return {
            "primary_category": primary_category,
            "additional_categories": additional_categories,
            "all_categories": all_categories,
            "classification": primary_category,  # Legacy compatibility
            "confidence": primary_confidence,
            "confidence_source": f"ensemble_{ensemble_count}llm",
            "category_scores": category_scores,
            "ensemble_variance": ensemble_variance,
            "ensemble_count": ensemble_count,
            **embedding_meta,
            "reasoning": reasoning,
            "logs": logs,
        }

    except Exception as e:
        logger.error(f"Ensemble classification failed: {e}", exc_info=True)

        # Fallback: use embedding best category if available
        if category_scores_ranked:
            best = category_scores_ranked[0]
            return {
                "primary_category": best["category"],
                "additional_categories": [],
                "all_categories": [best["category"]],
                "classification": best["category"],
                "confidence": best["score"],
                "confidence_source": "embedding_fallback",
                "category_scores": {},
                "ensemble_variance": {},
                "ensemble_count": 0,
                "reasoning": f"LLM ensemble failed: {e}. Using embedding-based classification.",
                "logs": logs + [f"Classification fallback to embeddings: {e}"],
            }

        return {
            "primary_category": "unclassified",
            "additional_categories": [],
            "all_categories": ["unclassified"],
            "classification": "unclassified",
            "confidence": 0.0,
            "confidence_source": "error",
            "category_scores": {},
            "ensemble_variance": {},
            "ensemble_count": 0,
            "reasoning": f"Classification failed: {e}",
            "logs": logs + [f"Classification error: {e}"],
        }


async def _single_llm_classify(
    llm: Any,
    content_preview: str,
    candidate_categories: dict[str, str],
    context_text: str,
) -> dict[str, float]:
    """
    Run a single LLM classification that returns per-category confidence scores.

    Args:
        llm: The LLM instance to use.
        content_preview: Document content to classify.
        candidate_categories: Dict of {category: description} to score.
        context_text: Additional context (examples, etc.).

    Returns:
        Dict mapping category names to confidence scores (0.0-1.0).
    """
    category_list = "\n".join(
        [f"* {cat.upper()}: {desc}" for cat, desc in candidate_categories.items()]
    )

    prompt = f"""You are a document classification expert. Score how well this document fits \
EACH category.

=== CATEGORIES TO SCORE ===
{category_list}

{context_text}

=== DOCUMENT CONTENT ===
{content_preview}

=== SCORING RULES ===
1. Score EACH category independently from 0.0 to 1.0
2. A document CAN fit multiple categories - score each on its own merit
3. 0.90-1.00: Perfect fit, document is clearly about this topic
4. 0.70-0.89: Strong fit, significant content relates to this category
5. 0.50-0.69: Moderate fit, some relevant content
6. 0.30-0.49: Weak fit, minimal relevance
7. 0.00-0.29: No fit, document doesn't relate to this category

Respond with ONLY valid JSON (no markdown):
{{
    "category_scores": {{
        "category_name": 0.XX,
        ...
    }},
    "reasoning": "Brief explanation"
}}

Score ALL categories listed above."""

    try:
        response = await llm.ainvoke(prompt)
        content = response.strip()

        # Parse JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        content = content.strip()
        result = json.loads(content)

        scores = result.get("category_scores", {})

        # Normalize scores to valid range and categories
        normalized_scores = {}
        for cat in candidate_categories.keys():
            # Try exact match first, then case-insensitive
            score = scores.get(cat)
            if score is None:
                score = scores.get(cat.lower())
            if score is None:
                score = scores.get(cat.upper())
            if score is None:
                # Try to find partial match
                for key, val in scores.items():
                    if key.lower() == cat.lower():
                        score = val
                        break

            if score is not None:
                try:
                    score = float(score)
                    score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
                except (TypeError, ValueError):
                    score = 0.0
            else:
                score = 0.0

            normalized_scores[cat] = score

        return normalized_scores

    except Exception as e:
        logger.warning(f"Single LLM classification failed: {e}")
        # Return zeros for all categories on failure
        return {cat: 0.0 for cat in candidate_categories.keys()}


async def _ensemble_classify(
    content_preview: str,
    candidate_categories: dict[str, str],
    context_text: str = "",
    models: list[str] | None = None,
    additional_threshold: float | None = None,
) -> dict[str, Any]:
    """
    Run ensemble classification with multiple diverse LLMs in parallel.

    Uses multiple LLM models, aggregates their per-category confidence scores,
    and determines primary + additional categories.

    Args:
        content_preview: Document content to classify.
        candidate_categories: Dict of {category: description} - pre-filtered by embeddings.
        context_text: Additional context (examples from DB).
        models: List of model names for ensemble (default: ENSEMBLE_MODELS).
        additional_threshold: Threshold for additional categories.

    Returns:
        Dict with primary_category, primary_confidence, additional_categories,
        category_scores, ensemble_variance, and reasoning.
    """
    if models is None:
        models = ENSEMBLE_MODELS
    if additional_threshold is None:
        additional_threshold = ENSEMBLE_ADDITIONAL_THRESHOLD

    # Create LLM instances with different models (temperature=0 for consistency)
    llms = [get_llm(model=model, temperature=0.0) for model in models]

    # Run all LLMs in parallel
    tasks = [
        _single_llm_classify(llm, content_preview, candidate_categories, context_text)
        for llm in llms
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and collect valid results
    valid_results: list[dict[str, float]] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"LLM {i} ({models[i]}) failed: {result}")
        elif isinstance(result, dict):
            valid_results.append(result)

    if not valid_results:
        # All LLMs failed - return unclassified for human review
        logger.error("All ensemble LLMs failed, returning 'unclassified'")
        return {
            "primary_category": "unclassified",
            "primary_confidence": 0.0,
            "additional_categories": [],
            "category_scores": {cat: 0.0 for cat in candidate_categories.keys()},
            "ensemble_variance": {},
            "ensemble_count": 0,
            "reasoning": "All ensemble LLMs failed - requires human classification",
        }

    # Aggregate scores: compute average per category
    avg_scores: dict[str, float] = {}
    variance_scores: dict[str, float] = {}

    for cat in candidate_categories.keys():
        scores = [r.get(cat, 0.0) for r in valid_results]
        avg = sum(scores) / len(scores)
        avg_scores[cat] = avg

        # Compute variance (high variance = LLMs disagree = flag for review)
        if len(scores) > 1:
            variance = sum((s - avg) ** 2 for s in scores) / len(scores)
            variance_scores[cat] = variance
        else:
            variance_scores[cat] = 0.0

    # Determine primary category (highest average score)
    primary_category = max(avg_scores, key=avg_scores.get)
    primary_confidence = avg_scores[primary_category]

    # Determine additional categories (above threshold, excluding primary)
    additional_categories = [
        cat
        for cat, score in avg_scores.items()
        if score >= additional_threshold and cat != primary_category
    ]

    # Sort additional categories by score (highest first)
    additional_categories.sort(key=lambda c: avg_scores[c], reverse=True)

    # Build reasoning
    score_summary = ", ".join(
        [
            f"{cat}: {score:.0%}"
            for cat, score in sorted(
                avg_scores.items(), key=lambda x: x[1], reverse=True
            )
        ]
    )
    reasoning = f"Ensemble ({len(valid_results)} LLMs): {score_summary}"

    return {
        "primary_category": primary_category,
        "primary_confidence": primary_confidence,
        "additional_categories": additional_categories,
        "category_scores": avg_scores,
        "ensemble_variance": variance_scores,
        "ensemble_count": len(valid_results),
        "reasoning": reasoning,
    }
