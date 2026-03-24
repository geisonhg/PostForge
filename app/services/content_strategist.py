"""
PostForge — Content Strategist
Primer paso del pipeline de IA. Analiza el input y produce un strategic brief
que el CopyGenerator usa para escribir copy con framework correcto y ángulo preciso.
"""
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import get_settings
from app.integrations.ai_client import ai_client
from app.services.input_processor import InputContext

settings = get_settings()


STRATEGIST_SYSTEM = """Eres un Content Strategist senior con 10 años de experiencia en social media para marcas tech en Latinoamérica.

Tu trabajo NO es escribir el copy. Tu trabajo es crear el brief estratégico perfecto para que un copywriter lo ejecute.

Analizas el input, el contexto de la marca y decides:
- Qué ángulo emocional va a conectar mejor con la audiencia
- Qué framework de copy es el más efectivo para este contenido
- Cuál es el mensaje central que no puede faltar
- Qué objeción principal hay que romper
- Cómo abrir el post para que nadie pase de largo

Siempre respondes con JSON válido y nada más."""


def _build_strategy_prompt(ctx: InputContext, brand_config: dict) -> str:
    business = brand_config.get("business", {})
    strategy = brand_config.get("content_strategy", {})
    voice = brand_config.get("voice", {})
    brand_name = brand_config.get("name", "Brand")

    icp = business.get("icp", {})
    pillars = strategy.get("pillars", [])
    frameworks = strategy.get("copy_frameworks", {})
    pain_points = business.get("pain_points", [])
    value_props = business.get("value_propositions", [])
    services = business.get("services", [])
    differentiators = business.get("differentiators", [])

    services_summary = "\n".join(
        f"  - {s['name']}: {s['description']}" for s in services
    )

    pillars_summary = "\n".join(
        f"  - {p['name']} ({p['ratio']}): {p['description']}" for p in pillars
    )

    framework_names = "\n".join(
        f"  - {k}: {v['name']} → {v['structure']}"
        for k, v in frameworks.items()
    )

    pain_points_list = "\n".join(f"  - {p}" for p in pain_points)
    value_props_list = "\n".join(f"  - {v}" for v in value_props)

    input_context = ""
    if ctx.text:
        input_context += f"INPUT BRIEF: \"{ctx.text}\"\n"
    if ctx.campaign_type:
        input_context += f"TIPO DE CAMPAÑA SOLICITADA: {ctx.campaign_type}\n"
    if ctx.detected_topics:
        input_context += f"TEMAS IDENTIFICADOS: {', '.join(ctx.detected_topics[:5])}\n"
    if ctx.content_category:
        input_context += f"CATEGORÍA: {ctx.content_category}\n"

    prompt = f"""Crea el brief estratégico para este post de Instagram de {brand_name}.

CONTEXTO DEL NEGOCIO:
{brand_name} es una agencia digital para PYMES en LATAM.
Servicios:
{services_summary}

Cliente ideal (ICP):
- {icp.get('primary', '')}
- Edad: {icp.get('age_range', '')}
- Mindset: {icp.get('mindset', '')}

Dolores del cliente que resolvemos:
{pain_points_list}

Propuestas de valor:
{value_props_list}

Tono de voz: {voice.get('tone', '')}
Personalidad: {voice.get('personality', '')}
NUNCA usar: {', '.join(voice.get('avoid', [])[:4])}

Pilares de contenido:
{pillars_summary}

Frameworks disponibles:
{framework_names}

---
{input_context}
---

Analiza este input y produce el brief estratégico perfecto. Decide:

1. ¿Qué pilar de contenido sirve mejor para este input?
2. ¿Qué framework de copy es el más efectivo?
3. ¿Cuál es el ángulo emocional que más va a conectar con el ICP?
4. ¿Cuál es EL mensaje central (1 idea, no 5)?
5. ¿Qué objeción típica del ICP hay que romper en este post?
6. ¿Qué hook style va a parar el scroll? (elige UNO: pregunta incómoda / dato sorprendente / afirmación controversial / antes-después / micro-historia / contra-intuición)
7. ¿Qué servicio de Confluex es el protagonista o más relevante para este post?
8. ¿Hay algún número, stat o resultado específico que se debería usar?

Responde SOLO con este JSON:

{{
  "content_pillar": "id del pilar elegido",
  "framework": "id del framework elegido",
  "central_message": "La idea central del post en 1 oración clara y directa",
  "emotional_angle": "Qué emoción o insight va a conectar: ej 'frustración con procesos manuales', 'miedo a quedarse atrás', 'alivio de delegar lo técnico'",
  "hook_style": "El tipo de hook elegido y una dirección específica: ej 'pregunta incómoda sobre cuánto tiempo pierden en X'",
  "main_objection": "La objeción que hay que romper: ej 'creen que automatizar es caro y complicado'",
  "objection_response": "Cómo responder esa objeción en 1 línea",
  "protagonist_service": "id del servicio más relevante para este post",
  "use_numbers": true,
  "suggested_stat": "Un número/resultado concreto si aplica, o null",
  "audience_segment": "primary | secondary | tertiary",
  "content_type": "educational | promotional | social_proof | branding | conversion",
  "urgency_level": "low | medium | high",
  "cta_type": "soft (follow, comentá) | medium (DM, link bio) | hard (agenda, cotiza)"
}}"""

    return prompt


@dataclass
class StrategyBrief:
    content_pillar: str = "educacion"
    framework: str = "educational_tip"
    central_message: str = ""
    emotional_angle: str = ""
    hook_style: str = ""
    main_objection: str = ""
    objection_response: str = ""
    protagonist_service: str = ""
    use_numbers: bool = False
    suggested_stat: str | None = None
    audience_segment: str = "primary"
    content_type: str = "educational"
    urgency_level: str = "medium"
    cta_type: str = "medium"
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "StrategyBrief":
        obj = cls()
        for f_name in cls.__dataclass_fields__:
            if f_name != "raw" and f_name in d:
                setattr(obj, f_name, d[f_name])
        obj.raw = d
        return obj

    def to_dict(self) -> dict:
        return self.raw or {
            k: getattr(self, k) for k in self.__dataclass_fields__ if k != "raw"
        }


class ContentStrategist:

    def load_brand_config(self, brand_id: str) -> dict:
        path = settings.abs_path(settings.config_brands_dir) / f"{brand_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    def strategize(self, ctx: InputContext, brand_id: str = "confluex") -> StrategyBrief:
        brand_config = self.load_brand_config(brand_id)
        prompt = _build_strategy_prompt(ctx, brand_config)

        logger.info(f"Strategizing for brand={brand_id} input='{(ctx.text or ctx.campaign_type or '')[:60]}'")

        try:
            raw = ai_client.complete_json(
                prompt=prompt,
                system=STRATEGIST_SYSTEM,
                max_tokens=1024,
            )
            brief = StrategyBrief.from_dict(raw)
            logger.info(
                f"Strategy → pillar={brief.content_pillar} "
                f"framework={brief.framework} "
                f"angle='{brief.emotional_angle[:50]}'"
            )
            return brief
        except Exception as e:
            logger.warning(f"Strategy step failed: {e}. Using heuristic fallback.")
            return self._heuristic_brief(ctx, brand_config)

    def _heuristic_brief(self, ctx: InputContext, brand_config: dict) -> StrategyBrief:
        """Rule-based fallback when AI is unavailable."""
        category = ctx.content_category or "general"
        strategy = brand_config.get("content_strategy", {})
        frameworks = strategy.get("copy_frameworks", {})

        framework_map = {
            "educational_tip": "educational_tip",
            "problem_solution": "problem_solution",
            "service_promo": "service_promo",
            "branding": "branding",
            "project_highlight": "project_highlight",
            "announcement": "announcement",
            "automation": "automation",
        }
        framework = framework_map.get(category, "problem_solution")

        return StrategyBrief(
            content_pillar="problema_solucion",
            framework=framework,
            central_message=f"Confluex resuelve {ctx.text or 'el problema de tu negocio'} con tecnología real",
            emotional_angle="frustración con procesos que no escalan",
            hook_style="pregunta incómoda sobre pérdida de tiempo",
            main_objection="Es caro y tardado",
            objection_response="Implementamos en semanas y se paga solo desde el primer mes",
            protagonist_service="automatizacion",
            use_numbers=True,
            suggested_stat="hasta 80% menos tiempo en tareas manuales",
            audience_segment="primary",
            content_type="educational",
            urgency_level="medium",
            cta_type="medium",
        )


content_strategist = ContentStrategist()
