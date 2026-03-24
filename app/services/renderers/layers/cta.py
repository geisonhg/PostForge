"""
CTA layer — renders the bottom call-to-action bar.
"""
from PIL import Image, ImageDraw

from app.services.renderers.font_loader import font


def _hex(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_cta_bar(
    img: Image.Image,
    cta_text: str,
    y_top: int,
    bg_color: str = "#0057FF",
    text_color: str = "#FFFFFF",
    size: int = 28,
    height: int = 80,
    alpha: int = 230,
) -> None:
    """Draw a full-width CTA bar at the bottom of the canvas."""
    w = img.width
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r, g, b = _hex(bg_color)
    draw.rectangle([0, y_top, w, y_top + height], fill=(r, g, b, alpha))
    base = img.convert("RGBA")
    img.paste(Image.alpha_composite(base, overlay).convert("RGB"), (0, 0))

    # Text centered in bar
    draw2 = ImageDraw.Draw(img)
    f = font(size, bold=True)
    bbox = draw2.textbbox((0, 0), cta_text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = y_top + (height - th) // 2
    draw2.text((x, y), cta_text, font=f, fill=_hex(text_color))


def draw_cta_pill(
    img: Image.Image,
    cta_text: str,
    cx: int,
    cy: int,
    bg_color: str = "#00FF88",
    text_color: str = "#080C18",
    size: int = 26,
    padding_x: int = 32,
    padding_y: int = 14,
    radius: int = 40,
) -> None:
    """Draw a pill-shaped CTA button centered at (cx, cy)."""
    draw = ImageDraw.Draw(img)
    f = font(size, bold=True)
    bbox = draw.textbbox((0, 0), cta_text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bw = tw + padding_x * 2
    bh = th + padding_y * 2
    x0 = cx - bw // 2
    y0 = cy - bh // 2
    draw.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=radius, fill=_hex(bg_color))
    draw.text((x0 + padding_x, y0 + padding_y), cta_text, font=f, fill=_hex(text_color))
