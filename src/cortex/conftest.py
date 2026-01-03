"""Shared pytest fixtures for Cortex tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_db_session():
    """Provide a mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_minio_client():
    """Provide a mock MinIO client."""
    client = MagicMock()
    client.bucket_exists = MagicMock(return_value=True)
    client.put_object = MagicMock()
    client.get_object = MagicMock()
    client.copy_object = MagicMock()
    return client


@pytest.fixture
def sample_document_content():
    """Provide sample document content for testing."""
    return """
    Q3 Financial Report 2024

    Revenue: $12.5M
    Expenses: $8.2M
    Net Profit: $4.3M

    Key Highlights:
    - 15% revenue growth year-over-year
    - Successful product launch in Q2
    - Expansion into new markets
    """


@pytest.fixture
def sample_classification_result():
    """Provide sample classification result."""
    return {
        "primary_category": "financial_forecast",
        "confidence": 0.87,
        "additional_categories": ["budget", "quarterly_report"],
        "reasoning": "Contains revenue projections and quarterly financial data",
    }
