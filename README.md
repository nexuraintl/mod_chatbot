# ms_ia_chatbot

Microservicio de chatbot con IA, **multitenant**, para atención al ciudadano. Cada cliente (tenant) tiene su propia identidad, protocolo de atención, respuestas predeterminadas y base de conocimiento, resueltos a partir de un `tenant_id`.

> Este README refleja la arquitectura multitenant introducida a partir del rediseño guiado por el agente OpenClaw (`agentes-ia-wpp/workspace_floridablanca`). El diseño completo, las decisiones tomadas y las alternativas descartadas están en el plan de arquitectura de esa sesión — este documento es la referencia operativa del código tal como quedó, no el historial de decisiones.

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
| Runtime | Python 3.10 |
| Servidor | Gunicorn + Uvicorn (`UvicornWorker`) |
| Modelo de IA / RAG | Google Gemini (`google-genai`), File Search Store |
| Registro de tenants | Google Cloud Firestore |
| Contenido de tenants | Google Cloud Storage (bucket por prefijo de tenant) |
| Scraping (fuente secundaria opcional) | httpx + BeautifulSoup4 |
| Contenerización | Docker (`python:3.10-slim`) |
| Despliegue | GCP Cloud Run |

**Ya no hay MySQL/SQLAlchemy/aiomysql** en este servicio — el fallback a base de datos institucional compartida se retiró; el contexto "institucional" ahora es el bucket propio de cada tenant.

## 3. Arquitectura y estructura del proyecto

```
ms_ia_chatbot/
├── app.py                          # Entrypoint local (python app.py)
├── Dockerfile
├── requirements.txt
├── scripts/
│   └── sync_tenant_kb.py           # CLI de backfill/reprocesamiento manual de un tenant
├── examples/tenants/floridablanca/ # Tenant de referencia completo (identity/protocol/predeterminadas/knowledge)
└── src/
    ├── main.py                     # Instancia FastAPI, registro de routers
    ├── config.py                   # Configuración por variables de entorno
    ├── routers/
    │   └── chat_router.py          # Endpoint POST /api/v1/chat
    ├── models/
    │   └── schemas.py              # ChatRequest / ChatResponse (Pydantic)
    └── services/
        ├── tenant_service.py               # Resolución de tenant: Firestore + GCS, cacheado con TTL
        ├── predetermined_answers_service.py # Fast path de respuestas sin LLM
        ├── gemini_service.py                # Integración Gemini (google-genai) + File Search Store
        ├── scraper_service.py               # Scraping web (fuente secundaria opcional)
        └── ingestion_service.py             # Ingesta de contenido del bucket al File Search Store del tenant
```

Servicio complementario, en repo/deploy separado: **`ms_ia_chatbot-ingest`** (ver sección 7).

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

### 4.1 Health Check
`GET /health` → `{"status": "ok"}` (sin autenticación).

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

| Variable | Requerida | Descripción |
|---|---|---|
| `GEMINI_API_KEY` | Sí | API key de Gemini con acceso a File Search. La app falla al arrancar si falta. |
| `GCP_PROJECT` | Sí | Proyecto GCP donde viven Firestore y el bucket de tenants. |
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

- **`src/services/ingestion_service.py`** — lógica compartida: registra el objeto de GCS, lo importa al store, y borra la versión previa si ya existía (evita contenido duplicado/obsoleto).
- **`scripts/sync_tenant_kb.py <tenant_id>`** — CLI para backfill inicial o reprocesamiento manual de todo el `knowledge/` de un tenant.
- **`ms_ia_chatbot-ingest`** (repo/servicio Cloud Run separado, junto a este) — expone `POST /events/gcs`, destino de un trigger de Eventarc sobre el bucket de tenants (`google.cloud.storage.object.v1.finalized` / `...v1.deleted`). Es el mecanismo de automatización real; está separado del servicio de chat porque necesita permisos distintos (escritura en Firestore + File Search vs. solo lectura).

## 8. Despliegue en Cloud Run

Comparado con el despliegue anterior (documentado en versiones previas de este README/PDF técnico):
- Ya **no** hace falta `--vpc-connector` ni `--set-secrets DB_PASSWORD` (no hay Cloud SQL).
- La cuenta de servicio del Cloud Run necesita `roles/datastore.user` (Firestore) y acceso de lectura al bucket de tenants.
- `ms_ia_chatbot-ingest` se despliega como servicio aparte, con su propia cuenta de servicio (`roles/storage.objectViewer` sobre el bucket + `roles/datastore.user`) y el trigger de Eventarc.

## 9. Estado y pendientes conocidos

- El uso de `google-genai` / File Search Store (`file_search_stores`, `files.register_files`) está implementado siguiendo la documentación oficial de Gemini, pero **no se ha validado todavía contra la API real** — es el primer paso a probar antes de un despliegue a producción.
- `examples/tenants/floridablanca/` es el primer tenant de referencia, con contenido real migrado desde el agente OpenClaw equivalente; `examples/tenants/floridablanca/PENDING.md` documenta qué contenido sigue faltando por parte del cliente.
