# Pendientes por parte del cliente (Alcaldía de Floridablanca)

Heredado de `agentes-ia-wpp/HANDOFF_FLORIDABLANCA.md` y de los `TODO.md` de cada
secretaría en `workspace_floridablanca/knowbase/`. El 2026-07-23 se revisó
https://www.floridablanca.gov.co/ para ver si alguno de estos puntos ya está
disponible públicamente. Resultado por ítem:

## ✅ Resuelto — portado a `knowledge/`
- **Símbolos patrios** (escudo, bandera, himno) — texto completo en `knowledge/general/simbolos_patrios.md`. La letra del himno no se reprodujo íntegra (derechos de autor); queda enlazada a la fuente oficial.
- **Calendario Tributario 2026** — descargado con tu autorización y portado completo a `knowledge/secretaria_hacienda/calendario_tributario_2026.md` (Resolución 6059 de 2025: ICA, ReteICA, publicidad exterior visual, sobretasa gasolina, espectáculos públicos, delineación urbana, juegos permitidos y azar, alumbrado público, degüello de ganado menor, telefonía, contribución especial de seguridad, certificados de retención). **No cubre Predial ni menciona el valor de la UVT como cifra fija** — ver el hallazgo del Estatuto Tributario abajo.
- **Certificación de accesibilidad de la sede electrónica** — descargada con tu autorización y portada a `knowledge/general/certificado_accesibilidad.md`. Nivel AA, 100% de cumplimiento según Resolución 1519 de 2020 / WCAG 2.1, expedido por Nexura Internacional S.A.S. el 31/07/2024.
- **Estatuto Tributario Municipal (norma base)** — descargado con tu autorización: Acuerdo 012 de 2021 completo (262 páginas), portado a `knowledge/secretaria_hacienda/estatuto_tributario_municipal.md`. **Hallazgo clave (Artículo 12):** Floridablanca no fija un valor de UVT propio — usa la **UVT nacional** (Artículo 868 del Estatuto Tributario Nacional), reajustada cada año por la DIAN. Esto resuelve conceptualmente el pendiente de "valor de la UVT vigente": no es un dato municipal a buscar, es el valor nacional de la DIAN para el año en curso.

## ✅ Confirmado que existe públicamente — pendiente de tu autorización para descargar el PDF y portarlo a `knowledge/`
Encontré estos documentos en el sitio oficial. No los descargué porque implica traer un archivo externo al proyecto — decisión tuya, no mía:

- **Modificaciones posteriores al Estatuto Tributario base** — el Acuerdo 012/2021 ya portado es solo la norma base; existen 4 acuerdos que la modifican después y **no están incorporados** al texto portado:
  - Acuerdo Municipal No 007 de 2024
  - Acuerdo Municipal 042 de 2024
  - Acuerdo Municipal 047 de 2024
  - Acuerdo Municipal No 025 de 2025
  Búsqueda: https://www.floridablanca.gov.co/documentos/buscar/?q=estatuto+tributario
- **Plazos del Impuesto Predial y descuentos por pronto pago 2026** — no localizados en este pase; probablemente exista un acto administrativo propio para Predial, separado de la Resolución 6059/2025 (que cubre los demás impuestos) y no explícito en el Acuerdo 012/2021 base (sí tiene un "Incentivo Fiscal para el Pago" para ICA en el Artículo 113, pero el porcentaje de descuento lo fija un acuerdo anual aparte que no se localizó). Buscar en https://www.floridablanca.gov.co/documentos/buscar/?q=predial

## 🟡 Existe pero es un documento grande / de bajo uso ciudadano directo
- **Plan de Desarrollo Municipal "Floridablanca en Orden 2024-2027"** — confirmado que existe con ese nombre oficial. Los documentos encontrados son informes de seguimiento/gestión, uno de 188 MB (demasiado grande para ingestar tal cual) y uno de 0.77 MB ("Informe seguimiento Plan de Desarrollo"). Antes de traer esto habría que decidir si se resume (como hace la skill `resumidor-documentos` de OpenClaw) en vez de ingestar el PDF completo.
  Búsqueda: https://www.floridablanca.gov.co/documentos/buscar/?q=plan+de+desarrollo
- **Manual de funciones** — existe como categoría de documentos internos de Gestión Humana (`https://www.floridablanca.gov.co/documentos/264/gestion-humana/`), pero es un manual de cargos/perfiles para funcionarios, no información que un ciudadano típico consulte por el chat. Se deja de baja prioridad a propósito.

## ❌ Confirmado que NO existe (no es que falte buscar, ya se buscó)
- **Matrícula/cupos escolares (K-12)** — se buscó explícitamente en el buscador de trámites del sitio. El único resultado para "matrícula" es *"Inscripción y matrícula a programas de trabajo y desarrollo humano"* (educación continuada para adultos), no matrícula escolar regular. Confirma lo que ya decía `tramites_educacion.md`: no inventar este trámite, seguir remitiendo a la institución educativa o a la Secretaría de Educación. (`predetermined_answers.json` ya tiene una respuesta fija para esto: `educacion_matricula`.)

## Sigue pendiente sin verificar (no se investigó en este pase)
- Contenido oficial detallado (guion tipo "flujo_*.md") para los submenús "Trámites y Servicios" (general), "Transparencia" y "Participación Ciudadana" — hoy solo tienen el enlace de la web en `predetermined_answers.json`. El sitio sí tiene contenido real bajo Transparencia (Ley 1712, ITA) y Participación (`/1168`); si se quiere un guion más trabajado para esas dos opciones del menú, valdría la pena portarlo igual que se hizo con Predial/PQRSD.
- Programas sociales adicionales y normativa propia de Interior/Planeación/Salud (POT, etc.) — no se buscó en este pase.

Cuando se resuelva alguno de estos: agregar el archivo en la subcarpeta de
`knowledge/` que corresponda y subirlo al bucket — la ingesta al File Search
Store queda automática (Eventarc) o se puede forzar con `scripts/sync_tenant_kb.py`.
