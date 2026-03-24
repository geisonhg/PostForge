"""
PostForge — Job Manager
Orchestrates the full pipeline: input → copy → image → output → status.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.job import Job, JobStatus, InputType
from app.services.input_processor import input_processor, InputContext
from app.services.content_strategist import content_strategist
from app.services.copy_generator import copy_generator
from app.services.visual_strategist import visual_strategist
from app.services.image_generator import image_generator
from app.services.file_manager import file_manager

settings = get_settings()


class JobManager:

    def create_job(
        self,
        db: Session,
        brand_id: str = "confluex",
        input_type: InputType = InputType.TEXT,
        input_text: str | None = None,
        input_image_path: str | None = None,
        campaign_type: str | None = None,
    ) -> Job:
        """Create and persist a new job."""
        job = Job(
            brand_id=brand_id,
            input_type=input_type,
            input_text=input_text,
            input_image_path=input_image_path,
            campaign_type=campaign_type,
            status=JobStatus.PENDING,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        logger.info(f"Job created: id={job.id} brand={brand_id} type={input_type.value}")
        return job

    def process_job(self, db: Session, job_id: str) -> Job:
        """
        Run the full generation pipeline for a job.
        Updates job status at each step.
        """
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        try:
            # ── Step 1: Analyze Input ─────────────────────────────────────
            self._update_status(db, job, JobStatus.ANALYZING)
            ctx = input_processor.analyze(
                input_text=job.input_text,
                image_path=job.input_image_path,
                campaign_type=job.campaign_type,
            )

            # ── Step 2: Strategize ────────────────────────────────────────
            self._update_status(db, job, JobStatus.GENERATING_COPY)
            brief = content_strategist.strategize(ctx, brand_id=job.brand_id)

            # ── Step 3: Generate Copy from Brief ──────────────────────────
            copy_data = copy_generator.generate(ctx, brand_id=job.brand_id, brief=brief)

            # Store generated copy in job
            job.generated_title = copy_data.get("title")
            job.generated_hook = copy_data.get("hook")
            job.generated_caption_long = copy_data.get("caption_long")
            job.generated_caption_short = copy_data.get("caption_short")
            job.generated_cta = copy_data.get("cta")
            job.generated_hashtags = copy_data.get("hashtags")
            job.generated_overlay_text = copy_data.get("overlay_text")
            db.commit()

            # ── Step 4: Visual Strategy ───────────────────────────────────
            self._update_status(db, job, JobStatus.GENERATING_IMAGE)
            visual_brief = visual_strategist.strategize(
                copy_data=copy_data,
                strategy_brief=brief,
                brand_id=job.brand_id,
                input_image_path=job.input_image_path,
            )

            # ── Step 5: Generate Image ────────────────────────────────────
            image_bytes = image_generator.generate(
                copy_data=copy_data,
                brand_id=job.brand_id,
                input_image_path=job.input_image_path,
                visual_brief=visual_brief,
            )

            # ── Step 4: Save Outputs ──────────────────────────────────────
            img_path = file_manager.save_image(job.id, image_bytes, "post.png")
            caption_path = file_manager.save_caption(job.id, copy_data)

            metadata = {
                "job_id": job.id,
                "brand_id": job.brand_id,
                "input_type": ctx.input_type.value,
                "content_category": ctx.content_category,
                "detected_topics": ctx.detected_topics,
                "language": ctx.language,
                "strategy_brief": brief.to_dict(),
                "visual_brief": visual_brief.to_dict(),
                "copy": {k: v for k, v in copy_data.items() if not k.startswith("_")},
                "output_files": file_manager.get_job_files(job.id),
                "pipeline_completed_at": datetime.now(timezone.utc).isoformat(),
            }
            meta_path = file_manager.save_metadata(job.id, metadata)

            # Update job with output paths
            job.output_image_path = str(img_path)
            job.output_caption_path = str(caption_path)
            job.output_metadata_path = str(meta_path)
            job.job_data = metadata
            job.completed_at = datetime.now(timezone.utc)

            # Move to review
            self._update_status(db, job, JobStatus.REVIEW)
            logger.info(f"Job completed successfully: id={job.id}")

        except Exception as e:
            logger.error(f"Job failed: id={job_id} error={e}", exc_info=True)
            job.error_message = str(e)
            job.status = JobStatus.FAILED
            db.commit()
            raise

        return job

    def approve_job(self, db: Session, job_id: str) -> Job:
        """Mark a reviewed job as approved (ready to publish)."""
        job = self._get_job_or_raise(db, job_id)
        if job.status != JobStatus.REVIEW:
            raise ValueError(f"Job must be in REVIEW status to approve. Current: {job.status}")
        self._update_status(db, job, JobStatus.APPROVED)
        return job

    def mark_published(self, db: Session, job_id: str, post_id: str | None = None) -> Job:
        """Mark a job as published after posting to Instagram."""
        job = self._get_job_or_raise(db, job_id)
        if job.status not in (JobStatus.APPROVED, JobStatus.REVIEW):
            raise ValueError(f"Job must be APPROVED to publish. Current: {job.status}")
        if post_id and job.job_data:
            job.job_data = {**job.job_data, "instagram_post_id": post_id}
        self._update_status(db, job, JobStatus.PUBLISHED)
        return job

    def get_job(self, db: Session, job_id: str) -> Job:
        return self._get_job_or_raise(db, job_id)

    def list_jobs(
        self,
        db: Session,
        status: JobStatus | None = None,
        brand_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[int, list[Job]]:
        q = db.query(Job)
        if status:
            q = q.filter(Job.status == status)
        if brand_id:
            q = q.filter(Job.brand_id == brand_id)
        total = q.count()
        items = q.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()
        return total, items

    def process_inbox_file(self, db: Session, file_path: str, brand_id: str = "confluex") -> Job:
        """Create and immediately process a job from an inbox file."""
        path = Path(file_path)
        ctx = input_processor.analyze_file(file_path)

        job = self.create_job(
            db=db,
            brand_id=brand_id,
            input_type=ctx.input_type,
            input_text=ctx.text if ctx.input_type != ctx.input_type.IMAGE else None,
            input_image_path=file_path if ctx.input_type == ctx.input_type.IMAGE else None,
            campaign_type=ctx.campaign_type,
        )

        # Move file to processed
        try:
            file_manager.move_to_processed(file_path)
        except Exception as e:
            logger.warning(f"Could not move inbox file: {e}")

        return self.process_job(db, job.id)

    def _update_status(self, db: Session, job: Job, status: JobStatus) -> None:
        job.status = status
        job.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.debug(f"Job {job.id} → {status.value}")

    def _get_job_or_raise(self, db: Session, job_id: str) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        return job


job_manager = JobManager()
