"""
Performance metrics middleware for tracking request performance.

Features:
- Tracks response time for every request
- Logs slow requests (>1 second)
- Adds X-Process-Time header for debugging
- Structured logging for analysis
"""
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

    Adds header:
    - X-Process-Time: Response time in seconds
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time
    duration_ms = round(duration * 1000, 2)

    # Log metrics (INFO level for normal requests)
    log_data = {
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
    }

    # Only log query params if they exist (reduce log noise)
    if request.query_params:
        log_data["query_params"] = str(request.query_params)

    logger.info(
        f"API Request: {request.method} {request.url.path} - "
        f"Status {response.status_code} - {duration_ms}ms",
        extra=log_data
    )

    # Add custom header for debugging
    response.headers["X-Process-Time"] = f"{duration:.4f}"

    # Alert on slow requests (>1 second)
    if duration > 1.0:
        logger.warning(
            f"⚠️  Slow request detected: {request.method} {request.url.path} "
            f"took {duration_ms}ms (threshold: 1000ms)",
            extra=log_data
        )

    # Alert on errors
    if response.status_code >= 500:
        logger.error(
            f"❌ Server error: {request.method} {request.url.path} - "
            f"Status {response.status_code}",
            extra=log_data
        )

    return response
