from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse, Response

from app.api.auth import router as auth_router
from app.api.customers import router as customer_router
from app.api.appointments import router as appointments_router
from app.api.orders import router as orders_router
from app.api.support import router as support_router
from app.api.agent import router as agent_router
from app.db.database import engine, Base
from app.db import models
from app.core.logging import get_logger, new_request_id, reset_request_id, set_request_id, setup_logging
from app.core.metrics import (
    HTTP_REQUESTS_IN_PROGRESS,
    METRICS_CONTENT_TYPE,
    generate_metrics,
    get_detailed_metrics_snapshot,
    get_metrics_summary,
    record_http_request,
)

DASHBOARD_HTML_PATH = Path(__file__).resolve().parent.parent / "dashboard" / "index.html"

setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize application resources when the service starts."""
    logger.info("Starting application")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified")
    yield
    logger.info("Stopping application")

app  = FastAPI(
    title="Voice Agent API",
    description="Enterprise Voice Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(appointments_router)
app.include_router(orders_router)
app.include_router(support_router)
app.include_router(agent_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID", new_request_id())
    context_token = set_request_id(request_id)
    started = perf_counter()
    status_code = 500
    HTTP_REQUESTS_IN_PROGRESS.inc()
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request completed method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            (perf_counter() - started) * 1000,
        )
        return response
    except Exception:
        logger.exception("Request failed method=%s path=%s", request.method, request.url.path)
        raise
    finally:
        duration_seconds = perf_counter() - started
        route = request.scope.get("route")
        if route and hasattr(route, "path"):
            endpoint = route.path
        elif status_code == 404:
            endpoint = "not_found"
        else:
            endpoint = request.url.path

        record_http_request(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code,
            duration_seconds=duration_seconds,
        )
        HTTP_REQUESTS_IN_PROGRESS.dec()
        reset_request_id(context_token)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Voice Agent API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/metrics", response_class=Response, tags=["Monitoring"])
def get_metrics(format: str | None = None) -> Response:
    """
    Expose Prometheus metrics for scraping.

    If format=json is specified, returns a JSON summary.
    Otherwise returns Prometheus exposition text format.
    """
    if format == "json":
        return Response(
            content=json.dumps(get_metrics_summary()),
            media_type="application/json",
        )
    return Response(
        content=generate_metrics(),
        media_type=METRICS_CONTENT_TYPE,
    )
