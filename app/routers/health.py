"""
PostForge — Health & Status Endpoints
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.services.watcher import inbox_watcher

settings = get_settings()
router = APIRouter(prefix="/health", tags=["System"])


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    timestamp: str
    watcher_running: bool
    ai_configured: bool


@router.get("/", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        env=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat(),
        watcher_running=inbox_watcher.is_running,
        ai_configured=bool(settings.anthropic_api_key),
    )
