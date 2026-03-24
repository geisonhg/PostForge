"""
PostForge — Job Schemas (Pydantic v2)
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.models.job import JobStatus, InputType


class JobCreate(BaseModel):
    brand_id: str = "confluex"
    input_type: InputType
    input_text: Optional[str] = None
    campaign_type: Optional[str] = None


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    error_message: Optional[str] = None
    generated_title: Optional[str] = None
    generated_hook: Optional[str] = None
    generated_caption_long: Optional[str] = None
    generated_caption_short: Optional[str] = None
    generated_cta: Optional[str] = None
    generated_hashtags: Optional[str] = None
    generated_overlay_text: Optional[str] = None
    output_image_path: Optional[str] = None
    output_caption_path: Optional[str] = None
    output_metadata_path: Optional[str] = None
    job_data: Optional[dict[str, Any]] = None


class JobRead(BaseModel):
    id: str
    brand_id: str
    input_type: InputType
    input_text: Optional[str]
    input_image_path: Optional[str]
    campaign_type: Optional[str]
    status: JobStatus
    error_message: Optional[str]
    generated_title: Optional[str]
    generated_hook: Optional[str]
    generated_caption_long: Optional[str]
    generated_caption_short: Optional[str]
    generated_cta: Optional[str]
    generated_hashtags: Optional[str]
    generated_overlay_text: Optional[str]
    output_image_path: Optional[str]
    output_caption_path: Optional[str]
    output_metadata_path: Optional[str]
    job_data: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class JobList(BaseModel):
    total: int
    items: list[JobRead]
