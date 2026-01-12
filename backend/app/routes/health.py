"""
Health check endpoints for monitoring and orchestration.

Provides:
- /health - Overall system health
- /health/ready - Readiness probe (Kubernetes/Docker)
- /health/live - Liveness probe (Kubernetes/Docker)
"""
from fastapi import APIRouter, Response
from app.database import Database
from app.cache import CacheService
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint for monitoring services.

    Returns:
    - Overall status (healthy/degraded/unhealthy)
    - Database connectivity
    - Cache connectivity (if enabled)
    - Version and environment info
    """
    health = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "services": {}
    }

    # Check database
    try:
        if Database.client:
            await Database.client.admin.command('ping')
            health["services"]["database"] = "connected"
        else:
            health["services"]["database"] = "disconnected"
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    # Check cache (optional)
    try:
        if CacheService.redis:
            await CacheService.redis.ping()
            health["services"]["cache"] = "connected"
        else:
            health["services"]["cache"] = "disabled"
    except Exception as e:
        health["services"]["cache"] = f"error: {str(e)}"
        # Cache is optional, don't mark as unhealthy

    # Check monitoring
    health["services"]["monitoring"] = "enabled" if settings.sentry_dsn else "disabled"

    return health


@router.get("/health/ready")
async def readiness_check(response: Response):
    """
    Readiness check for Kubernetes/Docker orchestration.

    Returns:
    - 200 if app is ready to serve requests
    - 503 if app is not ready (dependencies unavailable)

    Use this for:
    - Kubernetes readiness probes
    - Load balancer health checks
    - Deployment validation
    """
    try:
        # Check critical dependencies
        if Database.client:
            await Database.client.admin.command('ping')
            return {"status": "ready"}
        else:
            response.status_code = 503
            return {"status": "not ready", "reason": "database not connected"}
    except Exception as e:
        response.status_code = 503
        return {"status": "not ready", "reason": str(e)}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker orchestration.

    Returns:
    - 200 if app process is alive and responding

    Use this for:
    - Kubernetes liveness probes
    - Auto-restart detection
    - Process monitoring

    Note: This endpoint always returns 200 if the process is running.
    It does NOT check dependencies (use /health/ready for that).
    """
    return {"status": "alive"}
