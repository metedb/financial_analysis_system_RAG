# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "ingestion_service"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALPHA_VANTAGE_API_KEY: str  

        
    class Config:
        env_file = ".env"

settings = Settings()