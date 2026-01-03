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
