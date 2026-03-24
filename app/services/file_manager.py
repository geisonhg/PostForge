"""
PostForge — File Manager
Handles all file I/O: organizing outputs, moving inputs, writing metadata.
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import get_settings

settings = get_settings()


class FileManager:

    def job_output_dir(self, job_id: str) -> Path:
        """Returns the dedicated output directory for a job."""
        path = settings.abs_path(settings.output_posts_dir) / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def captions_dir(self, job_id: str) -> Path:
        path = settings.abs_path(settings.output_captions_dir) / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def metadata_dir(self, job_id: str) -> Path:
        path = settings.abs_path(settings.output_metadata_dir) / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_image(self, job_id: str, image_bytes: bytes, filename: str = "post.png") -> Path:
        """Save final image bytes to the job's output directory."""
        dest = self.job_output_dir(job_id) / filename
        dest.write_bytes(image_bytes)
        logger.info(f"Image saved → {dest}")
        return dest

    def save_caption(self, job_id: str, copy_data: dict) -> Path:
        """Save caption/copy as a structured JSON file."""
        dest = self.captions_dir(job_id) / "caption.json"
        dest.write_text(json.dumps(copy_data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Also save a plain-text version for easy copy-paste
        txt_dest = self.captions_dir(job_id) / "caption.txt"
        txt_content = self._build_caption_text(copy_data)
        txt_dest.write_text(txt_content, encoding="utf-8")

        logger.info(f"Caption saved → {dest}")
        return dest

    def save_metadata(self, job_id: str, metadata: dict) -> Path:
        """Persist job metadata as JSON."""
        metadata["saved_at"] = datetime.now(timezone.utc).isoformat()
        dest = self.metadata_dir(job_id) / "metadata.json"
        dest.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Metadata saved → {dest}")
        return dest

    def move_to_processed(self, source_path: str) -> Path:
        """Move an input file from inbox to processed after handling."""
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        dest_dir = settings.abs_path(settings.input_processed_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Avoid collision with timestamp prefix
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = dest_dir / f"{timestamp}_{src.name}"
        shutil.move(str(src), str(dest))
        logger.info(f"Input moved to processed → {dest}")
        return dest

    def list_inbox_files(self) -> list[Path]:
        """Return all files currently in the inbox directory."""
        inbox = settings.abs_path(settings.input_inbox_dir)
        return [
            f for f in inbox.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]

    def _build_caption_text(self, copy_data: dict) -> str:
        """Format caption data as a clean plain-text document."""
        lines = []
        if copy_data.get("title"):
            lines.append(f"TITLE\n{copy_data['title']}\n")
        if copy_data.get("hook"):
            lines.append(f"HOOK\n{copy_data['hook']}\n")
        if copy_data.get("caption_long"):
            lines.append(f"CAPTION (LONG)\n{copy_data['caption_long']}\n")
        if copy_data.get("caption_short"):
            lines.append(f"CAPTION (SHORT)\n{copy_data['caption_short']}\n")
        if copy_data.get("cta"):
            lines.append(f"CTA\n{copy_data['cta']}\n")
        if copy_data.get("hashtags"):
            lines.append(f"HASHTAGS\n{copy_data['hashtags']}\n")
        if copy_data.get("overlay_text"):
            lines.append(f"OVERLAY TEXT\n{copy_data['overlay_text']}\n")
        return "\n".join(lines)

    def get_job_files(self, job_id: str) -> dict[str, Any]:
        """Return a summary of all files generated for a job."""
        return {
            "image": str(self.job_output_dir(job_id) / "post.png"),
            "caption_json": str(self.captions_dir(job_id) / "caption.json"),
            "caption_txt": str(self.captions_dir(job_id) / "caption.txt"),
            "metadata": str(self.metadata_dir(job_id) / "metadata.json"),
        }


file_manager = FileManager()
