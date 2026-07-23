import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from google.cloud import firestore, storage

from src.config import settings

logger = logging.getLogger(__name__)

_firestore_client = firestore.AsyncClient(project=settings.GCP_PROJECT)
_storage_client = storage.Client(project=settings.GCP_PROJECT)


class TenantNotFoundError(Exception):
    """Se lanza cuando el tenant_id no existe en Firestore o está inactivo."""


@dataclass
class TenantContext:
    tenant_id: str
    bucket: str
    prefix: str
    file_search_store_name: Optional[str]
    allow_url_scraping: bool
    identity: Dict[str, Any] = field(default_factory=dict)
    protocol: Dict[str, Any] = field(default_factory=dict)
    predetermined_answers: Dict[str, Any] = field(default_factory=dict)


# cache en memoria del proceso: tenant_id -> (timestamp de carga, TenantContext)
_cache: Dict[str, "tuple[float, TenantContext]"] = {}


def _read_gcs_json(bucket_name: str, path: str) -> Dict[str, Any]:
    blob = _storage_client.bucket(bucket_name).blob(path)
    if not blob.exists():
        return {}
    return json.loads(blob.download_as_text())


async def _load_tenant(tenant_id: str) -> TenantContext:
    doc_ref = _firestore_client.collection("tenants").document(tenant_id)
    snapshot = await doc_ref.get()

    if not snapshot.exists:
        raise TenantNotFoundError(f"Tenant '{tenant_id}' no existe.")

    data = snapshot.to_dict()
    if not data.get("active", False):
        raise TenantNotFoundError(f"Tenant '{tenant_id}' está inactivo.")

    bucket = data["bucket"]

    identity, protocol, predetermined_answers = await asyncio.gather(
        asyncio.to_thread(_read_gcs_json, bucket, data["identity_path"]),
        asyncio.to_thread(_read_gcs_json, bucket, data["protocol_path"]),
        asyncio.to_thread(_read_gcs_json, bucket, data["predetermined_answers_path"]),
    )

    return TenantContext(
        tenant_id=tenant_id,
        bucket=bucket,
        prefix=data.get("prefix", f"{tenant_id}/"),
        file_search_store_name=data.get("file_search_store_name"),
        allow_url_scraping=data.get("allow_url_scraping", False),
        identity=identity,
        protocol=protocol,
        predetermined_answers=predetermined_answers,
    )


async def get_tenant(tenant_id: str) -> TenantContext:
    """Resuelve la config de un tenant, cacheada en memoria con TTL (settings.TENANT_CACHE_TTL_SECONDS)."""
    cached = _cache.get(tenant_id)
    if cached and (time.monotonic() - cached[0]) < settings.TENANT_CACHE_TTL_SECONDS:
        return cached[1]

    tenant = await _load_tenant(tenant_id)
    _cache[tenant_id] = (time.monotonic(), tenant)
    logger.info(f"TENANT_RESOLVED: {tenant_id}")
    return tenant


def invalidate_tenant_cache(tenant_id: str) -> None:
    """Fuerza a que la próxima resolución de este tenant relea Firestore/GCS."""
    _cache.pop(tenant_id, None)
