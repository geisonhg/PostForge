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
from app.integrations.ai_client import ai_client
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

# ── Claude generates the FLUX prompt ─────────────────────────────────────────

_PROMPT_SYSTEM = """\
You are an expert art director specializing in high-impact Instagram visuals for digital brands.
Your job: write ONE image generation prompt for FLUX (a diffusion model) that will serve as the background of an Instagram post.

The image MUST have text overlaid on top by another system — so never include text, words, letters, or UI elements in the prompt.

Rules:
- Write a single dense paragraph of 60-120 words
- Be extremely specific: lighting quality, color palette (use the exact hex codes), textures, atmosphere, composition, depth
- The visual must emotionally match the post's message and brand tone
- Specify that the lower half should be slightly darker to ensure text readability
- End with: "No text, no letters, no logos, no watermarks, no UI. Ultra high quality, 4K, professional photography or high-end digital art."
- Return ONLY the prompt — no explanations, no labels, nothing else"""


def _build_prompt(
    copy_data: dict[str, Any],
    visual_brief: VisualBrief,
    brand_config: dict[str, Any],
) -> str:
    vi       = brand_config.get("visual_identity", {})
    primary  = vi.get("primary_color", "#0057FF")
    accent   = vi.get("accent_color",  "#00FF88")
    industry = brand_config.get("industry", "digital agency")
    brand    = brand_config.get("name", "brand")
    tone     = brand_config.get("voice", {}).get("tone", "professional")
    title    = copy_data.get("title") or copy_data.get("overlay_text", "")
    hook     = copy_data.get("hook", "")

    user_msg = f"""\
Create a FLUX background image prompt for this Instagram post:

Brand: {brand} ({industry})
Brand colors: primary={primary}, accent={accent}
Brand tone: {tone}
Visual template: {visual_brief.template_family}
Color mood: {visual_brief.color_mood}

Post headline: "{title}"
Post hook: "{hook}"

The background must be visually stunning, scroll-stopping, and emotionally aligned with the message above."""

    try:
        logger.info("Asking Claude to craft FLUX prompt…")
        prompt = ai_client.complete(user_msg, system=_PROMPT_SYSTEM, max_tokens=200, temperature=0.85)
        logger.info(f"FLUX prompt (Claude) → {prompt[:120]}…")
        return prompt.strip()
    except Exception as e:
        logger.warning(f"Claude unavailable ({e}), using fallback prompt builder.")
        return _fallback_prompt(title, visual_brief, brand_config)


def _fallback_prompt(title: str, visual_brief: VisualBrief, brand_config: dict[str, Any]) -> str:
    """Build a solid FLUX prompt without Claude when API credits are unavailable."""
    vi      = brand_config.get("visual_identity", {})
    primary = vi.get("primary_color", "#0057FF")
    accent  = vi.get("accent_color",  "#00FF88")
    industry = brand_config.get("industry", "digital agency")

    mood_map = {
        "dark":     f"deep dark background, dramatic shadows, high contrast, dominant {primary} tones with {accent} glowing accents",
        "light":    f"bright airy composition, soft light, clean whitespace, {primary} and {accent} subtle accents",
        "gradient": f"rich vibrant gradient from {primary} to {accent}, dynamic and energetic",
    }
    template_map = {
        "bold_authority":    "bold geometric shapes, strong diagonal lines, commanding composition",
        "premium_dark_tech": "glowing circuit-like abstract lines, particles floating in space, futuristic bloom effects",
        "educational_card":  "clean grid lines, soft geometric shapes, calm and trustworthy atmosphere",
        "problem_solution":  "split composition dark-to-light, diagonal transition, transformation metaphor",
        "case_study_proof":  "upward trending abstract data shapes, confident dark slate, growth-inspired elements",
        "minimal_founder":   "minimal editorial whitespace, single accent stripe, refined linen texture",
        "clean_saas":        "rounded soft shapes, purple-blue gradient, airy modern SaaS aesthetic",
        "image_led_overlay": "cinematic depth of field, rich bokeh, layered atmospheric gradients",
    }
    mood    = mood_map.get(visual_brief.color_mood, mood_map["dark"])
    details = template_map.get(visual_brief.template_family, template_map["bold_authority"])

    prompt = (
        f"Instagram post background for a {industry} brand. {mood}. "
        f"{details}. "
        f"The lower half slightly darker for text readability. "
        f"Ultra high quality, 4K, professional. "
        f"No text, no letters, no logos, no watermarks, no UI."
    )
    logger.info(f"FLUX prompt (fallback) → {prompt[:120]}…")
    return prompt


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
        prompt = _build_prompt(copy_data, visual_brief, brand_config)
        img    = self._generate_background(prompt)
        _apply_text_overlay(img, copy_data, layout, brand_config, visual_brief)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=False)
        return buf.getvalue()


ai_renderer = AIRenderer()
