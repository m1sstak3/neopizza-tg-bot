from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    PAYMENT_PROVIDER_TOKEN: str
    
    # ID is passed from .env, no integer fallback to prevent identifying the dev
    SUPERADMIN_ID: int
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    DATABASE_URL: str
    
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()
