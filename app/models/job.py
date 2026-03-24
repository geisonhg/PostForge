"""
PostForge — Job Model
Represents a single content generation job (one Instagram post).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SAEnum
import enum

from app.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING_COPY = "generating_copy"
    GENERATING_IMAGE = "generating_image"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"


class InputType(str, enum.Enum):
    IMAGE = "image"
    TEXT = "text"
    TOPIC = "topic"
    MULTI_IMAGE = "multi_image"
    CAMPAIGN = "campaign"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    brand_id = Column(String(50), nullable=False, default="confluex")

    # Input
    input_type = Column(SAEnum(InputType), nullable=False)
    input_text = Column(Text, nullable=True)
    input_image_path = Column(String(500), nullable=True)
    campaign_type = Column(String(100), nullable=True)

    # Status
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING)
    error_message = Column(Text, nullable=True)

    # Generated Copy
    generated_title = Column(String(200), nullable=True)
    generated_hook = Column(Text, nullable=True)
    generated_caption_long = Column(Text, nullable=True)
    generated_caption_short = Column(Text, nullable=True)
    generated_cta = Column(String(300), nullable=True)
    generated_hashtags = Column(Text, nullable=True)
    generated_overlay_text = Column(Text, nullable=True)

    # Generated Assets
    output_image_path = Column(String(500), nullable=True)
    output_caption_path = Column(String(500), nullable=True)
    output_metadata_path = Column(String(500), nullable=True)

    # Extra metadata (named job_data to avoid SQLAlchemy reserved 'metadata')
    job_data = Column(JSON, nullable=True, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Job id={self.id} status={self.status} brand={self.brand_id}>"
