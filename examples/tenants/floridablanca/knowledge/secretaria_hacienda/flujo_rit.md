# Flujo oficial - RIT (Registro de Información Tributaria) (Alcaldía de Floridablanca)

> Fuente: "Banco de preguntas chat asistencial.xlsx" (hoja RIT). Trámite que no existía en el knowbase previo — se cubre exclusivamente la CANCELACIÓN/INACTIVACIÓN del RIT por cese de actividades. Para registro/pre-registro inicial del RIT (contribuyente nuevo de ICA), ver `flujo_ica.md` (nodo `ica_pre`).

Portal de radicación: https://portal.floridablanca.suiteneptuno.com/Correspondencia/Index

## Nodo: rit_inactivar
**Mensaje:** ¿Cerraste tu negocio o dejaste de prestar servicios en Floridablanca? Para evitar que la Alcaldía te siga cobrando impuestos, debes tramitar la Cancelación del RIT por Cese de Actividades. Cuéntame qué deseas hacer:
**Opciones:**
1. Ver requisitos y documentos → `rit_cancelar_req`
2. Paso a paso para tramitarlo → `rit_cancelar_pasos`
3. Dudas (¿Qué pasa si tengo deudas?) → `rit_cancelar_dudas`
4. Volver al menú RIT → `rit_menu`

## Nodo: rit_cancelar_req — Documentos obligatorios para cancelar o inactivar tu RIT
1️⃣ **Formulario Oficial:** Formulario de cese de actividades diligenciado y firmado por el contribuyente o representante legal.
2️⃣ **Cámara de Comercio:** Certificado de Cámara de Comercio vigente donde conste la cancelación definitiva del establecimiento (si aplica).
3️⃣ **Documento de Identidad:** Fotocopia de la cédula del propietario o del representante legal.
4️⃣ **Soportes de pago:** Copia de la última declaración del Impuesto de Industria y Comercio (ICA) pagada hasta la fecha del cierre.
**Opciones:** Ver el paso a paso para radicar → `rit_cancelar_pasos` | Volver → `rit_inactivar`

## Nodo: rit_cancelar_pasos — Paso a paso para radicar la cancelación de tu RIT
1️⃣ Ponte al día: liquida y paga el impuesto ICA proporcional a los meses que operaste en el año actual.
2️⃣ Reúne los papeles: junta los documentos indicados en la sección de requisitos.
3️⃣ Elige cómo radicar:
   - **Virtual:** Ingresa al módulo de Correspondencia PQRSD (https://portal.floridablanca.suiteneptuno.com/Correspondencia/Index), llena tus datos y sube los documentos en formato PDF.
   - **Presencial:** Lleva la carpeta con los documentos al primer piso del Palacio Municipal (Calle 5 No. 8 - 25 Casco Urbano).
La Secretaría de Hacienda revisará que todo esté en orden y procederá a inactivar la cuenta.
**Opciones:** Ir a radicar virtual (PQRSD) → `flujo_pqrsd_atencion.md` (nodo `pqrs_rad_pasos`) | Volver → `rit_inactivar`

## Nodo: rit_cancelar_dudas — Respuestas a dudas sobre la cancelación del RIT
**¿Puedo cancelar el RIT si tengo deudas de años anteriores?**
No, el sistema requiere que esté completamente al día con sus obligaciones tributarias (ICA y Avisos) para aceptar el trámite de cese de actividades.

**¿Qué pasa si cerré el negocio y nunca avisé a la Alcaldía?**
La Alcaldía asume que sigue operando y le seguirá generando cobros y posibles sanciones por no declarar. Es vital radicar el cese de actividades adjuntando la fecha exacta del cierre en Cámara de Comercio para frenar los cobros.
**Opciones:** Ver opciones de acuerdos de pago → `predial_acuerdo` (ver `flujo_predial.md`) | Volver → `rit_inactivar`
