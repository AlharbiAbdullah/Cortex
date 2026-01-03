"""SQLAlchemy ORM models for Cortex database."""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MetadataContextStore(Base):
    """
    Stores category contexts for smart routing.

    Types:
    - 'predefined': System-defined category descriptions (always available)
    - 'learned': Learned from successful document classifications
    - 'human_verified': Human-reviewed and verified contexts
    """

    __tablename__ = "metadata_context_store"

    context_id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    context_type = Column(String(50), nullable=False, index=True)
    context_text = Column(Text, nullable=False)
    sample_content = Column(Text, nullable=True)

    # Learning metadata
    source_document_key = Column(String(512), nullable=True)
    confidence_when_learned = Column(Float, nullable=True)

    # Verification
    verified = Column(Boolean, default=False)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "context_id": self.context_id,
            "category": self.category,
            "context_type": self.context_type,
            "context_text": self.context_text,
            "sample_content": self.sample_content,
            "source_document_key": self.source_document_key,
            "confidence_when_learned": self.confidence_when_learned,
            "verified": self.verified,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CategoryEmbeddingCache(Base):
    """
    Caches aggregated embeddings per category from MinIO documents.

    Used by fetch_context_node for fast embedding-based classification.
    The embedding is a centroid (average) of high-confidence document embeddings
    for each category, computed from actual documents in MinIO Silver layer.
    """

    __tablename__ = "category_embedding_cache"

    cache_id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, unique=True, index=True)
    embedding = Column(Text, nullable=False)  # JSON array of floats (centroid)
    sample_count = Column(Integer, default=0)
    sample_keys = Column(Text, nullable=True)  # JSON array of silver_keys

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "cache_id": self.cache_id,
            "category": self.category,
            "embedding": self.embedding,
            "sample_count": self.sample_count,
            "sample_keys": self.sample_keys,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_embedding_list(self) -> list[float]:
        """Parse and return embedding as list of floats."""
        try:
            return json.loads(self.embedding)
        except (json.JSONDecodeError, TypeError):
            return []


class RoutingDecision(Base):
    """
    Tracks routing decisions for documents.

    Used for learning and auditing classification history.
    """

    __tablename__ = "routing_decisions"

    decision_id = Column(Integer, primary_key=True, index=True)
    document_key = Column(String(512), nullable=False, index=True)

    # Classification result
    classification = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)

    # Context used for decision
    context_ids_used = Column(String(500), nullable=True)

    # Pipeline routing
    pipeline_routed_to = Column(String(100), nullable=False)

    # Outcome tracking
    processing_status = Column(String(50), default="pending")
    human_override = Column(Boolean, default=False)
    corrected_classification = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "decision_id": self.decision_id,
            "document_key": self.document_key,
            "classification": self.classification,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "context_ids_used": self.context_ids_used,
            "pipeline_routed_to": self.pipeline_routed_to,
            "processing_status": self.processing_status,
            "human_override": self.human_override,
            "corrected_classification": self.corrected_classification,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
