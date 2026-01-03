"""MinIO service helper functions."""

import base64
import math
import os
import re
from typing import Any

from cortex.services.minio.config import TAG_ALLOWED_EXTRA_CHARS


def sanitize_tag_value(value: Any, max_len: int = 256) -> str:
    """
    Sanitize a value for use as MinIO/S3 object tag.

    MinIO/S3 object tags have character and length restrictions.

    Args:
        value: The value to sanitize (any type).
        max_len: Maximum length for the tag value.

    Returns:
        Sanitized string safe for use as tag value.
    """
    if value is None:
        s = ""
    else:
        s = str(value)

    # Normalize whitespace / remove newlines
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip()

    # Replace disallowed chars (keep conservative ASCII-only set)
    cleaned = []
    for ch in s:
        if (ch.isascii() and ch.isalnum()) or ch in TAG_ALLOWED_EXTRA_CHARS:
            cleaned.append(ch)
        else:
            cleaned.append("_")
    s = "".join(cleaned)

    s = re.sub(r"_+", "_", s).strip(" _")
    if not s:
        s = "unknown"
    return s[:max_len]


def b64url_encode_utf8(value: str, max_len: int = 256) -> str | None:
    """
    Encode arbitrary UTF-8 text into a tag-safe base64url string.

    Args:
        value: The string to encode.
        max_len: Maximum length for the encoded result.

    Returns:
        Base64url encoded string, or None if it would exceed max_len.
    """
    if value is None:
        return None
    raw = value.encode("utf-8", errors="replace")
    enc = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    if len(enc) > max_len:
        return None
    return enc


def split_categories_tag(value: str) -> list[str]:
    """
    Parse categories from tag value (backward-compatible).

    Handles both old format (cat1+cat2) and new format with scores (cat1:0.85+cat2:0.72).

    Args:
        value: The categories tag value.

    Returns:
        List of category names.
    """
    if not value:
        return []
    if "+" in value:
        parts = value.split("+")
    elif "," in value:
        parts = value.split(",")
    else:
        parts = [value]

    categories = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            cat_name = part.split(":")[0].strip()
            if cat_name:
                categories.append(cat_name)
        else:
            categories.append(part)
    return categories


def parse_category_scores(value: str) -> dict[str, float]:
    """
    Parse category scores from tag value.

    Format: cat1:0.85+cat2:0.72+cat3:0.45

    Args:
        value: The categories tag value with scores.

    Returns:
        Dict mapping category names to confidence scores.
    """
    scores = {}
    if not value:
        return scores

    if "+" in value:
        parts = value.split("+")
    elif "," in value:
        parts = value.split(",")
    else:
        parts = [value]

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            try:
                cat_name, score_str = part.split(":", 1)
                cat_name = cat_name.strip()
                score = float(score_str.strip())
                if cat_name:
                    scores[cat_name] = max(0.0, min(1.0, score))
            except (ValueError, TypeError):
                if part:
                    scores[part] = 0.0
        else:
            scores[part] = 0.0

    return scores


def format_categories_with_scores(
    categories: list[str],
    category_scores: dict[str, float],
) -> str:
    """
    Format categories with their confidence scores for storage.

    Format: cat1:0.85+cat2:0.72+cat3:0.45

    Args:
        categories: List of category names.
        category_scores: Dict of per-category confidence scores.

    Returns:
        Formatted string for storage in tags.
    """
    if not categories:
        return ""

    scored_cats = []
    for cat in categories:
        score = category_scores.get(cat, 0.0)
        scored_cats.append((cat, score))

    scored_cats.sort(key=lambda x: x[1], reverse=True)
    parts = [f"{cat}:{score:.2f}" for cat, score in scored_cats]
    return "+".join(parts)


def infer_file_type_from_name(name: str) -> str:
    """
    Infer file type (extension) from filename.

    Args:
        name: The filename.

    Returns:
        File extension without dot, or 'unknown'.
    """
    ext = os.path.splitext(name)[1].lower()
    if not ext:
        return "unknown"

    ext_no_dot = ext[1:] if ext.startswith(".") else ext
    if not ext_no_dot:
        return "unknown"

    if ext_no_dot == "markdown":
        return "md"

    return ext_no_dot


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Parse float safely (guards NaN/inf/invalid values).

    Args:
        value: Value to parse as float.
        default: Default value if parsing fails.

    Returns:
        Parsed float or default.
    """
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return float(default)
        return f
    except Exception:
        return float(default)


def format_confidence_tag(confidence: Any) -> str:
    """
    Format confidence for storage as a tag value.

    Args:
        confidence: Confidence value (any type).

    Returns:
        Formatted confidence string.
    """
    c = safe_float(confidence, default=0.0)
    c = max(0.0, min(1.0, c))
    s = f"{c:.4f}".rstrip("0").rstrip(".")
    return s or "0"


def extract_document_id_from_key(silver_key: str) -> str:
    """
    Extract stable document_id from a Silver key.

    Args:
        silver_key: The Silver layer object key.

    Returns:
        Extracted document ID.
    """
    try:
        parts = silver_key.split("/", 1)
        if len(parts) <= 1:
            return silver_key
        name_part = parts[1]
        if "_" not in name_part:
            return os.path.splitext(name_part)[0]
        underscore_idx = name_part.find("_")
        if underscore_idx > 0:
            return name_part[:underscore_idx]
        return os.path.splitext(name_part)[0]
    except Exception:
        return silver_key


def extract_filename_from_key(silver_key: str) -> str:
    """
    Extract original filename from silver_key.

    Args:
        silver_key: The Silver layer object key.

    Returns:
        Extracted filename.
    """
    try:
        parts = silver_key.split("/", 1)
        if len(parts) > 1:
            name_part = parts[1]
            underscore_idx = name_part.find("_")
            if underscore_idx > 0:
                return name_part[underscore_idx + 1:]
            return os.path.basename(name_part)
        return os.path.basename(silver_key)
    except Exception:
        return os.path.basename(silver_key)


def normalize_tags_dict(tags: Any) -> dict[str, str]:
    """
    Normalize MinIO SDK tags object to a plain dict.

    Args:
        tags: Tags object from MinIO SDK.

    Returns:
        Plain dict of tag key-value pairs.
    """
    if not tags:
        return {}

    if isinstance(tags, dict):
        return {str(k): str(v) for k, v in tags.items()}
    if hasattr(tags, "items"):
        try:
            return {str(k): str(v) for k, v in tags.items()}
        except Exception:
            pass
    if hasattr(tags, "keys"):
        try:
            return {str(k): str(tags[k]) for k in tags.keys()}
        except Exception:
            pass
    for attr in ("tags", "_tags"):
        if hasattr(tags, attr):
            raw = getattr(tags, attr)
            if isinstance(raw, dict):
                return {str(k): str(v) for k, v in raw.items()}

    return {}
