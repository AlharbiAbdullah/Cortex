"""
Query Operations for Silver Layer.

Document listing, searching, and metadata retrieval from Silver layer.
"""

import logging
from typing import Any

from minio import Minio

from cortex.services.minio.helpers import (
    extract_document_id_from_key,
    extract_filename_from_key,
    infer_file_type_from_name,
    normalize_tags_dict,
    parse_category_scores,
    safe_float,
    split_categories_tag,
)

logger = logging.getLogger(__name__)


class QueryMixin:
    """
    Mixin providing query operations for Silver layer.

    Provides document listing, searching, and metadata retrieval.
    """

    client: Minio
    silver_bucket: str

    def list_documents(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        List all documents in Silver layer with full metadata.

        Args:
            limit: Maximum number of documents to return.

        Returns:
            List of document metadata dicts.
        """
        try:
            documents = []
            count = 0
            for obj in self.client.list_objects(self.silver_bucket, prefix="docs/"):
                if count >= limit:
                    break

                tags = self.get_tags(obj.object_name)
                filename = extract_filename_from_key(obj.object_name)
                raw_categories = tags.get("categories", "")

                file_type_from_name = infer_file_type_from_name(filename)
                if file_type_from_name == "unknown":
                    file_type_from_name = infer_file_type_from_name(obj.object_name)
                file_type_tag = tags.get("file_type", "unknown")
                file_type = (
                    file_type_from_name
                    if file_type_from_name != "unknown"
                    else (file_type_tag or "unknown")
                )

                try:
                    feed_the_brain = int(tags.get("feed_the_brain", "1"))
                except (ValueError, TypeError):
                    feed_the_brain = 1

                try:
                    feed_the_graph = int(tags.get("feed_the_graph", "0"))
                except (ValueError, TypeError):
                    feed_the_graph = 0

                try:
                    tableur = int(tags.get("tableur", "0"))
                except (ValueError, TypeError):
                    tableur = 0

                categories_list = split_categories_tag(raw_categories)
                primary_category = categories_list[0] if categories_list else "unclassified"
                category_scores = parse_category_scores(raw_categories)

                documents.append({
                    "document_id": tags.get(
                        "document_id",
                        extract_document_id_from_key(obj.object_name),
                    ),
                    "silver_key": obj.object_name,
                    "filename": filename,
                    "file_type": file_type,
                    "primary_category": primary_category,
                    "categories": categories_list,
                    "category_scores": category_scores,
                    "confidence": safe_float(tags.get("confidence", 0), default=0.0),
                    "status": tags.get("status", "unknown"),
                    "upload_date": tags.get("upload_date"),
                    "relearn_date": tags.get("relearn_date"),
                    "reasoning": tags.get("reasoning", ""),
                    "feed_the_brain": feed_the_brain,
                    "feed_the_graph": feed_the_graph,
                    "tableur": tableur,
                    "size": obj.size,
                    "last_modified": (
                        obj.last_modified.isoformat() if obj.last_modified else None
                    ),
                })
                count += 1

            documents.sort(key=lambda x: x.get("upload_date") or "", reverse=True)
            return documents
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    def get_document(self, silver_key: str) -> dict[str, Any] | None:
        """
        Get detailed info about a single document.

        Args:
            silver_key: Key in Silver bucket.

        Returns:
            Document metadata dict or None.
        """
        try:
            stat = self.client.stat_object(self.silver_bucket, silver_key)
            tags = self.get_tags(silver_key)
            filename = extract_filename_from_key(silver_key)
            raw_categories = tags.get("categories", "")

            file_type_from_name = infer_file_type_from_name(filename)
            if file_type_from_name == "unknown":
                file_type_from_name = infer_file_type_from_name(silver_key)
            file_type_tag = tags.get("file_type", "unknown")
            file_type = (
                file_type_from_name
                if file_type_from_name != "unknown"
                else (file_type_tag or "unknown")
            )

            try:
                feed_the_brain = int(tags.get("feed_the_brain", "1"))
            except (ValueError, TypeError):
                feed_the_brain = 1

            try:
                feed_the_graph = int(tags.get("feed_the_graph", "0"))
            except (ValueError, TypeError):
                feed_the_graph = 0

            try:
                tableur = int(tags.get("tableur", "0"))
            except (ValueError, TypeError):
                tableur = 0

            categories_list = split_categories_tag(raw_categories)
            primary_category = categories_list[0] if categories_list else "unclassified"
            category_scores = parse_category_scores(raw_categories)

            return {
                "document_id": tags.get(
                    "document_id", extract_document_id_from_key(silver_key)
                ),
                "silver_key": silver_key,
                "filename": filename,
                "file_type": file_type,
                "primary_category": primary_category,
                "categories": categories_list,
                "category_scores": category_scores,
                "confidence": safe_float(tags.get("confidence", 0), default=0.0),
                "status": tags.get("status", "unknown"),
                "upload_date": tags.get("upload_date"),
                "relearn_date": tags.get("relearn_date"),
                "reasoning": tags.get("reasoning", ""),
                "feed_the_brain": feed_the_brain,
                "feed_the_graph": feed_the_graph,
                "tableur": tableur,
                "size": stat.size,
                "last_modified": (
                    stat.last_modified.isoformat() if stat.last_modified else None
                ),
                "content_type": stat.content_type,
            }
        except Exception as e:
            logger.error(f"Failed to get document {silver_key}: {e}")
            return None

    def query_by_category(self, category: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Query documents by category.

        Args:
            category: Category to filter by.
            limit: Max number of results.

        Returns:
            List of matching document metadata.
        """
        try:
            all_docs = self.list_documents(limit=1000)
            matching = []

            for doc in all_docs:
                if len(matching) >= limit:
                    break
                if (
                    doc.get("primary_category") == category
                    or category in doc.get("categories", [])
                ):
                    matching.append(doc)

            return matching
        except Exception as e:
            logger.error(f"Failed to query by category: {e}")
            return []

    def query_by_filename(
        self, filename_pattern: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Search documents by filename (case-insensitive partial match).

        Args:
            filename_pattern: Pattern to search for.
            limit: Max number of results.

        Returns:
            List of matching document metadata.
        """
        try:
            all_docs = self.list_documents(limit=1000)
            pattern_lower = filename_pattern.lower()
            matching = []

            for doc in all_docs:
                if len(matching) >= limit:
                    break
                filename = doc.get("filename", "").lower()
                if pattern_lower in filename:
                    matching.append(doc)

            return matching
        except Exception as e:
            logger.error(f"Failed to query by filename: {e}")
            return []

    def list_documents_for_gold(self, limit: int = 100) -> list[dict[str, Any]]:
        """List documents with tableur=1 (candidates for Gold layer)."""
        try:
            all_docs = self.list_documents(limit=1000)
            tableur_docs = [doc for doc in all_docs if doc.get("tableur") == 1]
            return tableur_docs[:limit]
        except Exception as e:
            logger.error(f"Failed to list documents for Gold: {e}")
            return []

    def list_documents_for_graph(self, limit: int = 100) -> list[dict[str, Any]]:
        """List documents with feed_the_graph=1 (candidates for Neo4j)."""
        try:
            all_docs = self.list_documents(limit=1000)
            graph_docs = [doc for doc in all_docs if doc.get("feed_the_graph") == 1]
            return graph_docs[:limit]
        except Exception as e:
            logger.error(f"Failed to list documents for graph: {e}")
            return []

    def get_distinct_categories_with_samples(
        self,
        samples_per_category: int = 5,
        min_confidence: float = 0.7,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get all distinct categories with sample documents.

        Used by fetch_context_node to build category embeddings.

        Args:
            samples_per_category: Maximum samples per category.
            min_confidence: Minimum confidence score for inclusion.

        Returns:
            Dict mapping category names to sample document lists.
        """
        try:
            all_docs = self.list_documents(limit=2000)
            categories: dict[str, list[dict[str, Any]]] = {}

            for doc in all_docs:
                status = doc.get("status", "")
                if status not in ("processed", "relearned"):
                    continue

                confidence = doc.get("confidence", 0.0)
                if confidence < min_confidence:
                    continue

                category = doc.get("primary_category", "unclassified")
                if not category or category == "unclassified":
                    continue

                if category not in categories:
                    categories[category] = []

                if len(categories[category]) < samples_per_category:
                    categories[category].append({
                        "silver_key": doc.get("silver_key"),
                        "document_id": doc.get("document_id"),
                        "filename": doc.get("filename"),
                        "file_type": doc.get("file_type"),
                        "confidence": confidence,
                        "categories": doc.get("categories", []),
                    })

            logger.info(f"Found {len(categories)} distinct categories with samples")
            return categories

        except Exception as e:
            logger.error(f"Failed to get distinct categories: {e}")
            return {}
