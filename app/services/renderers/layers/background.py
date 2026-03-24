"""
Background layer — fills the canvas with gradients, solid colors, or image overlays.
Called first by every template renderer.
"""
import math
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

from app.services.design_renderer_interface import VisualBrief


def _hex(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_gradient_bg(
    img: Image.Image,
    color_start: str,
    color_end: str,
    direction: str = "linear_tb",
) -> None:
    """Fill `img` with a gradient between two hex colors."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    c1 = _hex(color_start)
    c2 = _hex(color_end)

    if direction == "radial":
        # Radial gradient from center
        cx, cy = w // 2, h // 2
        max_dist = math.sqrt(cx**2 + cy**2)
        pixels = img.load()
        for y in range(h):
            for x in range(w):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                t = min(dist / max_dist, 1.0)
                pixels[x, y] = _lerp_color(c1, c2, t)
    elif direction == "diagonal":
        for y in range(h):
            for x in range(w):
                t = (x / w + y / h) / 2
                draw.point((x, y), fill=_lerp_color(c1, c2, t))
    elif direction == "linear_lr":
        for x in range(w):
            t = x / w
            draw.line([(x, 0), (x, h)], fill=_lerp_color(c1, c2, t))
    else:  # linear_tb (default)
        for y in range(h):
            t = y / h
            draw.line([(0, y), (w, y)], fill=_lerp_color(c1, c2, t))


def draw_solid_bg(img: Image.Image, color: str) -> None:
    img.paste(_hex(color), [0, 0, img.width, img.height])


def draw_image_bg(
    img: Image.Image,
    input_image_path: str,
    overlay_color: str = "#080C18",
    overlay_opacity: float = 0.72,
) -> None:
    """Paste a source image as background with a dark overlay."""
    try:
        src = Image.open(input_image_path).convert("RGB")
        src = src.resize((img.width, img.height), Image.LANCZOS)
        img.paste(src, (0, 0))
    except Exception:
        draw_solid_bg(img, overlay_color)
        return

    # Dark overlay
    overlay = Image.new("RGBA", img.size, (*_hex(overlay_color), int(255 * overlay_opacity)))
    base = img.convert("RGBA")
    merged = Image.alpha_composite(base, overlay)
    img.paste(merged.convert("RGB"), (0, 0))


def draw_noise_texture(img: Image.Image, intensity: int = 12) -> None:
    """Add subtle noise for texture on light backgrounds."""
    import random
    pixels = img.load()
    w, h = img.size
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            noise = random.randint(-intensity, intensity)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
            )
