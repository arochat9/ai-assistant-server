import time
import uuid

import structlog
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


class APMMiddleware(BaseHTTPMiddleware):
    """Application Performance Monitoring middleware"""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Start timer
        start_time = time.time()

        # Log request start
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Update metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
            ).inc()

            REQUEST_DURATION.labels(
                method=request.method, endpoint=request.url.path
            ).observe(duration)

            # Log request completion
            logger.info(
                "Request completed",
                request_id=request_id,
                status_code=response.status_code,
                duration=duration,
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Update error metrics
            REQUEST_COUNT.labels(
                method=request.method, endpoint=request.url.path, status_code=500
            ).inc()

            # Log error
            logger.error(
                "Request failed", request_id=request_id, error=str(e), duration=duration
            )

            raise


class LoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced logging middleware"""

    async def dispatch(self, request: Request, call_next):
        # Add structured logging context
        with structlog.contextvars.bound_contextvars(
            request_method=request.method,
            request_path=request.url.path,
            request_query=str(request.query_params) if request.query_params else None,
        ):
            response = await call_next(request)
            return response
