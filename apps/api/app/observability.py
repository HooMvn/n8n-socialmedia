from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

logger = logging.getLogger("risheh.engage")

HTTP_REQUESTS = Counter(
    "engage_http_requests_total",
    "HTTP requests handled by Risheh Engage",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "engage_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


def normalized_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path or request.url.path


async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    started = time.perf_counter()
    status_code = 500
    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        path = normalized_path(request)
        elapsed = time.perf_counter() - started
        HTTP_REQUESTS.labels(request.method, path, str(status_code)).inc()
        HTTP_LATENCY.labels(request.method, path).observe(elapsed)
        logger.info(
            "request_complete method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
            request.method,
            path,
            status_code,
            elapsed * 1000,
            request_id,
        )
        # Starlette response headers can only be changed before it is returned.
        if "response" in locals():
            response.headers["X-Request-ID"] = request_id


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
