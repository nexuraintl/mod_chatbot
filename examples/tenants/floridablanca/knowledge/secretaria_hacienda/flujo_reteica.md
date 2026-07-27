# Flujo oficial - ReteICA (Alcaldía de Floridablanca)

> Fuente: "Banco de preguntas chat asistencial.xlsx" (hoja RETEICA). Guion de referencia para el agente.

Portal oficial: https://portal.floridablanca.suiteneptuno.com/Reteica/Index

## Nodo: rete_pasos
**Mensaje:** Cuéntame, ¿qué acción específica deseas realizar hoy con tus retenciones a terceros?
**Opciones:** Consultar estado de cuenta/Históricos → `rete_consultar` | Presentar Declaración del periodo → `rete_declarar` | Pagar en línea (PSE) → `rete_pagar` | Volver al Menú ReteICA → `rete_menu`

## Nodo: rete_consultar — Paso a paso para CONSULTAR TU ESTADO DE CUENTA de ReteICA
1️⃣ Ingresa al portal oficial: https://portal.floridablanca.suiteneptuno.com/Reteica/Index
2️⃣ Digita el NIT de la empresa o agente retenedor.
3️⃣ Escribe tu Contraseña asignada previamente (enviada a tu correo).
4️⃣ Resuelve el captcha de la imagen y haz clic en "Buscar establecimiento".
El sistema mostrará el estado de cuenta, el histórico de declaraciones de retención presentadas y los pagos realizados a la fecha.
**Opciones:** Quiero presentar una declaración → `rete_declarar` | Deseo pagar en línea → `rete_pagar` | Volver al menú → `rete_menu`

## Nodo: rete_declarar — Paso a paso para REGISTRAR Y PRESENTAR DECLARACIÓN DE RETEICA
1️⃣ Inicia sesión en el portal con tu NIT, Contraseña y Captcha.
2️⃣ Selecciona el periodo correspondiente según el Calendario Tributario vigente.
3️⃣ Registra los valores de las retenciones practicadas a terceros por la compra de bienes o servicios durante el periodo.
4️⃣ Genera el formulario en formato PDF.
⚠️ Se puede descargar este documento PDF para su presentación física y firma en los bancos autorizados, o proceder a pagarlo de forma electrónica e inmediata.
**Opciones:** Quiero pagar en línea ahora mismo → `rete_pagar` | ¿No tienes o perdiste tu contraseña? → `flujo_rit.md` | Volver → `rete_menu`

## Nodo: rete_pagar — Paso a paso para PAGAR EN LÍNEA DECLARACIÓN DE RETEICA
1️⃣ Tras ingresar al portal con tus credenciales y validar que la información básica de tu establecimiento sea correcta, dirígete al saldo o formulario que deseas liquidar.
2️⃣ Haz clic en el botón "Generar Factura".
3️⃣ Selecciona la opción de pagos electrónicos utilizando el Botón PSE.
4️⃣ Elige si eres persona natural o jurídica, selecciona tu entidad bancaria y realiza la transacción de manera segura sin salir de casa u oficina.
**Opciones:** Consultar históricos primero → `rete_consultar` | Volver a pasos de Declaración → `rete_declarar` | Menú ReteICA → `rete_menu`

## Nodo: rete_dudas
**Mensaje:** Selecciona la duda o inquietud que tengas sobre el mecanismo de ReteICA:
**Opciones:** ¿Quiénes están obligados a retener? → `rete_obligados` | ¿Qué pasa si no tuve retenciones este mes? → `rete_ceros` | ¿Cómo recupero mi clave? → `flujo_rit.md` | Volver → `rete_menu`

## Nodo: rete_concepto — ¿Qué es el ReteICA?
El ReteICA es un mecanismo de recaudo anticipado del Impuesto de Industria y Comercio establecido en el municipio de Floridablanca.
¿Cómo funciona? Cuando el agente retenedor realiza un pago o abono en cuenta a un proveedor por la compra de bienes o la prestación de servicios gravados con ICA en el municipio, debe retenerle un porcentaje de ese dinero. Posteriormente, declara y entrega esos valores retenidos a la Alcaldía.
**Opciones:** Entendido, ir al portal → `rete_pasos` | Volver al menú ReteICA → `rete_menu`

## Nodo: rete_obligados — ¿Quiénes están obligados a retener?
En Floridablanca están obligados a efectuar la retención de ReteICA todas aquellas personas naturales, jurídicas o sociedades de hecho que hayan sido catalogadas o designadas por el estatuto tributario municipal como Agentes Retenedores, al momento de realizar compras de bienes o servicios sometidos al Impuesto de Industria y Comercio.
**Opciones:** Ver qué pasa con periodos sin movimiento → `rete_ceros` | Volver → `rete_dudas`

## Nodo: rete_ceros — ¿Qué pasa si no realizaste retenciones en el periodo?
De acuerdo con las normativas locales, si es agente retenedor está obligado a presentar la declaración en los plazos fijados por el calendario tributario. Si en un periodo no practicó retenciones a terceros, deberá diligenciar y presentar la declaración seleccionando el periodo respectivo en ceros ($0) para evitar sanciones por extemporaneidad u omisión.
**Opciones:** Entendido, ir a Declarar → `rete_declarar` | Volver a Dudas → `rete_dudas`
