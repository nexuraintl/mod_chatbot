# Manual de Gobernanza — ms_ia_chatbot

Cumplimiento del estándar **GOB-GCP-STD-01**. Última actualización: 2026-07-23.

## 1. Descripción funcional

- **Nombre del servicio:** `ms_ia_chatbot`
- **Propósito:** Microservicio de chatbot con IA, multitenant, para atención al ciudadano. Dado un `tenant_id`, responde preguntas usando la identidad, protocolo, respuestas predeterminadas y base de conocimiento propios de ese cliente (Firestore + GCS + Gemini File Search Store).
- **Módulo / iniciativa:** Plataforma de IA — chatbots institucionales multitenant.
- **Responsable:** Santiago Valenzuela López (svalenzuela@nexura.com)

## 2. Arquitectura

- **Proyecto GCP:** `pre-qa-functions` (cubre tanto QA como preproducción — ambientes `qam` y `prem`).
- **Región:** `us-central1`.
- **Servicios Cloud Run:**
  | Ambiente | Nombre del servicio | Estado |
  |---|---|---|
  | QA (`qam`) | `qam-ia-chatbot` | Ya desplegado — corre el código anterior (single-tenant, MySQL). Pendiente redeploy con esta versión multitenant, condicionado a que exista Firestore + bucket (ver sección 8). |
  | Preproducción (`prem`) | `prem-ia-chatbot` | Ídem. |
- **API Gateway:** ya configurado para ambos ambientes, con el endpoint de `ia-chatbot` ya registrado apuntando a `/api/v1/chat`. El path no cambia con este rediseño, así que no debería requerir reconfiguración del Gateway — solo re-verificar tras el primer redeploy.
- **Dependencias:**
  - Google Gemini (`google-genai`), File Search Store — por tenant.
  - Firestore (Native mode) — registro de tenants. **No existe todavía en `pre-qa-functions`, hay que crearla.**
  - Google Cloud Storage — contenido de cada tenant (`identity.json`, `protocol.json`, `predetermined_answers.json`, `knowledge/`). Buckets **por crear**: `nexura-chatbot-tenants-qa`, `nexura-chatbot-tenants-prem`.
  - `ms_chatbot_ingest` (servicio hermano) — sincroniza `knowledge/` del bucket hacia el File Search Store de cada tenant vía Eventarc.

## 3. Endpoints

| Método | Path | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | No | `{"status": "UP"}` |
| GET | `/version` | No | `{"service", "version", "environment"}` |
| POST | `/api/v1/chat` | Vía API Gateway | `{"tenant_id", "question", "url"?}` → `{"answer", "source"}` |

## 4. Variables y secretos

| Variable | Origen en Cloud Run | Valor / Secreto |
|---|---|---|
| `SERVICE_NAME` | `--set-env-vars` | `qam-ia-chatbot` / `prem-ia-chatbot` (= `${_SERVICE_NAME}`) |
| `ENVIRONMENT` | `--set-env-vars` | `qa` / `prem` |
| `GOOGLE_CLOUD_PROJECT`, `GCP_PROJECT` | `--set-env-vars` | `pre-qa-functions` |
| `TENANT_BUCKET` | `--set-env-vars` | `nexura-chatbot-tenants-qa` / `nexura-chatbot-tenants-prem` |
| `LOG_LEVEL` | `--set-env-vars` | `INFO` |
| `GEMINI_API_KEY` | **Secret Manager** | Secreto `GEMINI_API_KEY`, versión `latest` — **nunca** como variable de entorno plana. |

`TENANT_CACHE_TTL_SECONDS` queda con su default de código (90s); no se parametriza por ambiente salvo que se necesite ajustar.

## 5. IAM

| Cuenta | Rol en este servicio | Roles requeridos | Estado |
|---|---|---|---|
| `run-sa@pre-qa-functions.iam.gserviceaccount.com` | Identidad de ejecución del Cloud Run (compartida entre los 4 servicios: `qam`/`prem` × `ia-chatbot`/`chatbot-ingest`) | `roles/datastore.user` (Firestore), lectura del bucket de tenants (`roles/storage.objectViewer` alcanza; `ms_ia_chatbot` solo lee) | ⚠️ **Pendiente de otorgar** — hoy no tiene ninguno de los dos. |
| `deploy-sa@pre-qa-functions.iam.gserviceaccount.com` | Cuenta que usa Cloud Build para build + push + deploy | Permisos estándar de Cloud Build/Cloud Run deploy (ya operativos, usados por los servicios `ia-chatbot` actuales) | ✅ Operativo |

Comandos para otorgar los roles pendientes a `run-sa` (ejecutar una vez existan los buckets):

```bash
gcloud projects add-iam-policy-binding pre-qa-functions \
  --member="serviceAccount:run-sa@pre-qa-functions.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud storage buckets add-iam-policy-binding gs://nexura-chatbot-tenants-qa \
  --member="serviceAccount:run-sa@pre-qa-functions.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud storage buckets add-iam-policy-binding gs://nexura-chatbot-tenants-prem \
  --member="serviceAccount:run-sa@pre-qa-functions.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

## 6. Despliegue

Definido en `cloudbuild.yaml` (defaults = QA; `prem` sobreescribe `_SERVICE_NAME`/`_ENVIRONMENT`/`_TENANT_BUCKET` a nivel de trigger de Cloud Build).

| Parámetro | Valor |
|---|---|
| Min instances | 0 |
| Max instances | 3 |
| CPU | 1 |
| Memoria | 512Mi |
| Concurrency | 80 |
| Timeout | 300s |
| Ingress | `all` (decisión deliberada — restringir a `internal-and-cloud-load-balancing` causó problemas de acceso desde el API Gateway) |
| Artifact Registry | `gcr.io/pre-qa-functions/<service>` (Container Registry heredado, no Artifact Registry regional) |

⚠️ **No ejecutar el deploy real (ni mergear a `qa`/`master`, que auto-despliegan) hasta:**
1. Crear la base Firestore Native mode en `pre-qa-functions` (ver comando abajo).
2. Crear los buckets `nexura-chatbot-tenants-qa` / `-prem`.
3. Otorgar los roles de IAM de la sección 5.
4. Validar `google-genai`/File Search Store contra la API real (spike pendiente, ver README sección 10).
5. Dar de alta el tenant `floridablanca` y comparar respuestas contra el agente OpenClaw actual.

```bash
gcloud firestore databases create --project=pre-qa-functions --location=us-central1 --type=firestore-native

gcloud storage buckets create gs://nexura-chatbot-tenants-qa --project=pre-qa-functions --location=us-central1
gcloud storage buckets create gs://nexura-chatbot-tenants-prem --project=pre-qa-functions --location=us-central1
```

## 7. Observabilidad

Logs JSON estructurados a stdout (`api/core/logging.py`), con `severity`, `logging.googleapis.com/trace`, `logging.googleapis.com/spanId` y `correlation_id`. Filtro sugerido en Cloud Logging:

```
resource.type="cloud_run_revision"
resource.labels.service_name="qam-ia-chatbot"
```
(sustituir `qam-ia-chatbot` por `prem-ia-chatbot` según el ambiente a inspeccionar)

Cada respuesta incluye el header `X-Correlation-ID` (generado o propagado desde el request), útil para correlacionar un request del ciudadano con sus logs.
