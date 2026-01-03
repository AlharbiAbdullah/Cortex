"""
Chat and Q&A endpoints.

This module provides endpoints for question answering and conversational
chat with AI assistants using RAG and web search capabilities.
"""

import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from cortex.models.requests import ChatRequest, QuestionRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Lazy service initialization
_qa_service = None
_document_service = None


def _get_document_service():
    """Get or create DocumentService instance."""
    global _document_service
    if _document_service is None:
        from cortex.services.document_service import DocumentService

        _document_service = DocumentService()
    return _document_service


def _get_qa_service():
    """Get or create QAService instance."""
    global _qa_service
    if _qa_service is None:
        from cortex.services.qa_service import QAService

        _qa_service = QAService(document_service=_get_document_service())
    return _qa_service


@router.post("/qa")
async def question_answering(request: QuestionRequest) -> dict:
    """
    Answer a question using QA service.

    Args:
        request: QuestionRequest with question, context, and options.

    Returns:
        Dict with question and answer.

    Raises:
        HTTPException: If QA processing fails.
    """
    try:
        qa_service = _get_qa_service()
        answer = await qa_service.answer_question(
            request.question,
            request.context,
            use_rag=request.use_rag,
            model_name=request.model_name,
        )
        return {"question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """
    Chat with the AI assistant.

    Supports RAG context, web search, and expert personas.

    Args:
        request: ChatRequest with message, history, and options.

    Returns:
        Dict with message, response, expert, and optional excel_file.

    Raises:
        HTTPException: If chat processing fails.
    """
    try:
        qa_service = _get_qa_service()
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

        logger.info(
            f"Chat request - message: {request.message[:50]}..., "
            f"expert: {request.expert}, model: {request.model_name}"
        )

        result = await qa_service.chat(
            message=request.message,
            conversation_history=history,
            use_rag=request.use_rag,
            use_web_search=True,
            model_name=request.model_name,
            expert=request.expert,
        )

        response_data = {
            "message": request.message,
            "response": result["response"],
            "expert": result.get("expert") or request.expert,
        }

        if "excel_file" in result:
            response_data["excel_file"] = result["excel_file"]

        return response_data
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    """
    Download a generated file.

    Args:
        filename: Name of the file to download.

    Returns:
        FileResponse with the requested file.

    Raises:
        HTTPException: If filename is invalid or file not found.
    """
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = f"generated_files/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
