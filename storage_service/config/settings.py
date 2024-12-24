## storage_service/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "storage_service"
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    MONGODB_URI: str  
    MONGODB_DB: str
    OPENAI_API_KEY: str

    POSTGRES_URI: str

    class Config:
        env_file = ".env"

settings = Settings()
