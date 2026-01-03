"""
Smart Router Embedding Functions.

This module handles embedding generation, caching, and similarity
computations for document classification pre-filtering.
"""

import logging
from threading import Lock

from sentence_transformers import SentenceTransformer

from cortex.agents.smart_router.config import ENSEMBLE_TOP_CANDIDATES, PIPELINE_CATEGORIES
from cortex.agents.smart_router.utils import cosine_similarity, scale_to_unit

logger = logging.getLogger(__name__)

# =============================================================================
# Global Embedder Instance (Thread-Safe Singleton)
# =============================================================================

_embedder: SentenceTransformer | None = None
_embedder_lock = Lock()


def get_router_embedder() -> SentenceTransformer:
    """
    Get the sentence transformer model for document embeddings.

    Uses a thread-safe singleton pattern to avoid loading the model multiple times.

    Returns:
        SentenceTransformer model instance.
    """
    global _embedder
    with _embedder_lock:
        if _embedder is None:
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        return _embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (as lists of floats).
    """
    if not texts:
        return []

    embedder = get_router_embedder()
    embeddings = embedder.encode(texts, convert_to_numpy=True)

    return [emb.tolist() for emb in embeddings]


def embed_single(text: str) -> list[float]:
    """
    Generate embedding for a single text.

    Args:
        text: Text string to embed.

    Returns:
        Embedding vector as list of floats.
    """
    if not text:
        return []

    result = embed_texts([text])
    return result[0] if result else []


def build_category_reference_texts(
    predefined_contexts: list[dict],
    learned_contexts: list[dict],
) -> dict[str, str]:
    """
    Build reference texts for each category from contexts.

    Combines predefined category descriptions with learned contexts
    to create comprehensive reference texts for embedding.

    Args:
        predefined_contexts: List of predefined context dicts from DB.
        learned_contexts: List of learned context dicts from DB.

    Returns:
        Dict mapping category name to reference text.
    """
    category_texts: dict[str, str] = {}

    # Start with base category descriptions
    for category, description in PIPELINE_CATEGORIES.items():
        category_texts[category] = description

    # Enhance with predefined contexts
    for ctx in predefined_contexts:
        cat = ctx.get("category", "")
        if cat in category_texts:
            context_text = ctx.get("context_text", "")
            sample_content = ctx.get("sample_content", "")
            if context_text:
                category_texts[cat] += f" {context_text}"
            if sample_content:
                # Add a snippet of sample content
                category_texts[cat] += f" Example: {sample_content[:200]}"

    # Enhance with learned contexts (higher weight for verified ones)
    for ctx in learned_contexts:
        cat = ctx.get("category", "")
        if cat in category_texts:
            context_text = ctx.get("context_text", "")
            if context_text:
                # Learned contexts get a boost
                category_texts[cat] += f" {context_text}"

    return category_texts


def compute_embedding_similarities(
    doc_embedding: list[float],
    category_embeddings: dict[str, list[float]],
) -> dict[str, float]:
    """
    Compute similarity between document and all category embeddings.

    Args:
        doc_embedding: Document embedding vector.
        category_embeddings: Dict of category name to embedding vector.

    Returns:
        Dict of category name to similarity score (0-1).
    """
    if not doc_embedding or not category_embeddings:
        return {}

    similarities = {}
    for category, cat_embedding in category_embeddings.items():
        if cat_embedding:
            sim = cosine_similarity(doc_embedding, cat_embedding)
            # Convert from [-1, 1] to [0, 1] range
            similarities[category] = (sim + 1.0) / 2.0

    return similarities


def get_top_candidate_categories(
    doc_embedding: list[float],
    category_embeddings: dict[str, list[float]],
    top_n: int = ENSEMBLE_TOP_CANDIDATES,
) -> list[tuple[str, float]]:
    """
    Get top N candidate categories based on embedding similarity.

    This is used as a pre-filter before expensive LLM classification.

    Args:
        doc_embedding: Document embedding vector.
        category_embeddings: Dict of category name to embedding vector.
        top_n: Number of top candidates to return.

    Returns:
        List of (category, similarity_score) tuples, sorted by similarity.
    """
    similarities = compute_embedding_similarities(doc_embedding, category_embeddings)

    # Sort by similarity descending
    sorted_cats = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

    return sorted_cats[:top_n]


def compute_embedding_confidence(
    doc_embedding: list[float],
    category_embeddings: dict[str, list[float]],
    predefined_contexts: list[dict],
    learned_contexts: list[dict],
) -> dict[str, dict]:
    """
    Compute embedding-based confidence scores for all categories.

    Uses multiple signals:
    1. Direct embedding similarity
    2. Context relevance
    3. Cross-category differentiation

    Args:
        doc_embedding: Document embedding vector.
        category_embeddings: Dict of category embeddings.
        predefined_contexts: Predefined context dicts.
        learned_contexts: Learned context dicts.

    Returns:
        Dict with embedding_scores, top_candidates, and category_scores_ranked.
    """
    if not doc_embedding:
        return {
            "embedding_scores": {},
            "top_candidates": [],
            "category_scores_ranked": [],
        }

    # Get base similarities
    similarities = compute_embedding_similarities(doc_embedding, category_embeddings)

    # If no embeddings, fall back to all categories with neutral score
    if not similarities:
        all_cats = list(PIPELINE_CATEGORIES.keys())
        return {
            "embedding_scores": {cat: 0.5 for cat in all_cats},
            "top_candidates": all_cats[:ENSEMBLE_TOP_CANDIDATES],
            "category_scores_ranked": [(cat, 0.5) for cat in all_cats],
        }

    # Sort and get top candidates
    sorted_cats = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    top_candidates = [cat for cat, _ in sorted_cats[:ENSEMBLE_TOP_CANDIDATES]]

    # Scale scores to be more discriminative
    if sorted_cats:
        min_sim = sorted_cats[-1][1]
        max_sim = sorted_cats[0][1]
        scaled_scores = {}
        for cat, sim in sorted_cats:
            # Scale to [0.3, 0.9] range for better LLM interpretation
            scaled = scale_to_unit(sim, min_sim, max_sim) * 0.6 + 0.3
            scaled_scores[cat] = scaled
    else:
        scaled_scores = similarities

    return {
        "embedding_scores": scaled_scores,
        "top_candidates": top_candidates,
        "category_scores_ranked": sorted_cats,
    }


def compute_centroid(embeddings: list[list[float]]) -> list[float]:
    """
    Compute the centroid (average) of multiple embeddings.

    Args:
        embeddings: List of embedding vectors.

    Returns:
        Centroid embedding vector.
    """
    if not embeddings:
        return []

    dim = len(embeddings[0])
    centroid = [0.0] * dim

    for emb in embeddings:
        for i, val in enumerate(emb):
            centroid[i] += val

    return [v / len(embeddings) for v in centroid]


def update_centroid_incremental(
    current_centroid: list[float],
    new_embedding: list[float],
    weight: float = 0.1,
) -> list[float]:
    """
    Update a centroid with a new embedding using weighted averaging.

    Args:
        current_centroid: Current centroid embedding.
        new_embedding: New embedding to incorporate.
        weight: Weight for the new embedding (0-1).

    Returns:
        Updated centroid embedding.
    """
    if not current_centroid:
        return new_embedding
    if not new_embedding:
        return current_centroid

    if len(current_centroid) != len(new_embedding):
        logger.warning("Embedding dimension mismatch in centroid update")
        return current_centroid

    # Weighted average: (1-w) * current + w * new
    return [
        (1 - weight) * c + weight * n for c, n in zip(current_centroid, new_embedding)
    ]
