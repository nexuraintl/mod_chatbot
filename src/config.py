import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY no está configurada.")

    # Proyecto GCP donde viven Firestore (registro de tenants) y el bucket de contexto
    GCP_PROJECT = os.getenv("GCP_PROJECT")

    # Bucket por defecto donde viven los prefijos de cada tenant (identity.json, protocol.json, knowledge/)
    TENANT_BUCKET = os.getenv("TENANT_BUCKET")

    # TTL del cache en memoria de la config de cada tenant (Firestore -> proceso)
    TENANT_CACHE_TTL_SECONDS = int(os.getenv("TENANT_CACHE_TTL_SECONDS", "90"))

settings = Config()
