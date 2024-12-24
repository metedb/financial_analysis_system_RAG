# main.py
from fastapi import FastAPI
from api.routes import router
from config.settings import settings

app = FastAPI(
    title="Data Ingestion Service",
    description="Service for fetching financial market data, news, and company financials",
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "documentation": "/docs" 
    }