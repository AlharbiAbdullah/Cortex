"""
Smart Router Utility Functions.

This module contains helper functions for category normalization,
confidence handling, content preview, and mathematical operations.
"""

import json
import math
import os
import re
from typing import Any

from cortex.agents.smart_router.config import CATEGORY_ALIASES, PIPELINE_CATEGORIES


def canonicalize_category(value: Any) -> str:
    """
    Normalize a category value to its canonical form.

    Handles various input types and applies alias mapping.
    Returns 'unclassified' for values that don't match any known category.

    Args:
        value: The category value to normalize (string, dict, or other).

    Returns:
        Canonical category name or 'unclassified'.
    """
    if value is None:
        return "unclassified"

    # Handle dict with 'category' key
    if isinstance(value, dict):
        value = value.get("category") or value.get("classification") or ""

    # Convert to string and normalize
    raw = str(value).strip().lower()

    # Remove common prefixes/suffixes
    raw = re.sub(r"^(category[:\s]*|type[:\s]*)", "", raw)
    raw = re.sub(r"[:\s]*$", "", raw)

    # Replace spaces/hyphens with underscores
    raw = re.sub(r"[\s\-]+", "_", raw)

    # Remove non-alphanumeric except underscores
    raw = re.sub(r"[^a-z0-9_]", "", raw)

    # Check if it's a valid category
    if raw in PIPELINE_CATEGORIES:
        return raw

    # Check aliases
    if raw in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[raw]

    # Try partial matching for common patterns
    for alias, canonical in CATEGORY_ALIASES.items():
        if alias in raw or raw in alias:
            return canonical

    return "unclassified"


def normalize_confidence(value: Any, default: float = 0.5) -> float:
    """
    Normalize a confidence value to a float between 0 and 1.

    Handles various input types including strings, percentages, and dicts.

    Args:
        value: The confidence value to normalize.
        default: Default value if parsing fails.

    Returns:
        Float between 0 and 1.
    """
    if value is None:
        return default

    # Handle dict with 'confidence' or 'score' key
    if isinstance(value, dict):
        value = (
            value.get("confidence")
            or value.get("score")
            or value.get("probability")
            or default
        )

    # Handle string
    if isinstance(value, str):
        # Remove percentage sign and extra whitespace
        value = value.strip().rstrip("%").strip()
        try:
            value = float(value)
            # If it looks like a percentage (>1), convert
            if value > 1:
                value = value / 100.0
        except (ValueError, TypeError):
            return default

    # Handle numeric types
    try:
        result = float(value)
        # Clamp to [0, 1]
        if result > 1:
            result = result / 100.0
        return max(0.0, min(1.0, result))
    except (ValueError, TypeError):
        return default


def build_content_preview(text: str, max_chars: int = 3000) -> str:
    """
    Build a content preview for classification.

    Truncates text and ensures clean boundaries.

    Args:
        text: Full text content.
        max_chars: Maximum characters for preview.

    Returns:
        Truncated preview text.
    """
    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text

    # Try to truncate at a sentence boundary
    preview = text[:max_chars]
    last_period = preview.rfind(".")
    last_newline = preview.rfind("\n")

    # Use the later of period or newline if reasonable
    boundary = max(last_period, last_newline)
    if boundary > max_chars * 0.7:  # At least 70% of content
        preview = preview[: boundary + 1]

    return preview.strip()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity between -1 and 1.
    """
    if not a or not b or len(a) != len(b):
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(x * x for x in b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def scale_to_unit(x: float, low: float, high: float) -> float:
    """
    Scale a value from [low, high] range to [0, 1].

    Values outside the range are clamped.

    Args:
        x: Value to scale.
        low: Lower bound of original range.
        high: Upper bound of original range.

    Returns:
        Scaled value between 0 and 1.
    """
    if high <= low:
        return 0.5

    scaled = (x - low) / (high - low)
    return max(0.0, min(1.0, scaled))


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename.

    Always returns the raw extension: csv, md, xlsx, docx, pdf, txt, etc.
    Returns 'unknown' if no extension found.

    Args:
        filename: The filename to extract extension from.

    Returns:
        Lowercase file extension without dot, or 'unknown'.
    """
    ext = os.path.splitext(filename)[1].lower()
    ext_no_dot = ext[1:] if ext.startswith(".") else ext
    return ext_no_dot or "unknown"


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks for processing.

    Args:
        text: Text to split.
        chunk_size: Maximum size of each chunk.
        overlap: Number of characters to overlap between chunks.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a word boundary
        if end < len(text):
            space_idx = text.rfind(" ", start + chunk_size - 100, end)
            if space_idx > start:
                end = space_idx

        chunks.append(text[start:end].strip())
        start = end - overlap

    return chunks


def safe_json_parse(text: str) -> dict | list | None:
    """
    Safely parse JSON from a string, handling common issues.

    Args:
        text: String that may contain JSON.

    Returns:
        Parsed JSON object or None if parsing fails.
    """
    if not text:
        return None

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find JSON object or array
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    return None
