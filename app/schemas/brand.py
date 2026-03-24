"""
PostForge — Brand Schemas (Pydantic v2)
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class BrandCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    primary_color: str = "#0066FF"
    secondary_color: str = "#00D4FF"
    accent_color: str = "#00FF88"
    dark_color: str = "#0A0E1A"
    light_color: str = "#FFFFFF"
    font_heading: str = "default"
    font_body: str = "default"
    tone: Optional[str] = None
    voice_keywords: list[str] = []
    base_hashtags: list[str] = []
    cta_options: list[str] = []
    instagram_handle: Optional[str] = None
    website: Optional[str] = None
    logo_path: Optional[str] = None
    config_snapshot: Optional[dict[str, Any]] = None


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    dark_color: Optional[str] = None
    light_color: Optional[str] = None
    tone: Optional[str] = None
    voice_keywords: Optional[list[str]] = None
    base_hashtags: Optional[list[str]] = None
    cta_options: Optional[list[str]] = None
    instagram_handle: Optional[str] = None
    website: Optional[str] = None
    logo_path: Optional[str] = None
    active: Optional[bool] = None


class BrandRead(BaseModel):
    id: str
    name: str
    description: Optional[str]
    active: bool
    primary_color: str
    secondary_color: str
    accent_color: str
    dark_color: str
    light_color: str
    font_heading: str
    font_body: str
    tone: Optional[str]
    voice_keywords: list[str]
    base_hashtags: list[str]
    cta_options: list[str]
    instagram_handle: Optional[str]
    website: Optional[str]
    logo_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
