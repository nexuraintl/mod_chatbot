import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, Optional

from google.cloud import firestore, storage

from api.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Los clientes de Firestore/GCS resuelven credenciales (ADC) al construirse, no de
# forma perezosa — instanciarlos a nivel de módulo rompe cualquier import que no
# tenga credenciales reales disponibles (incluidos los tests). @lru_cache los crea
# una sola vez, en el primer uso real, y los reutiliza después (mismo efecto que un
# singleton a nivel de módulo, pero sin el costo en import time).
@lru_cache
def _firestore_client() -> firestore.AsyncClient:
    return firestore.AsyncClient(project=settings.gcp_project)


@lru_cache
def _storage_client() -> storage.Client:
    return storage.Client(project=settings.gcp_project)


class TenantNotFoundError(Exception):
    """Se lanza cuando el tenant_id no existe en Firestore o está inactivo."""


@dataclass
class TenantContext:
    tenant_id: str
    bucket: str
    prefix: str
    file_search_store_name: Optional[str]
    identity: Dict[str, Any] = field(default_factory=dict)
    protocol: Dict[str, Any] = field(default_factory=dict)
    predetermined_answers: Dict[str, Any] = field(default_factory=dict)


# cache en memoria del proceso: tenant_id -> (timestamp de carga, TenantContext)
_cache: Dict[str, "tuple[float, TenantContext]"] = {}


def _read_gcs_json(bucket_name: str, path: str) -> Dict[str, Any]:
    blob = _storage_client().bucket(bucket_name).blob(path)
    if not blob.exists():
        return {}
    return json.loads(blob.download_as_text())


async def _load_tenant(tenant_id: str) -> TenantContext:
    doc_ref = _firestore_client().collection("tenants").document(tenant_id)
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
        identity=identity,
        protocol=protocol,
        predetermined_answers=predetermined_answers,
    )


async def get_tenant(tenant_id: str) -> TenantContext:
    """Resuelve la config de un tenant, cacheada en memoria con TTL (settings.tenant_cache_ttl_seconds)."""
    cached = _cache.get(tenant_id)
    if cached and (time.monotonic() - cached[0]) < settings.tenant_cache_ttl_seconds:
        return cached[1]

    tenant = await _load_tenant(tenant_id)
    _cache[tenant_id] = (time.monotonic(), tenant)
    logger.info("tenant_resolved", extra={"tenant_id": tenant_id})
    return tenant


def invalidate_tenant_cache(tenant_id: str) -> None:
    """Fuerza a que la próxima resolución de este tenant relea Firestore/GCS."""
    _cache.pop(tenant_id, None)
