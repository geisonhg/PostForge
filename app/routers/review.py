"""
PostForge — Review Interface Router
Serves HTML pages for manual review of generated content.
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.job import JobStatus
from app.services.job_manager import job_manager

settings = get_settings()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("/", response_class=HTMLResponse)
def review_dashboard(
    request: Request,
    status: Optional[str] = None,
    brand_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Main review dashboard — shows all jobs."""
    parsed_status = JobStatus(status) if status else None
    total, jobs = job_manager.list_jobs(
        db, status=parsed_status, brand_id=brand_id, limit=50
    )

    statuses = [s.value for s in JobStatus]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "jobs": jobs,
            "total": total,
            "selected_status": status,
            "selected_brand": brand_id,
            "statuses": statuses,
            "app_name": settings.app_name,
        },
    )


@router.get("/{job_id}", response_class=HTMLResponse)
def review_job(request: Request, job_id: str, db: Session = Depends(get_db)):
    """Detailed review page for a single job."""
    try:
        job = job_manager.get_job(db, job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found.")

    image_exists = bool(
        job.output_image_path and Path(job.output_image_path).exists()
    )

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
            "image_exists": image_exists,
            "image_url": f"/jobs/{job_id}/image" if image_exists else None,
            "can_approve": job.status == JobStatus.REVIEW,
            "can_publish": job.status == JobStatus.APPROVED,
            "app_name": settings.app_name,
        },
    )
