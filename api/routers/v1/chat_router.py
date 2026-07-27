# api/routers/v1/chat_router.py

import logging

from fastapi import APIRouter, HTTPException

from api.models.schemas import ChatRequest, ChatResponse
from api.services.gemini_service import generate_answer, is_context_sufficient
from api.services.predetermined_answers_service import find_predetermined_answer
from api.services.scraper_service import scrape_specific_urls, scrape_url_with_context
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

        # 3. Scraping opcional: solo si viene una url y el tenant lo permite.
        extra_context = ""
        used_scraping = False
        if payload.url and tenant.allow_url_scraping:
            if isinstance(payload.url, list):
                scraped = await scrape_specific_urls(payload.url)
            else:
                scraped = await scrape_url_with_context(str(payload.url), payload.question)

            if await is_context_sufficient(payload.question, scraped):
                extra_context = scraped
                used_scraping = True

        # 4. Generación final: Gemini hace retrieval sobre el File Search Store del
        #    tenant (knowledge/) y, si aplica, suma el contexto de scraping.
        answer = await generate_answer(
            question=payload.question,
            identity=tenant.identity,
            protocol=tenant.protocol,
            file_search_store_name=tenant.file_search_store_name,
            extra_context=extra_context,
        )

        source = "knowledge_base+scraping" if used_scraping else "knowledge_base"
        return ChatResponse(answer=answer, source=source)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "chat_endpoint_error",
            exc_info=True,
            extra={"tenant_id": payload.tenant_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Error interno procesando la solicitud.")
