from typing import Optional

from src.services.tenant_service import TenantContext

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


def find_predetermined_answer(tenant: TenantContext, question: str) -> Optional[str]:
    """Busca una respuesta predeterminada exacta antes de llamar a Gemini (fast path, costo cero de LLM)."""
    keywords = tenant.predetermined_answers.get("keywords", [])
    answers = tenant.predetermined_answers.get("answers", {})

    if not keywords or not answers:
        return None

    question_lower = question.lower()

    # Keywords más largas/específicas primero: "impuesto predial" debe ganarle a "impuesto"
    # para evitar falsos positivos por coincidencias genéricas de substring.
    sorted_keywords = sorted(keywords, key=lambda entry: len(entry.get("keyword", "")), reverse=True)

    for entry in sorted_keywords:
        keyword = entry.get("keyword", "").lower()
        if keyword and keyword in question_lower:
            answer = answers.get(entry.get("answer_key"))
            if answer:
                return answer

    return None
