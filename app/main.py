from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routers.qr import router as qr_router

app = FastAPI(title="QR Creator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Rate limiting (in-memory, por proceso)
RATE_LIMIT = int(os.getenv("QR_RATE_LIMIT", "60"))  # peticiones
RATE_WINDOW = int(os.getenv("QR_RATE_WINDOW", "60"))  # segundos
_buckets: dict[str, deque[float]] = defaultdict(deque)
_bucket_lock = asyncio.Lock()


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    # Solo se limita /api; si RATE_LIMIT es 0 o negativo, se desactiva.
    if RATE_LIMIT <= 0 or not request.url.path.startswith("/api"):
        return await call_next(request)

    now = time.monotonic()
    client_ip = request.client.host if request.client else "anonymous"

    async with _bucket_lock:
        bucket = _buckets[client_ip]
        # Limpia timestamps fuera de ventana
        cutoff = now - RATE_WINDOW
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail=f"Demasiadas peticiones: límite {RATE_LIMIT} cada {RATE_WINDOW}s",
            )
        bucket.append(now)

    return await call_next(request)

app.include_router(qr_router, prefix="/api")


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict[str, str]:
    return {"status": "ok"}
