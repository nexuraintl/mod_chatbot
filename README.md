# ms_ia_chatbot

Microservicio de chatbot con IA, **multitenant**, para atención al ciudadano. Cada cliente (tenant) tiene su propia identidad, protocolo de atención, respuestas predeterminadas y base de conocimiento, resueltos a partir de un `tenant_id`.

> Este README refleja la arquitectura multitenant introducida a partir del rediseño guiado por el agente OpenClaw (`agentes-ia-wpp/workspace_floridablanca`), y la estructura de repositorio alineada al estándar de gobernanza **GOB-GCP-STD-01** de NEXURA. Este documento es la referencia operativa del código tal como quedó, no el historial de decisiones.

## 1. Descripción general

Dado `{"tenant_id": "floridablanca", "question": "..."}`, el servicio:

1. Resuelve la configuración del tenant (Firestore + cache en memoria con TTL).
2. Intenta responder con una **respuesta predeterminada** (fast path, sin costo de LLM) si la pregunta matchea un keyword conocido del tenant.
3. Si no hay match, genera la respuesta con **Gemini**, usando el **File Search Store** del tenant como fuente de contexto (RAG administrado por Google sobre la base de conocimiento del tenant).

No hay integración con WhatsApp ni autenticación propia — el servicio solo responde preguntas dado un tenant válido; la mensajería y la autenticación quedan del lado del API Gateway/cliente que consuma este API.

## 2. Stack tecnológico

| Componente | Tecnología |
|---|---|
| Framework web | FastAPI |
| Runtime | Python 3.11 |
| Servidor | Gunicorn + Uvicorn (`UvicornWorker`) |
| Configuración | `pydantic-settings` (`api/core/config.py`) |
| Observabilidad | Logs JSON estructurados + `X-Correlation-ID` (`api/core/logging.py`, `api/core/middleware.py`) |
| Modelo de IA / RAG | Google Gemini (`google-genai`), File Search Store |
| Registro de tenants | Google Cloud Firestore |
| Contenido de tenants | Google Cloud Storage (bucket por prefijo de tenant) |
| Contenerización | Docker multi-stage (`python:3.11-slim`, usuario no-root) |
| Despliegue | GCP Cloud Run (proyecto `pre-qa-functions` en preproducción/QA) |

**Ya no hay MySQL/SQLAlchemy/aiomysql** en este servicio — el fallback a base de datos institucional compartida se retiró; el contexto "institucional" ahora es el bucket propio de cada tenant.

## 3. Arquitectura y estructura del proyecto

```
ms_ia_chatbot/
├── app.py                          # Entrypoint local (python app.py)
├── Dockerfile                      # Multi-stage, usuario no-root
├── .dockerignore
├── .env.example
├── requirements.txt
├── requirements-dev.txt
├── cloudbuild.yaml                 # Build + push + deploy a Cloud Run (pre-qa-functions)
├── .azure-pipelines.yml            # Bridge ADO -> GitHub (nexuraintl), dispara Cloud Build
├── scripts/
│   ├── onboard_tenant.py           # CLI de alta inicial de un tenant (Firestore + subida + ingesta)
│   └── sync_tenant_kb.py           # CLI de backfill/reprocesamiento manual de un tenant ya dado de alta
├── examples/tenants/floridablanca/ # Tenant de referencia completo (identity/protocol/predeterminadas/knowledge)
├── tests/
│   ├── conftest.py
│   └── test_health.py              # health, version, correlation-id (generado y propagado)
└── api/
    ├── main.py                     # setup_logging() + CorrelationMiddleware + registro de routers
    ├── core/
    │   ├── config.py                # Settings (pydantic-settings) + get_settings() con @lru_cache
    │   ├── logging.py                # JsonFormatter: severity, trace, correlation_id
    │   └── middleware.py             # CorrelationMiddleware + ContextVar de trace
    ├── models/
    │   └── schemas.py                # ChatRequest / ChatResponse (Pydantic)
    ├── routers/
    │   ├── health.py                 # GET /health, GET /version (sin prefijo de versión)
    │   └── v1/
    │       └── chat_router.py        # POST /api/v1/chat
    └── services/
        ├── tenant_service.py               # Resolución de tenant: Firestore + GCS, cacheado con TTL
        ├── predetermined_answers_service.py # Fast path de respuestas sin LLM
        ├── gemini_service.py                # Integración Gemini (google-genai) + File Search Store
        └── ingestion_service.py             # Ingesta de contenido del bucket al File Search Store del tenant
```

> Nota de nomenclatura: el prefijo de negocio quedó como `/api/v1` (no `/v1`) — decisión deliberada al aplicar el estándar de gobernanza, para no arriesgar romper un Gateway que ya pudiera apuntar a esa ruta.

Servicio complementario, en repo/deploy separado: **`ms_chatbot_ingest`** (ver sección 7).

### 3.1 Estructura de un tenant (bucket de GCS)

Ver `examples/tenants/floridablanca/` como referencia completa. Layout esperado bajo `gs://<TENANT_BUCKET>/<tenant_id>/`:

```
<tenant_id>/
├── identity.json               # Persona, tono, reglas de opacidad/confidencialidad
├── protocol.json                # Reglas de formato, escalamiento, fuera-de-alcance, idiomas
├── predetermined_answers.json   # keyword -> respuesta fija (fast path)
└── knowledge/                   # Documentos que se ingestan al File Search Store del tenant
    └── <subcarpetas libres>/*.md, *.txt, *.pdf, ...
```

`identity.json` y `protocol.json` se cargan completos en cada request (van al `system_instruction` de Gemini). `knowledge/` **no** se lee en el hot path — se ingesta por separado (ver sección 6) y Gemini hace el retrieval automáticamente vía File Search.

## 4. API Reference

### 4.1 Infraestructura
- `GET /health` → `{"status": "UP"}` (sin autenticación).
- `GET /version` → `{"service": "...", "version": "...", "environment": "..."}` (sin autenticación).

Ambos endpoints devuelven el header `X-Correlation-ID` (generado si el request no lo trae, o propagado si sí).

### 4.2 Chat
`POST /api/v1/chat`

**Request:**
```json
{
  "tenant_id": "floridablanca",
  "question": "¿Cómo pago mi impuesto predial?"
}
```
- `tenant_id` (string, requerido, no vacío).
- `question` (string, requerido).

**Response 200:**
```json
{
  "answer": "Para pagar su impuesto predial debe...",
  "source": "predetermined | knowledge_base"
}
```

**Errores:**
| Código | Causa |
|---|---|
| 404 | `tenant_id` no existe en Firestore o está inactivo |
| 422 | Payload inválido (validación Pydantic) |
| 500 | Error interno (Gemini, File Search, etc.) |

## 5. Variables de entorno

Ver `.env.example` para la lista completa con comentarios. Resumen:

| Variable | Requerida | Descripción |
|---|---|---|
| `SERVICE_NAME` | No (default `ms_ia_chatbot`) | Nombre del servicio, se expone en `/version` y en los logs. |
| `SERVICE_VERSION` | No | Versión desplegada. |
| `ENVIRONMENT` | No (default `dev`) | `dev` \| `qa` \| `preprod` \| `prod`. |
| `LOG_LEVEL` | No (default `INFO`) | Nivel de log. |
| `GOOGLE_CLOUD_PROJECT` | No | Proyecto GCP, para correlación de traces en Cloud Logging. |
| `GEMINI_API_KEY` | **Sí** | API key de Gemini con acceso a File Search. La app falla al arrancar si falta. En Cloud Run se inyecta vía Secret Manager, nunca como env var plana. |
| `GCP_PROJECT` | No | Proyecto GCP donde viven Firestore y el bucket de tenants. |
| `TENANT_BUCKET` | No | Bucket por defecto de tenants (cada tenant puede tener su propio `bucket` en su doc de Firestore). |
| `TENANT_CACHE_TTL_SECONDS` | No (default 90) | TTL del cache en memoria de la config de cada tenant. |

## 6. Registro de tenants (Firestore)

Colección `tenants`, un documento por `tenant_id`:

```json
{
  "active": true,
  "display_name": "Alcaldía de Floridablanca",
  "bucket": "<TENANT_BUCKET>",
  "prefix": "floridablanca/",
  "file_search_store_name": "fileSearchStores/...",
  "identity_path": "floridablanca/identity.json",
  "protocol_path": "floridablanca/protocol.json",
  "predetermined_answers_path": "floridablanca/predetermined_answers.json"
}
```

El alta de un tenant es **explícita** (script/consola), no automática: un archivo subido con un `tenant_id` mal escrito no debe crear un cliente fantasma. `file_search_store_name` se completa solo una vez, durante la primera ingesta — el request path de chat nunca crea ni busca stores, solo lee este campo.

Ver `examples/tenants/floridablanca/README.md` para el procedimiento completo de alta + subida al bucket + ingesta de un tenant nuevo.

## 7. Ingesta de contenido (`knowledge/` → File Search Store)

La subida de archivos al bucket sigue siendo manual (alguien tiene que poner el archivo ahí). Lo que es automático es todo lo posterior: en cuanto un archivo aparece bajo `<tenant>/knowledge/`, se debe reflejar en el File Search Store del tenant sin correr nada a mano.

- **`api/services/ingestion_service.py`** — lógica compartida: registra el objeto de GCS, lo importa al store, y borra la versión previa si ya existía (evita contenido duplicado/obsoleto).
- **`scripts/sync_tenant_kb.py <tenant_id>`** — CLI para backfill inicial o reprocesamiento manual de todo el `knowledge/` de un tenant.
- **`ms_chatbot_ingest`** (repo/servicio Cloud Run separado, junto a este) — expone `POST /events/gcs`, destino de un trigger de Eventarc sobre el bucket de tenants (`google.cloud.storage.object.v1.finalized` / `...v1.deleted`). Es el mecanismo de automatización real; está separado del servicio de chat porque necesita permisos distintos (escritura en Firestore + File Search vs. solo lectura).

## 8. Despliegue en Cloud Run (`pre-qa-functions`)

`cloudbuild.yaml` define build + push a `gcr.io/pre-qa-functions/<service>` + deploy, parametrizado con variables de sustitución. Defaults = ambiente QA (`qam-ia-chatbot`); el ambiente `prem` (`prem-ia-chatbot`) sobreescribe `_SERVICE_NAME`/`_ENVIRONMENT`/`_TENANT_BUCKET` a nivel de trigger de Cloud Build. Detalle completo (IAM, variables, comandos de creación de Firestore/buckets) en [`docs/MANUAL.md`](docs/MANUAL.md).

⚠️ **`qam-ia-chatbot` y `prem-ia-chatbot` ya están desplegados** (corriendo el código anterior, single-tenant + MySQL) **con auto-deploy en push a las ramas `qa`/`master`**. No mergear/pushear a esas ramas hasta que Firestore, los buckets (`nexura-chatbot-tenants-qa` / `-prem`) y los permisos IAM de `run-sa` existan — ver `docs/MANUAL.md` sección 6.

Comparado con el despliegue anterior (basado en MySQL/Cloud SQL):
- Ya **no** hace falta `--vpc-connector` ni `--set-secrets DB_PASSWORD`.
- La cuenta de servicio (`run-sa@pre-qa-functions.iam.gserviceaccount.com`, compartida por los 4 servicios) necesita `roles/datastore.user` (Firestore) y acceso de lectura al bucket de tenants — hoy no tiene ninguno de los dos.
- `ms_chatbot_ingest` se despliega como servicio aparte (`qam-chatbot-ingest` / `prem-chatbot-ingest`, aún no desplegados), con el trigger de Eventarc como único disparador — **no** se registra en el API Gateway.
- Ingress en `all` (no `internal-and-cloud-load-balancing`) — restringirlo causó problemas de acceso desde el API Gateway.

## 9. Tests

```bash
pip install -r requirements-dev.txt
pytest
```

`tests/conftest.py` inyecta credenciales dummy (`GEMINI_API_KEY`, `GCP_PROJECT`) solo para que los clientes de Firestore/GCS/Gemini se puedan instanciar al importar `api.main` — ningún test hace llamadas reales a GCP ni a Gemini.

## 10. Estado y pendientes conocidos

- ✅ **Spike de `google-genai`/File Search Store validado de punta a punta contra la API real** (2026-07-24), incluyendo `gemini_service.generate_answer()` tal cual corre en producción y el flujo completo de `ingestion_service.import_gcs_object()` contra un bucket real (`gs://nexura-chatbot-tenants-qa/...`, no un archivo local). Se encontraron y corrigieron **9 discrepancias reales** entre lo documentado/asumido y el comportamiento real de la API:
  1. `google-genai==1.2.0` (pin original) **no tiene `file_search_stores`** — hace falta `>=2.14.0`.
  2. Ese salto de versión arrastra `httpx>=0.28`, incompatible con el `TestClient` de `fastapi==0.109.0` (`app=` fue removido) — se subió todo el stack de FastAPI/Starlette/Uvicorn a versiones modernas (ver `requirements.txt`).
  3. `import_file(custom_metadata=[...])` no existe como kwarg directo — va envuelto en `config=types.ImportFileConfig(custom_metadata=[types.CustomMetadata(key=..., string_value=...)])`.
  4. `import_file()` es una long-running operation: hay que hacer *polling* con `client.operations.get(operation)` hasta `done=True` antes de leer `operation.response` — si no, `document_name` queda `None` (rompía el borrado de duplicados). Y el campo correcto es `operation.response.document_name`, no `.name`.
  5. `documents.delete(force=True)` tampoco es kwarg directo — va en `config=types.DeleteDocumentConfig(force=True)`; y `name=` espera el resource name completo (`fileSearchStores/.../documents/...`), no el ID corto.
  6. `files.register_files()` requiere un `auth=` (credenciales de GCP) explícito — no lo toma solo del entorno.
  7. `gemini-2.0-flash` está deprecado (404) — se migró a `gemini-2.5-flash`.
  8. **El scope de las credenciales de `auth=` para `register_files()` no alcanza con el default de `google.auth.default()`** — la API responde `403 ACCESS_TOKEN_SCOPE_INSUFFICIENT` a menos que se pidan explícitamente los scopes `https://www.googleapis.com/auth/cloud-platform` **y** `https://www.googleapis.com/auth/devstorage.read_only` (ya corregido en `_gcp_credentials()`, ambos repos). Con credenciales de **usuario** (`gcloud auth application-default login`), pedir un scope no estándar puede además chocar con la pantalla de "aplicación bloqueada" de Google si el cliente OAuth no está verificado para ese scope — con una service account (JWT, sin pantalla de consentimiento) no pasa.
  9. **`import_file()` necesita un permiso de IAM adicional que no está documentado en ningún lado obvio**: el propio *service agent* gestionado por Google para la Generative Language API (`service-<PROJECT_NUMBER>@gcp-sa-generativelanguage.iam.gserviceaccount.com`) es quien lee el objeto de GCS al importar — no nuestra identidad — y necesita `roles/storage.objectViewer` (o equivalente) sobre el bucket del tenant. Sin este permiso, `import_file()` falla con `403 PERMISSION_DENIED: ...does not have storage.objects.get access...`. **Ya otorgado** sobre `nexura-chatbot-tenants-qa` y `nexura-chatbot-tenants-prem` (ver `docs/MANUAL.md` sección 5) — hace falta repetirlo si se crea un bucket de tenants nuevo.

  Todo esto ya está corregido en `api/services/gemini_service.py` e `ingestion_service.py` (ambos repos).
- ✅ **Tenant `floridablanca` dado de alta y operativo en `pre-qa-functions`** (2026-07-24): documento en Firestore, contenido subido a `gs://nexura-chatbot-tenants-qa/floridablanca/` y 21 documentos de `knowledge/` indexados en su File Search Store (`fileSearchStores/tenantfloridablanca-oagnjysqdgfr`). Verificado end-to-end: el fast-path de respuestas predeterminadas y `generate_answer()` con retrieval real (probado con una pregunta sobre el calendario tributario 2026, respondió citando correctamente la Resolución 6059/2025). Ver `scripts/onboard_tenant.py` para dar de alta el próximo tenant.
- Firestore, los buckets de tenants y los permisos IAM base de `run-sa` (`datastore.user`, `storage.objectViewer`) — creados/otorgados en `pre-qa-functions`, confirmados funcionando en el onboarding de `floridablanca`.
- `examples/tenants/floridablanca/` es el contenido de referencia que se usó para el alta real; `examples/tenants/floridablanca/PENDING.md` documenta qué contenido sigue faltando por parte del cliente (no bloquea el uso del tenant, son mejoras incrementales).
- ✅ **`qam-ia-chatbot` desplegado en QA con el código multitenant y verificado de punta a punta en producción** (2026-07-29, PR `feature/gob-gcp-std-01` → `dev` → `qa`). Se encontraron y corrigieron **2 problemas reales de infraestructura**, no de código, al primer intento de deploy real:
  1. **El trigger de Cloud Build de la rama `qa` apuntaba al servicio equivocado.** Escuchaba el repo de GitHub correcto (`nexuraintl/ms_ia_chatbot`, una vez corregido un desajuste de nombre por un rename previo del repo) pero desplegaba a un Cloud Run service huérfano (`qa-ia-chatbot`, con 35 revisiones de historial pero **sin permisos IAM de Firestore/GCS** — usaba la service account default de Compute, no `run-sa`) en vez de a `qam-ia-chatbot` (el que realmente usa el API Gateway real, confirmado leyendo su spec OpenAPI). Además el trigger tenía su propio build inline en vez de usar el `cloudbuild.yaml` del repo, así que nunca iba a setear `GCP_PROJECT`/`TENANT_BUCKET`/etc. Se corrigió el trigger para que apunte a `qam-ia-chatbot` y use `filename: cloudbuild.yaml`.
  2. **`cloudbuild.yaml` usaba una imagen de builder deprecada** (`gcr.io/google-cloud-sdk/slim`) para el step de deploy — Google migró ese path a Artifact Registry y `deploy-sa` no tiene permiso de descarga ahí, el pull fallaba con 403. Se reemplazó por `gcr.io/google.com/cloudsdktool/cloud-sdk:slim`, el path que usan (y les funciona) todos los demás triggers reales del proyecto.

  Con ambos corregidos, el deploy real tuvo éxito (`qam-ia-chatbot-00004-656`) y se probó end-to-end vía el Gateway real (`https://qa-apig-functions-v1-r2q3xgg.uc.gateway.dev/ia/chatbot/api/v1/chat`): `/health`, el fast-path de respuestas predeterminadas y una pregunta libre respondida con `source: "knowledge_base"` (retrieval real de Gemini/File Search, citando correctamente el Estatuto Tributario Municipal). El servicio solo acepta invocaciones de `api-gateway@pre-qa-functions.iam.gserviceaccount.com` (`--no-allow-unauthenticated`), consistente con el diseño.
- Pendiente siguiente: comparar respuestas del chatbot multitenant contra las del agente OpenClaw equivalente con preguntas reales del guion oficial; repetir esta misma validación de deploy para `prem-ia-chatbot` (rama `master`) antes de tocarla — su trigger probablemente tenga los mismos dos problemas que tuvo el de QA; y desplegar `ms_chatbot_ingest` + su trigger de Eventarc para que la ingesta futura sea automática (hoy el alta/resync se corre a mano con `scripts/onboard_tenant.py` / `scripts/sync_tenant_kb.py`).
