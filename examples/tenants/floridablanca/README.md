# Tenant: floridablanca (Alcaldía de Floridablanca, Santander)

Primer tenant real de `ms_ia_chatbot`, migrado por completo desde
`agentes-ia-wpp/workspace_floridablanca` (agente OpenClaw). Layout según el
plan de multitenencia, sección 2.

- `identity.json` / `protocol.json` — persona, tono y reglas de atención, portados de `IDENTITY.md`/`SOUL.md`/`AGENTS.md`. El contacto del administrador (Jhoan) **no** se incluyó a propósito: no lo necesita el modelo para atender al ciudadano, así que nunca entra al prompt (más seguro que confiar solo en la instrucción "no lo revele").
- `predetermined_answers.json` — 15 respuestas de fast path (sin costo de LLM): menú principal, los 4 impuestos, PQRSD, trámites, directorio, transparencia, participación, y tres redirecciones "duras" que no dependen de que el LLM las recuerde bien: **tránsito/comparendos** (no es de la Alcaldía), **matrícula escolar** (no existe ese trámite, no inventar), y **concepto sanitario** (único trámite 100% en línea de Salud).
- `knowledge/` — los **17 documentos** de `workspace_floridablanca/knowbase/` (misma estructura de subcarpetas por secretaría) más **4 documentos nuevos** obtenidos del sitio oficial (https://www.floridablanca.gov.co/) el 2026-07-23, dos de ellos descargados como PDF con autorización explícita y convertidos a texto:
  - `secretaria_hacienda/` — flujo_predial, flujo_ica, flujo_reteica, flujo_rit, portal_tributario_suiteneptuno, **calendario_tributario_2026** (nuevo — Resolución 6059/2025, plazos reales de ICA/ReteICA/publicidad exterior/sobretasa gasolina/etc. para 2026), **estatuto_tributario_municipal** (nuevo — Acuerdo 012/2021 completo, 262 páginas; define que la UVT de Floridablanca es la UVT nacional de la DIAN, no una cifra propia)
  - `atencion_ciudadano/` — flujo_pqrsd_atencion, pqrsd_y_citas
  - `preguntas_frecuentes/` — flujo_tramites_interes (docentes/CNSC, RUNT, catastro, programas sociales, SUIT)
  - `secretaria_general/` — contacto_y_horarios, directorio_de_dependencias
  - `secretaria_educacion/`, `secretaria_gobierno/`, `secretaria_planeacion/`, `secretaria_salud/`, `secretaria_desarrollo_social/` — trámites por dependencia
  - `accesos_rapidos/` — enlaces_oficiales
  - `general/` — seguridad_y_datos_personales (privacidad/manejo de datos), **simbolos_patrios** (nuevo — escudo, bandera, himno; letra del himno no reproducida por derechos de autor), **certificado_accesibilidad** (nuevo — certificación AA / WCAG 2.1)
- `PENDING.md` — huecos de contenido que **ya existían** en la fuente y siguen sin resolver (Estatuto Tributario, certificado de accesibilidad, plazos de Predial, valor UVT, Plan de Desarrollo completo, manual de funciones), más el detalle de qué se buscó, qué se encontró y qué quedó pendiente de tu autorización para descargar.

A diferencia de OpenClaw, no hace falta un `KNOWBASE_INDEX.md` manual: el File
Search Store hace el retrieval automáticamente sobre todo `knowledge/`, no hay
que mantener un índice para que el modelo sepa qué archivo leer.

## Cómo darlo de alta

1. Crear el documento del tenant en Firestore (ver ejemplo abajo) — paso explícito, no automático.
2. Subir esta carpeta al bucket:
   ```bash
   gsutil -m cp -r examples/tenants/floridablanca gs://<TENANT_BUCKET>/floridablanca
   ```
   (Esto excluye implícitamente `PENDING.md` y este `README.md` si se sincroniza solo `knowledge/` + los 3 JSON — o se pueden subir igual, `tenant_service.py` solo lee las rutas declaradas en Firestore, y el handler de ingesta solo actúa sobre objetos bajo `knowledge/`.)
3. Si `ms_ia_chatbot-ingest` ya está desplegado con el trigger de Eventarc, la ingesta al File Search Store es automática. Si no, forzarla con:
   ```bash
   python scripts/sync_tenant_kb.py floridablanca
   ```

```python
from google.cloud import firestore

db = firestore.Client(project="<GCP_PROJECT>")
db.collection("tenants").document("floridablanca").set({
    "active": True,
    "display_name": "Alcaldía de Floridablanca",
    "bucket": "<TENANT_BUCKET>",
    "prefix": "floridablanca/",
    "identity_path": "floridablanca/identity.json",
    "protocol_path": "floridablanca/protocol.json",
    "predetermined_answers_path": "floridablanca/predetermined_answers.json",
})
```

## Prueba rápida esperada (una vez desplegado e ingestado)

```json
POST /api/v1/chat
{"tenant_id": "floridablanca", "question": "cómo pago mi predial"}
```
Debería responder desde `predetermined_answers.json` (`source: "predetermined"`, cero costo de Gemini). Una pregunta más específica como "qué pasa si mi predio está a nombre de otra persona" debería caer al File Search Store y citar `flujo_predial.md` (`source: "knowledge_base"`).
