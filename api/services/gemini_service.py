import json
import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# "gemini-2.0-flash" quedó deprecado (404 NOT_FOUND validado contra la API real
# el 2026-07 — Google recomienda migrar a la Interactions API a futuro).
MODEL_NAME = "gemini-2.5-flash"


@lru_cache
def _client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def get_or_create_store(tenant_id: str) -> str:
    """
    Devuelve el nombre del File Search Store del tenant, creándolo si no existe.

    Se usa SOLO durante la ingesta (scripts/sync_tenant_kb.py, servicio de Eventarc),
    nunca en el request path del chat: una vez creado, el store_name se persiste en
    Firestore (tenant.file_search_store_name) y el chat lo lee directo de ahí, sin
    volver a listar stores en cada request.
    """
    display_name = f"tenant-{tenant_id}"
    for store in _client().file_search_stores.list():
        if store.display_name == display_name:
            return store.name
    store = _client().file_search_stores.create(config={"display_name": display_name})
    return store.name


def _build_system_instruction(identity: Dict[str, Any], protocol: Dict[str, Any]) -> Optional[str]:
    """Arma el system prompt del tenant a partir de identity.json + protocol.json (persona, tono, reglas)."""
    parts = []
    if identity:
        parts.append(f"IDENTIDAD Y PERSONALIDAD:\n{json.dumps(identity, ensure_ascii=False, indent=2)}")
    if protocol:
        parts.append(f"PROTOCOLO DE ATENCIÓN (reglas obligatorias, sígalas al pie de la letra):\n{json.dumps(protocol, ensure_ascii=False, indent=2)}")
    return "\n\n".join(parts) if parts else None


async def generate_answer(
    question: str,
    identity: Dict[str, Any],
    protocol: Dict[str, Any],
    file_search_store_name: Optional[str] = None,
) -> str:
    """
    Genera la respuesta final para el ciudadano.

    Si el tenant tiene un File Search Store asociado, se adjunta como Tool y Gemini
    hace el retrieval sobre el knowledge/ del tenant automáticamente.
    """
    system_instruction = _build_system_instruction(identity, protocol)

    tools = None
    if file_search_store_name:
        tools = [types.Tool(file_search=types.FileSearch(file_search_store_names=[file_search_store_name]))]

    prompt = f"PREGUNTA DEL CIUDADANO:\n{question}"

    try:
        response = _client().models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
            ),
        )
        return response.text
    except Exception as e:
        logger.error("gemini_generate_error", exc_info=True, extra={"error": str(e)})
        return "Lo siento, ocurrió un error al procesar la respuesta. Por favor intente de nuevo."
