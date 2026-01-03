"""
Report Generation API endpoints.

This module provides endpoints for generating automated reports
from templates in multiple formats (HTML, PDF, DOCX).
"""

import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from cortex.services.report_service import (
    ChartConfig,
    GeneratedReport,
    ReportTemplate,
    get_report_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


class GenerateReportRequest(BaseModel):
    """Request model for report generation."""

    template_id: str = Field(..., description="Template identifier")
    data: dict[str, Any] = Field(..., description="Data to populate template")
    output_format: str = Field(
        default="html",
        description="Output format: html, pdf, docx",
    )
    filename: str | None = Field(
        default=None,
        description="Optional custom filename",
    )


class CreateTemplateRequest(BaseModel):
    """Request model for creating a custom template."""

    template_id: str = Field(..., min_length=1, description="Unique template ID")
    name: str = Field(..., min_length=1, description="Template display name")
    description: str = Field(default="", description="Template description")
    template_content: str = Field(..., min_length=10, description="Jinja2 HTML template")
    required_fields: list[str] = Field(
        default_factory=list,
        description="Required data fields",
    )
    sample_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Sample data for preview",
    )


class CreateChartRequest(BaseModel):
    """Request model for chart creation."""

    chart_type: str = Field(
        ...,
        description="Chart type: bar, line, pie, scatter",
    )
    title: str = Field(..., description="Chart title")
    data: dict[str, Any] = Field(..., description="Chart data")
    width: int = Field(default=600, ge=200, le=1200, description="Width in pixels")
    height: int = Field(default=400, ge=200, le=800, description="Height in pixels")


@router.get("/templates")
async def list_templates() -> dict[str, Any]:
    """
    List available report templates.

    Returns:
        Dict with list of template metadata.
    """
    try:
        service = get_report_service()
        templates = service.list_templates()
        return {
            "count": len(templates),
            "templates": templates,
        }
    except Exception as e:
        logger.error(f"List templates failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}")
async def get_template(template_id: str) -> dict[str, Any]:
    """
    Get template details.

    Args:
        template_id: Template identifier.

    Returns:
        Template metadata and sample data.

    Raises:
        HTTPException: If template not found.
    """
    try:
        service = get_report_service()
        templates = service.list_templates()

        for template in templates:
            if template["template_id"] == template_id:
                return template

        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get template failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates")
async def create_template(request: CreateTemplateRequest) -> dict[str, Any]:
    """
    Create a custom report template.

    Args:
        request: Template definition.

    Returns:
        Created template metadata.

    Raises:
        HTTPException: If template creation fails.
    """
    try:
        service = get_report_service()

        # Save template to filesystem
        template_path = os.path.join(
            service._settings.template_dir,
            f"{request.template_id}.html",
        )

        os.makedirs(os.path.dirname(template_path), exist_ok=True)

        with open(template_path, "w", encoding="utf-8") as f:
            f.write(request.template_content)

        return {
            "message": "Template created successfully",
            "template_id": request.template_id,
            "name": request.name,
            "file_path": template_path,
        }

    except Exception as e:
        logger.error(f"Create template failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GeneratedReport)
async def generate_report(request: GenerateReportRequest) -> GeneratedReport:
    """
    Generate a report from a template.

    Args:
        request: Report generation request with template and data.

    Returns:
        GeneratedReport with file details.

    Raises:
        HTTPException: If generation fails.
    """
    if request.output_format not in ("html", "pdf", "docx"):
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Supported: html, pdf, docx",
        )

    try:
        service = get_report_service()
        report = await service.generate_report(
            template_id=request.template_id,
            data=request.data,
            output_format=request.output_format,
            filename=request.filename,
        )
        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_report(filename: str) -> FileResponse:
    """
    Download a generated report.

    Args:
        filename: Report filename.

    Returns:
        FileResponse with the report file.

    Raises:
        HTTPException: If file not found or invalid.
    """
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        service = get_report_service()
        file_path = os.path.join(service._settings.output_dir, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Report not found")

        # Determine media type
        media_types = {
            ".html": "text/html",
            ".pdf": "application/pdf",
            ".docx": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
        }
        ext = os.path.splitext(filename)[1].lower()
        media_type = media_types.get(ext, "application/octet-stream")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chart")
async def create_chart(request: CreateChartRequest) -> dict[str, Any]:
    """
    Create a chart and return as base64 image.

    Args:
        request: Chart configuration.

    Returns:
        Dict with base64-encoded image.

    Raises:
        HTTPException: If chart creation fails.
    """
    if request.chart_type not in ("bar", "line", "pie", "scatter"):
        raise HTTPException(
            status_code=400,
            detail="Invalid chart type. Supported: bar, line, pie, scatter",
        )

    try:
        service = get_report_service()
        config = ChartConfig(
            chart_type=request.chart_type,
            title=request.title,
            data=request.data,
            width=request.width,
            height=request.height,
        )
        image_base64 = service.create_chart(config)

        if not image_base64:
            raise HTTPException(
                status_code=500,
                detail="Chart creation failed. Ensure matplotlib is installed.",
            )

        return {
            "chart_type": request.chart_type,
            "title": request.title,
            "image_base64": image_base64,
            "data_url": f"data:image/png;base64,{image_base64}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_report(request: GenerateReportRequest) -> dict[str, Any]:
    """
    Preview a report without saving to disk.

    Args:
        request: Report generation request.

    Returns:
        Dict with rendered HTML content.

    Raises:
        HTTPException: If preview fails.
    """
    try:
        from jinja2 import Environment

        service = get_report_service()

        # Get template
        if request.template_id in service._builtin_templates:
            template = service._builtin_templates[request.template_id]
            jinja_template = service._jinja_env.from_string(template.template_content)
        else:
            jinja_template = service._jinja_env.get_template(
                f"{request.template_id}.html"
            )

        # Render
        from datetime import datetime

        context = {
            "company_name": service._settings.company_name,
            "generated_at": datetime.now().isoformat(),
            "report_id": "preview",
            **request.data,
        }

        html_content = jinja_template.render(**context)

        return {
            "template_id": request.template_id,
            "preview": True,
            "html_content": html_content,
        }

    except Exception as e:
        logger.error(f"Report preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
