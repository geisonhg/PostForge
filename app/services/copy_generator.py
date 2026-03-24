"""
PostForge — Copy Generator
Segundo paso del pipeline. Recibe el strategic brief y escribe copy
usando el framework correcto, el ángulo preciso y el contexto completo del negocio.
"""
import json
import random
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import get_settings
from app.integrations.ai_client import ai_client
from app.services.input_processor import InputContext
from app.services.content_strategist import StrategyBrief

settings = get_settings()


COPYWRITER_SYSTEM = """Eres un Copywriter de respuesta directa especializado en marcas tech y de automatización para Instagram en Latinoamérica.

Escribes copy que hace 3 cosas:
1. Para el scroll en la primera línea
2. Genera una emoción o insight real en el lector
3. Hace que el lector quiera contactar a la marca

Tu copy es específico, directo y nunca genérico.
Usas el framework indicado en el brief y no lo abandonas.
Respondes ÚNICAMENTE con JSON válido."""


def _build_copy_prompt(ctx: InputContext, brief: StrategyBrief, brand_config: dict) -> str:
    business = brand_config.get("business", {})
    strategy = brand_config.get("content_strategy", {})
    voice = brand_config.get("voice", {})
    brand_name = brand_config.get("name", "Brand")
    website = brand_config.get("brand_assets", {}).get("website", "")
    handle = brand_config.get("brand_assets", {}).get("instagram_handle", "")

    # Obtener el framework específico del brief
    frameworks = strategy.get("copy_frameworks", {})
    framework_detail = frameworks.get(brief.framework, {})
    framework_structure = framework_detail.get("structure", "Hook → Desarrollo → CTA")
    framework_name = framework_detail.get("name", brief.framework)

    # Obtener información del servicio protagonista
    services = business.get("services", [])
    protagonist = next(
        (s for s in services if s.get("id") == brief.protagonist_service),
        services[0] if services else {}
    )

    # Hashtag strategy del brief
    hashtag_strategy = strategy.get("hashtag_strategy", {})
    always_include = hashtag_strategy.get("always_include", [])
    brand_pool = hashtag_strategy.get("brand_pool", [])[:4]
    service_tags = hashtag_strategy.get("by_service", {}).get(brief.protagonist_service, [])
    audience_tags = hashtag_strategy.get("audience", [])[:4]
    geo_tags = hashtag_strategy.get("geo", [])[:3]

    # Ejemplos de tono (good vs bad)
    tone_good = voice.get("examples", {}).get("good", [])
    tone_bad_avoid = voice.get("avoid", [])

    # Power words de la marca
    power_words = voice.get("power_words", [])

    tone_examples = "\n".join(f'  ✓ "{e}"' for e in tone_good[:3]) if tone_good else ""
    tone_avoid = "\n".join(f"  ✗ {a}" for a in tone_bad_avoid[:3])

    input_brief = ""
    if ctx.text:
        input_brief += f'Brief original: "{ctx.text}"\n'
    if ctx.campaign_type:
        input_brief += f"Campaña: {ctx.campaign_type}\n"

    stat_line = ""
    if brief.use_numbers and brief.suggested_stat:
        stat_line = f"\nUSA ESTE DATO: {brief.suggested_stat}"

    prompt = f"""Escribe el copy completo para este Instagram post de {brand_name}.

━━ BRIEF ESTRATÉGICO ━━
Mensaje central: {brief.central_message}
Ángulo emocional: {brief.emotional_angle}
Hook style: {brief.hook_style}
Objeción a romper: {brief.main_objection}
Respuesta a la objeción: {brief.objection_response}
Tipo de contenido: {brief.content_type}
Urgencia: {brief.urgency_level}
CTA type: {brief.cta_type} (soft=sigueme/comentá | medium=DM/link bio | hard=agenda/cotiza)
Segmento de audiencia: {brief.audience_segment}
{stat_line}

━━ FRAMEWORK A USAR ━━
{framework_name}
Estructura: {framework_structure}

━━ INPUT ORIGINAL ━━
{input_brief}

━━ SERVICIO PROTAGONISTA ━━
{protagonist.get('name', '')}: {protagonist.get('description', '')}
Dolor que resuelve: {protagonist.get('pain_solved', '')}
Resultado que genera: {protagonist.get('result', '')}

━━ VOZ DE LA MARCA ━━
Tono: {voice.get('tone', '')}
Personalidad: {voice.get('personality', '')}
Power words disponibles: {', '.join(power_words[:8])}

Ejemplos de tono correcto:
{tone_examples}

NUNCA usar:
{tone_avoid}

━━ ESTRATEGIA DE HASHTAGS ━━
Obligatorios: {' '.join(always_include)}
Pool de marca (elige 3-4): {' '.join(brand_pool)}
Del servicio (elige 4-6): {' '.join(service_tags)}
De audiencia (elige 2-3): {' '.join(audience_tags)}
Geográficos (elige 1-2): {' '.join(geo_tags)}
Agrega 8-10 hashtags adicionales específicos al tema exacto del post.
Total objetivo: 25-30 hashtags. Mezcla nichos pequeños (10K-100K) con medianos.

Idioma: {brand_config.get('voice', {}).get('language', 'es')}
Handle: {handle} | Web: {website}

━━ ENTREGA ━━
Responde SOLO con este JSON:

{{
  "title": "Título del post (máx 7 palabras, sin emojis, específico al tema)",
  "hook": "Primera línea EXACTA. Aplica el hook_style del brief. Máx 15 palabras. Puede usar 1 emoji al inicio o final.",
  "caption_long": "Caption completo siguiendo el framework indicado. 180-280 palabras. Párrafos de 2-3 líneas máx. Emojis como marcadores de estructura, no como decoración. \\n\\n entre párrafos. Termina con el CTA del tipo indicado.",
  "caption_short": "Versión corta. Hook + punto principal + CTA. 60-80 palabras.",
  "cta": "CTA final exacto (1 línea, concreto, acorde al urgency level)",
  "hashtags": "Los 25-30 hashtags elegidos separados por espacio",
  "overlay_text": "FRASE VISUAL para el arte (máx 5 palabras en mayúsculas o con énfasis, sin emojis, que sea impactante sola)"
}}"""

    return prompt


class CopyGenerator:

    def load_brand_config(self, brand_id: str) -> dict:
        path = settings.abs_path(settings.config_brands_dir) / f"{brand_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        logger.warning(f"Brand config not found for '{brand_id}'")
        return {}

    def generate(self, ctx: InputContext, brand_id: str = "confluex",
                 brief: StrategyBrief | None = None) -> dict[str, Any]:
        """
        Generate Instagram copy using a strategic brief.
        If no brief is provided, uses heuristic fallback.
        """
        brand_config = self.load_brand_config(brand_id)

        if brief is None:
            from app.services.content_strategist import content_strategist
            brief = content_strategist._heuristic_brief(ctx, brand_config)

        prompt = _build_copy_prompt(ctx, brief, brand_config)

        logger.info(
            f"Writing copy: brand={brand_id} framework={brief.framework} "
            f"angle='{brief.emotional_angle[:40]}'"
        )

        try:
            copy_data = ai_client.complete_json(
                prompt=prompt,
                system=COPYWRITER_SYSTEM,
                max_tokens=2800,
            )
        except Exception as e:
            logger.error(f"Copy generation failed: {e}")
            copy_data = self._fallback_copy(ctx, brief, brand_config)

        copy_data = self._validate_and_clean(copy_data, ctx, brief, brand_config)
        copy_data["_strategy"] = brief.to_dict()  # attach strategy metadata

        logger.info(f"Copy done: '{copy_data.get('title', '')}'")
        return copy_data

    def _validate_and_clean(self, data: dict, ctx: InputContext,
                             brief: StrategyBrief, brand_config: dict) -> dict:
        brand_name = brand_config.get("name", "Brand")
        topic = ctx.text or ctx.campaign_type or "tu negocio"

        defaults = {
            "title": f"{brief.central_message[:50] if brief.central_message else brand_name}",
            "hook": f"¿Cuánto tiempo perdés cada semana en {topic[:30]}?",
            "caption_long": (
                f"La mayoría de los negocios en LATAM pierden tiempo y dinero "
                f"en procesos que ya se pueden automatizar.\n\n"
                f"En {brand_name} lo implementamos en semanas, no meses.\n\n"
                f"¿Hablamos? → {brand_config.get('brand_assets', {}).get('website', '')}"
            ),
            "caption_short": f"Automatizamos lo que te frena. Primera consulta sin costo.",
            "cta": "Escribinos hoy y coordinamos una llamada →",
            "hashtags": "#Confluex #AutomatizaciónDigital #TechLatam #PymeDigital",
            "overlay_text": "Sin Excusas.",
        }
        for key, default in defaults.items():
            if not data.get(key):
                data[key] = default
        return data

    def _fallback_copy(self, ctx: InputContext, brief: StrategyBrief, brand_config: dict) -> dict:
        brand_name = brand_config.get("name", "Brand")
        website = brand_config.get("brand_assets", {}).get("website", "")
        topic = ctx.text or ctx.campaign_type or "automatización"

        hook_options = [
            f"¿Cuánto tiempo perdés cada semana haciendo esto a mano?",
            f"El mayor error de las PYMES con {topic[:25]}: hacerlo sin tecnología.",
            f"Mientras tu competencia automatiza, vos seguís con planillas de Excel.",
        ]

        return {
            "title": f"Transforma tu negocio con {topic[:25]}",
            "hook": random.choice(hook_options),
            "caption_long": (
                f"En {brand_name} no vendemos tecnología. Vendemos resultados.\n\n"
                f"Cada proyecto que implementamos tiene un objetivo claro: "
                f"que tu negocio funcione mejor de lo que funcionaba antes.\n\n"
                f"Sin procesos lentos. Sin errores manuales. Sin depender de una persona para que todo funcione.\n\n"
                f"¿Querés ver cómo lo hacemos?\n\n"
                f"Primera consulta sin costo → {website}"
            ),
            "caption_short": (
                f"Automatizamos lo que te frena para que te enfoques en crecer.\n"
                f"Primera consulta sin costo → {website}"
            ),
            "cta": "Primera consulta sin costo →",
            "hashtags": "#Confluex #AutomatizaciónDigital #TransformaciónDigital #TechLatam #AgenciaDigital #EmpresariosLatam",
            "overlay_text": "Tecnología Que Funciona.",
        }


copy_generator = CopyGenerator()
