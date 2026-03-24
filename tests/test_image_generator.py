"""
Tests — Image Generator
Verifies Pillow rendering produces valid PNG output without requiring AI keys.
"""
import pytest
from app.services.image_generator import ImageGenerator


SAMPLE_COPY = {
    "title": "Automatiza tu marketing hoy",
    "hook": "¿Sigues haciendo todo a mano? Hay una forma mejor.",
    "caption_long": "Ejemplo de caption largo para el test.",
    "caption_short": "Automatiza. Crece. Destaca.",
    "cta": "Hablemos de tu proyecto →",
    "hashtags": "#Confluex #Automatización #TechLatam",
    "overlay_text": "Automatiza. Crece.",
}


@pytest.fixture
def generator():
    return ImageGenerator()


def test_generate_gradient_text(generator):
    png_bytes = generator.generate(SAMPLE_COPY, brand_id="confluex", template="gradient_text")
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 10_000  # Should produce a real image
    assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n'  # PNG magic bytes


def test_generate_dark_tech(generator):
    png_bytes = generator.generate(SAMPLE_COPY, brand_id="confluex", template="dark_tech")
    assert isinstance(png_bytes, bytes)
    assert png_bytes[:4] == b'\x89PNG'


def test_generate_split_layout(generator):
    png_bytes = generator.generate(SAMPLE_COPY, brand_id="confluex", template="split_layout")
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 5_000


def test_generate_auto_template(generator):
    """Auto template selection should work without errors."""
    png_bytes = generator.generate(SAMPLE_COPY, brand_id="confluex", template="auto")
    assert isinstance(png_bytes, bytes)
    assert len(png_bytes) > 5_000


def test_fallback_brand(generator):
    """Should not crash with unknown brand — uses defaults."""
    png_bytes = generator.generate(SAMPLE_COPY, brand_id="unknown_brand", template="dark_tech")
    assert isinstance(png_bytes, bytes)
