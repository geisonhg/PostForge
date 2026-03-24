"""
Watermark layer — brand logo and handle overlay.
Always drawn last, on top of everything.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.renderers.font_loader import font


def _hex(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_watermark(
    img: Image.Image,
    brand_config: dict,
    padding: int = 40,
) -> None:
    """
    Draw brand handle (bottom-left) and logo (bottom-right).
    Falls back to text-only if logo file not found.
    """
    assets = brand_config.get("brand_assets", {})
    layout = brand_config.get("layout", {})
    handle = assets.get("watermark_text") or assets.get("instagram_handle", "")
    logo_path = assets.get("logo_white_path") or assets.get("logo_path", "")
    bottom_y = img.height - padding

    # Handle text — bottom left
    if handle:
        _draw_handle(img, handle, padding, bottom_y)

    # Logo — bottom right
    if logo_path:
        _draw_logo(img, logo_path, img.width - padding, bottom_y, brand_config)


def _draw_handle(img: Image.Image, handle: str, x: int, bottom_y: int) -> None:
    draw = ImageDraw.Draw(img)
    f = font(22, bold=False)
    bbox = draw.textbbox((0, 0), handle, font=f)
    th = bbox[3] - bbox[1]
    y = bottom_y - th
    # Subtle shadow
    draw.text((x + 1, y + 1), handle, font=f, fill=(0, 0, 0, 120) if img.mode == "RGBA" else (20, 20, 20))
    draw.text((x, y), handle, font=f, fill=(180, 180, 180))


def _draw_logo(img: Image.Image, logo_path: str, right_x: int, bottom_y: int, brand_config: dict) -> None:
    from app.config import get_settings
    settings = get_settings()
    full_path = settings.abs_path("assets") / logo_path.lstrip("assets/")

    if not Path(full_path).exists():
        # Fallback: draw brand name as text
        brand_name = brand_config.get("name", "")
        if brand_name:
            draw = ImageDraw.Draw(img)
            f = font(22, bold=True)
            bbox = draw.textbbox((0, 0), brand_name, font=f)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((right_x - tw, bottom_y - th), brand_name, font=f, fill=(200, 200, 200))
        return

    try:
        logo = Image.open(full_path).convert("RGBA")
        logo_h = 36
        ratio = logo_h / logo.height
        logo_w = int(logo.width * ratio)
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        x = right_x - logo_w
        y = bottom_y - logo_h
        if img.mode == "RGBA":
            img.paste(logo, (x, y), logo)
        else:
            base = img.convert("RGBA")
            base.paste(logo, (x, y), logo)
            img.paste(base.convert("RGB"), (0, 0))
    except Exception:
        pass
