"""
PostForge — Input Processor
Analyzes and classifies incoming inputs (image, text, topic, campaign).
Extracts context for the copy and image generators.
"""
import mimetypes
from pathlib import Path
from typing import Any

from loguru import logger

from app.models.job import InputType

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
MAX_TEXT_LENGTH = 4000


class InputContext:
    """Structured result of input analysis, passed to downstream services."""

    def __init__(
        self,
        input_type: InputType,
        text: str = "",
        image_path: str | None = None,
        campaign_type: str | None = None,
        detected_topics: list[str] | None = None,
        content_category: str = "general",
        language: str = "es",
        raw_metadata: dict | None = None,
    ):
        self.input_type = input_type
        self.text = text
        self.image_path = image_path
        self.campaign_type = campaign_type
        self.detected_topics = detected_topics or []
        self.content_category = content_category
        self.language = language
        self.raw_metadata = raw_metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_type": self.input_type.value,
            "text": self.text,
            "image_path": self.image_path,
            "campaign_type": self.campaign_type,
            "detected_topics": self.detected_topics,
            "content_category": self.content_category,
            "language": self.language,
        }


class InputProcessor:

    # Simple keyword-to-category classifier
    CATEGORY_KEYWORDS: dict[str, list[str]] = {
        "service_promo": [
            "servicio", "oferta", "precio", "contrata", "solución",
            "service", "offer", "hire", "solution"
        ],
        "educational_tip": [
            "tip", "consejo", "aprende", "cómo", "tutorial",
            "how to", "learn", "guide", "trick"
        ],
        "branding": [
            "marca", "identidad", "brand", "logo", "diseño", "design", "estilo"
        ],
        "problem_solution": [
            "problema", "solución", "pain", "fix", "reto", "challenge", "resuelve"
        ],
        "project_highlight": [
            "proyecto", "case study", "resultado", "cliente", "portfolio"
        ],
        "announcement": [
            "lanzamiento", "nuevo", "launch", "announcing", "estreno", "novedad"
        ],
        "automation": [
            "automatización", "automation", "flujo", "workflow", "bot", "proceso"
        ],
    }

    def analyze(
        self,
        input_text: str | None = None,
        image_path: str | None = None,
        campaign_type: str | None = None,
    ) -> InputContext:
        """
        Primary entry point. Determine input type and extract context.
        """
        if image_path and Path(image_path).exists():
            input_type = self._classify_image_input(image_path)
        elif input_text:
            input_type = InputType.TEXT if len(input_text.split()) > 3 else InputType.TOPIC
        elif campaign_type:
            input_type = InputType.CAMPAIGN
        else:
            raise ValueError("At least one of: input_text, image_path, or campaign_type is required.")

        text = (input_text or campaign_type or "").strip()[:MAX_TEXT_LENGTH]
        detected_topics = self._extract_topics(text)
        content_category = self._classify_category(text, campaign_type)
        language = self._detect_language(text)

        ctx = InputContext(
            input_type=input_type,
            text=text,
            image_path=image_path,
            campaign_type=campaign_type,
            detected_topics=detected_topics,
            content_category=content_category,
            language=language,
        )

        logger.info(
            f"Input analyzed: type={input_type.value} "
            f"category={content_category} lang={language} "
            f"topics={detected_topics[:3]}"
        )
        return ctx

    def analyze_file(self, file_path: str, campaign_type: str | None = None) -> InputContext:
        """Analyze a file dropped into the inbox."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()

        if suffix in IMAGE_EXTENSIONS:
            return self.analyze(image_path=file_path, campaign_type=campaign_type)

        if suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            return self.analyze(input_text=text, campaign_type=campaign_type)

        raise ValueError(f"Unsupported file type: {suffix}")

    def _classify_image_input(self, image_path: str) -> InputType:
        """Determine if input is a single image or multi-image."""
        return InputType.IMAGE

    def _extract_topics(self, text: str) -> list[str]:
        """Simple keyword extraction from input text."""
        if not text:
            return []
        words = text.lower().split()
        stop_words = {"el", "la", "de", "en", "y", "a", "que", "es", "the", "a", "an", "is"}
        topics = [w.strip(".,;:!?()") for w in words if len(w) > 4 and w not in stop_words]
        return list(dict.fromkeys(topics))[:8]

    def _classify_category(self, text: str, campaign_type: str | None = None) -> str:
        """Map input to a content category using keywords."""
        if campaign_type:
            campaign_lower = campaign_type.lower()
            for category in self.CATEGORY_KEYWORDS:
                if category in campaign_lower:
                    return category

        if not text:
            return "general"

        text_lower = text.lower()
        scores: dict[str, int] = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score

        if scores:
            return max(scores, key=lambda k: scores[k])
        return "general"

    def _detect_language(self, text: str) -> str:
        """Simple Spanish/English detection by common words."""
        if not text:
            return "es"
        spanish_markers = {"que", "con", "para", "por", "una", "los", "las", "del"}
        words = set(text.lower().split())
        if words & spanish_markers:
            return "es"
        return "en"


input_processor = InputProcessor()
