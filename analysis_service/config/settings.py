# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service configuration
    SERVICE_NAME: str = "analysis_service"
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # API configurations
    OPENAI_API_KEY: str 
    TAVILY_API_KEY: str 
    GATEWAY_URI: str = "http://localhost:8080"
    
    class Config:
        env_file = ".env"

settings = Settings()