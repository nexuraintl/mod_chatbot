# api/routers/v1/chat_router.py

import logging

from fastapi import APIRouter, HTTPException

from api.models.schemas import ChatRequest, ChatResponse
from api.services.gemini_service import generate_answer
from api.services.predetermined_answers_service import find_predetermined_answer
from api.services.tenant_service import TenantNotFoundError, get_tenant

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    # 1. Resolver tenant (Firestore + cache TTL). Un tenant_id inválido o inactivo
    #    corta acá mismo: nunca se cae a otro tenant ni a un contexto genérico.
    try:
        tenant = await get_tenant(payload.tenant_id)
    except TenantNotFoundError:
        raise HTTPException(status_code=404, detail=f"Tenant '{payload.tenant_id}' no encontrado o inactivo.")

    try:
        # 2. Fast path: respuesta predeterminada (sin tocar Gemini).
        predetermined = find_predetermined_answer(tenant, payload.question)
        if predetermined:
            return ChatResponse(answer=predetermined, source="predetermined")

        # 3. Generación final: Gemini hace retrieval sobre el File Search Store del tenant (knowledge/).
        answer = await generate_answer(
            question=payload.question,
            identity=tenant.identity,
            protocol=tenant.protocol,
            file_search_store_name=tenant.file_search_store_name,
        )

        return ChatResponse(answer=answer, source="knowledge_base")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "chat_endpoint_error",
            exc_info=True,
            extra={"tenant_id": payload.tenant_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Error interno procesando la solicitud.")
