# ms_ia_chatbot

Microservicio de chatbot con IA, **multitenant**, para atención al ciudadano. Cada cliente (tenant) tiene su propia identidad, protocolo de atención, respuestas predeterminadas y base de conocimiento, resueltos a partir de un `tenant_id`.

> Este README refleja la arquitectura multitenant introducida a partir del rediseño guiado por el agente OpenClaw (`agentes-ia-wpp/workspace_floridablanca`), y la estructura de repositorio alineada al estándar de gobernanza **GOB-GCP-STD-01** de NEXURA. Este documento es la referencia operativa del código tal como quedó, no el historial de decisiones.

## 1. Descripción general

Dado `{"tenant_id": "floridablanca", "question": "..."}`, el servicio:

1. Resuelve la configuración del tenant (Firestore + cache en memoria con TTL).
2. Intenta responder con una **respuesta predeterminada** (fast path, sin costo de LLM) si la pregunta matchea un keyword conocido del tenant.
3. Si no hay match, genera la respuesta con **Gemini**, usando el **File Search Store** del tenant como fuente de contexto (RAG administrado por Google sobre la base de conocimiento del tenant).
4. Opcionalmente, si el request trae una `url` puntual y el tenant lo permite, suma ese contexto vía scraping como fuente secundaria.

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
| Scraping (fuente secundaria opcional) | httpx + BeautifulSoup4 |
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
│   └── sync_tenant_kb.py           # CLI de backfill/reprocesamiento manual de un tenant
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
        ├── scraper_service.py               # Scraping web (fuente secundaria opcional)
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
  "question": "¿Cómo pago mi impuesto predial?",
  "url": "https://ejemplo.gov.co/opcional"
}
```
- `tenant_id` (string, requerido).
- `question` (string, requerido).
- `url` (string o lista de strings, opcional) — solo se usa si el tenant tiene `allow_url_scraping: true`.

**Response 200:**
```json
{
  "answer": "Para pagar su impuesto predial debe...",
  "source": "predetermined | knowledge_base | knowledge_base+scraping"
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
  "predetermined_answers_path": "floridablanca/predetermined_answers.json",
  "allow_url_scraping": false
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

- El uso de `google-genai` / File Search Store (`file_search_stores`, `files.register_files`) está implementado siguiendo la documentación oficial de Gemini. Las versiones pinneadas en `requirements.txt` (`google-genai`, `google-cloud-firestore`, `google-cloud-storage`) **instalan y pasan los tests** (`pytest` corrido de verdad, no solo `py_compile`), pero **ninguna llamada se ha probado todavía contra la API real de Gemini** — sigue siendo el spike pendiente antes de un deploy real.
- Firestore, los buckets de tenants y los permisos IAM de `run-sa` **no existen todavía** en `pre-qa-functions` — ver `docs/MANUAL.md` para los comandos exactos de creación.
- `examples/tenants/floridablanca/` es el primer tenant de referencia, con contenido real migrado desde el agente OpenClaw equivalente; `examples/tenants/floridablanca/PENDING.md` documenta qué contenido sigue faltando por parte del cliente.
