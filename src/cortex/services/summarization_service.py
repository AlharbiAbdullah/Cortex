"""
Document Summarization Service.

Provides extractive and abstractive summarization capabilities
for documents using LLM and NLP techniques.
"""

import logging
import re
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from cortex.agents.llm import get_llm

logger = logging.getLogger(__name__)


class SummarizationSettings(BaseSettings):
    """Summarization service configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    summarization_model: str = "qwen2.5:14b"
    max_summary_length: int = 500
    max_input_chars: int = 15000
    extractive_sentence_count: int = 5


@lru_cache()
def get_summarization_settings() -> SummarizationSettings:
    """Get cached summarization settings."""
    return SummarizationSettings()


class SummaryResult(BaseModel):
    """Result of document summarization."""

    executive_summary: str = Field(..., description="High-level executive summary")
    key_points: list[str] = Field(default_factory=list, description="Key bullet points")
    entities: list[dict[str, str]] = Field(
        default_factory=list,
        description="Extracted entities with type and name",
    )
    action_items: list[str] = Field(
        default_factory=list,
        description="Detected action items or tasks",
    )
    extractive_summary: str = Field(
        default="",
        description="Key sentences extracted from document",
    )
    word_count: int = Field(default=0, description="Original document word count")
    compression_ratio: float = Field(
        default=0.0,
        description="Ratio of summary to original length",
    )


class SummarizationService:
    """
    Service for generating document summaries.

    Provides multiple summarization modes:
    - Executive summary (abstractive, LLM-generated)
    - Key points extraction
    - Entity extraction
    - Action item detection
    - Extractive summarization (key sentences)
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialize the summarization service.

        Args:
            model_name: LLM model to use. Defaults to settings.
        """
        self._settings = get_summarization_settings()
        self._model_name = model_name or self._settings.summarization_model
        self._llm = get_llm(model=self._model_name, temperature=0.3)

    async def summarize(
        self,
        text: str,
        include_entities: bool = True,
        include_actions: bool = True,
        include_extractive: bool = True,
    ) -> SummaryResult:
        """
        Generate a comprehensive summary of the document.

        Args:
            text: Document text to summarize.
            include_entities: Whether to extract entities.
            include_actions: Whether to detect action items.
            include_extractive: Whether to include extractive summary.

        Returns:
            SummaryResult with all summary components.
        """
        if not text or len(text.strip()) < 50:
            return SummaryResult(
                executive_summary="Document too short to summarize.",
                word_count=len(text.split()),
            )

        # Truncate if too long
        truncated_text = text[: self._settings.max_input_chars]
        word_count = len(text.split())

        # Generate components in parallel conceptually (sequential for simplicity)
        executive_summary = await self._generate_executive_summary(truncated_text)
        key_points = await self._extract_key_points(truncated_text)

        entities = []
        if include_entities:
            entities = await self._extract_entities(truncated_text)

        action_items = []
        if include_actions:
            action_items = await self._detect_action_items(truncated_text)

        extractive_summary = ""
        if include_extractive:
            extractive_summary = self._extractive_summarize(
                truncated_text,
                num_sentences=self._settings.extractive_sentence_count,
            )

        # Calculate compression ratio
        summary_words = len(executive_summary.split())
        compression_ratio = summary_words / word_count if word_count > 0 else 0.0

        return SummaryResult(
            executive_summary=executive_summary,
            key_points=key_points,
            entities=entities,
            action_items=action_items,
            extractive_summary=extractive_summary,
            word_count=word_count,
            compression_ratio=round(compression_ratio, 3),
        )

    async def _generate_executive_summary(self, text: str) -> str:
        """
        Generate an executive summary using LLM.

        Args:
            text: Document text.

        Returns:
            Executive summary string.
        """
        prompt = f"""Summarize the following document in a concise executive summary.
Focus on the main purpose, key findings, and conclusions.
Keep the summary under {self._settings.max_summary_length} words.

DOCUMENT:
{text}

EXECUTIVE SUMMARY:"""

        try:
            response = await self._llm.ainvoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            return "Summary generation failed."

    async def _extract_key_points(self, text: str) -> list[str]:
        """
        Extract key bullet points from the document.

        Args:
            text: Document text.

        Returns:
            List of key point strings.
        """
        prompt = f"""Extract 3-7 key points from this document as bullet points.
Each point should be a single, concise sentence.

DOCUMENT:
{text}

KEY POINTS (one per line, starting with •):"""

        try:
            response = await self._llm.ainvoke(prompt)
            lines = response.strip().split("\n")
            points = []
            for line in lines:
                line = line.strip()
                # Remove bullet prefixes
                line = re.sub(r"^[•\-\*\d\.]+\s*", "", line)
                if line and len(line) > 10:
                    points.append(line)
            return points[:7]  # Max 7 points
        except Exception as e:
            logger.error(f"Key points extraction failed: {e}")
            return []

    async def _extract_entities(self, text: str) -> list[dict[str, str]]:
        """
        Extract named entities from the document.

        Args:
            text: Document text.

        Returns:
            List of entity dicts with 'type' and 'name' keys.
        """
        prompt = f"""Extract named entities from this document.
Categories: PERSON, ORGANIZATION, LOCATION, DATE, MONEY, PRODUCT

DOCUMENT:
{text[:5000]}

List entities as TYPE: NAME (one per line):"""

        try:
            response = await self._llm.ainvoke(prompt)
            entities = []
            seen = set()

            for line in response.strip().split("\n"):
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        entity_type = parts[0].strip().upper()
                        entity_name = parts[1].strip()

                        # Clean up and deduplicate
                        entity_name = re.sub(r"^[\-\*•\d\.]+\s*", "", entity_name)
                        key = f"{entity_type}:{entity_name.lower()}"

                        if (
                            entity_name
                            and len(entity_name) > 1
                            and key not in seen
                            and entity_type
                            in [
                                "PERSON",
                                "ORGANIZATION",
                                "LOCATION",
                                "DATE",
                                "MONEY",
                                "PRODUCT",
                            ]
                        ):
                            entities.append({"type": entity_type, "name": entity_name})
                            seen.add(key)

            return entities[:20]  # Max 20 entities
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []

    async def _detect_action_items(self, text: str) -> list[str]:
        """
        Detect action items and tasks from the document.

        Args:
            text: Document text.

        Returns:
            List of action item strings.
        """
        prompt = f"""Identify action items, tasks, or to-do items from this document.
Look for phrases like "must", "should", "will", "need to", "action required", etc.

DOCUMENT:
{text[:8000]}

ACTION ITEMS (one per line, starting with •):"""

        try:
            response = await self._llm.ainvoke(prompt)
            actions = []

            for line in response.strip().split("\n"):
                line = line.strip()
                line = re.sub(r"^[•\-\*\d\.]+\s*", "", line)
                if line and len(line) > 10:
                    actions.append(line)

            return actions[:10]  # Max 10 action items
        except Exception as e:
            logger.error(f"Action item detection failed: {e}")
            return []

    def _extractive_summarize(self, text: str, num_sentences: int = 5) -> str:
        """
        Extract key sentences using a simple scoring algorithm.

        Uses sentence position, length, and keyword density to score sentences.

        Args:
            text: Document text.
            num_sentences: Number of sentences to extract.

        Returns:
            Extractive summary string.
        """
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) <= num_sentences:
            return text

        # Score sentences
        scored = []
        total_sentences = len(sentences)

        for i, sentence in enumerate(sentences):
            score = 0.0
            sentence = sentence.strip()

            if len(sentence) < 20:
                continue

            # Position score (first and last sentences weighted higher)
            if i < 3:
                score += 2.0
            elif i >= total_sentences - 2:
                score += 1.5
            else:
                score += 1.0

            # Length score (prefer medium-length sentences)
            word_count = len(sentence.split())
            if 15 <= word_count <= 40:
                score += 1.5
            elif 10 <= word_count <= 50:
                score += 1.0

            # Keyword indicators
            indicators = [
                "important",
                "key",
                "significant",
                "main",
                "primary",
                "conclusion",
                "result",
                "finding",
                "summary",
                "therefore",
                "consequently",
                "overall",
            ]
            for indicator in indicators:
                if indicator in sentence.lower():
                    score += 0.5

            scored.append((score, i, sentence))

        # Sort by score and select top sentences
        scored.sort(key=lambda x: x[0], reverse=True)
        selected = scored[:num_sentences]

        # Sort selected by original position to maintain flow
        selected.sort(key=lambda x: x[1])

        return " ".join(s[2] for s in selected)

    async def quick_summary(self, text: str, max_words: int = 100) -> str:
        """
        Generate a quick, short summary.

        Args:
            text: Document text.
            max_words: Maximum words in summary.

        Returns:
            Short summary string.
        """
        if not text or len(text.strip()) < 50:
            return "Document too short to summarize."

        prompt = f"""Summarize this document in {max_words} words or less:

{text[:8000]}

SUMMARY:"""

        try:
            response = await self._llm.ainvoke(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Quick summary failed: {e}")
            return "Summary generation failed."


# Singleton instance
_summarization_service: SummarizationService | None = None


def get_summarization_service() -> SummarizationService:
    """Get or create the singleton summarization service."""
    global _summarization_service
    if _summarization_service is None:
        _summarization_service = SummarizationService()
    return _summarization_service
