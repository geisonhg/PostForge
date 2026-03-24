"""
Decorations layer — geometric accents, glows, grids, bars, and pills.
Called after background, before typography.
"""
import math
from PIL import Image, ImageDraw, ImageFilter


def _hex(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_glow(
    img: Image.Image,
    cx: int,
    cy: int,
    radius: int = 380,
    color: str = "#0057FF",
    alpha: int = 60,
) -> None:
    """Soft radial glow blob at (cx, cy)."""
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    r, g, b = _hex(color)
    for step in range(12):
        a = int(alpha * (1 - step / 12))
        r_cur = radius - step * (radius // 14)
        draw.ellipse(
            [cx - r_cur, cy - r_cur, cx + r_cur, cy + r_cur],
            fill=(r, g, b, a),
        )
    blurred = glow.filter(ImageFilter.GaussianBlur(radius // 4))
    base = img.convert("RGBA")
    merged = Image.alpha_composite(base, blurred)
    img.paste(merged.convert("RGB"), (0, 0))


def draw_accent_bar(
    img: Image.Image,
    x: int,
    y: int,
    width: int = 60,
    height: int = 6,
    color: str = "#00FF88",
    radius: int = 3,
) -> None:
    """Horizontal colored accent bar (pill shape)."""
    draw = ImageDraw.Draw(img)
    r, g, b = _hex(color)
    draw.rounded_rectangle([x, y, x + width, y + height], radius=radius, fill=(r, g, b))


def draw_dot_grid(
    img: Image.Image,
    x_start: int,
    y_start: int,
    cols: int = 8,
    rows: int = 8,
    spacing: int = 20,
    dot_r: int = 2,
    color: str = "#0057FF",
    alpha: int = 60,
) -> None:
    """Dot grid decoration — subtle tech texture."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r, g, b = _hex(color)
    for row in range(rows):
        for col in range(cols):
            cx = x_start + col * spacing
            cy = y_start + row * spacing
            draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=(r, g, b, alpha))
    base = img.convert("RGBA")
    merged = Image.alpha_composite(base, overlay)
    img.paste(merged.convert("RGB"), (0, 0))


def draw_geo_lines(
    img: Image.Image,
    color: str = "#0057FF",
    alpha: int = 40,
) -> None:
    """Corner geometric lines — subtle angular decoration."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r, g, b = _hex(color)
    w, h = img.size

    # Top-right corner lines
    for i in range(5):
        offset = i * 22
        draw.line([(w - 120 + offset, 40), (w - 40, 120 - offset)], fill=(r, g, b, alpha), width=1)

    # Bottom-left corner lines
    for i in range(5):
        offset = i * 22
        draw.line([(40, h - 120 + offset), (120 - offset, h - 40)], fill=(r, g, b, alpha), width=1)

    base = img.convert("RGBA")
    merged = Image.alpha_composite(base, overlay)
    img.paste(merged.convert("RGB"), (0, 0))


def draw_divider_line(
    img: Image.Image,
    y: int,
    x_start: int = 80,
    x_end: int = 1000,
    color: str = "#0057FF",
    alpha: int = 60,
    width: int = 1,
) -> None:
    """Thin horizontal divider line."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r, g, b = _hex(color)
    draw.line([(x_start, y), (x_end, y)], fill=(r, g, b, alpha), width=width)
    base = img.convert("RGBA")
    merged = Image.alpha_composite(base, overlay)
    img.paste(merged.convert("RGB"), (0, 0))


def draw_split_panel(
    img: Image.Image,
    split_x: int,
    left_color: str = "#1a0a0a",
    right_color: str = "#080C18",
) -> None:
    """Draw two-panel split background (for problem_solution template)."""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw.rectangle([0, 0, split_x, h], fill=_hex(left_color))
    draw.rectangle([split_x, 0, w, h], fill=_hex(right_color))


def draw_grid_lines(
    img: Image.Image,
    color: str = "#0057FF",
    alpha: int = 18,
    spacing: int = 90,
) -> None:
    """Subtle square grid overlay for tech templates."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    r, g, b = _hex(color)
    w, h = img.size
    for x in range(0, w, spacing):
        draw.line([(x, 0), (x, h)], fill=(r, g, b, alpha), width=1)
    for y in range(0, h, spacing):
        draw.line([(0, y), (w, y)], fill=(r, g, b, alpha), width=1)
    base = img.convert("RGBA")
    merged = Image.alpha_composite(base, overlay)
    img.paste(merged.convert("RGB"), (0, 0))
