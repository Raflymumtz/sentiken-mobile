import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter sliding-window sederhana berbasis in-memory per IP.

    Cocok untuk deployment single-instance (development/skala kecil sesuai
    kebutuhan penelitian ini). Untuk multi-instance produksi, ganti dengan
    backend Redis (misal token bucket) agar counter dibagi antar proses.
    """

    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.limit = requests_per_minute or settings.rate_limit_per_minute
        self.window_seconds = 60
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = self._hits[client_ip]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Terlalu banyak permintaan. Silakan coba lagi sebentar lagi.",
                    }
                },
            )

        hits.append(now)
        return await call_next(request)
