"""
PostForge — Instagram Integration (Stub)
Ready to connect with Meta Graph API v21.0.
In MVP: simulates publishing and logs the action.

To activate in production:
1. Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID in .env
2. Implement _upload_image() and _publish_container() below
3. Handle rate limits and error codes per Meta docs
"""
from pathlib import Path
from loguru import logger

from app.config import get_settings

settings = get_settings()

GRAPH_API_BASE = f"https://graph.facebook.com/{settings.instagram_api_version}"


class InstagramPublisher:
    """
    Meta Graph API client for Instagram publishing.
    Workflow: upload image → create container → publish container
    """

    def __init__(self):
        self.access_token = settings.instagram_access_token
        self.account_id = settings.instagram_account_id
        self.enabled = bool(self.access_token and self.account_id)

    def publish_post(
        self,
        image_path: str,
        caption: str,
        job_id: str,
    ) -> dict:
        """
        Publish a single image post to Instagram.
        Returns a result dict with status and post_id.
        """
        if not self.enabled:
            logger.info(
                f"[STUB] Instagram publish skipped (no credentials). "
                f"job_id={job_id} image={image_path}"
            )
            return {
                "status": "simulated",
                "job_id": job_id,
                "message": "Instagram credentials not configured. Post simulated.",
                "post_id": None,
            }

        # TODO: implement real publishing flow
        # container_id = self._create_container(image_path, caption)
        # post_id = self._publish_container(container_id)
        logger.warning("Instagram real publishing not yet implemented.")
        return {"status": "not_implemented", "job_id": job_id}

    def _create_container(self, image_url: str, caption: str) -> str:
        """Step 1: Upload image and create media container."""
        # POST /{account_id}/media
        raise NotImplementedError

    def _publish_container(self, container_id: str) -> str:
        """Step 2: Publish the created container."""
        # POST /{account_id}/media_publish
        raise NotImplementedError

    def get_account_info(self) -> dict:
        """Retrieve Instagram account details."""
        if not self.enabled:
            return {"status": "not_configured"}
        raise NotImplementedError


instagram_publisher = InstagramPublisher()
