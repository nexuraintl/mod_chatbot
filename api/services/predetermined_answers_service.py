import re
import unicodedata
from typing import Optional

from api.services.tenant_service import TenantContext

# Port de buscar_respuesta_predeterminada.py (agente OpenClaw), parametrizado por
# el predetermined_answers.json de cada tenant en vez de un diccionario hardcodeado.
#
# Formato esperado de predetermined_answers.json:
# {
#   "keywords": [
#     {"keyword": "impuesto predial", "answer_key": "impuestos_predial"},
#     {"keyword": "predial", "answer_key": "impuestos_predial"}
#   ],
#   "answers": {
#     "impuestos_predial": "Para consultar o pagar su Impuesto Predial..."
#   }
# }


def _normalize(text: str) -> str:
    # Quita tildes/diacríticos antes de matchear: keywords como "tránsito" o
    # "matrícula" no deben depender de que el ciudadano escriba la tilde
    # correctamente (muy común que no lo haga en un chat). El texto de las
    # respuestas (answers) no pasa por acá, solo se usa para comparar.
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def find_predetermined_answer(tenant: TenantContext, question: str) -> Optional[str]:
    """Busca una respuesta predeterminada exacta antes de llamar a Gemini (fast path, costo cero de LLM)."""
    keywords = tenant.predetermined_answers.get("keywords", [])
    answers = tenant.predetermined_answers.get("answers", {})

    if not keywords or not answers:
        return None

    question_normalized = _normalize(question.lower())

    # Keywords más largas/específicas primero: "impuesto predial" debe ganarle a "impuesto"
    # para evitar falsos positivos por coincidencias genéricas de substring.
    sorted_keywords = sorted(keywords, key=lambda entry: len(entry.get("keyword", "")), reverse=True)

    for entry in sorted_keywords:
        keyword = _normalize(entry.get("keyword", "").lower())
        # \b en vez de un simple "in": una keyword corta como "ica" no debe matchear
        # dentro de "certificado" ni "rit" dentro de "distrito" (bug real encontrado
        # comparando respuestas reales del tenant floridablanca contra el guion oficial).
        if keyword and re.search(rf"\b{re.escape(keyword)}\b", question_normalized):
            answer = answers.get(entry.get("answer_key"))
            if answer:
                return answer

    return None
