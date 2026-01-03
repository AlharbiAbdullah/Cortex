"""
Document Comparison Service.

Provides document comparison capabilities including semantic similarity,
text diff, and change summary generation.
"""

import difflib
import logging
import re
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from cortex.agents.llm import get_llm
from cortex.agents.smart_router.embeddings import embed_texts

logger = logging.getLogger(__name__)


class ComparisonSettings(BaseSettings):
    """Comparison service configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    comparison_model: str = "qwen2.5:14b"
    similarity_threshold: float = 0.85
    max_diff_lines: int = 100


@lru_cache()
def get_comparison_settings() -> ComparisonSettings:
    """Get cached comparison settings."""
    return ComparisonSettings()


class DiffChange(BaseModel):
    """A single change in the diff."""

    type: str = Field(..., description="Change type: added, removed, modified")
    line_number: int = Field(..., description="Line number in the document")
    content: str = Field(..., description="Changed content")
    context: str = Field(default="", description="Surrounding context")


class ComparisonResult(BaseModel):
    """Result of document comparison."""

    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Semantic similarity (0-1)",
    )
    is_similar: bool = Field(..., description="Whether documents are similar")
    diff_summary: str = Field(..., description="Summary of differences")
    changes: list[DiffChange] = Field(
        default_factory=list,
        description="List of specific changes",
    )
    added_count: int = Field(default=0, description="Number of added lines")
    removed_count: int = Field(default=0, description="Number of removed lines")
    modified_count: int = Field(default=0, description="Number of modified lines")
    word_count_diff: int = Field(default=0, description="Difference in word count")
    key_differences: list[str] = Field(
        default_factory=list,
        description="Key semantic differences",
    )


class DocumentVersion(BaseModel):
    """Metadata for a document version."""

    version_id: str = Field(..., description="Version identifier")
    silver_key: str = Field(..., description="Silver layer key")
    timestamp: str = Field(..., description="Version timestamp")
    word_count: int = Field(default=0, description="Word count")
    summary: str = Field(default="", description="Brief version summary")


class ComparisonService:
    """
    Service for comparing documents.

    Provides:
    - Semantic similarity scoring using embeddings
    - Text-based diff highlighting
    - Change summary generation
    - Version comparison
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialize the comparison service.

        Args:
            model_name: LLM model to use. Defaults to settings.
        """
        self._settings = get_comparison_settings()
        self._model_name = model_name or self._settings.comparison_model
        self._llm = get_llm(model=self._model_name, temperature=0.2)

    async def compare(
        self,
        text1: str,
        text2: str,
        generate_summary: bool = True,
    ) -> ComparisonResult:
        """
        Compare two documents.

        Args:
            text1: First document text (original/baseline).
            text2: Second document text (new/modified).
            generate_summary: Whether to generate LLM summary of differences.

        Returns:
            ComparisonResult with similarity score and differences.
        """
        if not text1 or not text2:
            return ComparisonResult(
                similarity_score=0.0,
                is_similar=False,
                diff_summary="One or both documents are empty.",
            )

        # Calculate semantic similarity
        similarity_score = await self._calculate_similarity(text1, text2)
        is_similar = similarity_score >= self._settings.similarity_threshold

        # Generate diff
        changes, added, removed, modified = self._generate_diff(text1, text2)

        # Calculate word count difference
        word_count_diff = len(text2.split()) - len(text1.split())

        # Generate summary of differences
        diff_summary = ""
        key_differences = []

        if generate_summary and not is_similar:
            diff_summary, key_differences = await self._summarize_differences(
                text1,
                text2,
                changes,
            )
        elif is_similar:
            diff_summary = "Documents are semantically similar with minimal differences."

        return ComparisonResult(
            similarity_score=round(similarity_score, 4),
            is_similar=is_similar,
            diff_summary=diff_summary,
            changes=changes[: self._settings.max_diff_lines],
            added_count=added,
            removed_count=removed,
            modified_count=modified,
            word_count_diff=word_count_diff,
            key_differences=key_differences,
        )

    async def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        Uses embedding cosine similarity.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Similarity score between 0 and 1.
        """
        try:
            # Truncate for embedding
            max_chars = 8000
            t1 = text1[:max_chars]
            t2 = text2[:max_chars]

            embeddings = embed_texts([t1, t2])
            if len(embeddings) < 2:
                return 0.0

            # Cosine similarity
            emb1 = embeddings[0]
            emb2 = embeddings[1]

            dot_product = sum(a * b for a, b in zip(emb1, emb2))
            norm1 = sum(a * a for a in emb1) ** 0.5
            norm2 = sum(b * b for b in emb2) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            # Fallback to simple text similarity
            return difflib.SequenceMatcher(None, text1, text2).ratio()

    def _generate_diff(
        self,
        text1: str,
        text2: str,
    ) -> tuple[list[DiffChange], int, int, int]:
        """
        Generate line-by-line diff between two texts.

        Args:
            text1: Original text.
            text2: Modified text.

        Returns:
            Tuple of (changes list, added count, removed count, modified count).
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        differ = difflib.unified_diff(
            lines1,
            lines2,
            lineterm="",
            n=1,
        )

        changes = []
        added_count = 0
        removed_count = 0
        modified_count = 0
        current_line = 0

        for line in differ:
            if line.startswith("@@"):
                # Parse line number from @@ -start,count +start,count @@
                match = re.search(r"\+(\d+)", line)
                if match:
                    current_line = int(match.group(1))
                continue
            elif line.startswith("---") or line.startswith("+++"):
                continue
            elif line.startswith("-"):
                changes.append(
                    DiffChange(
                        type="removed",
                        line_number=current_line,
                        content=line[1:],
                        context="",
                    )
                )
                removed_count += 1
            elif line.startswith("+"):
                changes.append(
                    DiffChange(
                        type="added",
                        line_number=current_line,
                        content=line[1:],
                        context="",
                    )
                )
                added_count += 1
                current_line += 1
            else:
                current_line += 1

        # Detect modifications (adjacent add/remove pairs)
        i = 0
        while i < len(changes) - 1:
            if (
                changes[i].type == "removed"
                and changes[i + 1].type == "added"
                and abs(changes[i].line_number - changes[i + 1].line_number) <= 1
            ):
                # Convert to modification
                changes[i] = DiffChange(
                    type="modified",
                    line_number=changes[i].line_number,
                    content=f"'{changes[i].content}' → '{changes[i + 1].content}'",
                    context="",
                )
                changes.pop(i + 1)
                added_count -= 1
                removed_count -= 1
                modified_count += 1
            i += 1

        return changes, added_count, removed_count, modified_count

    async def _summarize_differences(
        self,
        text1: str,
        text2: str,
        changes: list[DiffChange],
    ) -> tuple[str, list[str]]:
        """
        Generate a summary of differences using LLM.

        Args:
            text1: Original text.
            text2: Modified text.
            changes: List of detected changes.

        Returns:
            Tuple of (summary string, list of key differences).
        """
        # Build change summary for context
        change_summary = []
        for change in changes[:20]:
            change_summary.append(f"- {change.type.upper()}: {change.content[:100]}")

        prompt = f"""Compare these two document versions and summarize the key differences.

ORIGINAL (first 3000 chars):
{text1[:3000]}

MODIFIED (first 3000 chars):
{text2[:3000]}

DETECTED CHANGES:
{chr(10).join(change_summary)}

Provide:
1. A brief summary of the overall changes (2-3 sentences)
2. 3-5 key differences as bullet points

Format your response as:
SUMMARY: [your summary]

KEY DIFFERENCES:
• [difference 1]
• [difference 2]
• [difference 3]"""

        try:
            response = await self._llm.ainvoke(prompt)

            # Parse response
            summary = ""
            key_differences = []

            if "SUMMARY:" in response:
                parts = response.split("KEY DIFFERENCES:")
                summary = parts[0].replace("SUMMARY:", "").strip()

                if len(parts) > 1:
                    diff_lines = parts[1].strip().split("\n")
                    for line in diff_lines:
                        line = re.sub(r"^[•\-\*\d\.]+\s*", "", line.strip())
                        if line and len(line) > 10:
                            key_differences.append(line)

            return summary, key_differences[:5]

        except Exception as e:
            logger.error(f"Difference summarization failed: {e}")
            return (
                f"Found {len(changes)} changes between documents.",
                [],
            )

    async def compare_versions(
        self,
        versions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Compare multiple versions of a document.

        Args:
            versions: List of version dicts with 'version_id' and 'text' keys.

        Returns:
            List of comparison results between consecutive versions.
        """
        if len(versions) < 2:
            return []

        results = []
        for i in range(len(versions) - 1):
            v1 = versions[i]
            v2 = versions[i + 1]

            comparison = await self.compare(
                v1.get("text", ""),
                v2.get("text", ""),
            )

            results.append({
                "from_version": v1.get("version_id"),
                "to_version": v2.get("version_id"),
                "comparison": comparison.model_dump(),
            })

        return results

    def quick_diff(self, text1: str, text2: str) -> dict[str, Any]:
        """
        Generate a quick diff without LLM processing.

        Args:
            text1: Original text.
            text2: Modified text.

        Returns:
            Dict with basic diff statistics.
        """
        changes, added, removed, modified = self._generate_diff(text1, text2)

        # Simple text-based similarity
        ratio = difflib.SequenceMatcher(None, text1, text2).ratio()

        return {
            "similarity_ratio": round(ratio, 4),
            "added_lines": added,
            "removed_lines": removed,
            "modified_lines": modified,
            "total_changes": len(changes),
            "word_count_diff": len(text2.split()) - len(text1.split()),
        }


# Singleton instance
_comparison_service: ComparisonService | None = None


def get_comparison_service() -> ComparisonService:
    """Get or create the singleton comparison service."""
    global _comparison_service
    if _comparison_service is None:
        _comparison_service = ComparisonService()
    return _comparison_service
