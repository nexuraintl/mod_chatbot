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
| POST | `/api/v1/chat` | Vía API Gateway | `{"tenant_id", "question"}` → `{"answer", "source"}` |

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
| `run-sa@pre-qa-functions.iam.gserviceaccount.com` | Identidad de ejecución del Cloud Run (compartida entre los 4 servicios: `qam`/`prem` × `ia-chatbot`/`chatbot-ingest`) | `roles/datastore.user` (Firestore), lectura del bucket de tenants (`roles/storage.objectViewer` alcanza; `ms_ia_chatbot` solo lee) | ✅ Otorgado (confirmado funcionando en el alta real del tenant `floridablanca`, 2026-07-24). |
| `deploy-sa@pre-qa-functions.iam.gserviceaccount.com` | Cuenta que usa Cloud Build para build + push + deploy | Permisos estándar de Cloud Build/Cloud Run deploy (ya operativos, usados por los servicios `ia-chatbot` actuales) | ✅ Operativo |
| `service-<PROJECT_NUMBER>@gcp-sa-generativelanguage.iam.gserviceaccount.com` (service agent gestionado por Google, uno por proyecto) | Lee el objeto de GCS **en nombre de Google** durante `file_search_stores.import_file()` — no es nuestra identidad la que lee el archivo | `roles/storage.objectViewer` sobre el bucket de tenants | ✅ Otorgado sobre `nexura-chatbot-tenants-qa` y `-prem` (2026-07-24). Descubierto durante el alta real del tenant `floridablanca`: sin este permiso, `import_file()` falla con `403 PERMISSION_DENIED: ...does not have storage.objects.get access...` aunque `run-sa` y las credenciales de `register_files()` estén correctas. **Repetir este bloqueo si se crea un bucket de tenants nuevo** — el número de proyecto (`58937908768` en `pre-qa-functions`) se obtiene con `gcloud projects describe pre-qa-functions --format="value(projectNumber)"`. |

Comandos para otorgar los roles (ya ejecutados en `pre-qa-functions`; repetir para un proyecto/bucket nuevo):

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

# Service agent de Generative Language (necesario para import_file() contra GCS):
gcloud storage buckets add-iam-policy-binding gs://nexura-chatbot-tenants-qa \
  --member="serviceAccount:service-58937908768@gcp-sa-generativelanguage.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud storage buckets add-iam-policy-binding gs://nexura-chatbot-tenants-prem \
  --member="serviceAccount:service-58937908768@gcp-sa-generativelanguage.iam.gserviceaccount.com" \
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

✅ **`qam-ia-chatbot` está desplegado en QA con el código multitenant y verificado de punta a punta en producción (2026-07-29)** — revisión `qam-ia-chatbot-00004-656`, imagen `gcr.io/pre-qa-functions/qam-ia-chatbot:59d6e84...`. Checklist completo:
1. ✅ Firestore Native mode en `pre-qa-functions` — hecho.
2. ✅ Buckets `nexura-chatbot-tenants-qa` / `-prem` — hecho.
3. ✅ Roles de IAM de la sección 5, incluyendo el service agent de Generative Language — hecho.
4. ✅ `google-genai`/File Search Store validado de punta a punta contra la API real — hecho (2026-07-24), 9 discrepancias reales encontradas y corregidas; ver README sección 10.
5. ✅ Tenant `floridablanca` dado de alta — hecho (2026-07-24): Firestore + bucket + 21 documentos indexados.
6. ✅ Trigger de Cloud Build corregido (apuntaba al servicio/repo equivocado y a una imagen de builder deprecada — ver README sección 10) y probado con un deploy real exitoso.
7. ✅ Probado end-to-end vía el Gateway real (`https://qa-apig-functions-v1-r2q3xgg.uc.gateway.dev/ia/chatbot/api/v1/chat`): `/health`, fast-path de respuestas predeterminadas y retrieval real de Gemini/File Search (`source: "knowledge_base"`) — todos responden correctamente con el tenant `floridablanca`.

Pendiente, no bloqueante: comparar respuestas contra el agente OpenClaw actual con preguntas reales del guion oficial; repetir esta misma validación para `prem-ia-chatbot` (rama `master`) antes de tocarla — su trigger de Cloud Build probablemente tenga los mismos dos bugs que tuvo el de QA.

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
