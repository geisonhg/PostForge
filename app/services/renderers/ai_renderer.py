"""
PostForge — AI Background Renderer
Generates a high-quality background via HuggingFace FLUX.1-schnell,
then composites text / CTA / watermark on top using Pillow layers.

Swap _generate_background() to use Gemini Imagen 4 when billing is enabled.
"""
import io
from typing import Any

import httpx
from loguru import logger
from PIL import Image, ImageDraw

from app.config import get_settings
from app.services.design_renderer_interface import (
    DesignRendererInterface,
    LayoutMap,
    VisualBrief,
)
from app.services.renderers.layers.cta import draw_cta_bar
from app.services.renderers.layers.typography import (
    draw_text_centered,
    draw_stat_centered,
)
from app.services.renderers.layers.watermark import draw_watermark

# ── HuggingFace model ────────────────────────────────────────────────────────

_HF_ENDPOINT = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

# ── Template → visual prompt mapping ────────────────────────────────────────

_TEMPLATE_PROMPTS: dict[str, str] = {
    "bold_authority": (
        "Bold dark authority composition, deep navy or charcoal gradient, "
        "strong geometric lines, subtle gold or white accent edges. "
        "Professional, commanding, modern abstract background."
    ),
    "premium_dark_tech": (
        "Premium dark technology aesthetic, deep black background, "
        "glowing cyan or electric blue circuit-like abstract lines and particles, "
        "futuristic polished high-end tech feel, subtle light bloom effects."
    ),
    "educational_card": (
        "Clean light educational background, soft white or pale blue, "
        "subtle grid lines and minimal geometric shapes, "
        "calm trustworthy modern infographic style, plenty of clean space."
    ),
    "problem_solution": (
        "Split-mood abstract background, left side dark moody tones, "
        "right side bright hopeful light, diagonal division with soft gradient transition, "
        "represents transformation and solutions."
    ),
    "case_study_proof": (
        "Confident proof-of-results background, dark slate, "
        "subtle upward trending lines and data visualization shapes, "
        "gold or green accent elements suggesting growth and achievement."
    ),
    "minimal_founder": (
        "Minimal editorial founder-style background, warm off-white or cream, "
        "single bold accent color strip, clean lines, sophisticated whitespace, "
        "subtle texture like linen or paper grain."
    ),
    "clean_saas": (
        "Clean modern SaaS product background, light gray to white gradient, "
        "soft purple or blue accent shapes, rounded abstract forms, "
        "airy and modern like a premium software product."
    ),
    "image_led_overlay": (
        "Cinematic vibrant abstract background, rich colors and depth, "
        "bokeh light effects and layered gradients, dramatic and eye-catching, "
        "dark enough for white text overlay."
    ),
}

_COLOR_MOOD_HINTS: dict[str, str] = {
    "dark":     "Very dark tones, deep shadows, high contrast, dark background.",
    "light":    "Bright airy tones, light background, soft shadows.",
    "gradient": "Rich colorful gradient, vibrant and dynamic.",
}


def _build_prompt(visual_brief: VisualBrief, brand_config: dict[str, Any]) -> str:
    base = _TEMPLATE_PROMPTS.get(visual_brief.template_family, _TEMPLATE_PROMPTS["bold_authority"])
    mood = _COLOR_MOOD_HINTS.get(visual_brief.color_mood, "")
    vi   = brand_config.get("visual_identity", {})
    primary = vi.get("primary_color", "#0057FF")
    accent  = vi.get("accent_color",  "#00FF88")
    industry = brand_config.get("industry", "digital agency")

    return (
        f"Instagram post background image, 1:1 square format. "
        f"{base} {mood} "
        f"Color palette inspired by {primary} and {accent}. "
        f"Industry: {industry}. "
        "Ultra high quality, suitable for placing white text on top. "
        "No text, no people, no logos, no watermarks."
    )


# ── Text overlay helpers ──────────────────────────────────────────────────────

def _apply_text_overlay(
    img: Image.Image,
    copy_data: dict[str, Any],
    layout: LayoutMap,
    brand_config: dict[str, Any],
    visual_brief: VisualBrief,
) -> None:
    vi      = brand_config.get("visual_identity", {})
    accent  = vi.get("accent_color",  "#00FF88")
    primary = vi.get("primary_color", "#0057FF")

    # Readability scrim
    scrim = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd    = ImageDraw.Draw(scrim)
    base_alpha = 110 if visual_brief.color_mood == "light" else 90

    if visual_brief.layout_style == "split":
        sd.rectangle([0, 0, img.width // 2, img.height], fill=(0, 0, 0, 160))
    else:
        for y in range(img.height):
            a = int(base_alpha * (y / img.height) ** 0.65)
            sd.line([(0, y), (img.width, y)], fill=(0, 0, 0, a))

    img.paste(Image.alpha_composite(img.convert("RGBA"), scrim).convert("RGB"), (0, 0))

    # Accent bar above headline
    draw = ImageDraw.Draw(img)
    bx = layout.padding_x
    by = layout.headline_y - layout.headline_size // 2 - 22
    r, g, b = tuple(int(accent.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    draw.rectangle([bx, by, bx + 56, by + 5], fill=(r, g, b))

    # Headline
    title = copy_data.get("title") or copy_data.get("overlay_text", "")
    if title:
        draw_text_centered(img, title, layout.headline_y, layout.headline_size,
                           "#FFFFFF", layout.headline_max_w, bold=True, shadow=True)

    # Hook / sub-headline
    if layout.show_sub:
        hook = copy_data.get("hook", "")
        if hook:
            draw_text_centered(img, hook, layout.sub_y, layout.sub_size,
                               "#E0E0E0", layout.sub_max_w, bold=False)

    # Stat highlight
    if layout.show_stat:
        stat = copy_data.get("stat", "")
        if stat:
            draw_stat_centered(img, stat, layout.stat_y, layout.stat_size, accent)

    # CTA bar
    if layout.show_cta_bar:
        cta = copy_data.get("cta", "")
        if cta:
            draw_cta_bar(img, cta, layout.cta_bar_y, bg_color=primary, size=layout.cta_size)

    draw_watermark(img, brand_config)


# ── Renderer ─────────────────────────────────────────────────────────────────

class AIRenderer(DesignRendererInterface):
    """
    Renders Instagram posts using FLUX.1-schnell (HuggingFace) for the background,
    then composites text/CTA/watermark with Pillow.
    """

    def _generate_background(self, prompt: str) -> Image.Image:
        token = get_settings().huggingface_token
        if not token:
            raise ValueError("HUGGINGFACE_TOKEN is not set in .env")

        logger.info(f"Calling FLUX.1-schnell | {prompt[:100]}…")
        r = httpx.post(
            _HF_ENDPOINT,
            json={"inputs": prompt, "parameters": {"width": 1080, "height": 1080}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=120,
        )
        r.raise_for_status()

        img = Image.open(io.BytesIO(r.content)).convert("RGB")
        if img.size != (1080, 1080):
            img = img.resize((1080, 1080), Image.LANCZOS)

        logger.info("FLUX background generated successfully.")
        return img

    def render(
        self,
        copy_data: dict[str, Any],
        visual_brief: VisualBrief,
        layout: LayoutMap,
        brand_config: dict[str, Any],
        input_image_path: str | None = None,
    ) -> bytes:
        prompt = _build_prompt(visual_brief, brand_config)
        img    = self._generate_background(prompt)
        _apply_text_overlay(img, copy_data, layout, brand_config, visual_brief)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=False)
        return buf.getvalue()


ai_renderer = AIRenderer()
