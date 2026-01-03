"""
Smart Router Agent Package.

This package provides the Smart Router Agent for document classification
and routing using ensemble LLM classification and embedding pre-filtering.

Main Components:
- SmartRouterGraph: Main service class for running classification
- create_smart_router: Factory function
- RouterState: State definition for the graph
- PIPELINE_CATEGORIES: Available classification categories

Example:
    from cortex.agents.smart_router import SmartRouterGraph, create_smart_router

    # Using factory function
    router = create_smart_router()

    # Or direct instantiation
    router = SmartRouterGraph()

    # Run classification
    result = await router.run(
        bronze_key="uploads/doc123.pdf",
        filename="report.pdf"
    )
    print(result["primary_category"])
"""

from cortex.agents.smart_router.config import (
    CATEGORY_ALIASES,
    CATEGORY_DOMAINS,
    ENSEMBLE_ADDITIONAL_THRESHOLD,
    ENSEMBLE_MODELS,
    ENSEMBLE_TOP_CANDIDATES,
    HIGH_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
    PIPELINE_CATEGORIES,
    get_domain_for_category,
)
from cortex.agents.smart_router.graph import (
    SmartRouterGraph,
    build_smart_router_graph,
    create_smart_router,
)
from cortex.agents.smart_router.state import RouterState, create_initial_state

__all__ = [
    # Main classes and functions
    "SmartRouterGraph",
    "create_smart_router",
    "build_smart_router_graph",
    # State
    "RouterState",
    "create_initial_state",
    # Configuration
    "PIPELINE_CATEGORIES",
    "CATEGORY_ALIASES",
    "CATEGORY_DOMAINS",
    "HIGH_CONFIDENCE_THRESHOLD",
    "LOW_CONFIDENCE_THRESHOLD",
    "ENSEMBLE_MODELS",
    "ENSEMBLE_TOP_CANDIDATES",
    "ENSEMBLE_ADDITIONAL_THRESHOLD",
    "get_domain_for_category",
]
