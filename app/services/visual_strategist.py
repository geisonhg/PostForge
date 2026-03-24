"""
PostForge — Visual Strategist
Third AI step in the pipeline. Receives the strategy brief + generated copy
and decides which template family, color mood, layout style, and visual
emphasis will produce the most effective Instagram post.
"""
import json
from typing import Any

from loguru import logger

from app.config import get_settings
from app.integrations.ai_client import ai_client
from app.services.content_strategist import StrategyBrief
from app.services.design_renderer_interface import VisualBrief

settings = get_settings()


VISUAL_STRATEGIST_SYSTEM = """Eres un Art Director especializado en contenido para Instagram de marcas tech en Latinoamérica.

Tu trabajo es decidir la estrategia visual de un post antes de que se genere la imagen.
No diseñas tú. Produces el brief visual que usa el sistema de generación.

Conoces los 8 template families disponibles:
- bold_authority: Fondo oscuro intenso, headline enorme centrado, contraste máximo. Para mensajes de impacto o posicionamiento.
- clean_saas: Fondo blanco/gris claro, tipografía limpia, mucho espacio. Para contenido educativo y profesional.
- premium_dark_tech: Gradiente oscuro azul/índigo, detalles neón, rejilla geométrica. Para servicios tech premium.
- educational_card: Card con secciones, icono grande, bullet points. Para tips y tutoriales.
- problem_solution: Layout split: lado izquierdo = problema (rojo/oscuro), lado derecho = solución (azul/verde). Para PAS.
- case_study_proof: Estadística grande central, contexto pequeño arriba y abajo. Para prueba social.
- minimal_founder: Fondo liso con textura sutil, texto left-aligned, cita grande. Para marca personal y branding.
- image_led_overlay: Imagen de fondo con overlay semitransparente, texto flotante. Cuando hay imagen de input.

Siempre respondes con JSON válido y nada más."""


def _build_visual_prompt(
    copy_data: dict[str, Any],
    strategy_brief: StrategyBrief,
    brand_config: dict[str, Any],
    has_input_image: bool,
) -> str:
    visual_id = brand_config.get("visual_identity", {})
    overlay_text = copy_data.get("overlay_text", "")
    hook = copy_data.get("hook", "")
    title = copy_data.get("title", "")
    cta = copy_data.get("cta", "")
    suggested_stat = strategy_brief.suggested_stat or ""
    content_type = strategy_brief.content_type
    urgency = strategy_brief.urgency_level
    framework = strategy_brief.framework
    emotional_angle = strategy_brief.emotional_angle

    image_note = "Hay una imagen de input disponible para usar como fondo." if has_input_image else "No hay imagen de input. El template debe ser completamente generado."

    return f"""Decide la estrategia visual para este Instagram post.

━━ COPY GENERADO ━━
Overlay text (frase visual): "{overlay_text}"
Hook: "{hook}"
Título: "{title}"
CTA: "{cta}"
Stat a destacar: "{suggested_stat}"

━━ BRIEF ESTRATÉGICO ━━
Framework: {framework}
Tipo de contenido: {content_type}
Ángulo emocional: {emotional_angle}
Urgencia: {urgency}

━━ IDENTIDAD VISUAL DE LA MARCA ━━
Color primario: {visual_id.get('primary_color', '#0057FF')}
Color secundario: {visual_id.get('secondary_color', '#00D4FF')}
Color acento: {visual_id.get('accent_color', '#00FF88')}
Fondo oscuro: {visual_id.get('dark_color', '#080C18')}

━━ CONTEXTO ━━
{image_note}
Use numbers/stat: {strategy_brief.use_numbers}

━━ REGLAS DE SELECCIÓN ━━
- Si hay imagen de input → priorizar image_led_overlay
- Si framework es project_highlight o content_type es social_proof → case_study_proof
- Si framework es problem_solution → problem_solution
- Si framework es educational_tip → educational_card o clean_saas
- Si framework es branding o minimal_founder → minimal_founder
- Si urgency es high y content_type es conversion → bold_authority o service_promo → premium_dark_tech
- Si framework es automation → premium_dark_tech con stat prominente

━━ ENTREGA ━━
Responde SOLO con este JSON:

{{
  "template_family": "uno de los 8 template families",
  "color_mood": "dark | light | gradient",
  "layout_style": "centered | split | edge | minimal",
  "headline_prominence": "high | medium | low",
  "show_stat": true o false,
  "show_cta_bar": true,
  "show_sub_headline": true o false,
  "use_gradient_overlay": true o false,
  "gradient_direction": "radial | linear_tb | linear_lr | diagonal",
  "accent_style": "bar | dot_grid | geo | none",
  "glow_enabled": true o false,
  "headline_size_hint": número en px (sugerencia, 60-96),
  "sub_size_hint": número en px (24-48),
  "cta_size_hint": número en px (22-32),
  "visual_rationale": "Por qué elegiste este template para este post en 1 oración"
}}"""


class VisualStrategist:

    def load_brand_config(self, brand_id: str) -> dict:
        from pathlib import Path
        path = settings.abs_path(settings.config_brands_dir) / f"{brand_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def strategize(
        self,
        copy_data: dict[str, Any],
        strategy_brief: StrategyBrief,
        brand_id: str = "confluex",
        input_image_path: str | None = None,
    ) -> VisualBrief:
        brand_config = self.load_brand_config(brand_id)
        has_input_image = bool(input_image_path)

        prompt = _build_visual_prompt(copy_data, strategy_brief, brand_config, has_input_image)

        logger.info(
            f"Visual strategizing: brand={brand_id} "
            f"framework={strategy_brief.framework} "
            f"content_type={strategy_brief.content_type} "
            f"has_image={has_input_image}"
        )

        try:
            raw = ai_client.complete_json(
                prompt=prompt,
                system=VISUAL_STRATEGIST_SYSTEM,
                max_tokens=512,
            )
            brief = VisualBrief.from_dict(raw)
            logger.info(
                f"Visual brief → template={brief.template_family} "
                f"mood={brief.color_mood} layout={brief.layout_style}"
            )
            return brief
        except Exception as e:
            logger.warning(f"Visual strategy step failed: {e}. Using heuristic fallback.")
            return self._heuristic_brief(strategy_brief, has_input_image)

    def _heuristic_brief(
        self,
        strategy_brief: StrategyBrief,
        has_input_image: bool,
    ) -> VisualBrief:
        """Deterministic fallback — no randomness."""
        if has_input_image:
            return VisualBrief(
                template_family="image_led_overlay",
                color_mood="dark",
                layout_style="centered",
                headline_prominence="high",
                show_stat=False,
                glow_enabled=True,
                accent_style="bar",
            )

        content_type = strategy_brief.content_type
        framework = strategy_brief.framework
        urgency = strategy_brief.urgency_level
        use_numbers = strategy_brief.use_numbers and bool(strategy_brief.suggested_stat)

        if framework == "problem_solution":
            return VisualBrief(
                template_family="problem_solution",
                color_mood="dark",
                layout_style="split",
                headline_prominence="high",
                show_stat=use_numbers,
                accent_style="bar",
                glow_enabled=False,
            )
        if content_type == "social_proof" or framework == "project_highlight":
            return VisualBrief(
                template_family="case_study_proof",
                color_mood="dark",
                layout_style="centered",
                headline_prominence="medium",
                show_stat=True,
                stat_size_hint=120,
                accent_style="geo",
                glow_enabled=True,
            )
        if framework in ("educational_tip",):
            return VisualBrief(
                template_family="educational_card",
                color_mood="light",
                layout_style="minimal",
                headline_prominence="medium",
                show_stat=False,
                show_cta_bar=True,
                accent_style="dot_grid",
                glow_enabled=False,
            )
        if framework == "branding":
            return VisualBrief(
                template_family="minimal_founder",
                color_mood="light",
                layout_style="edge",
                headline_prominence="low",
                show_stat=False,
                accent_style="none",
                glow_enabled=False,
            )
        if urgency == "high" and content_type in ("conversion", "promotional"):
            return VisualBrief(
                template_family="premium_dark_tech",
                color_mood="gradient",
                layout_style="centered",
                headline_prominence="high",
                show_stat=use_numbers,
                accent_style="geo",
                glow_enabled=True,
            )
        if framework == "automation":
            return VisualBrief(
                template_family="premium_dark_tech",
                color_mood="dark",
                layout_style="centered",
                headline_prominence="high",
                show_stat=use_numbers,
                accent_style="dot_grid",
                glow_enabled=True,
            )
        # Default: bold_authority
        return VisualBrief(
            template_family="bold_authority",
            color_mood="dark",
            layout_style="centered",
            headline_prominence="high",
            show_stat=False,
            accent_style="bar",
            glow_enabled=True,
        )


visual_strategist = VisualStrategist()
