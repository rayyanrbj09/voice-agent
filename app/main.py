from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.customers import router as customer_router
from app.api.agent import router as agent_router
from app.db.database import engine, Base
from app.db import models

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize application resources when the service starts."""
    Base.metadata.create_all(bind=engine)
    yield

app  = FastAPI(
    title="Voice Agent API",
    description="Enterprise Voice Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(agent_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Voice Agent API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
