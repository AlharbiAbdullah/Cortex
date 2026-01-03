"""Database connection and service for Cortex."""

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Generator

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

from cortex.database.models import (
    Base,
    CategoryEmbeddingCache,
    MetadataContextStore,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cortex_db"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    pool_timeout: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get cached database settings."""
    return DatabaseSettings()


class DatabaseService:
    """
    Database service for PostgreSQL operations.

    Provides methods for managing metadata contexts, routing decisions,
    and category embedding caches.
    """

    def __init__(self, settings: DatabaseSettings | None = None):
        """
        Initialize database service.

        Args:
            settings: Database settings. If None, loads from environment.
        """
        self.settings = settings or get_db_settings()
        self.engine = None
        self.SessionLocal = None
        self._connect()

    def _get_database_url(self) -> str:
        """Build database URL from settings."""
        return (
            f"postgresql://{self.settings.db_user}:{self.settings.db_password}"
            f"@{self.settings.db_host}:{self.settings.db_port}/{self.settings.db_name}"
        )

    def _connect(self) -> None:
        """Establish database connection with connection pooling."""
        try:
            self.engine = create_engine(
                self._get_database_url(),
                pool_size=self.settings.pool_size,
                max_overflow=self.settings.max_overflow,
                pool_pre_ping=True,
                pool_recycle=self.settings.pool_recycle,
                pool_timeout=self.settings.pool_timeout,
            )
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            Base.metadata.create_all(bind=self.engine)
            logger.info(
                f"Database connected (pool_size={self.settings.pool_size}, "
                f"max_overflow={self.settings.max_overflow})"
            )
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")

    def get_db(self) -> Generator[Session, None, None]:
        """
        Generator for FastAPI dependency injection.

        Yields:
            Database session.

        Raises:
            Exception: If database is not initialized.
        """
        if not self.SessionLocal:
            self._connect()

        if not self.SessionLocal:
            raise Exception("Database not initialized")

        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with auto-commit/rollback.

        Yields:
            Database session.

        Example:
            with db_service.get_session() as session:
                result = session.query(Model).all()
        """
        if not self.SessionLocal:
            self._connect()
        if not self.SessionLocal:
            raise Exception("Database not initialized")

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # --- Metadata Context Store Methods ---

    def get_all_contexts(self, limit: int = 100) -> list[dict]:
        """
        Get all metadata contexts ordered by usage count.

        Args:
            limit: Maximum number of contexts to return.

        Returns:
            List of context dictionaries.
        """
        with self.get_session() as session:
            contexts = (
                session.query(MetadataContextStore)
                .order_by(MetadataContextStore.usage_count.desc())
                .limit(limit)
                .all()
            )
            return [ctx.to_dict() for ctx in contexts]

    def get_contexts_by_type(self, context_type: str, limit: int = 50) -> list[dict]:
        """
        Get contexts filtered by type.

        Args:
            context_type: One of 'predefined', 'learned', 'human_verified'.
            limit: Maximum number of contexts to return.

        Returns:
            List of context dictionaries.
        """
        with self.get_session() as session:
            contexts = (
                session.query(MetadataContextStore)
                .filter(MetadataContextStore.context_type == context_type)
                .order_by(MetadataContextStore.usage_count.desc())
                .limit(limit)
                .all()
            )
            return [ctx.to_dict() for ctx in contexts]

    def get_contexts_by_category(self, category: str, limit: int = 20) -> list[dict]:
        """
        Get all contexts for a specific category.

        Args:
            category: Category name.
            limit: Maximum number of contexts to return.

        Returns:
            List of context dictionaries.
        """
        with self.get_session() as session:
            contexts = (
                session.query(MetadataContextStore)
                .filter(MetadataContextStore.category == category)
                .order_by(MetadataContextStore.usage_count.desc())
                .limit(limit)
                .all()
            )
            return [ctx.to_dict() for ctx in contexts]

    def get_predefined_contexts(self) -> list[dict]:
        """Get all predefined contexts (handles cold start)."""
        return self.get_contexts_by_type("predefined")

    def get_top_learned_contexts(self, limit: int = 10) -> list[dict]:
        """
        Get top learned contexts by usage count.

        Args:
            limit: Maximum number of contexts to return.

        Returns:
            List of context dictionaries.
        """
        with self.get_session() as session:
            contexts = (
                session.query(MetadataContextStore)
                .filter(
                    MetadataContextStore.context_type.in_(["learned", "human_verified"])
                )
                .order_by(MetadataContextStore.usage_count.desc())
                .limit(limit)
                .all()
            )
            return [ctx.to_dict() for ctx in contexts]

    def save_predefined_context(
        self, category: str, context_text: str, sample_content: str | None = None
    ) -> int:
        """
        Save a predefined context (used by seeding script).

        Args:
            category: Category name.
            context_text: Description of the category.
            sample_content: Optional example content.

        Returns:
            Context ID of created or updated MetadataContextStore.
        """
        with self.get_session() as session:
            existing = (
                session.query(MetadataContextStore)
                .filter(
                    MetadataContextStore.category == category,
                    MetadataContextStore.context_type == "predefined",
                )
                .first()
            )

            if existing:
                existing.context_text = context_text
                if sample_content:
                    existing.sample_content = sample_content
                existing.updated_at = datetime.now(timezone.utc)
                session.flush()
                context_id = existing.context_id
                return context_id

            context = MetadataContextStore(
                category=category,
                context_type="predefined",
                context_text=context_text,
                sample_content=sample_content,
                verified=True,
            )
            session.add(context)
            session.flush()
            context_id = context.context_id
            return context_id

    def save_learned_context(
        self,
        category: str,
        context_text: str,
        sample_content: str,
        source_document_key: str | None,
        confidence: float,
    ) -> MetadataContextStore | None:
        """
        Save a learned context from successful classification.

        Args:
            category: Category name.
            context_text: Learned context description.
            sample_content: Sample content from document.
            source_document_key: MinIO Silver key of source document.
            confidence: Confidence score when learned.

        Returns:
            Created MetadataContextStore or None on error.
        """
        try:
            with self.get_session() as session:
                context = MetadataContextStore(
                    category=category,
                    context_type="learned",
                    context_text=context_text,
                    sample_content=sample_content[:1000] if sample_content else None,
                    source_document_key=source_document_key,
                    confidence_when_learned=confidence,
                    verified=False,
                )
                session.add(context)
                session.flush()
                logger.info(
                    f"Saved learned context for '{category}' from {source_document_key}"
                )
                return context
        except Exception as e:
            logger.error(f"Error saving learned context: {e}")
            return None

    def update_context_usage(self, context_ids: list[int]) -> None:
        """
        Increment usage count for contexts that helped with routing.

        Args:
            context_ids: List of context IDs to update.
        """
        if not context_ids:
            return

        try:
            with self.get_session() as session:
                contexts = (
                    session.query(MetadataContextStore)
                    .filter(MetadataContextStore.context_id.in_(context_ids))
                    .all()
                )
                for ctx in contexts:
                    ctx.usage_count += 1
                    ctx.last_used_at = datetime.now(timezone.utc)
        except Exception as e:
            logger.error(f"Error updating context usage: {e}")

    # --- Routing Decision Methods ---

    def save_routing_decision(
        self,
        document_key: str,
        classification: str,
        confidence_score: float,
        reasoning: str,
        pipeline_routed_to: str,
        context_ids_used: list[int] | None = None,
        additional_categories: list[str] | None = None,
        category_scores: dict[str, float] | None = None,
    ) -> RoutingDecision:
        """
        Save a routing decision for auditing and learning.

        Args:
            document_key: MinIO Silver key of the document.
            classification: Assigned category.
            confidence_score: Classification confidence.
            reasoning: LLM reasoning for classification.
            pipeline_routed_to: Target pipeline.
            context_ids_used: IDs of contexts used in classification.
            additional_categories: Additional categories (not stored, for future use).
            category_scores: Per-category scores (not stored, for future use).

        Returns:
            Created RoutingDecision.
        """
        with self.get_session() as session:
            decision = RoutingDecision(
                document_key=document_key,
                classification=classification,
                confidence_score=confidence_score,
                reasoning=reasoning,
                pipeline_routed_to=pipeline_routed_to,
                context_ids_used=(
                    ",".join(map(str, context_ids_used)) if context_ids_used else None
                ),
                processing_status="pending",
            )
            session.add(decision)
            session.flush()
            return decision

    def get_routing_decisions(
        self, document_key: str | None = None, limit: int = 50
    ) -> list[dict]:
        """
        Get routing decisions, optionally filtered by document key.

        Args:
            document_key: Optional MinIO Silver key filter.
            limit: Maximum number of decisions to return.

        Returns:
            List of decision dictionaries.
        """
        with self.get_session() as session:
            query = session.query(RoutingDecision)
            if document_key:
                query = query.filter(RoutingDecision.document_key == document_key)
            decisions = (
                query.order_by(RoutingDecision.created_at.desc()).limit(limit).all()
            )
            return [d.to_dict() for d in decisions]

    def get_low_confidence_decisions(
        self, threshold: float = 0.5, limit: int = 20
    ) -> list[dict]:
        """
        Get routing decisions with low confidence for human review.

        Args:
            threshold: Confidence threshold (decisions below this are returned).
            limit: Maximum number of decisions to return.

        Returns:
            List of decision dictionaries.
        """
        with self.get_session() as session:
            decisions = (
                session.query(RoutingDecision)
                .filter(
                    RoutingDecision.confidence_score < threshold,
                    RoutingDecision.human_override == False,  # noqa: E712
                )
                .order_by(RoutingDecision.created_at.desc())
                .limit(limit)
                .all()
            )
            return [d.to_dict() for d in decisions]

    def get_category_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get statistics about document classifications.

        Returns:
            Dictionary mapping categories to their stats (count, avg_confidence).
        """
        with self.get_session() as session:
            stats = (
                session.query(
                    RoutingDecision.classification,
                    func.count(RoutingDecision.decision_id).label("count"),
                    func.avg(RoutingDecision.confidence_score).label("avg_confidence"),
                )
                .group_by(RoutingDecision.classification)
                .all()
            )
            return {
                stat.classification: {
                    "count": stat.count,
                    "avg_confidence": (
                        round(stat.avg_confidence, 3) if stat.avg_confidence else 0
                    ),
                }
                for stat in stats
            }

    # --- Category Embedding Cache Methods ---

    def get_category_embeddings(self) -> dict[str, list[float]]:
        """
        Load all cached category embeddings from the database.

        Returns:
            Dict mapping category names to embedding vectors.
        """
        with self.get_session() as session:
            caches = session.query(CategoryEmbeddingCache).all()
            result = {}
            for cache in caches:
                embedding = cache.get_embedding_list()
                if embedding:
                    result[cache.category] = embedding
            return result

    def save_category_embedding(
        self,
        category: str,
        embedding: list[float],
        sample_keys: list[str],
        sample_count: int,
    ) -> CategoryEmbeddingCache:
        """
        Save or update a category embedding in the cache.

        Args:
            category: Category name.
            embedding: Embedding vector (list of floats).
            sample_keys: List of MinIO Silver keys used.
            sample_count: Number of documents used.

        Returns:
            Saved CategoryEmbeddingCache.
        """
        with self.get_session() as session:
            existing = (
                session.query(CategoryEmbeddingCache)
                .filter(CategoryEmbeddingCache.category == category)
                .first()
            )

            embedding_json = json.dumps(embedding)
            sample_keys_json = json.dumps(sample_keys)

            if existing:
                existing.embedding = embedding_json
                existing.sample_keys = sample_keys_json
                existing.sample_count = sample_count
                existing.updated_at = datetime.now(timezone.utc)
                session.flush()
                logger.info(f"Updated embedding cache for '{category}' ({sample_count} samples)")
                return existing

            cache = CategoryEmbeddingCache(
                category=category,
                embedding=embedding_json,
                sample_keys=sample_keys_json,
                sample_count=sample_count,
            )
            session.add(cache)
            session.flush()
            logger.info(f"Created embedding cache for '{category}' ({sample_count} samples)")
            return cache

    def update_category_embedding_incremental(
        self,
        category: str,
        new_embedding: list[float],
        new_sample_key: str,
        weight: float = 0.1,
    ) -> CategoryEmbeddingCache | None:
        """
        Incrementally update a category embedding with exponential moving average.

        Args:
            category: Category name.
            new_embedding: New document's embedding vector.
            new_sample_key: MinIO Silver key of the new document.
            weight: Weight for new embedding (0.1 = 10% influence).

        Returns:
            Updated CategoryEmbeddingCache or None if error.
        """
        try:
            with self.get_session() as session:
                existing = (
                    session.query(CategoryEmbeddingCache)
                    .filter(CategoryEmbeddingCache.category == category)
                    .first()
                )

                if not existing:
                    return self.save_category_embedding(
                        category=category,
                        embedding=new_embedding,
                        sample_keys=[new_sample_key],
                        sample_count=1,
                    )

                old_embedding = existing.get_embedding_list()

                if not old_embedding or len(old_embedding) != len(new_embedding):
                    existing.embedding = json.dumps(new_embedding)
                    existing.sample_count = 1
                    existing.sample_keys = json.dumps([new_sample_key])
                    existing.updated_at = datetime.now(timezone.utc)
                    session.flush()
                    return existing

                # Compute exponential moving average
                updated_embedding = [
                    (1 - weight) * old + weight * new
                    for old, new in zip(old_embedding, new_embedding)
                ]

                # Update sample keys (keep last 10)
                try:
                    sample_keys = json.loads(existing.sample_keys or "[]")
                except (json.JSONDecodeError, TypeError):
                    sample_keys = []

                if new_sample_key not in sample_keys:
                    sample_keys.append(new_sample_key)
                    sample_keys = sample_keys[-10:]

                existing.embedding = json.dumps(updated_embedding)
                existing.sample_keys = json.dumps(sample_keys)
                existing.sample_count = existing.sample_count + 1
                existing.updated_at = datetime.now(timezone.utc)
                session.flush()

                logger.info(
                    f"Incrementally updated embedding for '{category}' "
                    f"({existing.sample_count} samples)"
                )
                return existing

        except Exception as e:
            logger.error(f"Error updating category embedding: {e}")
            return None

    def is_embedding_cache_stale(self, max_age_hours: int = 24) -> bool:
        """
        Check if the category embedding cache is stale.

        Args:
            max_age_hours: Maximum age in hours before cache is stale.

        Returns:
            True if cache is empty or oldest entry exceeds max_age_hours.
        """
        with self.get_session() as session:
            count = session.query(CategoryEmbeddingCache).count()
            if count == 0:
                return True

            oldest = (
                session.query(CategoryEmbeddingCache)
                .order_by(CategoryEmbeddingCache.updated_at.asc())
                .first()
            )

            if not oldest or not oldest.updated_at:
                return True

            age = datetime.now(timezone.utc) - oldest.updated_at
            return age > timedelta(hours=max_age_hours)


# Singleton instance
_db_service: DatabaseService | None = None


def get_database_service() -> DatabaseService:
    """Get or create the singleton database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
