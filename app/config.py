"""
PostForge — Application Configuration
Centralized settings via Pydantic BaseSettings + .env
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "PostForge"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "dev-secret-key-change-in-production"

    # ── AI Provider ──────────────────────────────────────────────
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_api_key: str = ""

    # ── Brand ────────────────────────────────────────────────────
    default_brand: str = "confluex"

    # ── Storage Paths ────────────────────────────────────────────
    input_inbox_dir: str = "input/inbox"
    input_processed_dir: str = "input/processed"
    output_posts_dir: str = "output/final_posts"
    output_captions_dir: str = "output/captions"
    output_metadata_dir: str = "output/metadata"
    output_logs_dir: str = "output/logs"
    config_brands_dir: str = "config/brands"
    assets_dir: str = "assets"
    fonts_dir: str = "fonts"

    # ── Database ─────────────────────────────────────────────────
    database_url: str = f"sqlite:///{BASE_DIR}/postforge.db"

    # ── Image Generation ─────────────────────────────────────────
    image_width: int = 1080
    image_height: int = 1080
    image_format: str = "PNG"
    image_quality: int = 95

    # ── Watcher ──────────────────────────────────────────────────
    watcher_enabled: bool = True
    watcher_interval: int = 5

    # ── Future Integrations ──────────────────────────────────────
    instagram_access_token: str = ""
    instagram_account_id: str = ""
    instagram_api_version: str = "v21.0"

    google_drive_credentials_file: str = ""
    google_drive_folder_id: str = ""

    canva_api_key: str = ""
    canva_template_id: str = ""

    gemini_api_key: str = ""
    huggingface_token: str = ""
    image_renderer: str = "pillow"   # pillow | ai

    webhook_secret: str = ""
    webhook_publish_url: str = ""

    # ── Computed Paths ────────────────────────────────────────────
    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    def abs_path(self, relative: str) -> Path:
        return BASE_DIR / relative

    def ensure_dirs(self) -> None:
        """Create all required directories if they don't exist."""
        dirs = [
            self.input_inbox_dir,
            self.input_processed_dir,
            self.output_posts_dir,
            self.output_captions_dir,
            self.output_metadata_dir,
            self.output_logs_dir,
            self.config_brands_dir,
            self.assets_dir,
            self.fonts_dir,
        ]
        for d in dirs:
            self.abs_path(d).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
