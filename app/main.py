"""
PostForge — FastAPI Application Entry Point
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import get_settings
from app.database import init_db
from app.routers import health, jobs, brands, review
from app.services.watcher import inbox_watcher

settings = get_settings()


def configure_logging() -> None:
    """Set up Loguru + redirect stdlib logging to loguru."""
    log_dir = settings.abs_path(settings.output_logs_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_dir / "postforge.log"),
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{line} — {message}",
    )

    # Intercept stdlib logging
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = str(record.levelno)
            logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    configure_logging()
    logger.info(f"Starting {settings.app_name} [{settings.app_env}]")

    # Ensure all directories exist
    settings.ensure_dirs()

    # Initialize database
    init_db()
    logger.info("Database initialized.")

    # Seed default brand if not present
    _seed_default_brand()

    # Start inbox file watcher
    inbox_watcher.start(brand_id=settings.default_brand)

    yield

    # Shutdown
    inbox_watcher.stop()
    logger.info(f"{settings.app_name} shutdown complete.")


def _seed_default_brand() -> None:
    """Seed Confluex brand from config file if not in DB."""
    from app.database import SessionLocal
    from app.models.brand import Brand
    db = SessionLocal()
    try:
        existing = db.query(Brand).filter(Brand.id == "confluex").first()
        if not existing:
            import json
            config_path = settings.abs_path(settings.config_brands_dir) / "confluex.json"
            if config_path.exists():
                config = json.loads(config_path.read_text())
                vis = config.get("visual_identity", {})
                voice = config.get("voice", {})
                content = config.get("content", {})
                assets = config.get("brand_assets", {})

                brand = Brand(
                    id="confluex",
                    name=config.get("name", "Confluex"),
                    description=config.get("description"),
                    primary_color=vis.get("primary_color", "#0057FF"),
                    secondary_color=vis.get("secondary_color", "#00D4FF"),
                    accent_color=vis.get("accent_color", "#00FF88"),
                    dark_color=vis.get("dark_color", "#080C18"),
                    light_color=vis.get("light_color", "#FFFFFF"),
                    tone=voice.get("tone"),
                    voice_keywords=voice.get("keywords", []),
                    base_hashtags=content.get("base_hashtags", []),
                    cta_options=content.get("cta_options", []),
                    instagram_handle=assets.get("instagram_handle"),
                    website=assets.get("website"),
                    logo_path=assets.get("logo_path"),
                    config_snapshot=config,
                )
                db.add(brand)
                db.commit()
                logger.info("Confluex brand seeded from config file.")
    except Exception as e:
        logger.warning(f"Could not seed brand: {e}")
    finally:
        db.close()


# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="PostForge",
    description="Instagram Content Automation Engine — Confluex Internal Tool",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(brands.router)
app.include_router(review.router)


@app.get("/", include_in_schema=False)
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/review")
