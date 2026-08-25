from fastapi import FastAPI

from app.db.database import engine, Base
from app.db import models

Base.metadata.create_all(bind=engine)

app  = FastAPI(
    title="Voice Agent API",
    description="Enterprise Voice Agent",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Voice Agent API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
