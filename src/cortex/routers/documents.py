"""
Document management endpoints.

This module provides endpoints for listing, managing, and processing
documents across the Bronze, Silver, and Gold data lake layers.
"""

import json
import logging
import os
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from cortex.models.requests import FeedTheBrainRequest, TableurRequest
from cortex.services.minio import get_minio_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["documents"])

# Lazy service initialization
_document_service = None


def _get_document_service():
    """Get or create DocumentService instance."""
    global _document_service
    if _document_service is None:
        from cortex.services.document_service import DocumentService

        _document_service = DocumentService()
    return _document_service


@router.get("/documents")
async def list_documents(limit: int = 100) -> dict:
    """
    List documents from MinIO Silver layer (source of truth).

    Args:
        limit: Maximum number of documents to return.

    Returns:
        Dict with list of documents.

    Raises:
        HTTPException: If listing fails.
    """
    try:
        minio = get_minio_service()
        documents = minio.list_documents(limit=limit)
        return {"documents": documents}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.delete("/documents/{silver_key:path}")
async def delete_document(silver_key: str) -> dict:
    """
    Delete a document from MinIO Silver layer and ChromaDB.

    Args:
        silver_key: The Silver layer key of the document.

    Returns:
        Dict with success message.

    Raises:
        HTTPException: If deletion fails.
    """
    try:
        minio = get_minio_service()

        # Delete from Silver
        minio.delete_from_silver(silver_key)

        # Delete vectors
        document_service = _get_document_service()
        document_service.delete_document(silver_key)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/feed-the-brain")
async def update_feed_the_brain(request: FeedTheBrainRequest) -> dict:
    """
    Update the FeedTheBrain tag for a document.

    - feed_the_brain=1: Include document in Q/A service (triggers ChromaDB ingestion)
    - feed_the_brain=0: Exclude document from Q/A service (removes from ChromaDB)

    Args:
        request: FeedTheBrainRequest with silver_key and feed_the_brain value.

    Returns:
        Dict with update status and ChromaDB sync result.

    Raises:
        HTTPException: If update fails.
    """
    if request.feed_the_brain not in (0, 1):
        raise HTTPException(status_code=400, detail="feed_the_brain must be 0 or 1")

    try:
        minio = get_minio_service()
        document_service = _get_document_service()

        # Get existing document
        doc = minio.get_document(request.silver_key)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found in Silver layer",
            )

        old_feed_the_brain = doc.get("feed_the_brain", 1)

        # Update the tag in MinIO
        success = minio.update_feed_the_brain(request.silver_key, request.feed_the_brain)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update feed_the_brain tag",
            )

        chroma_status = "unchanged"

        # Handle ChromaDB sync based on the change
        if request.feed_the_brain == 0:
            try:
                document_service.delete_document(request.silver_key)
                chroma_status = "removed"
                logger.info(
                    f"Removed document {request.silver_key} from ChromaDB "
                    "(feed_the_brain=0)"
                )
            except Exception as e:
                logger.warning(f"Could not remove from ChromaDB: {e}")
                chroma_status = f"removal_failed: {str(e)}"

        elif request.feed_the_brain == 1 and old_feed_the_brain == 0:
            try:
                chroma_result = await document_service.ingest_from_silver(
                    doc_key=request.silver_key,
                    silver_key=request.silver_key,
                    filename=doc.get("filename", "unknown"),
                    file_type=doc.get("file_type", "unknown"),
                    categories=doc.get("categories", []),
                    feed_the_brain=1,
                )
                if chroma_result.get("status") == "success":
                    chroma_status = f"ingested ({chroma_result.get('chunk_count', 0)} chunks)"
                else:
                    chroma_status = f"ingestion_status: {chroma_result.get('status')}"
                logger.info(
                    f"Re-ingested document {request.silver_key} to ChromaDB "
                    "(feed_the_brain=1)"
                )
            except Exception as e:
                logger.warning(f"Could not re-ingest to ChromaDB: {e}")
                chroma_status = f"ingestion_failed: {str(e)}"

        return {
            "silver_key": request.silver_key,
            "filename": doc.get("filename"),
            "old_feed_the_brain": old_feed_the_brain,
            "new_feed_the_brain": request.feed_the_brain,
            "chroma_status": chroma_status,
            "message": (
                f"FeedTheBrain updated successfully: "
                f"{old_feed_the_brain} -> {request.feed_the_brain}"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feed_the_brain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _process_document_to_gold(
    silver_key: str,
    document_id: str,
    filename: str,
    file_type: str,
) -> dict[str, Any]:
    """
    Process a document from Silver layer and extract tabular data to Gold layer.

    Args:
        silver_key: Silver layer key of the document.
        document_id: Document identifier.
        filename: Original filename.
        file_type: File type extension.

    Returns:
        Dict with processing status and results.
    """
    minio = get_minio_service()
    temp_path = f"/tmp/gold_process_{document_id}_{os.path.basename(silver_key)}"

    try:
        # Download from Silver
        minio.get_silver_file_to_path(silver_key, temp_path)

        df = None
        ext = (file_type or "").lower()

        if ext in ("xlsx", "xls"):
            df = pd.read_excel(temp_path)
        elif ext == "csv":
            try:
                df = pd.read_csv(temp_path, sep=None, engine="python")
            except Exception:
                df = pd.read_csv(
                    temp_path,
                    encoding="utf-8-sig",
                    sep=None,
                    engine="python",
                )
        elif ext == "json":
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                elif isinstance(data, dict):
                    df = pd.DataFrame([data])
        else:
            return {
                "status": "skipped",
                "reason": f"File type '{file_type}' is not tabular data",
            }

        if df is None or df.empty:
            return {
                "status": "empty",
                "reason": "No records found in file",
            }

        gold_key = minio.save_to_gold(
            document_id=document_id,
            data_type="tabular",
            df=df,
            source_silver_key=silver_key,
            filename=filename,
        )

        return {
            "status": "success",
            "gold_key": gold_key,
            "record_count": len(df),
        }

    except Exception as e:
        logger.error(f"Error processing document to Gold: {e}")
        return {
            "status": "error",
            "error": str(e),
        }
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@router.post("/documents/tableur")
async def update_tableur(request: TableurRequest) -> dict:
    """
    Update the tableur tag for a document and process to Gold layer if enabled.

    - tableur=1: Process document's tabular data to Gold layer
    - tableur=0: Skip Gold layer processing (removes from Gold if exists)

    Args:
        request: TableurRequest with silver_key and tableur value.

    Returns:
        Dict with update status and Gold layer processing result.

    Raises:
        HTTPException: If update fails.
    """
    if request.tableur not in (0, 1):
        raise HTTPException(status_code=400, detail="tableur must be 0 or 1")

    try:
        minio = get_minio_service()

        # Get existing document
        doc = minio.get_document(request.silver_key)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found in Silver layer",
            )

        old_tableur = doc.get("tableur", 0)

        # Update the tag in MinIO
        success = minio.update_tableur(request.silver_key, request.tableur)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update tableur tag")

        gold_status = "unchanged"
        gold_key = None

        if request.tableur == 1:
            try:
                gold_result = await _process_document_to_gold(
                    silver_key=request.silver_key,
                    document_id=doc.get("document_id"),
                    filename=doc.get("filename", "unknown"),
                    file_type=doc.get("file_type", "unknown"),
                )
                if gold_result.get("status") == "success":
                    gold_status = f"processed ({gold_result.get('record_count', 0)} records)"
                    gold_key = gold_result.get("gold_key")
                else:
                    gold_status = f"processing_status: {gold_result.get('status')}"
                logger.info(
                    f"Processed document {request.silver_key} to Gold layer (tableur=1)"
                )
            except Exception as e:
                logger.warning(f"Could not process to Gold: {e}")
                gold_status = f"processing_failed: {str(e)}"

        elif request.tableur == 0 and old_tableur == 1:
            try:
                document_id = doc.get("document_id")
                gold_items = minio.query_gold_by_document(document_id)
                for item in gold_items:
                    minio.delete_from_gold(item.get("gold_key"))
                if gold_items:
                    gold_status = f"removed ({len(gold_items)} files)"
                else:
                    gold_status = "no_gold_data_to_remove"
                logger.info(
                    f"Removed Gold data for document {request.silver_key} (tableur=0)"
                )
            except Exception as e:
                logger.warning(f"Could not remove from Gold: {e}")
                gold_status = f"removal_failed: {str(e)}"

        return {
            "silver_key": request.silver_key,
            "filename": doc.get("filename"),
            "old_tableur": old_tableur,
            "new_tableur": request.tableur,
            "gold_status": gold_status,
            "gold_key": gold_key,
            "message": f"Tableur updated successfully: {old_tableur} -> {request.tableur}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tableur: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/tableur")
async def list_tableur_documents(limit: int = 100) -> dict:
    """
    List all documents with tableur=1 (candidates for Gold layer).

    Args:
        limit: Maximum number of documents to return.

    Returns:
        Dict with count and list of tableur documents.

    Raises:
        HTTPException: If listing fails.
    """
    try:
        minio = get_minio_service()
        documents = minio.list_documents_for_gold(limit=limit)
        return {
            "count": len(documents),
            "documents": documents,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tableur documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tableur documents")


# ==================== Gold Layer Endpoints ====================
@router.get("/gold/documents")
async def list_gold_documents(
    data_type: str | None = None,
    limit: int = 100,
) -> dict:
    """
    List all documents in the Gold layer (processed tabular data).

    Args:
        data_type: Optional filter by data type.
        limit: Maximum number of documents to return.

    Returns:
        Dict with list of Gold documents.

    Raises:
        HTTPException: If listing fails.
    """
    try:
        minio = get_minio_service()
        documents = minio.list_gold_data(data_type=data_type, limit=limit)
        return {"documents": documents}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing Gold documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list Gold documents")


@router.get("/gold/documents/{gold_key:path}")
async def get_gold_document(gold_key: str) -> dict:
    """
    Get a specific document from the Gold layer.

    Args:
        gold_key: Gold layer key of the document.

    Returns:
        Gold document data.

    Raises:
        HTTPException: If document not found or retrieval fails.
    """
    try:
        minio = get_minio_service()
        data = minio.get_from_gold(gold_key)
        if not data:
            raise HTTPException(status_code=404, detail="Gold document not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Gold document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gold/stats")
async def get_gold_stats() -> dict:
    """
    Get statistics about Gold layer data.

    Returns:
        Dict with Gold layer statistics.

    Raises:
        HTTPException: If retrieval fails.
    """
    try:
        minio = get_minio_service()
        stats = minio.get_gold_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting Gold stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gold/sync-to-postgres")
async def sync_gold_to_postgres(
    dry_run: bool = Query(default=False),
    limit: int | None = None,
) -> dict:
    """
    Sync Gold layer data from MinIO to PostgreSQL for Superset dashboards.

    Args:
        dry_run: If True, only simulate the sync without making changes.
        limit: Optional limit on number of items to sync.

    Returns:
        Dict with sync results.

    Raises:
        HTTPException: If sync fails.
    """
    try:
        from cortex.scripts.gold_to_postgres import sync_gold_to_postgres as do_sync
        import asyncio

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: do_sync(dry_run=dry_run, limit=limit),
        )

        return result

    except Exception as e:
        logger.error(f"Error syncing Gold to PostgreSQL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gold/postgres-tables")
async def list_gold_postgres_tables() -> dict:
    """
    List all tables in the PostgreSQL 'gold' schema.

    Returns:
        Dict with schema info, table list, and Superset connection details.

    Raises:
        HTTPException: If listing fails.
    """
    try:
        import psycopg2

        from cortex.database.connection import get_db_settings

        settings = get_db_settings()

        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
        )

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name = 'gold'
                """)
                if not cur.fetchone():
                    return {
                        "schema": "gold",
                        "tables": [],
                        "message": "Gold schema not found. Run sync first.",
                    }

                cur.execute("""
                    SELECT
                        table_name,
                        (SELECT COUNT(*) FROM information_schema.columns
                         WHERE table_schema = 'gold' AND table_name = t.table_name
                        ) as column_count
                    FROM information_schema.tables t
                    WHERE table_schema = 'gold'
                    ORDER BY table_name
                """)
                tables = []
                for row in cur.fetchall():
                    table_name = row[0]
                    column_count = row[1]

                    cur.execute(f'SELECT COUNT(*) FROM gold."{table_name}"')
                    row_count = cur.fetchone()[0]

                    tables.append({
                        "table_name": table_name,
                        "full_name": f"gold.{table_name}",
                        "column_count": column_count,
                        "row_count": row_count,
                    })

                return {
                    "schema": "gold",
                    "table_count": len(tables),
                    "tables": tables,
                    "superset_connection": {
                        "host": "db",
                        "port": 5432,
                        "database": settings.db_name,
                        "schema": "gold",
                    },
                }
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error listing Gold PostgreSQL tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))
