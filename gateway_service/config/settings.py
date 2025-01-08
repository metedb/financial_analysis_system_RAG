from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    INGESTION_SERVICE_URL: str = "http://ingestion_service:8000"
    STORAGE_SERVICE_URL: str = "http://storage_service:8001"
    ANALYSIS_SERVICE_URL: str = "http://analysis_service:8002"

    class Config:
        env_file = ".env"

settings = Settings()