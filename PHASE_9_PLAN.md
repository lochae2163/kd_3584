# Phase 9: Monitoring & Analytics - IMPLEMENTATION PLAN

## Overview
Phase 9 adds production-grade monitoring, error tracking, and performance analytics to ensure the application runs smoothly in production and issues are detected proactively.

---

## 🎯 GOALS

1. **Error Monitoring**: Catch and track production errors automatically
2. **Performance Metrics**: Monitor response times and identify bottlenecks
3. **Health Checks**: Endpoint for service health monitoring
4. **Request Logging**: Track API usage and performance
5. **Alerting**: Get notified of critical issues

---

## 🚀 IMPLEMENTATION TASKS

### Task 1: Sentry Error Monitoring (HIGH PRIORITY)
**Priority**: 🔴 CRITICAL for production
**Estimated Impact**: Proactive error detection
**Estimated Time**: 1-2 hours

**Implementation:**

1. **Add Sentry dependency:**
```txt
# requirements.txt
sentry-sdk[fastapi]>=1.40.0
```

2. **Configure Sentry in main.py:**
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

# Initialize Sentry (optional - only if DSN provided)
if settings.sentry_dsn:
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
    logger.info("✅ Sentry error monitoring enabled")
```

3. **Add config settings:**
```python
# config.py
sentry_dsn: str = Field(default="", description="Sentry DSN for error monitoring")
environment: str = Field(default="production", description="Environment name")
```

4. **Update .env.example:**
```ini
# Sentry Error Monitoring (Optional - Phase 9)
# Get DSN from sentry.io after creating a project
# Free tier: 5,000 errors/month
SENTRY_DSN=""
ENVIRONMENT="production"  # or "development", "staging"
```

**Benefits:**
- Automatic error capture with full context
- Performance monitoring (slow queries, endpoints)
- Release tracking
- User impact analysis
- Email/Slack alerts for critical errors

---

### Task 2: Performance Metrics Middleware (HIGH)
**Priority**: 🟠 HIGH
**Estimated Impact**: Track performance over time
**Estimated Time**: 2-3 hours

**Create Middleware (`backend/app/middleware/metrics.py`):**
```python
from fastapi import Request
import time
import logging
from typing import Callable

logger = logging.getLogger(__name__)

async def performance_metrics_middleware(request: Request, call_next: Callable):
    """
    Track request performance metrics.

    Logs:
    - Request method and path
    - Response status code
    - Response time in milliseconds
    - Query parameters (for debugging)
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time
    duration_ms = round(duration * 1000, 2)

    # Log metrics
    logger.info(
        "API Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "query_params": str(request.query_params),
        }
    )

    # Add custom header for debugging
    response.headers["X-Process-Time"] = str(duration)

    # Alert on slow requests (>1 second)
    if duration > 1.0:
        logger.warning(
            f"Slow request detected: {request.method} {request.url.path} took {duration_ms}ms"
        )

    return response
```

**Add to main.py:**
```python
from app.middleware.metrics import performance_metrics_middleware

app.middleware("http")(performance_metrics_middleware)
```

**Benefits:**
- Track response times per endpoint
- Identify slow queries
- Monitor performance trends
- Debug production issues

---

### Task 3: Enhanced Request Logging (MEDIUM)
**Priority**: 🟡 MEDIUM
**Estimated Time**: 1 hour

**Create structured logging (`backend/app/logging_config.py`):**
```python
import logging
import sys
from datetime import datetime

def setup_logging():
    """Configure structured logging for production."""

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return root_logger
```

**Update main.py:**
```python
from app.logging_config import setup_logging

# Setup logging
logger = setup_logging()
logger.info("🚀 Starting KvK Tracker...")
```

---

### Task 4: Health Check Endpoint (HIGH)
**Priority**: 🟠 HIGH
**Estimated Time**: 30 minutes

**Create health check route (`backend/app/routes/health.py`):**
```python
from fastapi import APIRouter
from app.database import Database
from app.cache import CacheService
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring services.

    Returns:
    - Overall status
    - Database connectivity
    - Cache connectivity (if enabled)
    - Version info
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

    return health

@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes/Docker.

    Returns 200 if app is ready to serve requests.
    Returns 503 if app is not ready.
    """
    try:
        # Check critical dependencies
        if Database.client:
            await Database.client.admin.command('ping')
            return {"status": "ready"}
        else:
            return {"status": "not ready", "reason": "database not connected"}, 503
    except Exception as e:
        return {"status": "not ready", "reason": str(e)}, 503

@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker.

    Returns 200 if app is alive (process is running).
    """
    return {"status": "alive"}
```

**Add to main.py:**
```python
from app.routes.health import router as health_router

app.include_router(health_router)
```

---

### Task 5: Cache Hit Rate Tracking (MEDIUM)
**Priority**: 🟡 MEDIUM
**Estimated Time**: 1-2 hours

**Enhance CacheService with metrics:**
```python
class CacheService:
    redis: Optional[aioredis.Redis] = None

    # Metrics
    cache_hits: int = 0
    cache_misses: int = 0

    @classmethod
    async def get(cls, key: str) -> Optional[Any]:
        """Get value from cache (with metrics)."""
        if not cls.redis:
            return None

        try:
            value = await cls.redis.get(key)
            if value:
                cls.cache_hits += 1
                return json.loads(value)
            else:
                cls.cache_misses += 1
                return None
        except Exception as e:
            logger.error(f"❌ Cache get failed for key '{key}': {e}")
            cls.cache_misses += 1
            return None

    @classmethod
    def get_hit_rate(cls) -> float:
        """Calculate cache hit rate percentage."""
        total = cls.cache_hits + cls.cache_misses
        if total == 0:
            return 0.0
        return (cls.cache_hits / total) * 100

    @classmethod
    def get_stats(cls) -> Dict:
        """Get cache statistics."""
        return {
            "hits": cls.cache_hits,
            "misses": cls.cache_misses,
            "hit_rate": f"{cls.get_hit_rate():.2f}%"
        }
```

**Add metrics endpoint:**
```python
@router.get("/metrics/cache")
async def get_cache_metrics():
    """Get cache performance metrics."""
    if not CacheService.redis:
        return {"status": "disabled"}

    return {
        "status": "enabled",
        "statistics": CacheService.get_stats()
    }
```

---

### Task 6: Admin Metrics Dashboard Endpoint (LOW)
**Priority**: 🔵 LOW
**Estimated Time**: 1-2 hours

**Create admin metrics route:**
```python
@router.get("/admin/metrics")
async def get_admin_metrics(current_admin: str = Depends(get_current_admin)):
    """
    Get comprehensive system metrics for admin dashboard.

    Requires authentication.
    """
    metrics = {
        "cache": CacheService.get_stats() if CacheService.redis else {"status": "disabled"},
        "database": {
            "collections": [],
            "total_documents": 0
        }
    }

    # Get database stats
    if Database.client:
        db = Database.get_database()
        collections = await db.list_collection_names()

        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            metrics["database"]["collections"].append({
                "name": collection_name,
                "documents": count
            })
            metrics["database"]["total_documents"] += count

    return metrics
```

---

## 📊 EXPECTED BENEFITS

### Error Monitoring (Sentry)
- **Proactive Detection**: Know about errors before users report them
- **Context**: Full stack traces, user context, breadcrumbs
- **Performance**: Identify slow queries and endpoints
- **Trends**: Track error rates over time
- **Alerts**: Email/Slack notifications for critical issues

### Performance Metrics
- **Visibility**: See which endpoints are slow
- **Trends**: Track performance improvements over time
- **Debugging**: Identify performance regressions quickly
- **Optimization**: Data-driven performance improvements

### Health Checks
- **Uptime Monitoring**: External services can monitor health
- **Kubernetes**: Ready/live probes for orchestration
- **Quick Diagnosis**: Instant status of all services
- **Automated Recovery**: Auto-restart unhealthy containers

---

## 🎯 SUCCESS CRITERIA

- ✅ Sentry captures and reports errors automatically
- ✅ Performance metrics logged for every request
- ✅ Health check endpoint responds correctly
- ✅ Cache hit rate tracked and visible
- ✅ Slow requests identified and logged
- ✅ No performance degradation from monitoring
- ✅ Admin can view system metrics

---

## 📋 TESTING STRATEGY

### Sentry Testing
```python
# Test error capture
@router.get("/test/error")
async def test_error():
    """Test endpoint - trigger Sentry error."""
    raise Exception("Test error for Sentry monitoring")
```

### Performance Metrics Testing
```bash
# Make requests and check logs
curl http://localhost:8000/api/leaderboard
# Should see: "API Request | duration_ms: 123.45"
```

### Health Check Testing
```bash
# Test health endpoint
curl http://localhost:8000/health
# Expected: {"status": "healthy", "services": {...}}

# Test ready/live probes
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live
```

---

## ⚠️ CONSIDERATIONS

1. **Sentry DSN**: Optional - app works without it
2. **Performance Overhead**: Metrics middleware adds <1ms per request
3. **Log Volume**: May increase in production (use log aggregation)
4. **Privacy**: Don't log sensitive data (passwords, tokens)
5. **Cost**: Sentry free tier is 5,000 errors/month

---

## 🚀 IMPLEMENTATION ORDER

### Priority 1: Essential (Complete First)
1. Sentry error monitoring (1-2 hours)
2. Health check endpoints (30 min)
3. Performance metrics middleware (2-3 hours)

### Priority 2: Nice to Have
4. Cache hit rate tracking (1-2 hours)
5. Enhanced logging (1 hour)
6. Admin metrics dashboard (1-2 hours)

---

## 📝 INFRASTRUCTURE SETUP

### Sentry Setup
1. Sign up at sentry.io
2. Create new project (Python/FastAPI)
3. Copy DSN from project settings
4. Add to .env: `SENTRY_DSN="https://...@sentry.io/..."`

### Log Aggregation (Optional)
- **Papertrail**: Simple log aggregation
- **Loggly**: Log search and analysis
- **ELK Stack**: Self-hosted logging
- **CloudWatch**: AWS logging

### Uptime Monitoring (Optional)
- **UptimeRobot**: Free uptime monitoring
- **Pingdom**: Professional monitoring
- **StatusCake**: Global monitoring

---

## 🎯 READY TO BEGIN

Phase 9 will add production-grade observability to ensure the application runs smoothly and issues are detected early.

**Next Step:** Start with Task 1 (Sentry Error Monitoring)

---

**Status:** 📋 PLANNED
**Created:** 2026-01-12
**Phase 8 Status:** ✅ COMPLETE
**Phase 9 Status:** 🚧 READY TO START
