import logging
from typing import Optional

from google import genai
from google.cloud import firestore

from src.config import settings

logger = logging.getLogger(__name__)

client = genai.Client(api_key=settings.GEMINI_API_KEY)
_firestore_client = firestore.Client(project=settings.GCP_PROJECT)

# Módulo de ingesta compartido entre scripts/sync_tenant_kb.py (backfill/CLI, en este
# repo) y el handler de Eventarc del servicio ms_ia_chatbot-ingest (repo separado, ver
# HANDOFF/plan de multitenencia). Nunca se llama desde el request path del chat.


def _doc_id_for_path(rel_path: str) -> str:
    """Firestore no permite '/' en un doc id suelto; se codifica de forma reversible-legible."""
    return rel_path.replace("/", "__")


def get_tenant_doc_ref(tenant_id: str):
    return _firestore_client.collection("tenants").document(tenant_id)


def ensure_store(tenant_id: str) -> str:
    """
    Devuelve el file_search_store_name del tenant, creándolo y persistiéndolo en
    Firestore la primera vez. Se asume que el documento del tenant ya existe
    (alta explícita de onboarding, ver plan sección 4.5).
    """
    tenant_ref = get_tenant_doc_ref(tenant_id)
    snapshot = tenant_ref.get()
    if not snapshot.exists:
        raise ValueError(f"Tenant '{tenant_id}' no está dado de alta en Firestore.")

    data = snapshot.to_dict()
    store_name = data.get("file_search_store_name")
    if store_name:
        return store_name

    display_name = f"tenant-{tenant_id}"
    store_name = None
    for store in client.file_search_stores.list():
        if store.display_name == display_name:
            store_name = store.name
            break
    if not store_name:
        store = client.file_search_stores.create(config={"display_name": display_name})
        store_name = store.name

    tenant_ref.update({"file_search_store_name": store_name})
    logger.info(f"INGEST_STORE_READY: tenant={tenant_id} store={store_name}")
    return store_name


def get_tracked_document(tenant_id: str, rel_path: str) -> Optional[str]:
    """Devuelve el document.name previamente ingestado para esta ruta del tenant, si existe."""
    doc_ref = get_tenant_doc_ref(tenant_id).collection("kb_documents").document(_doc_id_for_path(rel_path))
    snapshot = doc_ref.get()
    if snapshot.exists:
        return snapshot.to_dict().get("document_name")
    return None


def save_tracked_document(tenant_id: str, rel_path: str, document_name: str) -> None:
    doc_ref = get_tenant_doc_ref(tenant_id).collection("kb_documents").document(_doc_id_for_path(rel_path))
    doc_ref.set({"document_name": document_name, "rel_path": rel_path})


def delete_tracked_document(tenant_id: str, rel_path: str) -> None:
    doc_ref = get_tenant_doc_ref(tenant_id).collection("kb_documents").document(_doc_id_for_path(rel_path))
    doc_ref.delete()


def import_gcs_object(store_name: str, bucket: str, object_name: str, tenant_id: str, rel_path: str) -> str:
    """
    Ingresa (o re-ingresa) un objeto de GCS al File Search Store del tenant.

    Si esta ruta ya tenía un documento indexado, lo borra primero para no dejar
    contenido duplicado/obsoleto (Gemini podría citar la versión vieja). Devuelve
    el nuevo document.name y lo persiste en Firestore.
    """
    old_document_name = get_tracked_document(tenant_id, rel_path)
    if old_document_name:
        try:
            client.file_search_stores.documents.delete(name=old_document_name, force=True)
        except Exception as e:
            logger.warning(f"INGEST_DELETE_OLD_DOC_FAILED: {old_document_name}: {e}", exc_info=True)

    gcs_uri = f"gs://{bucket}/{object_name}"
    registered = client.files.register_files(uris=[gcs_uri])

    operation = client.file_search_stores.import_file(
        file_search_store_name=store_name,
        file_name=registered.files[0].name,
        custom_metadata=[
            {"key": "tenant_id", "value": tenant_id},
            {"key": "path", "value": rel_path},
        ],
    )

    document_name = operation.response.name
    save_tracked_document(tenant_id, rel_path, document_name)
    logger.info(f"INGEST_OK: tenant={tenant_id} path={rel_path} document={document_name}")
    return document_name


def remove_gcs_object(tenant_id: str, rel_path: str) -> None:
    """Contraparte de import_gcs_object para cuando se borra un archivo del bucket."""
    document_name = get_tracked_document(tenant_id, rel_path)
    if not document_name:
        logger.warning(f"INGEST_DELETE_NOOP: no había documento trackeado para tenant={tenant_id} path={rel_path}")
        return

    client.file_search_stores.documents.delete(name=document_name, force=True)
    delete_tracked_document(tenant_id, rel_path)
    logger.info(f"INGEST_DELETED: tenant={tenant_id} path={rel_path} document={document_name}")
