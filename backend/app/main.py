from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import Database
from app.cache import CacheService
from app.routes.auth import router as auth_router
from app.routes.upload import router as upload_router
from app.routes.players import router as players_router
from app.routes.seasons import admin_router as seasons_admin_router, public_router as seasons_public_router
from app.routes.player_classification import admin_router as player_classification_admin_router, public_router as player_classification_public_router
from app.routes.verified_deaths import router as verified_deaths_router
from app.routes.final_kvk import router as final_kvk_router
from app.routes.fight_periods import admin_router as fight_periods_admin_router, public_router as fight_periods_public_router
from app.routes.health import router as health_router
from app.middleware.metrics import performance_metrics_middleware

# Initialize Sentry error monitoring (optional)
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
        ],
        traces_sample_rate=0.1,  # 10% of requests for performance monitoring
        environment=settings.environment,
        release=settings.app_version,
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.sentry_dsn:
    logger.info("✅ Sentry error monitoring enabled")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting KvK Tracker...")
    await Database.connect_db()
    await CacheService.connect()
    yield
    logger.info("🛑 Shutting down...")
    await Database.close_db()
    await CacheService.disconnect()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for tracking Rise of Kingdoms KvK statistics",
    lifespan=lifespan
)

# CORS Configuration - Load from settings
# Development: Uses localhost origins
# Production: Must explicitly set CORS_ORIGINS in .env
allowed_origins = settings.cors_origins if settings.cors_origins else [
    "https://kd-3584.vercel.app",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

# Only allow wildcard in debug mode
if settings.debug and "*" not in allowed_origins:
    logger.warning("⚠️  Debug mode enabled - Adding wildcard CORS")
    allowed_origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# Add performance metrics middleware
app.middleware("http")(performance_metrics_middleware)

logger.info(f"✅ CORS enabled for origins: {allowed_origins}")

# Include health check routes (before other routes for priority)
app.include_router(health_router)

app.include_router(auth_router)

app.include_router(upload_router)

app.include_router(players_router)

# Season routes - both public and admin
app.include_router(seasons_public_router)
app.include_router(seasons_admin_router)

# Player classification routes - both public and admin
app.include_router(player_classification_public_router)
app.include_router(player_classification_admin_router)

app.include_router(verified_deaths_router)

app.include_router(final_kvk_router)

# Fight period routes - both public and admin
app.include_router(fight_periods_public_router)
app.include_router(fight_periods_admin_router)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "KvK Tracker API is running!",
        "version": settings.app_version,
        "status": "healthy"
    }

@app.get("/api/test")
async def test():
    """Test endpoint to verify API is working."""
    return {
        "message": "API is working!",
        "database": "connected" if Database.client else "disconnected"
    }

# Test endpoints removed for production
# These should be in a separate test suite, not in production code
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)