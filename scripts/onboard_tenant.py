#!/usr/bin/env python3
"""
CLI de alta inicial de un tenant nuevo: crea su documento en Firestore, sube
el contenido local (identity.json, protocol.json, predetermined_answers.json,
knowledge/) al bucket, y corre la ingesta hacia su File Search Store.

Uso:
    python scripts/onboard_tenant.py <tenant_id> <bucket> <local_dir>

Ejemplo (con el layout de examples/tenants/):
    python scripts/onboard_tenant.py floridablanca nexura-chatbot-tenants-qa examples/tenants/floridablanca

Idempotente: si el tenant ya existe en Firestore no se sobreescribe el
documento; los archivos se re-suben (upload_from_filename sobreescribe) y la
ingesta reemplaza versiones previas del mismo path (ver ingestion_service).
No reemplaza sync_tenant_kb.py (backfill/resync de un tenant ya dado de alta)
ni el trigger de Eventarc de ms_chatbot_ingest (ingesta automática posterior a
este alta inicial) — es solo el paso de onboarding.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.cloud import storage  # noqa: E402

from api.services import ingestion_service  # noqa: E402


def create_tenant_doc(tenant_id: str, bucket_name: str, prefix: str, display_name: str) -> None:
    ref = ingestion_service.get_tenant_doc_ref(tenant_id)
    if ref.get().exists:
        print(f"Tenant '{tenant_id}' ya existe en Firestore, no se sobreescribe.")
        return
    ref.set(
        {
            "active": True,
            "display_name": display_name,
            "bucket": bucket_name,
            "prefix": prefix,
            "identity_path": f"{prefix}identity.json",
            "protocol_path": f"{prefix}protocol.json",
            "predetermined_answers_path": f"{prefix}predetermined_answers.json",
        }
    )
    print(f"Documento Firestore creado: tenants/{tenant_id}")


def upload_content(bucket_name: str, prefix: str, local_dir: Path) -> None:
    client = storage.Client(project=ingestion_service.settings.gcp_project)
    bucket = client.bucket(bucket_name)

    files_to_upload = [
        local_dir / "identity.json",
        local_dir / "protocol.json",
        local_dir / "predetermined_answers.json",
        *sorted((local_dir / "knowledge").rglob("*")),
    ]

    count = 0
    for local_path in files_to_upload:
        if not local_path.is_file():
            continue
        rel_path = local_path.relative_to(local_dir).as_posix()
        blob_name = f"{prefix}{rel_path}"
        bucket.blob(blob_name).upload_from_filename(str(local_path))
        print(f"  subido: gs://{bucket_name}/{blob_name}")
        count += 1

    print(f"Total subido: {count} archivo(s).")


def run_ingestion(tenant_id: str, bucket_name: str, prefix: str) -> None:
    store_name = ingestion_service.ensure_store(tenant_id)
    print(f"File Search Store listo: {store_name}")

    client = storage.Client(project=ingestion_service.settings.gcp_project)
    knowledge_prefix = f"{prefix}knowledge/"
    blobs = list(client.list_blobs(bucket_name, prefix=knowledge_prefix))

    count = 0
    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        rel_path = blob.name[len(prefix):]
        print(f"  ingestando: {rel_path} ...")
        document_name = ingestion_service.import_gcs_object(
            store_name=store_name,
            bucket=bucket_name,
            object_name=blob.name,
            tenant_id=tenant_id,
            rel_path=rel_path,
        )
        print(f"    -> {document_name}")
        count += 1

    print(f"Ingesta completa: {count} documento(s) indexado(s) en el store.")


def onboard(tenant_id: str, bucket_name: str, local_dir: Path, display_name: str) -> None:
    prefix = f"{tenant_id}/"
    print(f"== 1/3: alta en Firestore ({tenant_id}) ==")
    create_tenant_doc(tenant_id, bucket_name, prefix, display_name)
    print(f"\n== 2/3: subida a gs://{bucket_name}/{prefix} ==")
    upload_content(bucket_name, prefix, local_dir)
    print("\n== 3/3: ingesta al File Search Store ==")
    run_ingestion(tenant_id, bucket_name, prefix)


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        raise SystemExit(
            "Uso: python scripts/onboard_tenant.py <tenant_id> <bucket> <local_dir> [display_name]"
        )
    _tenant_id = sys.argv[1]
    _bucket = sys.argv[2]
    _local_dir = Path(sys.argv[3]).resolve()
    _display_name = sys.argv[4] if len(sys.argv) == 5 else _tenant_id
    onboard(_tenant_id, _bucket, _local_dir, _display_name)
