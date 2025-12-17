# QR Creator (FastAPI + Next.js)

Backend en FastAPI que genera codigos QR (PNG/SVG) y frontend en Next.js 16 + Tailwind con una UI moderna y controles visuales avanzados.

## Requisitos
- Python 3.10+
- Node.js 18+ y npm

## Backend (FastAPI)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Health check: `http://localhost:8000/healthz`  
API docs: `http://localhost:8000/docs` (ReDoc) y `http://localhost:8000/swagger` (Swagger UI)

Endpoint QR (solo POST JSON): `http://localhost:8000/api/qr`

Parametros del endpoint (body JSON; requiere `qrcode>=8.2.0`):
- `data` (obligatorio): texto o URL a codificar.
- `format`: `png` | `svg` (en SVG se fuerza estilo cuadrado, ojos auto y color solido; estilos solo en PNG).
- `error_correction`: `L` | `M` | `Q` | `H`
- `box_size`: tamano de modulo (1-32)
- `border`: borde en modulos (0-10)
- `fill_color` / `back_color`: colores en hex (`#ff0000`, `#f00`, etc.)
- `fill_mode`: `solid` | `gradient` (solo PNG; usa `fill_color_to` para el destino)
- `fill_color_to`: color destino del degradado vertical (solo si `fill_mode=gradient`)
- `style`: `square` | `dots` | `rounded` | `gapped` | `bars-vertical` | `bars-horizontal` (no aplican en SVG)
- `eye_style`: `square` | `rounded` | `dots` | `gapped` | `bars-vertical` | `bars-horizontal` (solo PNG)
- `eye_color`: color de los localizadores (solo PNG)

Ejemplo `curl` (PNG solido):
```bash
curl -X POST http://localhost:8000/api/qr \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <tu_clave_si_se_requiere>" \
  -o qr.png \
  -d '{
    "data": "Hola mundo",
    "format": "png",
    "error_correction": "M",
    "box_size": 10,
    "border": 4,
    "fill_color": "#7c3aed",
    "back_color": "#0b0f1a",
    "style": "gapped",
    "eye_style": "square",
    "eye_color": "#38bdf8",
    "fill_mode": "solid"
  }'
```

Rate limit (en memoria por proceso):
- Env `QR_RATE_LIMIT` (peticiones, por defecto 60)
- Env `QR_RATE_WINDOW` (segundos, por defecto 60)
- Para desactivar: `QR_RATE_LIMIT=0`

API key opcional:
- Si defines `QR_API_KEY`, el backend exige el header `X-API-Key` con ese valor.
- El frontend envia `X-API-Key` si defines `NEXT_PUBLIC_API_KEY` (debe coincidir con la del backend).

Variables de entorno (ejemplos):
- `.env.example` (backend): `QR_API_KEY`, `QR_RATE_LIMIT`, `QR_RATE_WINDOW`, `NEXT_PUBLIC_API_BASE`.
- `frontend/.env.local.example` (frontend): `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_API_KEY` (opcional).

## Frontend (Next.js 16.0.10 + Tailwind)
En otra terminal:
```bash
cd frontend
npm install
npm run dev
```
Abre `http://localhost:3000`. Por defecto consume `http://localhost:8000`. Si cambias el backend:
```bash
setx NEXT_PUBLIC_API_BASE "http://localhost:8001"
npm run dev
```

## UX rapida (estado actual)
- Diseno en 3 columnas: configuracion basica, colores/fondo y previsualizacion.
- Validacion: texto/URL obligatorio antes de generar.
- Estilos del cuerpo: square, dots, rounded, gapped, barras verticales/horizontales (PNG).
- Localizadores: mismos estilos disponibles y color independiente.
- Cuerpo: color solido o degradado vertical con 8 swatches (frio -> calido) y pickers.
- Fondo: paleta rapida y picker; default oscuro (#0b0f1a).
- Boton de generar junto a la previsualizacion; descarga desde la tarjeta de resultado.
- Fondo animado tipo aurora con textura sutil.

## Estructura
- `app/` FastAPI y rutas (`/api/qr`)
- `frontend/` Next.js + Tailwind (UI)
