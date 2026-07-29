import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.rate_limit import RateLimitMiddleware

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="SENTIKEN Mobile API",
    description=(
        "API backend untuk pengumpulan dan analisis sentimen ulasan pengguna "
        "aplikasi PLN Mobile dan MyPertamina dari Google Play Store."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_origins_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

register_exception_handlers(app)

app.include_router(api_router)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "environment": settings.environment}


@app.get("/", tags=["System"])
def root():
    return {"name": "SENTIKEN Mobile API", "docs": "/docs"}
