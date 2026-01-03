"""
Smart Router Graph Builder and Main Service Class.

This module provides the main interface for the Smart Router Agent,
including graph construction and the SmartRouterGraph service class.
"""

import logging
import os
from typing import Any

import pandas as pd
import pymupdf
from docx import Document
from langgraph.graph import END, StateGraph

from cortex.agents.smart_router.config import (
    HIGH_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
    PIPELINE_CATEGORIES,
)
from cortex.agents.smart_router.nodes import (
    classify_content_node,
    copy_to_silver_node,
    extract_text_node,
    fetch_context_node,
    init_node,
    learning_node,
    save_results_node,
)
from cortex.agents.smart_router.state import RouterState, create_initial_state
from cortex.agents.smart_router.utils import get_file_extension

logger = logging.getLogger(__name__)


def build_smart_router_graph():
    """
    Build the LangGraph for smart document routing with MinIO Data Lake.

    Flow:
    INGESTION PHASE (Bronze -> Silver = FINAL DESTINATION):
        /api/upload streams the file to Bronze first.
        Then the graph runs:
            [init] -> [extract_text] -> [fetch_context] -> [classify] -> [copy_to_silver]

    METADATA PHASE:
        -> [save] -> [learn] -> END

    Returns:
        Compiled LangGraph StateGraph.
    """
    graph = StateGraph(RouterState)

    # ==================== INGESTION PHASE NODES ====================
    graph.add_node("init", init_node)
    graph.add_node("extract_text", extract_text_node)
    graph.add_node("fetch_context", fetch_context_node)
    graph.add_node("classify", classify_content_node)
    graph.add_node("copy_to_silver", copy_to_silver_node)  # FINAL DESTINATION

    # ==================== METADATA PHASE NODES ====================
    graph.add_node("save", save_results_node)
    graph.add_node("learn", learning_node)

    # ==================== INGESTION PHASE EDGES ====================
    # Bronze -> Silver flow (Silver = FINAL DESTINATION)
    graph.set_entry_point("init")
    graph.add_edge("init", "extract_text")
    graph.add_edge("extract_text", "fetch_context")
    graph.add_edge("fetch_context", "classify")
    graph.add_edge("classify", "copy_to_silver")  # File lands in Silver here

    # ==================== METADATA PHASE EDGES ====================
    graph.add_edge("copy_to_silver", "save")
    graph.add_edge("save", "learn")
    graph.add_edge("learn", END)

    return graph.compile()


class SmartRouterGraph:
    """
    Main interface for the Smart Router Agent with MinIO Data Lake.

    Implements the Routing agentic design pattern:
    - Uploads to Bronze (landing zone)
    - Classifies content using LLM (multi-category support)
    - Copies to Silver (FINAL DESTINATION) with category tags
    - Saves routing decisions + learns from high-confidence classifications

    Example:
        router = SmartRouterGraph()
        result = await router.run(
            bronze_key="uploads/doc123.pdf",
            filename="report.pdf"
        )
        print(result["primary_category"])  # e.g., "financial_forecast"
    """

    def __init__(self) -> None:
        """Initialize the Smart Router Graph."""
        self.graph = build_smart_router_graph()
        self.categories = PIPELINE_CATEGORIES

    async def run(
        self,
        bronze_key: str,
        filename: str,
        document_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the smart router on an uploaded file.

        Flow: Bronze -> Classification -> Silver (FINAL)

        Args:
            bronze_key: MinIO Bronze key where the raw file was uploaded
                       (e.g., uploads/<id>.pdf).
            filename: Original filename.
            document_id: Stable document identifier (if omitted, derived from bronze_key).

        Returns:
            Dict with routing decision, classification, MinIO keys, and processing results.
        """
        if not bronze_key:
            return {
                "success": False,
                "status": "error",
                "error": "Missing bronze_key",
                "logs": ["Router error: missing bronze_key"],
            }

        initial_state = create_initial_state(
            bronze_key=bronze_key,
            filename=filename,
            document_id=document_id,
        )

        try:
            final_state = await self.graph.ainvoke(initial_state)

            return {
                "success": final_state.get("status") != "error",
                "file_type": final_state.get("file_type"),
                "filename": final_state.get("filename"),
                "document_id": final_state.get("document_id"),
                # MinIO keys
                "bronze_key": final_state.get("bronze_key"),
                "silver_key": final_state.get("silver_key"),
                # Multi-category classification with ensemble
                "primary_category": final_state.get("primary_category"),
                "additional_categories": final_state.get("additional_categories", []),
                "all_categories": final_state.get("all_categories", []),
                "classification": final_state.get("classification"),  # Legacy compat
                "confidence": final_state.get("confidence"),
                "category_scores": final_state.get("category_scores", {}),
                "ensemble_variance": final_state.get("ensemble_variance", {}),
                "ensemble_count": final_state.get("ensemble_count", 0),
                "reasoning": final_state.get("reasoning"),
                "routing_decision_id": final_state.get("routing_decision_id"),
                "raw_content": final_state.get("raw_content", ""),
                "status": final_state.get("status"),
                "error": final_state.get("error"),
                "logs": final_state.get("logs", []),
            }

        except Exception as e:
            logger.error(f"Smart router failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "logs": [f"Router error: {e}"],
            }

    async def classify_only(self, file_path: str) -> dict[str, Any]:
        """
        Run classification only (for re-learning existing documents).

        Does NOT upload to MinIO or create new records.

        Args:
            file_path: Path to the file to classify.

        Returns:
            Dict with classification results (primary_category, additional_categories,
            confidence).
        """
        from cortex.agents.smart_router.nodes.classification import classify_content_node
        from cortex.database.connection import DatabaseService

        # File type is the raw extension
        file_type = get_file_extension(os.path.basename(file_path))

        # Extract text directly from file
        text_content = ""
        try:
            if file_type in ("xlsx", "xls"):
                df = pd.read_excel(file_path)
                text_content = f"Columns: {', '.join(df.columns.astype(str))}\n\n"
                text_content += df.head(20).to_string(index=False)
            elif file_type == "csv":
                try:
                    df = pd.read_csv(file_path)
                except Exception:
                    df = pd.read_csv(file_path, encoding="utf-8-sig")
                text_content = f"Columns: {', '.join(df.columns.astype(str))}\n\n"
                text_content += df.head(20).to_string(index=False)
            elif file_type == "docx":
                doc = Document(file_path)
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                text_content = "\n\n".join(paragraphs)
            elif file_type == "pdf":
                doc = pymupdf.open(file_path)
                pages_text = [page.get_text() for page in doc]
                text_content = "\n\n".join(pages_text)
                doc.close()
            elif file_type in ("txt", "md"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()
            elif file_type == "json":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()
        except Exception as e:
            logger.error(f"Text extraction failed for classify_only: {e}")
            return {
                "primary_category": "unclassified",
                "additional_categories": [],
                "confidence": 0.0,
                "error": str(e),
            }

        # Run classification
        state = {
            "content_preview": text_content[:4000],
            "raw_content": text_content,
            "predefined_contexts": [],
            "learned_contexts": [],
            "doc_embedding": [],
            "category_embeddings": {},
            "logs": [],
        }

        # Fetch contexts
        db_service = DatabaseService()
        try:
            state["predefined_contexts"] = db_service.get_predefined_contexts()
            state["learned_contexts"] = db_service.get_top_learned_contexts(limit=10)
        except Exception:
            pass

        # Run classification node
        result = await classify_content_node(state)

        return {
            "primary_category": result.get("primary_category", "unclassified"),
            "additional_categories": result.get("additional_categories", []),
            "all_categories": result.get("all_categories", ["unclassified"]),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", ""),
        }

    def get_available_categories(self) -> dict[str, str]:
        """
        Get all available classification categories.

        Returns:
            Dict mapping category names to descriptions.
        """
        return self.categories

    def get_confidence_thresholds(self) -> dict[str, float]:
        """
        Get confidence thresholds.

        Returns:
            Dict with high_confidence and low_confidence thresholds.
        """
        return {
            "high_confidence": HIGH_CONFIDENCE_THRESHOLD,
            "low_confidence": LOW_CONFIDENCE_THRESHOLD,
        }


def create_smart_router() -> SmartRouterGraph:
    """
    Factory function to create a SmartRouterGraph instance.

    Returns:
        New SmartRouterGraph instance.
    """
    return SmartRouterGraph()
