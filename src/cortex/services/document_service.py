"""
Document Service for ChromaDB Integration.

Handles document ingestion from MinIO Silver layer for RAG.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from functools import lru_cache

import chromadb
import pandas as pd
import pymupdf
from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_settings import BaseSettings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ChromaSettings(BaseSettings):
    """ChromaDB configuration settings."""

    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "documents"
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_chroma_settings() -> ChromaSettings:
    """Get cached ChromaDB settings."""
    return ChromaSettings()


class DocumentService:
    """
    Document service for ChromaDB vector storage.

    Handles document ingestion, text extraction, chunking, embedding,
    and similarity search for RAG.
    """

    def __init__(self, settings: ChromaSettings | None = None) -> None:
        """
        Initialize ChromaDB client and embedding model.

        Args:
            settings: ChromaDB settings. If None, loads from environment.
        """
        self.settings = settings or get_chroma_settings()

        os.makedirs(self.settings.chroma_persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.settings.chroma_persist_directory
        )
        self.collection = self.client.get_or_create_collection(
            name=self.settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self.embedding_model = SentenceTransformer(self.settings.embedding_model)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    def _doc_uid(self, doc_key: str) -> str:
        """Generate a stable, Chroma-safe identifier from a document key."""
        return str(uuid.uuid5(uuid.NAMESPACE_URL, doc_key))

    async def ingest_text(
        self, doc_key: str, filename: str, text: str, file_type: str
    ) -> dict:
        """
        Ingest text content directly into ChromaDB.

        Args:
            doc_key: Stable document identifier (typically MinIO silver_key).
            filename: Original filename.
            text: Text content to ingest.
            file_type: File type (pdf, docx, etc.).

        Returns:
            Dict with chunk_count and status.
        """
        if not text.strip():
            logger.warning(f"Document {filename} (key: {doc_key}) is empty, skipping.")
            return {}

        chunks = self.text_splitter.split_text(text)

        if not chunks:
            logger.warning(f"No text chunks generated for {filename}, skipping.")
            return {}

        embeddings = self._get_embeddings(chunks)

        # Ensure re-ingest doesn't duplicate
        self.delete_document(doc_key)

        doc_uid = self._doc_uid(doc_key)
        ids = [f"doc_{doc_uid}_{i}" for i in range(len(chunks))]

        metadatas = [
            {
                "document_key": doc_key,
                "filename": filename,
                "file_type": file_type,
                "chunk_index": i,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info(f"Ingested {filename} (key: {doc_key}) with {len(chunks)} chunks")

        return {"chunk_count": len(chunks), "status": "success"}

    def _extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from a local file based on file type.

        Args:
            file_path: Path to the file.
            file_type: File extension (csv, xlsx, docx, pdf, txt, etc.).

        Returns:
            Extracted text content.
        """
        text_content = ""
        ext = (file_type or "").lower()

        try:
            if ext in ("xlsx", "xls"):
                df = pd.read_excel(file_path)
                text_content = f"Columns: {', '.join(df.columns.astype(str))}\n\n"
                text_content += df.to_string(index=False)

            elif ext == "csv":
                try:
                    df = pd.read_csv(file_path, sep=None, engine="python")
                except Exception:
                    df = pd.read_csv(
                        file_path, encoding="utf-8-sig", sep=None, engine="python"
                    )
                text_content = f"Columns: {', '.join(df.columns.astype(str))}\n\n"
                text_content += df.to_string(index=False)

            elif ext == "docx":
                doc = Document(file_path)
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                text_content = "\n\n".join(paragraphs)

            elif ext == "pdf":
                doc = pymupdf.open(file_path)
                pages_text = [page.get_text() for page in doc]
                text_content = "\n\n".join(pages_text)
                doc.close()

            elif ext in ("txt", "md"):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()

            elif ext == "json":
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()

            else:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        text_content = f.read()
                except Exception:
                    logger.warning(f"Could not extract text from: {file_type}")

        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")

        return text_content

    async def ingest_from_silver(
        self,
        doc_key: str,
        silver_key: str,
        filename: str,
        file_type: str,
        categories: list[str] | None = None,
        feed_the_brain: int | None = None,
    ) -> dict:
        """
        Ingest document from MinIO Silver layer into ChromaDB.

        Args:
            doc_key: Document identifier (typically the MinIO silver_key).
            silver_key: MinIO Silver layer key.
            filename: Original filename.
            file_type: File type (pdf, docx, excel, txt).
            categories: List of categories for metadata.
            feed_the_brain: Whether to include in Q/A service (1=include, 0=exclude).

        Returns:
            Dict with chunk_count and status.
        """
        from cortex.services.minio import get_minio_service

        minio = get_minio_service()

        # Check feed_the_brain from MinIO tags if not provided
        if feed_the_brain is None:
            doc_info = minio.get_document(silver_key)
            if doc_info:
                feed_the_brain = doc_info.get("feed_the_brain", 1)
            else:
                feed_the_brain = 1

        # Skip ingestion if feed_the_brain is 0
        if feed_the_brain == 0:
            logger.info(f"Skipping ingestion for {silver_key} (feed_the_brain=0)")
            self.delete_document(doc_key)
            return {
                "chunk_count": 0,
                "status": "skipped",
                "reason": "feed_the_brain is 0",
            }

        temp_path = (
            f"/tmp/chroma_ingest_{self._doc_uid(doc_key)}_{os.path.basename(silver_key)}"
        )

        try:
            minio.get_silver_file_to_path(silver_key, temp_path)
            logger.info(f"Downloaded Silver file for ingestion: {silver_key}")

            text_content = self._extract_text_from_file(temp_path, file_type)

            if not text_content.strip():
                logger.warning(f"Document {filename} is empty, skipping.")
                return {"chunk_count": 0, "status": "empty"}

            chunks = self.text_splitter.split_text(text_content)

            if not chunks:
                logger.warning(f"No text chunks generated for {filename}.")
                return {"chunk_count": 0, "status": "no_chunks"}

            embeddings = self._get_embeddings(chunks)

            # Ensure re-ingest doesn't duplicate
            self.delete_document(doc_key)

            doc_uid = self._doc_uid(doc_key)
            ids = [f"doc_{doc_uid}_{i}" for i in range(len(chunks))]

            metadatas = [
                {
                    "document_key": doc_key,
                    "filename": filename,
                    "file_type": file_type,
                    "silver_key": silver_key,
                    "categories": ",".join(categories) if categories else "",
                    "feed_the_brain": 1,
                    "chunk_index": i,
                    "ingested_at": datetime.now(timezone.utc).isoformat(),
                }
                for i in range(len(chunks))
            ]

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
            )

            logger.info(
                f"Ingested {filename} (key: {doc_key}) from Silver with {len(chunks)} chunks"
            )

            return {"chunk_count": len(chunks), "status": "success"}

        except Exception as e:
            logger.error(f"Error ingesting from Silver: {e}")
            return {"chunk_count": 0, "status": "error", "error": str(e)}

        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def list_documents(self) -> list[dict]:
        """List summary of ingested documents from Chroma metadata."""
        try:
            results = self.collection.get(include=["metadatas"])
            docs = {}
            for m in results["metadatas"]:
                doc_key = m.get("document_key")
                if not doc_key:
                    continue
                if doc_key not in docs:
                    docs[doc_key] = {
                        "document_key": doc_key,
                        "filename": m.get("filename"),
                        "chunks": 0,
                    }
                docs[doc_key]["chunks"] += 1
            return list(docs.values())
        except Exception:
            return []

    def delete_document(self, doc_key: str) -> bool:
        """Delete all chunks for a specific document key."""
        try:
            self.collection.delete(where={"document_key": doc_key})
            logger.info(f"Deleted vectors for document key {doc_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False

    def search_similar(self, query: str, n_results: int = 5) -> list[dict]:
        """
        Search for similar document chunks.

        Args:
            query: Search query.
            n_results: Number of results to return.

        Returns:
            List of matching chunks with metadata.
        """
        if not query.strip():
            return []

        try:
            query_embedding = self._get_embeddings([query])[0]

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )

            if not results or not results["documents"] or not results["documents"][0]:
                return []

            formatted_results = []
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                formatted_results.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "source": (
                        f"File: {meta.get('filename')} (Key: {meta.get('document_key')})"
                    ),
                })

            return formatted_results
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def get_context_for_query(self, query: str, max_context_length: int = 3000) -> str:
        """
        Get formatted context string for RAG.

        Args:
            query: Search query.
            max_context_length: Maximum context length in characters.

        Returns:
            Formatted context string with citations.
        """
        results = self.search_similar(query, n_results=5)

        if not results:
            return ""

        context_parts = []
        current_length = 0

        for result in results:
            content = result["content"]
            source = result["source"]

            chunk_text = f"[{source}]\n{content}"

            if current_length + len(chunk_text) > max_context_length:
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)

        return "\n\n---\n\n".join(context_parts)


# Singleton instance
_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    """Get or create the singleton document service instance."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
