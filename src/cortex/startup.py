"""
Application startup hooks.

This module contains functions that run during application startup.
"""

import logging

logger = logging.getLogger(__name__)


async def seed_contexts_on_startup() -> None:
    """
    Seed predefined contexts if database is empty.

    Checks for existing predefined contexts in the database and seeds
    them if none exist. This ensures the Smart Router has context
    for classification on first run.
    """
    try:
        from cortex.database.connection import DatabaseService

        db = DatabaseService()

        # Check if predefined contexts exist
        existing_contexts = db.get_predefined_contexts()

        if not existing_contexts:
            logger.info("No predefined contexts found. Seeding database...")
            from cortex.scripts.seed_contexts import seed_predefined_contexts

            success_count, error_count = seed_predefined_contexts()
            logger.info(
                f"Seeded {success_count} predefined contexts ({error_count} errors)"
            )
        else:
            logger.info(f"Found {len(existing_contexts)} existing predefined contexts")

    except Exception as e:
        logger.warning(f"Could not seed contexts on startup: {e}")
        logger.warning("You can manually seed contexts via POST /api/router/seed")

    # Seed sample documents if none exist
    await seed_documents_on_startup()

    # Seed tabular data for BI platforms
    await seed_tabular_data_on_startup()


async def seed_documents_on_startup() -> None:
    """
    Seed sample documents if ChromaDB is empty.

    Checks for existing documents in ChromaDB and seeds sample documents
    if none exist. This provides test data for all AI services on first run.
    """
    try:
        from cortex.scripts.seed_documents import check_documents_exist, seed_sample_documents

        if not check_documents_exist():
            logger.info("No documents found in ChromaDB. Seeding sample documents...")
            success_count, error_count = await seed_sample_documents()
            logger.info(
                f"Seeded {success_count} sample documents ({error_count} errors)"
            )
        else:
            logger.info("Documents already exist in ChromaDB, skipping document seeding")

    except Exception as e:
        logger.warning(f"Could not seed documents on startup: {e}")
        logger.warning("You can manually upload documents via the frontend or API")


async def seed_tabular_data_on_startup() -> None:
    """
    Seed tabular data for BI platforms if not exists.

    Populates MinIO layers (Bronze/Silver/Gold) with sample tables
    and creates PostgreSQL Gold tables for Superset access.
    """
    try:
        from cortex.scripts.seed_tabular_data import (
            check_tabular_data_exists,
            seed_tabular_data,
        )

        if not check_tabular_data_exists():
            logger.info("No tabular data found. Seeding BI sample data...")
            success_count, error_count = await seed_tabular_data()
            logger.info(
                f"Seeded {success_count} tables ({error_count} errors)"
            )
        else:
            logger.info("Tabular data already exists, skipping BI data seeding")

    except Exception as e:
        logger.warning(f"Could not seed tabular data on startup: {e}")
        logger.warning("Run: python -m cortex.scripts.seed_tabular_data")
