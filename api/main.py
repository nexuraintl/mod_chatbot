from fastapi import FastAPI

from api.core.config import get_settings
from api.core.logging import setup_logging
from api.core.middleware import CorrelationMiddleware
from api.routers import health
from api.routers.v1 import chat_router

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(
    title="ms_ia_chatbot",
    version=settings.service_version,
)

app.add_middleware(CorrelationMiddleware)

app.include_router(health.router)
app.include_router(chat_router.router, prefix="/api/v1")
