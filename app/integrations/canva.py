"""
PostForge — Canva Integration (Stub)
Prepared for Canva Connect API / Design Automation.
In MVP: PostForge uses its own Pillow-based renderer.

To activate:
1. Set CANVA_API_KEY in .env
2. Create templates in Canva with autofill fields
3. Implement create_design() below using the Canva API
"""
from loguru import logger
from app.config import get_settings

settings = get_settings()


class CanvaClient:
    """Canva Connect API client (stub)."""

    def __init__(self):
        self.api_key = settings.canva_api_key
        self.template_id = settings.canva_template_id
        self.enabled = bool(self.api_key)

    def create_design(
        self,
        template_id: str,
        fields: dict,
        export_format: str = "png",
    ) -> dict:
        """
        Create a Canva design from a template with dynamic fields.
        Returns the exported file URL or path.
        """
        if not self.enabled:
            logger.info("[STUB] Canva design creation skipped — API key not configured.")
            return {
                "status": "simulated",
                "message": "Canva not configured. Using Pillow renderer instead.",
                "file_url": None,
            }
        raise NotImplementedError("Canva integration not yet implemented.")

    def export_design(self, design_id: str, format: str = "png") -> str:
        """Export a Canva design to a downloadable URL."""
        raise NotImplementedError


canva_client = CanvaClient()
