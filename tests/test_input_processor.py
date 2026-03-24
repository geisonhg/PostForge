"""
Tests — Input Processor
"""
import pytest
from app.services.input_processor import InputProcessor, InputContext
from app.models.job import InputType


@pytest.fixture
def processor():
    return InputProcessor()


def test_classify_text_input(processor):
    ctx = processor.analyze(input_text="Automatizamos tu marketing con inteligencia artificial")
    assert ctx.input_type == InputType.TEXT
    assert ctx.language == "es"
    assert len(ctx.detected_topics) > 0


def test_classify_topic_input(processor):
    ctx = processor.analyze(input_text="IA marketing")
    assert ctx.input_type == InputType.TOPIC


def test_classify_campaign_type(processor):
    ctx = processor.analyze(campaign_type="service_promo")
    assert ctx.input_type == InputType.CAMPAIGN
    assert ctx.content_category == "service_promo"


def test_detect_spanish(processor):
    ctx = processor.analyze(input_text="Creamos soluciones digitales para tu empresa")
    assert ctx.language == "es"


def test_detect_english(processor):
    ctx = processor.analyze(input_text="We build modern digital solutions for your business")
    assert ctx.language == "en"


def test_category_educational(processor):
    ctx = processor.analyze(input_text="5 tips para mejorar tu presencia digital")
    assert ctx.content_category == "educational_tip"


def test_category_automation(processor):
    ctx = processor.analyze(input_text="Automatizamos tus procesos con bots y flujos")
    assert ctx.content_category == "automation"


def test_no_input_raises(processor):
    with pytest.raises(ValueError):
        processor.analyze()


def test_to_dict(processor):
    ctx = processor.analyze(input_text="test input para instagram")
    d = ctx.to_dict()
    assert "input_type" in d
    assert "content_category" in d
    assert "language" in d
