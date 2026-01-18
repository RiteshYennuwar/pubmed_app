from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PUBMED_EMAIL: str
    PUBMED_API_KEY: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()