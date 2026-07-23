# Flujo oficial - Industria y Comercio (ICA) (Alcaldía de Floridablanca)

> Fuente: "Banco de preguntas chat asistencial.xlsx" (hoja ICA). Guion de referencia para el agente — seguir el mensaje y opciones, navegar al nodo destino según la elección del ciudadano.

Portal oficial: https://portal.floridablanca.suiteneptuno.com/IndustriaComercio/Index
(Nota: este es el enlace correcto y limpio del módulo de Industria y Comercio; reemplaza cualquier enlace anterior con `moduloId` hash.)

## Nodo: ica_pasos
**Mensaje:** Cuéntame, ¿qué acción específica deseas realizar hoy con tu impuesto ICA o Autorretenciones?
**Opciones:**
1. Consultar estado de cuenta → `ica_consultar`
2. Registrar Declaración → `ica_declarar`
3. Pagar en línea (PSE) → `ica_pagar`
4. Volver al Menú ICA → `ica_menu`

## Nodo: ica_consultar — Paso a paso para CONSULTAR TU ESTADO DE CUENTA de ICA
1️⃣ Ingresa al portal oficial: https://portal.floridablanca.suiteneptuno.com/IndustriaComercio/Index
2️⃣ Digita el NIT de la empresa o persona natural registrada.
3️⃣ Escribe tu Contraseña RIT asignada.
4️⃣ Resuelve el captcha de la imagen y haz clic en "Buscar establecimiento".
Allí verás el histórico de tus declaraciones presentadas, tus pagos anteriores y si tienes saldos pendientes por liquidar.
**Opciones:** Quiero registrar una declaración → `ica_declarar` | Deseo pagar en línea → `ica_pagar` | Volver al menú → `ica_menu`

## Nodo: ica_declarar — Paso a paso para REGISTRAR TU DECLARACIÓN WEB
1️⃣ Inicia sesión en el portal con tu NIT y Contraseña RIT.
2️⃣ Selecciona la vigencia o periodo a declarar según el Calendario Tributario.
3️⃣ Diligencia los ingresos de tu actividad y el sistema liquidará el impuesto de forma automática.
4️⃣ Genera el formulario en PDF.
⚠️ Puedes imprimir este PDF para presentarlo y firmarlo físicamente en las entidades bancarias autorizadas, o proceder directamente al pago virtual.
**Opciones:** Quiero pagar esta declaración en línea → `ica_pagar` | ¿No tienes contraseña RIT? → `flujo_rit.md` | Volver → `ica_menu`

## Nodo: ica_pagar — Paso a paso para PAGAR EN LÍNEA (ICA y Avisos/Complementarios)
1️⃣ Tras buscar tu establecimiento e iniciar sesión con tu clave RIT, valida que los datos que muestra la pantalla sean correctos.
2️⃣ Si tienes una declaración web lista o un saldo pendiente, dale clic al botón "Generar Factura".
3️⃣ Elige la opción de pagos electrónicos (Botón PSE).
4️⃣ Selecciona tu banco, ingresa tus credenciales financieras de forma segura y efectúa el pago sin filas.
**Opciones:** Consultar deudas primero → `ica_consultar` | Olvidé mi contraseña RIT → `flujo_rit.md` | Volver → `ica_menu`

## Nodo: ica_pre — ¿Aún no estás registrado como contribuyente de ICA?
Si iniciaste una actividad comercial en Floridablanca y necesitas reportarlo por primera vez, dirígete al Pre-Registro virtual en el portal ingresando toda la información de tu negocio. Una vez aprobado, quedarás habilitado en el sistema.
**Opciones:** Entendido, ir al Pre-Registro → `ica_pre_enlace` | Volver al menú ICA → `ica_menu`

## Nodo: ica_pre_enlace
Puedes iniciar tu Pre-Registro ingresando tus datos en: https://portal.floridablanca.suiteneptuno.com/IndustriaComercio/Index
Recuerda tener a la mano el RUT de la DIAN y los datos de tu establecimiento.

## Nodo: ica_dudas
**Mensaje:** Selecciona la duda o inquietud que tengas sobre el impuesto de Industria y Comercio:
**Opciones:** ¿Cómo se clasifican los contribuyentes? → `ica_clasificacion` | ¿Qué actividades están gravadas? → `ica_actividades` | ¿Qué hago si olvidé mi contraseña? → `flujo_rit.md` | Volver → `ica_menu`

## Nodo: ica_concepto — ¿Qué es el ICA?
El Impuesto de Industria y Comercio (ICA) es un gravamen municipal obligatorio. Se genera por realizar de forma directa o indirecta cualquier actividad industrial, comercial o de servicios en Floridablanca, ya sea de forma permanente u ocasional, con o sin un local físico.
¿Quiénes deben declarar? Las personas naturales, jurídicas o sociedades de hecho que ejecuten estas actividades en la jurisdicción del municipio.
**Opciones:** Entendido, quiero ingresar al portal → `ica_pasos` | Volver → `ica_menu`

## Nodo: ica_clasificacion
Los contribuyentes del Impuesto de Industria y Comercio en Floridablanca se clasifican legalmente en dos grupos según el volumen de sus ingresos y condiciones:
🔹 Régimen Simplificado
🔹 Régimen Común
**Opciones:** Ver actividades gravadas → `ica_actividades` | Volver a Dudas → `ica_dudas`

## Nodo: ica_actividades — Tipos de actividades gravadas con ICA
- **Actividad Industrial:** Producción, extracción, fabricación, manufactura o cualquier proceso de transformación de bienes.
- **Actividad Comercial:** Expendio, compraventa o distribución de bienes y mercancías al por mayor o al por menor.
- **Actividad de Servicios:** Labores o trabajos ejecutados sin relación laboral que generen una contraprestación en dinero o especie (predomine el factor intelectual o material).
**Opciones:** Entendido, ir a Declarar → `ica_declarar` | Volver a Dudas → `ica_dudas`
