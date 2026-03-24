"""
PostForge — Google Drive Integration (Stub)
Prepared for automatic upload of generated posts to Drive.

To activate:
1. Create a Google Cloud project and enable Drive API
2. Download credentials JSON and set GOOGLE_DRIVE_CREDENTIALS_FILE in .env
3. Set GOOGLE_DRIVE_FOLDER_ID to your target folder
4. Install: pip install google-api-python-client google-auth
"""
from pathlib import Path
from loguru import logger
from app.config import get_settings

settings = get_settings()


class GoogleDriveClient:
    """Google Drive API client (stub)."""

    def __init__(self):
        self.credentials_file = settings.google_drive_credentials_file
        self.folder_id = settings.google_drive_folder_id
        self.enabled = bool(self.credentials_file and self.folder_id)

    def upload_file(self, file_path: str, folder_id: str = "") -> dict:
        """
        Upload a file to Google Drive.
        Returns file metadata including shareable URL.
        """
        if not self.enabled:
            logger.info(
                f"[STUB] Google Drive upload skipped — not configured. "
                f"file={file_path}"
            )
            return {
                "status": "simulated",
                "message": "Google Drive not configured.",
                "file_id": None,
                "web_view_link": None,
            }
        raise NotImplementedError("Google Drive integration not yet implemented.")

    def create_folder(self, name: str, parent_id: str = "") -> str:
        """Create a folder in Drive and return its ID."""
        raise NotImplementedError

    def list_files(self, folder_id: str) -> list:
        """List files in a Drive folder."""
        raise NotImplementedError


google_drive_client = GoogleDriveClient()
