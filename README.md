# QR Creator (FastAPI + Next.js)

Backend en FastAPI que genera códigos QR (PNG/SVG) y frontend en Next.js 16 + Tailwind para usarlos con un UI moderno.

## Requisitos
- Python 3.10+
- Node.js 18+ y npm

## Backend (FastAPI)
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # en Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Health check: `http://localhost:8000/healthz`  
API docs (OpenAPI): `http://localhost:8000/docs` o `http://localhost:8000/redoc`

Endpoint QR: `http://localhost:8000/api/qr?data=hola&format=png`

Parámetros del endpoint:
- `format`: `png` | `svg` (SVG admite colores; dots solo en PNG)
- `error_correction`: `L` | `M` | `Q` | `H`
- `box_size`: tamaño de módulo (1-32)
- `border`: borde en módulos (0-10)
- `fill_color` / `back_color`: colores en hex (`#ff0000`, `#f00`, etc.)
- `style`: `square` | `dots` (punteado solo PNG)

Rate limit (in-memory por proceso):
- Env `QR_RATE_LIMIT` (peticiones, por defecto 60)
- Env `QR_RATE_WINDOW` (segundos, por defecto 60)
- Para desactivar: `QR_RATE_LIMIT=0`

API key opcional:
- Si defines `QR_API_KEY`, el backend exige el header `X-API-Key` con ese valor.
- El frontend enviará `X-API-Key` si defines `NEXT_PUBLIC_API_KEY` (debe coincidir con la del backend).

Variables de entorno (ejemplos):
- `.env.example` en la raíz (backend): `QR_API_KEY`, `QR_RATE_LIMIT`, `QR_RATE_WINDOW`, `NEXT_PUBLIC_API_BASE`.
- `frontend/.env.local.example` (frontend): `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_API_KEY` (opcional; se envía como `X-API-Key`).

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

## UX rápida
- Selector de formato PNG/SVG; estilo punteado se desactiva en SVG.
- Colores QR y fondo aplican en ambos formatos (en PNG y SVG).
- Swatches rápidos de color y pickers; descarga con botón e ícono.

## Estructura
- `app/` FastAPI y rutas (`/api/qr`)
- `frontend/` Next.js + Tailwind (UI moderna)

## Capturas (ejemplo)
- Pantalla principal: muestra formulario con opciones de formato, corrección, colores y preview animada.
- Botón de descarga: botón con ícono para descargar el QR generado.

_(Adjunta tus propias capturas tras ejecutar `npm run dev` y `uvicorn app.main:app --reload`)._
