"""
Font loader — loads and caches PIL ImageFont instances.
Extracted from image_generator.py for reuse across all renderers.
"""
from pathlib import Path
from functools import lru_cache

from PIL import ImageFont
from loguru import logger

# Font paths relative to project root (renderers/ → services/ → app/ → postforge/)
_FONTS_DIR = Path(__file__).parents[3] / "fonts"
_BOLD_PATH = _FONTS_DIR / "Bold.ttf"
_REGULAR_PATH = _FONTS_DIR / "Regular.ttf"


@lru_cache(maxsize=64)
def get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Return a cached PIL font at the given size."""
    path = _BOLD_PATH if bold else _REGULAR_PATH
    try:
        return ImageFont.truetype(str(path), size)
    except Exception as e:
        logger.warning(f"Font load failed ({path}, size={size}): {e}. Using default.")
        return ImageFont.load_default()


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Alias for get_font — shorthand for use inside renderers."""
    return get_font(size, bold)
