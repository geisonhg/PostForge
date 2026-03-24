"""
PostForge — Layout Engine
Converts a VisualBrief + copy_data into a concrete LayoutMap:
exact font sizes, vertical positions, padding — no guessing inside renderers.

Rules:
- Measures real text extents using PIL to detect overflow before commit
- Shrinks font sizes until text fits within max width
- Distributes elements vertically with minimum gaps (vertical rhythm)
- Special handling for stat-led, split, and minimal layouts
"""
from typing import Any

from PIL import ImageDraw, Image
from loguru import logger

from app.services.design_renderer_interface import VisualBrief, LayoutMap
from app.services.renderers.font_loader import font

# Canvas constants
W = H = 1080
PAD_X = 80          # horizontal margin each side
SAFE_W = W - PAD_X * 2   # 920 px
CTA_BAR_H = 80      # height of bottom CTA strip
CTA_BAR_TOP = H - CTA_BAR_H   # y=1000

# Minimum/maximum font sizes
HEADLINE_MIN = 44
HEADLINE_MAX = 96
SUB_MIN = 22
SUB_MAX = 48
STAT_MIN = 80
STAT_MAX = 160


def _text_width(text: str, size: int, bold: bool = True) -> int:
    """Return pixel width of text rendered at given size."""
    f = font(size, bold)
    # Use a scratch image to measure
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=f)
    return bbox[2] - bbox[0]


def _fit_size(text: str, max_w: int, start_size: int, min_size: int, bold: bool = True) -> int:
    """Shrink font size until text fits in max_w. Returns resolved size."""
    size = min(start_size, HEADLINE_MAX if bold else SUB_MAX)
    while size > min_size:
        if _text_width(text, size, bold) <= max_w:
            return size
        size -= 2
    return min_size


def _multiline_height(text: str, size: int, max_w: int, bold: bool = True, line_spacing: float = 1.35) -> int:
    """Return total pixel height of wrapped text block."""
    words = text.split()
    f = font(size, bold)
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)

    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=f)
        if bbox[2] - bbox[0] > max_w and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))

    if not lines:
        return size

    bbox = draw.textbbox((0, 0), "Ag", font=f)
    line_h = int((bbox[3] - bbox[1]) * line_spacing)
    return line_h * len(lines)


class LayoutEngine:

    def plan(
        self,
        copy_data: dict[str, Any],
        visual_brief: VisualBrief,
        brand_config: dict[str, Any],
    ) -> LayoutMap:
        """
        Produce a LayoutMap for the given VisualBrief + copy_data.
        Delegates to specialized planners per layout_style.
        """
        layout_style = visual_brief.layout_style
        try:
            if layout_style == "split":
                return self._plan_split(copy_data, visual_brief)
            elif layout_style == "minimal":
                return self._plan_minimal(copy_data, visual_brief)
            elif layout_style == "edge":
                return self._plan_edge(copy_data, visual_brief)
            else:
                return self._plan_centered(copy_data, visual_brief)
        except Exception as e:
            logger.warning(f"Layout planning failed ({layout_style}): {e}. Using safe defaults.")
            return self._safe_defaults(visual_brief)

    # ── Centered layout (most common) ────────────────────────────────────────

    def _plan_centered(self, copy_data: dict, vb: VisualBrief) -> LayoutMap:
        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        sub = copy_data.get("hook", "")
        stat = vb.show_stat and vb.raw.get("suggested_stat") or ""
        show_stat = bool(vb.show_stat and stat)
        show_sub = bool(vb.show_sub_headline and sub)

        # Resolve font sizes
        hl_size = _fit_size(headline, SAFE_W, vb.headline_size_hint, HEADLINE_MIN, bold=True)
        sub_size = _fit_size(sub[:60], SAFE_W, vb.sub_size_hint, SUB_MIN, bold=False) if show_sub else 0
        stat_size = _fit_size(str(stat)[:20], SAFE_W, 120, STAT_MIN, bold=True) if show_stat else 0

        # Heights of each block
        hl_h = _multiline_height(headline, hl_size, SAFE_W, bold=True)
        sub_h = _multiline_height(sub, sub_size, SAFE_W, bold=False) if show_sub else 0
        stat_h = stat_size if show_stat else 0

        # Total content height (with gaps)
        gap = 28
        total_content = hl_h + (gap + sub_h if show_sub else 0) + (gap + stat_h if show_stat else 0)

        # Center the content block vertically, accounting for CTA bar
        usable_h = (CTA_BAR_TOP if vb.show_cta_bar else H) - 100  # top padding 100
        content_top = 100 + max(0, (usable_h - total_content) // 2)

        # Assign y positions
        if show_stat:
            stat_y = content_top + stat_h // 2
            hl_y = stat_y + stat_h // 2 + gap + hl_h // 2
        else:
            stat_y = H // 2
            hl_y = content_top + hl_h // 2

        sub_y = hl_y + hl_h // 2 + gap + sub_h // 2 if show_sub else hl_y + 60

        return LayoutMap(
            headline_size=hl_size,
            sub_size=sub_size or vb.sub_size_hint,
            cta_size=vb.cta_size_hint,
            stat_size=stat_size or 120,
            headline_y=int(hl_y),
            sub_y=int(sub_y),
            stat_y=int(stat_y),
            cta_bar_y=CTA_BAR_TOP,
            padding_x=PAD_X,
            headline_max_w=SAFE_W,
            sub_max_w=SAFE_W,
            show_stat=show_stat,
            show_sub=show_sub,
            show_cta_bar=vb.show_cta_bar,
        )

    # ── Split layout (problem_solution) ──────────────────────────────────────

    def _plan_split(self, copy_data: dict, vb: VisualBrief) -> LayoutMap:
        # Split doesn't need tight font fitting — fixed layout
        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        hl_size = _fit_size(headline, SAFE_W // 2 - 20, vb.headline_size_hint, HEADLINE_MIN, bold=True)

        return LayoutMap(
            headline_size=hl_size,
            sub_size=vb.sub_size_hint,
            cta_size=vb.cta_size_hint,
            stat_size=96,
            headline_y=H // 2,
            sub_y=H // 2 + 80,
            stat_y=H // 2 - 80,
            cta_bar_y=CTA_BAR_TOP,
            padding_x=PAD_X,
            headline_max_w=SAFE_W // 2 - 20,
            sub_max_w=SAFE_W // 2 - 20,
            show_stat=vb.show_stat,
            show_sub=vb.show_sub_headline,
            show_cta_bar=vb.show_cta_bar,
        )

    # ── Minimal layout (clean_saas, minimal_founder) ─────────────────────────

    def _plan_minimal(self, copy_data: dict, vb: VisualBrief) -> LayoutMap:
        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        hl_size = _fit_size(headline, SAFE_W - 40, vb.headline_size_hint, HEADLINE_MIN, bold=True)

        return LayoutMap(
            headline_size=hl_size,
            sub_size=vb.sub_size_hint,
            cta_size=vb.cta_size_hint,
            stat_size=100,
            headline_y=360,
            sub_y=500,
            stat_y=260,
            cta_bar_y=CTA_BAR_TOP,
            padding_x=PAD_X + 20,
            headline_max_w=SAFE_W - 40,
            sub_max_w=SAFE_W - 40,
            show_stat=False,
            show_sub=True,
            show_cta_bar=vb.show_cta_bar,
        )

    # ── Edge layout (minimal_founder) ────────────────────────────────────────

    def _plan_edge(self, copy_data: dict, vb: VisualBrief) -> LayoutMap:
        headline = copy_data.get("overlay_text") or copy_data.get("title", "")
        hl_size = _fit_size(headline, SAFE_W, min(vb.headline_size_hint, 68), HEADLINE_MIN, bold=True)

        return LayoutMap(
            headline_size=hl_size,
            sub_size=vb.sub_size_hint,
            cta_size=vb.cta_size_hint,
            stat_size=100,
            headline_y=H - 300,
            sub_y=H - 200,
            stat_y=H // 2,
            cta_bar_y=CTA_BAR_TOP,
            padding_x=PAD_X,
            headline_max_w=SAFE_W,
            sub_max_w=SAFE_W,
            show_stat=False,
            show_sub=True,
            show_cta_bar=vb.show_cta_bar,
        )

    # ── Safe fallback ─────────────────────────────────────────────────────────

    def _safe_defaults(self, vb: VisualBrief) -> LayoutMap:
        return LayoutMap(
            headline_size=vb.headline_size_hint,
            sub_size=vb.sub_size_hint,
            cta_size=vb.cta_size_hint,
            stat_size=120,
            headline_y=420,
            sub_y=540,
            stat_y=280,
            cta_bar_y=CTA_BAR_TOP,
            padding_x=PAD_X,
            headline_max_w=SAFE_W,
            sub_max_w=SAFE_W,
            show_stat=vb.show_stat,
            show_sub=vb.show_sub_headline,
            show_cta_bar=vb.show_cta_bar,
        )


layout_engine = LayoutEngine()
