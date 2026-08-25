from fastapi import FastAPI

app = FastAPI(
    title="Voice Agent API",
    description="Enterprise Voice Agent application",
    version="1.0.0",
)

@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the Voice Agent API!"}

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}
