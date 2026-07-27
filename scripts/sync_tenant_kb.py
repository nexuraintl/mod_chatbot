#!/usr/bin/env python3
"""
CLI de backfill/reprocesamiento manual de la knowledge base de un tenant.

Uso:
    python scripts/sync_tenant_kb.py <tenant_id>

Reingesta TODOS los archivos bajo `knowledge/` en el bucket del tenant hacia su
File Search Store. Pensado para:
  - la carga inicial de un tenant nuevo (ej. migrar knowbase/ de Floridablanca de una vez).
  - reprocesar manualmente si algo quedó desincronizado.

No reemplaza el trigger automático de Eventarc (ver ms_chatbot_ingest) — lo
complementa. Reusa la misma lógica de api/services/ingestion_service.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.cloud import storage  # noqa: E402

from api.services import ingestion_service  # noqa: E402
from api.services.ingestion_service import get_tenant_doc_ref  # noqa: E402


def sync_tenant(tenant_id: str) -> None:
    tenant_ref = get_tenant_doc_ref(tenant_id)
    snapshot = tenant_ref.get()
    if not snapshot.exists:
        raise SystemExit(f"Tenant '{tenant_id}' no está dado de alta en Firestore. Créelo antes de sincronizar.")

    data = snapshot.to_dict()
    bucket_name = data["bucket"]
    prefix = data.get("prefix", f"{tenant_id}/")
    knowledge_prefix = f"{prefix}knowledge/"

    store_name = ingestion_service.ensure_store(tenant_id)

    storage_client = storage.Client(project=ingestion_service.settings.gcp_project)
    blobs = storage_client.list_blobs(bucket_name, prefix=knowledge_prefix)

    count = 0
    for blob in blobs:
        if blob.name.endswith("/"):
            continue  # "carpetas" vacías

        rel_path = blob.name[len(prefix):]  # ej. "knowledge/secretaria_hacienda/flujo_predial.md"
        ingestion_service.import_gcs_object(
            store_name=store_name,
            bucket=bucket_name,
            object_name=blob.name,
            tenant_id=tenant_id,
            rel_path=rel_path,
        )
        count += 1

    print(f"Listo: {count} documento(s) sincronizado(s) para el tenant '{tenant_id}' (store {store_name}).")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/sync_tenant_kb.py <tenant_id>")
    sync_tenant(sys.argv[1])
