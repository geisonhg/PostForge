"""
PostForge — Brand Model
Stores brand configuration (can also be loaded from config/brands/*.json).
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean

from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    # Visual Identity
    primary_color = Column(String(7), default="#0066FF")
    secondary_color = Column(String(7), default="#00D4FF")
    accent_color = Column(String(7), default="#00FF88")
    dark_color = Column(String(7), default="#0A0E1A")
    light_color = Column(String(7), default="#FFFFFF")

    # Typography
    font_heading = Column(String(100), default="default")
    font_body = Column(String(100), default="default")

    # Voice & Tone
    tone = Column(String(200), nullable=True)
    voice_keywords = Column(JSON, default=list)

    # Content Defaults
    base_hashtags = Column(JSON, default=list)
    cta_options = Column(JSON, default=list)
    instagram_handle = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)

    # Logo
    logo_path = Column(String(500), nullable=True)

    # Full config snapshot (raw JSON from file)
    config_snapshot = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<Brand id={self.id} name={self.name}>"
