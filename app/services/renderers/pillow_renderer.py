"""
PostForge — Pillow Renderer
Implements DesignRendererInterface using PIL/Pillow.
Dispatches to one of 8 template family methods based on VisualBrief.
"""
import io
from typing import Any

from PIL import Image
from loguru import logger

from app.services.design_renderer_interface import (
    DesignRendererInterface, VisualBrief, LayoutMap
)
from app.services.renderers.layers.background import (
    draw_gradient_bg, draw_solid_bg, draw_image_bg, draw_noise_texture
)
from app.services.renderers.layers.decorations import (
    draw_glow, draw_accent_bar, draw_dot_grid, draw_geo_lines,
    draw_divider_line, draw_split_panel, draw_grid_lines
)
from app.services.renderers.layers.typography import (
    draw_text_centered, draw_text_left, draw_stat_centered, draw_badge
)
from app.services.renderers.layers.cta import draw_cta_bar, draw_cta_pill
from app.services.renderers.layers.watermark import draw_watermark

W = H = 1080


def _vi(brand_config: dict) -> dict:
    return brand_config.get("visual_identity", {})


class PillowRenderer(DesignRendererInterface):

    TEMPLATE_MAP = {
        "bold_authority":     "_render_bold_authority",
        "clean_saas":         "_render_clean_saas",
        "premium_dark_tech":  "_render_premium_dark_tech",
        "educational_card":   "_render_educational_card",
        "problem_solution":   "_render_problem_solution",
        "case_study_proof":   "_render_case_study_proof",
        "minimal_founder":    "_render_minimal_founder",
        "image_led_overlay":  "_render_image_led_overlay",
    }

    def render(
        self,
        copy_data: dict[str, Any],
        visual_brief: VisualBrief,
        layout: LayoutMap,
        brand_config: dict[str, Any],
        input_image_path: str | None = None,
    ) -> bytes:
        method_name = self.TEMPLATE_MAP.get(visual_brief.template_family, "_render_bold_authority")
        method = getattr(self, method_name)
        logger.info(f"Rendering template: {visual_brief.template_family}")
        try:
            img = method(copy_data, visual_brief, layout, brand_config, input_image_path)
        except Exception as e:
            logger.error(f"Template {visual_brief.template_family} failed: {e}. Using fallback.")
            img = self._render_bold_authority(copy_data, visual_brief, layout, brand_config, input_image_path)

        draw_watermark(img, brand_config)

        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    # ── 1. Bold Authority ─────────────────────────────────────────────────────

    def _render_bold_authority(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H))

        draw_gradient_bg(img, vi.get("dark_color", "#080C18"), vi.get("surface_color", "#0F1629"), "linear_tb")

        if vb.glow_enabled:
            draw_glow(img, W // 2, H // 3, 420, vi.get("primary_color", "#0057FF"), alpha=55)

        if vb.accent_style == "bar":
            draw_accent_bar(img, W // 2 - 40, layout.headline_y - 70, 80, 6, vi.get("accent_color", "#00FF88"))
        elif vb.accent_style == "geo":
            draw_geo_lines(img, vi.get("primary_color", "#0057FF"), alpha=45)

        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        draw_text_centered(img, headline, layout.headline_y, layout.headline_size,
                           "#FFFFFF", layout.headline_max_w, bold=True, shadow=True)

        if layout.show_sub:
            hook = copy_data.get("hook", "")
            draw_text_centered(img, hook, layout.sub_y, layout.sub_size,
                               "#CCCCCC", layout.sub_max_w, bold=False)

        if layout.show_cta_bar:
            cta = copy_data.get("cta", "")
            draw_cta_bar(img, cta, layout.cta_bar_y, vi.get("primary_color", "#0057FF"), "#FFFFFF", layout.cta_size)

        return img

    # ── 2. Clean SaaS ─────────────────────────────────────────────────────────

    def _render_clean_saas(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H), (248, 249, 252))

        draw_noise_texture(img, intensity=6)

        # Top accent bar
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        primary = vi.get("primary_color", "#0057FF")
        r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)
        draw.rectangle([0, 0, W, 8], fill=(r, g, b))

        if vb.accent_style == "dot_grid":
            draw_dot_grid(img, W - 200, 60, cols=8, rows=12, spacing=22, dot_r=2,
                          color=vi.get("primary_color", "#0057FF"), alpha=35)

        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        draw_text_centered(img, headline, layout.headline_y, layout.headline_size,
                           "#0A0A0A", layout.headline_max_w, bold=True)

        draw_accent_bar(img, W // 2 - 30, layout.headline_y + layout.headline_size // 2 + 16,
                        60, 4, vi.get("accent_color", "#00FF88"))

        if layout.show_sub:
            hook = copy_data.get("hook", "")
            draw_text_centered(img, hook, layout.sub_y, layout.sub_size,
                               "#444444", layout.sub_max_w, bold=False)

        if layout.show_cta_bar:
            cta = copy_data.get("cta", "")
            draw_cta_bar(img, cta, layout.cta_bar_y, vi.get("primary_color", "#0057FF"), "#FFFFFF", layout.cta_size)

        return img

    # ── 3. Premium Dark Tech ───────────────────────────────────────────────────

    def _render_premium_dark_tech(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H))

        draw_gradient_bg(img, vi.get("dark_color", "#080C18"),
                         vi.get("gradient_end", "#00D4FF") + "22",
                         vb.gradient_direction or "diagonal")
        draw_gradient_bg(img, vi.get("dark_color", "#080C18"), "#0d1f3c", "linear_tb")

        draw_grid_lines(img, vi.get("primary_color", "#0057FF"), alpha=20)
        draw_geo_lines(img, vi.get("secondary_color", "#00D4FF"), alpha=35)

        if vb.glow_enabled:
            draw_glow(img, W // 4, H // 4, 300, vi.get("primary_color", "#0057FF"), alpha=45)
            draw_glow(img, W * 3 // 4, H * 2 // 3, 260, vi.get("secondary_color", "#00D4FF"), alpha=30)

        if layout.show_stat:
            stat = vb.raw.get("suggested_stat", "")
            if stat:
                draw_stat_centered(img, str(stat), layout.stat_y, layout.stat_size,
                                   vi.get("accent_color", "#00FF88"),
                                   label="resultado comprobado", label_size=22, label_color="#888888")

        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        draw_text_centered(img, headline, layout.headline_y, layout.headline_size,
                           "#FFFFFF", layout.headline_max_w, bold=True, shadow=True)

        if layout.show_sub:
            hook = copy_data.get("hook", "")
            draw_text_centered(img, hook, layout.sub_y, layout.sub_size,
                               vi.get("secondary_color", "#00D4FF"), layout.sub_max_w, bold=False)

        if layout.show_cta_bar:
            cta = copy_data.get("cta", "")
            draw_cta_bar(img, cta, layout.cta_bar_y,
                         vi.get("gradient_start", "#0057FF"), "#FFFFFF", layout.cta_size)

        return img

    # ── 4. Educational Card ───────────────────────────────────────────────────

    def _render_educational_card(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H), (245, 247, 252))

        draw_noise_texture(img, intensity=5)

        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        primary = vi.get("primary_color", "#0057FF")
        r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)
        # Card background
        draw.rounded_rectangle([60, 80, W - 60, H - 80], radius=24, fill=(255, 255, 255))
        # Top color bar inside card
        draw.rounded_rectangle([60, 80, W - 60, 160], radius=24, fill=(r, g, b))

        if vb.accent_style == "dot_grid":
            draw_dot_grid(img, W - 160, 180, cols=6, rows=8, spacing=20, dot_r=2,
                          color=vi.get("primary_color", "#0057FF"), alpha=30)

        # "TIP" badge
        draw_badge(img, "CONSEJO PRO", 100, 100, size=20,
                   bg_color="#FFFFFF", text_color=primary, padding_x=12, padding_y=6)

        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        draw_text_centered(img, headline, layout.headline_y, layout.headline_size,
                           "#1A1A2E", layout.headline_max_w - 80, bold=True)

        draw_divider_line(img, layout.headline_y + layout.headline_size // 2 + 20,
                          x_start=120, x_end=W - 120,
                          color=vi.get("primary_color", "#0057FF"), alpha=40)

        if layout.show_sub:
            hook = copy_data.get("hook", "")
            draw_text_centered(img, hook, layout.sub_y, layout.sub_size,
                               "#444455", layout.sub_max_w - 80, bold=False)

        if layout.show_cta_bar:
            cta = copy_data.get("cta", "")
            draw_cta_pill(img, cta, W // 2, layout.cta_bar_y + 40,
                          vi.get("primary_color", "#0057FF"), "#FFFFFF", layout.cta_size)

        return img

    # ── 5. Problem → Solution ─────────────────────────────────────────────────

    def _render_problem_solution(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H))
        split_x = W // 2

        draw_split_panel(img, split_x, "#1a0505", vi.get("dark_color", "#080C18"))

        # Glow on solution side
        if vb.glow_enabled:
            draw_glow(img, W * 3 // 4, H // 2, 300, vi.get("primary_color", "#0057FF"), alpha=50)

        # "ANTES" / "DESPUÉS" labels
        draw_badge(img, "ANTES", split_x // 2 - 40, 80, size=22,
                   bg_color="#cc2222", text_color="#FFFFFF")
        draw_badge(img, "DESPUÉS", split_x + split_x // 2 - 50, 80, size=22,
                   bg_color=vi.get("primary_color", "#0057FF"), text_color="#FFFFFF")

        # Divider line
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.line([(split_x, 0), (split_x, H)], fill=(80, 80, 100), width=2)

        # Problem side (left)
        main_objection = copy_data.get("_strategy", {}).get("main_objection", "")
        if not main_objection:
            main_objection = copy_data.get("hook", "")
        draw_text_centered(img, main_objection, H // 2, layout.headline_size - 12,
                           "#FF6666", split_x - 40, bold=True, shadow=True)

        # Solution side (right)
        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        draw_text_centered(img,
                           headline,
                           H // 2,
                           layout.headline_size - 12,
                           "#FFFFFF",
                           split_x - 40,
                           bold=True, shadow=True)
        # center offset for right side
        from PIL import ImageDraw as ID2
        d2 = ID2.Draw(img)
        from app.services.renderers.font_loader import font as fnt
        f = fnt(layout.headline_size - 12, bold=True)
        # Reposition: draw_text_centered draws at img center; we redraw on right side only
        # Clear with right panel color and redraw
        d2.rectangle([split_x + 1, 0, W, H], fill=_vi(brand_config).get("dark_color", "#080C18") or "#080C18")
        if vb.glow_enabled:
            draw_glow(img, W * 3 // 4, H // 2, 300, vi.get("primary_color", "#0057FF"), alpha=50)
        draw_text_left(img, headline, split_x + 40, H // 2,
                       layout.headline_size - 12, "#FFFFFF", split_x - 80, bold=True)

        if layout.show_cta_bar:
            cta = copy_data.get("cta", "")
            draw_cta_bar(img, cta, layout.cta_bar_y, vi.get("primary_color", "#0057FF"),
                         "#FFFFFF", layout.cta_size)

        return img

    # ── 6. Case Study / Proof ─────────────────────────────────────────────────

    def _render_case_study_proof(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H))

        draw_gradient_bg(img, "#080C18", "#0a1628", "linear_tb")
        draw_geo_lines(img, vi.get("primary_color", "#0057FF"), alpha=30)

        if vb.glow_enabled:
            draw_glow(img, W // 2, H // 2, 380, vi.get("accent_color", "#00FF88"), alpha=35)

        # Big stat
        stat = copy_data.get("_strategy", {}).get("suggested_stat", "")
        if not stat:
            stat = copy_data.get("overlay_text", "")
        draw_stat_centered(img, str(stat) if stat else "80%", H // 2 - 40,
                           layout.stat_size, vi.get("accent_color", "#00FF88"),
                           label="de reducción en tiempo operativo", label_size=24,
                           label_color="#888888")

        # Context above stat
        title = copy_data.get("title", "")
        draw_text_centered(img, title, H // 2 - layout.stat_size - 20, 34,
                           "#AAAAAA", layout.headline_max_w, bold=False)

        # Headline below stat
        headline = copy_data.get("overlay_text") or copy_data.get("hook", "")
        draw_text_centered(img, headline, H // 2 + layout.stat_size // 2 + 80,
                           layout.sub_size, "#FFFFFF", layout.sub_max_w, bold=True)

        if layout.show_cta_bar:
            cta = copy_data.get("cta", "")
            draw_cta_bar(img, cta, layout.cta_bar_y, vi.get("primary_color", "#0057FF"),
                         "#FFFFFF", layout.cta_size)

        return img

    # ── 7. Minimal Founder ────────────────────────────────────────────────────

    def _render_minimal_founder(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H), (252, 252, 250))
        draw_noise_texture(img, intensity=8)

        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        primary = vi.get("primary_color", "#0057FF")
        r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)
        # Left accent bar
        draw.rectangle([60, 120, 68, H - 120], fill=(r, g, b, 180) if img.mode == "RGBA" else (r, g, b))

        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        draw_text_left(img, headline, 100, layout.headline_y,
                       layout.headline_size, "#0A0A0A", layout.headline_max_w - 40, bold=True)

        draw_divider_line(img, layout.headline_y + layout.headline_size // 2 + 24,
                          x_start=100, x_end=400, color=vi.get("accent_color", "#00FF88"), alpha=200, width=3)

        if layout.show_sub:
            hook = copy_data.get("hook", "")
            draw_text_left(img, hook, 100, layout.sub_y,
                           layout.sub_size, "#555555", layout.sub_max_w - 40, bold=False)

        brand_name = brand_config.get("name", "")
        if brand_name:
            draw_text_left(img, brand_name, 100, H - 120, 28, primary, bold=True)

        return img

    # ── 8. Image-Led Overlay ──────────────────────────────────────────────────

    def _render_image_led_overlay(self, copy_data, vb, layout, brand_config, input_image_path):
        vi = _vi(brand_config)
        img = Image.new("RGB", (W, H))

        overlay_opacity = brand_config.get("layout", {}).get("overlay_opacity", 0.72)
        draw_image_bg(img, input_image_path, vi.get("dark_color", "#080C18"), overlay_opacity)

        if vb.glow_enabled:
            draw_glow(img, W // 2, H * 2 // 3, 350, vi.get("primary_color", "#0057FF"), alpha=40)

        if vb.accent_style == "bar":
            draw_accent_bar(img, W // 2 - 40, layout.headline_y - 65, 80, 6,
                            vi.get("accent_color", "#00FF88"))

        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        draw_text_centered(img, headline, layout.headline_y, layout.headline_size,
                           "#FFFFFF", layout.headline_max_w, bold=True, shadow=True, shadow_offset=4)

        if layout.show_sub:
            hook = copy_data.get("hook", "")
            draw_text_centered(img, hook, layout.sub_y, layout.sub_size,
                               "#DDDDDD", layout.sub_max_w, bold=False, shadow=True)

        if layout.show_cta_bar:
            cta = copy_data.get("cta", "")
            draw_cta_bar(img, cta, layout.cta_bar_y, vi.get("primary_color", "#0057FF"),
                         "#FFFFFF", layout.cta_size, alpha=210)

        return img


pillow_renderer = PillowRenderer()
