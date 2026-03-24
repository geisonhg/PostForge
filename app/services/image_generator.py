"""
PostForge — Image Generator
Thin orchestrator: receives copy_data + brand_id + optional input image,
delegates visual strategy → layout planning → rendering to the new pipeline.
"""
import json
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import get_settings
from app.services.design_renderer_interface import VisualBrief, LayoutMap
from app.services.layout_engine import layout_engine
from app.services.renderers.pillow_renderer import pillow_renderer

settings = get_settings()


class ImageGenerator:

    def load_brand_config(self, brand_id: str) -> dict:
        path = settings.abs_path(settings.config_brands_dir) / f"{brand_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        logger.warning(f"Brand config not found for '{brand_id}'")
        return {}

    # Maps legacy/shorthand template names to current template_family values
    _TEMPLATE_ALIASES: dict[str, str] = {
        "gradient_text": "bold_authority",
        "dark_tech": "premium_dark_tech",
        "split_layout": "problem_solution",
        "photo_overlay": "image_led_overlay",
    }

    def generate(
        self,
        copy_data: dict[str, Any],
        brand_id: str = "confluex",
        input_image_path: str | None = None,
        visual_brief: VisualBrief | None = None,
        template: str | None = None,
    ) -> bytes:
        """
        Generate a 1080×1080 PNG and return raw bytes.

        Priority order for template selection:
          1. explicit visual_brief (full pipeline)
          2. explicit template name / alias
          3. heuristic fallback based on copy_data content
        """
        brand_config = self.load_brand_config(brand_id)

        if visual_brief is None:
            if template and template != "auto":
                family = self._TEMPLATE_ALIASES.get(template, template)
                color_mood = "dark" if "dark" in family or "tech" in family else "gradient"
                visual_brief = VisualBrief(template_family=family, color_mood=color_mood)
            else:
                visual_brief = self._heuristic_brief(copy_data, input_image_path)

        layout = layout_engine.plan(copy_data, visual_brief, brand_config)

        logger.info(
            f"Generating image: template={visual_brief.template_family} "
            f"mood={visual_brief.color_mood} brand={brand_id}"
        )

        return pillow_renderer.render(
            copy_data=copy_data,
            visual_brief=visual_brief,
            layout=layout,
            brand_config=brand_config,
            input_image_path=input_image_path,
        )

    def _heuristic_brief(
        self,
        copy_data: dict[str, Any],
        input_image_path: str | None,
    ) -> VisualBrief:
        """Deterministic fallback when visual_strategist is not in the pipeline."""
        if input_image_path:
            return VisualBrief(template_family="image_led_overlay", color_mood="dark")

        strategy = copy_data.get("_strategy", {})
        framework = strategy.get("framework", "")
        content_type = strategy.get("content_type", "")

        if framework == "problem_solution":
            return VisualBrief(template_family="problem_solution", color_mood="dark", layout_style="split")
        if content_type == "social_proof" or framework == "project_highlight":
            return VisualBrief(template_family="case_study_proof", color_mood="dark", show_stat=True)
        if framework == "educational_tip":
            return VisualBrief(template_family="educational_card", color_mood="light", layout_style="minimal")
        if framework == "branding":
            return VisualBrief(template_family="minimal_founder", color_mood="light", layout_style="edge")
        if framework == "automation":
            return VisualBrief(template_family="premium_dark_tech", color_mood="dark", glow_enabled=True)
        if content_type in ("conversion", "promotional"):
            return VisualBrief(template_family="premium_dark_tech", color_mood="gradient", glow_enabled=True)

        return VisualBrief(template_family="bold_authority", color_mood="dark")


image_generator = ImageGenerator()
