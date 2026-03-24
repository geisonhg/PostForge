"""
PostForge — Jobs API Router
Handles job creation, processing, status, and file upload.
"""
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.job import JobStatus, InputType
from app.schemas.job import JobCreate, JobRead, JobList
from app.services.job_manager import job_manager
from app.services.file_manager import file_manager

settings = get_settings()
router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/", response_model=JobList)
def list_jobs(
    status: Optional[str] = None,
    brand_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all jobs with optional filtering."""
    parsed_status = JobStatus(status) if status else None
    total, items = job_manager.list_jobs(
        db, status=parsed_status, brand_id=brand_id, limit=limit, offset=offset
    )
    return JobList(total=total, items=[JobRead.model_validate(j) for j in items])


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get a single job by ID."""
    try:
        job = job_manager.get_job(db, job_id)
        return JobRead.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=JobRead, status_code=201)
def create_and_process_job(
    background_tasks: BackgroundTasks,
    brand_id: str = Form(default="confluex"),
    input_type: InputType = Form(...),
    input_text: Optional[str] = Form(default=None),
    campaign_type: Optional[str] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
):
    """
    Create a new job. Accepts text input and/or image upload.
    Processing runs in the background and updates job status.
    """
    image_path: str | None = None

    # Handle image upload
    if image and image.filename:
        inbox_dir = settings.abs_path(settings.input_inbox_dir)
        inbox_dir.mkdir(parents=True, exist_ok=True)
        dest = inbox_dir / f"upload_{image.filename}"
        with dest.open("wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = str(dest)

    # Validate input
    if not input_text and not image_path and not campaign_type:
        raise HTTPException(
            status_code=422,
            detail="Provide at least one of: input_text, campaign_type, or an image file.",
        )

    job = job_manager.create_job(
        db=db,
        brand_id=brand_id,
        input_type=input_type,
        input_text=input_text,
        input_image_path=image_path,
        campaign_type=campaign_type,
    )

    # Process in background so the API returns immediately
    background_tasks.add_task(_run_job, job.id)

    return JobRead.model_validate(job)


@router.post("/{job_id}/process", response_model=JobRead)
def reprocess_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Re-trigger processing for a pending or failed job."""
    try:
        job = job_manager.get_job(db, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if job.status not in (JobStatus.PENDING, JobStatus.FAILED, JobStatus.REVIEW):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reprocess job with status '{job.status}'.",
        )

    background_tasks.add_task(_run_job, job_id)
    return JobRead.model_validate(job)


@router.post("/{job_id}/approve", response_model=JobRead)
def approve_job(job_id: str, db: Session = Depends(get_db)):
    """Approve a reviewed job (marks it ready for publishing)."""
    try:
        job = job_manager.approve_job(db, job_id)
        return JobRead.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{job_id}/publish", response_model=JobRead)
def publish_job(job_id: str, db: Session = Depends(get_db)):
    """
    Publish a job to Instagram (stub — simulates publishing in MVP).
    In production, connects to Meta Graph API.
    """
    from app.integrations.instagram import instagram_publisher
    try:
        job = job_manager.get_job(db, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    result = instagram_publisher.publish_post(
        image_path=job.output_image_path or "",
        caption=job.generated_caption_long or "",
        job_id=job_id,
    )

    updated_job = job_manager.mark_published(db, job_id, post_id=result.get("post_id"))
    return JobRead.model_validate(updated_job)


@router.get("/{job_id}/image")
def download_image(job_id: str, db: Session = Depends(get_db)):
    """Download the generated post image."""
    try:
        job = job_manager.get_job(db, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not job.output_image_path or not Path(job.output_image_path).exists():
        raise HTTPException(status_code=404, detail="Image not yet generated.")

    return FileResponse(
        job.output_image_path,
        media_type="image/png",
        filename=f"postforge_{job_id}.png",
    )


def _run_job(job_id: str) -> None:
    """Background task — runs in a separate thread from FastAPI."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        job_manager.process_job(db, job_id)
    except Exception:
        pass  # Error is already logged and persisted in the job
    finally:
        db.close()
