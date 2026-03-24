"""
Typography layer — renders text blocks onto the canvas.
Handles multiline wrapping, alignment, and color.
"""
from PIL import Image, ImageDraw

from app.services.renderers.font_loader import font


def _hex(color: str) -> tuple[int, int, int]:
    h = color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _wrap_lines(text: str, size: int, max_w: int, bold: bool = True) -> list[str]:
    """Split text into lines that fit within max_w pixels."""
    f = font(size, bold)
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    words = text.split()
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
    return lines or [""]


def _line_height(size: int, bold: bool = True, spacing: float = 1.35) -> int:
    f = font(size, bold)
    img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), "Ag", font=f)
    return int((bbox[3] - bbox[1]) * spacing)


def draw_text_centered(
    img: Image.Image,
    text: str,
    y_center: int,
    size: int,
    color: str = "#FFFFFF",
    max_w: int = 920,
    bold: bool = True,
    line_spacing: float = 1.35,
    shadow: bool = False,
    shadow_color: str = "#000000",
    shadow_offset: int = 3,
) -> None:
    """Draw centered, wrapped text. y_center is the vertical midpoint of the block."""
    if not text:
        return
    draw = ImageDraw.Draw(img)
    f = font(size, bold)
    lines = _wrap_lines(text, size, max_w, bold)
    lh = _line_height(size, bold, line_spacing)
    total_h = lh * len(lines)
    y = y_center - total_h // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=f)
        line_w = bbox[2] - bbox[0]
        x = (img.width - line_w) // 2
        if shadow:
            draw.text((x + shadow_offset, y + shadow_offset), line, font=f, fill=_hex(shadow_color))
        draw.text((x, y), line, font=f, fill=_hex(color))
        y += lh


def draw_text_left(
    img: Image.Image,
    text: str,
    x: int,
    y_center: int,
    size: int,
    color: str = "#FFFFFF",
    max_w: int = 920,
    bold: bool = True,
    line_spacing: float = 1.35,
) -> None:
    """Draw left-aligned, wrapped text."""
    if not text:
        return
    draw = ImageDraw.Draw(img)
    f = font(size, bold)
    lines = _wrap_lines(text, size, max_w, bold)
    lh = _line_height(size, bold, line_spacing)
    total_h = lh * len(lines)
    y = y_center - total_h // 2

    for line in lines:
        draw.text((x, y), line, font=f, fill=_hex(color))
        y += lh


def draw_stat_centered(
    img: Image.Image,
    stat: str,
    y_center: int,
    size: int = 120,
    color: str = "#00FF88",
    label: str = "",
    label_size: int = 24,
    label_color: str = "#AAAAAA",
) -> None:
    """Draw a large centered stat number with an optional label below."""
    draw_text_centered(img, stat, y_center, size, color, bold=True, shadow=True)
    if label:
        draw_text_centered(img, label, y_center + size // 2 + label_size, label_size, label_color, bold=False)


def draw_badge(
    img: Image.Image,
    text: str,
    x: int,
    y: int,
    size: int = 22,
    bg_color: str = "#0057FF",
    text_color: str = "#FFFFFF",
    padding_x: int = 16,
    padding_y: int = 8,
    radius: int = 6,
) -> None:
    """Draw a pill/badge with text (for labels, tags, etc.)."""
    draw = ImageDraw.Draw(img)
    f = font(size, bold=False)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    rx0 = x
    ry0 = y
    rx1 = x + tw + padding_x * 2
    ry1 = y + th + padding_y * 2
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=radius, fill=_hex(bg_color))
    draw.text((rx0 + padding_x, ry0 + padding_y), text, font=f, fill=_hex(text_color))
