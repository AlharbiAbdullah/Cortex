"""
Smart Router Graph Nodes.

This package contains all the node functions used in the Smart Router LangGraph.
Each module contains related functionality for the document processing pipeline.
"""

from cortex.agents.smart_router.nodes.classification import classify_content_node
from cortex.agents.smart_router.nodes.context import fetch_context_node
from cortex.agents.smart_router.nodes.extraction import extract_text_node, init_node
from cortex.agents.smart_router.nodes.learning import learning_node
from cortex.agents.smart_router.nodes.storage import copy_to_silver_node, save_results_node

__all__ = [
    "init_node",
    "extract_text_node",
    "fetch_context_node",
    "classify_content_node",
    "copy_to_silver_node",
    "save_results_node",
    "learning_node",
]
