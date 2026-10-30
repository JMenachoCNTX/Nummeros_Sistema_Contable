# Nummeros_Sistema_Contable — guía para Claude

## Para qué sirve
Sistema contable web de CONTAX para llevar la contabilidad de varias empresas cliente (se elige la empresa
activa / por NIT). Módulos (pestañas): Dashboard, Comprobantes, Plan de cuentas, Apertura, Estados financieros
(EE), Notas, Reporte, Gráficos, CxC, CxP, Ingresos, RCV, Nómina, Cuadro de activos fijos y vida útil, UFVs,
Tributario, Compensaciones, Verificaciones, NITs, Historial, Usuarios, Configuración, IA (API) y
**Lista EEFF** (lee los Estados Financieros recibidos en el panel NUMMEROS).

## Para qué empresa
- **CONTAX** (estudio contable), para trabajar las empresas de sus clientes.
- Con la marca **NUMMEROS by CONTAX** desde la V3.37.

## Cómo está armado (archivos principales)
- `index.html` — el sistema VIGENTE, un solo archivo grande (~800 KB). Versión en la constante `VERSION`
  (ej. `'V3.39'`), cerca de la línea 350.
- `CONTAX_v2_V31.html` — **copia antigua** (título "CONTAX Sistema Contable v2", subida el 07/07/2026, sin
  Firebase, solo guardaba en el navegador, logos en base64). No se publica como página principal; no editarla.
- `marca/` — logos, íconos, fuentes, colores (`nummeros-tokens.css`) y fotos "clásicos".
- `CNAME` — dominio propio. `README.md` casi vacío.

## Dónde se guardan los datos
- **Firebase Firestore** (proyecto `sistema-contable-contax`), con ingreso anónimo de Firebase:
  - `contax/{id}` — datos de cada empresa.
  - `contax_config/acceso` y `global` — usuarios autorizados (correo + PIN + rol), permisos, plan de cuentas,
    UFV, NITs, Lista EEFF, URL de Google Sheet y llaves de IA.
  - `contax_config/empresas`, `contax_config/panel` (llave del puente del panel), `contax_presence`.
- **localStorage** del navegador (claves `cx_*`, `contax_v2`) como copia local.
- **Apps Script del panel NUMMEROS** (`PANEL_PUENTE`) para la Lista EEFF; ese código no está aquí.
- IA: llama directo desde el navegador a Anthropic, OpenAI o Gemini con la llave configurada.

## Cómo se publica
- GitHub Pages desde `main`, dominio **sistema.contaxbolivia.com** (archivo `CNAME`).
- No hay `firestore.rules` en el repo: las reglas se manejan solo en la consola de Firebase.
- Commits recientes: `V3.xx — descripción`; antes muchos "Update index.html" subidos desde la web de GitHub.

## Cuidados importantes
- El repositorio es **PÚBLICO**: no subir PIN, llaves de IA, llave del panel ni datos de clientes.
- Hay mejoras de seguridad pendientes en el ingreso y en las reglas de Firestore (Jhonny tiene el detalle
  aparte). Revisar las reglas en la consola antes de agregar datos sensibles.
- La configuración web de Firebase (apiKey) es pública por diseño.
- Al cambiar `index.html`, subir `VERSION`. No confundir con `CONTAX_v2_V31.html`.
