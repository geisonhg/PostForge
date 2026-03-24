"""
PostForge — Design Renderer Interface
Abstract base class for all image renderers.
Concrete implementations: PillowRenderer (active), CanvaRenderer (stub).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VisualBrief:
    """
    Output of VisualStrategist — drives template + layout decisions.
    All fields have sensible defaults so callers can construct partial briefs.
    """
    # Template selection
    template_family: str = "bold_authority"     # one of 8 template families
    color_mood: str = "dark"                    # dark | light | gradient
    layout_style: str = "centered"              # centered | split | edge | minimal

    # Content weights (which elements to emphasize)
    headline_prominence: str = "high"           # high | medium | low
    show_stat: bool = False                     # surface the stat as a big number
    show_cta_bar: bool = True                   # include CTA strip at bottom
    show_sub_headline: bool = True              # include supporting line under headline

    # Visual mood
    use_gradient_overlay: bool = True
    gradient_direction: str = "radial"         # radial | linear_tb | linear_lr | diagonal
    accent_style: str = "bar"                  # bar | dot_grid | geo | none
    glow_enabled: bool = True

    # Typography sizing hints (layout engine may override)
    headline_size_hint: int = 72               # px
    sub_size_hint: int = 36
    cta_size_hint: int = 28

    # Extra metadata from strategist
    visual_rationale: str = ""
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "VisualBrief":
        obj = cls()
        for key in cls.__dataclass_fields__:
            if key != "raw" and key in d:
                setattr(obj, key, d[key])
        obj.raw = d
        return obj

    def to_dict(self) -> dict:
        return self.raw or {
            k: getattr(self, k)
            for k in self.__dataclass_fields__
            if k != "raw"
        }


@dataclass
class LayoutMap:
    """
    Output of LayoutEngine — exact pixel positions and font sizes for every
    element. Passed directly to the renderer so it never has to guess.
    """
    canvas_w: int = 1080
    canvas_h: int = 1080

    # Resolved font sizes (px)
    headline_size: int = 72
    sub_size: int = 36
    cta_size: int = 28
    stat_size: int = 120
    hashtag_size: int = 20

    # Vertical positions (y center of each block)
    headline_y: int = 400
    sub_y: int = 520
    stat_y: int = 300
    cta_bar_y: int = 950       # top of CTA bar
    watermark_y: int = 30

    # Horizontal padding
    padding_x: int = 80

    # Text max widths
    headline_max_w: int = 920
    sub_max_w: int = 880

    # Flags resolved by layout engine
    show_stat: bool = False
    show_sub: bool = True
    show_cta_bar: bool = True


class DesignRendererInterface(ABC):
    """
    All image renderers must implement this interface.
    Input: copy_data dict + VisualBrief + LayoutMap + brand_config dict
    Output: raw PNG bytes
    """

    @abstractmethod
    def render(
        self,
        copy_data: dict[str, Any],
        visual_brief: VisualBrief,
        layout: LayoutMap,
        brand_config: dict[str, Any],
        input_image_path: str | None = None,
    ) -> bytes:
        """Render a 1080×1080 PNG and return raw bytes."""
        ...


class CanvaRenderer(DesignRendererInterface):
    """
    Stub for future Canva API / external-service renderer.
    Raises NotImplementedError until implemented.
    """

    def render(self, copy_data, visual_brief, layout, brand_config, input_image_path=None) -> bytes:
        raise NotImplementedError(
            "CanvaRenderer is not yet implemented. Use PillowRenderer."
        )
