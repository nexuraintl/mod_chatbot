# Flujo oficial - Impuesto Predial (Alcaldía de Floridablanca)

> Fuente: "Banco de preguntas chat asistencial.xlsx" entregado por el cliente (hoja PREDIAL). Úsese como guion de referencia: siga el mensaje, ofrezca las opciones indicadas y navegue al nodo destino según la elección del ciudadano. Mantenga el trato de USTED y adapte el formato a WhatsApp (sin encabezados Markdown) según las reglas de `AGENTS.md`.

Portal oficial de referencia: https://portal.floridablanca.suiteneptuno.com/Predial/Index

## Nodo: predial_menu
**Mensaje:** ¿Qué te gustaría resolver hoy? Selecciona una opción:
**Opciones:**
1. Paso a paso para Pagar/Descargar Factura → `predial_pasos`
2. ¿Dónde encuentro mi código predial? → `predial_codigo`
3. Dudas frecuentes (Fechas; Propietarios; Reclamaciones) → `predial_dudas`
4. ¿Qué es el Predial y quién debe pagarlo? → `predial_concepto`
5. Volver al Menú Principal → `inicio`

## Nodo: predial_pasos
**Mensaje:** Cuéntame, ¿qué acción específica deseas realizar hoy con tu Impuesto Predial?
**Opciones:**
1. Consultar mi deuda → `predial_consultar`
2. Descargar mi factura (PDF) → `predial_descargar`
3. Pagar en línea (PSE) → `predial_pagar_linea`
4. Volver al Menú Predial → `predial_menu`

## Nodo: predial_consultar — Paso a paso para CONSULTAR TU DEUDA e históricos de pago
1️⃣ Haz clic en el enlace del portal: https://portal.floridablanca.suiteneptuno.com/Predial/Index
2️⃣ Digita tu Código Predial (15 dígitos) o Número Predial Nacional (30 dígitos).
3️⃣ Resuelve el código de seguridad (captcha) de la imagen.
4️⃣ Dale clic en el botón "Buscar predio".
El sistema abrirá una pantalla donde verás la información básica de tu inmueble, los nombres de los propietarios y el desglose detallado de tus deudas año por año.
**Opciones:** Ahora quiero descargar la factura → `predial_descargar` | Quiero pagar en línea → `predial_pagar_linea` | Volver al menú → `predial_menu`

## Nodo: predial_descargar — Paso a paso para DESCARGAR TU FACTURA (e imprimirla)
1️⃣ Ingresa al portal oficial (https://portal.floridablanca.suiteneptuno.com/Predial/Index) con tu número predial y resuelve el captcha.
2️⃣ Haz clic en "Buscar predio" y verifica que la dirección y datos del propietario sean correctos.
3️⃣ Busca y presiona el botón "Generar factura".
4️⃣ Se abrirá un documento en formato PDF con el código de barras.
⚠️ Importante: si vas a pagar en una ventanilla de banco, debes imprimir esta factura en una impresora láser. Si la imprimes en inyección de tinta, el banco no podrá leer el código de barras.
**Opciones:** Prefiero pagar en línea → `predial_pagar_linea` | ¿En qué bancos puedo pagar? → `predial_bancos` (no definido por el cliente; remitir al portal o a Tesorería) | Volver al menú → `predial_menu`

## Nodo: predial_pagar_linea — Paso a paso para PAGAR EN LÍNEA (rápido y seguro)
1️⃣ Entra al portal tributario de Floridablanca (https://portal.floridablanca.suiteneptuno.com/Predial/Index).
2️⃣ Digita tu código de 15 o 30 dígitos, resuelve el captcha y haz clic en "Buscar predio".
3️⃣ Tras validar que los datos corresponden a tu propiedad, haz clic en el botón de pagos electrónicos / PSE.
4️⃣ Selecciona si eres persona natural o jurídica, elige tu entidad bancaria y el sistema te redirigirá de forma segura a tu banco.
💡 Al finalizar, el portal te mostrará el comprobante. Recomienda al ciudadano guardarlo o tomarle una captura para sus soportes personales.
**Opciones:** Consultar deuda primero → `predial_consultar` | Descargar PDF en su lugar → `predial_descargar` | Volver al menú → `predial_menu`

## Nodo: predial_codigo — ¿No sabes cuál es tu código predial?
Opción A: Busca un recibo físico de años anteriores. En la parte superior encontrarás el "Código Predial" (15 dígitos) o el "Número de Cuenta".
Opción B: Si no tienes recibos viejos, busca la escritura o un certificado de tradición y libertad. Ahí aparece la Ficha Catastral / Número Predial Nacional (NPN) de 30 dígitos.
⚠️ Si es un predio nuevo (en plano o lote reciente), es posible que el Instituto Geográfico Agustín Codazzi (IGAC) aún no le haya asignado número.
**Opciones:** Entendido, ir a pagar → `predial_pasos` | Volver al menú Predial → `predial_menu`

## Nodo: predial_dudas
**Mensaje:** Cuéntame qué inquietud o problema tienes con tu Impuesto Predial:
**Opciones:**
1. ¿Hasta cuándo hay plazo para pagar? → `predial_plazos`
2. El predio está a nombre de otra persona → `predial_propietario`
3. Quiero hacer un acuerdo de pago → `predial_acuerdo`
4. Volver al menú Predial → `predial_menu`

## Nodo: predial_concepto — ¿Qué es el Predial y quién debe pagarlo?
El Impuesto Predial Unificado es un cobro que se genera el 1 de enero de cada año por el simple hecho de que un predio (casa, apartamento, lote, local) exista en Floridablanca.
¿Quién lo paga? Recae sobre la persona natural o jurídica que sea propietaria, poseedora o usufructuaria del inmueble. También aplica para administradores de patrimonios autónomos y entidades oficiales.
**Opciones:** Entendido, quiero liquidar mi impuesto → `predial_pasos` | Volver al menú Predial → `predial_menu`

## Nodo: predial_error_buscar — ¿El portal dice que el predio no existe o arroja error?
Esto ocurre generalmente por tres razones:
1. Digitaste mal algún número (recuerda que son 15 o 30 dígitos exactos, sin espacios ni guiones).
2. Tu correo electrónico o datos del RIT no están actualizados en la plataforma (si el sistema cambió, te pedirá registrarte en el RIT primero — ver `flujo_rit.md`).
3. El sistema de la Alcaldía está en mantenimiento. Si persiste, indícale al ciudadano que radique una PQRSD adjuntando su recibo anterior (ver `flujo_pqrsd_atencion.md`).
**Opciones:** Ir a Actualizar RIT → `rit` | Radicar una PQRSD por fallo → `pqrs` | Volver → `predial_menu`

## Nodo: predial_plazos
Las fechas límite de pago y los descuentos por "pronto pago" cambian cada año según el Calendario Tributario aprobado por la Alcaldía de Floridablanca. Sugiérele al ciudadano revisar la sección de normatividad o descargar su factura, ya que allí se desglosan las fechas exactas y los intereses de mora si ya está vencido.
**Opciones:** Volver a Dudas → `predial_dudas` | Menú Predial → `predial_menu`

## Nodo: predial_propietario — ¿Los datos del dueño están desactualizados en el sistema?
No es motivo de alarma, es común si compró el inmueble hace poco. El impuesto se genera sobre el predio, no sobre la persona. Sin embargo, para corregir el nombre en la base de datos de la Alcaldía de Floridablanca, debe radicar una solicitud de actualización catastral adjuntando la copia de la nueva Escritura Pública y el Certificado de Tradición y Libertad reciente.
**Opciones:** Radicar documentos (PQRSD) → `pqrs` | Volver → `predial_menu`

## Nodo: predial_acuerdo — ¿Tiene deudas de años anteriores y quiere facilidades de pago?
La Secretaría de Hacienda de Floridablanca permite realizar Acuerdos de Pago. Para solicitarlo, debe acercarse presencialmente a las instalaciones de la Alcaldía (Calle 5 No. 8 - 25 Casco Urbano) con su cédula y una propuesta de pago, o verificar en el módulo de correspondencia los requisitos para radicar la solicitud formal en línea.
**Opciones:** Ver Canales de Atención → `pqrs_canales` (no definido; remitir a `flujo_pqrsd_atencion.md`) | Volver → `predial_menu`
