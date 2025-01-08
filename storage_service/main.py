# storage_service/main.py
from fastapi import FastAPI
from api.routes import router
from database.mongodb_atlas import test_mongodb_connection, save_news
from database.postgres import Base, engine
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def lifespan(app: FastAPI):
    try:
        # initialize PostgreSQL tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL tables created successfully")

        # test MongoDB connection
        await test_mongodb_connection()
        logger.info("MongoDB connection tested successfully")

        yield  # control is passed to the application

    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

# initialise FastAPI
app = FastAPI(
    title="Storage Service",
    description="Service for storing financial data in PostgreSQL and MongoDB",
    lifespan=lifespan  
)

app.include_router(router)





# health check endpoinf
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "storage_service",
        "databases": {
            "postgresql": "connected",
            "mongodb": "connected"
        }
    }

# toot endpoint
@app.get("/")
async def root():
    return {
        "message": "Storage Service API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
