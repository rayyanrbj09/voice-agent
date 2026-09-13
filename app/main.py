from contextlib import asynccontextmanager
import logging
from time import perf_counter

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import Response

from app.api.auth import router as auth_router
from app.api.customers import router as customer_router
from app.api.agent import router as agent_router
from app.db.database import engine, Base
from app.db import models
from app.core.logging import get_logger, new_request_id, reset_request_id, set_request_id, setup_logging

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
app.include_router(agent_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID", new_request_id())
    context_token = set_request_id(request_id)
    started = perf_counter()
    try:
        response = await call_next(request)
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
        reset_request_id(context_token)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Voice Agent API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
